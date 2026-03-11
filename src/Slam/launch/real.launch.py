import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_slam = get_package_share_directory('Slam')
    xacro_file = os.path.join(pkg_slam, 'description', 'larry.urdf.xacro')
    controllers_yaml = os.path.join(pkg_slam, 'config', 'controllers_real.yaml')
    rviz_config = os.path.join(pkg_slam, 'config', 'slam.rviz')

    lidar_port = LaunchConfiguration('lidar_port')
    rviz = LaunchConfiguration('rviz')

    # Layer 1: headless RSP (real URDF — LarrySystemHardware plugin, wall-clock time).
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('Slam'), 'launch', 'rsp.launch.py'])
        ),
        launch_arguments={'use_sim': 'false', 'use_sim_time': 'false'}.items(),
    )

    # ros2_control_node manages the LarrySystemHardware plugin directly.
    # robot_description is computed here so the controller manager has it at startup
    # without depending on the RSP topic being available yet.
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' use_sim:=false']),
        value_type=str,
    )

    ros2_control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {'robot_description': robot_description},
            controllers_yaml,
        ],
        output='screen',
    )

    # Spawn controllers once the controller manager is up (~2 s delay).
    joint_state_broadcaster_spawner = TimerAction(
        period=2.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen',
        )],
    )

    diff_drive_spawner = TimerAction(
        period=2.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['diff_drive_controller'],
            output='screen',
        )],
    )

    # Real HLS LiDAR driver.
    lidar = Node(
        package='hls_lfcd_lds_driver',
        executable='hlds_laser_publisher',
        name='hlds_laser_publisher',
        parameters=[{'port': lidar_port, 'frame_id': 'laser'}],
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        condition=IfCondition(rviz),
        arguments=['-d', rviz_config],
    )

    return LaunchDescription([
        DeclareLaunchArgument('lidar_port', default_value='/dev/ttyUSB1',
                              description='Serial port for the HLS LiDAR sensor'),
        DeclareLaunchArgument('rviz', default_value='false', description='Open RViz'),
        rsp,
        ros2_control_node,
        joint_state_broadcaster_spawner,
        diff_drive_spawner,
        lidar,
        rviz_node,
    ])
