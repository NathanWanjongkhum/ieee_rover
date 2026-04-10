import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_ieee_rover = get_package_share_directory('ieee_rover')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    nav2_params_file = os.path.join(pkg_ieee_rover, 'config', 'nav2_params.yaml')
    twist_mux_params = os.path.join(pkg_ieee_rover, 'config', 'twist_mux.yaml')

    # Hardware bringup + SLAM (wall-clock time).
    slam_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('Slam'), 'launch', 'slam_robot.launch.py'])
        ),
    )

    # Nav2 navigation stack only (use_sim_time=false for real hardware).
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': nav2_params_file,
            'autostart': 'true',
        }.items(),
    )

    # Velocity multiplexer — merges nav2 /cmd_vel with teleop inputs and
    # outputs TwistStamped to diff_drive_controller/cmd_vel.
    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux',
        output='screen',
        parameters=[
            twist_mux_params,
            {'use_stamped': True},
        ],
        remappings=[
            ('cmd_vel_out', 'diff_drive_controller/cmd_vel'),
        ],
    )

    return LaunchDescription([
        slam_robot,
        nav2,
        twist_mux,
    ])
