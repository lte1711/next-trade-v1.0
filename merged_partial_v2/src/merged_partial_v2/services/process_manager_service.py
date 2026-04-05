"""Background autonomous process control for the local dashboard."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from merged_partial_v2.pathing import install_root as resolve_install_root


def _runtime_dir() -> Path:
    path = resolve_install_root() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def process_record_path() -> Path:
    return _runtime_dir() / "autonomous_process.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def load_process_record() -> dict[str, Any]:
    path = process_record_path()
    if not path.exists():
        return {"ok": False, "reason": "no_process_record", "path": str(path)}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    payload["ok"] = True
    payload["path"] = str(path)
    return payload


def write_process_record(payload: dict[str, Any]) -> Path:
    path = process_record_path()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return path


def clear_process_record() -> None:
    path = process_record_path()
    if path.exists():
        path.unlink()


def get_process_status() -> dict[str, Any]:
    record = load_process_record()
    if not record.get("ok"):
        return {
            "ok": True,
            "running": False,
            "reason": record.get("reason"),
            "path": record.get("path"),
        }

    pid = int(record.get("pid", 0) or 0)
    running = _is_pid_running(pid)
    return {
        "ok": True,
        "running": running,
        "pid": pid,
        "mode": record.get("mode"),
        "live": record.get("live"),
        "adopt_active_positions": record.get("adopt_active_positions"),
        "started_at": record.get("started_at"),
        "command": record.get("command"),
        "path": record.get("path"),
    }


def _launcher_command(
    *,
    live: bool,
    adopt_active_positions: bool,
    interval_seconds: float,
) -> list[str]:
    args = [
        "--autonomous-loop",
        "--autonomous-cycles",
        "1000000",
        "--autonomous-interval-seconds",
        str(max(interval_seconds, 1.0)),
    ]
    if adopt_active_positions:
        args.append("--adopt-active-positions")
    if live:
        args.append("--live")

    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable).resolve()), *args]

    launcher = resolve_install_root() / "run_merged_partial_v2.py"
    return [sys.executable, str(launcher), *args]


def start_autonomous_process(
    *,
    live: bool,
    adopt_active_positions: bool,
    interval_seconds: float,
) -> dict[str, Any]:
    status = get_process_status()
    if status.get("running"):
        return {
            "ok": False,
            "started": False,
            "reason": "autonomous_process_already_running",
            "status": status,
        }

    command = _launcher_command(
        live=live,
        adopt_active_positions=adopt_active_positions,
        interval_seconds=interval_seconds,
    )
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]

    process = subprocess.Popen(  # noqa: S603
        command,
        cwd=str(resolve_install_root()),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )
    record = {
        "pid": process.pid,
        "mode": "autonomous_loop",
        "live": live,
        "adopt_active_positions": adopt_active_positions,
        "interval_seconds": interval_seconds,
        "command": command,
        "started_at": _utc_now(),
    }
    write_process_record(record)
    return {
        "ok": True,
        "started": True,
        "pid": process.pid,
        "record": record,
    }


def stop_autonomous_process() -> dict[str, Any]:
    status = get_process_status()
    if not status.get("running"):
        clear_process_record()
        return {
            "ok": True,
            "stopped": False,
            "reason": "autonomous_process_not_running",
            "status": status,
        }

    pid = int(status.get("pid", 0) or 0)
    try:
        if os.name == "nt":
            os.kill(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return {
            "ok": False,
            "stopped": False,
            "reason": "stop_failed",
            "error": str(exc),
            "status": status,
        }

    clear_process_record()
    return {
        "ok": True,
        "stopped": True,
        "pid": pid,
        "stopped_at": _utc_now(),
    }
