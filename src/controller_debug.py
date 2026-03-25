#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import pygame


class ControllerDebugNode(Node):
    def __init__(self):
        super().__init__('controller_debug_node')

        pygame.init()
        pygame.joystick.init()

        self.js = None
        self.prev_buttons = []
        self.prev_axes = []
        self.prev_hats = []

        count = pygame.joystick.get_count()
        if count == 0:
            self.get_logger().error('No controller detected')
            return

        self.js = pygame.joystick.Joystick(0)
        self.js.init()

        self.num_buttons = self.js.get_numbuttons()
        self.num_axes = self.js.get_numaxes()
        self.num_hats = self.js.get_numhats()

        self.prev_buttons = [0] * self.num_buttons
        self.prev_axes = [0.0] * self.num_axes
        self.prev_hats = [(0, 0)] * self.num_hats

        self.get_logger().info(f'Controller detected: {self.js.get_name()}')
        self.get_logger().info(f'Buttons: {self.num_buttons}')
        self.get_logger().info(f'Axes: {self.num_axes}')
        self.get_logger().info(f'Hats: {self.num_hats}')
        self.get_logger().info('Press buttons / move sticks / press D-pad to test')

        self.timer = self.create_timer(0.05, self.read_controller)  # 20 Hz

    def read_controller(self):
        if self.js is None:
            return

        pygame.event.pump()

        # Check buttons
        for i in range(self.num_buttons):
            value = self.js.get_button(i)
            if value != self.prev_buttons[i]:
                if value == 1:
                    self.get_logger().info(f'Button {i} PRESSED')
                else:
                    self.get_logger().info(f'Button {i} RELEASED')
                self.prev_buttons[i] = value

        # Check axes
        for i in range(self.num_axes):
            value = self.js.get_axis(i)

            # Only print when axis changes enough
            if abs(value - self.prev_axes[i]) > 0.15:
                self.get_logger().info(f'Axis {i}: {value:.3f}')
                self.prev_axes[i] = value

        # Check hats / D-pad
        for i in range(self.num_hats):
            value = self.js.get_hat(i)
            if value != self.prev_hats[i]:
                self.get_logger().info(f'Hat {i}: {value}')
                self.prev_hats[i] = value


def main(args=None):
    rclpy.init(args=args)
    node = ControllerDebugNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
