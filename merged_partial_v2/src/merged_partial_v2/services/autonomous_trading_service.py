"""Autonomous entry/exit cycle for merged_partial_v2."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from merged_partial_v2.services.autonomous_state_service import AutonomousStateService


class AutonomousTradingService:
    """Run operator-free autonomous trading cycles on top of the merged engine."""

    def __init__(
        self,
        *,
        engine: Any,
        merged_root: Path,
        autonomous_config: Dict[str, Any] | None = None,
    ) -> None:
        self.engine = engine
        self.merged_root = Path(merged_root)
        self.autonomous_config = dict(autonomous_config or {})
        self.state_service = AutonomousStateService(self.merged_root)
        self.report_dir = self.merged_root / "autonomous_reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def run_cycle(self, *, dry_run: bool, adopt_existing_positions: bool | None = None) -> Dict[str, Any]:
        cycle_ts = self._ts()
        scan_limit = int(self.autonomous_config.get("scan_limit", 80))
        max_new_orders = int(self.autonomous_config.get("max_new_orders_per_cycle", 1))
        close_unselected = bool(self.autonomous_config.get("close_when_unselected_after_min_hold", True))
        interval_seconds = float(self.autonomous_config.get("cycle_interval_seconds", 60.0))
        adopt_existing = (
            bool(adopt_existing_positions)
            if adopt_existing_positions is not None
            else bool(self.autonomous_config.get("adopt_existing_positions_on_start", False))
        )

        snapshot = self.engine.build_paper_decision(limit=scan_limit)
        account_positions = list(snapshot["account"]["positions"].get("active_positions", []))
        state_before = self.state_service.load()
        synced_state = self.state_service.sync_active_positions(
            state_before,
            account_positions,
            adopt_existing=adopt_existing,
        )

        exits = self._evaluate_exits(
            snapshot=snapshot,
            state=synced_state,
            dry_run=dry_run,
            close_unselected=close_unselected,
            interval_seconds=interval_seconds,
        )

        refreshed_positions = self.engine.private_read_client.get_positions()
        current_active = list(refreshed_positions.get("active_positions", account_positions))
        synced_state = self.state_service.sync_active_positions(
            synced_state,
            current_active,
            adopt_existing=False,
        )

        entries = self._evaluate_entries(
            snapshot=snapshot,
            state=synced_state,
            dry_run=dry_run,
            max_new_orders=max_new_orders,
        )

        final_positions = self.engine.private_read_client.get_positions()
        final_active = list(final_positions.get("active_positions", current_active))
        synced_state = self.state_service.sync_active_positions(
            synced_state,
            final_active,
            adopt_existing=False,
            preserve_recent_entries_seconds=max(interval_seconds * 2.0, 120.0),
        )
        if not dry_run and entries:
            final_active_map = {
                str(row.get("symbol", "")).upper(): row
                for row in final_active
                if str(row.get("symbol", "")).strip()
            }
            managed_symbols = set(self.state_service.summarize(synced_state).get("managed_symbols", []))
            for entry in entries:
                symbol = str(entry.get("symbol", "")).upper()
                result = entry.get("result")
                if not symbol or not isinstance(result, dict):
                    continue
                if symbol in managed_symbols:
                    continue
                synced_state = self.state_service.register_entry(
                    synced_state,
                    symbol=symbol,
                    order_result=result,
                    position_snapshot=final_active_map.get(symbol),
                    recommendation=entry.get("recommendation"),
                )

        if not dry_run:
            self.state_service.save(synced_state)

        report = {
            "mode": "autonomous_cycle",
            "ts": cycle_ts,
            "dry_run": dry_run,
            "profile_name": snapshot["market"]["profile"]["name"],
            "market_regime": snapshot["market"]["market_regime"],
            "risk_gate": snapshot["paper_decision"].get("risk_gate", {}),
            "paper_decision": snapshot["paper_decision"],
            "state_before": self.state_service.summarize(state_before),
            "state_after": self.state_service.summarize(synced_state),
            "entry_count": len(entries),
            "exit_count": len(exits),
            "entries": entries,
            "exits": exits,
            "selected_symbols": [item["symbol"] for item in snapshot["market"].get("selected_symbols", [])],
            "managed_symbols": self.state_service.summarize(synced_state).get("managed_symbols", []),
            "decision_line": (
                f"autonomous cycle | entries={len(entries)} | exits={len(exits)} | "
                f"managed={self.state_service.summarize(synced_state).get('managed_position_count', 0)}"
            ),
        }
        self._write_report(report)
        return report

    def last_report_path(self) -> Path:
        return self.report_dir / "last_autonomous_report.json"

    def _write_report(self, report: Dict[str, Any]) -> Path:
        path = self.last_report_path()
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def _evaluate_exits(
        self,
        *,
        snapshot: Dict[str, Any],
        state: Dict[str, Any],
        dry_run: bool,
        close_unselected: bool,
        interval_seconds: float,
    ) -> list[Dict[str, Any]]:
        exits = []
        managed = dict(state.get("managed_positions", {}))
        active_map = {
            str(row.get("symbol", "")).upper(): row
            for row in snapshot["account"]["positions"].get("active_positions", [])
            if str(row.get("symbol", "")).strip()
        }
        evaluated_map = {
            str(row.get("symbol", "")).upper(): row
            for row in snapshot["market"].get("evaluated_symbols", [])
            if str(row.get("symbol", "")).strip()
        }
        selected_symbols = {
            str(row.get("symbol", "")).upper()
            for row in snapshot["market"].get("selected_symbols", [])
            if str(row.get("symbol", "")).strip()
        }
        min_hold_bars = int(snapshot["market"]["profile"].get("minimum_hold_bars", 0))
        min_hold_seconds = min_hold_bars * interval_seconds
        take_profit = float(snapshot["market"]["profile"].get("take_profit", 0.0) or 0.0)
        replacement_threshold = float(snapshot["market"]["profile"].get("replacement_threshold", -1.0) or -1.0)

        for symbol, managed_row in managed.items():
            active = active_map.get(symbol)
            if not active:
                continue
            pnl_percent = self._calculate_position_pnl_percent(active)
            held_seconds = self._held_seconds(managed_row.get("opened_at"))
            exit_reason = None
            if pnl_percent >= take_profit:
                exit_reason = "take_profit_reached"
            elif pnl_percent <= replacement_threshold:
                exit_reason = "stop_loss_reached"
            elif close_unselected and held_seconds >= min_hold_seconds and symbol not in selected_symbols:
                exit_reason = "unselected_after_min_hold"

            if not exit_reason:
                continue

            quantity = abs(float(active.get("positionAmt", 0.0) or 0.0))
            if quantity <= 0:
                continue
            close_side = "SELL" if float(active.get("positionAmt", 0.0) or 0.0) > 0 else "BUY"
            payload = {
                "symbol": symbol,
                "side": close_side,
                "type": "MARKET",
                "qty": quantity,
                "reduceOnly": True,
                "trace_id": f"auto-close-{symbol.lower()}",
                "dry_run": dry_run,
                "wait_for_fill": not dry_run,
                "status_timeout_seconds": 8.0,
            }
            try:
                result = self.engine.submit_order(payload)
            except Exception as exc:
                exits.append(
                    {
                        "symbol": symbol,
                        "reason": f"{exit_reason}_submit_failed",
                        "pnl_percent": pnl_percent,
                        "held_seconds": held_seconds,
                        "submitted_side": close_side,
                        "quantity": quantity,
                        "error": str(exc),
                        "current_signal": evaluated_map.get(symbol, {}),
                    }
                )
                continue
            exit_record = {
                "symbol": symbol,
                "reason": exit_reason,
                "pnl_percent": pnl_percent,
                "held_seconds": held_seconds,
                "submitted_side": close_side,
                "quantity": quantity,
                "result": result,
                "current_signal": evaluated_map.get(symbol, {}),
            }
            exits.append(exit_record)
            if not dry_run:
                self.state_service.register_exit(
                    state,
                    symbol=symbol,
                    order_result=result,
                    exit_reason=exit_reason,
                )

        return exits

    def _evaluate_entries(
        self,
        *,
        snapshot: Dict[str, Any],
        state: Dict[str, Any],
        dry_run: bool,
        max_new_orders: int,
    ) -> list[Dict[str, Any]]:
        entries = []
        recommendations = list(snapshot["paper_decision"].get("recommendations", []))
        managed = dict(state.get("managed_positions", {}))
        for recommendation in recommendations[:max_new_orders]:
            symbol = str(recommendation.get("symbol", "")).upper()
            if not symbol or symbol in managed:
                continue
            payload = {
                "symbol": symbol,
                "side": recommendation.get("side", "BUY"),
                "type": "MARKET",
                "qty": recommendation.get("estimated_quantity", 0.0),
                "trace_id": f"auto-open-{symbol.lower()}",
                "dry_run": dry_run,
                "wait_for_fill": not dry_run,
                "status_timeout_seconds": 8.0,
            }
            try:
                result = self.engine.submit_order(payload)
            except Exception as exc:
                entries.append(
                    {
                        "symbol": symbol,
                        "allocation": recommendation.get("allocation"),
                        "estimated_quantity": recommendation.get("estimated_quantity"),
                        "recommendation": recommendation,
                        "error": str(exc),
                    }
                )
                continue
            entry_record = {
                "symbol": symbol,
                "allocation": recommendation.get("allocation"),
                "estimated_quantity": recommendation.get("estimated_quantity"),
                "result": result,
                "recommendation": recommendation,
            }
            entries.append(entry_record)
            if not dry_run:
                positions = self.engine.private_read_client.get_positions()
                active_map = {
                    str(row.get("symbol", "")).upper(): row
                    for row in positions.get("active_positions", [])
                    if str(row.get("symbol", "")).strip()
                }
                self.state_service.register_entry(
                    state,
                    symbol=symbol,
                    order_result=result,
                    position_snapshot=active_map.get(symbol),
                    recommendation=recommendation,
                )
        return entries

    def _calculate_position_pnl_percent(self, position: Dict[str, Any]) -> float:
        position_amt = float(position.get("positionAmt", 0.0) or 0.0)
        entry_price = float(position.get("entryPrice", 0.0) or 0.0)
        mark_price = float(position.get("markPrice", 0.0) or 0.0)
        if position_amt == 0 or entry_price <= 0:
            return 0.0
        if position_amt > 0:
            return ((mark_price - entry_price) / entry_price) * 100.0
        return ((entry_price - mark_price) / entry_price) * 100.0

    def _held_seconds(self, opened_at: str | None) -> float:
        if not opened_at:
            return 0.0
        try:
            opened = datetime.fromisoformat(opened_at)
        except Exception:
            return 0.0
        return max((datetime.now(timezone.utc) - opened).total_seconds(), 0.0)

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()
