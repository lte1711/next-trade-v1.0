#!/usr/bin/env python3
"""Start the original, hybrid, and scalping strategies with symbol partitions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "partition_test_logs"


def build_env(base_env: dict[str, str], module: str, partition_index: int, max_open_positions: int, end_time: datetime) -> dict[str, str]:
    env = dict(base_env)
    env.update(
        {
            "STRATEGY_MODULE": module,
            "STRATEGY_CLASS": "CompletelyFixedAutoStrategyFuturesTrading",
            "STRATEGY_RUN_UNTIL_ISO": end_time.isoformat(),
            "STRATEGY_SYMBOL_PARTITION_COUNT": "3",
            "STRATEGY_SYMBOL_PARTITION_INDEX": str(partition_index),
            "MAX_RANKED_SYMBOLS": "210",
            "STRATEGY_MAX_OPEN_POSITIONS": str(max_open_positions),
            "SIGNAL_DIAGNOSTIC_LOG_INTERVAL_SEC": "300",
        }
    )
    return env


def start_process(name: str, env: dict[str, str], timestamp: str) -> dict[str, object]:
    stdout_path = LOG_DIR / f"{name}_{timestamp}.out.log"
    stderr_path = LOG_DIR / f"{name}_{timestamp}.err.log"
    stdout_file = open(stdout_path, "w", encoding="utf-8")
    stderr_file = open(stderr_path, "w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-u", "run_strategy_until.py"],
        cwd=str(ROOT),
        env=env,
        stdout=stdout_file,
        stderr=stderr_file,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )
    return {
        "name": name,
        "pid": process.pid,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "module": env["STRATEGY_MODULE"],
        "partition_index": env["STRATEGY_SYMBOL_PARTITION_INDEX"],
        "max_open_positions": env["STRATEGY_MAX_OPEN_POSITIONS"],
    }


def main() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    end_time = datetime.now() + timedelta(hours=24)
    base_env = os.environ.copy()

    specs = [
        ("original_partition1", "completely_fixed_auto_strategy_trading", 1, 20),
        ("hybrid_partition2", "completely_fixed_auto_strategy_trading_hybrid", 2, 20),
        ("scalping_partition3", "completely_fixed_auto_strategy_trading_scalping", 3, 6),
    ]
    started = [
        start_process(name, build_env(base_env, module, partition_index, max_open_positions, end_time), timestamp)
        for name, module, partition_index, max_open_positions in specs
    ]

    manifest = {
        "started_at": datetime.now().isoformat(),
        "end_time": end_time.isoformat(),
        "ranked_symbol_limit": 210,
        "partition_count": 3,
        "partition_size": 70,
        "processes": started,
    }
    manifest_path = LOG_DIR / f"three_way_partitioned_{timestamp}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
