cmake_minimum_required(VERSION 3.16)
project(Slam LANGUAGES CXX)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── Hybrid build: CMake for C++ plugin + Python for teleop scripts ───────────
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

# Python module — installs Slam/ package to site-packages
ament_python_install_package(${PROJECT_NAME})

# Python console script (ros2 run Slam teleop_wasd)
install(PROGRAMS Slam/teleop_wasd.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME teleop_wasd
)

# ── larry_hardware shared library ────────────────────────────────────────────
add_library(larry_hardware SHARED
  hardware/larry_system.cpp
)

target_compile_features(larry_hardware PUBLIC cxx_std_17)

target_include_directories(larry_hardware PUBLIC
  $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/hardware/include>
  $<INSTALL_INTERFACE:include/Slam>
)

target_link_libraries(larry_hardware PUBLIC
  hardware_interface::hardware_interface
  pluginlib::pluginlib
  rclcpp::rclcpp
  rclcpp_lifecycle::rclcpp_lifecycle
)

# ── Install ──────────────────────────────────────────────────────────────────
install(DIRECTORY hardware/include/
  DESTINATION include/Slam
)

install(TARGETS larry_hardware
  EXPORT export_larry_hardware
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY launch config description worlds
  DESTINATION share/${PROJECT_NAME}
)

install(FILES resource/${PROJECT_NAME}
  DESTINATION share/ament_index/resource_index/packages
)

install(FILES package.xml
  DESTINATION share/${PROJECT_NAME}
)

# ── Pluginlib export ──────────────────────────────────────────────────────────
pluginlib_export_plugin_description_file(hardware_interface larry_hardware.xml)

# ── Exports ───────────────────────────────────────────────────────────────────
ament_export_targets(export_larry_hardware HAS_LIBRARY_TARGET)
ament_export_dependencies(
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
