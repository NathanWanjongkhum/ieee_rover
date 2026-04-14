#!/usr/bin/env bash
# Starts a tmux session with the full IMU simulator stack:
#
#   Window 0 — simulator   socat + IMU data generator (start_simulator.sh)
#   Window 1 — bridge      ROS2 imu_serial_bridge node
#   Window 2 — monitor     ros2 topic echo /imu/raw
#   Window 3 — shell       free shell inside the workspace
#
# Usage:
#   ./tools/sim_session.sh            # attach after launch
#   ./tools/sim_session.sh --no-attach  # start detached
#
# Kill the session:
#   tmux kill-session -t imu_sim

set -e

SESSION="imu_sim"
WS="$(cd "$(dirname "$0")/../.." && pwd)"
TOOLS="$WS/HALO-III/tools"

_shell_name="$(basename "${SHELL:-bash}")"
case "$_shell_name" in
    zsh)  _ext="zsh"  ;;
    fish) _ext="fish" ;;
    *)    _ext="bash" ;;
esac

SETUP="$WS/install/setup.$_ext"
if [[ ! -f "$SETUP" ]]; then
    echo "WARNING: $SETUP not found, falling back to setup.bash" >&2
    SETUP="$WS/install/setup.bash"
fi
RX=/tmp/imu_sim_rx

tmux kill-session -t "$SESSION" 2>/dev/null || true

tmux new-session -d -s "$SESSION" -n simulator -x 220 -c "$WS"
tmux send-keys -t "$SESSION:simulator" "bash $TOOLS/start_simulator.sh" Enter

for i in $(seq 1 50); do
    [[ -e "$RX" ]] && break
    sleep 0.1
done

if [[ ! -e "$RX" ]]; then
    echo "ERROR: $RX never appeared — is socat installed?" >&2
    tmux kill-session -t "$SESSION"
    exit 1
fi

tmux new-window -t "$SESSION" -n bridge -c "$WS"
tmux send-keys -t "$SESSION:bridge" \
    "source $SETUP && ros2 run imu_serial_bridge imu_bridge --ros-args -p port:=$RX" Enter

tmux new-window -t "$SESSION" -n monitor -c "$WS"
tmux send-keys -t "$SESSION:monitor" \
    "source $SETUP && ros2 topic echo /imu/raw --qos-reliability best_effort" Enter

tmux new-window -t "$SESSION" -n shell -c "$WS"
tmux send-keys -t "$SESSION:shell" "source $SETUP" Enter

tmux select-window -t "$SESSION:simulator"

if [[ "$1" != "--no-attach" ]]; then
    tmux attach -t "$SESSION"
fi
