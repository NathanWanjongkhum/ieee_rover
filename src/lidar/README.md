import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchSubstitution, LaunchConfiguration

def generate_launch_description():
    # 1. Setup configurations
    # Replace 'robot_name' and 'lidar_name' with what you defined in your SDF file
    robot_name = LaunchConfiguration('robot_name', default='my_rover')
    lidar_name = LaunchConfiguration('lidar_name', default='gpu_lidar')

    # 2. Define the Bridge
    # Format: <gz_topic>@<ros_msg_type>[<gz_msg_type>
    # The '[' means Gazebo -> ROS 2
    bridge_config = [
        '/model/my_rover/sensor/gpu_lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
    ]

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument(
            'robot_name',
            default_value='my_rover',
            description='Name of the robot model in Gazebo'
        ),

        # The Bridge Node
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_bridge_lidar',
            output='screen',
            parameters=[{
                'config_file': '', # You can also use a YAML file, but we'll use arguments:
            }],
            arguments=bridge_config
        ),

        # Optional: Static Transform for the LiDAR frame
        # This maps the Gazebo sensor frame to a ROS frame so RViz can see it
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'my_rover/gpu_lidar_link/gpu_lidar']
        )
    ])import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchSubstitution, LaunchConfiguration

def generate_launch_description():
    # 1. Setup configurations
    # Replace 'robot_name' and 'lidar_name' with what you defined in your SDF file
    robot_name = LaunchConfiguration('robot_name', default='my_rover')
    lidar_name = LaunchConfiguration('lidar_name', default='gpu_lidar')

    # 2. Define the Bridge
    # Format: <gz_topic>@<ros_msg_type>[<gz_msg_type>
    # The '[' means Gazebo -> ROS 2
    bridge_config = [
        '/model/my_rover/sensor/gpu_lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
    ]

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument(
            'robot_name',
            default_value='my_rover',
            description='Name of the robot model in Gazebo'
        ),

        # The Bridge Node
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_bridge_lidar',
            output='screen',
            parameters=[{
                'config_file': '', # You can also use a YAML file, but we'll use arguments:
            }],
            arguments=bridge_config
        ),

        # Optional: Static Transform for the LiDAR frame
        # This maps the Gazebo sensor frame to a ROS frame so RViz can see it
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'my_rover/gpu_lidar_link/gpu_lidar']
        )
    ])import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchSubstitution, LaunchConfiguration

def generate_launch_description():
    # 1. Setup configurations
    # Replace 'robot_name' and 'lidar_name' with what you defined in your SDF file
    robot_name = LaunchConfiguration('robot_name', default='my_rover')
    lidar_name = LaunchConfiguration('lidar_name', default='gpu_lidar')

    # 2. Define the Bridge
    # Format: <gz_topic>@<ros_msg_type>[<gz_msg_type>
    # The '[' means Gazebo -> ROS 2
    bridge_config = [
        '/model/my_rover/sensor/gpu_lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
    ]

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument(
            'robot_name',
            default_value='my_rover',
            description='Name of the robot model in Gazebo'
        ),

        # The Bridge Node
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_bridge_lidar',
            output='screen',
            parameters=[{
                'config_file': '', # You can also use a YAML file, but we'll use arguments:
            }],
            arguments=bridge_config
        ),

        # Optional: Static Transform for the LiDAR frame
        # This maps the Gazebo sensor frame to a ROS frame so RViz can see it
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'my_rover/gpu_lidar_link/gpu_lidar']
        )
    ])import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchSubstitution, LaunchConfiguration

def generate_launch_description():
    # 1. Setup configurations
    # Replace 'robot_name' and 'lidar_name' with what you defined in your SDF file
    robot_name = LaunchConfiguration('robot_name', default='my_rover')
    lidar_name = LaunchConfiguration('lidar_name', default='gpu_lidar')

    # 2. Define the Bridge
    # Format: <gz_topic>@<ros_msg_type>[<gz_msg_type>
    # The '[' means Gazebo -> ROS 2
    bridge_config = [
        '/model/my_rover/sensor/gpu_lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
    ]

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument(
            'robot_name',
            default_value='my_rover',
            description='Name of the robot model in Gazebo'
        ),

        # The Bridge Node
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_bridge_lidar',
            output='screen',
            parameters=[{
                'config_file': '', # You can also use a YAML file, but we'll use arguments:
            }],
            arguments=bridge_config
        ),

        # Optional: Static Transform for the LiDAR frame
        # This maps the Gazebo sensor frame to a ROS frame so RViz can see it
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'my_rover/gpu_lidar_link/gpu_lidar']
        )
    ])import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchSubstitution, LaunchConfiguration

def generate_launch_description():
    # 1. Setup configurations
    # Replace 'robot_name' and 'lidar_name' with what you defined in your SDF file
    robot_name = LaunchConfiguration('robot_name', default='my_rover')
    lidar_name = LaunchConfiguration('lidar_name', default='gpu_lidar')

    # 2. Define the Bridge
    # Format: <gz_topic>@<ros_msg_type>[<gz_msg_type>
    # The '[' means Gazebo -> ROS 2
    bridge_config = [
        '/model/my_rover/sensor/gpu_lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
    ]

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument(
            'robot_name',
            default_value='my_rover',
            description='Name of the robot model in Gazebo'
        ),

        # The Bridge Node
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='gz_bridge_lidar',
            output='screen',
            parameters=[{
                'config_file': '', # You can also use a YAML file, but we'll use arguments:
            }],
            arguments=bridge_config
        ),

        # Optional: Static Transform for the LiDAR frame
        # This maps the Gazebo sensor frame to a ROS frame so RViz can see it
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'my_rover/gpu_lidar_link/gpu_lidar']
        )
    ])# Introduction

This guide walks you through setting up the HLS-LFCD LDS (LiDAR) on ROS 2 Jazzy. It covers the driver installation, permanent permission fixes, and how to use a custom launch package to automate the setup.

# Steps

## Step 1: Install the Driver
Install the official Hitachi-LG sensor driver for the Jazzy distribution:

```shell
sudo apt update
sudo apt install ros-jazzy-hls-lfcd-lds-driver
```


## Step 2: Permanent Permission Fix

Instead of running chmod every time you plug in the LiDAR, add your user to the dialout group. Note: You must restart your computer after running this for it to take effect.

```shell
sudo usermod -a -G dialout $USER
```

Or if you don't want to add a user, just run this command everytime you plug the lidar in.

```shell
sudo chmod a+rw /dev/ttyUSB0
```

## Step 3:Automation Package
Build the lidar package

```shell
colcon build --packages-select lidar
source install/setup.bash
```

## Step 4: Launch Everything
Run your custom launch file. This will start the LiDAR, set the correct coordinate frames (so you don't get the "No TF Data" error), and open RViz:

```shell
ros2 launch lidar lidar_launch.py
```

and if everything goes well you should be seen the lidar in rviz

## Step 5: Verify Data

If RViz is open but you don't see dots:

    - Ensure Fixed Frame is set to base_link or laser.

    - In the LaserScan settings, ensure Reliability Policy is set to Best Effort. It will not show up if its not on best effort.

    - Make sure when you add the item in rviz you grab it through "by topic" not "by display type". The dots only show up when grabbed through "by topic" for some reason.

    - Make sure you always give usb permissions, if they aren't on, then well it can't publish.