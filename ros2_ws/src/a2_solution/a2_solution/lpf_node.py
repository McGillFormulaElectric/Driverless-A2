"""A2.2 — subscribe to /neil/signal, apply a first-order IIR low-pass
filter, publish the filtered value on <namespace>/answer.

Filter spec (see README for theory):
    y[n] = alpha * x[n] + (1 - alpha) * y[n - 1]
    y[0] = x[0]
    alpha = 0.1   (fixed for grading; do NOT change)

params: alpha (see a2_solution/config/params.yaml; the default 0.1 is fixed by
the assignment and grader — do not change it).

Run with your GitHub username as the ROS namespace:

    ros2 run a2_solution lpf_node --ros-args -r __ns:=/<github-username>
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import Float32

RELIABLE_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
)


class LowPassFilterNode(Node):
    def __init__(self):
        super().__init__('lpf_node')

        # Filter coefficient. Fixed by the assignment (grader uses 0.1); do NOT
        # change. Exposed as a ROS parameter for consistency with the rest of
        # the scenario config (see a2_solution/config/params.yaml).
        self.declare_parameter('alpha', 0.1)
        self.alpha = float(self.get_parameter('alpha').value)

        # Subscribe to Neil's noisy signal.
        self.sub = self.create_subscription(
            Float32, '/neil/signal', self._on_signal, RELIABLE_QOS
        )

        # Publish your filtered answer on <namespace>/answer.
        self.pub = self.create_publisher(Float32, 'answer', RELIABLE_QOS)

        # Filter state (last output). None until the first sample arrives.
        self._y_prev: float | None = None

        ns = self.get_namespace()
        self.get_logger().info(
            f"Subscribed to /neil/signal, publishing filtered output on {ns}/answer"
        )

    def _on_signal(self, msg: Float32) -> None:
        x = float(msg.data)

        # ------------------------------------------------------------------
        # TODO(student): implement the IIR low-pass filter.
        #
        #   y[n] = self.alpha * x[n] + (1 - self.alpha) * y[n - 1]
        #
        # Handle the first sample: y[0] = x[0].
        # Store the new output in self._y_prev so the next callback can use it.
        # Then publish `y` on `self.pub`.
        # ------------------------------------------------------------------
        y = x  # <-- replace this stub with the correct expression

        self._y_prev = y

        out = Float32()
        out.data = float(y)
        self.pub.publish(out)


def main():
    rclpy.init()
    node = LowPassFilterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
