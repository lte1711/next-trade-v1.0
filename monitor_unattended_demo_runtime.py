import json
import subprocess
from pathlib import Path


STATUS_FILE = Path("unattended_live_demo_status.json")
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
    if LAUNCH_FILE.exists():
        print(LAUNCH_FILE.read_text(encoding="utf-8"))
    else:
        print("Launch file not found.")

    if STATUS_FILE.exists():
        print(STATUS_FILE.read_text(encoding="utf-8"))
    else:
        print("Status file not found yet.")

    processes = find_processes()
    print(json.dumps({"matching_processes": processes}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
