# Slam Package

ROS 2 Jazzy package for SLAM (Simultaneous Localization and Mapping) using Gazebo simulation and slam_toolbox. Spawns the rover in Gazebo, bridges LiDAR data to ROS, runs `diff_drive_controller` for odometry, and builds a live map.

---

## Prerequisites

Install required ROS 2 packages if not already present:

```bash
sudo apt update
sudo apt install \
  ros-jazzy-slam-toolbox \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-diff-drive-controller \
  ros-jazzy-joint-state-broadcaster \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-xacro \
  ros-jazzy-rviz2
```

---

## Building

From the root of the workspace (`ieee_rover/`):

```bash
colcon build --packages-select Slam
source install/setup.bash
```

---

## Launching SLAM in Simulation

`slam_launch.py` is the main entry point. It starts everything:
- Gazebo with the rover and playground world
- LiDAR + clock bridge (Gazebo → ROS)
- `diff_drive_controller` and `joint_state_broadcaster` for odometry
- `slam_toolbox` async mapping node
- RViz for visualization

```bash
ros2 launch Slam slam_launch.py
```

Gazebo will open with the rover spawned. After ~4 seconds the controllers activate and SLAM begins building a map as soon as the robot moves.

---

## Viewing the Map in RViz

RViz opens automatically. To see the SLAM map:

1. Click **Add** → **By Topic** → select `/map` → **Map**
2. Set **Fixed Frame** to `map` (top-left panel under Global Options)
3. Optionally add:
   - **By Topic** → `/scan` → **LaserScan** (set Reliability to **Best Effort**)
   - **By Display Type** → **TF** (to see the coordinate frames)

The map updates live as the robot moves.

---

## Moving the Robot

To drive the robot and build a map, publish velocity commands on `/diff_drive_controller/cmd_vel_unstamped`:

```bash
# Drive forward
ros2 topic pub --once /diff_drive_controller/cmd_vel_unstamped geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.0}}"

# Turn left
ros2 topic pub --once /diff_drive_controller/cmd_vel_unstamped geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}"

# Stop
ros2 topic pub --once /diff_drive_controller/cmd_vel_unstamped geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}"
```

Or use teleop keyboard in a second terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/diff_drive_controller/cmd_vel_unstamped
```

---

## Getting the Map Data

### Check active topics

```bash
ros2 topic list | grep map
```

You should see `/map` (occupancy grid) and `/map_metadata`.

### Print map info

```bash
ros2 topic echo /map_metadata
```

### Save the map to a file

Use `map_saver_cli` from `nav2_map_server`:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_map
```

This saves two files:
- `~/my_map.pgm` — grayscale image of the map (white = free, black = obstacle, grey = unknown)
- `~/my_map.yaml` — metadata (resolution, origin, etc.)

### Reload a saved map later

```bash
ros2 run nav2_map_server map_server --ros-args -p map_yaml_filename:=~/my_map.yaml
```

---

## Simulation-Only Launch (No SLAM)

To launch Gazebo + LiDAR + controllers without SLAM (useful for testing sensors):

```bash
ros2 launch Slam lidar_sim_launch.py rviz:=true
```

---

## Hardware LiDAR (Real Robot)

To run with the physical HLS-LFCD LDS sensor instead of simulation:

```bash
# One-time permission fix (requires reboot to take effect permanently)
sudo usermod -a -G dialout $USER

# Or per-session
sudo chmod a+rw /dev/ttyUSB0

# Launch
ros2 launch Slam lidar_launch.py
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Controllers fail to activate | Wait longer — Gazebo may not have fully loaded the hardware interfaces yet. The spawners have a 4s delay; if it still fails try restarting. |
| `/map` topic not appearing | Check `ros2 topic list`; SLAM toolbox may still be configuring. Look for `[SLAM] slam_toolbox configured — activating.` in the launch output. |
| RViz shows no laser dots | Set Reliability to **Best Effort** on the LaserScan display, and add it via **By Topic** not **By Display Type**. |
| `No TF data` in RViz | Set Fixed Frame to `map`. If the frame still doesn't exist, the controllers may not have activated — check for spawner errors in the launch output. |
| Gazebo world not found | Run `colcon build` and `source install/setup.bash` before launching. |
