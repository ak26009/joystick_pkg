import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Int32

class SensorMonitor(Node):
    def __init__(self):
        super().__init__('sensor_monitor')
        
        # Publishers
        self.up_limit_pub = self.create_publisher(Bool, '/limits/upper_hit', 10)
        self.down_limit_pub = self.create_publisher(Bool, '/limits/lower_hit', 10)
        self.pressure_pub = self.create_publisher(Int32, '/sensor/pressure', 10)
        self.angle_pub = self.create_publisher(Int32, '/sensor/angle', 10)
        
        self.subscription = self.create_subscription(
            String, 
            'sensor_val', 
            self.listener_callback, 
            10)
        
        self.get_logger().info("🚀 Sensor Monitor started. Publishing to /limits and /sensor topics.")

    def listener_callback(self, msg):
        try:
            # Parse raw string "UP:0 DOWN:1 PRES:254 ANG:0"
            data_dict = {}
            for item in msg.data.strip().upper().split(' '):
                if ':' in item:
                    key, val = item.split(':')
                    data_dict[key] = int(val)

            # Publish Upper Limit
            if 'UP' in data_dict:
                self.up_limit_pub.publish(Bool(data=bool(data_dict['UP'])))

            # Publish Lower Limit
            if 'DOWN' in data_dict:
                self.down_limit_pub.publish(Bool(data=bool(data_dict['DOWN'])))

            # Publish Pressure
            if 'PRES' in data_dict:
                self.pressure_pub.publish(Int32(data=data_dict['PRES']))

            # Publish Angle
            if 'ANG' in data_dict:
                self.angle_pub.publish(Int32(data=data_dict['ANG']))

        except Exception:
            # Silently ignore malformed packets to keep terminal clean
            pass

def main(args=None):
    rclpy.init(args=args)
    node = SensorMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
