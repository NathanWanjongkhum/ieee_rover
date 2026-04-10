# IEEE Rover — Project State

> Last updated: 2026-04-10 | Branch: `slam-2` | ROS 2 target: **Jazzy**

---

## SLAM

**Status: COMPLETE**

- **Implementation:** `slam_toolbox` — `async_slam_toolbox_node`
- **Config:** [src/Slam/config/slam_params.yaml](src/Slam/config/slam_params.yaml)
- **Solver:** CeresSolver (`SPARSE_NORMAL_CHOLESKY`)
- **TF chain:** `map → odom → base_link`
- **Scan topic:** `/scan`
- **Resolution:** 0.05 m | **Max range:** 12.0 m
- **Min travel before update:** 0.2 m / 0.2 rad
- **Loop closure:** enabled with configured thresholds

**Launch files:**

| File | Purpose |
|------|---------|
| [src/Slam/launch/slam_sim.launch.py](src/Slam/launch/slam_sim.launch.py) | Simulation SLAM (uses sim time) |
| [src/Slam/launch/slam_robot.launch.py](src/Slam/launch/slam_robot.launch.py) | Hardware SLAM (wall-clock time) |

Both manage the `slam_toolbox` node through the ROS 2 lifecycle and include RViz with automatic map display.

---

## Nav2

**Status: COMPLETE**

- **Config:** [src/ieee_rover/config/nav2_params.yaml](src/ieee_rover/config/nav2_params.yaml)

**Components configured:**

| Component | Details |
|-----------|---------|
| BT Navigator | Default nav2 BT (navigate_w_replanning_and_recovery) |
| Global Planner | Navfn (Dijkstra, A* disabled) |
| Local Controller | DWB with RotateToGoal, PathAlign, GoalAlign, PathDist, GoalDist critics |
| Local Costmap | Rolling 3×3 m window, 0.05 m resolution, voxel layer |
| Global Costmap | Static + obstacle + inflation layers, tracks unknown space |
| Inflation Radius | 0.55 m |
| Recovery Behaviors | spin, backup, drive_on_heading, assisted_teleop, wait |
| Velocity Smoother | 20 Hz, open-loop, max 0.26 m/s |
| Smoother Server | SimpleSmoother |
| Waypoint Follower | WaitAtWaypoint |
| AMCL | Configured (for localization-only mode with a pre-built map) |

**Launch files:**

| File | Purpose |
|------|---------|
| [src/Slam/launch/nav2_sim.launch.py](src/Slam/launch/nav2_sim.launch.py) | Simulation: SLAM + Gazebo + Nav2 + twist_mux |
| [src/Slam/launch/nav2_robot.launch.py](src/Slam/launch/nav2_robot.launch.py) | Hardware: SLAM + Nav2 + twist_mux |

**Velocity command routing:**
```
nav2 controller_server → cmd_vel_nav
velocity_smoother      → cmd_vel          (final Twist output)
twist_mux              → diff_drive_controller/cmd_vel  (TwistStamped, use_stamped=true)
```
twist_mux priority: joystick (100) > tracker (20) > navigation/nav2 (10)

**Localization-only mode (pre-built map):**
Use `nav2_bringup/bringup_launch.py` instead of `navigation_launch.py`, and set `map_server.ros__parameters.yaml_filename` to your saved map path.

---

## Launch Files

