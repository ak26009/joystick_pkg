import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ServoNode(Node):

    def __init__(self):
        super().__init__('spray_gun')

        # Publisher to manual_cmd (same topic used for U/D/S/P)
        self.publisher = self.create_publisher(String, 'manual_cmd', 10)

        self.get_logger().info("Servo Node Started")

        # Example: remove this timer if you want external trigger only
        # self.create_timer(2.0, self.test_move)

    def send_angle(self, angle):
        # Clamp between 0–180
        if angle < 0:
            angle = 0
        if angle > 180:
            angle = 180

        msg = String()
        msg.data = f"A{angle}"
        self.publisher.publish(msg)

        self.get_logger().info(f"Published Servo Command: A{angle}")

    # Optional test function
    # def test_move(self):
    #     self.send_angle(90)


def main(args=None):
    rclpy.init(args=args)
    node = ServoNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
