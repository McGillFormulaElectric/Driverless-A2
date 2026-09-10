#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# A2 — Watch /neil/feedback live.
# Run from a second terminal while launch_neil.sh is running.
# ---------------------------------------------------------------------------
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker compose -f "$REPO_ROOT/docker/docker-compose.yml" run --rm neil bash -c "
  source /opt/ros/humble/setup.bash
  if [ -f /workspace/install/setup.bash ]; then source /workspace/install/setup.bash; fi
  echo '[neil] Watching /neil/feedback — verdicts appear here when members submit...'
  ros2 topic echo /neil/feedback
"
