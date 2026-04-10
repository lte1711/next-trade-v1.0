import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUNTIME_DIR = os.path.join(REPO_ROOT, "runtime")
LOG_DIR = os.path.join(REPO_ROOT, "logs")
PID_PATH = os.path.join(RUNTIME_DIR, "main_runtime_testnet.pid")
STATUS_PATH = os.path.join(RUNTIME_DIR, "main_runtime_testnet_status.json")
LOG_PATH = os.path.join(LOG_DIR, "main_runtime_testnet.log")
KST = timezone(timedelta(hours=9))


def now_kst():
    return datetime.now(KST).isoformat()


def ensure_dirs():
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)


def is_process_running(pid):
    if not pid:
        return False
    try:
        if os.name == "nt":
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and str(pid) in result.stdout
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def find_runtime_processes():
    if os.name != "nt":
        pid = read_pid()
        return [{"pid": pid, "command_line": ""}] if is_process_running(pid) else []
    try:
        ps_command = (
            "Get-CimInstance Win32_Process "
            "| Where-Object { $_.Name -eq 'python.exe' "
            " -and $_.CommandLine -like '*runtime_ops.py child*' } "
            "| Select-Object ProcessId, CommandLine "
            "| ConvertTo-Json -Compress"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        parsed = json.loads(result.stdout)
        if isinstance(parsed, dict):
            parsed = [parsed]
        return [
            {
                "pid": int(item.get("ProcessId")),
                "command_line": item.get("CommandLine", ""),
            }
            for item in parsed
            if item.get("ProcessId")
        ]
    except Exception:
        return []


def read_pid():
    try:
        with open(PID_PATH, "r", encoding="utf-8") as handle:
            return int(handle.read().strip())
    except Exception:
        return None


def write_pid(pid):
    with open(PID_PATH, "w", encoding="utf-8") as handle:
        handle.write(str(pid))


def load_config_safety():
    config = read_json(os.path.join(REPO_ROOT, "config.json"), {})
    testnet = config.get("binance_testnet", {})
    return {
        "base_url": testnet.get("base_url"),
        "execution_mode": config.get("binance_execution_mode"),
        "simulation_mode": config.get("simulation_mode"),
        "force_real_exchange": config.get("force_real_exchange"),
        "max_open_positions": config.get("trading_config", {}).get("max_open_positions"),
    }


def start_runtime():
    ensure_dirs()
    existing_processes = find_runtime_processes()
    if existing_processes:
        return {
            "started": False,
            "reason": "already_running",
            "processes": existing_processes,
            "status_path": STATUS_PATH,
            "log_path": LOG_PATH,
        }

    safety = load_config_safety()
    if safety.get("base_url") != "https://demo-fapi.binance.com":
        return {
            "started": False,
            "reason": "blocked_non_demo_endpoint",
            "safety": safety,
        }

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    command = [sys.executable, __file__, "child"]
    log_handle = open(LOG_PATH, "a", encoding="utf-8")
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        env=env,
        creationflags=creationflags,
        close_fds=False,
    )
    write_pid(process.pid)
    status = {
        "status": "starting",
        "pid": process.pid,
        "started_at": now_kst(),
        "safety": safety,
        "log_path": LOG_PATH,
        "pid_path": PID_PATH,
    }
    write_json(STATUS_PATH, status)
    time.sleep(5)
    return {
        "started": is_process_running(process.pid),
        "pid": process.pid,
        "status": read_json(STATUS_PATH, status),
        "log_path": LOG_PATH,
        "pid_path": PID_PATH,
    }


def child_runtime():
    ensure_dirs()
    os.chdir(REPO_ROOT)
    sys.path.insert(0, REPO_ROOT)

    from main_runtime import TradingRuntime

    status = {
        "status": "initializing",
        "pid": os.getpid(),
        "started_at": now_kst(),
        "safety": load_config_safety(),
    }
    write_json(STATUS_PATH, status)

    runtime = TradingRuntime()
    status.update({
        "status": "running" if runtime.initialized else "initialization_failed",
        "initialized": runtime.initialized,
        "active_strategies": getattr(runtime, "active_strategies", []),
        "valid_symbols_count": len(getattr(runtime, "valid_symbols", [])),
        "max_open_positions": getattr(runtime, "max_open_positions", None),
        "available_balance": runtime.trading_results.get("available_balance"),
        "updated_at": now_kst(),
    })
    write_json(STATUS_PATH, status)

    if not runtime.initialized:
        return 2

    runtime.run()
    status["status"] = "stopped"
    status["stopped_at"] = now_kst()
    write_json(STATUS_PATH, status)
    return 0


def status_runtime():
    pid = read_pid()
    runtime_processes = find_runtime_processes()
    runtime_status = read_json(STATUS_PATH, {})
    trading_results = read_json(os.path.join(REPO_ROOT, "trading_results.json"), {})
    return {
        "pid": pid,
        "running": bool(runtime_processes),
        "processes": runtime_processes,
        "status": runtime_status,
        "trading": {
            "active_positions_count": len(trading_results.get("active_positions", {}) or {}),
            "pending_trades_count": len(trading_results.get("pending_trades", []) or []),
            "real_orders_count": len(trading_results.get("real_orders", []) or []),
            "realized_pnl_journal_count": len(trading_results.get("realized_pnl_journal", []) or []),
            "system_errors_count": len(trading_results.get("system_errors", []) or []),
            "available_balance": trading_results.get("available_balance"),
        },
        "log_path": LOG_PATH,
        "pid_path": PID_PATH,
        "status_path": STATUS_PATH,
    }


def stop_runtime():
    processes = find_runtime_processes()
    if not processes:
        return {"stopped": False, "reason": "not_running", "pid": read_pid()}

    stopped_pids = []
    failed = []
    for process in processes:
        pid = process["pid"]
        if os.name == "nt":
            result = subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                stopped_pids.append(pid)
            else:
                failed.append({"pid": pid, "stdout": result.stdout, "stderr": result.stderr})
        else:
            os.kill(pid, 15)
            stopped_pids.append(pid)
    time.sleep(2)
    remaining = find_runtime_processes()
    stopped = not remaining

    status = read_json(STATUS_PATH, {})
    status.update({"status": "stopped" if stopped else "stop_failed", "stopped_at": now_kst()})
    write_json(STATUS_PATH, status)
    return {
        "stopped": stopped,
        "stopped_pids": stopped_pids,
        "failed": failed,
        "remaining": remaining,
        "status": status,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "status", "stop", "child"])
    args = parser.parse_args()

    if args.command == "child":
        raise SystemExit(child_runtime())
    if args.command == "start":
        result = start_runtime()
    elif args.command == "status":
        result = status_runtime()
    else:
        result = stop_runtime()

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
