import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, TextSubstitution

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_lidar = get_package_share_directory('lidar')

    xacro_file = os.path.join(pkg_lidar, 'description', 'robot.urdf.xacro')
    bridge_config_path = os.path.join(pkg_lidar, 'config', 'gpu_lidar.yaml')
    default_world = os.path.join(pkg_lidar, 'worlds', 'playground.sdf')

    robot_name = LaunchConfiguration('robot_name')
    gz_args = LaunchConfiguration('gz_args')
    rviz = LaunchConfiguration('rviz')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    yaw = LaunchConfiguration('Y')
    use_ros2_control = LaunchConfiguration('use_ros2_control')
    render_engine = LaunchConfiguration('render_engine')

    # Generate URDF from xacro at launch time
    robot_description = Command([
        TextSubstitution(text='xacro '),
        xacro_file,
        TextSubstitution(text=' sim_mode:=true'),
        TextSubstitution(text=' use_ros2_control:='),
        use_ros2_control,
        TextSubstitution(text=' render_engine:='),
        render_engine,
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

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        condition=IfCondition(rviz),
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_name',
            default_value='Larry 2.0',
            description='This is a lidar bot that does lidar things',
        ),
        DeclareLaunchArgument(
            'gz_args',
            default_value=f'-r {default_world}',
            description='Arguments passed to `gz sim` (example: "-r -s <world.sdf>")',
        ),
        DeclareLaunchArgument(
            'use_ros2_control',
            default_value='true',
            description='Enable gz_ros2_control plugin in the robot description',
        ),
        DeclareLaunchArgument(
            'render_engine',
            default_value='ogre2',
            description='Render engine for gz::sim::systems::Sensors (ogre1 or ogre2)',
        ),
        DeclareLaunchArgument('x', default_value='0.0', description='Spawn X'),
        DeclareLaunchArgument('y', default_value='0.0', description='Spawn Y'),
        DeclareLaunchArgument('z', default_value='0.2', description='Spawn Z'),
        DeclareLaunchArgument('Y', default_value='0.0', description='Spawn yaw (rad)'),
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz'),
        gz_sim,
        robot_state_publisher,
        spawn_delayed,
        bridge,
        rviz_node,
    ])