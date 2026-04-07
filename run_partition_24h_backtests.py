#!/usr/bin/env python3
"""Run 24-hour backtests for the active three-way symbol partitions."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "partition_test_logs"
BACKTEST_SCRIPT = ROOT / "backtest_completely_fixed_auto_strategy_trading_v2_5y.py"


def latest_manifest() -> Path:
    manifests = sorted(LOG_DIR.glob("three_way_partitioned_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not manifests:
        raise FileNotFoundError("No partition manifest found")
    return manifests[0]


def read_partition_symbols(stdout_path: str) -> list[str]:
    text = Path(stdout_path).read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"with symbols=(\[.*?\]) max_open_positions", text, re.S)
    if not match:
        raise ValueError(f"Could not parse partition symbols from {stdout_path}")
    symbols = ast.literal_eval(match.group(1))
    return [symbol for symbol in symbols if isinstance(symbol, str) and symbol.isascii()]


def run_backtest(name: str, source_file: str, symbols: list[str]) -> dict:
    env = os.environ.copy()
    env.update(
        {
            "V2_BACKTEST_SOURCE_FILE": source_file,
            "V2_BACKTEST_SYMBOLS": ",".join(symbols),
            "V2_BACKTEST_YEARS": str(1 / 365),
            "V2_BACKTEST_EVAL_STEP_BARS": "1",
            "V2_BACKTEST_TIMEFRAME_MODE": "standard",
            "V2_BACKTEST_INITIAL_CAPITAL": "10000",
        }
    )
    started_at = datetime.now().isoformat()
    result = subprocess.run(
        [sys.executable, str(BACKTEST_SCRIPT)],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
    )
    return {
        "name": name,
        "source_file": source_file,
        "symbol_count": len(symbols),
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def main() -> None:
    manifest_path = latest_manifest()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_by_name = {
        "original_partition1": "completely_fixed_auto_strategy_trading.py",
        "hybrid_partition2": "completely_fixed_auto_strategy_trading_hybrid.py",
        "scalping_partition3": "completely_fixed_auto_strategy_trading_scalping.py",
    }

    results = []
    for process in manifest["processes"]:
        name = process["name"]
        symbols = read_partition_symbols(process["stdout"])
        results.append(run_backtest(name, source_by_name[name], symbols))

    report = {
        "generated_at": datetime.now().isoformat(),
        "manifest": str(manifest_path),
        "period": "last_24h",
        "results": results,
    }
    report_path = ROOT / f"partition_24h_backtests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved partition 24h backtest report to {report_path}")


if __name__ == "__main__":
    main()
