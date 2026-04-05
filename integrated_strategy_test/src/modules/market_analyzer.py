"""
Market analysis helpers for the modular trading simulator.
"""

from typing import Any, Dict, List

import requests
import statistics


class MarketAnalyzer:
    """Fetch market data and score symbols with lightweight technical signals."""

    def __init__(self, exchange_base_url: str = "https://demo-fapi.binance.com"):
        self.exchange_base_url = exchange_base_url
        self.supported_symbols = set()

    def get_top_volume_symbols(self, limit: int = 80) -> List[Dict[str, Any]]:
        """Return the most liquid USDT symbols ranked by quote volume."""
        print(f"FACT: top-volume symbol lookup started (limit={limit})")

        try:
            response = requests.get(f"{self.exchange_base_url}/fapi/v1/ticker/24hr", timeout=10)
            if response.status_code != 200:
                print(f"  API response error: {response.status_code}")
                return []

            filtered_data: List[Dict[str, Any]] = []
            for item in response.json():
                try:
                    symbol = item["symbol"]
                    volume = float(item["volume"])
                    quote_volume = float(item["quoteVolume"])
                    price = float(item["lastPrice"])
                    change_percent = float(item["priceChangePercent"])
                except (ValueError, KeyError) as exc:
                    print(f"  skipped malformed ticker row for {item.get('symbol', 'UNKNOWN')}: {exc}")
                    continue

                if symbol.endswith("USDT") and volume > 0 and quote_volume > 0:
                    filtered_data.append(
                        {
                            "symbol": symbol,
                            "volume": volume,
                            "quote_volume": quote_volume,
                            "quoteVolume": quote_volume,
                            "price": price,
                            "change_percent": change_percent,
                        }
                    )

            filtered_data.sort(key=lambda item: item["quote_volume"], reverse=True)
            top_symbols = filtered_data[:limit]

            print(f"  top-volume symbols fetched: {len(top_symbols)}")
            for index, symbol in enumerate(top_symbols[:5], start=1):
                print(f"    {index}. {symbol['symbol']}: quote volume={symbol['quote_volume']:,.0f}")

            return top_symbols

        except Exception as exc:
            print(f"  top-volume lookup failed: {exc}")
            return []

    def evaluate_bullish_potential_advanced(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate symbols with technical indicators and a weighted score."""
        print(f"FACT: bullish potential evaluation started ({len(symbols)} symbols)")

        evaluated_symbols: List[Dict[str, Any]] = []
        failed_count = 0

        for symbol_data in symbols:
            try:
                symbol = symbol_data["symbol"]
                indicators = self._calculate_indicators_from_symbol(symbol)
                bullish_score_result = self._calculate_bullish_score(symbol_data, indicators)

                evaluated_symbols.append(
                    {
                        "symbol": symbol,
                        "price": symbol_data["price"],
                        "volume": symbol_data["volume"],
                        "quote_volume": symbol_data.get("quote_volume", symbol_data.get("quoteVolume", 0.0)),
                        "quoteVolume": symbol_data.get("quote_volume", symbol_data.get("quoteVolume", 0.0)),
                        "change_percent": symbol_data["change_percent"],
                        **indicators,
                        **bullish_score_result,
                    }
                )
            except Exception as exc:
                failed_count += 1
                print(f"  {symbol_data.get('symbol', 'UNKNOWN')} evaluation failed: {exc}")

        evaluated_symbols.sort(key=lambda item: item["bullish_score"], reverse=True)
        for index, symbol in enumerate(evaluated_symbols, start=1):
            symbol["bullish_rank"] = index

        print(f"  bullish evaluation complete: {len(evaluated_symbols)} succeeded, {failed_count} failed")
        return evaluated_symbols

    def _calculate_indicators_from_symbol(self, symbol: str) -> Dict[str, Any]:
        """Fetch one-hour klines and derive indicators."""
        try:
            klines_response = requests.get(
                f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=100",
                timeout=10,
            )
            if klines_response.status_code != 200:
                print(f"  {symbol} klines lookup failed")
                return self._get_default_indicators()

            klines = klines_response.json()
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            return self._calculate_indicators(closes, volumes, highs, lows)

        except Exception as exc:
            print(f"  {symbol} indicator calculation failed: {exc}")
            return self._get_default_indicators()

    def _calculate_indicators(
        self, closes: List[float], volumes: List[float], highs: List[float], lows: List[float]
    ) -> Dict[str, Any]:
        """Derive the lightweight technical indicators used by the simulator."""
        indicators: Dict[str, Any] = {}
        indicators["rsi"] = self._calculate_rsi(closes, 14)
        indicators["macd_signal"] = self._calculate_macd_signal(closes)
        indicators["sma_20"] = sum(closes[-20:]) / 20
        indicators["sma_50"] = sum(closes[-50:]) / 50 if len(closes) >= 50 else indicators["sma_20"]

        bb_upper, bb_lower = self._calculate_bollinger_bands(closes, 20)
        indicators["bb_upper"] = bb_upper
        indicators["bb_lower"] = bb_lower

        if len(closes) >= 2:
            returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
            indicators["volatility"] = statistics.stdev(returns) * 100 if returns else 0.0
        else:
            indicators["volatility"] = 0.0

        if len(volumes) >= 10:
            recent_volume = sum(volumes[-5:]) / 5
            previous_volume = sum(volumes[-10:-5]) / 5
            indicators["volume_momentum"] = (
                ((recent_volume - previous_volume) / previous_volume) * 100 if previous_volume > 0 else 0.0
            )
        else:
            indicators["volume_momentum"] = 0.0

        return indicators

    def _get_default_indicators(self) -> Dict[str, Any]:
        """Return neutral indicator values when market data is unavailable."""
        return {
            "rsi": 50.0,
            "macd_signal": "NEUTRAL",
            "sma_20": 0.0,
            "sma_50": 0.0,
            "bb_upper": 0.0,
            "bb_lower": 0.0,
            "volatility": 0.0,
            "volume_momentum": 0.0,
        }

    def _calculate_bullish_score(self, symbol_data: Dict[str, Any], indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the weighted bullish score used for ranking."""
        score = 0.0
        score_breakdown: Dict[str, float] = {}

        change_percent = symbol_data["change_percent"]
        if change_percent > 0:
            momentum_score = min(change_percent * 2.5, 25.0)
        else:
            momentum_score = max(change_percent * 2.5, -10.0)
        score += momentum_score
        score_breakdown["momentum"] = momentum_score

        rsi = indicators["rsi"]
        if 30 <= rsi <= 70:
            rsi_score = 20.0
        elif 20 <= rsi < 30:
            rsi_score = 25.0
        elif 70 < rsi <= 80:
            rsi_score = 10.0
        else:
            rsi_score = 0.0
        score += rsi_score
        score_breakdown["rsi"] = rsi_score

        macd_signal = indicators["macd_signal"]
        if macd_signal == "BULLISH":
            macd_score = 15.0
        elif macd_signal == "BEARISH":
            macd_score = -5.0
        else:
            macd_score = 5.0
        score += macd_score
        score_breakdown["macd"] = macd_score

        current_price = symbol_data["price"]
        sma_20 = indicators["sma_20"]
        trend_score = 15.0 if current_price > sma_20 else -5.0
        score += trend_score
        score_breakdown["trend"] = trend_score

        bb_upper = indicators["bb_upper"]
        bb_lower = indicators["bb_lower"]
        if bb_upper != bb_lower:
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            bb_position = min(max(bb_position, 0.0), 1.0)
            bb_score = bb_position * 10.0
        else:
            bb_score = 5.0
        score += bb_score
        score_breakdown["bollinger"] = bb_score

        volatility = indicators["volatility"]
        if volatility < 0.5:
            volatility_bonus = 1.0
        elif volatility <= 2.5:
            volatility_bonus = 6.0
        elif volatility <= 5.0:
            volatility_bonus = 10.0
        elif volatility <= 8.0:
            volatility_bonus = 5.0
        else:
            volatility_bonus = 0.0
        score += volatility_bonus
        score_breakdown["volatility"] = volatility_bonus

        volume_momentum = indicators["volume_momentum"]
        volume_score = min(max(volume_momentum / 10.0, -5.0), 5.0)
        score += volume_score
        score_breakdown["volume_momentum"] = volume_score

        final_score = min(max(score, 0.0), 100.0)
        return {"bullish_score": final_score, "score_breakdown": score_breakdown}

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate a simplified RSI from close prices."""
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
        """Return a simplified MACD direction using EMA-style smoothing."""
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
        """Calculate a lightweight EMA for directional comparisons."""
        if len(closes) < period:
            return closes[-1]

        multiplier = 2 / (period + 1)
        ema = sum(closes[:period]) / period
        for price in closes[period:]:
            ema = ((price - ema) * multiplier) + ema
        return ema

    def _calculate_bollinger_bands(
        self, closes: List[float], period: int = 20, std_dev: float = 2.0
    ) -> tuple[float, float]:
        """Calculate a simple Bollinger band pair."""
        if len(closes) < period:
            latest = closes[-1]
            return latest * 1.02, latest * 0.98

        sma = sum(closes[-period:]) / period
        variance = sum((value - sma) ** 2 for value in closes[-period:]) / period
        std = variance**0.5
        return sma + (std * std_dev), sma - (std * std_dev)
