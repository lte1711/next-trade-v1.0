"""
Selection logic extracted from the modular test strategy.
"""

from typing import Any, Dict, List


class SymbolSelectionService:
    """Classify the market regime and select entry candidates."""

    def __init__(self):
        self.market_regime_thresholds = {
            "EXTREME": 70.0,
            "HIGH_VOLATILITY": 75.0,
            "NORMAL": 80.0,
        }

    def analyze_market_regime(self, top_symbols: List[Dict[str, Any]]) -> str:
        """Classify the market from average absolute 24h moves."""
        if not top_symbols:
            return "NORMAL"
        volatility = sum(abs(item.get("change_percent", 0.0)) for item in top_symbols) / len(top_symbols)
        if volatility > 5.0:
            return "EXTREME"
        if volatility > 2.5:
            return "HIGH_VOLATILITY"
        return "NORMAL"

    def filter_profitable_symbols(
        self,
        evaluated_symbols: List[Dict[str, Any]],
        market_regime: str,
    ) -> List[Dict[str, Any]]:
        """Keep symbols whose bullish score and profit potential clear the regime threshold."""
        threshold = self.market_regime_thresholds.get(market_regime, 80.0)
        profitable = [
            item
            for item in evaluated_symbols
            if item.get("bullish_score", 0.0) >= threshold and item.get("profit_potential", 0.0) >= threshold
        ]
        profitable.sort(key=lambda item: item["profit_potential"], reverse=True)
        return profitable

    def select_symbols(self, profitable_symbols: List[Dict[str, Any]], market_regime: str, symbol_count: int) -> List[Dict[str, Any]]:
        """Apply regime-aware symbol-count limits."""
        if market_regime == "EXTREME":
            max_symbols = min(symbol_count, 5)
        elif market_regime == "HIGH_VOLATILITY":
            max_symbols = min(symbol_count, 7)
        else:
            max_symbols = symbol_count
        return profitable_symbols[:max_symbols]
