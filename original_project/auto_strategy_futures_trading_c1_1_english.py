#!/usr/bin/env python3
"""
Automated Strategy Futures Trading System - Complete Refactoring
================================================
Modifications:
  [1] API key hardcoding removal → Environment variables mandatory
  [2] random() complete removal → Real market data based signals
  [3] Position size unit modification (USD → Quantity)
  [4] __init__ initialization order modification (Network calls separated)
  [5] Volatility calculation modification (Price difference → Return rate standard deviation)
  [6] API call minimization (Caching + Batch processing)
  [7] All Korean messages and icons changed to English
"""

import json
import time
import hmac
import hashlib
import os
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import requests


# ─────────────────────────────────────────────────────
# 0. Configuration & Constants
# ─────────────────────────────────────────────────────

TESTNET_BASE_URL  = "https://testnet.binancefuture.com"
MAINNET_BASE_URL  = "https://fapi.binance.com"

# Cache validity time (seconds)
KLINES_CACHE_TTL  = 60    # 1 minute
PRICE_CACHE_TTL   = 5     # 5 seconds

# Strategy default parameters (backtest-based fixed values)
STRATEGY_PARAMS = {
    "momentum": {
        "stop_loss":    0.03,   # 3%
        "take_profit":  0.06,   # 6%  (RR 1:2)
        "risk_per_trade": 0.01, # 1% of account
    },
    "mean_reversion": {
        "stop_loss":    0.025,
        "take_profit":  0.05,
        "risk_per_trade": 0.01,
    },
    "volatility": {
        "stop_loss":    0.04,
        "take_profit":  0.10,
        "risk_per_trade": 0.008,
    },
    "trend_following": {
        "stop_loss":    0.035,
        "take_profit":  0.08,
        "risk_per_trade": 0.012,
    },
    "arbitrage": {
        "stop_loss":    0.005,
        "take_profit":  0.003,
        "risk_per_trade": 0.005,
    },
}

TOP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT",
    "LINKUSDT", "BNBUSDT", "SOLUSDT", "LTCUSDT", "BCHUSDT",
    "AVAXUSDT", "MATICUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT",
    "ETCUSDT", "ICPUSDT", "VETUSDT", "THETAUSDT", "FTMUSDT",
]


# ─────────────────────────────────────────────────────
# 1. Enums
# ─────────────────────────────────────────────────────

class MarketRegime(Enum):
    BULL     = "BULL_MARKET"
    BEAR     = "BEAR_MARKET"
    SIDEWAYS = "SIDEWAYS_MARKET"


