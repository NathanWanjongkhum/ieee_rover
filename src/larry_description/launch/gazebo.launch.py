import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

# ros2 run ros_gz_bridge parameter_bridge /cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist

def generate_launch_description():
    pkg_path = get_package_share_directory('larry_description')

    gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(pkg_path)
    )

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(pkg_path, 'launch', 'rsp.launch.py')]),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
        launch_arguments={'gz_args': '-r empty.sdf'}.items()
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'larry_robot', '-z', '0.15'],
        output='screen'
    )

    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    load_diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
    )

    return LaunchDescription([
        gz_resource_path,
        rsp, 
        gazebo, 
        spawn_robot,
        load_joint_state_broadcaster,
        load_diff_drive_controller 
    ])