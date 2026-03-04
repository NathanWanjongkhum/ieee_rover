import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

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

    # Clock bridge for simulation time synchronization
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    # Remap the controller's command topic to match teleop_twist_keyboard
    load_diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "diff_drive_controller",
            "--controller-ros-args",
            "-r", "/diff_drive_controller/cmd_vel:=/cmd_vel"
        ],
    )

    # Sequence the startups using Event Handlers
    delay_jsb_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[load_joint_state_broadcaster],
        )
    )

    delay_ddc_after_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_joint_state_broadcaster,
            on_exit=[load_diff_drive_controller],
        )
    )

    return LaunchDescription([
        gz_resource_path,
        rsp, 
        gazebo, 
        spawn_robot,
        clock_bridge,
        delay_jsb_after_spawn,
        delay_ddc_after_jsb 
    ])