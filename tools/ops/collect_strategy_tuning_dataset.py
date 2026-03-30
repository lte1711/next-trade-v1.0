from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any


ROOT = Path(os.getenv("NT_PROJECT_ROOT") or Path(__file__).resolve().parents[2])
RUNTIME_DIR = ROOT / "logs" / "runtime"
EVENTS_LOG = RUNTIME_DIR / "profitmax_v1_events.jsonl"
TRADE_OUTCOMES = RUNTIME_DIR / "trade_outcomes.json"
STRATEGY_PERFORMANCE = RUNTIME_DIR / "strategy_performance.json"
OUT_PATH = RUNTIME_DIR / "strategy_tuning_dataset.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except Exception:
                continue
            if isinstance(row, dict):
                yield row


def main() -> int:
    trade_outcomes = load_json(TRADE_OUTCOMES, [])
    strategy_performance = load_json(STRATEGY_PERFORMANCE, {})

    exit_reason_counts: dict[str, int] = defaultdict(int)
    symbol_event_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    realized_pnl_by_symbol: dict[str, float] = defaultdict(float)
    entry_quality_samples: list[dict[str, Any]] = []
    hold_time_samples: list[dict[str, Any]] = []
    recent_events: list[dict[str, Any]] = []

    for row in iter_jsonl(EVENTS_LOG) or []:
        event_type = str(row.get("event_type", "")).strip()
        symbol = str(row.get("symbol", "")).upper().strip() or "-"
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        symbol_event_counts[symbol][event_type] += 1

        if event_type == "REALIZED_PNL":
            realized_pnl_by_symbol[symbol] += float(payload.get("pnl", 0.0) or 0.0)
        elif event_type == "EXIT":
            exit_reason = str(payload.get("reason", "")).strip() or "unknown"
            exit_reason_counts[exit_reason] += 1
        elif event_type == "ENTRY_QUALITY_GATE":
            entry_quality_samples.append(
                {
                    "ts": row.get("ts"),
                    "symbol": symbol,
                    "entry_quality_score": payload.get("entry_quality_score"),
                    "expected_edge": payload.get("expected_edge"),
                    "signal_score": payload.get("signal_score"),
                    "adjusted_signal_score": payload.get("adjusted_signal_score"),
                    "decision": payload.get("decision"),
                }
            )
        elif event_type in {"POSITION_HOLD_TIME", "TRADE_DURATION"}:
            hold_time_samples.append(
                {
                    "ts": row.get("ts"),
                    "symbol": symbol,
                    "reason": payload.get("reason"),
                    "hold_seconds": payload.get("hold_seconds", payload.get("duration_seconds")),
                }
            )

        if len(recent_events) < 200:
            recent_events.append(
                {
                    "ts": row.get("ts"),
                    "event_type": event_type,
                    "symbol": symbol,
                }
            )
        else:
            recent_events.pop(0)
            recent_events.append(
                {
                    "ts": row.get("ts"),
                    "event_type": event_type,
                    "symbol": symbol,
                }
            )

    tuning_payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "events_log_path": str(EVENTS_LOG),
        "trade_outcomes_path": str(TRADE_OUTCOMES),
        "strategy_performance_path": str(STRATEGY_PERFORMANCE),
        "trade_outcomes_count": len(trade_outcomes) if isinstance(trade_outcomes, list) else 0,
        "strategy_performance_symbols": sorted(strategy_performance.keys()) if isinstance(strategy_performance, dict) else [],
        "realized_pnl_by_symbol": {k: round(v, 12) for k, v in sorted(realized_pnl_by_symbol.items())},
        "exit_reason_counts": dict(sorted(exit_reason_counts.items())),
        "symbol_event_counts": {k: dict(sorted(v.items())) for k, v in sorted(symbol_event_counts.items())},
        "entry_quality_samples": entry_quality_samples[-100:],
        "hold_time_samples": hold_time_samples[-100:],
        "recent_events": recent_events[-100:],
    }
    OUT_PATH.write_text(json.dumps(tuning_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out_path": str(OUT_PATH), "trade_outcomes_count": tuning_payload["trade_outcomes_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
