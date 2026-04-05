#!/usr/bin/env python3
"""Run the promoted remote-data candidate profile against the prepared external input."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from historical_data_profile_backtest import load_history
from modified_strategy_1year_simulation import (
    REMOTE_V3_DEFAULT_PROFILE,
    SCRIPT_DIR,
    save_json,
    simulate_modified_strategy,
)


INPUT_PATH = SCRIPT_DIR / "real_market_backtest_input.json"
OUTPUT_JSON = SCRIPT_DIR / "real_market_v3_remote_candidate_results.json"
OUTPUT_MD = SCRIPT_DIR / "real_market_v3_remote_candidate_report.md"


def build_report(results: dict) -> str:
    meta = results["simulation_metadata"]
    params = results["strategy_params"]
    counts = Counter(item["action"] for item in results["trade_history"])
    exits = counts.get("TAKE_PROFIT", 0) + counts.get("LOSS_THRESHOLD", 0) + counts.get("POTENTIAL_DROP", 0)
    win_rate = counts.get("TAKE_PROFIT", 0) / exits * 100.0 if exits else 0.0
    return "\n".join(
        [
            "# Real Market V3 Remote Candidate Report",
            "",
            "## Summary",
            f"- Profile: `{results['analysis_basis']['profile_name']}`",
            f"- Final capital: ${meta['final_capital']:.2f}",
            f"- Final PnL: {meta['final_pnl_percent']:+.2f}%",
            f"- Fees paid: ${meta['total_fees_paid']:.2f}",
            f"- Entries: {counts.get('ENTRY', 0)}",
            f"- Take profits: {counts.get('TAKE_PROFIT', 0)}",
            f"- Loss exits: {counts.get('LOSS_THRESHOLD', 0)}",
            f"- Potential-drop exits: {counts.get('POTENTIAL_DROP', 0)}",
            f"- Win rate: {win_rate:.1f}%",
            f"- Market regimes: {meta['market_regime_counts']}",
            "",
            "## Parameters",
            f"- Entry thresholds: {params['normal_threshold']} / {params['high_volatility_threshold']} / {params['extreme_threshold']}",
            f"- Regime volatility thresholds: {params['regime_volatility_thresholds']}",
            f"- Max symbols: {params['normal_max_symbols']} / {params['high_volatility_max_symbols']} / {params['extreme_max_symbols']}",
            f"- Take profit: {params['take_profit']}%",
            f"- Stop threshold: {params['replacement_threshold']}%",
            f"- Allocation: ${params['fixed_allocation']:.2f}",
        ]
    ) + "\n"


def main() -> None:
    historical_data = load_history(INPUT_PATH)
    results = simulate_modified_strategy(historical_data, REMOTE_V3_DEFAULT_PROFILE)
    results["analysis_basis"]["data_type"] = "external_historical_daily_data"
    results["analysis_basis"]["source_path"] = str(INPUT_PATH)
    save_json(OUTPUT_JSON, results)
    OUTPUT_MD.write_text(build_report(results), encoding="utf-8")

    meta = results["simulation_metadata"]
    print(f"remote v3 candidate final capital: ${meta['final_capital']:.2f}")
    print(f"remote v3 candidate pnl: {meta['final_pnl_percent']:+.2f}%")
    print(f"saved {OUTPUT_JSON.name}")
    print(f"saved {OUTPUT_MD.name}")


if __name__ == "__main__":
    main()
