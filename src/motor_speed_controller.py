#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import pygame

AXIS_ID = 2
AXIS_THRESHOLD = -0.9

ENABLE_BUTTON = 4
INCREASE_BUTTON = 3
DECREASE_BUTTON = 0

SPEED_STEP = 10
MIN_SPEED = 0
MAX_SPEED = 100


class MotorSpeedControlNode(Node):
    def __init__(self):
        super().__init__('motor_speed_control_node')

        self.speed_pub = self.create_publisher(Int32, 'motor_speed', 10)

        pygame.init()
        pygame.joystick.init()

        self.js = None

        if pygame.joystick.get_count() == 0:
            self.get_logger().error('No controller detected')
            return

        self.js = pygame.joystick.Joystick(0)
        self.js.init()

        self.get_logger().info(f'Controller detected: {self.js.get_name()}')

        self.motor_speed = 0
        self.prev_increase_combo = 0
        self.prev_decrease_combo = 0

        self.timer = self.create_timer(0.05, self.read_controller)

    def publish_speed(self):
        msg = Int32()
        msg.data = self.motor_speed
        self.speed_pub.publish(msg)

    def read_controller(self):
        if self.js is None:
            return

        pygame.event.pump()

        axis_2 = self.js.get_axis(AXIS_ID)
        button_4 = self.js.get_button(ENABLE_BUTTON)
        button_3 = self.js.get_button(INCREASE_BUTTON)
        button_0 = self.js.get_button(DECREASE_BUTTON)

        increase_combo = 1 if (axis_2 <= AXIS_THRESHOLD and button_4 == 1 and button_3 == 1) else 0
        decrease_combo = 1 if (axis_2 <= AXIS_THRESHOLD and button_4 == 1 and button_0 == 1) else 0

        if increase_combo == 1 and self.prev_increase_combo == 0:
            self.motor_speed += SPEED_STEP
            if self.motor_speed > MAX_SPEED:
                self.motor_speed = MAX_SPEED

            self.publish_speed()
            self.get_logger().info(
                f'INCREASE -> Axis 2 + Button 4 + Button 3 | Motor Speed = {self.motor_speed}'
            )

        if decrease_combo == 1 and self.prev_decrease_combo == 0:
            self.motor_speed -= SPEED_STEP
            if self.motor_speed < MIN_SPEED:
                self.motor_speed = MIN_SPEED

            self.publish_speed()
            self.get_logger().info(
                f'DECREASE -> Axis 2 + Button 4 + Button 0 | Motor Speed = {self.motor_speed}'
            )

        self.prev_increase_combo = increase_combo
        self.prev_decrease_combo = decrease_combo


def main(args=None):
    rclpy.init(args=args)
    node = MotorSpeedControlNode()

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
