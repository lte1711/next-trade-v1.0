#!/usr/bin/env python3
"""Generate a focused comparison report between the aggressive and balanced remote candidates."""

from __future__ import annotations

import json
from pathlib import Path

from backtest_risk_analysis import compute_loss_streaks, compute_max_drawdown, compute_monthly_returns


SCRIPT_DIR = Path(__file__).resolve().parent
REFERENCE_PATH = SCRIPT_DIR / "real_market_risk_tuning_results" / "remote_risk_reference_results.json"
DEFAULT_PATH = SCRIPT_DIR / "real_market_v3_remote_candidate_results.json"
OUTPUT_MD = SCRIPT_DIR / "real_market_remote_final_comparison.md"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summarize(results: dict) -> dict:
    meta = results["simulation_metadata"]
    performance_history = results["performance_history"]
    trade_history = results["trade_history"]
    drawdown = compute_max_drawdown(performance_history)
    streaks = compute_loss_streaks(trade_history)
    monthly = compute_monthly_returns(performance_history, float(meta["initial_capital"]))
    positive_months = sum(1 for row in monthly if row["monthly_return_percent"] > 0)
    negative_months = sum(1 for row in monthly if row["monthly_return_percent"] < 0)
    return {
        "profile_name": results["analysis_basis"]["profile_name"],
        "final_capital": meta["final_capital"],
        "final_pnl_percent": meta["final_pnl_percent"],
        "fees": meta["total_fees_paid"],
        "max_drawdown": drawdown["max_drawdown_percent"],
        "max_consecutive_losses": streaks["max_consecutive_losses"],
        "positive_months": positive_months,
        "negative_months": negative_months,
    }


def build_report(reference: dict, default: dict) -> str:
    ref = summarize(reference)
    bal = summarize(default)
    return "\n".join(
        [
            "# Real Market Remote Final Comparison",
            "",
            "## Aggressive vs Balanced",
            f"- Aggressive reference: `{ref['profile_name']}`",
            f"  Final capital ${ref['final_capital']:.2f} | PnL {ref['final_pnl_percent']:+.2f}% | "
            f"Max DD {ref['max_drawdown']:.2f}% | Fees ${ref['fees']:.2f} | "
            f"Max loss streak {ref['max_consecutive_losses']} | Up months {ref['positive_months']} / Down months {ref['negative_months']}",
            f"- Balanced default: `{bal['profile_name']}`",
            f"  Final capital ${bal['final_capital']:.2f} | PnL {bal['final_pnl_percent']:+.2f}% | "
            f"Max DD {bal['max_drawdown']:.2f}% | Fees ${bal['fees']:.2f} | "
            f"Max loss streak {bal['max_consecutive_losses']} | Up months {bal['positive_months']} / Down months {bal['negative_months']}",
            "",
            "## Recommendation",
            "- Choose the aggressive reference when maximizing upside is the top priority and a deeper drawdown is acceptable.",
            "- Choose the balanced default when adoption safety matters more and you want materially lower drawdown with still-strong returns.",
            "",
            "## Default Decision",
            "- The balanced candidate remains the recommended default profile.",
            "- The aggressive reference should remain an alternate high-beta profile for controlled experiments.",
        ]
    ) + "\n"


def main() -> None:
    reference = load_json(REFERENCE_PATH)
    default = load_json(DEFAULT_PATH)
    OUTPUT_MD.write_text(build_report(reference, default), encoding="utf-8")
    print(f"saved {OUTPUT_MD.name}")


if __name__ == "__main__":
    main()
