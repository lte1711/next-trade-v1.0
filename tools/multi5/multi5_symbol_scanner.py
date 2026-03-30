from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from strategies.momentum_intraday_v1 import MomentumIntradayV1

try:
    from .multi5_config import (
        DYNAMIC_UNIVERSE_CACHE_SEC,
        DYNAMIC_UNIVERSE_LIMIT,
        DYNAMIC_UNIVERSE_MIN_QUOTE_VOLUME,
        DYNAMIC_UNIVERSE_QUOTE_ASSET,
        ENABLE_DYNAMIC_SYMBOL_UNIVERSE,
        SYMBOL_UNIVERSE,
    )
except ImportError:
    from multi5_config import (
        DYNAMIC_UNIVERSE_CACHE_SEC,
        DYNAMIC_UNIVERSE_LIMIT,
        DYNAMIC_UNIVERSE_MIN_QUOTE_VOLUME,
        DYNAMIC_UNIVERSE_QUOTE_ASSET,
        ENABLE_DYNAMIC_SYMBOL_UNIVERSE,
        SYMBOL_UNIVERSE,
    )

BINANCE_TESTNET_MARKET_URL = "https://demo-fapi.binance.com/fapi/v1/klines"
BINANCE_TESTNET_EXCHANGE_INFO_URL = "https://demo-fapi.binance.com/fapi/v1/exchangeInfo"
BINANCE_TESTNET_TICKER_24H_URL = "https://demo-fapi.binance.com/fapi/v1/ticker/24hr"
MOMENTUM_INTRADAY = MomentumIntradayV1()
_UNIVERSE_CACHE: dict[str, Any] = {
    "symbols": list(SYMBOL_UNIVERSE),
    "expires_at": datetime.now(timezone.utc),
}


def calculate_edge_score(prices: list[float]) -> float:
    if len(prices) < 20:
        return 0.0
    window = prices[-30:] if len(prices) >= 30 else prices
    mu = mean(window)
    sigma = pstdev(window) if len(window) > 1 else 0.0
    if sigma <= 0:
        return 0.0
    z = (window[-1] - mu) / sigma
    return max(0.0, min(abs(z) / 2.0, 1.8))


def _classify_regime(prices: list[float]) -> str:
    if len(prices) < 30:
        return "warmup"
    ma_short = mean(prices[-10:])
    ma_long = mean(prices[-30:])
    trend_strength = abs((ma_short - ma_long) / ma_long) if ma_long else 0.0
    returns: list[float] = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]
        if prev > 0:
            returns.append((prices[i] - prev) / prev)
    vol = pstdev(returns[-20:]) if len(returns) >= 20 else 0.0
    if vol > 0.0015:
        return "high_vol"
    if trend_strength > 0.0008:
        return "trend"
    return "range"


def _infer_exploratory_signal(
    *,
    edge_score: float,
    regime: str,
    roc: float,
    rsi: float,
    price: float,
    sma: float,
    volume_ratio: float,
) -> str:
    if edge_score < 0.45:
        return "HOLD"

    long_ok = roc >= 0.18 and price > sma and rsi >= 52.0 and volume_ratio >= 0.75
    short_ok = roc <= -0.18 and price < sma and rsi <= 48.0 and volume_ratio >= 0.75

    if regime == "range":
        if edge_score < 0.75:
            return "HOLD"
        if long_ok and rsi <= 68.0:
            return "LONG"
        if short_ok and rsi >= 32.0:
            return "SHORT"
        return "HOLD"

    if long_ok:
        return "LONG"
    if short_ok:
        return "SHORT"
    return "HOLD"


def build_symbol_state(symbol: str, closes: list[float], volumes: list[float]) -> dict[str, Any]:
    edge_score = calculate_edge_score(closes)
    returns: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev > 0:
            returns.append((closes[i] - prev) / prev)
    volatility = pstdev(returns[-20:]) if len(returns) >= 20 else 0.0
    regime = _classify_regime(closes)
    strategy_eval = MOMENTUM_INTRADAY.evaluate(symbol, closes, volumes)
    signal = str(strategy_eval.get("signal", "HOLD"))
    strategy_score = float(strategy_eval.get("signal_score", 0.0) or 0.0)
    signal_source = "strategy"
    if signal == "HOLD":
        exploratory_signal = _infer_exploratory_signal(
            edge_score=edge_score,
            regime=regime,
            roc=float(strategy_eval.get("roc_10", 0.0) or 0.0),
            rsi=float(strategy_eval.get("rsi_14", 50.0) or 50.0),
            price=float(strategy_eval.get("close", 0.0) or 0.0),
            sma=float(strategy_eval.get("sma_20", 0.0) or 0.0),
            volume_ratio=float(strategy_eval.get("volume_ratio", 0.0) or 0.0),
        )
        if exploratory_signal in {"LONG", "SHORT"}:
            signal = exploratory_signal
            strategy_score = max(strategy_score, min(1.2, edge_score))
            signal_source = "exploratory_fallback"
    boosted_edge = edge_score + (strategy_score if signal in {"LONG", "SHORT"} else 0.0)
    return {
        "symbol": symbol,
        "edge_score": round(boosted_edge, 6),
        "base_edge_score": round(edge_score, 6),
        "volatility": round(float(volatility), 6),
        "regime": regime,
        "strategy_id": strategy_eval.get("strategy_id"),
        "strategy_unit": strategy_eval.get("strategy_unit"),
        "strategy_signal": signal,
        "strategy_signal_source": signal_source,
        "strategy_signal_score": round(strategy_score, 6),
        "roc_10": strategy_eval.get("roc_10", 0.0),
        "rsi_14": strategy_eval.get("rsi_14", 50.0),
        "sma_20": strategy_eval.get("sma_20", 0.0),
        "close": strategy_eval.get("close", 0.0),
        "volume_ratio": strategy_eval.get("volume_ratio", 0.0),
        "take_profit_pct": strategy_eval.get("take_profit_pct", 0.012),
        "stop_loss_pct": strategy_eval.get("stop_loss_pct", 0.006),
    }


