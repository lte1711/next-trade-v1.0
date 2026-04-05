#!/usr/bin/env python3
"""Second-stage tuning around the best concentrated_swing profile."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from modified_strategy_1year_simulation import generate_historical_data, save_json, simulate_modified_strategy


SCRIPT_DIR = Path(__file__).resolve().parent
ROUND2_DIR = SCRIPT_DIR / "round2_tuning_results"
SUMMARY_JSON_PATH = ROUND2_DIR / "modified_strategy_round2_summary.json"
SUMMARY_MD_PATH = ROUND2_DIR / "modified_strategy_round2_summary.md"


ROUND2_PROFILES = [
    {
        "name": "cs_base_reference",
        "entry_thresholds": {"NORMAL": 60.0, "HIGH_VOLATILITY": 62.0, "EXTREME": 58.0},
        "profit_potential_offset": 26.0,
        "entry_buffer": -3.0,
        "exit_buffer": 3.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 200.0,
        "take_profit": 2.5,
        "replacement_threshold": -1.0,
        "minimum_hold_bars": 1,
    },
    {
        "name": "cs_hold_winners",
        "entry_thresholds": {"NORMAL": 60.0, "HIGH_VOLATILITY": 62.0, "EXTREME": 58.0},
        "profit_potential_offset": 26.0,
        "entry_buffer": -3.0,
        "exit_buffer": 6.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 200.0,
        "take_profit": 2.8,
        "replacement_threshold": -1.0,
        "minimum_hold_bars": 2,
    },
    {
        "name": "cs_wider_stop",
        "entry_thresholds": {"NORMAL": 60.0, "HIGH_VOLATILITY": 62.0, "EXTREME": 58.0},
        "profit_potential_offset": 26.0,
        "entry_buffer": -3.0,
        "exit_buffer": 6.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 200.0,
        "take_profit": 3.0,
        "replacement_threshold": -1.4,
        "minimum_hold_bars": 2,
    },
    {
        "name": "cs_more_entries",
        "entry_thresholds": {"NORMAL": 58.0, "HIGH_VOLATILITY": 60.0, "EXTREME": 56.0},
        "profit_potential_offset": 28.0,
        "entry_buffer": -4.0,
        "exit_buffer": 5.0,
        "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
        "fixed_allocation": 180.0,
        "take_profit": 2.6,
        "replacement_threshold": -1.1,
        "minimum_hold_bars": 1,
    },
    {
        "name": "cs_conviction",
        "entry_thresholds": {"NORMAL": 62.0, "HIGH_VOLATILITY": 64.0, "EXTREME": 60.0},
        "profit_potential_offset": 24.0,
        "entry_buffer": -2.0,
        "exit_buffer": 5.0,
        "max_symbols_by_regime": {"NORMAL": 1, "HIGH_VOLATILITY": 1, "EXTREME": 1},
        "fixed_allocation": 250.0,
        "take_profit": 3.2,
        "replacement_threshold": -1.2,
        "minimum_hold_bars": 2,
    },
]


def summarize(results: dict) -> dict:
    meta = results["simulation_metadata"]
    counts = Counter(item["action"] for item in results["trade_history"])
    exits = counts.get("TAKE_PROFIT", 0) + counts.get("LOSS_THRESHOLD", 0) + counts.get("POTENTIAL_DROP", 0)
    active_days = sum(1 for row in results["performance_history"] if row["invested_symbols"] > 0)
    avg_symbols = (
        sum(row["invested_symbols"] for row in results["performance_history"]) / len(results["performance_history"])
        if results["performance_history"]
        else 0.0
    )
    return {
        "profile_name": results["analysis_basis"]["profile_name"],
        "final_capital": meta["final_capital"],
        "final_pnl_percent": meta["final_pnl_percent"],
        "total_fees_paid": meta["total_fees_paid"],
        "realized_pnl": meta["realized_pnl"],
        "entries": counts.get("ENTRY", 0),
        "take_profits": counts.get("TAKE_PROFIT", 0),
        "loss_threshold_exits": counts.get("LOSS_THRESHOLD", 0),
        "potential_drop_exits": counts.get("POTENTIAL_DROP", 0),
        "win_rate_percent": (counts.get("TAKE_PROFIT", 0) / exits * 100.0) if exits else 0.0,
        "active_days": active_days,
        "avg_invested_symbols": avg_symbols,
    }


def build_summary_markdown(rows: list[dict]) -> str:
    ordered = sorted(rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    best = ordered[0]
    lines = [
        "# Modified Strategy Round 2 Tuning Summary",
        "",
        "## Ranking",
    ]
    for index, row in enumerate(ordered, start=1):
        lines.append(
            f"{index}. `{row['profile_name']}`: {row['final_pnl_percent']:+.2f}% | "
            f"final ${row['final_capital']:.2f} | entries {row['entries']} | "
            f"TP {row['take_profits']} | LS {row['loss_threshold_exits']} | "
            f"PD {row['potential_drop_exits']} | fees ${row['total_fees_paid']:.2f}"
        )

    lines.extend(
        [
            "",
            "## Best Variant",
            f"- Name: `{best['profile_name']}`",
            f"- Final capital: ${best['final_capital']:.2f}",
            f"- Final PnL: {best['final_pnl_percent']:+.2f}%",
            f"- Entries: {best['entries']}",
            f"- Win rate: {best['win_rate_percent']:.1f}%",
            f"- Fees: ${best['total_fees_paid']:.2f}",
            "",
            "## Reading Guide",
            "- `cs_hold_winners` tests whether looser potential-drop exits preserve upside.",
            "- `cs_wider_stop` tests a wider stop and higher take profit for bigger swings.",
            "- `cs_more_entries` tests a more active, lower-threshold variant.",
            "- `cs_conviction` tests fewer but larger bets.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)
    historical_data = generate_historical_data()

    summary_rows = []
    for profile in ROUND2_PROFILES:
        results = simulate_modified_strategy(historical_data, profile)
        out_path = ROUND2_DIR / f"{profile['name']}_results.json"
        save_json(out_path, results)
        summary_rows.append(summarize(results))

    save_json(SUMMARY_JSON_PATH, {"profiles": summary_rows})
    SUMMARY_MD_PATH.write_text(build_summary_markdown(summary_rows), encoding="utf-8")

    ordered = sorted(summary_rows, key=lambda row: row["final_pnl_percent"], reverse=True)
    for row in ordered:
        print(
            f"{row['profile_name']}: pnl {row['final_pnl_percent']:+.2f}% | "
            f"final ${row['final_capital']:.2f} | entries {row['entries']} | "
            f"win {row['win_rate_percent']:.1f}% | fees ${row['total_fees_paid']:.2f}"
        )
    print(f"saved {SUMMARY_JSON_PATH.name}")
    print(f"saved {SUMMARY_MD_PATH.name}")


if __name__ == "__main__":
    main()