| File | Purpose | Status |
|------|---------|--------|
| [src/Slam/launch/nav2_sim.launch.py](src/Slam/launch/nav2_sim.launch.py) | Full sim + SLAM + Nav2 entry point | Working |
| [src/Slam/launch/nav2_robot.launch.py](src/Slam/launch/nav2_robot.launch.py) | Full hardware + SLAM + Nav2 entry point | Working |
| [src/Slam/launch/slam_sim.launch.py](src/Slam/launch/slam_sim.launch.py) | Sim + SLAM only (no Nav2) | Working |
| [src/Slam/launch/slam_robot.launch.py](src/Slam/launch/slam_robot.launch.py) | Hardware + SLAM only (no Nav2) | Working |
| [src/Slam/launch/sim.launch.py](src/Slam/launch/sim.launch.py) | Gazebo + bridge + controllers | Working |
| [src/Slam/launch/robot.launch.py](src/Slam/launch/robot.launch.py) | Hardware bringup (RSP + controllers + LiDAR) | Working |
| [src/Slam/launch/rsp.launch.py](src/Slam/launch/rsp.launch.py) | Robot State Publisher (sim and hardware) | Working |
| [src/ieee_rover/launch/sim_launch.py](src/ieee_rover/launch/sim_launch.py) | Alt sim with twist_mux + image republishers | Working (refs `sim_config.rviz` which may be missing) |
| [src/ieee_rover/launch/robot_launch.py](src/ieee_rover/launch/robot_launch.py) | Hardware bringup | **Broken** — references `rsp_launch.py` and `joystick_launch.py` which do not exist |
| [src/larry_description/launch/gazebo.launch.py](src/larry_description/launch/gazebo.launch.py) | Legacy Gazebo launcher | Legacy/reference |
| [src/larry_description/launch/rsp.launch.py](src/larry_description/launch/rsp.launch.py) | Legacy RSP | Legacy/reference |
| [src/larry_description/launch/display.launch.py](src/larry_description/launch/display.launch.py) | RViz display with joint state GUI | Legacy/reference |
| [src/lidar/launch/gpu_lidar_bridge.launch.xml](src/lidar/launch/gpu_lidar_bridge.launch.xml) | Legacy LiDAR bridge | Legacy/reference |

**Primary entry points:**
- Simulation (SLAM + Nav2): `ros2 launch Slam nav2_sim.launch.py`
- Hardware (SLAM + Nav2): `ros2 launch Slam nav2_robot.launch.py`
- Simulation (SLAM only): `ros2 launch Slam slam_sim.launch.py`
- Hardware (SLAM only): `ros2 launch Slam slam_robot.launch.py`

---

## Motor Controller / Simulation

### Hardware Controller

- **Plugin:** Custom `LarrySystemHardware` (`ros2_control` `SystemInterface`)
- **Source:** [src/Slam/hardware/larry_system.cpp](src/Slam/hardware/larry_system.cpp)
- **Hardware description:** [src/Slam/larry_hardware.xml](src/Slam/larry_hardware.xml)
- **Transport:** UART serial → `/dev/ttyUSB0` @ 57,600 baud
- **Command format:** `M<left_pwm> <right_pwm>\r\n` (range −255 to +255)
- **Feedback format:** `E<left_ticks> <right_ticks>\r\n` (cumulative signed encoder counts)
- **Encoder resolution:** 11,131 counts/rev
- **Control loop rate:** 30 Hz

### Simulation

- **Simulator:** Gazebo (`ros_gz_sim` / `ros_gz_bridge`)
- **ros2_control plugin:** `gz_ros2_control/GazeboSimSystem`
- **World:** [src/Slam/worlds/playground.sdf](src/Slam/worlds/playground.sdf)

**Simulated sensors:**

| Sensor | Details |
|--------|---------|
| GPU LiDAR | 360 samples, 360° horizontal, 10 Hz, 0.1–12 m range |
| Depth Camera | 640×480, 10 Hz, near=0.02 m, far=300 m |

### diff_drive_controller

- **Controller:** `diff_drive_controller/DiffDriveController`
- **Config (sim):** [src/Slam/config/controllers.yaml](src/Slam/config/controllers.yaml)
- **Config (hardware):** [src/Slam/config/controllers_robot.yaml](src/Slam/config/controllers_robot.yaml)
- **Command topic:** `/diff_drive_controller/cmd_vel` (`TwistStamped`)
- **Odometry topic:** `/odom` (`nav_msgs/Odometry`)
- **TF published:** `odom → base_link`

### Input multiplexing

- **Twist Mux:** [src/ieee_rover/config/twist_mux.yaml](src/ieee_rover/config/twist_mux.yaml) — priority-based merging of joystick, teleop, and autonomous commands
- **Twist Stamper:** Adds timestamps to `Twist` before forwarding to `TwistStamped` controller input
- **Joystick config:** [src/ieee_rover/config/joystick.yaml](src/ieee_rover/config/joystick.yaml)

