from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .multi5_config import EDGE_SCORE_THRESHOLD, SCAN_INTERVAL_SEC
    from .multi5_symbol_ranker import select_top_one, sort_by_edge
    from .multi5_symbol_scanner import fetch_universe_data
except ImportError:
    from multi5_config import EDGE_SCORE_THRESHOLD, SCAN_INTERVAL_SEC
    from multi5_symbol_ranker import select_top_one, sort_by_edge
    from multi5_symbol_scanner import fetch_universe_data


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _scan_log_path() -> Path:
    return _project_root() / "logs/runtime/multi5_symbol_scan.jsonl"


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_scan_log(ranked_rows: list[dict[str, Any]], selected_symbol: str | None) -> None:
    path = _scan_log_path()
    for idx, row in enumerate(ranked_rows, start=1):
        _append_jsonl(
            path,
            {
                "ts": _utc_now_iso(),
                "symbol": row.get("symbol"),
                "edge_score": row.get("edge_score", 0.0),
                "rank": idx,
                "selected": row.get("symbol") == selected_symbol,
            },
        )


def base_engine_call(selected_symbol: str, session_hours: float = 2.0) -> subprocess.Popen:
    root = _project_root()
    python_exe = root / "venv/Scripts/python.exe"
    engine_script = root / "tools/ops/profitmax_v1_runner.py"
    cmd = [
        str(python_exe),
        str(engine_script),
        "--profile",
        "TESTNET_INTRADAY_SCALP",
        "--session-hours",
        str(session_hours),
        "--symbol",
        selected_symbol,
    ]
    return subprocess.Popen(cmd, cwd=str(root))


def run_once(session_hours: float = 2.0, launch_engine: bool = False) -> dict[str, Any]:
    symbol_states = fetch_universe_data()
    ranked = sort_by_edge(symbol_states)
    top = select_top_one(symbol_states)
    selected_symbol = top.get("SELECTED_SYMBOL") if top else None
    _write_scan_log(ranked, selected_symbol)

    result: dict[str, Any] = {
        "scanner_count": len(symbol_states),
        "selected": top,
        "engine_started": False,
    }
    if top and float(top.get("EDGE_SCORE", 0.0)) >= EDGE_SCORE_THRESHOLD and launch_engine:
        base_engine_call(selected_symbol=str(top["SELECTED_SYMBOL"]), session_hours=session_hours)
        result["engine_started"] = True
    return result


def run_loop(session_hours: float = 2.0, launch_engine: bool = False) -> None:
    while True:
        run_once(session_hours=session_hours, launch_engine=launch_engine)
        time.sleep(SCAN_INTERVAL_SEC)


if __name__ == "__main__":
    # Default safe mode: scan/rank/log only. Engine launch is opt-in.
    run_loop(session_hours=2.0, launch_engine=False)
