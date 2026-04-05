#!/usr/bin/env python3
"""Convert integrated_strategy_test's real-market-style loader output into v3 backtest input JSON."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INTEGRATED_ROOT = SCRIPT_DIR.parent
if str(INTEGRATED_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATED_ROOT))

from src.data.market_data import RealMarketDataLoader  # noqa: E402
from modified_strategy_1year_simulation import save_json  # noqa: E402


OUTPUT_PATH = SCRIPT_DIR / "real_market_backtest_input.json"


def enrich_history(raw_history: list[dict]) -> list[dict]:
    change_windows: dict[str, list[float]] = {}
    volume_windows: dict[str, list[float]] = {}
    enriched = []

    for day in raw_history:
        date_record = {
            "date": day["date"],
            "timestamp": day.get("timestamp", day["date"]),
            "synthetic_regime": day.get("market_phase", "UNKNOWN"),
            "symbols": {},
        }
        for symbol, symbol_data in day["symbols"].items():
            change_windows.setdefault(symbol, []).append(float(symbol_data["change"]))
            volume_windows.setdefault(symbol, []).append(float(symbol_data["volume"]) * float(symbol_data["price"]))

            quote_volume = float(symbol_data["volume"]) * float(symbol_data["price"])
            date_record["symbols"][symbol] = {
                "price": float(symbol_data["price"]),
                "change": float(symbol_data["change"]),
                "volatility": float(symbol_data["volatility"]),
                "volume": int(symbol_data["volume"]),
                "quote_volume": quote_volume,
                "high": float(symbol_data["high"]),
                "low": float(symbol_data["low"]),
                "synthetic_regime": day.get("market_phase", "UNKNOWN"),
                "change_history": change_windows[symbol][-20:],
                "quote_volume_history": volume_windows[symbol][-20:],
            }
        enriched.append(date_record)

    return enriched


def main() -> None:
    loader = RealMarketDataLoader()
    raw_history = loader.load_real_market_data()
    transformed = enrich_history(raw_history)
    save_json(OUTPUT_PATH, transformed)
    print(f"saved {OUTPUT_PATH}")
    print(f"days: {len(transformed)}")
    print(f"symbols_per_day: {len(transformed[0]['symbols']) if transformed else 0}")


if __name__ == "__main__":
    main()
