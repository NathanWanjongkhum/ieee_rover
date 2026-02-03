

colcon build --symlink-install

source install/setup.bash
    
ros2 launch lidar lidar_sim_launch.py
