import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial

class MotorDriver(Node):
    def __init__(self):
        super().__init__('controller_publisher_interface')
        
        # Serial Init
        self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)

        # Internals
        self.mode = 'manual'  
        self.manual_val = 'S'
        self.auto_val = 'S'

        # 1. Mode Selector
        self.create_subscription(String, 'control_mode', self.mode_cb, 10)
        
        # 2. Input Streams
        self.create_subscription(String, 'manual_cmd', self.manual_cb, 10)
        self.create_subscription(String, 'auto_cmd', self.auto_cb, 10)

        # 3. Limit Publisher
        self.limit_pub = self.create_publisher(String, 'sensor_val', 10)

        # 4. Main Control Loop (20Hz)
        self.create_timer(0.05, self.loop)
        
        self.get_logger().info("System started in MANUAL mode.")

    def mode_cb(self, msg):
        new_mode = msg.data.lower()
        if new_mode in ['manual', 'auto']:
            self.mode = new_mode
            self.get_logger().info(f"--- MODE SWITCHED TO: {self.mode.upper()} ---")

    def manual_cb(self, msg):
        data = msg.data.upper()

        # Pressure Command
        if data.startswith('P'):
            self.ser.write(data.encode())
            self.get_logger().info(f"Pressure Command Sent to Arduino: {data}")

        # Servo Command
        elif data.startswith('A'):
            self.ser.write(data.encode())
            self.get_logger().info(f"Servo Command Sent to Arduino: {data}")

        # Motor Command (U, D, S)
        else:
            self.manual_val = data

    def auto_cb(self, msg):
        self.auto_val = msg.data.upper()

    def loop(self):
        # Determine which motor command to send
        cmd = self.manual_val if self.mode == 'manual' else self.auto_val
        
        # Only send motor commands (U, D, S) in the loop
        self.ser.write(cmd.encode())

        # Read status back from Arduino (Limits + Pressure Feedback)
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                self.limit_pub.publish(String(data=line))

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(MotorDriver())
    rclpy.shutdown()
