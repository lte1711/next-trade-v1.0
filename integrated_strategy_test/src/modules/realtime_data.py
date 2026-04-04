"""
Modular simulator realtime data helpers.
"""

from typing import Any, Dict, List

import requests


class RealTimeDataFetcher:
    """Fetches ticker data and lightweight realtime indicators."""

    def __init__(self, exchange_base_url: str = "https://demo-fapi.binance.com"):
        self.exchange_base_url = exchange_base_url

    def get_real_time_symbol_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch current ticker plus derived indicators for each symbol."""
        real_time_data: List[Dict[str, Any]] = []

        print(f"FACT: realtime symbol lookup started ({len(symbols)} symbols)")

        for symbol in symbols:
            try:
                ticker_response = requests.get(
                    f"{self.exchange_base_url}/fapi/v1/ticker/24hr?symbol={symbol}",
                    timeout=10,
                )
                if ticker_response.status_code != 200:
                    print(f"  {symbol}: API response error ({ticker_response.status_code})")
                    continue

                ticker_data = ticker_response.json()
                symbol_data = {
                    "symbol": symbol,
                    "price": float(ticker_data["lastPrice"]),
                    "change_percent": float(ticker_data["priceChangePercent"]),
                    "volume": float(ticker_data["volume"]),
                    "rsi": self.calculate_real_time_rsi(symbol),
                    "macd_signal": self.calculate_real_time_macd(symbol),
                    "bullish_score": self.calculate_real_time_bullish_score(symbol),
                }
                real_time_data.append(symbol_data)
                print(
                    f"  {symbol}: price=${symbol_data['price']:.4f}, "
                    f"change={symbol_data['change_percent']:+.2f}%"
                )

            except Exception as exc:
                print(f"  {symbol}: realtime lookup failed - {exc}")

        print(f"  realtime lookups succeeded: {len(real_time_data)}")
        return real_time_data

    def calculate_real_time_rsi(self, symbol: str) -> float:
        """Calculate RSI from the last 14 one-hour candles."""
        try:
            klines_response = requests.get(
                f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=14",
                timeout=10,
            )
            if klines_response.status_code != 200:
                return 50.0

            closes = [float(k[4]) for k in klines_response.json()]
            if len(closes) < 2:
                return 50.0

            gains: List[float] = []
            losses: List[float] = []
            for idx in range(1, len(closes)):
                change = closes[idx] - closes[idx - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / len(gains) if gains else 0.0
            avg_loss = sum(losses) / len(losses) if losses else 0.0
            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return min(max(rsi, 0.0), 100.0)

        except Exception as exc:
            print(f"  {symbol} RSI calculation failed: {exc}")
            return 50.0

    def calculate_real_time_macd(self, symbol: str) -> str:
        """Return a simplified MACD direction from one-hour candles."""
        try:
            klines_response = requests.get(
                f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=26",
                timeout=10,
            )
            if klines_response.status_code != 200:
                return "NEUTRAL"

            closes = [float(k[4]) for k in klines_response.json()]
            if len(closes) < 26:
                return "NEUTRAL"

            ema_12 = closes[0]
            for price in closes[1:12]:
                ema_12 = (price * 2 / 13) + (ema_12 * 11 / 13)

            ema_26 = closes[0]
            for price in closes[1:26]:
                ema_26 = (price * 2 / 27) + (ema_26 * 25 / 27)

            macd_line = ema_12 - ema_26
            if macd_line > 0:
                return "BULLISH"
            if macd_line < 0:
                return "BEARISH"
            return "NEUTRAL"

        except Exception as exc:
            print(f"  {symbol} MACD calculation failed: {exc}")
            return "NEUTRAL"

    def calculate_real_time_bullish_score(self, symbol: str) -> float:
        """Calculate a lightweight realtime bullish score."""
        try:
            klines_response = requests.get(
                f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=24",
                timeout=10,
            )
            if klines_response.status_code != 200:
                return 50.0

            klines = klines_response.json()
            closes = [float(k[4]) for k in klines]
            if len(closes) < 2:
                return 50.0

            recent_change = (closes[-1] - closes[0]) / closes[0] * 100
            volumes = [float(k[5]) for k in klines]
            previous_volume_sum = sum(volumes[-10:-5]) if len(volumes) >= 10 else 0.0
            volume_trend = (sum(volumes[-5:]) / previous_volume_sum) if previous_volume_sum > 0 else 1.0

            bullish_score = 50.0
            if recent_change > 0:
                bullish_score += min(recent_change * 2, 30)
            else:
                bullish_score += max(recent_change * 2, -30)

            if volume_trend > 1.2:
                bullish_score += 20
            elif volume_trend > 1.0:
                bullish_score += 10
            elif volume_trend < 0.8:
                bullish_score -= 10

            return min(max(bullish_score, 0.0), 100.0)

        except Exception as exc:
            print(f"  {symbol} bullish score calculation failed: {exc}")
            return 50.0

    def find_high_potential_symbols(
        self, symbols: List[Dict[str, Any]], threshold: float = 75.0
    ) -> List[Dict[str, Any]]:
        """Return symbols whose realtime profit potential meets the threshold."""
        print(f"FACT: high-potential symbol search started (threshold: {threshold}%)")

        high_potential_symbols: List[Dict[str, Any]] = []
        for symbol_data in symbols:
            current_potential = self._calculate_profit_potential(symbol_data)
            symbol_data["profit_potential"] = current_potential

            if current_potential >= threshold:
                high_potential_symbols.append(symbol_data)
                print(
                    f"  {symbol_data['symbol']}: profit potential {current_potential:.1f}% "
                    f"(meets threshold)"
                )
            else:
                print(
                    f"  {symbol_data['symbol']}: profit potential {current_potential:.1f}% "
                    f"(below threshold)"
                )

        high_potential_symbols.sort(key=lambda item: item["profit_potential"], reverse=True)
        print(f"  threshold-qualified symbols: {len(high_potential_symbols)}")
        return high_potential_symbols

    def _calculate_profit_potential(self, symbol_data: Dict[str, Any]) -> float:
        """Combine momentum, volume, RSI and MACD into a potential score."""
        potential = 0.0

        bullish_score = symbol_data.get("bullish_score", 0.0)
        potential += bullish_score * 0.4

        change_percent = symbol_data.get("change_percent", 0.0)
        if change_percent > 0:
            momentum_score = min(change_percent * 3, 25)
        else:
            momentum_score = 0
        potential += momentum_score

        volume = symbol_data.get("volume", 0.0)
        potential += min(volume / 800000, 15)

        rsi = symbol_data.get("rsi", 50.0)
        if 40 <= rsi <= 60:
            rsi_score = 10
        elif 30 <= rsi < 40:
            rsi_score = 15
        elif 60 < rsi <= 70:
            rsi_score = 8
        else:
            rsi_score = 0
        potential += rsi_score

        if symbol_data.get("macd_signal", "NEUTRAL") == "BULLISH":
            potential += 5

        return potential
