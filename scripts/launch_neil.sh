#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# A2 — Neil's side launcher
# Run this on your (Neil's) machine to start the signal publisher + grader.
# New members connect over Tailscale and you grade them automatically.
#
# Usage:  bash scripts/launch_neil.sh [--build]
# ---------------------------------------------------------------------------
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="docker compose -f $REPO_ROOT/docker/docker-compose.yml"

# Optional rebuild
if [[ "${1:-}" == "--build" ]]; then
  echo "[neil] Building image..."
  $COMPOSE build neil
fi

echo "[neil] Starting A2 grading node..."
echo "[neil] Feedback will appear on /neil/feedback"
echo "[neil] New members are visible at: ros2 topic list | grep /neil"
echo ""

$COMPOSE run --rm neil bash -c "
  source /opt/ros/humble/setup.bash
  cd /workspace
  if [ -f install/setup.bash ]; then source install/setup.bash; fi
  colcon build --packages-select a2_neil --symlink-install --quiet
  source install/setup.bash
  echo '[neil] Launching signal_publisher + grader...'
  ros2 launch a2_neil neil.launch.py
"
