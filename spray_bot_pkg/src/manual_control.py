import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pynput import keyboard

class KeyboardPublisher(Node):
    def __init__(self):
        super().__init__('manual_control')
        # Change 'motor_command' to 'manual_cmd'
        self.publisher_ = self.create_publisher(String, 'manual_cmd', 10)
        
        self.up_pressed = False
        self.down_pressed = False
        self.last_sent = None

        self.get_logger().info("Keyboard Publisher Started. Use UP/DOWN arrows. Press 'S' to stop.")
        
        # Start the listener
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

    def update_state(self):
        cmd = 'S'
        if self.up_pressed: cmd = 'U'
        elif self.down_pressed: cmd = 'D'
        
        if cmd != self.last_sent:
            msg = String()
            msg.data = cmd
            self.publisher_.publish(msg)
            self.last_sent = cmd

    def on_press(self, key):
        if key == keyboard.Key.up: self.up_pressed = True
        elif key == keyboard.Key.down: self.down_pressed = True
        self.update_state()

    def on_release(self, key):
        if key == keyboard.Key.up: self.up_pressed = False
        elif key == keyboard.Key.down: self.down_pressed = False
        self.update_state()

def main(args=None):
    rclpy.init(args=args)
    node = KeyboardPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
