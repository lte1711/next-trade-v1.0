import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


STATUS_FILE = Path("unattended_live_demo_status.json")
REPORT_FILE = Path("UNATTENDED_LIVE_DEMO_REPORT.md")
LAUNCH_FILE = Path("unattended_live_demo_launch.json")


def now_iso():
    return datetime.now().astimezone().isoformat()


def main():
    cycles = 36
    sleep_seconds = 10

    command = [
        str(Path(".venv") / "Scripts" / "python.exe"),
        "supervised_long_session.py",
        "--cycles",
        str(cycles),
        "--sleep-seconds",
        str(sleep_seconds),
        "--status-file",
        str(STATUS_FILE),
        "--report-file",
        str(REPORT_FILE),
    ]

    process = subprocess.Popen(
        command,
        cwd=str(Path.cwd()),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

    launch_payload = {
        "launched_at": now_iso(),
        "pid": process.pid,
        "status_file": str(STATUS_FILE),
        "report_file": str(REPORT_FILE),
        "command": command,
        "requested_cycles": cycles,
        "sleep_seconds": sleep_seconds,
        "status": "started",
    }
    LAUNCH_FILE.write_text(
        json.dumps(launch_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    time.sleep(3)

    print("UNATTENDED DEMO RUNTIME STARTED")
    print(f"PID: {process.pid}")
    print(f"Status File: {STATUS_FILE}")
    print(f"Report File: {REPORT_FILE}")
    print(f"Launch File: {LAUNCH_FILE}")


if __name__ == "__main__":
    main()
