"""Run the imported strategy against cached three-month Binance futures data.

This file is a thin runner around the imported modules. It does not modify the
strategy rules and only adapts cached OHLCV data into the expected DataFrames.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backtester import calc_kpi, run_backtest
from indicators import build_all
from signal_engine import Config, generate_signals


ROOT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT_DIR / "data" / "backtest_cache_v2"
OUTPUT_DIR = ROOT_DIR / "imported_files_zip" / "results"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
CACHE_SUFFIX = "5m_0.25y"
SIGNAL_FILTER_MODES = {
    "all": None,
    "pullback": {"pullback"},
    "fractal_break": {"fractal_break"},
    "cloud_rebound": {"cloud_rebound"},
}


def clean_text(value: object) -> str:
    text = str(value)
    return text.encode("ascii", "backslashreplace").decode("ascii")


def clean_mapping(mapping: dict) -> dict:
    return {clean_text(key): value for key, value in mapping.items()}


def clean_kpi(kpi: dict) -> dict:
    cleaned = dict(kpi)
    cleaned.pop("equity_curve", None)
    if "by_signal_type" in cleaned:
        cleaned["by_signal_type"] = {
            clean_text(key): value for key, value in cleaned["by_signal_type"].items()
        }
    return cleaned


def load_cached_5m(symbol: str) -> pd.DataFrame:
    cache_path = CACHE_DIR / f"{symbol}_{CACHE_SUFFIX}.json"
    rows = json.loads(cache_path.read_text(encoding="utf-8"))
    frame = pd.DataFrame(
        [
            {
                "timestamp": pd.to_datetime(int(row[0]), unit="ms", utc=True),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
            }
            for row in rows
        ]
    )
    return frame.set_index("timestamp").sort_index()


def resample_to_15m(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.resample("15min").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    }).dropna()


def run_symbol(symbol: str, cfg: Config, mode_name: str, allowed_signal_types: set[str] | None) -> dict:
    ltf = load_cached_5m(symbol)
    htf = resample_to_15m(ltf)
    ltf_ind = build_all(ltf)
    htf_ind = build_all(htf)
    signals = generate_signals(ltf_ind, htf_ind, cfg)
    if allowed_signal_types is not None:
        signals = [signal for signal in signals if signal.signal_type in allowed_signal_types]
    trades = run_backtest(ltf_ind, signals, cfg)
    kpi = calc_kpi(trades)
    side_counts = Counter(signal.side for signal in signals)
    type_counts = Counter(signal.signal_type for signal in signals)
    exit_counts = Counter(trade.exit_reason for trade in trades)
    return {
        "symbol": symbol,
        "mode": mode_name,
        "start": ltf.index[0].isoformat(),
        "end": ltf.index[-1].isoformat(),
        "ltf_rows": int(len(ltf)),
        "htf_rows": int(len(htf)),
        "signal_count": int(len(signals)),
        "trade_event_count": int(len(trades)),
        "side_counts": clean_mapping(dict(side_counts)),
        "signal_type_counts": clean_mapping(dict(type_counts)),
        "exit_reason_counts": clean_mapping(dict(exit_counts)),
        "kpi": clean_kpi(kpi),
    }


def main() -> None:
    cfg = Config()
    mode_reports = []
    for mode_name, allowed_signal_types in SIGNAL_FILTER_MODES.items():
        results = [
            run_symbol(symbol, cfg, mode_name, allowed_signal_types)
            for symbol in SYMBOLS
        ]
        combined_net_pnl_pct = sum(item.get("kpi", {}).get("net_pnl_pct", 0.0) for item in results)
        combined_final_trades = sum(item.get("kpi", {}).get("total_trades", 0) for item in results)
        combined_wins = sum(item.get("kpi", {}).get("wins", 0) for item in results)
        combined_losses = sum(item.get("kpi", {}).get("losses", 0) for item in results)
        combined_win_rate = (combined_wins / combined_final_trades * 100.0) if combined_final_trades else 0.0
        mode_reports.append({
            "mode": mode_name,
            "allowed_signal_types": sorted(list(allowed_signal_types)) if allowed_signal_types else ["all"],
            "summary": {
                "combined_net_pnl_pct_simple_sum": round(combined_net_pnl_pct, 6),
                "combined_final_trades": int(combined_final_trades),
                "combined_wins": int(combined_wins),
                "combined_losses": int(combined_losses),
                "combined_win_rate_pct": round(combined_win_rate, 6),
            },
            "results": results,
        })

    report = {
        "source": "imported_files_zip",
        "symbols": SYMBOLS,
        "cache_suffix": CACHE_SUFFIX,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "modes": mode_reports,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"imported_strategy_3m_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps({
        "output_path": str(output_path),
        "modes": [
            {
                "mode": mode["mode"],
                "summary": mode["summary"],
                "per_symbol": [
                    {
                        "symbol": item["symbol"],
                        "signals": item["signal_count"],
                        "trades": item.get("kpi", {}).get("total_trades", 0),
                        "win_rate_pct": item.get("kpi", {}).get("win_rate_pct", 0.0),
                        "net_pnl_pct": item.get("kpi", {}).get("net_pnl_pct", 0.0),
                    }
                    for item in mode["results"]
                ],
            }
            for mode in mode_reports
        ],
    }, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
