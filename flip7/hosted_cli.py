#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    script = os.path.basename(sys.argv[0])
    mapping = {
        "flip7-admin-seed-token": "seed-token",
        "flip7-api-submit-bot": "submit-bot",
        "flip7-api-get-me": "get-me",
        "flip7-admin-run-tournament": "run-tournament",
        "flip7-admin-publish": "publish",
        "flip7-api-leaderboard": "leaderboard",
    }
    subcommand = mapping.get(script)
    if not subcommand:
        raise SystemExit(f"Unknown command: {script}")

    cmd = [
        "uv",
        "run",
        "--project",
        "hosted/app",
        "hosted/app/flip7_api_cli.py",
        subcommand,
        *sys.argv[1:],
    ]
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
