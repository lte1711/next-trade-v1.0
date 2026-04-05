#!/usr/bin/env python3
"""Tune external-input profiles against real_market_backtest_input.json."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from historical_data_profile_backtest import load_history
from modified_strategy_1year_simulation import save_json, simulate_modified_strategy


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "real_market_backtest_input.json"
OUTPUT_DIR = SCRIPT_DIR / "real_market_remote_tuning_results"
SUMMARY_JSON = OUTPUT_DIR / "real_market_remote_tuning_summary.json"
SUMMARY_MD = OUTPUT_DIR / "real_market_remote_tuning_summary.md"


REMOTE_PROFILES = [
    {
        "name": "remote_balanced_1",
        "entry_thresholds": {"NORMAL": 64.0, "HIGH_VOLATILITY": 68.0, "EXTREME": 72.0},
        "regime_volatility_thresholds": {"EXTREME": 12.0, "HIGH_VOLATILITY": 6.0},
        "profit_potential_offset": 20.0,
        "entry_buffer": -1.0,
        "exit_buffer": 5.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 1, "EXTREME": 1},
        "fixed_allocation": 150.0,
        "take_profit": 2.4,
        "replacement_threshold": -1.0,
        "minimum_hold_bars": 1,
    },
    {
        "name": "remote_balanced_2",
        "entry_thresholds": {"NORMAL": 66.0, "HIGH_VOLATILITY": 70.0, "EXTREME": 74.0},
        "regime_volatility_thresholds": {"EXTREME": 14.0, "HIGH_VOLATILITY": 7.0},
        "profit_potential_offset": 18.0,
        "entry_buffer": 0.0,
        "exit_buffer": 5.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 1, "EXTREME": 1},
        "fixed_allocation": 150.0,
        "take_profit": 2.8,
        "replacement_threshold": -1.2,
        "minimum_hold_bars": 2,
    },
    {
        "name": "remote_low_churn",
        "entry_thresholds": {"NORMAL": 68.0, "HIGH_VOLATILITY": 72.0, "EXTREME": 76.0},
        "regime_volatility_thresholds": {"EXTREME": 16.0, "HIGH_VOLATILITY": 8.0},
        "profit_potential_offset": 16.0,
        "entry_buffer": 0.0,
        "exit_buffer": 6.0,
        "max_symbols_by_regime": {"NORMAL": 1, "HIGH_VOLATILITY": 1, "EXTREME": 1},
        "fixed_allocation": 180.0,
        "take_profit": 3.0,
        "replacement_threshold": -1.3,
        "minimum_hold_bars": 2,
    },
    {
        "name": "remote_selective_momentum",
        "entry_thresholds": {"NORMAL": 62.0, "HIGH_VOLATILITY": 66.0, "EXTREME": 70.0},
        "regime_volatility_thresholds": {"EXTREME": 13.0, "HIGH_VOLATILITY": 6.5},
        "profit_potential_offset": 22.0,
        "entry_buffer": -2.0,
        "exit_buffer": 4.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 140.0,
        "take_profit": 2.2,
        "replacement_threshold": -1.0,
        "minimum_hold_bars": 1,
    },
]


def summarize(results: dict) -> dict:
    meta = results["simulation_metadata"]
    counts = Counter(item["action"] for item in results["trade_history"])
    exits = counts.get("TAKE_PROFIT", 0) + counts.get("LOSS_THRESHOLD", 0) + counts.get("POTENTIAL_DROP", 0)
    return {
        "profile_name": results["analysis_basis"]["profile_name"],
        "final_capital": meta["final_capital"],
        "final_pnl_percent": meta["final_pnl_percent"],
        "total_fees_paid": meta["total_fees_paid"],
        "entries": counts.get("ENTRY", 0),
        "take_profits": counts.get("TAKE_PROFIT", 0),
        "loss_threshold_exits": counts.get("LOSS_THRESHOLD", 0),
        "potential_drop_exits": counts.get("POTENTIAL_DROP", 0),
        "win_rate_percent": (counts.get("TAKE_PROFIT", 0) / exits * 100.0) if exits else 0.0,
        "market_regime_counts": meta["market_regime_counts"],
    }


def build_summary_md(rows: list[dict]) -> str:
    ordered = sorted(rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    best = ordered[0]
    lines = [
        "# Real Market Remote Tuning Summary",
        "",
        "## Ranking",
    ]
    for idx, row in enumerate(ordered, start=1):
        lines.append(
            f"{idx}. `{row['profile_name']}`: {row['final_pnl_percent']:+.2f}% | "
            f"final ${row['final_capital']:.2f} | entries {row['entries']} | "
            f"win {row['win_rate_percent']:.1f}% | fees ${row['total_fees_paid']:.2f}"
        )
    lines.extend(
        [
            "",
            "## Best Remote Candidate",
            f"- Name: `{best['profile_name']}`",
            f"- Final capital: ${best['final_capital']:.2f}",
            f"- Final PnL: {best['final_pnl_percent']:+.2f}%",
            f"- Entries: {best['entries']}",
            f"- Win rate: {best['win_rate_percent']:.1f}%",
            "",
            "## Goal",
            "- These profiles try to reduce EXTREME overclassification and overtrading on the external-input dataset.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    historical_data = load_history(INPUT_PATH)
    rows = []
    for profile in REMOTE_PROFILES:
        results = simulate_modified_strategy(historical_data, profile)
        out = OUTPUT_DIR / f"{profile['name']}_results.json"
        save_json(out, results)
        rows.append(summarize(results))

    save_json(SUMMARY_JSON, {"profiles": rows})
    SUMMARY_MD.write_text(build_summary_md(rows), encoding="utf-8")

    ordered = sorted(rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    for row in ordered:
        print(
            f"{row['profile_name']}: pnl {row['final_pnl_percent']:+.2f}% | "
            f"final ${row['final_capital']:.2f} | entries {row['entries']} | "
            f"win {row['win_rate_percent']:.1f}% | fees ${row['total_fees_paid']:.2f}"
        )
    print(f"saved {SUMMARY_JSON.name}")
    print(f"saved {SUMMARY_MD.name}")


if __name__ == "__main__":
    main()
