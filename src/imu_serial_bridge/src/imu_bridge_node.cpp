// Parses LSM6DSV16X UART output and publishes typed ROS2 IMU messages.
//
// Wire format (one sample = 5 lines, values tab-separated):
//  Accel [mg]:<x>\t<y>\t<z>\r\n
//  Gyro [mdps]:<x>\t<y>\t<z>\r\n
//  GBIAS [mdps]:<x>\t<y>\t<z>\r\n
//  Gravity [mg]:<x>\t<y>\t<z>\r\n
//  Game Rotation \tX:<x>\tY:<y>\tZ:<z>\tW:<w>\r\n`

#include <atomic>
#include <array>
#include <cmath>
#include <optional>
#include <sstream>
#include <string>
#include <thread>

#include "geometry_msgs/msg/vector3_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"

#include "serial_port.hpp"

namespace imu_serial_bridge
{
  using Imu = sensor_msgs::msg::Imu;
  using V3S = geometry_msgs::msg::Vector3Stamped;

  constexpr double kMgToMs2 = 9.81e-3;             // milli-g   → m/s^2
  constexpr double kMdpsToRads = M_PI / 180'000.0; // milli-dps → rad/s

  /// Parse N whitespace-separated doubles from `s` into `out`. Returns true on success.
  template <std::size_t N>
  static bool parse_doubles(const std::string &s, std::array<double, N> &out)
  {
    std::istringstream ss(s);
    for (auto &v : out)
    {
      if (!(ss >> v))
      {
        return false;
      }
    }
    return true;
  }

  /// If `line` starts with `prefix`, parse the N doubles that follow the colon.
  template <std::size_t N>
  static std::optional<std::array<double, N>>
  parse_after(const std::string &line, const std::string &prefix)
  {
    if (line.rfind(prefix, 0) != 0)
    {
      return std::nullopt;
    }
    std::array<double, N> vals;
    if (!parse_doubles<N>(line.substr(prefix.size()), vals))
    {
      return std::nullopt;
    }
    return vals;
  }

  /// Parse "Game Rotation …X: qx …Y: qy …Z: qz …W: qw" → {x, y, z, w}.
  static std::optional<std::array<double, 4>> parse_quat(const std::string &line)
  {
    if (line.rfind("Game Rotation", 0) != 0)
    {
      return std::nullopt;
    }
    std::array<double, 4> q;
    const char *labels[] = {"X:", "Y:", "Z:", "W:"};
    for (std::size_t i = 0; i < 4; ++i)
    {
      const auto pos = line.find(labels[i]);
      if (pos == std::string::npos)
      {
        return std::nullopt;
      }
      std::istringstream ss(line.substr(pos + 2));
      if (!(ss >> q[i]))
      {
        return std::nullopt;
      }
    }
    return q;
  }

  // Partial sample accumulator
  struct PartialSample
  {
    std::optional<std::array<double, 3>> accel;
    std::optional<std::array<double, 3>> gyro;
    std::optional<std::array<double, 3>> gbias;
    std::optional<std::array<double, 3>> gravity;
    std::optional<std::array<double, 4>> quat;

    bool complete() const
    {
      return accel && gyro && gbias && gravity && quat;
    }
    void reset() { *this = {}; }
  };

  class ImuBridgeNode : public rclcpp::Node
  {
  public:
    ImuBridgeNode()
        : Node("imu_bridge"), running_(false)
    {
      declare_parameter("port", "/dev/ttyUSB0");
      declare_parameter("baudrate", 115200);

      const auto port = get_parameter("port").as_string();
      const auto baudrate = static_cast<int>(get_parameter("baudrate").as_int());

      auto qos = rclcpp::QoS(rclcpp::KeepLast(10))
                     .reliability(rclcpp::ReliabilityPolicy::BestEffort);

      pub_raw_ = create_publisher<Imu>("/imu/raw", qos);
      pub_data_ = create_publisher<Imu>("/imu/data", qos);
      pub_gravity_ = create_publisher<V3S>("/imu/gravity", qos);
      pub_gbias_ = create_publisher<V3S>("/imu/gbias", qos);

      serial_ = std::make_unique<SerialPort>(port, baudrate);
      RCLCPP_INFO(get_logger(), "Opened %s @ %d baud", port.c_str(), baudrate);

      running_ = true;
      thread_ = std::thread(&ImuBridgeNode::read_loop, this);
    }

    ~ImuBridgeNode() override
    {
      running_ = false;
      if (thread_.joinable())
      {
        thread_.join();
      }
    }

