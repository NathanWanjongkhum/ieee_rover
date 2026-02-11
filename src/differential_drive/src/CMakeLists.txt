cmake_minimum_required(VERSION 3.16)
project(differential_drive_controller LANGUAGES CXX)

find_package(ros2_control_cmake REQUIRED)
set_compiler_options()
export_windows_symbols()

# find dependencies
set(THIS_PACKAGE_INCLUDE_DEPENDS
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
)

# Specify the required version of ros2_control
find_package(controller_manager 4.0.0)
# Handle the case where the required version is not found
if(NOT controller_manager_FOUND)
  message(FATAL_ERROR "ros2_control version 4.0.0 or higher is required. "
  "Are you using the correct branch of the ros2_control_demos repository?")
endif()

# find dependencies
find_package(backward_ros REQUIRED)
find_package(ament_cmake REQUIRED)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

## COMPILE
add_library(
  differential_drive_controller
  SHARED
  hardware/diffbot_system.cpp
)
target_compile_features(differential_drive_controller PUBLIC cxx_std_17)
target_include_directories(differential_drive_controller PUBLIC
$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/hardware/include>
$<INSTALL_INTERFACE:include/differential_drive_controller>
)
target_link_libraries(differential_drive_controller PUBLIC
  hardware_interface::hardware_interface
  pluginlib::pluginlib
  rclcpp::rclcpp
  rclcpp_lifecycle::rclcpp_lifecycle
)

# Install Header Files
install(
  DIRECTORY hardware/include/
  DESTINATION include/
)

# Install Resources
install(
  DIRECTORY 
    bringup 
    description 
    hardware
  DESTINATION share/${PROJECT_NAME}
)

# Export the Plugin
pluginlib_export_plugin_description_file(hardware_interface differential_drive_controller.xml)

install(TARGETS differential_drive_controller
  EXPORT export_differential_drive_controller
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(example_2_urdf_xacro test/test_urdf_xacro.py)

  # Integration (launch) tests
  find_package(ament_cmake_ros REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)
  function(add_ros_isolated_launch_test path)
    set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
    add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
  endfunction()
  add_ros_isolated_launch_test(test/test_view_robot_launch.py)
  add_ros_isolated_launch_test(test/test_diffbot_launch.py)
endif()

## EXPORTS
ament_export_targets(export_differential_drive_controller HAS_LIBRARY_TARGET)
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()
