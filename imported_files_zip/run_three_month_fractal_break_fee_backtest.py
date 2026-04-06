"""Run only the imported fractal-break strategy with fee-adjusted session output."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from signal_engine import Config
from run_three_month_session_fee_backtest import (
    CACHE_SUFFIX,
    FEE_RATE_PER_SIDE,
    OUTPUT_DIR,
    ROUND_TRIP_FEE_PCT,
    SYMBOLS,
    merge_session_reports,
    run_symbol,
)


def main() -> None:
    cfg = Config()
    symbol_reports = [
        run_symbol(symbol, cfg, "fractal_break", {"fractal_break"})
        for symbol in SYMBOLS
    ]
    report = {
        "source": "imported_files_zip",
        "mode": "fractal_break",
        "allowed_signal_types": ["fractal_break"],
        "split_basis": "entry_time_utc_session",
        "fee_rate_per_side": FEE_RATE_PER_SIDE,
        "round_trip_fee_pct_per_event": ROUND_TRIP_FEE_PCT,
        "symbols": SYMBOLS,
        "cache_suffix": CACHE_SUFFIX,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session_summary": merge_session_reports(symbol_reports),
        "symbol_reports": symbol_reports,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"imported_fractal_break_3m_fee_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps({
        "output_path": str(output_path),
        "fee_rate_per_side": FEE_RATE_PER_SIDE,
        "round_trip_fee_pct_per_event": ROUND_TRIP_FEE_PCT,
        "session_summary": report["session_summary"],
        "per_symbol": [
            {
                "symbol": item["symbol"],
                "overall": item["overall"],
            }
            for item in symbol_reports
        ],
    }, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
