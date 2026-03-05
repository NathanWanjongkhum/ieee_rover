#!/usr/bin/env python3
"""WASD keyboard teleop — publishes TwistStamped to diff_drive_controller/cmd_vel."""

import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped

TOPIC = '/diff_drive_controller/cmd_vel'

LINEAR_SPEED  = 0.4   # m/s  (W/S)
ANGULAR_SPEED = 1.0   # rad/s (A/D)
SPEED_STEP    = 0.05  # increment per +/-

HELP = """
WASD Teleop  —  Larry Rover
----------------------------
  W : forward         S : backward
  A : turn left       D : turn right
  Q : rotate CCW      E : rotate CW

  + / = : increase speed
  -     : decrease speed
  Space : stop
  Ctrl+C: quit
"""

KEY_BINDINGS: dict[str, tuple[float, float]] = {
    'w': ( 1.0,  0.0),
    's': (-1.0,  0.0),
    'a': ( 0.0,  1.0),
    'd': ( 0.0, -1.0),
    'q': ( 0.0,  1.0),   # pure rotate left
    'e': ( 0.0, -1.0),   # pure rotate right
    ' ': ( 0.0,  0.0),   # stop
}


def get_key(settings) -> str:
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class WasdTeleop(Node):
    def __init__(self):
        super().__init__('wasd_teleop')
        self._pub = self.create_publisher(TwistStamped, TOPIC, 10)

    def publish(self, linear: float, angular: float) -> None:
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = linear
        msg.twist.angular.z = angular
        self._pub.publish(msg)


def main():
    rclpy.init()
    node = WasdTeleop()

    settings = termios.tcgetattr(sys.stdin)
    linear_speed  = LINEAR_SPEED
    angular_speed = ANGULAR_SPEED

    print(HELP)
    print(f'Speed: linear={linear_speed:.2f} m/s  angular={angular_speed:.2f} rad/s')

    try:
        while rclpy.ok():
            key = get_key(settings).lower()

            if key == '\x03':   # Ctrl+C
                break

            if key in ('+', '='):
                linear_speed  = min(linear_speed  + SPEED_STEP, 2.0)
                angular_speed = min(angular_speed + SPEED_STEP, 3.0)
                print(f'Speed: linear={linear_speed:.2f}  angular={angular_speed:.2f}')
                continue

            if key == '-':
                linear_speed  = max(linear_speed  - SPEED_STEP, 0.05)
                angular_speed = max(angular_speed - SPEED_STEP, 0.1)
                print(f'Speed: linear={linear_speed:.2f}  angular={angular_speed:.2f}')
                continue

            if key in KEY_BINDINGS:
                lin_scale, ang_scale = KEY_BINDINGS[key]
                # W/S move, A/D strafe-turn (linear + angular simultaneously)
                if key in ('a', 'd'):
                    node.publish(linear_speed * 0.3, angular_speed * ang_scale)
                else:
                    node.publish(linear_speed * lin_scale, angular_speed * ang_scale)
            else:
                # Any other key: stop
                node.publish(0.0, 0.0)

    finally:
        node.publish(0.0, 0.0)   # safety stop
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
