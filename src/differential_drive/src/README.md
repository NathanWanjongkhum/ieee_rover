# differential_drive_controller

   *DiffBot*, or ''Differential Mobile Robot'', is a simple mobile base with differential drive.
   The robot is basically a box moving according to differential drive kinematics.

Find the documentation in [doc/userdoc.rst](doc/userdoc.rst) or on [control.ros.org](https://control.ros.org/master/doc/ros2_control_demos/example_2/doc/userdoc.html).

### Quick Start
As always start by building the project from the root of the workspace by running
```bash
colcon build --symlink-install --packages-select differential_drive_control
```
Now whenever you open a new terminal you will need to source the package 
```bash
source install/setup.bash
```
Now launch the riv enviroment
```bash
ros2 launch differential_drive_controller diffbot.launch.py
```
You should now see the robot stationary in the world so to get it moving keep the launch program running and in another terminal run
```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/TwistStamped "
  header: auto
  twist:
    linear:
      x: 0.7
      y: 0.0
      z: 0.0
    angular:
      x: 0.0
      y: 0.0
      z: 1.0"
```
If everything worked it should now be moving in a circle every tick.

If you need more information use the web link at the start of the document.