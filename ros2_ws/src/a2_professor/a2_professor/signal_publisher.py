"""Publishes /professor/signal at SIGNAL_HZ Hz.

Signal = sum of two sinusoids + zero-mean Gaussian noise, deterministic given
the seed (so grading is reproducible across restarts on the professor side).

    x(t) = A1*sin(2*pi*f1*t) + A2*sin(2*pi*f2*t) + noise(t)
"""
import math

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import Float32

RELIABLE_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
)

SIGNAL_HZ = 20.0        # publish rate
F1, A1 = 0.5, 1.0       # slow component (should survive the LPF)
F2, A2 = 5.0, 0.6       # fast component (should be attenuated by the LPF)
NOISE_STD = 0.3
SEED = 20260909


class SignalPublisher(Node):
    def __init__(self):
        super().__init__('signal_publisher')
        self.pub = self.create_publisher(Float32, '/professor/signal', RELIABLE_QOS)
        self.timer = self.create_timer(1.0 / SIGNAL_HZ, self._tick)
        self._rng = np.random.default_rng(SEED)
        self._t0 = self.get_clock().now().nanoseconds * 1e-9
        self.get_logger().info(
            f'Publishing /professor/signal @ {SIGNAL_HZ:.1f} Hz '
            f'(f1={F1} Hz, f2={F2} Hz, noise_std={NOISE_STD})'
        )

    def _tick(self):
        t = self.get_clock().now().nanoseconds * 1e-9 - self._t0
        clean = A1 * math.sin(2 * math.pi * F1 * t) + A2 * math.sin(2 * math.pi * F2 * t)
        x = clean + float(self._rng.normal(0.0, NOISE_STD))
        msg = Float32()
        msg.data = float(x)
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = SignalPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
