"""
A lightweight merged orchestration layer that combines original clients and extracted strategy services.
"""

from typing import Any, Dict, List

from merged_partial_v2.exchange.execution_client import ExecutionClient
from merged_partial_v2.exchange.local_binance_bridge import (
    get_recent_health_check_summary,
    get_recent_order_failure_summary,
)
from merged_partial_v2.exchange.private_read_client import PrivateReadClient
from merged_partial_v2.exchange.public_read_client import PublicReadClient
from merged_partial_v2.services.market_scoring_service import MarketScoringService
from merged_partial_v2.services.paper_decision_service import PaperDecisionService
from merged_partial_v2.services.profile_switcher_service import ProfileSwitcherService
from merged_partial_v2.services.risk_gate_service import RiskGateService
from merged_partial_v2.services.symbol_selection_service import SymbolSelectionService


class MergedPartialStrategyEngine:
    """Combine original account/order access with extracted test-strategy scoring."""

    def __init__(
        self,
        exchange_base_url: str = "https://demo-fapi.binance.com",
        symbol_count: int = 10,
        profile_name: str | None = None,
        selection_config: Dict[str, Any] | None = None,
        benchmark_metrics: Dict[str, Dict[str, Any]] | None = None,
    ):
        self.public_read_client = PublicReadClient(exchange_base_url=exchange_base_url)
        self.private_read_client = PrivateReadClient()
        self.execution_client = ExecutionClient()
        self.profile_switcher_service = ProfileSwitcherService(
            selection_config=selection_config,
            benchmark_metrics=benchmark_metrics,
        )
        self.profile = self.profile_switcher_service.get_profile(profile_name)
        self.market_scoring_service = MarketScoringService(self.public_read_client)
        self.symbol_selection_service = SymbolSelectionService(self.profile)
        self.paper_decision_service = PaperDecisionService(self.profile)
        self.risk_gate_service = RiskGateService()
        self.symbol_count = symbol_count

    def select_profile_from_metrics(
        self,
        *,
        max_drawdown_percent: float | None = None,
        positive_months: int | None = None,
        negative_months: int | None = None,
        prefer_aggressive: bool = False,
    ) -> Dict[str, Any]:
        self.profile = self.profile_switcher_service.choose_profile_from_metrics(
            max_drawdown_percent=max_drawdown_percent,
            positive_months=positive_months,
            negative_months=negative_months,
            prefer_aggressive=prefer_aggressive,
        )
        self.symbol_selection_service = SymbolSelectionService(self.profile)
        self.paper_decision_service = PaperDecisionService(self.profile)
        self.risk_gate_service = RiskGateService()
        return self.profile_switcher_service.build_selection_summary(
            selected_profile=self.profile,
            max_drawdown_percent=max_drawdown_percent,
            positive_months=positive_months,
            negative_months=negative_months,
        )

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
            "profile": self.profile,
            "profile_benchmark": self.profile_switcher_service.get_benchmark_metrics(self.profile["name"]),
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

    def build_paper_decision(self, limit: int = 80) -> Dict[str, Any]:
        """Return recommendation-only trade decisions without submitting orders."""
        combined = self.build_combined_snapshot(limit=limit)
        risk_gate = self.risk_gate_service.evaluate(
            market_snapshot=combined["market"],
            account_context=combined["account"],
            recent_health_check=get_recent_health_check_summary(),
            recent_order_failures=get_recent_order_failure_summary(),
        )
        decision = self.paper_decision_service.build_decision(
            combined["market"],
            combined["account"],
            risk_gate,
        )
        return {**combined, "paper_decision": decision}

    def submit_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an order through the original project's order bridge."""
        return self.execution_client.submit_order(payload)

    def close_all_active_positions(self, *, dry_run: bool) -> Dict[str, Any]:
        """Close all current active positions through the execution bridge."""
        return self.execution_client.close_all_active_positions(dry_run=dry_run)
