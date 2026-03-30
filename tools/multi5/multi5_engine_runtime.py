from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .multi5_config import (
        ALLOCATION_MAX_WEIGHT,
        ALLOCATION_MIN_WEIGHT,
        ALLOCATION_OBSERVATION_MODE,
        API_FAILURE_LIMIT,
        BIAS_CHECK_WINDOW,
        DRAWDDOWN_SOFT_LIMIT,
        ENABLE_MARKET_REGIME,
        ENABLE_PORTFOLIO_ALLOCATION,
        ENGINE_ERROR_LIMIT,
        MAX_ACCOUNT_DRAWDOWN,
        MAX_CONSECUTIVE_LOSS,
        MAX_PORTFOLIO_EXPOSURE,
        MAX_SHORT_POSITIONS,
        MAX_SIDE_EXPOSURE,
        MAX_VOLATILITY_THRESHOLD,
        MIN_ENTRY_QUALITY_SCORE,
        MIN_LONG_RATIO,
        REGIME_TREND_THRESHOLD,
        REGIME_VOL_HIGH,
        REGIME_VOL_LOW,
        SHORT_BIAS_GUARD_ENABLED,
        WIN_RATE_SOFT_LIMIT,
    )
except ImportError:
    from multi5_config import (
        ALLOCATION_MAX_WEIGHT,
        ALLOCATION_MIN_WEIGHT,
        ALLOCATION_OBSERVATION_MODE,
        API_FAILURE_LIMIT,
        BIAS_CHECK_WINDOW,
        DRAWDDOWN_SOFT_LIMIT,
        ENABLE_MARKET_REGIME,
        ENABLE_PORTFOLIO_ALLOCATION,
        ENGINE_ERROR_LIMIT,
        MAX_ACCOUNT_DRAWDOWN,
        MAX_CONSECUTIVE_LOSS,
        MAX_PORTFOLIO_EXPOSURE,
        MAX_SHORT_POSITIONS,
        MAX_SIDE_EXPOSURE,
        MAX_VOLATILITY_THRESHOLD,
        MIN_ENTRY_QUALITY_SCORE,
        MIN_LONG_RATIO,
        REGIME_TREND_THRESHOLD,
        REGIME_VOL_HIGH,
        REGIME_VOL_LOW,
        SHORT_BIAS_GUARD_ENABLED,
        WIN_RATE_SOFT_LIMIT,
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def scan_log_path() -> Path:
    return project_root() / "logs/runtime/multi5_symbol_scan.jsonl"


def runtime_log_path() -> Path:
    return project_root() / "logs/runtime/multi5_runtime_events.jsonl"


def worker_log_path() -> Path:
    return project_root() / "logs/runtime/profitmax_v1_events.jsonl"


def strategy_signal_dir() -> Path:
    return project_root() / "logs/runtime/strategy_signals"


# STANDARD_LOCK: DO NOT MODIFY (DENNIS APPROVED 2026-03-30)
# This function implements the official project path isolation standard
# Any modification requires explicit Dennis approval and constitutional amendment
def strategy_signal_path(symbol: str, strategy_id: str) -> Path:
    safe_symbol = re.sub(r"[^A-Za-z0-9_]+", "_", symbol.upper())
    safe_strategy = re.sub(r"[^A-Za-z0-9_]+", "_", strategy_id.lower())
    return strategy_signal_dir() / f"{safe_symbol}_{safe_strategy}.json"


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# STANDARD_LOCK: DO NOT MODIFY (DENNIS APPROVED 2026-03-30)
# This function is the official project standard for atomic JSON writes
# Any modification requires explicit Dennis approval and constitutional amendment
def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False, suffix='.tmp') as tmp:
        tmp.write(json.dumps(payload, ensure_ascii=False, indent=2))
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    os.replace(tmp_path, path)


def find_running_workers() -> list[dict[str, Any]]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -like 'python*.exe' -and $_.CommandLine -like '*profitmax_v1_runner.py*' } | "
            "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
        ),
    ]
    try:
        out = subprocess.check_output(cmd, text=True).strip()
        if not out:
            return []
        data = json.loads(out)
        if isinstance(data, dict):
            return [data] if data.get("ProcessId") else []
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict) and row.get("ProcessId")]
        return []
    except Exception:
        return []


def fetch_open_position_symbols() -> set[str]:
    try:
        with subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Invoke-RestMethod -Uri 'http://127.0.0.1:8100/api/v1/investor/positions' -TimeoutSec 10 | ConvertTo-Json -Compress -Depth 5",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as proc:
            stdout, _ = proc.communicate(timeout=12)
        if not stdout:
            return set()
        payload = json.loads(stdout)
        rows = payload.get("positions", []) if isinstance(payload, dict) else []
        open_symbols: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("symbol", "")).upper().strip()
            if not symbol:
                continue
            try:
                qty = float(row.get("positionAmt", "0") or 0.0)
            except Exception:
                qty = 0.0
            if abs(qty) > 0.0:
                open_symbols.add(symbol)
        return open_symbols
    except Exception:
        return set()


