#!/bin/sh
# PanelX downloader / launcher
#
#   - if panelx.py exists next to this script, run it
#   - otherwise git clone the repo, then run it
#
# Usage:  ./Download.sh

set -e

cd "$(dirname "$0")"

if [ -f panelx.py ]; then
    echo "PanelX already present, starting..."
    exec ./run.sh
fi

if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is not installed."
    echo "       Install git, or place panelx.py next to this script."
    exit 1
fi

echo "Cloning PanelX from GitHub..."
git -c http.version=HTTP/1.1 clone https://github.com/Developerprit/PanelX.git
cd PanelX
chmod +x run.sh
exec ./run.sh
