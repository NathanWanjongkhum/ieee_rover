import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # Define Launch Configurations (Variables)
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim = LaunchConfiguration('use_sim')

    # Declare Launch Arguments
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_use_sim = DeclareLaunchArgument(
        'use_sim',
        default_value='false',
        description='Enable Gazebo hardware plugins in the URDF'
    )

    # Setup Paths
    pkg_path = get_package_share_directory('larry_description')
    xacro_file = os.path.join(pkg_path, 'urdf', 'larry.urdf.xacro')

    # 4. Process Xacro
    robot_description_content = Command(
        ['xacro ', xacro_file, ' use_sim:=', use_sim]
    )
    
    params = {
        'robot_description': ParameterValue(robot_description_content, value_type=str),
        'use_sim_time': use_sim_time
    }

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_sim,
        node_robot_state_publisher
    ])