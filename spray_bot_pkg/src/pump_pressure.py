import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32

class PressureNode(Node):
    def __init__(self):
        super().__init__('pump_pressure')
        
        # Mapping Logic
        self.pressure_map = {
            "LOW": 100,
            "MEDIUM": 170,
            "HIGH": 230,
            "OFF": 0
        }

        # 1. Hardware Bridge: Sends 'P' commands to the Motor Driver (Gatekeeper)
        self.cmd_pub = self.create_publisher(String, 'manual_cmd', 10)
        
        # 2. Hardware Feedback: Listens to the raw Serial string from Driver
        self.create_subscription(String, 'sensor_val', self.parse_status, 10)
        
        # 3. User Interface: Receive words, publish numbers
        self.create_subscription(String, 'set_pressure_level', self.level_cb, 10)
        self.pressure_val_pub = self.create_publisher(Int32, 'current_pressure_value', 10)

        # 4. Initialization: Set pressure to 0 at start
        self.init_timer = self.create_timer(1.0, self.send_initial_zero)
        
        self.get_logger().info("Pressure Node Started. Waiting for: Low, Medium, or High.")

    def send_initial_zero(self):
        # Send 0 at start, then stop the timer
        self.send_pressure_command(0)
        self.get_logger().info("Initialization: Pressure set to 0.")
        self.init_timer.cancel()

    def level_cb(self, msg):
        level = msg.data.upper().strip()
        
        if level in self.pressure_map:
            target_value = self.pressure_map[level]
            self.send_pressure_command(target_value)
            self.get_logger().info(f"Level received: {level} -> Sending PWM: {target_value}")
        else:
            self.get_logger().warn(f"Invalid Level: {level}. Use Low, Medium, or High.")



    def send_pressure_command(self, val):
        out_msg = String()
        out_msg.data = f"P{val}"
        self.cmd_pub.publish(out_msg)

    def parse_status(self, msg):
        # Extracts "PRES:X" from the Arduino status string
        if "PRES:" in msg.data:
            try:
                pres_str = msg.data.split("PRES:")[1].strip()
                val_msg = Int32()
                val_msg.data = int(pres_str)
                self.pressure_val_pub.publish(val_msg)
            except (IndexError, ValueError):
                pass

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(PressureNode())
    rclpy.shutdown()
