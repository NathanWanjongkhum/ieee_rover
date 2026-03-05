import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, TextSubstitution

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_slam = get_package_share_directory('Slam')
    larry_description_share = get_package_share_directory('larry_description')

    xacro_file = os.path.join(pkg_slam, 'description', 'larry.urdf.xacro')
    bridge_config_path = os.path.join(pkg_slam, 'config', 'gpu_lidar.yaml')
    default_world = os.path.join(pkg_slam, 'worlds', 'playground.sdf')

    robot_name = LaunchConfiguration('robot_name')
    gz_args = LaunchConfiguration('gz_args')
    rviz = LaunchConfiguration('rviz')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    yaw = LaunchConfiguration('Y')

    # Generate URDF from xacro at launch time.
    # use_sim:=true enables gz_ros2_control and the Gazebo sensors plugins.
    robot_description = Command([
        TextSubstitution(text='xacro '),
        xacro_file,
        TextSubstitution(text=' use_sim:=true'),
    ])
    robot_description_param = ParameterValue(robot_description, value_type=str)

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            ])
        ),
        launch_arguments={
            'gz_args': gz_args,
        }.items(),
    )

    # Publish the URDF TF tree (fixed joints like base_link->chassis->laser do not
    # require joint_states and will always be available for RViz).
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_description_param,
        }],
    )

    # Spawn the robot into Gazebo Sim.
    # We spawn from the URDF string directly to avoid relying on a /robot_description topic.
    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        parameters=[{
            'name': robot_name,
            'allow_renaming': True,
            'string': robot_description_param,
            'x': x,
            'y': y,
            'z': z,
            'Y': yaw,
        }],
    )

    # Give Gazebo a moment to start before spawning
    spawn_delayed = TimerAction(period=2.0, actions=[spawn])

    # Bridge Gazebo <-> ROS topics using YAML config (scan + optional points)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_bridge_lidar',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'config_file': bridge_config_path,
        }],
    )

    # Spawn ros2_control controllers (delayed to let Gazebo + gz_ros2_control start up).
    # joint_state_broadcaster publishes /joint_states so robot_state_publisher can
    # compute the full TF tree. diff_drive_controller publishes the odom->base_link TF
    # which SLAM toolbox needs.
    joint_state_broadcaster_spawner = TimerAction(
        period=4.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen',
        )]
    )

    diff_drive_spawner = TimerAction(
        period=4.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['diff_drive_controller'],
            output='screen',
        )]
    )

    rviz_config = os.path.join(pkg_slam, 'config', 'slam.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        condition=IfCondition(rviz),
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
    )

    # Let Gazebo resolve model://larry_description/meshes/... URIs.
    # GZ_SIM_RESOURCE_PATH must point to the parent of the package share dir.
    set_gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(larry_description_share),
    )

    return LaunchDescription([
        set_gz_resource_path,
        DeclareLaunchArgument(
            'robot_name',
            default_value='Larry 2.0',
            description='Name for the spawned robot entity in Gazebo',
        ),
        DeclareLaunchArgument(
            'gz_args',
            default_value=f'-r {default_world}',
            description='Arguments passed to `gz sim` (example: "-r -s <world.sdf>")',
        ),
        DeclareLaunchArgument('x', default_value='0.0', description='Spawn X'),
        DeclareLaunchArgument('y', default_value='0.0', description='Spawn Y'),
        DeclareLaunchArgument('z', default_value='0.2', description='Spawn Z'),
        DeclareLaunchArgument('Y', default_value='0.0', description='Spawn yaw (rad)'),
        DeclareLaunchArgument('rviz', default_value='false', description='Open RViz'),
        gz_sim,
        robot_state_publisher,
        spawn_delayed,
        bridge,
        joint_state_broadcaster_spawner,
        diff_drive_spawner,
        rviz_node,
    ])