class Signal(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# ─────────────────────────────────────────────────────
# 2. Data Classes
# ─────────────────────────────────────────────────────

@dataclass
class MarketState:
    regime:     MarketRegime
    volatility: float   # Return rate based standard deviation
    strength:   float   # Average return rate (replaces EMA slope)
    spread_pct: float = 0.0


@dataclass
class TradeSignal:
    strategy:       str
    signal:         Signal
    strength:       float
    leverage:       float
    stop_loss_pct:  float
    take_profit_pct: float
    risk_per_trade: float
    reason:         str = ""


@dataclass
class PerformanceTracker:
    pnl_list: list = field(default_factory=list)
    wins:  int = 0
    losses: int = 0

    def record(self, pnl_pct: float):
        self.pnl_list.append(pnl_pct)
        if pnl_pct > 0:
            self.wins += 1
        else:
            self.losses += 1

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total else 0.0

    def summary(self) -> dict:
        return {
            "total_trades": self.wins + self.losses,
            "win_rate":     round(self.win_rate, 3),
            "total_pnl":    round(sum(self.pnl_list), 4),
        }


# ─────────────────────────────────────────────────────
# 3. API Client (Caching + Batch Processing)
# ─────────────────────────────────────────────────────

class BinanceClient:
    """
    Binance Futures API Client
    - API keys loaded only from environment variables (hardcoding prohibited)
    - Caching for API rate limit protection
    - Batch processing for API call minimization
    """

    def __init__(self, testnet: bool = True):
        # [Modification 1] Load only from environment variables, no fallback defaults
        self.api_key    = os.environ.get("BINANCE_TESTNET_KEY") if testnet else os.environ.get("BINANCE_API_KEY")
        self.api_secret = os.environ.get("BINANCE_TESTNET_SECRET") if testnet else os.environ.get("BINANCE_API_SECRET")
        self.base_url   = TESTNET_BASE_URL if testnet else MAINNET_BASE_URL
        self.testnet    = testnet

        if not self.api_key or not self.api_secret:
            env_name = "BINANCE_TESTNET_KEY / BINANCE_TESTNET_SECRET" if testnet else "BINANCE_API_KEY / BINANCE_API_SECRET"
            raise EnvironmentError(
                f"API key not configured.\n"
                f"Please set environment variables: {env_name}\n"
                f"Example) export {env_name.split('/')[0].strip()}=your_key_here"
            )

        # Cache storage
        self._klines_cache:  dict[str, tuple[float, list]] = {}   # symbol → (timestamp, data)
        self._price_cache:   dict[str, tuple[float, float]] = {}  # symbol → (timestamp, price)
        self._symbol_cache:  dict[str, dict] = {}                 # symbol → info
        self._exchange_info: Optional[dict] = None

        print(f"[OK] BinanceClient initialized ({'testnet' if testnet else 'live'})")

    # ── Signature ────────────────────────────────────────
    def _sign(self, params: dict) -> str:
        query = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _headers(self) -> dict:
        return {"X-MBX-APIKEY": self.api_key}

    # ── Server Time ────────────────────────────────────
    def get_server_time(self) -> int:
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            r.raise_for_status()
            return r.json()["serverTime"]
        except Exception:
            return int(time.time() * 1000)

    # ── Account Balance ────────────────────────────────────
    def get_balance(self) -> float:
        params = {"timestamp": self.get_server_time(), "recvWindow": 5000}
        params["signature"] = self._sign(params)
        try:
            r = requests.get(
                f"{self.base_url}/fapi/v2/account",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return float(r.json()["totalWalletBalance"])
        except Exception as e:
            print(f"[ERROR] Balance query failed: {e}")
            raise

    # ── Symbol List ─────────────────────────────────────
    def get_exchange_info(self) -> dict:
        if self._exchange_info:
            return self._exchange_info
        r = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
        r.raise_for_status()
        self._exchange_info = r.json()
        return self._exchange_info

    def get_valid_symbols(self) -> list[str]:
        info = self.get_exchange_info()
        trading = {s["symbol"] for s in info["symbols"] if s["status"] == "TRADING"}
        return [s for s in TOP_SYMBOLS if s in trading]

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]
        info = self.get_exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                self._symbol_cache[symbol] = s
                return s
        return None

    # ── Price Query (Cache) ──────────────────────────────────────
    def get_price(self, symbol: str) -> float:
        now = time.time()
        if symbol in self._price_cache:
            ts, price = self._price_cache[symbol]
            if now - ts < PRICE_CACHE_TTL:
                return price
        try:
            r = requests.get(
                f"{self.base_url}/fapi/v1/ticker/price",
                params={"symbol": symbol},
                timeout=5,
            )
            r.raise_for_status()
            price = float(r.json()["price"])
            self._price_cache[symbol] = (now, price)
            return price
        except Exception as e:
            print(f"[ERROR] {symbol} price query failed: {e}")
            raise

    # ── Batch Price Query (Single API Call for All) ───────────────
    def get_all_prices(self) -> dict[str, float]:
        """Single API call for all symbol prices — saves rate limit"""
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/ticker/price", timeout=10)
            r.raise_for_status()
            now = time.time()
            prices = {}
            for item in r.json():
                sym = item["symbol"]
                price = float(item["price"])
                prices[sym] = price
                self._price_cache[sym] = (now, price)
            return prices
        except Exception as e:
            print(f"[ERROR] Batch price query failed: {e}")
            return {}

    # ── Klines (Cache) ─────────────────────────────────────────
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list:
        cache_key = f"{symbol}_{interval}_{limit}"
        now = time.time()
        if cache_key in self._klines_cache:
            ts, data = self._klines_cache[cache_key]
            if now - ts < KLINES_CACHE_TTL:
                return data
        try:
            r = requests.get(
                f"{self.base_url}/fapi/v1/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            self._klines_cache[cache_key] = (now, data)
            return data
        except Exception as e:
            print(f"[ERROR] {symbol} klines query failed: {e}")
            return []

    # ── Order Submission ─────────────────────────────────────
    def submit_order(self, symbol: str, side: str, quantity: float) -> Optional[dict]:
        params = {
            "symbol":     symbol,
            "side":       side,
            "type":       "MARKET",
            "quantity":   str(quantity),
            "timestamp":  self.get_server_time(),
            "recvWindow": 5000,
        }
        params["signature"] = self._sign(params)
        try:
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            print(f"[ERROR] Order failed ({symbol} {side}): {e.response.text}")
            return None
        except Exception as e:
            print(f"[ERROR] Order failed: {e}")
            return None

    def submit_stop_market(self, symbol: str, side: str, quantity: float, stop_price: float) -> Optional[dict]:
        params = {
            "symbol":     symbol,
            "side":       side,
            "type":       "STOP_MARKET",
            "quantity":   str(quantity),
            "stopPrice":  str(round(stop_price, 4)),
            "timestamp":  self.get_server_time(),
            "recvWindow": 5000,
        }
        params["signature"] = self._sign(params)
        try:
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            print(f"[ERROR] Stop loss order failed: {e.response.text}")
            return None

    def submit_take_profit(self, symbol: str, side: str, quantity: float, price: float) -> Optional[dict]:
        params = {
            "symbol":      symbol,
            "side":        side,
            "type":        "LIMIT",
            "quantity":    str(quantity),
            "price":       str(round(price, 4)),
            "timeInForce": "GTC",
            "timestamp":   self.get_server_time(),
            "recvWindow": 5000,
        }
        params["signature"] = self._sign(params)
        try:
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            print(f"[ERROR] Take profit order failed: {e.response.text}")
            return None


# ─────────────────────────────────────────────────────
# 4. Market Analyzer
# ─────────────────────────────────────────────────────

class MarketAnalyzer:
    """
    [Modification 5] Volatility calculation modified: Symbol price difference → Return rate standard deviation
    [Modification 6] Klines caching to minimize API calls
    """

    # BTC-based market regime analysis only (analyzes all symbols every time X)
    REGIME_SYMBOL = "BTCUSDT"

    def __init__(self, client: BinanceClient):
        self.client = client
        self._regime_cache: Optional[tuple[float, MarketState]] = None
        self._regime_ttl = 300  # Update every 5 minutes

    def get_market_state(self, symbol: str = REGIME_SYMBOL) -> MarketState:
        """Return cached market state (5 minute TTL)"""
        now = time.time()
        if self._regime_cache:
            ts, state = self._regime_cache
            if now - ts < self._regime_ttl:
                return state

        state = self._analyze(symbol)
        self._regime_cache = (now, state)
        return state

    def _analyze(self, symbol: str) -> MarketState:
        klines = self.client.get_klines(symbol, "1h", 24)
        if not klines:
            return MarketState(MarketRegime.SIDEWAYS, 0.02, 0.0)

        # [Modification 5] Return rate based volatility calculation
        returns = []
        for k in klines:
            open_p  = float(k[1])
            close_p = float(k[4])
            if open_p > 0:
                returns.append((close_p - open_p) / open_p)

        if not returns:
            return MarketState(MarketRegime.SIDEWAYS, 0.02, 0.0)

        avg_return = sum(returns) / len(returns)
        variance   = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5

        # Market regime
        if avg_return > 0.005:       # Average hourly +0.5% → Bull market
            regime = MarketRegime.BULL
        elif avg_return < -0.005:    # Average hourly -0.5% → Bear market
            else:
                regime = MarketRegime.SIDEWAYS

        return MarketState(
            regime     = regime,
            volatility = round(volatility, 6),
            strength   = round(avg_return, 6),
        )


# ─────────────────────────────────────────────────────
# 5. Strategy Engine (Complete random removal)
# ─────────────────────────────────────────────────────

class StrategyEngine:
    """
    [Modification 2] Complete random removal
    All signals are deterministically derived from market data
    """

    MAX_LEVERAGE = 20.0
    MIN_LEVERAGE = 2.0

    def _calc_leverage(self, volatility: float) -> float:
        """Inverse proportion leverage to volatility"""
        raw = self.MAX_LEVERAGE * (0.01 / max(volatility, 0.001))
        return round(min(max(raw, self.MIN_LEVERAGE), self.MAX_LEVERAGE), 1)

    def _build(self, name: str, signal: Signal, strength: float,
               market: MarketState, reason: str) -> TradeSignal:
        params  = STRATEGY_PARAMS[name]
        vol     = market.volatility
        sl      = max(params["stop_loss"], 1.5 * vol)
        tp      = sl * 2.0
        return TradeSignal(
            strategy        = name,
            signal          = signal,
            strength        = round(strength, 3),
            leverage        = self._calc_leverage(vol),
            stop_loss_pct   = round(sl, 4),
            take_profit_pct = round(tp, 4),
            risk_per_trade  = params["risk_per_trade"],
            reason          = reason,
        )

    def momentum(self, market: MarketState) -> TradeSignal:
        if market.regime == MarketRegime.BULL and market.strength > 0.003:
            return self._build("momentum", Signal.BUY, 0.80, market, "Bull market momentum buy")
        if market.regime == MarketRegime.BEAR and market.strength < -0.003:
            return self._build("momentum", Signal.SELL, 0.80, market, "Bear market momentum sell")
        return self._build("momentum", Signal.HOLD, 0.20, market, "Trend unclear → Hold")

    def mean_reversion(self, market: MarketState) -> TradeSignal:
        if market.regime == MarketRegime.SIDEWAYS and abs(market.strength) < 0.002:
            sig = Signal.BUY if market.strength < 0 else Signal.SELL
            reason = "Sideways oversold reversal buy" if sig == Signal.BUY else "Sideways overbought reversal sell"
            return self._build("mean_reversion", sig, 0.70, market, reason)
        return self._build("mean_reversion", Signal.HOLD, 0.20, market, "Trending market → Mean reversion not suitable")

    def volatility(self, market: MarketState) -> TradeSignal:
        if market.volatility > 0.03:
            sig = Signal.BUY if market.strength > 0 else Signal.SELL
            return self._build("volatility", sig, 0.75, market,
                               f"High volatility({market.volatility:.2%}) breakout")
        return self._build("volatility", Signal.HOLD, 0.20, market, "Low volatility → Hold")

    def trend_following(self, market: MarketState) -> TradeSignal:
        s = market.strength
        if s > 0.005:
            return self._build("trend_following", Signal.BUY, 0.70, market,
                               f"Uptrend (strength={s:.4f})")
        if s < -0.005:
            return self._build("trend_following", Signal.SELL, 0.70, market,
                               f"Downtrend (strength={s:.4f})")
        return self._build("trend_following", Signal.HOLD, 0.20, market, "No trend")

    def arbitrage(self, market: MarketState) -> TradeSignal:
        """Spread based — spread_pct is injected externally"""
        spread = market.spread_pct
        if spread > 0.15:
            return TradeSignal("arbitrage", Signal.SELL,
                               min(spread / 0.15 * 0.5, 0.95),
                               3.0, 0.005, 0.003, 0.005,
                               f"Spread {spread:.3f}% arbitrage entry")
        if spread < -0.15:
            return TradeSignal("arbitrage", Signal.BUY,
                               min(abs(spread) / 0.15 * 0.5, 0.95),
                               3.0, 0.005, 0.003, 0.005,
                               f"Reverse spread {spread:.3f}% reverse arbitrage entry")
        return TradeSignal("arbitrage", Signal.HOLD, 0.0,
                           1.0, 0.0, 0.0, 0.0, "Spread below threshold → No opportunity")

    def run_all(self, market: MarketState) -> dict[str, TradeSignal]:
        return {
            "momentum":       self.momentum(market),
            "mean_reversion": self.mean_reversion(market),
            "volatility":     self.volatility(market),
            "trend_following":self.trend_following(market),
            "arbitrage":      self.arbitrage(market),
        }

    def aggregate(self, signals: dict[str, TradeSignal], threshold: float = 0.55) -> TradeSignal:
        """Weighted sum final signal"""
        buy_score = sum(s.strength for s in signals.values() if s.signal == Signal.BUY)
        sel_score = sum(s.strength for s in signals.values() if s.signal == Signal.SELL)
        total = buy_score + sel_score

        if total == 0:
            # Return strongest signal as reference
            best = max(signals.values(), key=lambda s: s.strength)
            return best

        if buy_score > sel_score and buy_score / total >= threshold:
            candidates = [s for s in signals.values() if s.signal == Signal.BUY]
        elif sel_score > buy_score and sel_score / total >= threshold:
            candidates = [s for s in signals.values() if s.signal == Signal.SELL]
        else:
            best = max(signals.values(), key=lambda s: s.strength)
            return TradeSignal(best.strategy, Signal.HOLD, 0.5,
                               best.leverage, best.stop_loss_pct,
                               best.take_profit_pct, best.risk_per_trade,
                               "Signal insufficient → Hold")

        return max(candidates, key=lambda s: s.strength)


# ─────────────────────────────────────────────────────
# 6. Order Executor
# ─────────────────────────────────────────────────────

class OrderExecutor:
    """
    [Modification 3] Position size: Dollar amount → Actual quantity conversion
    [Modification 4] Initialization order safety guarantee
    """

    def __init__(self, client: BinanceClient):
        self.client = client

    def calc_quantity(self, symbol: str, signal: TradeSignal,
                      total_capital: float) -> Optional[float]:
        """
        Quantity = (Account * risk_per_trade * leverage) / Current price
        → Apply LOT_SIZE, MIN_NOTIONAL filters
        """
        info = self.client.get_symbol_info(symbol)
        if not info:
            print(f"[ERROR] No symbol info for {symbol}")
            return None

        try:
            price = self.client.get_price(symbol)
        except Exception:
            return None

        # Dollar-based position
        dollar_position = total_capital * signal.risk_per_trade * signal.leverage
        max_position    = total_capital * 0.20   # Maximum 20%
        dollar_position = min(dollar_position, max_position)

        # [Modification 3] Quantity calculation (Dollar → Coin quantity)
        raw_qty = dollar_position / price

        # LOT_SIZE, MIN_NOTIONAL filter application
        min_qty      = 0.0
        max_qty      = float("inf")
        step_size    = None
        min_notional = 5.0

        for f in info.get("filters", []):
            if f["filterType"] == "LOT_SIZE":
                min_qty   = float(f["minQty"])
                max_qty   = float(f["maxQty"])
                step_size = f.get("stepSize", "1")
            elif f["filterType"] == "MIN_NOTIONAL":
                min_notional = float(f.get("notional", f.get("minNotional", 5.0)))

        # StepSize based precision
        qty_precision = 0
        if step_size and "." in step_size:
            qty_precision = len(step_size.rstrip("0").split(".")[1])

        qty = max(raw_qty, min_qty)
        qty = min(qty, max_qty)
        qty = round(qty, qty_precision)

        # MIN_NOTIONAL correction
        if qty * price < min_notional:
            qty = round((min_notional * 1.01) / price, qty_precision)

        print(f"[CALC] {symbol} | Price=${price:.4f} | Position=${dollar_position:.2f} | Quantity={qty}")
        return qty

    def execute(self, symbol: str, signal: TradeSignal,
                total_capital: float) -> Optional[dict]:
        if signal.signal == Signal.HOLD:
            return None

        qty = self.calc_quantity(symbol, signal, total_capital)
        if not qty:
            return None

        side = signal.signal.value  # "BUY" or "SELL"
        result = self.client.submit_order(symbol, side, qty)
        if not result:
            return None

        print(f"[OK] Entry order successful: {symbol} {side} {qty}")

        # Stop loss / Take profit orders
        try:
            price = self.client.get_price(symbol)
            exit_side = "SELL" if side == "BUY" else "BUY"

            if side == "BUY":
                sl_price = price * (1 - signal.stop_loss_pct)
                tp_price = price * (1 + signal.take_profit_pct)
            else:
                sl_price = price * (1 + signal.stop_loss_pct)
                tp_price = price * (1 - signal.take_profit_pct)

            if self.client.testnet:
                # Testnet: Stop loss / Take profit simulation
                print(f"[SIM] Stop loss=${sl_price:.4f} ({signal.stop_loss_pct:.1%}) | "
                      f"Take profit=${tp_price:.4f} ({signal.take_profit_pct:.1%})")
            else:
                self.client.submit_stop_market(symbol, exit_side, qty, sl_price)
                self.client.submit_take_profit(symbol, exit_side, qty, tp_price)

        except Exception as e:
            print(f"[WARN] Stop loss / Take profit order failed: {e}")

        return result


# ─────────────────────────────────────────────────────
# 7. Main Trading System
# ─────────────────────────────────────────────────────

class AutoStrategyFuturesTrading:
    """
    [Modification 4] __init__ initialization order safely reconfigured
    Network calls separated into initialize() method
    """

    def __init__(self, testnet: bool = True, duration_hours: int = 24,
                 loop_interval_sec: int = 60):
        self.duration_hours    = duration_hours
        self.loop_interval_sec = loop_interval_sec

        # ── Client initialization (Environment variable verification) ──────────────
        self.client   = BinanceClient(testnet=testnet)
        self.analyzer = MarketAnalyzer(self.client)
        self.engine   = StrategyEngine()
        self.executor = OrderExecutor(self.client)

        # ── State (filled in initialize()) ─────────────────
        self.total_capital:  float      = 0.0
        self.valid_symbols:  list[str]  = []
        self.current_prices: dict       = {}

        self.start_time: Optional[datetime] = None
        self.end_time:   Optional[datetime] = None

        self.trackers: dict[str, PerformanceTracker] = {
            name: PerformanceTracker() for name in STRATEGY_PARAMS
        }
        self.results = {
            "trades":  [],
            "errors":  [],
        }

    def initialize(self):
        """
        [Modification 4] Network calls only here — Order guaranteed
        1. Symbol list
        2. Batch prices (Single API call)
        3. Account balance
        """
        print("[INIT] System initialization in progress...")

        # 1. Symbol list
        self.valid_symbols = self.client.get_valid_symbols()
        print(f"[OK] Tradable symbols: {len(self.valid_symbols)}")

        # 2. Batch price query (Single call)
        self.current_prices = self.client.get_all_prices()
        print(f"[OK] Price query: {len(self.current_prices)} symbols")

        # 3. Account balance query
        self.total_capital = self.client.get_balance()
        print(f"[OK] Account balance: ${self.total_capital:.2f}")

        self.start_time = datetime.now()
        self.end_time   = self.start_time + timedelta(hours=self.duration_hours)

        self.results["meta"] = {
            "start_time":    self.start_time.isoformat(),
            "end_time":      self.end_time.isoformat(),
            "total_capital": self.total_capital,
            "symbols":       len(self.valid_symbols),
            "testnet":       self.client.testnet,
        }

        print(f"[OK] Initialization complete | Capital=${self.total_capital:.2f} | "
              f"Symbols={len(self.valid_symbols)} | "
              f"End={self.end_time.strftime('%H:%M:%S')}")

    def _print_status(self, trade_count: int, error_count: int):
        now     = datetime.now()
        elapsed = now - self.start_time
        remain  = self.end_time - now
        prog    = elapsed.total_seconds() / (self.duration_hours * 3600) * 100

        market = self.analyzer.get_market_state()
        print("=" * 70)
        print(f"[{now.strftime('%H:%M:%S')}] Progress={prog:.1f}% | Remaining={remain} | Balance=${self.total_capital:.2f}")
        print(f"  Market regime: {market.regime.value} | Volatility={market.volatility:.3%} | Strength={market.strength:.4f}")
        print(f"  Trades={trade_count} | Errors={error_count}")
        for name, tracker in self.trackers.items():
            s = tracker.summary()
            if s["total_trades"] > 0:
                print(f"  [{name:15s}] Trades={s['total_trades']} WinRate={s['win_rate']:.0%} PnL={s['total_pnl']:+.4f}")

    def run(self):
        self.initialize()

        print("\n" + "=" * 70)
        print("[START] Automated Strategy Futures Trading")
        print("=" * 70)

        trade_count = 0
        error_count = 0

        while datetime.now() < self.end_time:
            try:
                # Batch price update (Single API call)
                self.current_prices = self.client.get_all_prices()

                # Market analysis (5 minute cache)
                market = self.analyzer.get_market_state()

                # Generate all strategy signals
                signals  = self.engine.run_all(market)
                final    = self.engine.aggregate(signals)

                self._print_status(trade_count, error_count)

                # Select suitable symbols for each strategy and trade
                # Symbol selection: Distribute valid_symbols by strategy
                symbols_per_strategy = max(1, len(self.valid_symbols) // len(STRATEGY_PARAMS))

                for i, (name, sig) in enumerate(signals.items()):
                    if sig.signal == Signal.HOLD:
                        print(f"  [{name}] HOLD — {sig.reason}")
                        continue

                    # Strategy-specific symbol slice
                    start = i * symbols_per_strategy
                    batch = self.valid_symbols[start: start + symbols_per_strategy]
                    if not batch:
                        batch = self.valid_symbols[:1]

                    # Select symbol with highest volume (highest price = proxy)
                    symbol = max(
                        batch,
                        key=lambda s: self.current_prices.get(s, 0),
                    )

                    result = self.executor.execute(symbol, sig, self.total_capital)

                    if result:
                        trade_count += 1
                        self.trackers[name].record(0)  # PnL updated at liquidation
                        self.results["trades"].append({
                            "time":     datetime.now().isoformat(),
                            "strategy": name,
                            "symbol":   symbol,
                            "signal":   sig.signal.value,
                            "leverage": sig.leverage,
                            "sl":       sig.stop_loss_pct,
                            "tp":       sig.take_profit_pct,
                            "reason":   sig.reason,
                        })
                        print(f"  [OK] {name} | {symbol} {sig.signal.value} {sig.leverage}x | {sig.reason}")
                    else:
                        error_count += 1
                        self.results["errors"].append({
                            "time":     datetime.now().isoformat(),
                            "strategy": name,
                            "symbol":   symbol,
                        })

                time.sleep(self.loop_interval_sec)

            except KeyboardInterrupt:
                print(f"\n[STOP] User interrupt: {datetime.now()}")
                break
            except Exception as e:
                print(f"[ERROR] Loop error: {e}")
                error_count += 1
                time.sleep(10)

        self._save_results(trade_count, error_count)

    def _save_results(self, trade_count: int, error_count: int):
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = results_dir / f"trading_results_{ts}.json"

        self.results["summary"] = {
            "total_trades":  trade_count,
            "total_errors":  error_count,
            "success_rate":  round(trade_count / max(trade_count + error_count, 1) * 100, 1),
            "trackers":      {k: v.summary() for k, v in self.trackers.items()},
            "end_time":      datetime.now().isoformat(),
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Results saved: {json_path}")
        print(f"[SUMMARY] Total trades={trade_count} | Errors={error_count} | "
              f"Success rate={self.results['summary']['success_rate']:.1f}%")


# ─────────────────────────────────────────────────────
# 8. Entry Point
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[START] Automated Strategy Futures Trading System")
    print("=" * 70)

    # Environment variable pre-verification
    required_env = ["BINANCE_TESTNET_KEY", "BINANCE_TESTNET_SECRET"]
    missing = [e for e in required_env if not os.environ.get(e)]
    if missing:
        print(f"[ERROR] Missing environment variables: {', '.join(missing)}")
        print("  Setup method:")
        for e in missing:
            print(f"    export {e}=your_value_here")
        exit(1)

    try:
        system = AutoStrategyFuturesTrading(
            testnet          = True,
            duration_hours   = 24,
            loop_interval_sec = 60,   # Loop every 1 minute (API rate limit protection)
        )
        system.run()

    except EnvironmentError as e:
        print(f"[ERROR] {e}")
        exit(1)
    except KeyboardInterrupt:
        print(f"\n[STOP] Exit: {datetime.now()}")
    except Exception as e:
        print(f"[ERROR] System error: {e}")
        import traceback
        traceback.print_exc()

    print("[END] System shutdown")
