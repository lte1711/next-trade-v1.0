"""
Public market-data client for the merged partial integration workspace.
"""

from typing import Any, Dict, List

import requests


class PublicReadClient:
    """Read-only market data access for ticker and kline lookups."""

    def __init__(self, exchange_base_url: str = "https://demo-fapi.binance.com"):
        self.exchange_base_url = exchange_base_url.rstrip("/")

    def get_top_quote_volume_symbols(self, limit: int = 80) -> List[Dict[str, Any]]:
        """Return liquid USDT futures symbols sorted by quote volume."""
        response = requests.get(f"{self.exchange_base_url}/fapi/v1/ticker/24hr", timeout=10)
        response.raise_for_status()

        symbols: List[Dict[str, Any]] = []
        for item in response.json():
            try:
                symbol = str(item["symbol"])
                volume = float(item["volume"])
                quote_volume = float(item["quoteVolume"])
                price = float(item["lastPrice"])
                change_percent = float(item["priceChangePercent"])
            except (KeyError, TypeError, ValueError):
                continue

            if symbol.endswith("USDT") and volume > 0 and quote_volume > 0:
                symbols.append(
                    {
                        "symbol": symbol,
                        "volume": volume,
                        "quote_volume": quote_volume,
                        "quoteVolume": quote_volume,
                        "price": price,
                        "change_percent": change_percent,
                    }
                )

        symbols.sort(key=lambda item: item["quote_volume"], reverse=True)
        return symbols[:limit]

    def get_symbol_ticker(self, symbol: str) -> Dict[str, Any]:
        """Return 24h ticker information for one symbol."""
        response = requests.get(
            f"{self.exchange_base_url}/fapi/v1/ticker/24hr?symbol={symbol}",
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "symbol": symbol,
            "price": float(payload["lastPrice"]),
            "change_percent": float(payload["priceChangePercent"]),
            "volume": float(payload["volume"]),
            "quote_volume": float(payload.get("quoteVolume", 0.0)),
            "quoteVolume": float(payload.get("quoteVolume", 0.0)),
        }

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[List[Any]]:
        """Return raw kline rows from the exchange."""
        response = requests.get(
            f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
