"""Execution client backed by the merged workspace bridge."""

import time
from typing import Any, Dict, List

from merged_partial_v2.exchange.local_binance_bridge import get_positions_snapshot, submit_order


class ExecutionClient:
    """Submit orders without importing the original project."""

    def submit_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an order payload through the local merged bridge."""
        return submit_order(payload)

    def close_all_active_positions(
        self,
        *,
        dry_run: bool,
        status_timeout_seconds: float = 8.0,
    ) -> Dict[str, Any]:
        """Close all active positions with reduceOnly market orders."""
        snapshot = get_positions_snapshot()
        active_positions: List[Dict[str, Any]] = list(snapshot.get("active_positions", []))
        results: List[Dict[str, Any]] = []
        for row in active_positions:
            symbol = str(row.get("symbol", "")).upper()
            try:
                position_amt = float(row.get("positionAmt", 0.0) or 0.0)
            except (TypeError, ValueError):
                position_amt = 0.0
            if not symbol or position_amt == 0.0:
                continue
            side = "SELL" if position_amt > 0 else "BUY"
            quantity = abs(position_amt)
            payload = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "qty": quantity,
                "reduceOnly": True,
                "trace_id": f"dashboard-close-{symbol.lower()}",
                "dry_run": dry_run,
                "wait_for_fill": not dry_run,
                "status_timeout_seconds": status_timeout_seconds,
            }
            try:
                result = self.submit_order(payload)
                results.append(
                    {
                        "symbol": symbol,
                        "requested_quantity": quantity,
                        "side": side,
                        "ok": True,
                        "result": result,
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "symbol": symbol,
                        "requested_quantity": quantity,
                        "side": side,
                        "ok": False,
                        "error": str(exc),
                    }
                )
        return {
            "ok": True,
            "dry_run": dry_run,
            "active_position_count": len(active_positions),
            "close_attempt_count": len(results),
            "results": results,
        }

    def open_and_close_test_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        hold_seconds: float = 1.0,
        status_timeout_seconds: float = 8.0,
    ) -> Dict[str, Any]:
        """Submit a small test order, wait briefly, then close it with reduceOnly."""
        side = side.upper().strip()
        close_side = "SELL" if side == "BUY" else "BUY"

        open_result = self.submit_order(
            {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "qty": quantity,
                "trace_id": f"health-open-{symbol.lower()}",
                "wait_for_fill": True,
                "status_timeout_seconds": status_timeout_seconds,
            }
        )
        time.sleep(hold_seconds)
        mid_positions = get_positions_snapshot()
        close_result = self.submit_order(
            {
                "symbol": symbol,
                "side": close_side,
                "type": "MARKET",
                "qty": open_result["quantity"],
                "reduceOnly": True,
                "trace_id": f"health-close-{symbol.lower()}",
                "wait_for_fill": True,
                "status_timeout_seconds": status_timeout_seconds,
            }
        )
        time.sleep(hold_seconds)
        after_positions = get_positions_snapshot()

        return {
            "symbol": symbol,
            "requested_quantity": quantity,
            "submitted_quantity": open_result.get("quantity"),
            "open_result": open_result,
            "mid_positions": [row for row in mid_positions.get("active_positions", []) if row.get("symbol") == symbol],
            "close_result": close_result,
            "after_positions": [row for row in after_positions.get("active_positions", []) if row.get("symbol") == symbol],
        }
