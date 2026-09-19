#!/usr/bin/env python3
"""PanelX launcher (cross-platform).

Convenience entry point so users don't have to remember flags:

    python3 run.py                 # -> http://0.0.0.0:5221/
    python3 run.py --port 8080     # custom port
    PX_PORT=8080 python3 run.py    # env override also works

It simply boots panelx.py (same dir) with the current interpreter.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="run.py",
        description="PanelX - server ops panel launcher (cross-platform)",
    )
    ap.add_argument(
        "--host",
        default=os.environ.get("PX_HOST", "0.0.0.0"),
        help="bind address (default 0.0.0.0)",
    )
    ap.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PX_PORT", "5221")),
        help="listen port (default 5221)",
    )
    args = ap.parse_args(argv)

    target = os.path.join(HERE, "panelx.py")
    if not os.path.isfile(target):
        sys.exit("error: panelx.py not found next to run.py (%s)" % HERE)

    cmd = [sys.executable, target, "--host", args.host, "--port", str(args.port)]
    print("PanelX starting -> http://%s:%d/" % (args.host, args.port))
    try:
        proc = subprocess.run(cmd, cwd=HERE)
    except KeyboardInterrupt:
        print("\nPanelX stopped")
        return 0
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
