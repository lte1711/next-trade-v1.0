#!/usr/bin/env python3
"""Backtest the promoted profile against user-provided historical JSON or CSV daily-bar data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from modified_strategy_1year_simulation import V3_CANDIDATE_PROFILE, save_json, simulate_modified_strategy


REQUIRED_FIELDS = {"date", "symbol", "price", "change", "volatility", "quote_volume", "high", "low"}


def load_json_history(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict) and "historical_data" in payload:
        payload = payload["historical_data"]

    if not isinstance(payload, list):
        raise ValueError("JSON historical input must be a list or contain a 'historical_data' list.")

    if payload and isinstance(payload[0], dict) and "symbols" in payload[0]:
        return payload

    grouped: dict[str, dict[str, Any]] = {}
    symbol_windows: dict[str, list[float]] = defaultdict(list)
    volume_windows: dict[str, list[float]] = defaultdict(list)

    for row in payload:
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise ValueError(f"JSON row is missing required fields: {sorted(missing)}")

        date = str(row["date"])
        symbol = str(row["symbol"])
        symbol_windows[symbol].append(float(row["change"]))
        volume_windows[symbol].append(float(row["quote_volume"]))
        grouped.setdefault(
            date,
            {"date": date, "timestamp": date, "synthetic_regime": "UNKNOWN", "symbols": {}},
        )
        grouped[date]["symbols"][symbol] = {
            "price": float(row["price"]),
            "change": float(row["change"]),
            "volatility": float(row["volatility"]),
            "volume": int(float(row["quote_volume"]) / max(float(row["price"]), 0.0001)),
            "quote_volume": float(row["quote_volume"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "synthetic_regime": "UNKNOWN",
            "change_history": symbol_windows[symbol][-20:],
            "quote_volume_history": volume_windows[symbol][-20:],
        }

    return [grouped[date] for date in sorted(grouped)]


def load_csv_history(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_headers = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing_headers:
            raise ValueError(f"CSV is missing required headers: {sorted(missing_headers)}")
        for row in reader:
            rows.append(row)
    return load_json_history(rows)


def load_history(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json_history(path)
    if suffix == ".csv":
        return load_csv_history(path)
    raise ValueError("Only .json and .csv historical inputs are supported.")


def build_output_path(input_path: Path, output: str | None) -> Path:
    if output:
        return Path(output).resolve()
    return input_path.with_name(f"{input_path.stem}_v3_backtest_results.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the v3 candidate profile on external historical daily-bar data.")
    parser.add_argument("input_path", help="Path to a CSV or JSON historical data file.")
    parser.add_argument("--output", help="Optional output JSON path.")
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    historical_data = load_history(input_path)
    results = simulate_modified_strategy(historical_data, V3_CANDIDATE_PROFILE)
    results["analysis_basis"]["data_type"] = "external_historical_daily_data"
    results["analysis_basis"]["source_path"] = str(input_path)

    output_path = build_output_path(input_path, args.output)
    save_json(output_path, results)

    meta = results["simulation_metadata"]
    print(f"source: {input_path}")
    print(f"final capital: ${meta['final_capital']:.2f}")
    print(f"final pnl: {meta['final_pnl_percent']:+.2f}%")
    print(f"saved {output_path}")


if __name__ == "__main__":
    main()