def _fetch_symbol_klines(symbol: str, interval: str = "5m", limit: int = 60) -> tuple[list[float], list[float]]:
    response = requests.get(
        BINANCE_TESTNET_MARKET_URL,
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=8,
    )
    response.raise_for_status()
    rows = response.json()
    closes: list[float] = []
    volumes: list[float] = []
    for row in rows:
        closes.append(float(row[4]))
        volumes.append(float(row[5]))
    return closes, volumes


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _fetch_dynamic_symbol_universe() -> list[str]:
    exchange_info = requests.get(BINANCE_TESTNET_EXCHANGE_INFO_URL, timeout=8)
    exchange_info.raise_for_status()
    ticker_24h = requests.get(BINANCE_TESTNET_TICKER_24H_URL, timeout=8)
    ticker_24h.raise_for_status()

    ticker_rows = ticker_24h.json()
    quote_volume_by_symbol: dict[str, float] = {}
    for row in ticker_rows:
        symbol = str(row.get("symbol", "")).upper().strip()
        if not symbol:
            continue
        try:
            quote_volume_by_symbol[symbol] = float(row.get("quoteVolume", 0.0) or 0.0)
        except Exception:
            quote_volume_by_symbol[symbol] = 0.0

    dynamic_symbols: list[tuple[str, float]] = []
    for row in exchange_info.json().get("symbols", []):
        symbol = str(row.get("symbol", "")).upper().strip()
        if not symbol:
            continue
        if str(row.get("status", "")).upper() != "TRADING":
            continue
        if str(row.get("quoteAsset", "")).upper() != DYNAMIC_UNIVERSE_QUOTE_ASSET:
            continue
        if str(row.get("contractType", "")).upper() != "PERPETUAL":
            continue
        if str(row.get("underlyingType", "")).upper() not in {"COIN", "INDEX", "STOCK", "COMMODITY"}:
            # Testnet occasionally returns mixed instruments; keep standard perpetual listings.
            pass
        quote_volume = quote_volume_by_symbol.get(symbol, 0.0)
        if quote_volume < DYNAMIC_UNIVERSE_MIN_QUOTE_VOLUME:
            continue
        dynamic_symbols.append((symbol, quote_volume))

    dynamic_symbols.sort(key=lambda item: item[1], reverse=True)
    resolved = [symbol for symbol, _ in dynamic_symbols[:DYNAMIC_UNIVERSE_LIMIT]]
    return resolved or list(SYMBOL_UNIVERSE)


def resolve_symbol_universe(symbols: list[str] | None = None) -> list[str]:
    if symbols:
        return symbols
    if not ENABLE_DYNAMIC_SYMBOL_UNIVERSE:
        return list(SYMBOL_UNIVERSE)

    now = _utc_now()
    cached_symbols = _UNIVERSE_CACHE.get("symbols") or []
    expires_at = _UNIVERSE_CACHE.get("expires_at")
    if isinstance(expires_at, datetime) and now < expires_at and cached_symbols:
        return list(cached_symbols)

    try:
        resolved = _fetch_dynamic_symbol_universe()
        _UNIVERSE_CACHE["symbols"] = list(resolved)
        _UNIVERSE_CACHE["expires_at"] = now + timedelta(seconds=max(30, DYNAMIC_UNIVERSE_CACHE_SEC))
        return list(resolved)
    except Exception:
        if cached_symbols:
            return list(cached_symbols)
        return list(SYMBOL_UNIVERSE)


def fetch_universe_data(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    universe = resolve_symbol_universe(symbols)
    states: list[dict[str, Any]] = []
    for symbol in universe:
        try:
            closes, volumes = _fetch_symbol_klines(symbol)
            states.append(build_symbol_state(symbol, closes, volumes))
        except Exception:
            states.append(
                {
                    "symbol": symbol,
                    "edge_score": 0.0,
                    "base_edge_score": 0.0,
                    "volatility": 0.0,
                    "regime": "error",
                    "strategy_id": MOMENTUM_INTRADAY.strategy_id,
                    "strategy_unit": MOMENTUM_INTRADAY.strategy_unit,
                    "strategy_signal": "HOLD",
                    "strategy_signal_score": 0.0,
                    "roc_10": 0.0,
                    "rsi_14": 50.0,
                    "sma_20": 0.0,
                    "close": 0.0,
                    "volume_ratio": 0.0,
                    "take_profit_pct": MOMENTUM_INTRADAY.take_profit_pct,
                    "stop_loss_pct": MOMENTUM_INTRADAY.stop_loss_pct,
                }
            )
    return states
