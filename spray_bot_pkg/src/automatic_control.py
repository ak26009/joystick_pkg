import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class AutoNode(Node):
    def __init__(self):
        super().__init__('automatic_control')
        
        self.target = 'S'
        self.up_limit = False
        self.down_limit = False

        # Listen for Limits
        self.create_subscription(String, 'sensor_val', self.limit_cb, 10)
        
        # Listen for Auto-Goals (Where do you want to go automatically?)
        self.create_subscription(String, 'auto_goal', self.goal_cb, 10)

        # Publish to the Auto Channel
        self.auto_pub = self.create_publisher(String, 'auto_cmd', 10)
        
        self.create_timer(0.1, self.timer_cb)

    def limit_cb(self, msg):
        self.up_limit = "UP:1" in msg.data
        self.down_limit = "DOWN:1" in msg.data

    def goal_cb(self, msg):
        self.target = msg.data.upper() # 'U' or 'D'
        self.get_logger().info(f"New Auto Goal received: {self.target}")

    def timer_cb(self):
        # Logic: If moving U and hit limit, stop.
        out = self.target
        if self.target == 'U' and self.up_limit: out = 'S'
        if self.target == 'D' and self.down_limit: out = 'S'
        
        self.auto_pub.publish(String(data=out))

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(AutoNode())
    rclpy.shutdown()
