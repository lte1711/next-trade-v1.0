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
