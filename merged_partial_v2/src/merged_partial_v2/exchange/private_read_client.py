"""Private account-read client backed by the merged workspace bridge."""

from typing import Any, Dict

from merged_partial_v2.exchange.local_binance_bridge import get_account_snapshot, get_positions_snapshot


class PrivateReadClient:
    """Load private account context without depending on the original package."""

    def get_account(self) -> Dict[str, Any]:
        """Return the current account snapshot."""
        return get_account_snapshot()

    def get_positions(self) -> Dict[str, Any]:
        """Return current position information."""
        return get_positions_snapshot()

    def get_active_positions(self) -> Dict[str, Any]:
        """Return only non-zero positions for simpler operational checks."""
        snapshot = get_positions_snapshot()
        return {
            "ok": snapshot.get("ok"),
            "ts": snapshot.get("ts"),
            "source": snapshot.get("source"),
            "active_positions": snapshot.get("active_positions", []),
            "active_position_count": snapshot.get("active_position_count", 0),
            "error": snapshot.get("error"),
        }
