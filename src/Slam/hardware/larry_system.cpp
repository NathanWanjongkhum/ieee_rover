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

#include "larry_system.hpp"

#include <fcntl.h>
#include <sys/select.h>
#include <termios.h>
#include <unistd.h>

#include <algorithm>
#include <array>
#include <cerrno>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <sstream>
#include <string>

#include "hardware_interface/lexical_casts.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

namespace larry_hardware
{

// ─────────────────────────────────────────────────────────────────────────────
// constexpr storage (required for ODR-use before C++17 inline variables)
// ─────────────────────────────────────────────────────────────────────────────
constexpr std::size_t LarrySystemHardware::NUM_JOINTS;
constexpr std::size_t LarrySystemHardware::NUM_LEFT;
constexpr const char * LarrySystemHardware::JOINT_NAMES[LarrySystemHardware::NUM_JOINTS];

// ─────────────────────────────────────────────────────────────────────────────
// SerialPort — POSIX termios implementation
// ─────────────────────────────────────────────────────────────────────────────

speed_t SerialPort::baud_to_speed(int baud)
{
  switch (baud) {
    case 9600:   return B9600;
    case 19200:  return B19200;
    case 38400:  return B38400;
    case 57600:  return B57600;
    case 115200: return B115200;
    case 230400: return B230400;
    default:     return B57600;
  }
}

bool SerialPort::open(const std::string & device, int baud)
{
  // Open non-blocking initially so ::open() doesn't hang on a missing device
  fd_ = ::open(device.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);
  if (fd_ < 0) {
    return false;
  }

  // Switch to blocking mode for subsequent I/O
  int flags = fcntl(fd_, F_GETFL, 0);
  if (flags < 0 || fcntl(fd_, F_SETFL, flags & ~O_NONBLOCK) < 0) {
    ::close(fd_);
    fd_ = -1;
    return false;
  }

  struct termios tty {};
  if (tcgetattr(fd_, &tty) != 0) {
    ::close(fd_);
    fd_ = -1;
    return false;
  }

  speed_t speed = baud_to_speed(baud);
  cfsetispeed(&tty, speed);
  cfsetospeed(&tty, speed);

  // 8N1, raw mode, no flow control
  tty.c_cflag &= ~PARENB;          // No parity
  tty.c_cflag &= ~CSTOPB;          // 1 stop bit
  tty.c_cflag &= ~CSIZE;
  tty.c_cflag |=  CS8;             // 8 data bits
  tty.c_cflag &= ~CRTSCTS;         // No HW flow control
  tty.c_cflag |=  CREAD | CLOCAL;  // Enable receiver, ignore modem lines

  tty.c_lflag &= ~ICANON;   // Raw (byte-by-byte) mode
  tty.c_lflag &= ~ECHO;
  tty.c_lflag &= ~ECHOE;
  tty.c_lflag &= ~ECHONL;
  tty.c_lflag &= ~ISIG;    // No signals from special chars

  tty.c_iflag &= ~(IXON | IXOFF | IXANY);   // No SW flow control
  tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL);

  tty.c_oflag &= ~OPOST;   // Raw output
  tty.c_oflag &= ~ONLCR;

  // Non-blocking reads: return immediately with whatever is available.
  // We rely on select() in read_line() for the actual timeout logic.
  tty.c_cc[VMIN]  = 0;
  tty.c_cc[VTIME] = 0;

  if (tcsetattr(fd_, TCSANOW, &tty) != 0) {
    ::close(fd_);
    fd_ = -1;
    return false;
  }

  tcflush(fd_, TCIOFLUSH);
  return true;
}

void SerialPort::close()
{
  if (fd_ >= 0) {
    ::close(fd_);
    fd_ = -1;
  }
}

bool SerialPort::write_line(const std::string & msg)
{
  if (fd_ < 0) {
    return false;
  }
  ssize_t written = ::write(fd_, msg.c_str(), msg.size());
  return written == static_cast<ssize_t>(msg.size());
}

