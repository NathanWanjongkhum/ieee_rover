#!/usr/bin/env bash
# run.sh — build the SLAM workspace, launch the sim, then open WASD teleop
# Run from the ieee_rover/ workspace root OR from inside src/Slam/
set -e

# ── Resolve workspace root ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# If we're inside src/<pkg>/, walk up two levels to the workspace root
if [[ "$SCRIPT_DIR" == */src/* ]]; then
    WS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
    WS_ROOT="$(cd "$SCRIPT_DIR" && pwd)"
fi

echo "Workspace: $WS_ROOT"
cd "$WS_ROOT"

# ── Build ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Building larry_description + Slam  ║"
echo "╚══════════════════════════════════════╝"
colcon build --packages-select larry_description Slam

# ── Source ────────────────────────────────────────────────────────────────────
# shellcheck source=/dev/null
source "$WS_ROOT/install/setup.bash"

# ── Launch sim in background ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Launching SLAM simulation...       ║"
echo "╚══════════════════════════════════════╝"
ros2 launch Slam slam_launch.py &
SIM_PID=$!

# Give Gazebo + controllers time to come up before teleop steals the terminal
echo ""
echo "  Waiting 8 s for Gazebo to initialise..."
sleep 8

# ── WASD teleop ───────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  WASD  TELEOP                            ║"
echo "║                                                          ║"
echo "║    W : forward          S : backward                     ║"
echo "║    A : turn left        D : turn right                   ║"
echo "║    Q : rotate CCW       E : rotate CW                    ║"
echo "║    +/= : speed up       - : slow down                    ║"
echo "║    Space : stop         Ctrl+C : quit                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

ros2 run Slam teleop_wasd

# ── Cleanup ───────────────────────────────────────────────────────────────────
echo ""
echo "Shutting down simulation (PID $SIM_PID)..."
kill "$SIM_PID" 2>/dev/null || true
wait "$SIM_PID" 2>/dev/null || true
echo "Done."
