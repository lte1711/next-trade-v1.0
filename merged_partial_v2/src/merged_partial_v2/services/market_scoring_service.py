"""
Extracted market-scoring logic for the merged partial integration workspace.
"""

import statistics
from typing import Any, Dict, List

from merged_partial_v2.exchange.public_read_client import PublicReadClient


class MarketScoringService:
    """Calculate symbol indicators and weighted scores from one-hour market data."""

    def __init__(self, public_read_client: PublicReadClient):
        self.public_read_client = public_read_client

    def evaluate_symbols(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate a universe of symbols and rank them by bullish score."""
        evaluated: List[Dict[str, Any]] = []
        for symbol_data in symbols:
            symbol = symbol_data["symbol"]
            klines = self.public_read_client.get_klines(symbol, interval="1h", limit=100)
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            indicators = self._calculate_indicators(closes, volumes)
            bullish_score = self._calculate_bullish_score(symbol_data, indicators)
            profit_potential = self._calculate_profit_potential(
                symbol_data=symbol_data,
                indicators=indicators,
                bullish_score=bullish_score,
            )

            evaluated.append(
                {
                    **symbol_data,
                    **indicators,
                    "bullish_score": bullish_score,
                    "profit_potential": profit_potential,
                }
            )

        evaluated.sort(key=lambda item: item["bullish_score"], reverse=True)
        for index, item in enumerate(evaluated, start=1):
            item["bullish_rank"] = index
        return evaluated

    def _calculate_indicators(self, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """Build the indicator set used by the extracted scoring strategy."""
        rsi = self._calculate_rsi(closes, 14)
        macd_signal = self._calculate_macd_signal(closes)
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
        bb_upper, bb_lower = self._calculate_bollinger_bands(closes, 20)

        if len(closes) >= 2:
            returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
            volatility = statistics.stdev(returns) * 100 if returns else 0.0
        else:
            volatility = 0.0

        if len(volumes) >= 10:
            recent_volume = sum(volumes[-5:]) / 5
            previous_volume = sum(volumes[-10:-5]) / 5
            volume_momentum = ((recent_volume - previous_volume) / previous_volume) * 100 if previous_volume > 0 else 0.0
        else:
            volume_momentum = 0.0

        return {
            "rsi": rsi,
            "macd_signal": macd_signal,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "volatility": volatility,
            "volume_momentum": volume_momentum,
        }

    def _calculate_bullish_score(self, symbol_data: Dict[str, Any], indicators: Dict[str, Any]) -> float:
        """Reused weighted bullish score from the test strategy."""
        score = 0.0

        change_percent = symbol_data["change_percent"]
        score += min(change_percent * 2.5, 25.0) if change_percent > 0 else max(change_percent * 2.5, -10.0)

        rsi = indicators["rsi"]
        if 30 <= rsi <= 70:
            score += 20.0
        elif 20 <= rsi < 30:
            score += 25.0
        elif 70 < rsi <= 80:
            score += 10.0

        macd_signal = indicators["macd_signal"]
        score += 15.0 if macd_signal == "BULLISH" else -5.0 if macd_signal == "BEARISH" else 5.0

        score += 15.0 if symbol_data["price"] > indicators["sma_20"] else -5.0

        if indicators["bb_upper"] != indicators["bb_lower"]:
            bb_position = (symbol_data["price"] - indicators["bb_lower"]) / (indicators["bb_upper"] - indicators["bb_lower"])
            bb_position = min(max(bb_position, 0.0), 1.0)
            score += bb_position * 10.0
        else:
            score += 5.0

        volatility = indicators["volatility"]
        if volatility < 0.5:
            score += 1.0
        elif volatility <= 2.5:
            score += 6.0
        elif volatility <= 5.0:
            score += 10.0
        elif volatility <= 8.0:
            score += 5.0

        score += min(max(indicators["volume_momentum"] / 10.0, -5.0), 5.0)
        return min(max(score, 0.0), 100.0)

    def _calculate_profit_potential(
        self,
        *,
        symbol_data: Dict[str, Any],
        indicators: Dict[str, Any],
        bullish_score: float,
    ) -> float:
        """Reused profit-potential logic extracted from the test strategy."""
        potential = bullish_score * 0.4

        change_percent = symbol_data.get("change_percent", 0.0)
        potential += min(change_percent * 3.0, 25.0) if change_percent > 0 else max(change_percent * 1.5, -10.0)

        quote_volume = symbol_data.get("quote_volume", symbol_data.get("quoteVolume", 0.0))
        potential += min(quote_volume / 50_000_000, 15.0)

        rsi = indicators["rsi"]
        if 40 <= rsi <= 60:
            potential += 10.0
        elif 30 <= rsi < 40:
            potential += 15.0
        elif 60 < rsi <= 70:
            potential += 8.0

        if indicators["macd_signal"] == "BULLISH":
            potential += 5.0

        return min(max(potential, 0.0), 100.0)

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate a simplified RSI."""
        if len(closes) < period + 1:
            return 50.0
        gains: List[float] = []
        losses: List[float] = []
        for index in range(1, len(closes)):
            delta = closes[index] - closes[index - 1]
            if delta > 0:
                gains.append(delta)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(delta))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _calculate_macd_signal(self, closes: List[float]) -> str:
        """Calculate a simplified EMA-style MACD direction."""
        if len(closes) < 26:
            return "NEUTRAL"
        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)
        if ema_12 > ema_26:
            return "BULLISH"
        if ema_12 < ema_26:
            return "BEARISH"
        return "NEUTRAL"

    def _calculate_ema(self, closes: List[float], period: int) -> float:
        """Calculate a lightweight EMA."""
        multiplier = 2 / (period + 1)
        ema = sum(closes[:period]) / period
        for price in closes[period:]:
            ema = ((price - ema) * multiplier) + ema
        return ema

    def _calculate_bollinger_bands(self, closes: List[float], period: int = 20) -> tuple[float, float]:
        """Calculate a simple Bollinger band pair."""
        if len(closes) < period:
            latest = closes[-1]
            return latest * 1.02, latest * 0.98
        sma = sum(closes[-period:]) / period
        variance = sum((value - sma) ** 2 for value in closes[-period:]) / period
        std = variance**0.5
        return sma + (std * 2.0), sma - (std * 2.0)
