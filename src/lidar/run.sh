

colcon build --packages-select lidar

source install/setup.bash
    
ros2 launch lidar lidar_sim_launch.py