std::string SerialPort::read_line(int timeout_ms)
{
  if (fd_ < 0) {
    return {};
  }

  std::string line;
  line.reserve(32);

  auto deadline = std::chrono::steady_clock::now() +
                  std::chrono::milliseconds(timeout_ms);

  while (true) {
    auto now = std::chrono::steady_clock::now();
    if (now >= deadline) {
      break;
    }

    auto remaining_us =
      std::chrono::duration_cast<std::chrono::microseconds>(deadline - now).count();

    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(fd_, &read_fds);

    struct timeval tv;
    tv.tv_sec  = remaining_us / 1'000'000L;
    tv.tv_usec = remaining_us % 1'000'000L;

    int ret = select(fd_ + 1, &read_fds, nullptr, nullptr, &tv);
    if (ret <= 0) {
      break;  // timeout or error
    }

    char c;
    ssize_t n = ::read(fd_, &c, 1);
    if (n <= 0) {
      break;  // disconnected or error
    }

    if (c == '\n') {
      return line;
    }
    if (c != '\r') {
      line += c;
    }
  }

  return {};  // timeout — caller keeps last known state
}

// ─────────────────────────────────────────────────────────────────────────────
// LarrySystemHardware — lifecycle callbacks
// ─────────────────────────────────────────────────────────────────────────────

