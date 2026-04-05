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
