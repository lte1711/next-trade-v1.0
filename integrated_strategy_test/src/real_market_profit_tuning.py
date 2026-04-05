#!/usr/bin/env python3
"""Profit-focused remote tuning around the current aggressive reference profile."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from historical_data_profile_backtest import load_history
from modified_strategy_1year_simulation import (
    REMOTE_V3_REFERENCE_PROFILE,
    save_json,
    simulate_modified_strategy,
)


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "real_market_backtest_input.json"
OUTPUT_DIR = SCRIPT_DIR / "real_market_profit_tuning_results"
SUMMARY_JSON = OUTPUT_DIR / "real_market_profit_tuning_summary.json"
SUMMARY_MD = OUTPUT_DIR / "real_market_profit_tuning_summary.md"


PROFIT_PROFILES = [
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_reference",
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_more_entries",
        "entry_thresholds": {"NORMAL": 66.0, "HIGH_VOLATILITY": 70.0, "EXTREME": 74.0},
        "entry_buffer": -1.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 1, "EXTREME": 1},
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_higher_tp",
        "take_profit": 3.6,
        "replacement_threshold": -1.4,
        "exit_buffer": 5.0,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_partial_take",
        "take_profit": 4.0,
        "partial_take_profit": 2.2,
        "partial_take_profit_ratio": 0.5,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_trailing",
        "take_profit": 4.2,
        "trailing_stop_activation": 3.0,
        "trailing_stop_drawdown": 1.2,
        "replacement_threshold": -1.4,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_partial_trailing",
        "take_profit": 4.5,
        "partial_take_profit": 2.4,
        "partial_take_profit_ratio": 0.5,
        "trailing_stop_activation": 3.0,
        "trailing_stop_drawdown": 1.0,
        "replacement_threshold": -1.4,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_dynamic_sizing",
        "dynamic_sizing": True,
        "allocation_min": 120.0,
        "allocation_max": 240.0,
        "allocation_score_floor": 66.0,
        "allocation_score_ceiling": 88.0,
        "take_profit": 3.2,
        "replacement_threshold": -1.3,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_partial_reaccel",
        "take_profit": 4.0,
        "partial_take_profit": 2.2,
        "partial_take_profit_ratio": 0.5,
        "allow_reacceleration": True,
        "reacceleration_bullish_bonus": 3.0,
        "reacceleration_profit_offset": 8.0,
        "reacceleration_add_fraction": 0.6,
        "reacceleration_min_pnl_percent": 1.0,
        "max_reaccelerations_per_position": 1,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_dynamic_reaccel",
        "dynamic_sizing": True,
        "allocation_min": 120.0,
        "allocation_max": 260.0,
        "allocation_score_floor": 64.0,
        "allocation_score_ceiling": 86.0,
        "partial_take_profit": 2.0,
        "partial_take_profit_ratio": 0.45,
        "allow_reacceleration": True,
        "reacceleration_bullish_bonus": 2.0,
        "reacceleration_profit_offset": 8.0,
        "reacceleration_add_fraction": 0.5,
        "reacceleration_min_pnl_percent": 0.9,
        "max_reaccelerations_per_position": 1,
        "take_profit": 4.2,
        "replacement_threshold": -1.35,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_dual_slot",
        "entry_thresholds": {"NORMAL": 67.0, "HIGH_VOLATILITY": 71.0, "EXTREME": 75.0},
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 150.0,
        "take_profit": 3.2,
        "replacement_threshold": -1.4,
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "profit_fast_momentum",
        "entry_thresholds": {"NORMAL": 64.0, "HIGH_VOLATILITY": 68.0, "EXTREME": 72.0},
        "entry_buffer": -2.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 1, "EXTREME": 1},
        "take_profit": 2.8,
        "replacement_threshold": -1.2,
        "profit_potential_offset": 18.0,
    },
]


def summarize(results: dict) -> dict:
    meta = results["simulation_metadata"]
    counts = Counter(item["action"] for item in results["trade_history"])
    return {
        "profile_name": results["analysis_basis"]["profile_name"],
        "final_capital": meta["final_capital"],
        "final_pnl_percent": meta["final_pnl_percent"],
        "total_fees_paid": meta["total_fees_paid"],
        "entries": counts.get("ENTRY", 0),
        "take_profits": counts.get("TAKE_PROFIT", 0),
        "partial_take_profits": counts.get("PARTIAL_TAKE_PROFIT", 0),
        "trailing_stops": counts.get("TRAILING_STOP", 0),
        "reaccelerations": counts.get("REACCELERATION", 0),
        "loss_threshold_exits": counts.get("LOSS_THRESHOLD", 0),
        "potential_drop_exits": counts.get("POTENTIAL_DROP", 0),
    }


def build_summary_md(rows: list[dict]) -> str:
    ordered = sorted(rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    best = ordered[0]
    lines = [
        "# Real Market Profit Tuning Summary",
        "",
        "## Ranking By Final PnL",
    ]
    for idx, row in enumerate(ordered, start=1):
        lines.append(
            f"{idx}. `{row['profile_name']}`: {row['final_pnl_percent']:+.2f}% | "
            f"final ${row['final_capital']:.2f} | entries {row['entries']} | "
            f"partials {row['partial_take_profits']} | reaccels {row['reaccelerations']} | "
            f"fees ${row['total_fees_paid']:.2f}"
        )
    lines.extend(
        [
            "",
            "## Best Profit Candidate",
            f"- Name: `{best['profile_name']}`",
            f"- Final capital: ${best['final_capital']:.2f}",
            f"- Final PnL: {best['final_pnl_percent']:+.2f}%",
            f"- Entries: {best['entries']}",
            f"- Partial take profits: {best['partial_take_profits']}",
            f"- Reaccelerations: {best['reaccelerations']}",
            f"- Fees: ${best['total_fees_paid']:.2f}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    historical_data = load_history(INPUT_PATH)
    rows = []
    for profile in PROFIT_PROFILES:
        results = simulate_modified_strategy(historical_data, profile)
        out_path = OUTPUT_DIR / f"{profile['name']}_results.json"
        save_json(out_path, results)
        rows.append(summarize(results))

    save_json(SUMMARY_JSON, {"profiles": rows})
    SUMMARY_MD.write_text(build_summary_md(rows), encoding="utf-8")

    ordered = sorted(rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    for row in ordered:
        print(
            f"{row['profile_name']}: pnl {row['final_pnl_percent']:+.2f}% | "
            f"final ${row['final_capital']:.2f} | entries {row['entries']} | fees ${row['total_fees_paid']:.2f}"
        )
    print(f"saved {SUMMARY_JSON.name}")
    print(f"saved {SUMMARY_MD.name}")


if __name__ == "__main__":
    main()
