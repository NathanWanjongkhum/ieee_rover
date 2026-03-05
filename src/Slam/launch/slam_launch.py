import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, IncludeLaunchDescription,
                            LogInfo, RegisterEventHandler)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (AndSubstitution, LaunchConfiguration,
                                  NotSubstitution, PathJoinSubstitution)
from launch.events import matches_action
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from launch_ros.substitutions import FindPackageShare
from lifecycle_msgs.msg import Transition


def generate_launch_description():
    pkg_slam = get_package_share_directory('Slam')
    slam_params_file = os.path.join(pkg_slam, 'config', 'slam_params.yaml')

    autostart = LaunchConfiguration('autostart')
    use_lifecycle_manager = LaunchConfiguration('use_lifecycle_manager')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Automatically start the slam_toolbox node through its lifecycle.')
    declare_use_lifecycle_manager = DeclareLaunchArgument(
        'use_lifecycle_manager', default_value='false',
        description='Enable bond connection during node activation (nav2 lifecycle manager).')

    # Include the full Gazebo simulation: robot, LiDAR bridge, and controllers.
    # rviz is enabled here so you can see the map being built.
    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('Slam'),
                'launch',
                'lidar_sim_launch.py',
            ])
        ),
        launch_arguments={
            'rviz': 'true',
        }.items(),
    )

    # SLAM Toolbox async mapping node, managed as a lifecycle node so we can
    # reliably configure then activate it after the rest of the system is up.
    slam_toolbox_node = LifecycleNode(
        parameters=[
            slam_params_file,
            {
                'use_lifecycle_manager': use_lifecycle_manager,
                'use_sim_time': True,
            }
        ],
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        namespace='',
    )

    # Emit a configure transition as soon as the node is launched (when autostart=true).
    configure_event = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=matches_action(slam_toolbox_node),
            transition_id=Transition.TRANSITION_CONFIGURE,
        ),
        condition=IfCondition(AndSubstitution(autostart, NotSubstitution(use_lifecycle_manager)))
    )

    # Once configured and inactive, activate the node.
    activate_event = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=slam_toolbox_node,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                LogInfo(msg='[SLAM] slam_toolbox configured — activating.'),
                EmitEvent(event=ChangeState(
                    lifecycle_node_matcher=matches_action(slam_toolbox_node),
                    transition_id=Transition.TRANSITION_ACTIVATE,
                )),
            ]
        ),
        condition=IfCondition(AndSubstitution(autostart, NotSubstitution(use_lifecycle_manager)))
    )

    ld = LaunchDescription()

    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_use_lifecycle_manager)
    ld.add_action(sim)
    ld.add_action(slam_toolbox_node)
    ld.add_action(configure_event)
    ld.add_action(activate_event)

    return ld
