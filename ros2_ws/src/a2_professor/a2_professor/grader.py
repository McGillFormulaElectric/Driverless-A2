"""Auto-discovery grader for MFE A2.

Periodically scans the ROS graph for topics matching:
  - /<user>/hello   (std_msgs/String)   -> A2.1
  - /<user>/answer  (std_msgs/Float32)  -> A2.2

For each newly-seen topic it creates a subscription. It also subscribes to the
professor's own /professor/signal so it can run the *reference* LPF and
compare each student's stream against the expected output.

Feedback is published on /professor/feedback (std_msgs/String) as either:
    'Congrats <user>, the answer is correct'
    'Sorry <user>, the answer is incorrect'
The message is only republished when a student transitions between states.
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import Float32, String

RELIABLE_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
)

ALPHA = 0.1                # must match the value students are told to use
MATCH_WINDOW = 200         # samples used to score A2.2 (10 s @ 20 Hz)
MSE_TOLERANCE = 0.02       # (units of signal^2) — tuned to catch obvious wrong filters
DISCOVERY_PERIOD_S = 2.0   # how often to re-scan for new student topics
GRADE_PERIOD_S = 2.0       # how often to re-grade A2.2 streams

HELLO_RE = re.compile(r'^/([^/]+)/hello$')
ANSWER_RE = re.compile(r'^/([^/]+)/answer$')
RESERVED_USERS = {'professor'}


@dataclass
class HelloState:
    last_verdict: str | None = None  # 'correct' | 'incorrect' | None


@dataclass
class AnswerState:
    samples: Deque[tuple[float, float]] = field(
        default_factory=lambda: deque(maxlen=MATCH_WINDOW)
    )
    last_verdict: str | None = None


class Grader(Node):
    def __init__(self):
        super().__init__('grader')

        self.feedback_pub = self.create_publisher(String, '/professor/feedback', RELIABLE_QOS)

        # Reference LPF state, computed from our own signal stream.
        self._ref_samples: Deque[tuple[float, float]] = deque(maxlen=MATCH_WINDOW * 4)
        self._ref_y_prev: float | None = None
        self.create_subscription(Float32, '/professor/signal', self._on_signal, RELIABLE_QOS)

        self._hello: dict[str, HelloState] = {}
        self._hello_subs: dict[str, object] = {}
        self._answer: dict[str, AnswerState] = {}
        self._answer_subs: dict[str, object] = {}

        self.create_timer(DISCOVERY_PERIOD_S, self._discover)
        self.create_timer(GRADE_PERIOD_S, self._grade_answers)

        self.get_logger().info(
            f'Grader running. ALPHA={ALPHA}, window={MATCH_WINDOW}, '
            f'mse_tol={MSE_TOLERANCE}'
        )

    # --- signal handling ---------------------------------------------------
    def _on_signal(self, msg: Float32) -> None:
        x = float(msg.data)
        if self._ref_y_prev is None:
            y = x
        else:
            y = ALPHA * x + (1.0 - ALPHA) * self._ref_y_prev
        self._ref_y_prev = y
        t = self.get_clock().now().nanoseconds * 1e-9
        self._ref_samples.append((t, y))

    # --- discovery ---------------------------------------------------------
    def _discover(self) -> None:
        for name, types in self.get_topic_names_and_types():
            m = HELLO_RE.match(name)
            if m and 'std_msgs/msg/String' in types:
                user = m.group(1)
                if user in RESERVED_USERS or user in self._hello_subs:
                    continue
                self._hello[user] = HelloState()
                self._hello_subs[user] = self.create_subscription(
                    String, name, self._make_hello_cb(user), RELIABLE_QOS
                )
                self.get_logger().info(f'Discovered A2.1 topic: {name}')
                continue

            m = ANSWER_RE.match(name)
            if m and 'std_msgs/msg/Float32' in types:
                user = m.group(1)
                if user in RESERVED_USERS or user in self._answer_subs:
                    continue
                self._answer[user] = AnswerState()
                self._answer_subs[user] = self.create_subscription(
                    Float32, name, self._make_answer_cb(user), RELIABLE_QOS
                )
                self.get_logger().info(f'Discovered A2.2 topic: {name}')

    # --- A2.1 --------------------------------------------------------------
    def _make_hello_cb(self, user: str):
        def _cb(msg: String) -> None:
            state = self._hello[user]
            verdict = 'correct' if msg.data == 'Hello World!' else 'incorrect'
            if verdict != state.last_verdict:
                state.last_verdict = verdict
                self._publish_feedback(user, verdict)
        return _cb

    # --- A2.2 --------------------------------------------------------------
    def _make_answer_cb(self, user: str):
        def _cb(msg: Float32) -> None:
            t = self.get_clock().now().nanoseconds * 1e-9
            self._answer[user].samples.append((t, float(msg.data)))
        return _cb

    def _grade_answers(self) -> None:
        if len(self._ref_samples) < MATCH_WINDOW:
            return  # not enough reference data yet
        ref_t = np.array([t for t, _ in self._ref_samples])
        ref_y = np.array([y for _, y in self._ref_samples])

        for user, state in self._answer.items():
            if len(state.samples) < MATCH_WINDOW // 2:
                continue
            stu_t = np.array([t for t, _ in state.samples])
            stu_y = np.array([y for _, y in state.samples])

            # Nearest-neighbour match on receive time.
            idx = np.searchsorted(ref_t, stu_t)
            idx = np.clip(idx, 1, len(ref_t) - 1)
            left = ref_t[idx - 1]
            right = ref_t[idx]
            pick_left = np.abs(stu_t - left) < np.abs(stu_t - right)
            matched = np.where(pick_left, ref_y[idx - 1], ref_y[idx])

            mse = float(np.mean((matched - stu_y) ** 2))
            verdict = 'correct' if mse < MSE_TOLERANCE else 'incorrect'
            if verdict != state.last_verdict:
                state.last_verdict = verdict
                self._publish_feedback(user, verdict, extra=f'(MSE={mse:.4f})')

    # --- feedback ----------------------------------------------------------
    def _publish_feedback(self, user: str, verdict: str, extra: str = '') -> None:
        if verdict == 'correct':
            text = f'Congrats {user}, the answer is correct'
        else:
            text = f'Sorry {user}, the answer is incorrect'
        if extra:
            text = f'{text} {extra}'
        msg = String()
        msg.data = text
        self.feedback_pub.publish(msg)
        self.get_logger().info(text)


def main():
    rclpy.init()
    node = Grader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