---

## URDF

**Status: COMPLETE (minor physics placeholder noted)**

**Primary robot description:** [src/Slam/description/larry.urdf.xacro](src/Slam/description/larry.urdf.xacro)

| Xacro file | Contents |
|------------|---------|
| [larry.urdf.xacro](src/Slam/description/larry.urdf.xacro) | Top-level assembly |
| [larry_core.xacro](src/Slam/description/larry_core.xacro) | Chassis body (30+ mesh-based visual/collision definitions) |
| [larry_wheels.xacro](src/Slam/description/larry_wheels.xacro) | 6 wheels (3 per side, continuous joints) |
| [larry.ros2_control.xacro](src/Slam/description/larry.ros2_control.xacro) | ros2_control hardware interface declaration |
| [lidar.xacro](src/Slam/description/lidar.xacro) | LiDAR link + Gazebo GPU sensor plugin |
| [depth_camera.xacro](src/Slam/description/depth_camera.xacro) | Camera link + optical frame + Gazebo depth sensor plugin |

**Links:** `base_link`, `part_1` (chassis), `front/mid/rear_left/right_wheel_link` (×6), `laser`, `camera_link`, `camera_link_optical`

**Key dimensions:**
- Wheel radius: 0.06 m | Wheel length: 0.04 m | Wheel mass: 0.5 kg each
- Track width (separation): 0.66 m (left x=−0.16, right x=0.50)

**Known issues:**
- `part_1` inertial mass is set to `1e-09 kg` — this is a placeholder and will produce unrealistic physics. Needs to be updated with the actual chassis mass and correct inertia tensor.
- Collision geometry uses mesh files, which is computationally expensive in Gazebo. Consider simplified collision primitives.

**Secondary URDF (ieee_rover):** [src/ieee_rover/description/robot.urdf.xacro](src/ieee_rover/description/robot.urdf.xacro) — simpler 2-wheel reference design, not the primary robot.

---

## Package Overview

```
src/
├── Slam/                   ← PRIMARY package (SLAM + hardware + sim)
│   ├── hardware/           LarrySystemHardware C++ plugin
│   ├── description/        larry.urdf.xacro + sensor xacros
│   ├── config/             slam_params.yaml, controllers*.yaml, bridge configs
│   ├── launch/             slam_robot, slam_sim, robot, sim, rsp
│   └── worlds/             playground.sdf
│
├── ieee_rover/             ← SECONDARY package (nav2 config, twist_mux, alt sim)
│   ├── description/        robot.urdf.xacro (2-wheel reference)
│   ├── config/             nav2_params.yaml, joystick.yaml, twist_mux.yaml
│   └── launch/             sim_launch.py (works), robot_launch.py (broken)
│
├── larry_description/      ← LEGACY reference
├── lidar/                  ← LEGACY reference
└── differential_drive/     ← REFERENCE implementation (DiffBot tutorial)
```

---

## Open Issues / What Needs Work

| Item | Priority | Notes |
|------|----------|-------|
| Fix `robot_launch.py` | Medium | Remove/replace references to missing `rsp_launch.py` and `joystick_launch.py` |
| Fix chassis inertia in URDF | Medium | `part_1` has `1e-09 kg` mass — needs real values for accurate physics |
| Collision simplification | Low | Mesh-based collision on chassis is expensive; primitives would be faster |
| Package metadata | Low | 3 packages have `TODO` in `package.xml` (`ieee_rover`, `larry_description`, `lidar`) |
| `sim_config.rviz` | Low | Referenced by `ieee_rover/sim_launch.py` — verify it exists or create it |

---

## Hardware Setup Notes

- Serial motor controller: `/dev/ttyUSB0`
- HLS-LFCD LiDAR: `/dev/ttyUSB1`
- Both ports are configurable as launch arguments
- Serial access requires dialout group: `sudo usermod -a -G dialout $USER`

## Build

```bash
# Primary packages
colcon build --packages-select Slam

# Everything
colcon build
```