#!/usr/bin/env python3
"""Compute risk metrics from a backtest result JSON."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_results(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def compute_max_drawdown(performance_history: list[dict]) -> dict:
    peak = None
    peak_date = None
    max_drawdown = 0.0
    trough_date = None
    for row in performance_history:
        total_value = float(row["total_value"])
        if peak is None or total_value > peak:
            peak = total_value
            peak_date = row["date"]
        if peak:
            drawdown = (total_value - peak) / peak * 100.0
            if drawdown < max_drawdown:
                max_drawdown = drawdown
                trough_date = row["date"]
    return {
        "max_drawdown_percent": max_drawdown,
        "peak_date": peak_date,
        "trough_date": trough_date,
    }


def compute_loss_streaks(trade_history: list[dict]) -> dict:
    max_loss_streak = 0
    current_loss_streak = 0
    max_win_streak = 0
    current_win_streak = 0
    for trade in trade_history:
        action = trade.get("action")
        if action == "ENTRY":
            continue
        realized = float(trade.get("realized_pnl", 0.0))
        if realized < 0:
            current_loss_streak += 1
            current_win_streak = 0
        elif realized > 0:
            current_win_streak += 1
            current_loss_streak = 0
        else:
            current_loss_streak = 0
            current_win_streak = 0
        max_loss_streak = max(max_loss_streak, current_loss_streak)
        max_win_streak = max(max_win_streak, current_win_streak)
    return {
        "max_consecutive_losses": max_loss_streak,
        "max_consecutive_wins": max_win_streak,
    }


def compute_monthly_returns(performance_history: list[dict], initial_capital: float) -> list[dict]:
    monthly = defaultdict(list)
    for row in performance_history:
        monthly[row["date"][:7]].append(row)

    monthly_rows = []
    prev_month_end = initial_capital
    for month in sorted(monthly):
        rows = monthly[month]
        start_value = prev_month_end
        end_value = float(rows[-1]["total_value"])
        monthly_return = ((end_value - start_value) / start_value * 100.0) if start_value else 0.0
        monthly_rows.append(
            {
                "month": month,
                "start_value": start_value,
                "end_value": end_value,
                "monthly_return_percent": monthly_return,
            }
        )
        prev_month_end = end_value
    return monthly_rows


def build_report(results: dict, risk: dict) -> str:
    meta = results["simulation_metadata"]
    action_counts = Counter(item["action"] for item in results["trade_history"])
    monthly_lines = [
        f"- {row['month']}: {row['monthly_return_percent']:+.2f}% ({row['start_value']:.2f} -> {row['end_value']:.2f})"
        for row in risk["monthly_returns"]
    ]
    return "\n".join(
        [
            "# Backtest Risk Analysis",
            "",
            "## Summary",
            f"- Final capital: ${meta['final_capital']:.2f}",
            f"- Final PnL: {meta['final_pnl_percent']:+.2f}%",
            f"- Fees paid: ${meta['total_fees_paid']:.2f}",
            f"- Entries: {action_counts.get('ENTRY', 0)}",
            f"- Take profits: {action_counts.get('TAKE_PROFIT', 0)}",
            f"- Loss exits: {action_counts.get('LOSS_THRESHOLD', 0)}",
            f"- Potential-drop exits: {action_counts.get('POTENTIAL_DROP', 0)}",
            "",
            "## Risk Metrics",
            f"- Max drawdown: {risk['max_drawdown']['max_drawdown_percent']:.2f}%",
            f"- Peak date: {risk['max_drawdown']['peak_date']}",
            f"- Trough date: {risk['max_drawdown']['trough_date']}",
            f"- Max consecutive losses: {risk['loss_streaks']['max_consecutive_losses']}",
            f"- Max consecutive wins: {risk['loss_streaks']['max_consecutive_wins']}",
            "",
            "## Monthly Returns",
            *monthly_lines,
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze risk metrics from a backtest result JSON.")
    parser.add_argument("input_path", help="Path to a backtest result JSON.")
    parser.add_argument("--output", help="Optional markdown output path.")
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    results = load_results(input_path)
    performance_history = results.get("performance_history", [])
    trade_history = results.get("trade_history", [])
    initial_capital = float(results["simulation_metadata"]["initial_capital"])

    risk = {
        "max_drawdown": compute_max_drawdown(performance_history),
        "loss_streaks": compute_loss_streaks(trade_history),
        "monthly_returns": compute_monthly_returns(performance_history, initial_capital),
    }

    output_path = Path(args.output).resolve() if args.output else input_path.with_name(f"{input_path.stem}_risk_report.md")
    output_path.write_text(build_report(results, risk), encoding="utf-8")

    print(f"max drawdown: {risk['max_drawdown']['max_drawdown_percent']:.2f}%")
    print(f"max consecutive losses: {risk['loss_streaks']['max_consecutive_losses']}")
    print(f"saved {output_path}")


if __name__ == "__main__":
    main()
