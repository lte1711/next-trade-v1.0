#!/usr/bin/env python3
"""Third-stage tuning focused on reducing drawdown for the remote candidate."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from backtest_risk_analysis import compute_loss_streaks, compute_max_drawdown
from historical_data_profile_backtest import load_history
from modified_strategy_1year_simulation import (
    REMOTE_V3_DEFAULT_PROFILE,
    REMOTE_V3_REFERENCE_PROFILE,
    save_json,
    simulate_modified_strategy,
)


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_PATH = SCRIPT_DIR / "real_market_backtest_input.json"
OUTPUT_DIR = SCRIPT_DIR / "real_market_risk_tuning_results"
SUMMARY_JSON = OUTPUT_DIR / "real_market_risk_tuning_summary.json"
SUMMARY_MD = OUTPUT_DIR / "real_market_risk_tuning_summary.md"


RISK_PROFILES = [
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "remote_risk_reference",
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "remote_drawdown_guard",
        "entry_thresholds": {"NORMAL": 70.0, "HIGH_VOLATILITY": 74.0, "EXTREME": 78.0},
        "fixed_allocation": 160.0,
        "replacement_threshold": -1.0,
        "take_profit": 2.8,
        "exit_buffer": 7.0,
    },
    {
        **REMOTE_V3_DEFAULT_PROFILE,
        "name": "remote_capital_preserver",
    },
    {
        **REMOTE_V3_REFERENCE_PROFILE,
        "name": "remote_smoother_equity",
        "entry_thresholds": {"NORMAL": 69.0, "HIGH_VOLATILITY": 73.0, "EXTREME": 77.0},
        "fixed_allocation": 150.0,
        "replacement_threshold": -1.1,
        "take_profit": 2.7,
        "entry_buffer": 1.0,
        "exit_buffer": 7.0,
        "minimum_hold_bars": 2,
    },
]


def summarize(results: dict) -> dict:
    meta = results["simulation_metadata"]
    trade_counts = Counter(item["action"] for item in results["trade_history"])
    max_dd = compute_max_drawdown(results["performance_history"])
    streaks = compute_loss_streaks(results["trade_history"])
    return {
        "profile_name": results["analysis_basis"]["profile_name"],
        "final_capital": meta["final_capital"],
        "final_pnl_percent": meta["final_pnl_percent"],
        "total_fees_paid": meta["total_fees_paid"],
        "entries": trade_counts.get("ENTRY", 0),
        "take_profits": trade_counts.get("TAKE_PROFIT", 0),
        "loss_threshold_exits": trade_counts.get("LOSS_THRESHOLD", 0),
        "potential_drop_exits": trade_counts.get("POTENTIAL_DROP", 0),
        "max_drawdown_percent": max_dd["max_drawdown_percent"],
        "max_consecutive_losses": streaks["max_consecutive_losses"],
        "risk_adjusted_score": meta["final_pnl_percent"] + max_dd["max_drawdown_percent"],
    }


def build_summary_md(rows: list[dict]) -> str:
    ordered = sorted(rows, key=lambda row: (row["risk_adjusted_score"], row["final_pnl_percent"]), reverse=True)
    best = ordered[0]
    lines = [
        "# Real Market V3 Risk Tuning Summary",
        "",
        "## Ranking By Risk-Adjusted Score",
    ]
    for idx, row in enumerate(ordered, start=1):
        lines.append(
            f"{idx}. `{row['profile_name']}`: pnl {row['final_pnl_percent']:+.2f}% | "
            f"max DD {row['max_drawdown_percent']:.2f}% | score {row['risk_adjusted_score']:+.2f} | "
            f"entries {row['entries']} | fees ${row['total_fees_paid']:.2f}"
        )
    lines.extend(
        [
            "",
            "## Best Risk-Adjusted Candidate",
            f"- Name: `{best['profile_name']}`",
            f"- Final capital: ${best['final_capital']:.2f}",
            f"- Final PnL: {best['final_pnl_percent']:+.2f}%",
            f"- Max drawdown: {best['max_drawdown_percent']:.2f}%",
            f"- Max consecutive losses: {best['max_consecutive_losses']}",
            "",
            "## Interpretation",
            "- `remote_drawdown_guard` tightens entries and shrinks size first.",
            "- `remote_capital_preserver` is the most defensive variant.",
            "- `remote_smoother_equity` aims to reduce churn without over-tightening entries.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    historical_data = load_history(INPUT_PATH)
    rows = []
    for profile in RISK_PROFILES:
        results = simulate_modified_strategy(historical_data, profile)
        out_path = OUTPUT_DIR / f"{profile['name']}_results.json"
        save_json(out_path, results)
        rows.append(summarize(results))

    save_json(SUMMARY_JSON, {"profiles": rows})
    SUMMARY_MD.write_text(build_summary_md(rows), encoding="utf-8")

    ordered = sorted(rows, key=lambda row: (row["risk_adjusted_score"], row["final_pnl_percent"]), reverse=True)
    for row in ordered:
        print(
            f"{row['profile_name']}: pnl {row['final_pnl_percent']:+.2f}% | "
            f"maxDD {row['max_drawdown_percent']:.2f}% | score {row['risk_adjusted_score']:+.2f} | "
            f"entries {row['entries']} | fees ${row['total_fees_paid']:.2f}"
        )
    print(f"saved {SUMMARY_JSON.name}")
    print(f"saved {SUMMARY_MD.name}")


if __name__ == "__main__":
    main()
