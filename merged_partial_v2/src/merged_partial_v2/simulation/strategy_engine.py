"""
A lightweight merged orchestration layer that combines original clients and extracted strategy services.
"""

from typing import Any, Dict, List

from merged_partial_v2.exchange.execution_client import ExecutionClient
from merged_partial_v2.exchange.private_read_client import PrivateReadClient
from merged_partial_v2.exchange.public_read_client import PublicReadClient
from merged_partial_v2.services.market_scoring_service import MarketScoringService
from merged_partial_v2.services.symbol_selection_service import SymbolSelectionService


class MergedPartialStrategyEngine:
    """Combine original account/order access with extracted test-strategy scoring."""

    def __init__(self, exchange_base_url: str = "https://demo-fapi.binance.com", symbol_count: int = 10):
        self.public_read_client = PublicReadClient(exchange_base_url=exchange_base_url)
        self.private_read_client = PrivateReadClient()
        self.execution_client = ExecutionClient()
        self.market_scoring_service = MarketScoringService(self.public_read_client)
        self.symbol_selection_service = SymbolSelectionService()
        self.symbol_count = symbol_count

    def build_market_snapshot(self, limit: int = 80) -> Dict[str, Any]:
        """Build a merged market snapshot without changing original code paths."""
        top_symbols = self.public_read_client.get_top_quote_volume_symbols(limit=limit)
        market_regime = self.symbol_selection_service.analyze_market_regime(top_symbols[:20])
        evaluated_symbols = self.market_scoring_service.evaluate_symbols(top_symbols)
        profitable_symbols = self.symbol_selection_service.filter_profitable_symbols(evaluated_symbols, market_regime)
        selected_symbols = self.symbol_selection_service.select_symbols(
            profitable_symbols,
            market_regime,
            self.symbol_count,
        )
        return {
            "market_regime": market_regime,
            "top_symbols": top_symbols,
            "evaluated_symbols": evaluated_symbols,
            "profitable_symbols": profitable_symbols,
            "selected_symbols": selected_symbols,
        }

    def get_account_context(self) -> Dict[str, Any]:
        """Load private account and position context from the original project."""
        return {
            "account": self.private_read_client.get_account(),
            "positions": self.private_read_client.get_positions(),
        }

    def build_combined_snapshot(self, limit: int = 80) -> Dict[str, Any]:
        """Return both market-selection output and original account context."""
        market = self.build_market_snapshot(limit=limit)
        account = self.get_account_context()
        return {"market": market, "account": account}

    def submit_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an order through the original project's order bridge."""
        return self.execution_client.submit_order(payload)
