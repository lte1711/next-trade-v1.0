"""
Entry point for the merged partial integration workspace.
"""

import json
from pathlib import Path

from merged_partial_v2.simulation.strategy_engine import MergedPartialStrategyEngine


def main() -> None:
    """Build a merged snapshot and write it into the merge workspace."""
    engine = MergedPartialStrategyEngine(symbol_count=10)
    snapshot = engine.build_combined_snapshot(limit=80)

    selected_symbols = snapshot["market"]["selected_symbols"]
    print(f"Market regime: {snapshot['market']['market_regime']}")
    print(f"Selected symbols: {len(selected_symbols)}")
    for item in selected_symbols[:10]:
        print(
            f"{item['symbol']} | "
            f"bullish={item['bullish_score']:.1f} | "
            f"potential={item['profit_potential']:.1f} | "
            f"change={item['change_percent']:+.2f}%"
        )

    output_path = Path(__file__).resolve().parents[2] / "merged_snapshot.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
