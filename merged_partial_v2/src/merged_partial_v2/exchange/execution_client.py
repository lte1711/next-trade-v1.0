"""Execution client backed by the merged workspace bridge."""

from typing import Any, Dict

from merged_partial_v2.exchange.local_binance_bridge import submit_order


class ExecutionClient:
    """Submit orders without importing the original project."""

    def submit_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an order payload through the local merged bridge."""
        return submit_order(payload)
