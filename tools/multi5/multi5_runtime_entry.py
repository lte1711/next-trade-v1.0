from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import sys

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from profit_engine.profit_engine_controller import run_once as run_profit_once


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _runtime_log_path() -> Path:
    return _project_root() / "logs/runtime/multi5_primary_runtime.jsonl"


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_loop(runtime_minutes: int, scan_interval_sec: int, session_hours: float) -> dict[str, Any]:
    end_at = _utc_now() + timedelta(minutes=max(1, runtime_minutes))
    scans = 0
    engine_calls = 0
    selected_symbols: list[str] = []
    errors = 0

    while _utc_now() < end_at:
        try:
            result = run_profit_once(launch_engine=True, session_hours=session_hours)
            scans += 1
            symbol = str(result.get("selected_symbol", ""))
            if symbol:
                selected_symbols.append(symbol)
            if bool(result.get("engine_called", False)):
                engine_calls += 1
            _append_jsonl(
                _runtime_log_path(),
                {
                    "ts": _utc_now().isoformat(),
                    "selected_symbol": symbol,
                    "edge_score_computed": bool(result.get("edge_score_computed", False)),
                    "liquidity_check_working": bool(result.get("liquidity_check_working", False)),
                    "engine_called": bool(result.get("engine_called", False)),
                    "final_decision": result.get("final_decision", ""),
                },
            )
        except Exception as exc:
            errors += 1
            _append_jsonl(
                _runtime_log_path(),
                {
                    "ts": _utc_now().isoformat(),
                    "selected_symbol": "",
                    "engine_called": False,
                    "final_decision": "RUNTIME_ERROR",
                    "error": str(exc),
                },
            )
        time.sleep(max(1, scan_interval_sec))

    switches = 0
    for i in range(1, len(selected_symbols)):
        if selected_symbols[i] != selected_symbols[i - 1]:
            switches += 1

    return {
        "runtime_min": runtime_minutes,
        "scan_events": scans,
        "symbol_switch_count": switches,
        "entry_attempts": engine_calls,
        "runtime_errors": errors,
        "last_selected_symbol": selected_symbols[-1] if selected_symbols else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MULTI5 primary runtime entry")
    parser.add_argument("--runtime-minutes", type=int, default=10)
    parser.add_argument("--scan-interval-sec", type=int, default=3)
    parser.add_argument("--session-hours", type=float, default=2.0)
    args = parser.parse_args()
    summary = run_loop(
        runtime_minutes=max(1, args.runtime_minutes),
        scan_interval_sec=max(1, args.scan_interval_sec),
        session_hours=max(0.05, args.session_hours),
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
