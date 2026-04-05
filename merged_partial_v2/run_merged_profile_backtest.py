"""Run merged_partial_v2 profiles against a 1-year historical dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MERGED_SRC = ROOT / "src"
HISTORICAL_SRC = ROOT.parent / "integrated_strategy_test" / "src"
if str(MERGED_SRC) not in sys.path:
    sys.path.insert(0, str(MERGED_SRC))
if str(HISTORICAL_SRC) not in sys.path:
    sys.path.insert(0, str(HISTORICAL_SRC))

from historical_data_profile_backtest import load_history  # noqa: E402
from modified_strategy_1year_simulation import save_json, simulate_modified_strategy  # noqa: E402
from merged_partial_v2.main import load_merge_config, load_profile_metrics  # noqa: E402
from merged_partial_v2.services.profile_switcher_service import (  # noqa: E402
    REMOTE_DEFAULT_PROFILE,
    REMOTE_RISK_REFERENCE_PROFILE,
)


PROFILE_MAP = {
    REMOTE_DEFAULT_PROFILE["name"]: REMOTE_DEFAULT_PROFILE,
    REMOTE_RISK_REFERENCE_PROFILE["name"]: REMOTE_RISK_REFERENCE_PROFILE,
}


def resolve_profile(profile_name: str) -> dict:
    normalized = profile_name.strip().lower()
    for name, profile in PROFILE_MAP.items():
        if normalized == name.lower():
            return dict(profile)
    raise ValueError(f"Unknown merged profile: {profile_name}")


def build_output_path(profile_name: str) -> Path:
    output_dir = ROOT / "backtest_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = profile_name.replace(" ", "_")
    return output_dir / f"{safe_name}_1year_backtest.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest merged_partial_v2 profiles on 1-year historical data.")
    parser.add_argument(
        "--input-path",
        default=str(ROOT.parent / "integrated_strategy_test" / "src" / "real_market_backtest_input.json"),
        help="CSV or JSON historical input path.",
    )
    parser.add_argument(
        "--profile-name",
        default=None,
        help="Merged profile name to backtest. Defaults to config current/default profile.",
    )
    args = parser.parse_args()

    config = load_merge_config()
    selection_config, _ = load_profile_metrics(config)
    profile_name = (
        args.profile_name
        or selection_config.get("current_metrics_profile_name")
        or selection_config.get("default_profile_name")
        or REMOTE_DEFAULT_PROFILE["name"]
    )
    profile = resolve_profile(profile_name)

    input_path = Path(args.input_path).resolve()
    historical_data = load_history(input_path)
    results = simulate_modified_strategy(historical_data, profile)
    results["analysis_basis"]["data_type"] = "merged_partial_v2_external_historical_daily_data"
    results["analysis_basis"]["source_path"] = str(input_path)
    results["analysis_basis"]["merged_profile_name"] = profile["name"]
    results["analysis_basis"]["merged_workspace"] = str(ROOT)

    output_path = build_output_path(profile["name"])
    save_json(output_path, results)

    meta = results["simulation_metadata"]
    summary = {
        "profile_name": profile["name"],
        "source_path": str(input_path),
        "start_date": meta["start_date"],
        "end_date": meta["end_date"],
        "total_days": meta["total_days"],
        "final_capital": round(meta["final_capital"], 2),
        "final_pnl_percent": round(meta["final_pnl_percent"], 2),
        "total_fees_paid": round(meta["total_fees_paid"], 2),
        "market_regime_counts": meta.get("market_regime_counts", {}),
        "output_path": str(output_path),
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
