import json
import subprocess
from datetime import datetime
from pathlib import Path


LAUNCH_FILE = Path("unattended_live_demo_launch.json")


def find_processes():
    ps_command = (
        "Get-CimInstance Win32_Process "
        "| Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*supervised_long_session.py*' "
        "-and $_.CommandLine -like '*unattended_live_demo_status.json*' } "
        "| Select-Object ProcessId, CommandLine "
        "| ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_command],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []

    parsed = json.loads(result.stdout)
    if isinstance(parsed, dict):
        parsed = [parsed]
    return parsed


def main():
    stopped = []
    for process in find_processes():
        pid = str(process.get("ProcessId"))
        if not pid:
            continue
        subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, text=True)
        stopped.append(pid)

    payload = {
        "stopped_at": datetime.now().astimezone().isoformat(),
        "stopped_pids": stopped,
        "status": "stopped",
    }
    if LAUNCH_FILE.exists():
        existing = json.loads(LAUNCH_FILE.read_text(encoding="utf-8"))
        existing.update(payload)
        payload = existing

    LAUNCH_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