hardware_interface::CallbackReturn LarrySystemHardware::on_init(
  const hardware_interface::HardwareComponentInterfaceParams & params)
{
  if (hardware_interface::SystemInterface::on_init(params) !=
      hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // ── Parse URDF parameters (all have safe defaults) ──────────────────────
  if (info_.hardware_parameters.count("serial_port")) {
    serial_port_ = info_.hardware_parameters.at("serial_port");
  }
  if (info_.hardware_parameters.count("baud_rate")) {
    baud_rate_ = static_cast<int>(
      hardware_interface::stod(info_.hardware_parameters.at("baud_rate")));
  }
  if (info_.hardware_parameters.count("enc_counts_per_rev")) {
    enc_counts_per_rev_ = static_cast<int>(
      hardware_interface::stod(info_.hardware_parameters.at("enc_counts_per_rev")));
  }
  if (info_.hardware_parameters.count("loop_rate")) {
    loop_rate_ = hardware_interface::stod(info_.hardware_parameters.at("loop_rate"));
  }

  RCLCPP_INFO(
    get_logger(),
    "LarrySystemHardware init: port=%s  baud=%d  enc_cpr=%d  loop_rate=%.1f Hz",
    serial_port_.c_str(), baud_rate_, enc_counts_per_rev_, loop_rate_);

  // ── Validate joint count ─────────────────────────────────────────────────
  if (info_.joints.size() != NUM_JOINTS) {
    RCLCPP_FATAL(
      get_logger(), "Expected %zu joints, got %zu.",
      NUM_JOINTS, info_.joints.size());
    return hardware_interface::CallbackReturn::ERROR;
  }

  // ── Validate each joint: 1 velocity command, 2 state (position, velocity) ─
  for (const hardware_interface::ComponentInfo & joint : info_.joints) {
    if (joint.command_interfaces.size() != 1) {
      RCLCPP_FATAL(
        get_logger(), "Joint '%s': expected 1 command interface, got %zu.",
        joint.name.c_str(), joint.command_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.command_interfaces[0].name != hardware_interface::HW_IF_VELOCITY) {
      RCLCPP_FATAL(
        get_logger(), "Joint '%s': command interface must be velocity, got '%s'.",
        joint.name.c_str(), joint.command_interfaces[0].name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.state_interfaces.size() != 2) {
      RCLCPP_FATAL(
        get_logger(), "Joint '%s': expected 2 state interfaces, got %zu.",
        joint.name.c_str(), joint.state_interfaces.size());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION) {
      RCLCPP_FATAL(
        get_logger(), "Joint '%s': first state interface must be position, got '%s'.",
        joint.name.c_str(), joint.state_interfaces[0].name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
    if (joint.state_interfaces[1].name != hardware_interface::HW_IF_VELOCITY) {
      RCLCPP_FATAL(
        get_logger(), "Joint '%s': second state interface must be velocity, got '%s'.",
        joint.name.c_str(), joint.state_interfaces[1].name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn LarrySystemHardware::on_configure(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(get_logger(), "Configuring Larry hardware — opening %s at %d baud...",
    serial_port_.c_str(), baud_rate_);

  if (!serial_.open(serial_port_, baud_rate_)) {
    RCLCPP_FATAL(get_logger(), "Failed to open serial port '%s': %s",
      serial_port_.c_str(), std::strerror(errno));
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Zero all state and command interfaces
  for (const auto & [name, descr] : joint_state_interfaces_) {
    set_state(name, 0.0);
  }
  for (const auto & [name, descr] : joint_command_interfaces_) {
    set_command(name, 0.0);
  }

  RCLCPP_INFO(get_logger(), "Serial port opened successfully.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn LarrySystemHardware::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(get_logger(), "Activating Larry hardware...");

  // Capture the current encoder counts as a baseline so that position
  // starts at 0 from the moment the hardware interface is activated.
  serial_.write_line("E\r\n");
  std::string response = serial_.read_line(200);

  if (!response.empty() && response[0] == 'E') {
    long long l = 0, r = 0;
    if (std::sscanf(response.c_str() + 1, "%lld %lld", &l, &r) == 2) {
      prev_left_ticks_  = l;
      prev_right_ticks_ = r;
    }
  }

  // Match commands to current states (all zero after configure)
  for (const auto & [name, descr] : joint_command_interfaces_) {
    set_command(name, get_state(name));
  }

  RCLCPP_INFO(get_logger(),
    "Larry hardware activated. Encoder baseline L=%lld R=%lld",
    prev_left_ticks_, prev_right_ticks_);
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn LarrySystemHardware::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(get_logger(), "Deactivating Larry hardware — sending stop command...");

  // Command both sides to zero. Serial port is left open for fast re-activation.
  serial_.write_line("M0 0\r\n");

  RCLCPP_INFO(get_logger(), "Larry hardware deactivated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn LarrySystemHardware::on_cleanup(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(get_logger(), "Cleaning up Larry hardware — closing serial port.");
  serial_.close();
  return hardware_interface::CallbackReturn::SUCCESS;
}

// ─────────────────────────────────────────────────────────────────────────────
// read() — request encoder feedback, update joint states
// ─────────────────────────────────────────────────────────────────────────────

hardware_interface::return_type LarrySystemHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{
  // Request encoder counts from the MCU
  if (!serial_.write_line("E\r\n")) {
    RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 1000,
      "Serial write failed (encoder request). Keeping last known state.");
    return hardware_interface::return_type::OK;
  }

  std::string response = serial_.read_line(100);

  if (response.empty() || response[0] != 'E') {
    RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 1000,
      "No valid encoder response (got: '%s'). Keeping last known state.",
      response.c_str());
    return hardware_interface::return_type::OK;
  }

  // Parse "E<left_ticks> <right_ticks>"
  long long left_now = 0, right_now = 0;
  if (std::sscanf(response.c_str() + 1, "%lld %lld", &left_now, &right_now) != 2) {
    RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 1000,
      "Failed to parse encoder response: '%s'.", response.c_str());
    return hardware_interface::return_type::OK;
  }

  // Delta ticks since last read
  const long long delta_left  = left_now  - prev_left_ticks_;
  const long long delta_right = right_now - prev_right_ticks_;
  prev_left_ticks_  = left_now;
  prev_right_ticks_ = right_now;

  // Convert ticks → radians
  const double ticks_to_rad = 2.0 * M_PI / static_cast<double>(enc_counts_per_rev_);
  const double delta_left_rad  = static_cast<double>(delta_left)  * ticks_to_rad;
  const double delta_right_rad = static_cast<double>(delta_right) * ticks_to_rad;

  // Velocity in rad/s
  const double dt = period.seconds();
  const double vel_left  = (dt > 1e-9) ? (delta_left_rad  / dt) : 0.0;
  const double vel_right = (dt > 1e-9) ? (delta_right_rad / dt) : 0.0;

  // Update all 6 joints.
  // Joints 0..2 are left side; joints 3..5 are right side.
  for (std::size_t i = 0; i < NUM_JOINTS; ++i) {
    const bool is_left    = (i < NUM_LEFT);
    const double delta    = is_left ? delta_left_rad  : delta_right_rad;
    const double velocity = is_left ? vel_left        : vel_right;

    const std::string pos_key =
      std::string(JOINT_NAMES[i]) + "/" + hardware_interface::HW_IF_POSITION;
    const std::string vel_key =
      std::string(JOINT_NAMES[i]) + "/" + hardware_interface::HW_IF_VELOCITY;

    set_state(pos_key, get_state(pos_key) + delta);
    set_state(vel_key, velocity);
  }

  return hardware_interface::return_type::OK;
}

// ─────────────────────────────────────────────────────────────────────────────
// write() — aggregate wheel commands, convert to PWM, send to MCU
// ─────────────────────────────────────────────────────────────────────────────

hardware_interface::return_type LarrySystemHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Sum velocity commands for each side.
  // The diff_drive_controller sends identical values to all joints on the same
  // side, so the average equals each individual command — averaging here is
  // just a safety measure against floating-point rounding.
  double left_sum  = 0.0;
  double right_sum = 0.0;

  for (std::size_t i = 0; i < NUM_LEFT; ++i) {
    left_sum += get_command(
      std::string(JOINT_NAMES[i]) + "/" + hardware_interface::HW_IF_VELOCITY);
  }
  for (std::size_t i = NUM_LEFT; i < NUM_JOINTS; ++i) {
    right_sum += get_command(
      std::string(JOINT_NAMES[i]) + "/" + hardware_interface::HW_IF_VELOCITY);
  }

  const double left_rad_s  = left_sum  / static_cast<double>(NUM_LEFT);
  const double right_rad_s = right_sum / static_cast<double>(NUM_JOINTS - NUM_LEFT);

  // Convert rad/s → PWM integer (-255..255).
  //
  // Derivation:
  //   ticks_per_loop = cmd_rad_s × enc_counts_per_rev / (2π) / loop_rate
  //   PWM            = clamp(round(ticks_per_loop), -255, 255)
  //
  // At 30 Hz and 11131 CPR a 1 rad/s command maps to ≈59 PWM units, so the
  // ±10 rad/s velocity limit in the URDF covers roughly ±255 at max throttle.
  //
  // loop_rate must match controllers.yaml update_rate (30 Hz by default).
  const double scale = static_cast<double>(enc_counts_per_rev_) /
                       (2.0 * M_PI * loop_rate_);

  const int pwm_left  = static_cast<int>(
    std::round(std::clamp(left_rad_s  * scale, -255.0, 255.0)));
  const int pwm_right = static_cast<int>(
    std::round(std::clamp(right_rad_s * scale, -255.0, 255.0)));

  // Serialise: "M<left> <right>\r\n"
  std::ostringstream cmd;
  cmd << "M" << pwm_left << " " << pwm_right << "\r\n";

  if (!serial_.write_line(cmd.str())) {
    RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 1000,
      "Serial write failed (motor command).");
  } else {
    RCLCPP_DEBUG(get_logger(),
      "CMD: L=%.3f rad/s → %d PWM  |  R=%.3f rad/s → %d PWM",
      left_rad_s, pwm_left, right_rad_s, pwm_right);
  }

  return hardware_interface::return_type::OK;
}

}  // namespace larry_hardware

// ── Pluginlib export ──────────────────────────────────────────────────────────
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  larry_hardware::LarrySystemHardware,
  hardware_interface::SystemInterface)
