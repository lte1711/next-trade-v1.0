"""
Realtime data helpers for the modular trading simulator.
"""

from typing import Any, Dict, List

import requests


class RealTimeDataFetcher:
    """Fetch ticker data and derive lightweight intraday signals."""

    def __init__(self, exchange_base_url: str = "https://demo-fapi.binance.com"):
        self.exchange_base_url = exchange_base_url

    def get_real_time_symbol_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch current ticker data plus derived indicators for each symbol."""
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
                indicator_source = self._get_indicator_source(symbol)
                closes = indicator_source["closes"]
                volumes = indicator_source["volumes"]

                symbol_data = {
                    "symbol": symbol,
                    "price": float(ticker_data["lastPrice"]),
                    "change_percent": float(ticker_data["priceChangePercent"]),
                    "volume": float(ticker_data["volume"]),
                    "quote_volume": float(ticker_data.get("quoteVolume", 0.0)),
                    "quoteVolume": float(ticker_data.get("quoteVolume", 0.0)),
                    "rsi": self._calculate_rsi_from_closes(closes),
                    "macd_signal": self._calculate_macd_from_closes(closes),
                    "bullish_score": self._calculate_bullish_score_from_series(closes, volumes),
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
        """Calculate RSI from one-hour candles."""
        try:
            source = self._get_indicator_source(symbol)
            return self._calculate_rsi_from_closes(source["closes"])
        except Exception as exc:
            print(f"  {symbol} RSI calculation failed: {exc}")
            return 50.0

    def calculate_real_time_macd(self, symbol: str) -> str:
        """Return a simplified MACD direction from one-hour candles."""
        try:
            source = self._get_indicator_source(symbol)
            return self._calculate_macd_from_closes(source["closes"])
        except Exception as exc:
            print(f"  {symbol} MACD calculation failed: {exc}")
            return "NEUTRAL"

    def calculate_real_time_bullish_score(self, symbol: str) -> float:
        """Calculate a lightweight realtime bullish score from one-hour candles."""
        try:
            source = self._get_indicator_source(symbol)
            return self._calculate_bullish_score_from_series(source["closes"], source["volumes"])
        except Exception as exc:
            print(f"  {symbol} bullish score calculation failed: {exc}")
            return 50.0

    def find_high_potential_symbols(
        self, symbols: List[Dict[str, Any]], threshold: float = 75.0
    ) -> List[Dict[str, Any]]:
        """Return symbols whose profit potential clears the threshold."""
        print(f"FACT: high-potential symbol search started (threshold={threshold:.1f})")

        high_potential_symbols: List[Dict[str, Any]] = []
        for symbol_data in symbols:
            current_potential = self._calculate_profit_potential(symbol_data)
            symbol_data["profit_potential"] = current_potential

            if current_potential >= threshold:
                high_potential_symbols.append(symbol_data)
                print(f"  {symbol_data['symbol']}: profit potential {current_potential:.1f} (qualified)")
            else:
                print(f"  {symbol_data['symbol']}: profit potential {current_potential:.1f} (below)")

        high_potential_symbols.sort(key=lambda item: item["profit_potential"], reverse=True)
        print(f"  threshold-qualified symbols: {len(high_potential_symbols)}")
        return high_potential_symbols

    def _get_indicator_source(self, symbol: str, limit: int = 100) -> Dict[str, List[float]]:
        """Fetch one-hour candles once and reuse them for multiple indicators."""
        klines_response = requests.get(
            f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit={limit}",
            timeout=10,
        )
        if klines_response.status_code != 200:
            raise RuntimeError(f"{symbol} kline lookup failed with status {klines_response.status_code}")

        klines = klines_response.json()
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        if len(closes) < 2:
            raise RuntimeError(f"{symbol} kline response is too short")
        return {"closes": closes, "volumes": volumes}

    def _calculate_rsi_from_closes(self, closes: List[float], period: int = 14) -> float:
        """Calculate a simplified RSI from close prices."""
        if len(closes) < period + 1:
            return 50.0

        gains: List[float] = []
        losses: List[float] = []
        for index in range(1, len(closes)):
            change = closes[index] - closes[index - 1]
            if change > 0:
                gains.append(change)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return min(max(rsi, 0.0), 100.0)

    def _calculate_macd_from_closes(self, closes: List[float]) -> str:
        """Calculate a simplified MACD direction using EMA-style smoothing."""
        if len(closes) < 26:
            return "NEUTRAL"

        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)
        if ema_12 > ema_26:
            return "BULLISH"
        if ema_12 < ema_26:
            return "BEARISH"
        return "NEUTRAL"

    def _calculate_bullish_score_from_series(self, closes: List[float], volumes: List[float]) -> float:
        """Calculate a bounded bullish score from recent change and volume trend."""
        if len(closes) < 2:
            return 50.0

        recent_change = ((closes[-1] - closes[0]) / closes[0]) * 100
        recent_volume = sum(volumes[-5:]) / min(len(volumes), 5)
        previous_slice = volumes[-10:-5]
        previous_volume = sum(previous_slice) / len(previous_slice) if previous_slice else recent_volume
        volume_trend = (recent_volume / previous_volume) if previous_volume > 0 else 1.0

        bullish_score = 50.0
        if recent_change > 0:
            bullish_score += min(recent_change * 2, 30.0)
        else:
            bullish_score += max(recent_change * 2, -30.0)

        if volume_trend > 1.2:
            bullish_score += 20.0
        elif volume_trend > 1.0:
            bullish_score += 10.0
        elif volume_trend < 0.8:
            bullish_score -= 10.0

        return min(max(bullish_score, 0.0), 100.0)

    def _calculate_profit_potential(self, symbol_data: Dict[str, Any]) -> float:
        """Combine momentum, liquidity, RSI, and MACD into a bounded score."""
        potential = 0.0

        bullish_score = symbol_data.get("bullish_score", 0.0)
        potential += bullish_score * 0.4

        change_percent = symbol_data.get("change_percent", 0.0)
        if change_percent > 0:
            momentum_score = min(change_percent * 3.0, 25.0)
        else:
            momentum_score = max(change_percent * 1.5, -10.0)
        potential += momentum_score

        quote_volume = symbol_data.get("quote_volume", symbol_data.get("quoteVolume", 0.0))
        potential += min(quote_volume / 50_000_000, 15.0)

        rsi = symbol_data.get("rsi", 50.0)
        if 40 <= rsi <= 60:
            rsi_score = 10.0
        elif 30 <= rsi < 40:
            rsi_score = 15.0
        elif 60 < rsi <= 70:
            rsi_score = 8.0
        else:
            rsi_score = 0.0
        potential += rsi_score

        if symbol_data.get("macd_signal", "NEUTRAL") == "BULLISH":
            potential += 5.0

        return min(max(potential, 0.0), 100.0)

    def _calculate_ema(self, closes: List[float], period: int) -> float:
        """Calculate a lightweight EMA."""
        if len(closes) < period:
            return closes[-1]

        multiplier = 2 / (period + 1)
        ema = sum(closes[:period]) / period
        for price in closes[period:]:
            ema = ((price - ema) * multiplier) + ema
        return ema
