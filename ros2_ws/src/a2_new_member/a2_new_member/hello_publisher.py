"""A2.1 — publish 'Hello World!' on <namespace>/hello at 1 Hz.

Run with your GitHub username as the ROS namespace:

    ros2 run a2_new_member hello_publisher --ros-args -r __ns:=/<github-username>
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import String

RELIABLE_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
)


class HelloPublisher(Node):
    def __init__(self):
        super().__init__('hello_publisher')
        self.pub = self.create_publisher(String, 'hello', RELIABLE_QOS)
        self.timer = self.create_timer(1.0, self._tick)
        ns = self.get_namespace()
        self.get_logger().info(f"Publishing 'Hello World!' on {ns}/hello")

    def _tick(self):
        msg = String()
        msg.data = 'Hello World!'
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = HelloPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
