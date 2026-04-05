"""
Selection logic extracted from the modular test strategy.
"""

from typing import Any, Dict, List


class SymbolSelectionService:
    """Classify the market regime and select entry candidates."""

    def __init__(self, profile: Dict[str, Any] | None = None):
        self.profile = profile or {
            "entry_thresholds": {
                "EXTREME": 80.0,
                "HIGH_VOLATILITY": 76.0,
                "NORMAL": 72.0,
            },
            "regime_volatility_thresholds": {
                "EXTREME": 18.0,
                "HIGH_VOLATILITY": 9.0,
            },
            "max_symbols_by_regime": {
                "EXTREME": 5,
                "HIGH_VOLATILITY": 5,
                "NORMAL": 5,
            },
            "profit_potential_offset": 16.0,
        }

    def analyze_market_regime(self, top_symbols: List[Dict[str, Any]]) -> str:
        """Classify the market from average absolute 24h moves."""
        if not top_symbols:
            return "NORMAL"
        volatility = sum(abs(item.get("change_percent", 0.0)) for item in top_symbols) / len(top_symbols)
        thresholds = self.profile.get("regime_volatility_thresholds", {})
        extreme_threshold = thresholds.get("EXTREME", 18.0)
        high_threshold = thresholds.get("HIGH_VOLATILITY", 9.0)
        if volatility > extreme_threshold:
            return "EXTREME"
        if volatility > high_threshold:
            return "HIGH_VOLATILITY"
        return "NORMAL"

    def filter_profitable_symbols(
        self,
        evaluated_symbols: List[Dict[str, Any]],
        market_regime: str,
    ) -> List[Dict[str, Any]]:
        """Keep symbols whose rise-rate clears the configured live-entry floor."""
        threshold = float(self.profile.get("entry_thresholds", {}).get(market_regime, 72.0) or 72.0)
        rise_rate_floor = float(self.profile.get("live_rise_rate_floor", 80.0) or 80.0)
        profitable = [
            item
            for item in evaluated_symbols
            if item.get("bullish_score", 0.0) >= threshold and item.get("profit_potential", 0.0) >= rise_rate_floor
        ]
        profitable.sort(
            key=lambda item: (
                float(item.get("quote_volume", item.get("quoteVolume", 0.0)) or 0.0),
                float(item.get("profit_potential", 0.0) or 0.0),
                float(item.get("bullish_score", 0.0) or 0.0),
            ),
            reverse=True,
        )
        return profitable

    def select_symbols(self, profitable_symbols: List[Dict[str, Any]], market_regime: str, symbol_count: int) -> List[Dict[str, Any]]:
        """Select the highest-volume candidates from the scanned universe."""
        ranked = sorted(
            profitable_symbols,
            key=lambda item: (
                float(item.get("quote_volume", item.get("quoteVolume", 0.0)) or 0.0),
                float(item.get("volume", 0.0) or 0.0),
                float(item.get("bullish_score", 0.0) or 0.0),
            ),
            reverse=True,
        )
        return ranked[: max(int(symbol_count or 0), 0)]
