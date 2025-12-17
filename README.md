# ROS File Structure

The ROS project is organized hierarchically, starting with the top-level workspace and containing multiple individual packages.

-----

## Top-level Organization (Workspace)

The workspace is the project root, often referred to as the project root.

```
workspace/
├── src/
├── build/
├── devel/
└── install/
```

  * **src/**: This is the **source space** where all the ROS packages reside.
  * **build/**: The **build space** is where CMake is invoked to build the packages in the `src` directory. It contains build files, intermediate files, and other artifacts generated during the compilation process.
  * **devel/**: The **development space** contains the executables and libraries built from the packages. It also includes setup files that can be sourced to add the development space to the ROS environment.
  * **install/**: The **install space** is used when you want to install the built packages.

### Build Commands

Run the following commands at the project root:

1.  `source install/setup.bash`: Applies the project's ROS 2 overlay.
2.  `colcon build --symlink-install`: Builds packages using symbolic links.

-----

## Package-level Organization

An ROS package is a set of files that encapsulate a specific piece of functionality. The following shows a common package tree, although not all folders are required in every package. Some directories (like `msg`, `srv`, `scripts`) should only be added when relevant.

```
package_name/
├── CMakeLists.txt
├── package.xml
├── LICENSE.md
├── README.md
├── include/package_name/
├── src/
├── scripts/
├── launch/
├── config/
├── msg/
├── srv/
├── action/
└── test/
```

### Key Package Directories and Files

| Directory/File | Purpose |
| :--- | :--- |
| **`CMakeLists.txt`** | The CMake build file that defines how the package should be built, including files to compile, dependencies, and installation instructions. |
| **`package.xml`** | An XML file containing metadata about the package, such as its name, version, description, maintainer information, license, and dependencies (build, run, and test). |
| **`include/package_name/`** | Contains C++ header files (`.h` or `.hpp`). The nested directory prevents naming conflicts when headers are installed system-wide. |
| **`src/`** | Contains C++ source files (`.cpp`) where the main functionality of C++ nodes is implemented. |
| **`scripts/`** | Contains executable scripts, often written in Python, which can be ROS nodes or utility scripts. |
| **`launch/`** | Stores XML or Python launch files (`.launch` or `*_launch.py`) that allow you to start multiple ROS nodes, set parameters, and configure the ROS system. The `*_launch.py` suffix is required to be recognized by `ros2 launch`. |
| **`config/`** | Stores configuration files, often in YAML format, which can contain parameters for nodes. |
| **`msg/`** | Stores custom message type definitions in `.msg` files. |
| **`srv/`** | Stores custom service type definitions in `.srv` files, which allow request-response interactions. |
| **`action/`** | Stores action type definitions in `.action` files, used for long-running tasks that provide feedback. |
| **`test/`** | Contains unit tests and integration tests for the package. |

### Package Setup

#### Python Package

Run the following command in the `/src` directory:

`ros2 pkg create --build-type ament_python --license Apache-2.0 {package_name} --dependencies rclpy`

**Modify `setup.py`** to include launch files:

```python
import os
from glob import glob
# Other imports ...

package_name = 'py_launch_example'

setup(
    # Other parameters ...
    data_files=[
        # ... Other data files
        # Include all launch files.
        (os.path.join('share', package_name, 'launch'), glob('launch/*'))
    ]
)
```

**`package.xml` Example Dependencies:**

```xml
<test_depend>ament_cmake_pytest</test_depend>
<buildtool_depend>ament_cmake_python</buildtool_depend>
```

**`CMakeLists.txt` Example:**

```cmake
find_package(ament_cmake_python REQUIRED)
# ...
ament_python_install_package(${PROJECT_NAME})
```

#### C++ Package

Run the following command in the `/src` directory:

`ros2 pkg create --build-type ament_cmake --license Apache-2.0 {package_name} --dependencies rclcpp`

**Modify `CMakeLists.txt`** to install launch files:

```cmake
# Install launch files.
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)
```

-----

## Dependencies

The dependency manager used is **[Rosdep](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Rosdep.html)**. It uses the dependencies listed in `package.xml` as "rosdep keys" to find and install the required set of dependencies.

### Installation and Initialization

1.  **Installation:** `python3-rosdep2` (Note: **NOT** `apt-get install python3-rosdep`).
2.  **Initialization:**
      * `sudo rosdep init`: Initialize rosdep.
      * `rosdep update`: Update the locally cached rosdistro index.
      * `rosdep install --from-paths src -y --ignore-src`: Install dependencies in the workspace.

-----

## Testing

The `test/` directory contains unit and integration tests.

### Test Naming and Execution

  * **Naming Convention:** `test/test_*.py`.
  * **Running Tests:** `colcon test --ctest-args tests`.
  * **Seeing Results:** `colcon test-result --all`.

### Testing Types

  * **Unit Testing:** Focuses on individual components.
      * C++ Tutorial
      * Python Tutorial
  * **Integration Testing:** Validates the interaction between pieces of code. This often involves launching a system of one or several nodes.
      * Utilities for writing ROS 2 launch tests are provided by the `launch_testing_ros` package.

-----

## Simulation and Visualization

  * **[RViz2](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/RViz-Main.html)**: Used for visualization (`rviz2-11`).
  * **[Gazebo Harmonic](https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Gazebo/Gazebo.html)**: A simulator (`gazebo-9`).

-----