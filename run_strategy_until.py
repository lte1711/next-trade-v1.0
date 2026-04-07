#!/usr/bin/env python3
"""Run a strategy module until a configured timestamp.

This helper is intentionally separate from the strategy sources so test sessions
can be launched with isolated symbols and an externally controlled end time.
"""

from __future__ import annotations

import importlib
import os
from datetime import datetime


def parse_symbol_list(raw_value: str) -> list[str]:
    return [symbol.strip().upper() for symbol in raw_value.split(",") if symbol.strip()]


def parse_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    return int(float(raw_value))


def select_symbol_partition(symbols: list[str]) -> list[str]:
    partition_count = parse_int_env("STRATEGY_SYMBOL_PARTITION_COUNT", 0)
    partition_index = parse_int_env("STRATEGY_SYMBOL_PARTITION_INDEX", 0)
    partition_size = parse_int_env("STRATEGY_SYMBOL_PARTITION_SIZE", 0)

    if partition_count <= 0 and partition_size <= 0:
        return symbols

    if partition_count > 0:
        if partition_index < 1 or partition_index > partition_count:
            raise ValueError("STRATEGY_SYMBOL_PARTITION_INDEX must be between 1 and STRATEGY_SYMBOL_PARTITION_COUNT")
        partition_size = max(1, (len(symbols) + partition_count - 1) // partition_count)

    if partition_index < 1:
        raise ValueError("STRATEGY_SYMBOL_PARTITION_INDEX must be at least 1 when partitioning is enabled")

    start = (partition_index - 1) * partition_size
    end = start + partition_size
    return symbols[start:end]


def main() -> None:
    module_name = os.getenv("STRATEGY_MODULE", "").strip()
    class_name = os.getenv("STRATEGY_CLASS", "CompletelyFixedAutoStrategyFuturesTrading").strip()
    run_until_iso = os.getenv("STRATEGY_RUN_UNTIL_ISO", "").strip()
    symbol_list = parse_symbol_list(os.getenv("STRATEGY_SYMBOLS", ""))
    max_open_positions = os.getenv("STRATEGY_MAX_OPEN_POSITIONS", "").strip()

    if not module_name:
        raise ValueError("STRATEGY_MODULE is required")
    if not run_until_iso:
        raise ValueError("STRATEGY_RUN_UNTIL_ISO is required")

    module = importlib.import_module(module_name)
    strategy_cls = getattr(module, class_name)
    strategy = strategy_cls()

    run_until = datetime.fromisoformat(run_until_iso)
    strategy.end_time = run_until
    strategy.test_duration = max(0, int((strategy.end_time - strategy.start_time).total_seconds()))
    strategy.trading_results["end_time"] = strategy.end_time.isoformat()

    if max_open_positions:
        strategy.max_open_positions = max(1, int(float(max_open_positions)))

    if not symbol_list:
        symbol_list = select_symbol_partition(list(getattr(strategy, "valid_symbols", [])))

    if symbol_list:
        strategy.managed_symbols = set(symbol_list)
        strategy.valid_symbols = symbol_list
        strategy.current_prices = {symbol: strategy.get_current_price(symbol, 0.0) for symbol in symbol_list}
        strategy.strategies = strategy.generate_dynamic_strategies()
        strategy.refresh_strategy_capital_allocations()

    print(
        f"[INFO] Running {module_name}.{class_name} until {strategy.end_time.isoformat()} "
        f"with symbols={strategy.valid_symbols} max_open_positions={strategy.max_open_positions}"
    )
    strategy.run_trading()


if __name__ == "__main__":
    main()
