import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_slam = get_package_share_directory('Slam')
    larry_description_share = get_package_share_directory('larry_description')

    bridge_config = os.path.join(pkg_slam, 'config', 'gpu_lidar.yaml')
    default_world = os.path.join(pkg_slam, 'worlds', 'playground.sdf')
    rviz_config = os.path.join(pkg_slam, 'config', 'slam.rviz')

    robot_name = LaunchConfiguration('robot_name')
    gz_args = LaunchConfiguration('gz_args')
    rviz = LaunchConfiguration('rviz')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    yaw = LaunchConfiguration('Y')

    # Let Gazebo resolve model://larry_description/meshes/... URIs.
    set_gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(larry_description_share),
    )

    # Layer 1: headless RSP (sim URDF + sim clock).
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('Slam'), 'launch', 'rsp.launch.py'])
        ),
        launch_arguments={'use_sim': 'true', 'use_sim_time': 'true'}.items(),
    )

    # Layer 2: Gazebo simulator.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])
        ),
        launch_arguments={'gz_args': gz_args}.items(),
    )

    # Spawn robot from /robot_description topic (published by RSP above).
    spawn = TimerAction(
        period=2.0,
        actions=[Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            arguments=[
                '-topic', 'robot_description',
                '-name', robot_name,
                '-x', x, '-y', y, '-z', z, '-Y', yaw,
            ],
        )],
    )

    # Bridge Gazebo LiDAR scan + clock → ROS topics.
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_bridge',
        output='screen',
        parameters=[{'use_sim_time': True, 'config_file': bridge_config}],
    )

    # Controllers (spawned after Gazebo + gz_ros2_control have had time to start).
    joint_state_broadcaster_spawner = TimerAction(
        period=4.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen',
        )],
    )

    diff_drive_spawner = TimerAction(
        period=4.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['diff_drive_controller'],
            output='screen',
        )],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        condition=IfCondition(rviz),
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        set_gz_resource_path,
        DeclareLaunchArgument('robot_name', default_value='Larry 2.0',
                              description='Entity name in Gazebo'),
        DeclareLaunchArgument('gz_args', default_value=f'-r {default_world}',
                              description='Arguments passed to gz sim'),
        DeclareLaunchArgument('x', default_value='0.0', description='Spawn X'),
        DeclareLaunchArgument('y', default_value='0.0', description='Spawn Y'),
        DeclareLaunchArgument('z', default_value='0.2', description='Spawn Z'),
        DeclareLaunchArgument('Y', default_value='0.0', description='Spawn yaw (rad)'),
        DeclareLaunchArgument('rviz', default_value='false', description='Open RViz'),
        rsp,
        gz_sim,
        spawn,
        bridge,
        joint_state_broadcaster_spawner,
        diff_drive_spawner,
        rviz_node,
    ])
