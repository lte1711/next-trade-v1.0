"""Background autonomous process control for the local dashboard."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from merged_partial_v2.pathing import install_root as resolve_install_root


_AUTONOMOUS_THREAD: threading.Thread | None = None
_AUTONOMOUS_STOP_EVENT: threading.Event | None = None
_THREAD_LOCK = threading.Lock()


def _runtime_dir() -> Path:
    path = resolve_install_root() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def process_record_path() -> Path:
    return _runtime_dir() / "autonomous_process.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_failure_recovery_attempt(pid: int, recovery_type: str) -> None:
    """실패 복구 시도 기록"""
    try:
        record = {
            "pid": pid,
            "recovery_type": recovery_type,
            "timestamp": _utc_now(),
            "reason": "Automatic recovery attempt recorded",
        }
        
        recovery_path = _runtime_dir() / "recovery_attempts.json"
        if recovery_path.exists():
            with recovery_path.open("r", encoding="utf-8") as f:
                existing_records = json.load(f)
            existing_records.append(record)
        else:
            existing_records = [record]
        
        with recovery_path.open("w", encoding="utf-8") as f:
            json.dump(existing_records, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # 기록 실패 시 무시


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _thread_is_running() -> bool:
    with _THREAD_LOCK:
        return _AUTONOMOUS_THREAD is not None and _AUTONOMOUS_THREAD.is_alive()


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


def update_process_record(pid: int, **updates: Any) -> dict[str, Any]:
    record = load_process_record()
    if not record.get("ok"):
        return {"ok": False, "reason": record.get("reason"), "path": record.get("path")}

    record_pid = int(record.get("pid", 0) or 0)
    if record_pid != int(pid):
        return {
            "ok": False,
            "reason": "pid_mismatch",
            "path": record.get("path"),
            "record_pid": record_pid,
            "requested_pid": int(pid),
        }

    record.update(updates)
    write_process_record({k: v for k, v in record.items() if k not in {"ok", "path"}})
    record["ok"] = True
    return record


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
    running = _thread_is_running() if pid == os.getpid() else _is_pid_running(pid)
    return {
        "ok": True,
        "running": running,
        "pid": pid,
        "mode": record.get("mode"),
        "live": record.get("live"),
        "adopt_active_positions": record.get("adopt_active_positions"),
        "started_at": record.get("started_at"),
        "last_heartbeat_at": record.get("last_heartbeat_at"),
        "last_cycle_at": record.get("last_cycle_at"),
        "stopped_at": record.get("stopped_at"),
        "exit_reason": record.get("exit_reason"),
        "command": record.get("command"),
        "path": record.get("path"),
    }


def _launcher_command(
    *,
    live: bool,
    adopt_active_positions: bool,
    interval_seconds: float,
) -> list[str]:
    """자동매매 루프를 별도 프로세스로 실행하기 위한 명령어 생성"""
    args = [
        "--autonomous-loop",
        "--autonomous-cycles",
        "0",  # 무한 루프
        "--autonomous-interval-seconds",
        str(max(interval_seconds, 1.0)),
    ]
    if adopt_active_positions:
        args.append("--adopt-active-positions")
    if live:
        args.append("--live")
    else:
        # 테스트넷 환경에서는 --live 플래그 없이 실행 (dry_run 모드)
        pass

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

    global _AUTONOMOUS_THREAD, _AUTONOMOUS_STOP_EVENT
    with _THREAD_LOCK:
        if _AUTONOMOUS_THREAD is not None and _AUTONOMOUS_THREAD.is_alive():
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
        _AUTONOMOUS_STOP_EVENT = threading.Event()
        _AUTONOMOUS_THREAD = threading.Thread(
            target=_run_autonomous_loop_in_background,
            kwargs={
                "stop_event": _AUTONOMOUS_STOP_EVENT,
                "live": live,
                "adopt_active_positions": adopt_active_positions,
                "interval_seconds": interval_seconds,
            },
            name="merged_partial_v2_autonomous_loop",
            daemon=True,
        )
        _AUTONOMOUS_THREAD.start()
    record = {
        "pid": os.getpid(),
        "mode": "autonomous_loop",
        "live": live,
        "adopt_active_positions": adopt_active_positions,
        "interval_seconds": interval_seconds,
        "command": command,
        "started_at": _utc_now(),
        "last_heartbeat_at": _utc_now(),
        "host": "dashboard_thread",
    }
    write_process_record(record)
    return {
        "ok": True,
        "started": True,
        "pid": os.getpid(),
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
    if pid == os.getpid() and _thread_is_running():
        global _AUTONOMOUS_THREAD, _AUTONOMOUS_STOP_EVENT
        with _THREAD_LOCK:
            if _AUTONOMOUS_STOP_EVENT is not None:
                _AUTONOMOUS_STOP_EVENT.set()
            if _AUTONOMOUS_THREAD is not None:
                _AUTONOMOUS_THREAD.join(timeout=10.0)
            _AUTONOMOUS_THREAD = None
            _AUTONOMOUS_STOP_EVENT = None
        clear_process_record()
        return {
            "ok": True,
            "stopped": True,
            "pid": pid,
            "stopped_at": _utc_now(),
        }
    try:
        if os.name == "nt":
            os.kill(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
        
        # 프로세스가 실제로 종료될 때까지 대기 (최대 5초)
        max_wait_time = 5.0
        wait_interval = 0.1
        elapsed_time = 0.0
        
        while elapsed_time < max_wait_time:
            if not _is_pid_running(pid):
                break
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        # 여전히 실행 중이면 강제 종료
        if _is_pid_running(pid):
            try:
                if os.name == "nt":
                    os.kill(pid, signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGKILL)
            except OSError:
                pass  # 이미 종료되었을 수 있음
        
        # 실패 기록 남기기
        _record_failure_recovery_attempt(pid, "process_termination")
        
        clear_process_record()
        return {
            "ok": True,
            "stopped": True,
            "pid": pid,
            "stopped_at": _utc_now(),
            "recovery_attempted": True,
        }
        
    except OSError as exc:
        return {
            "ok": False,
            "stopped": False,
            "reason": "stop_failed",
            "error": str(exc),
            "status": status,
        }


def heartbeat_autonomous_process(pid: int, *, last_cycle_at: str | None = None) -> dict[str, Any]:
    updates: dict[str, Any] = {"last_heartbeat_at": _utc_now()}
    if last_cycle_at:
        updates["last_cycle_at"] = last_cycle_at
    return update_process_record(pid, **updates)


def finalize_autonomous_process(
    pid: int,
    *,
    exit_reason: str,
    stopped_at: str | None = None,
    clear_if_current: bool = True,
) -> dict[str, Any]:
    status = get_process_status()
    if int(status.get("pid", 0) or 0) != int(pid):
        return {
            "ok": False,
            "reason": "pid_mismatch",
            "status": status,
            "requested_pid": int(pid),
        }

    payload = update_process_record(
        pid,
        exit_reason=exit_reason,
        stopped_at=stopped_at or _utc_now(),
        last_heartbeat_at=_utc_now(),
    )
    if clear_if_current:
        clear_process_record()
    return payload


def _run_autonomous_loop_in_background(
    *,
    stop_event: threading.Event,
    live: bool,
    adopt_active_positions: bool,
    interval_seconds: float,
) -> None:
    try:
        from run_merged_partial_v2 import _build_autonomous_service, _build_engine, _write_crash_log
        from merged_partial_v2.main import build_snapshot_payload, write_snapshot_payload

        engine, config, _, _ = _build_engine()
        service = _build_autonomous_service(engine, config)
        cycle_index = 0
        while not stop_event.is_set():
            try:
                try:
                    write_snapshot_payload(build_snapshot_payload())
                except Exception:
                    pass
                report = service.run_cycle(
                    dry_run=False,
                    adopt_existing_positions=adopt_active_positions if cycle_index == 0 else False,
                )
                try:
                    write_snapshot_payload(build_snapshot_payload())
                except Exception:
                    pass
                heartbeat_autonomous_process(os.getpid(), last_cycle_at=report.get("ts"))
            except Exception as exc:  # noqa: BLE001
                report = service.write_loop_error_report(
                    error=exc,
                    dry_run=False,
                    cycle_index=cycle_index,
                    retry_sleep_seconds=max(interval_seconds, 0.0),
                )
                heartbeat_autonomous_process(os.getpid(), last_cycle_at=report.get("ts"))
                _write_crash_log(exc)
            cycle_index += 1
            if stop_event.wait(max(interval_seconds, 0.0)):
                break
    except Exception as exc:  # noqa: BLE001
        try:
            from run_merged_partial_v2 import _write_crash_log

            _write_crash_log(exc)
        except Exception:
            pass
    finally:
        global _AUTONOMOUS_THREAD, _AUTONOMOUS_STOP_EVENT
        with _THREAD_LOCK:
            _AUTONOMOUS_THREAD = None
            _AUTONOMOUS_STOP_EVENT = None
