from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_events(events_path: Path) -> dict[str, dict[str, Any]]:
    traces: dict[str, dict[str, Any]] = {}
    with events_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            event_type = str(row.get("event_type", "")).strip()
            payload = row.get("payload") or {}
            trace_id = str(payload.get("trace_id", "")).strip()
            if not trace_id:
                continue
            record = traces.setdefault(trace_id, {})
            record["symbol"] = str(row.get("symbol", "")).strip() or str(record.get("symbol", "")).strip()
            record[f"{event_type}_row"] = row
            record[f"{event_type}_payload"] = payload
    return traces


def build_trade_outcomes(traces: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trace_id, record in traces.items():
        realized_row = record.get("REALIZED_PNL_row")
        realized_payload = record.get("REALIZED_PNL_payload")
        if not isinstance(realized_row, dict) or not isinstance(realized_payload, dict):
            continue
        closed_payload = record.get("POSITION_CLOSED_payload") or {}
        trade_payload = record.get("TRADE_EXECUTED_payload") or {}
        hold_payload = record.get("POSITION_HOLD_TIME_payload") or {}
        exit_payload = record.get("EXIT_payload") or {}

        entry_price = trade_payload.get("entry_price", exit_payload.get("entry_price", 0.0))
        exit_price = trade_payload.get("exit_price", exit_payload.get("exit_price", 0.0))
        side = closed_payload.get("position_side") or exit_payload.get("position_side") or ""
        hold_time = hold_payload.get("hold_seconds", 0.0)
        pnl = realized_payload.get("pnl", 0.0)

        rows.append(
            {
                "symbol": str(record.get("symbol", "")).strip(),
                "side": str(side or "").strip(),
                "entry_price": round(float(entry_price or 0.0), 6),
                "exit_price": round(float(exit_price or 0.0), 6),
                "pnl": round(float(pnl or 0.0), 12),
                "pnl_display": round(float(pnl or 0.0), 6),
                "hold_time": round(float(hold_time or 0.0), 3),
                "entry_quality_score": 0.0,
                "timestamp": str(realized_row.get("ts", "")).strip(),
                "trace_id": trace_id,
            }
        )

    rows.sort(key=lambda row: str(row.get("timestamp", "")))
    return rows


def build_strategy_performance(trade_outcomes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "trades": 0,
            "pnl": 0.0,
            "wins": 0,
            "losses": 0,
            "avg_hold_time_sec": 0.0,
        }
    )
    for row in trade_outcomes:
        symbol = str(row.get("symbol", "")).strip()
        if not symbol:
            continue
        pnl = float(row.get("pnl", 0.0) or 0.0)
        hold = float(row.get("hold_time", 0.0) or 0.0)
        symbol_stats = stats[symbol]
        prev_trades = int(symbol_stats["trades"])
        symbol_stats["trades"] = prev_trades + 1
        symbol_stats["pnl"] = float(symbol_stats["pnl"]) + pnl
        if pnl > 0:
            symbol_stats["wins"] = int(symbol_stats["wins"]) + 1
        else:
            symbol_stats["losses"] = int(symbol_stats["losses"]) + 1
        prev_avg = float(symbol_stats["avg_hold_time_sec"])
        symbol_stats["avg_hold_time_sec"] = ((prev_avg * prev_trades) + hold) / max(1, symbol_stats["trades"])

    normalized: dict[str, dict[str, Any]] = {}
    for symbol, row in sorted(stats.items()):
        normalized[symbol] = {
            "trades": int(row["trades"]),
            "pnl": float(row["pnl"]),
            "wins": int(row["wins"]),
            "losses": int(row["losses"]),
            "avg_hold_time_sec": float(row["avg_hold_time_sec"]),
        }
    return normalized


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.stem}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}")
    backup.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild runtime trade artifacts from REALIZED_PNL events.")
    parser.add_argument("--events", default="logs/runtime/profitmax_v1_events.jsonl")
    parser.add_argument("--trade-outcomes", default="logs/runtime/trade_outcomes.json")
    parser.add_argument("--strategy-performance", default="logs/runtime/strategy_performance.json")
    args = parser.parse_args()

    events_path = Path(args.events)
    trade_outcomes_path = Path(args.trade_outcomes)
    strategy_performance_path = Path(args.strategy_performance)

    traces = load_events(events_path)
    trade_outcomes = build_trade_outcomes(traces)
    strategy_performance = build_strategy_performance(trade_outcomes)

    trade_backup = backup_file(trade_outcomes_path)
    perf_backup = backup_file(strategy_performance_path)

    trade_outcomes_path.write_text(json.dumps(trade_outcomes, ensure_ascii=False, indent=2), encoding="utf-8")
    strategy_performance_path.write_text(json.dumps(strategy_performance, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "ts": utc_now_text(),
        "events_path": str(events_path.resolve()),
        "trade_outcomes_path": str(trade_outcomes_path.resolve()),
        "strategy_performance_path": str(strategy_performance_path.resolve()),
        "trade_outcomes_backup": str(trade_backup.resolve()) if trade_backup else None,
        "strategy_performance_backup": str(perf_backup.resolve()) if perf_backup else None,
        "realized_pnl_trace_count": len(trade_outcomes),
        "strategy_symbol_count": len(strategy_performance),
        "trade_outcomes_pnl_sum": round(sum(float(row.get("pnl", 0.0) or 0.0) for row in trade_outcomes), 6),
        "strategy_performance_trade_sum": sum(int(row.get("trades", 0) or 0) for row in strategy_performance.values()),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
