#!/bin/sh
# PanelX launcher for Linux / macOS
#
#   ./run.sh                 -> http://0.0.0.0:5221/
#   PX_PORT=8080 ./run.sh    -> custom port (env override)
#   PYTHON=python ./run.sh   -> choose interpreter (default: python3)
#
# Make it executable once:  chmod +x run.sh

set -e

PX_DIR="$(cd "$(dirname "$0")" && pwd)"
PX_HOST="${PX_HOST:-0.0.0.0}"
PX_PORT="${PX_PORT:-5221}"
PY="${PYTHON:-python3}"

echo "Starting PanelX on http://${PX_HOST}:${PX_PORT}/"
exec "$PY" "${PX_DIR}/panelx.py" --host "$PX_HOST" --port "$PX_PORT"
