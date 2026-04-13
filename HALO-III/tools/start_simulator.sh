#!/usr/bin/env bash
# Starts a virtual serial port pair and the IMU simulator.
#
# Creates two symlinks at known paths — no need to read socat output:
#   /tmp/imu_sim_tx  ← simulator writes here
#   /tmp/imu_sim_rx  ← ROS2 bridge / minicom reads here
#
# Usage:
#   ./tools/start_simulator.sh
 
set -e

TX=/tmp/imu_sim_tx
RX=/tmp/imu_sim_rx

cleanup() {
    echo ""
    echo "[simulator] shutting down..."
    kill "$SOCAT_PID" 2>/dev/null
    rm -f "$TX" "$RX"
    echo "[simulator] done"
}
trap cleanup EXIT INT TERM

# Remove stale symlinks from a previous run
rm -f "$TX" "$RX"

# Start socat in background with fixed symlink paths
socat pty,raw,echo=0,link="$TX" pty,raw,echo=0,link="$RX" &
SOCAT_PID=$!

# Wait for socat to create the symlinks
for i in $(seq 1 20); do
    [[ -e "$TX" && -e "$RX" ]] && break
    sleep 0.1
done

if [[ ! -e "$TX" || ! -e "$RX" ]]; then
    echo "[simulator] ERROR: socat failed to create virtual ports" >&2
    exit 1
fi

echo "[simulator] virtual ports ready"
echo "  simulator  →  $TX"
echo "  bridge/minicom  →  $RX"
echo ""
echo "Connect with:"
echo "  minicom -D $RX -b 115200"
echo "  ros2 run imu_serial_bridge imu_bridge --ros-args -p port:=$RX"
echo "---"

# Run simulator in foreground — Ctrl+C hits this process, trap handles cleanup
python3 "$(dirname "$0")/simulate_imu.py" --port "$TX"
