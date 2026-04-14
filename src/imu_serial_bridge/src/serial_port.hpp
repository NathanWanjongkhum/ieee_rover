#pragma once

#include <fcntl.h>
#include <sys/select.h>
#include <termios.h>
#include <unistd.h>

#include <string>
#include <system_error>

namespace imu_serial_bridge
{
  class SerialPort
  {
  public:
    SerialPort(const std::string &port, int baudrate)
    {
      fd_ = ::open(port.c_str(), O_RDWR | O_NOCTTY | O_SYNC);
      if (fd_ < 0)
      {
        throw std::system_error(errno, std::generic_category(), "open(" + port + ")");
      }

      struct termios tty{};
      if (::tcgetattr(fd_, &tty) != 0)
      {
        ::close(fd_);
        throw std::system_error(errno, std::generic_category(), "tcgetattr");
      }

      const speed_t speed = to_speed(baudrate);
      ::cfsetispeed(&tty, speed);
      ::cfsetospeed(&tty, speed);

      // 8N1, raw mode
      tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;
      tty.c_cflag &= ~(PARENB | CSTOPB);
      tty.c_cflag |= CREAD | CLOCAL;
      tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
      tty.c_iflag &= ~(IXON | IXOFF | IXANY | IGNBRK | BRKINT | PARMRK |
                       ISTRIP | INLCR | IGNCR | ICRNL);
      tty.c_oflag &= ~OPOST;
      tty.c_cc[VMIN] = 1;  // block until at least 1 byte
      tty.c_cc[VTIME] = 0; // no inter-byte timeout (select handles the timeout)

      if (::tcsetattr(fd_, TCSANOW, &tty) != 0)
      {
        ::close(fd_);
        throw std::system_error(errno, std::generic_category(), "tcsetattr");
      }
    }

    ~SerialPort()
    {
      if (fd_ >= 0)
      {
        ::close(fd_);
      }
    }

    SerialPort(const SerialPort &) = delete;
    SerialPort &operator=(const SerialPort &) = delete;

    /// Read one '\n'-terminated line.  Strips '\r'.
    /// Returns "" if no data arrives within timeout_ms milliseconds.
    std::string readline(int timeout_ms = 100)
    {
      std::string line;
      char c;

      while (true)
      {
        fd_set rfds;
        FD_ZERO(&rfds);
        FD_SET(fd_, &rfds);
        struct timeval tv{timeout_ms / 1000, (timeout_ms % 1000) * 1000};

        const int ready = ::select(fd_ + 1, &rfds, nullptr, nullptr, &tv);
        if (ready < 0)
        {
          throw std::system_error(errno, std::generic_category(), "select");
        }
        if (ready == 0)
        {
          return ""; // timeout
        }

        const ssize_t n = ::read(fd_, &c, 1);
        if (n <= 0)
        {
          return "";
        }
        if (c == '\n')
        {
          return line;
        }
        if (c != '\r')
        {
          line += c;
        }
      }
    }

  private:
    int fd_{-1};

    static speed_t to_speed(int baud)
    {
      switch (baud)
      {
      case 9600:
        return B9600;
      case 19200:
        return B19200;
      case 38400:
        return B38400;
      case 57600:
        return B57600;
      case 115200:
        return B115200;
      case 230400:
        return B230400;
      default:
        return B115200;
      }
    }
  };

}
