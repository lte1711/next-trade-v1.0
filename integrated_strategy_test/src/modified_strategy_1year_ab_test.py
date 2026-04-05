#!/usr/bin/env python3
"""Run aggressive profile A/B tests on the deterministic 1-year synthetic simulator."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from modified_strategy_1year_simulation import (
    SCRIPT_DIR,
    build_profile,
    generate_historical_data,
    save_json,
    simulate_modified_strategy,
)


PROFILE_RESULTS_DIR = SCRIPT_DIR / "ab_test_results"
SUMMARY_JSON_PATH = PROFILE_RESULTS_DIR / "modified_strategy_1year_ab_summary.json"
SUMMARY_MD_PATH = PROFILE_RESULTS_DIR / "modified_strategy_1year_ab_summary.md"

AGGRESSIVE_PROFILES = [
    {
        "name": "aggressive_momentum",
        "entry_thresholds": {"NORMAL": 62.0, "HIGH_VOLATILITY": 64.0, "EXTREME": 60.0},
        "profit_potential_offset": 24.0,
        "entry_buffer": -2.0,
        "max_symbols_by_regime": {"NORMAL": 3, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 150.0,
        "take_profit": 1.8,
        "replacement_threshold": -1.0,
    },
    {
        "name": "trend_capture",
        "entry_thresholds": {"NORMAL": 64.0, "HIGH_VOLATILITY": 66.0, "EXTREME": 62.0},
        "profit_potential_offset": 22.0,
        "entry_buffer": -1.0,
        "max_symbols_by_regime": {"NORMAL": 3, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 150.0,
        "take_profit": 2.2,
        "replacement_threshold": -1.2,
    },
    {
        "name": "concentrated_swing",
        "entry_thresholds": {"NORMAL": 60.0, "HIGH_VOLATILITY": 62.0, "EXTREME": 58.0},
        "profit_potential_offset": 26.0,
        "entry_buffer": -3.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 200.0,
        "take_profit": 2.5,
        "replacement_threshold": -1.0,
    },
]


def summarize_results(results: dict) -> dict:
    metadata = results["simulation_metadata"]
    trades = results["trade_history"]
    counts = Counter(item["action"] for item in trades)
    closed = counts.get("TAKE_PROFIT", 0) + counts.get("LOSS_THRESHOLD", 0) + counts.get("POTENTIAL_DROP", 0)
    active_days = sum(1 for row in results["performance_history"] if row["invested_symbols"] > 0)
    avg_invested_symbols = (
        sum(row["invested_symbols"] for row in results["performance_history"]) / len(results["performance_history"])
        if results["performance_history"]
        else 0.0
    )
    return {
        "profile_name": results["analysis_basis"]["profile_name"],
        "final_capital": metadata["final_capital"],
        "final_pnl": metadata["final_pnl"],
        "final_pnl_percent": metadata["final_pnl_percent"],
        "total_fees_paid": metadata["total_fees_paid"],
        "entries": counts.get("ENTRY", 0),
        "take_profits": counts.get("TAKE_PROFIT", 0),
        "loss_threshold_exits": counts.get("LOSS_THRESHOLD", 0),
        "potential_drop_exits": counts.get("POTENTIAL_DROP", 0),
        "win_rate_percent": (counts.get("TAKE_PROFIT", 0) / closed * 100.0) if closed else 0.0,
        "active_days": active_days,
        "avg_invested_symbols": avg_invested_symbols,
        "market_regime_counts": metadata["market_regime_counts"],
    }


def build_summary_markdown(summary_rows: list[dict]) -> str:
    sorted_rows = sorted(summary_rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    best = sorted_rows[0]
    lines = [
        "# Modified Strategy 1-Year A/B Summary",
        "",
        "## Ranking",
    ]
    for index, row in enumerate(sorted_rows, start=1):
        lines.append(
            f"{index}. `{row['profile_name']}`: ${row['final_capital']:.2f}, "
            f"{row['final_pnl_percent']:+.2f}% PnL, {row['entries']} entries, "
            f"{row['win_rate_percent']:.1f}% win rate, ${row['total_fees_paid']:.2f} fees"
        )

    lines.extend(
        [
            "",
            "## Best Profile",
            f"- Name: `{best['profile_name']}`",
            f"- Final capital: ${best['final_capital']:.2f}",
            f"- Final PnL: {best['final_pnl_percent']:+.2f}%",
            f"- Entries: {best['entries']}",
            f"- Win rate: {best['win_rate_percent']:.1f}%",
            "",
            "## Interpretation",
            "- `aggressive_momentum` is the highest-churn profile and should be chosen if opportunity capture matters most.",
            "- `trend_capture` balances trade count and hold quality, and is usually the safest first live candidate.",
            "- `concentrated_swing` takes fewer, larger bets; it benefits most when signal quality is high.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    PROFILE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    historical_data = generate_historical_data()

    summary_rows = []
    for overrides in AGGRESSIVE_PROFILES:
        profile = build_profile(overrides)
        results = simulate_modified_strategy(historical_data, profile)
        output_path = PROFILE_RESULTS_DIR / f"{profile['name']}_results.json"
        save_json(output_path, results)
        summary_rows.append(summarize_results(results))

    summary_payload = {"profiles": summary_rows}
    save_json(SUMMARY_JSON_PATH, summary_payload)
    SUMMARY_MD_PATH.write_text(build_summary_markdown(summary_rows), encoding="utf-8")

    sorted_rows = sorted(summary_rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    for row in sorted_rows:
        print(
            f"{row['profile_name']}: final ${row['final_capital']:.2f} | "
            f"pnl {row['final_pnl_percent']:+.2f}% | entries {row['entries']} | "
            f"win {row['win_rate_percent']:.1f}% | fees ${row['total_fees_paid']:.2f}"
        )
    print(f"saved {SUMMARY_JSON_PATH.name}")
    print(f"saved {SUMMARY_MD_PATH.name}")


if __name__ == "__main__":
    main()
