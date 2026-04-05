#!/usr/bin/env python3
"""Convert integrated_strategy_test's real-market-style loader output into v3 backtest input JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INTEGRATED_ROOT = SCRIPT_DIR.parent
if str(INTEGRATED_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATED_ROOT))

from src.data.market_data import RealMarketDataLoader  # noqa: E402
from modified_strategy_1year_simulation import save_json  # noqa: E402


OUTPUT_PATH = SCRIPT_DIR / "real_market_backtest_input.json"
MERGED_ROOT = SCRIPT_DIR.parents[1] / "merged_partial_v2"
INSTALLED_ROOT = Path("C:/tradev1")


def load_runtime_symbol_hints() -> tuple[list[str], dict[str, float]]:
    symbols: list[str] = []
    price_hints: dict[str, float] = {}

    state_path = INSTALLED_ROOT / "runtime" / "autonomous_state.json"
    if state_path.exists():
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        for symbol, item in dict(payload.get("managed_positions") or {}).items():
            normalized = str(symbol or "").upper()
            if not normalized:
                continue
            symbols.append(normalized)
            price_value = item.get("mark_price") or item.get("entry_price")
            if price_value is not None:
                price_hints[normalized] = float(price_value)

    snapshot_paths = [
        INSTALLED_ROOT / "merged_snapshot.json",
        MERGED_ROOT / "merged_snapshot.json",
    ]
    for snapshot_path in snapshot_paths:
        if not snapshot_path.exists():
            continue
        payload = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
        market = dict(payload.get("market") or {})
        account_positions = list((payload.get("account") or {}).get("positions", {}).get("active_positions") or [])
        for row in account_positions:
            normalized = str(row.get("symbol") or "").upper()
            if not normalized:
                continue
            symbols.append(normalized)
            price_value = row.get("markPrice") or row.get("entryPrice")
            if price_value is not None:
                price_hints[normalized] = float(price_value)
        for row in market.get("selected_symbols", []) + market.get("evaluated_symbols", []):
            normalized = str(row.get("symbol") or "").upper()
            if not normalized:
                continue
            symbols.append(normalized)
            price_value = row.get("price")
            if price_value is not None:
                price_hints[normalized] = float(price_value)
        break

    ordered_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        if symbol not in seen:
            ordered_symbols.append(symbol)
            seen.add(symbol)
    return ordered_symbols, price_hints


def augment_loader_symbols(loader: RealMarketDataLoader) -> None:
    runtime_symbols, price_hints = load_runtime_symbol_hints()
    if not runtime_symbols:
        return
    for symbol in runtime_symbols:
        if symbol not in loader.symbols:
            loader.symbols.append(symbol)
        if symbol not in loader.initial_prices and symbol in price_hints:
            loader.initial_prices[symbol] = price_hints[symbol]


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
    augment_loader_symbols(loader)
    raw_history = loader.load_real_market_data()
    transformed = enrich_history(raw_history)
    save_json(OUTPUT_PATH, transformed)
    print(f"saved {OUTPUT_PATH}")
    print(f"days: {len(transformed)}")
    print(f"symbols_per_day: {len(transformed[0]['symbols']) if transformed else 0}")


if __name__ == "__main__":
    main()