def is_api_server_reachable(host: str = "127.0.0.1", port: int = 8100, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def parse_worker_symbols(workers: list[dict[str, Any]]) -> set[str]:
    symbols: set[str] = set()
    for row in workers:
        cmd = str(row.get("CommandLine", ""))
        match = re.search(r"--symbol(?:\s+|=)([A-Za-z0-9_]+)", cmd)
        if match:
            symbols.add(match.group(1).upper())
    return symbols


def terminate_workers(workers: list[dict[str, Any]]) -> None:
    for row in workers:
        pid = int(row.get("ProcessId", 0) or 0)
        if pid <= 0:
            continue
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            try:
                os.kill(pid, 9)
            except Exception:
                pass


def terminate_worker_symbols(workers: list[dict[str, Any]], symbols_to_stop: set[str]) -> None:
    if not symbols_to_stop:
        return
    for row in workers:
        pid = int(row.get("ProcessId", 0) or 0)
        if pid <= 0:
            continue
        cmd = str(row.get("CommandLine", ""))
        match = re.search(r"--symbol(?:\s+|=)([A-Za-z0-9_]+)", cmd)
        if not match:
            continue
        symbol = match.group(1).upper()
        if symbol not in symbols_to_stop:
            continue
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            try:
                os.kill(pid, 9)
            except Exception:
                pass


def write_scan_log(ranked_rows: list[dict[str, Any]], selected_symbol: str | None, selected_symbols: set[str] | None = None) -> None:
    path = scan_log_path()
    selected_symbols = selected_symbols or set()
    for idx, row in enumerate(ranked_rows, start=1):
        append_jsonl(
            path,
            {
                "ts": utc_now().isoformat(),
                "symbol": row.get("symbol"),
                "edge_score": row.get("edge_score", 0.0),
                "rank": idx,
                "selected": row.get("symbol") == selected_symbol,
                "selected_batch": row.get("symbol") in selected_symbols,
            },
        )


def run_engine(
    symbol: str,
    session_hours: float,
    max_positions: int,
    *,
    strategy_unit: str,
    strategy_signal_path_value: Path,
    take_profit_pct: float,
    stop_loss_pct: float,
) -> subprocess.Popen:
    root = project_root()
    python_exe = root / ".venv/Scripts/python.exe"
    if not python_exe.exists():
        python_exe = root / "venv/Scripts/python.exe"
    engine_script = root / "tools/ops/profitmax_v1_runner.py"
    cmd = [
        str(python_exe),
        str(engine_script),
        "--profile",
        "TESTNET_INTRADAY_SCALP",
        "--session-hours",
        str(session_hours),
        "--max-positions",
        str(max_positions),
        "--max-short-positions",
        str(MAX_SHORT_POSITIONS),
        "--min-long-ratio",
        str(MIN_LONG_RATIO),
        "--bias-check-window",
        str(BIAS_CHECK_WINDOW),
        "--max-portfolio-exposure",
        str(MAX_PORTFOLIO_EXPOSURE),
        "--max-side-exposure",
        str(MAX_SIDE_EXPOSURE),
        "--min-entry-quality-score",
        str(MIN_ENTRY_QUALITY_SCORE),
        "--drawdown-soft-limit",
        str(DRAWDDOWN_SOFT_LIMIT),
        "--win-rate-soft-limit",
        str(WIN_RATE_SOFT_LIMIT),
        "--max-account-drawdown",
        str(MAX_ACCOUNT_DRAWDOWN),
        "--max-consecutive-loss",
        str(MAX_CONSECUTIVE_LOSS),
        "--max-volatility-threshold",
        str(MAX_VOLATILITY_THRESHOLD),
        "--api-failure-limit",
        str(API_FAILURE_LIMIT),
        "--engine-error-limit",
        str(ENGINE_ERROR_LIMIT),
        "--regime-trend-threshold",
        str(REGIME_TREND_THRESHOLD),
        "--regime-vol-high",
        str(REGIME_VOL_HIGH),
        "--regime-vol-low",
        str(REGIME_VOL_LOW),
        "--allocation-max-weight",
        str(ALLOCATION_MAX_WEIGHT),
        "--allocation-min-weight",
        str(ALLOCATION_MIN_WEIGHT),
        "--max-position-minutes",
        "15",
        "--symbol",
        symbol,
        "--strategy-unit",
        strategy_unit,
        "--strategy-signal-path",
        str(strategy_signal_path_value),
        "--max-signal-age-sec",
        "90",
        "--take-profit-pct-override",
        str(take_profit_pct),
        "--stop-loss-pct-override",
        str(stop_loss_pct),
    ]
    if SHORT_BIAS_GUARD_ENABLED:
        cmd.append("--short-bias-guard-enabled")
    if ENABLE_MARKET_REGIME:
        cmd.append("--enable-market-regime")
    if ENABLE_PORTFOLIO_ALLOCATION:
        cmd.append("--enable-portfolio-allocation")
    if ALLOCATION_OBSERVATION_MODE:
        cmd.append("--allocation-observation-mode")
    return subprocess.Popen(cmd, cwd=str(root))
