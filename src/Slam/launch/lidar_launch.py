import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Node 1: The LiDAR Driver
        Node(
            package='hls_lfcd_lds_driver',
            executable='hlds_laser_publisher',
            name='hlds_laser_publisher',
            parameters=[{'port': '/dev/ttyUSB0', 'frame_id': 'laser'}]
        ), # <--- MAKE SURE THIS COMMA IS HERE

        # Node 2: The Static Transform
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser']
        ), # <--- AND THIS ONE

        # Node 3: RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2'
        ) # Last one doesn't strictly need a comma, but it's good practice
    ])