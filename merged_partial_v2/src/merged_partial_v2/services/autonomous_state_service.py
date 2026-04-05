"""Persistent state helpers for autonomous trading inside merged_partial_v2."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class AutonomousStateService:
    """Load and store managed autonomous position state."""

    def __init__(self, merged_root: Path) -> None:
        self.merged_root = Path(merged_root)
        self.runtime_dir = self.merged_root / "runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_dir / "autonomous_state.json"

    def load(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return self._default_state()
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return self._default_state()

    def save(self, state: Dict[str, Any]) -> Path:
        normalized = self._normalize_state(state)
        self.state_path.write_text(
            json.dumps(normalized, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return self.state_path

    def sync_active_positions(
        self,
        state: Dict[str, Any],
        active_positions: list[Dict[str, Any]],
        *,
        adopt_existing: bool,
        preserve_recent_entries_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        normalized = self._normalize_state(state)
        active_map = {
            str(row.get("symbol", "")).upper(): row
            for row in active_positions
            if str(row.get("symbol", "")).strip()
        }
        managed = dict(normalized.get("managed_positions", {}))

        for symbol in list(managed.keys()):
            active = active_map.get(symbol)
            if not active:
                if preserve_recent_entries_seconds > 0 and self._should_preserve_missing_recent_entry(
                    managed.get(symbol, {}),
                    preserve_recent_entries_seconds,
                ):
                    managed[symbol]["last_seen_at"] = self._ts()
                    managed[symbol]["pending_exchange_sync"] = True
                    continue
                self._append_event(
                    normalized,
                    {
                        "ts": self._ts(),
                        "event": "position_removed_from_exchange",
                        "symbol": symbol,
                    },
                )
                managed.pop(symbol, None)
                continue
            managed[symbol].update(self._snapshot_from_position(active))
            managed[symbol]["last_seen_at"] = self._ts()

        if adopt_existing:
            for symbol, active in active_map.items():
                if symbol in managed:
                    continue
                managed[symbol] = {
                    **self._snapshot_from_position(active),
                    "symbol": symbol,
                    "managed": True,
                    "adopted": True,
                    "opened_at": self._ts(),
                    "last_seen_at": self._ts(),
                    "source": "adopted_active_position",
                }
                self._append_event(
                    normalized,
                    {
                        "ts": self._ts(),
                        "event": "adopted_existing_position",
                        "symbol": symbol,
                    },
                )

        normalized["managed_positions"] = managed
        normalized["last_synced_at"] = self._ts()
        return normalized

    def register_entry(
        self,
        state: Dict[str, Any],
        *,
        symbol: str,
        order_result: Dict[str, Any],
        position_snapshot: Dict[str, Any] | None,
        recommendation: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        normalized = self._normalize_state(state)
        managed = dict(normalized.get("managed_positions", {}))
        symbol = str(symbol).upper()
        existing = dict(managed.get(symbol, {}))
        position_data = self._snapshot_from_position(position_snapshot or {})
        managed[symbol] = {
            **existing,
            "symbol": symbol,
            "managed": True,
            "adopted": bool(existing.get("adopted", False)),
            "opened_at": existing.get("opened_at") or self._ts(),
            "last_seen_at": self._ts(),
            "source": existing.get("source") or "autonomous_entry",
            "order_trace_id": order_result.get("trace_id"),
            "order_final_status": order_result.get("final_status") or order_result.get("status"),
            "allocation": (recommendation or {}).get("allocation"),
            "profile_name": (recommendation or {}).get("profile_name"),
            "market_regime": (recommendation or {}).get("market_regime"),
            "entry_action": (recommendation or {}).get("action", "new_entry"),
            "pending_exchange_sync": position_snapshot is None,
            "dry_run_simulated": bool(order_result.get("dry_run")) and position_snapshot is not None,
            "avg_fill_price": ((order_result.get("status_check") or {}).get("avg_price") or order_result.get("avg_price")),
            "executed_qty": ((order_result.get("status_check") or {}).get("executed_qty") or order_result.get("quantity")),
            **position_data,
        }
        normalized["managed_positions"] = managed
        self._append_event(
            normalized,
            {
                "ts": self._ts(),
                "event": "autonomous_entry" if not existing else "autonomous_scale_in",
                "symbol": symbol,
                "trace_id": order_result.get("trace_id"),
                "status": order_result.get("final_status") or order_result.get("status"),
            },
        )
        return normalized

    def register_exit(
        self,
        state: Dict[str, Any],
        *,
        symbol: str,
        order_result: Dict[str, Any],
        exit_reason: str,
    ) -> Dict[str, Any]:
        normalized = self._normalize_state(state)
        managed = dict(normalized.get("managed_positions", {}))
        symbol = str(symbol).upper()
        managed.pop(symbol, None)
        normalized["managed_positions"] = managed
        self._append_event(
            normalized,
            {
                "ts": self._ts(),
                "event": "autonomous_exit",
                "symbol": symbol,
                "exit_reason": exit_reason,
                "trace_id": order_result.get("trace_id"),
                "status": order_result.get("final_status") or order_result.get("status"),
            },
        )
        return normalized

    def summarize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_state(state)
        managed = dict(normalized.get("managed_positions", {}))
        return {
            "managed_position_count": len(managed),
            "managed_symbols": sorted(managed.keys()),
            "last_synced_at": normalized.get("last_synced_at"),
            "event_count": len(normalized.get("event_history", [])),
        }

    def _append_event(self, state: Dict[str, Any], event: Dict[str, Any], max_events: int = 200) -> None:
        history = list(state.get("event_history", []))
        history.append(event)
        state["event_history"] = history[-max_events:]

    def _normalize_state(self, state: Dict[str, Any] | None) -> Dict[str, Any]:
        base = self._default_state()
        if not state:
            return base
        base.update({k: v for k, v in dict(state).items() if k != "managed_positions"})
        base["managed_positions"] = dict(state.get("managed_positions", {}))
        base["event_history"] = list(state.get("event_history", []))
        return base

    def _default_state(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "managed_positions": {},
            "event_history": [],
            "last_synced_at": None,
        }

    def _snapshot_from_position(self, position: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "position_amt": position.get("positionAmt"),
            "entry_price": position.get("entryPrice"),
            "mark_price": position.get("markPrice"),
            "unrealized_profit": position.get("unRealizedProfit"),
            "position_side": position.get("positionSide"),
            "leverage": position.get("leverage"),
            "margin_type": position.get("marginType"),
        }

    def _should_preserve_missing_recent_entry(
        self,
        managed_row: Dict[str, Any],
        preserve_recent_entries_seconds: float,
    ) -> bool:
        if bool(managed_row.get("dry_run_simulated")):
            return True
        if str(managed_row.get("source", "")) != "autonomous_entry":
            return False
        opened_at = managed_row.get("opened_at")
        if not opened_at:
            return False
        try:
            opened_dt = datetime.fromisoformat(str(opened_at))
        except Exception:
            return False
        now = datetime.now(timezone.utc)
        return (now - opened_dt).total_seconds() <= preserve_recent_entries_seconds

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()
