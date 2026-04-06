"""Run imported strategy session analysis with fee-adjusted PnL.

The imported modules are kept unchanged. This runner subtracts a configurable
round-trip fee from each final trade and each partial event so the session
split is less optimistic than the original simple KPI.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backtester import run_backtest
from indicators import build_all
from signal_engine import Config, generate_signals


ROOT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT_DIR / "data" / "backtest_cache_v2"
OUTPUT_DIR = ROOT_DIR / "imported_files_zip" / "results"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
CACHE_SUFFIX = "5m_0.25y"
FEE_RATE_PER_SIDE = float(os.getenv("IMPORTED_BACKTEST_FEE_RATE_PER_SIDE", "0.0004"))
ROUND_TRIP_FEE_PCT = FEE_RATE_PER_SIDE * 2.0 * 100.0
SIGNAL_FILTER_MODES = {
    "all": None,
    "pullback": {"pullback"},
    "fractal_break": {"fractal_break"},
    "cloud_rebound": {"cloud_rebound"},
}


def get_market_session(timestamp: object) -> str:
    ts = pd.Timestamp(timestamp)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    ts = ts.tz_convert("UTC")
    hour = int(ts.hour)
    if 19 <= hour < 21 or 22 <= hour < 24:
        return "US_PEAK"
    if 16 <= hour < 18:
        return "EU_PEAK"
    if 8 <= hour < 10:
        return "ASIA_PEAK"
    if 2 <= hour < 7:
        return "DEAD_ZONE"
    return "NORMAL"


def clean_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


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


def fee_adjusted_pnl_pct(trade) -> float:
    return float(trade.pnl_pct) - ROUND_TRIP_FEE_PCT


def summarize_trades(trades: list) -> dict:
    final_trades = [trade for trade in trades if not trade.partial_exit]
    partial_trades = [trade for trade in trades if trade.partial_exit]
    final_net = [fee_adjusted_pnl_pct(trade) for trade in final_trades]
    all_net = [fee_adjusted_pnl_pct(trade) for trade in trades]
    wins = [value for value in final_net if value > 0]
    losses = [value for value in final_net if value < 0]
    gross_win = sum(value for value in final_net if value > 0)
    gross_loss = abs(sum(value for value in final_net if value < 0))
    by_signal = defaultdict(float)
    by_exit = Counter()
    by_side = Counter()
    for trade in trades:
        by_signal[clean_text(trade.signal.signal_type)] += fee_adjusted_pnl_pct(trade)
        by_exit[clean_text(trade.exit_reason)] += 1
        by_side[clean_text(trade.signal.side)] += 1
    return {
        "trade_events": int(len(trades)),
        "final_trades": int(len(final_trades)),
        "partial_events": int(len(partial_trades)),
        "wins_after_fee": int(len(wins)),
        "losses_after_fee": int(len(losses)),
        "win_rate_after_fee_pct": round((len(wins) / len(final_trades) * 100.0) if final_trades else 0.0, 6),
        "net_pnl_after_fee_pct": round(float(sum(all_net)), 6),
        "fee_drag_pct": round(float(ROUND_TRIP_FEE_PCT * len(trades)), 6),
        "avg_final_pnl_after_fee_pct": round(float(sum(final_net) / len(final_trades)), 6) if final_trades else 0.0,
        "profit_factor_after_fee": round(float(gross_win / gross_loss), 6) if gross_loss else None,
        "by_signal_type_pnl_after_fee_pct": {key: round(value, 6) for key, value in sorted(by_signal.items())},
        "exit_counts": dict(sorted(by_exit.items())),
        "side_counts": dict(sorted(by_side.items())),
    }


def run_symbol(symbol: str, cfg: Config, mode_name: str, allowed_signal_types: set[str] | None) -> dict:
    ltf = load_cached_5m(symbol)
    htf = resample_to_15m(ltf)
    ltf_ind = build_all(ltf)
    htf_ind = build_all(htf)
    signals = generate_signals(ltf_ind, htf_ind, cfg)
    if allowed_signal_types is not None:
        signals = [signal for signal in signals if signal.signal_type in allowed_signal_types]
    trades = run_backtest(ltf_ind, signals, cfg)

    session_trades = defaultdict(list)
    for trade in trades:
        session_trades[get_market_session(trade.signal.timestamp)].append(trade)

    return {
        "symbol": symbol,
        "mode": mode_name,
        "start": ltf.index[0].isoformat(),
        "end": ltf.index[-1].isoformat(),
        "signal_count": int(len(signals)),
        "session_summary": {
            session: summarize_trades(session_trades.get(session, []))
            for session in ["US_PEAK", "EU_PEAK", "ASIA_PEAK", "NORMAL", "DEAD_ZONE"]
        },
        "overall": summarize_trades(trades),
    }


def merge_session_reports(symbol_reports: list[dict]) -> dict:
    merged = {}
    for session in ["US_PEAK", "EU_PEAK", "ASIA_PEAK", "NORMAL", "DEAD_ZONE"]:
        totals = {
            "trade_events": 0,
            "final_trades": 0,
            "partial_events": 0,
            "wins_after_fee": 0,
            "losses_after_fee": 0,
            "net_pnl_after_fee_pct": 0.0,
            "fee_drag_pct": 0.0,
        }
        for report in symbol_reports:
            item = report["session_summary"][session]
            for key in totals:
                totals[key] += item[key]
        totals["win_rate_after_fee_pct"] = round(
            (totals["wins_after_fee"] / totals["final_trades"] * 100.0) if totals["final_trades"] else 0.0,
            6,
        )
        totals["net_pnl_after_fee_pct"] = round(float(totals["net_pnl_after_fee_pct"]), 6)
        totals["fee_drag_pct"] = round(float(totals["fee_drag_pct"]), 6)
        merged[session] = totals
    return merged


def main() -> None:
    cfg = Config()
    mode_reports = []
    for mode_name, allowed_signal_types in SIGNAL_FILTER_MODES.items():
        symbol_reports = [
            run_symbol(symbol, cfg, mode_name, allowed_signal_types)
            for symbol in SYMBOLS
        ]
        mode_reports.append({
            "mode": mode_name,
            "allowed_signal_types": sorted(list(allowed_signal_types)) if allowed_signal_types else ["all"],
            "session_summary": merge_session_reports(symbol_reports),
            "symbols": symbol_reports,
        })

    report = {
        "source": "imported_files_zip",
        "split_basis": "entry_time_utc_session",
        "fee_rate_per_side": FEE_RATE_PER_SIDE,
        "round_trip_fee_pct_per_event": ROUND_TRIP_FEE_PCT,
        "symbols": SYMBOLS,
        "cache_suffix": CACHE_SUFFIX,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "modes": mode_reports,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"imported_strategy_3m_sessions_fee_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps({
        "output_path": str(output_path),
        "fee_rate_per_side": FEE_RATE_PER_SIDE,
        "round_trip_fee_pct_per_event": ROUND_TRIP_FEE_PCT,
        "modes": [
            {
                "mode": mode["mode"],
                "session_summary": mode["session_summary"],
            }
            for mode in mode_reports
        ],
    }, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
