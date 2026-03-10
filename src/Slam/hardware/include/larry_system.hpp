// Copyright 2024 Larry Robot Team
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef LARRY_HARDWARE__LARRY_SYSTEM_HPP_
#define LARRY_HARDWARE__LARRY_SYSTEM_HPP_

#include <string>
#include <termios.h>  // POSIX serial — available on all Linux targets (Jetson Nano / desktop)

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/state.hpp"

namespace larry_hardware
{

// ─────────────────────────────────────────────────────────────────────────────
// Minimal POSIX serial port helper
//
// Wraps a raw file descriptor opened in 8N1 raw mode. read_line() uses
// select() so it never blocks the ros2_control update thread for longer than
// timeout_ms milliseconds.
// ─────────────────────────────────────────────────────────────────────────────
class SerialPort
{
public:
  SerialPort() = default;
  ~SerialPort() { close(); }

  // Non-copyable
  SerialPort(const SerialPort &) = delete;
  SerialPort & operator=(const SerialPort &) = delete;

  /// Open and configure the port at the given baud rate (8N1, raw mode).
  /// Returns true on success, false on any OS error (errno is set).
  bool open(const std::string & device, int baud);

  /// Close the file descriptor (safe to call when already closed).
  void close();

  bool is_open() const { return fd_ >= 0; }

  /// Write all bytes of msg to the port. Returns true if all bytes written.
  bool write_line(const std::string & msg);

  /// Read bytes until '\n' (stripping '\r') or timeout_ms elapses.
  /// Returns the line (without the newline) or an empty string on timeout.
  std::string read_line(int timeout_ms = 100);

private:
  int fd_{-1};

  /// Map an integer baud rate to a termios B* constant.
  static speed_t baud_to_speed(int baud);
};

// ─────────────────────────────────────────────────────────────────────────────
// LarrySystemHardware
//
// ros2_control SystemInterface for a 6-wheel differential drive robot.
//
// Robot topology (joint order from larry.ros2_control.xacro):
//   Index 0: front_left_wheel_joint   |
//   Index 1: mid_left_wheel_joint     | left side
//   Index 2: rear_left_wheel_joint    |
//   Index 3: front_right_wheel_joint  |
//   Index 4: mid_right_wheel_joint    | right side
//   Index 5: rear_right_wheel_joint   |
//
// All joints on the same side receive identical velocity commands from the
// diff_drive_controller and share one encoder source (left or right).
//
// Serial protocol (ASCII, terminated with \r\n):
//   ROS → MCU  "M<L> <R>\r\n"     velocity command, integers -255..255
//   ROS → MCU  "E\r\n"            request encoder counts
//   MCU → ROS  "E<L> <R>\r\n"     cumulative signed tick counts
//
// URDF parameters (all optional — defaults are shown):
//   serial_port         /dev/ttyUSB0
//   baud_rate           57600
//   enc_counts_per_rev  11131
//   loop_rate           30.0   (must match controllers.yaml update_rate)
// ─────────────────────────────────────────────────────────────────────────────
class LarrySystemHardware : public hardware_interface::SystemInterface
{
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(LarrySystemHardware)

  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareComponentInterfaceParams & params) override;

  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_cleanup(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  // ── URDF parameters ────────────────────────────────────────────────────────
  std::string serial_port_{"/dev/ttyUSB0"};
  int baud_rate_{57600};
  int enc_counts_per_rev_{11131};
  double loop_rate_{30.0};

  // ── Encoder baseline (set at activation so position starts from 0) ─────────
  long long prev_left_ticks_{0};
  long long prev_right_ticks_{0};

  // ── Serial port ────────────────────────────────────────────────────────────
  SerialPort serial_;

  // ── Joint layout constants ─────────────────────────────────────────────────
  static constexpr std::size_t NUM_JOINTS = 6;
  static constexpr std::size_t NUM_LEFT   = 3;  // joints 0..2
  // joints 3..5 are right side

  // Ordered to match larry.ros2_control.xacro joint declaration order.
  static constexpr const char * JOINT_NAMES[NUM_JOINTS] = {
    "front_left_wheel_joint",
    "mid_left_wheel_joint",
    "rear_left_wheel_joint",
    "front_right_wheel_joint",
    "mid_right_wheel_joint",
    "rear_right_wheel_joint",
  };
};

}  // namespace larry_hardware

#endif  // LARRY_HARDWARE__LARRY_SYSTEM_HPP_
