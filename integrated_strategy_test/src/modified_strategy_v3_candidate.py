#!/usr/bin/env python3
"""Run the promoted v3 candidate profile on the deterministic 1-year synthetic dataset."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from modified_strategy_1year_simulation import (
    SCRIPT_DIR,
    V3_CANDIDATE_PROFILE,
    generate_historical_data,
    save_json,
    simulate_modified_strategy,
)


OUTPUT_JSON = SCRIPT_DIR / "modified_strategy_v3_candidate_results.json"
OUTPUT_MD = SCRIPT_DIR / "modified_strategy_v3_candidate_report.md"


def build_report(results: dict) -> str:
    meta = results["simulation_metadata"]
    params = results["strategy_params"]
    counts = Counter(item["action"] for item in results["trade_history"])
    closed = counts.get("TAKE_PROFIT", 0) + counts.get("LOSS_THRESHOLD", 0) + counts.get("POTENTIAL_DROP", 0)
    win_rate = counts.get("TAKE_PROFIT", 0) / closed * 100.0 if closed else 0.0
    return "\n".join(
        [
            "# Modified Strategy V3 Candidate Report",
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
            "",
            "## Parameters",
            f"- Entry thresholds: {params['normal_threshold']} / {params['high_volatility_threshold']} / {params['extreme_threshold']}",
            f"- Max symbols: {params['normal_max_symbols']} / {params['high_volatility_max_symbols']} / {params['extreme_max_symbols']}",
            f"- Take profit: {params['take_profit']}%",
            f"- Stop threshold: {params['replacement_threshold']}%",
            f"- Allocation: ${params['fixed_allocation']:.2f}",
            "",
            "## Caveat",
            "- This result still uses deterministic synthetic daily data for tuning only.",
        ]
    ) + "\n"


def main() -> None:
    historical_data = generate_historical_data()
    results = simulate_modified_strategy(historical_data, V3_CANDIDATE_PROFILE)
    save_json(OUTPUT_JSON, results)
    OUTPUT_MD.write_text(build_report(results), encoding="utf-8")

    meta = results["simulation_metadata"]
    print(f"v3 candidate final capital: ${meta['final_capital']:.2f}")
    print(f"v3 candidate pnl: {meta['final_pnl_percent']:+.2f}%")
    print(f"saved {OUTPUT_JSON.name}")
    print(f"saved {OUTPUT_MD.name}")


if __name__ == "__main__":
    main()