  private:
    // Serial reader thread
    void read_loop()
    {
      while (running_)
      {
        std::string line;
        try
        {
          line = serial_->readline();
        }
        catch (const std::exception &e)
        {
          RCLCPP_ERROR(get_logger(), "Serial read error: %s", e.what());
          running_ = false;
          break;
        }
        if (!line.empty())
        {
          parse_line(line);
        }
      }
    }

    // Line parser
    void parse_line(const std::string &line)
    {
      // Generic helper: if we already have this field, the previous sample was
      // incomplete — drop it and start fresh.
      auto assign = [&](auto &field, auto value, const char *name)
      {
        if (field.has_value())
        {
          RCLCPP_DEBUG(get_logger(),
                       "Dropped incomplete sample (duplicate \"%s\")", name);
          partial_.reset();
        }
        field = std::move(value);
      };

      if (auto v = parse_after<3>(line, "Accel [mg]:"))
      {
        assign(partial_.accel, *v, "accel");
      }
      else if (auto v = parse_after<3>(line, "Gyro [mdps]:"))
      {
        assign(partial_.gyro, *v, "gyro");
      }
      else if (auto v = parse_after<3>(line, "GBIAS [mdps]:"))
      {
        assign(partial_.gbias, *v, "gbias");
      }
      else if (auto v = parse_after<3>(line, "Gravity [mg]:"))
      {
        assign(partial_.gravity, *v, "gravity");
      }
      else if (auto v = parse_quat(line))
      {
        assign(partial_.quat, *v, "quat");
      }
      else
      {
        return; // unrecognised line (FIFO header, blank, etc.) — ignore
      }

      if (partial_.complete())
      {
        publish();
        partial_.reset();
      }
    }

    void publish()
    {
      const auto stamp = now();

      const auto &a = *partial_.accel;
      const auto &g = *partial_.gyro;
      const auto &b = *partial_.gbias;
      const auto &gv = *partial_.gravity;
      const auto &q = *partial_.quat;

      // /imu/raw = accel + gyro, no orientation
      Imu raw{};
      raw.header.stamp = stamp;
      raw.header.frame_id = "imu_link";
      raw.orientation_covariance[0] = -1.0;
      raw.linear_acceleration.x = a[0] * kMgToMs2;
      raw.linear_acceleration.y = a[1] * kMgToMs2;
      raw.linear_acceleration.z = a[2] * kMgToMs2;
      raw.angular_velocity.x = g[0] * kMdpsToRads;
      raw.angular_velocity.y = g[1] * kMdpsToRads;
      raw.angular_velocity.z = g[2] * kMdpsToRads;
      pub_raw_->publish(raw);

      // /imu/data - SFLP quaternion only, no accel / gyro
      Imu data{};
      data.header.stamp = stamp;
      data.header.frame_id = "imu_link";
      data.orientation.x = q[0];
      data.orientation.y = q[1];
      data.orientation.z = q[2];
      data.orientation.w = q[3];
      data.linear_acceleration_covariance[0] = -1.0;
      data.angular_velocity_covariance[0] = -1.0;
      pub_data_->publish(data);

      // /imu/gravity - SFLP gravity vector in m/s^2
      V3S gravity{};
      gravity.header.stamp = stamp;
      gravity.header.frame_id = "imu_link";
      gravity.vector.x = gv[0] * kMgToMs2;
      gravity.vector.y = gv[1] * kMgToMs2;
      gravity.vector.z = gv[2] * kMgToMs2;
      pub_gravity_->publish(gravity);

      // /imu/gbias - gyro bias in mdps
      V3S gbias{};
      gbias.header.stamp = stamp;
      gbias.header.frame_id = "imu_link";
      gbias.vector.x = b[0];
      gbias.vector.y = b[1];
      gbias.vector.z = b[2];
      pub_gbias_->publish(gbias);
    }

    rclcpp::Publisher<Imu>::SharedPtr pub_raw_;
    rclcpp::Publisher<Imu>::SharedPtr pub_data_;
    rclcpp::Publisher<V3S>::SharedPtr pub_gravity_;
    rclcpp::Publisher<V3S>::SharedPtr pub_gbias_;

    std::unique_ptr<SerialPort> serial_;
    std::atomic<bool> running_;
    std::thread thread_;
    PartialSample partial_;
  };
}

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<imu_serial_bridge::ImuBridgeNode>());
  rclcpp::shutdown();
  return 0;
}
