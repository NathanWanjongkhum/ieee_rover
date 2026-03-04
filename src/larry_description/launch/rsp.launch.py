import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_path = get_package_share_directory('larry_description')
    xacro_file = os.path.join(pkg_path, 'urdf', 'robot.urdf')
    
    doc = xacro.process_file(xacro_file)
    
    params = {'robot_description': doc.toxml(), 'use_sim_time': False}
    
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    return LaunchDescription([
        node_robot_state_publisher
    ])