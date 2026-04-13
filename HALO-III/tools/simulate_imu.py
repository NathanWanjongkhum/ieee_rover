#!/usr/bin/env python3
"""
STM32 IMU UART simulator.

Generates synthetic LSM6DSV16X output that matches the serial protocol.
Intended for testing the ROS2 imu_serial_bridge node without physical hardware.

Usage:
    # Create a virtual serial port pair
    socat -d -d pty,raw,echo=0 pty,raw,echo=0

    # socat will print something like:
    #   /dev/pts/3  (simulator writes here)
    #   /dev/pts/4  (ROS2 bridge reads here)

    # Run the simulator
    python3 simulate_imu.py --port /dev/pts/3

    # Point the ROS2 bridge at the other end
    ros2 run imu_serial_bridge imu_bridge --ros-args -p port:=/dev/pts/4
"""

import argparse
import math
import time
import serial
import sys


FIFO_WATERMARK = 32
ODR_HZ = 30
BATCH_INTERVAL = FIFO_WATERMARK / ODR_HZ  # seconds between FIFO drain events


def simulate_accel(t: float) -> tuple[float, float, float]:
    """Gravity vector with small sinusoidal tilt disturbance. Units: mg."""
    tilt = math.sin(t * 0.2) * 100.0  # slow ±100 mg tilt
    ax = tilt
    ay = math.cos(t * 0.15) * 50.0
    az = -1000.0 + math.sin(t * 0.3) * 20.0  # ~-1g on Z + noise
    return ax, ay, az


def simulate_gyro(t: float) -> tuple[float, float, float]:
    """Slow rotation with small oscillation. Units: mdps."""
    gx = math.sin(t * 0.5) * 500.0
    gy = math.cos(t * 0.4) * 300.0
    gz = 100.0 + math.sin(t * 0.1) * 50.0
    return gx, gy, gz


def simulate_quaternion(t: float) -> tuple[float, float, float, float]:
    """Slow yaw rotation. Unit quaternion (X Y Z W)."""
    angle = t * 0.05  # slow rotation in radians
    x = 0.0
    y = 0.0
    z = math.sin(angle / 2.0)
    w = math.cos(angle / 2.0)
    return x, y, z, w


def simulate_gravity(t: float) -> tuple[float, float, float]:
    """SFLP gravity estimate tracks accel Z with smoothing. Units: mg."""
    ax, ay, az = simulate_accel(t)
    return ax * 0.9, ay * 0.9, az * 0.9


def simulate_gbias(t: float) -> tuple[float, float, float]:
    """Slowly converging gyro bias estimate. Units: mdps."""
    decay = math.exp(-t * 0.01)
    return 12.0 * decay, -8.0 * decay, 3.0 * decay


def build_batch(t_start: float) -> bytes:
    lines = []
    lines.append(f"-- FIFO num {FIFO_WATERMARK} \r\n")

    for i in range(FIFO_WATERMARK):
        t = t_start + i / ODR_HZ

        ax, ay, az = simulate_accel(t)
        lines.append(f"Accel [mg]:{ax:4.2f}\t{ay:4.2f}\t{az:4.2f}\r\n")

        gx, gy, gz = simulate_gyro(t)
        lines.append(f"Gyro [mdps]:{gx:4.2f}\t{gy:4.2f}\t{gz:4.2f}\r\n")

        bx, by, bz = simulate_gbias(t)
        lines.append(f"GBIAS [mdps]:{bx:4.2f}\t{by:4.2f}\t{bz:4.2f}\r\n")

        gvx, gvy, gvz = simulate_gravity(t)
        lines.append(f"Gravity [mg]:{gvx:4.2f}\t{gvy:4.2f}\t{gvz:4.2f}\r\n")

        qx, qy, qz, qw = simulate_quaternion(t)
        lines.append(
            f"Game Rotation \tX: {qx:2.3f}\tY: {qy:2.3f}\tZ: {qz:2.3f}\tW: {qw:2.3f}\r\n"
        )

    lines.append("------ \r\n\r\n")
    return "".join(lines).encode("utf-8")


def run(port: str, stdout: bool) -> None:
    if stdout:
        sink = sys.stdout.buffer
        print(f"[simulator] writing to stdout at {ODR_HZ} Hz", file=sys.stderr)
    else:
        sink = serial.Serial(port=port, baudrate=115200, timeout=1)
        print(f"[simulator] writing to {port} at 115200 baud", file=sys.stderr)

    t = 0.0
    try:
        while True:
            batch_start = time.monotonic()
            data = build_batch(t)
            try:
                sink.write(data)
                if hasattr(sink, "flush"):
                    sink.flush()
            except (serial.SerialException, OSError, BrokenPipeError) as e:
                print(f"\n[simulator] port closed ({e}), exiting", file=sys.stderr)
                break
            t += BATCH_INTERVAL

            # sleep for the remainder of the batch interval
            elapsed = time.monotonic() - batch_start
            sleep_time = BATCH_INTERVAL - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[simulator] stopped", file=sys.stderr)
    finally:
        if not stdout and hasattr(sink, "close"):
            sink.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="STM32 IMU UART simulator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--port", help="Virtual serial port to write to (e.g. /dev/pts/3)")
    group.add_argument("--stdout", action="store_true", help="Write to stdout instead of a serial port")
    args = parser.parse_args()
    run(args.port, args.stdout)


if __name__ == "__main__":
    main()
