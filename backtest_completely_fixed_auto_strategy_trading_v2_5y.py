#!/usr/bin/env python3
"""
Five-year backtest runner for completely_fixed_auto_strategy_trading_v2.py.

This script keeps the live process untouched and runs a separate historical
simulation using public Binance futures market data.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = SCRIPT_DIR / os.getenv("V2_BACKTEST_SOURCE_FILE", "completely_fixed_auto_strategy_trading_v2.py")
OUTPUT_PATH = SCRIPT_DIR / f"backtest_v2_5y_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
PUBLIC_BASE_URL = "https://fapi.binance.com"
CACHE_DIR = SCRIPT_DIR / "data" / "backtest_cache_v2"
BACKTEST_SYMBOLS = [symbol.strip() for symbol in os.getenv("V2_BACKTEST_SYMBOLS", "BTCUSDT,ETHUSDT,XRPUSDT").split(",") if symbol.strip()]
EVALUATION_STEP_BARS = int(os.getenv("V2_BACKTEST_EVAL_STEP_BARS", "3"))
INITIAL_CAPITAL = float(os.getenv("V2_BACKTEST_INITIAL_CAPITAL", "10000"))
FEE_RATE = float(os.getenv("V2_BACKTEST_FEE_RATE", "0.0004"))
YEARS = float(os.getenv("V2_BACKTEST_YEARS", "5"))
EXIT_MODE = "ma_trailing_ema21"
COMPARE_EXIT_MODES = ""
TIMEFRAME_MODE = os.getenv("V2_BACKTEST_TIMEFRAME_MODE", "standard")
COMPARE_TIMEFRAME_MODES = ""
PARTIAL_TAKE_PROFIT_ENABLED = os.getenv("V2_BACKTEST_PARTIAL_TAKE_PROFIT", "0").lower() in {"1", "true", "yes", "on"}
PARTIAL_TAKE_PROFIT_R = float(os.getenv("V2_BACKTEST_PARTIAL_TAKE_PROFIT_R", "1.0"))
PARTIAL_TAKE_PROFIT_RATIO = float(os.getenv("V2_BACKTEST_PARTIAL_TAKE_PROFIT_RATIO", "0.5"))

EXIT_MODE_CONFIGS = {
    "fixed_original": {
        "label": "A_fixed_original_sl_1_5_tp_3_0",
        "stop_loss_pct": 1.5,
        "take_profit_pct": 3.0,
        "ema21_trailing": False,
    },
    "ma_no_tp": {
        "label": "B_ma_exit_sl_2_0_no_tp",
        "stop_loss_pct": 2.0,
        "take_profit_pct": None,
        "ema21_trailing": False,
    },
    "ma_wide_tp": {
        "label": "C_ma_exit_sl_2_0_tp_6_0",
        "stop_loss_pct": 2.0,
        "take_profit_pct": 6.0,
        "ema21_trailing": False,
    },
    "ma_trailing_ema21": {
        "label": "D_ma_exit_sl_2_0_no_tp_ema21_trailing",
        "stop_loss_pct": 2.0,
        "take_profit_pct": None,
        "ema21_trailing": True,
    },
}

TIMEFRAME_MODE_CONFIGS = {
    "standard": {
        "label": "current_5m_15m_1h",
        "base_interval": "5m",
        "reference_interval": "5m",
        "protective_interval": "5m",
        "strategy_interval_map": {"5m": "5m", "15m": "15m", "1h": "1h"},
    },
    "fast_stack": {
        "label": "experimental_1m_5m_15m",
        "base_interval": "1m",
        "reference_interval": "1m",
        "protective_interval": "1m",
        "strategy_interval_map": {"5m": "1m", "15m": "5m", "1h": "15m"},
    },
    "one_min_trigger": {
        "label": "compromise_1m_trigger_5m_1h_filter",
        "base_interval": "1m",
        "reference_interval": "1m",
        "protective_interval": "1m",
        "strategy_interval_map": {"5m": "1m", "15m": "5m", "1h": "1h"},
    },
}


def load_strategy_module():
    spec = importlib.util.spec_from_file_location("strategy_v2_module", SOURCE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def floor_time_to_five_minutes(dt: datetime) -> datetime:
    minute = (dt.minute // 5) * 5
    return dt.replace(minute=minute, second=0, microsecond=0)


def interval_to_milliseconds(interval: str) -> int:
    if interval.endswith("m"):
        return int(interval[:-1]) * 60_000
    if interval.endswith("h"):
        return int(interval[:-1]) * 60 * 60_000
    raise ValueError(f"Unsupported interval: {interval}")


def fetch_klines(symbol: str, interval: str, start_time_ms: int, end_time_ms: int) -> list[list]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{symbol}_{interval}_{YEARS}y.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    all_rows: list[list] = []
    current_start = start_time_ms
    session = requests.Session()
    while current_start < end_time_ms:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "endTime": end_time_ms,
            "limit": 1500,
        }
        response = None
        for retry_index in range(8):
            response = session.get(f"{PUBLIC_BASE_URL}/fapi/v1/klines", params=params, timeout=30)
            if response.status_code == 200:
                break
            if response.status_code in {429, 418, 500, 502, 503, 504}:
                sleep_seconds = min(60, 2 ** retry_index)
                time.sleep(sleep_seconds)
                continue
            response.raise_for_status()
        assert response is not None
        response.raise_for_status()
        rows = response.json()
        if not rows:
            break
        all_rows.extend(rows)
        last_open_time = int(rows[-1][0])
        next_open_time = last_open_time + interval_to_milliseconds(interval)
        if next_open_time <= current_start:
            break
        current_start = next_open_time
        time.sleep(0.12)
    cache_path.write_text(json.dumps(all_rows), encoding="utf-8")
    return all_rows


def aggregate_bars(rows_5m: list[list], factor: int) -> list[list]:
    aggregated: list[list] = []
    chunk: list[list] = []
    for row in rows_5m:
        chunk.append(row)
        if len(chunk) < factor:
            continue
        open_time = int(chunk[0][0])
        close_time = int(chunk[-1][6])
        open_price = str(chunk[0][1])
        high_price = str(max(float(item[2]) for item in chunk))
        low_price = str(min(float(item[3]) for item in chunk))
        close_price = str(chunk[-1][4])
        volume = str(sum(float(item[5]) for item in chunk))
        aggregated.append([
            open_time,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            close_time,
        ])
        chunk = []
    return aggregated


class BacktestEngine:
    def __init__(self, strategy_module, exit_mode: str = EXIT_MODE, timeframe_mode: str = TIMEFRAME_MODE):
        if exit_mode not in EXIT_MODE_CONFIGS:
            raise ValueError(f"Unsupported exit mode: {exit_mode}")
        if timeframe_mode not in TIMEFRAME_MODE_CONFIGS:
            raise ValueError(f"Unsupported timeframe mode: {timeframe_mode}")
        self.strategy_module = strategy_module
        self.exit_mode = exit_mode
        self.exit_config = EXIT_MODE_CONFIGS[exit_mode]
        self.timeframe_mode = timeframe_mode
        self.timeframe_config = TIMEFRAME_MODE_CONFIGS[timeframe_mode]
        self.strategy_interval_map = self.timeframe_config["strategy_interval_map"]
        base_cls = strategy_module.CompletelyFixedAutoStrategyFuturesTrading
        self.obj = object.__new__(base_cls)
        self._bind_methods(base_cls)
        self._init_state()

    def _bind_methods(self, base_cls):
        method_names = [
            "safe_float_conversion",
            "calculate_sma",
            "calculate_ema",
            "calculate_recent_fractals",
            "calculate_heikin_ashi",
            "analyze_heikin_ashi",
            "analyze_timeframe_ma",
            "analyze_market_regime",
            "get_ma_trade_decision",
            "should_exit_position_ma",
            "get_strategy_profile",
            "get_available_strategies",
            "generate_strategy_config",
            "generate_dynamic_strategies",
            "select_preferred_symbols",
            "calculate_market_volatility",
            "score_trade_candidate",
            "select_candidate_symbols",
            "get_session_policy",
            "get_dynamic_capital_per_strategy",
            "refresh_strategy_capital_allocations",
            "get_strategy_entries_today",
            "has_reached_daily_entry_limit",
            "generate_strategy_signal",
        ]
        for name in method_names:
            if hasattr(base_cls, name):
                setattr(self.obj, name, getattr(base_cls, name).__get__(self.obj, base_cls))
        self._install_compatibility_methods()

    def _install_compatibility_methods(self):
        """Install compatibility helpers for older strategy sources."""
        if not hasattr(self.obj, "get_market_session"):
            def get_market_session():
                current_time = getattr(self.obj, "backtest_current_time", datetime.now(timezone.utc))
                hour = current_time.hour
                if 19 <= hour < 21 or 22 <= hour < 24:
                    return "US_PEAK"
                if 16 <= hour < 18:
                    return "EU_PEAK"
                if 8 <= hour < 10:
                    return "ASIA_PEAK"
                if 2 <= hour < 7:
                    return "DEAD_ZONE"
                return "NORMAL"

            self.obj.get_market_session = get_market_session

        if not hasattr(self.obj, "get_session_policy"):
            def get_session_policy(session_name=None):
                session_name = session_name or self.obj.get_market_session()
                if session_name == "DEAD_ZONE":
                    return {"allow_new_entries": True, "position_size_multiplier": 0.5}
                return {"allow_new_entries": True, "position_size_multiplier": 1.0}

            self.obj.get_session_policy = get_session_policy

        if not hasattr(self.obj, "get_strategy_entries_today"):
            self.obj.get_strategy_entries_today = lambda strategy_name: 0

        if not hasattr(self.obj, "has_reached_daily_entry_limit"):
            self.obj.has_reached_daily_entry_limit = lambda strategy_name: False

    def _init_state(self):
        self.obj.running = False
        self.obj.dead_zone_entry_blocked = True
        self.obj.pullback_lookback_bars = 3
        self.obj.pullback_proximity_pct = 0.35 / 100.0
        self.obj.default_stop_loss_pct = float(self.exit_config["stop_loss_pct"])
        self.obj.default_take_profit_pct = float(self.exit_config["take_profit_pct"] or 0.0)
        self.obj.max_open_positions = 20
        self.obj.current_prices = {}
        self.obj.valid_symbols = list(BACKTEST_SYMBOLS)
        if hasattr(self.obj, "sideways_strategy_name"):
            if hasattr(self.obj, "create_sideways_engine"):
                self.obj.sideways_engine = self.obj.create_sideways_engine()
            else:
                self.obj.sideways_engine = self.strategy_module.SidewaysMarketStrategyV3()
            self.obj.sideways_min_confidence = getattr(self.obj, "sideways_min_confidence", 0.45)
            self.obj.sideways_signal_cache = {}
        self.obj.total_capital = INITIAL_CAPITAL
        self.obj.capital_per_strategy = self.obj.get_dynamic_capital_per_strategy()
        self.obj.trading_results = {
            "real_orders": [],
            "active_positions": {},
            "market_regime": "UNKNOWN",
            "available_balance": INITIAL_CAPITAL,
            "current_capital": INITIAL_CAPITAL,
            "total_pnl": 0.0,
            "market_session": "UNKNOWN",
        }
        self.obj.strategies = self.obj.generate_dynamic_strategies()
        self.obj.backtest_current_time = datetime.now(timezone.utc)
        self.data_1m: dict[str, list[list]] = {}
        self.data_5m: dict[str, list[list]] = {}
        self.data_15m: dict[str, list[list]] = {}
        self.data_1h: dict[str, list[list]] = {}
        self.index_1m = 0
        self.index_5m = 0
        self.index_15m = 0
        self.index_1h = 0
        self.position_entry_times = {}
        self.daily_entry_tracker: dict[str, int] = {}
        self.sideways_features: dict[str, object] = {}

        def get_market_session_override():
            hour = self.obj.backtest_current_time.hour
            if 19 <= hour < 21 or 22 <= hour < 24:
                return "US_PEAK"
            if 16 <= hour < 18:
                return "EU_PEAK"
            if 8 <= hour < 10:
                return "ASIA_PEAK"
            if 2 <= hour < 7:
                return "DEAD_ZONE"
            return "NORMAL"

        self.obj.get_market_session = get_market_session_override
        self.obj.log_system_error = lambda *args, **kwargs: None

        def get_klines_override(symbol, interval, limit):
            actual_interval = self.strategy_interval_map[interval]
            data_map = {"1m": self.data_1m, "5m": self.data_5m, "15m": self.data_15m, "1h": self.data_1h}
            index_map = {"1m": self.index_1m, "5m": self.index_5m, "15m": self.index_15m, "1h": self.index_1h}
            rows = data_map[actual_interval][symbol][: index_map[actual_interval] + 1]
            if not rows:
                return []
            # Add a synthetic forming bar so the original method can drop it.
            return rows[-limit:] + [rows[-1]]

        self.obj.get_klines = get_klines_override
        self.obj.get_current_price = lambda symbol, default=0.0: self.obj.current_prices.get(symbol, default)

        if hasattr(self.obj, "sideways_strategy_name"):
            def get_sideways_snapshot_override(symbol):
                features = self.sideways_features.get(symbol)
                if features is None or self.index_5m < 0 or self.index_5m >= len(features):
                    return None
                return features.iloc[self.index_5m].to_dict()

            self.obj.get_sideways_snapshot = get_sideways_snapshot_override

    def load_data(self):
        end_dt = floor_time_to_five_minutes(datetime.now(timezone.utc))
        start_dt = end_dt - timedelta(days=int(365 * YEARS))
        loaded_symbols = []
        requested_days = max(1, int(365 * YEARS))
        min_1m_history = min(5000, max(240, requested_days * 800))
        min_5m_history = min(1000, max(120, requested_days * 160))
        for symbol in BACKTEST_SYMBOLS:
            if self.timeframe_config["base_interval"] == "1m":
                rows_1m = fetch_klines(symbol, "1m", int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000))
                if len(rows_1m) < min_1m_history:
                    continue
                self.data_1m[symbol] = rows_1m
                self.data_5m[symbol] = aggregate_bars(rows_1m, 5)
                self.data_15m[symbol] = aggregate_bars(rows_1m, 15)
                self.data_1h[symbol] = aggregate_bars(rows_1m, 60)
            else:
                rows_5m = fetch_klines(symbol, "5m", int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000))
                if len(rows_5m) < min_5m_history:
                    continue
                self.data_5m[symbol] = rows_5m
                self.data_15m[symbol] = aggregate_bars(rows_5m, 3)
                self.data_1h[symbol] = aggregate_bars(rows_5m, 12)
            loaded_symbols.append(symbol)
            if hasattr(self.obj, "sideways_strategy_name"):
                frame = pd.DataFrame(
                    [
                        {
                            "open": float(row[1]),
                            "high": float(row[2]),
                            "low": float(row[3]),
                            "close": float(row[4]),
                            "volume": float(row[5]),
                        }
                        for row in self.data_5m[symbol]
                    ]
                )
                self.sideways_features[symbol] = self.obj.sideways_engine.prepare_features(frame)
        if not loaded_symbols:
            raise RuntimeError("No symbols had enough history for this backtest period")
        globals()["BACKTEST_SYMBOLS"] = loaded_symbols
        self.obj.valid_symbols = list(loaded_symbols)
        self.obj.strategies = self.obj.generate_dynamic_strategies()

    def _set_indexes_for_time(self, current_time_ms: int):
        if self.data_1m:
            self.index_1m = self._find_last_completed_index(self.data_1m[BACKTEST_SYMBOLS[0]], current_time_ms)
        if self.data_5m:
            self.index_5m = self._find_last_completed_index(self.data_5m[BACKTEST_SYMBOLS[0]], current_time_ms)
        if self.data_15m:
            self.index_15m = self._find_last_completed_index(self.data_15m[BACKTEST_SYMBOLS[0]], current_time_ms)
        if self.data_1h:
            self.index_1h = self._find_last_completed_index(self.data_1h[BACKTEST_SYMBOLS[0]], current_time_ms)

    @staticmethod
    def _find_last_completed_index(rows: list[list], current_time_ms: int) -> int:
        lo = 0
        hi = len(rows) - 1
        answer = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            close_time = int(rows[mid][6])
            if close_time <= current_time_ms:
                answer = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return answer

    def _current_bar(self, symbol: str) -> list:
        interval = self.timeframe_config["protective_interval"]
        data_map = {"1m": self.data_1m, "5m": self.data_5m, "15m": self.data_15m, "1h": self.data_1h}
        index_map = {"1m": self.index_1m, "5m": self.index_5m, "15m": self.index_15m, "1h": self.index_1h}
        return data_map[interval][symbol][index_map[interval]]

    def _register_entry(
        self,
        strategy_name: str,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
        current_dt: datetime,
        market_regime: dict | None = None,
    ):
        stop_loss_pct = float(self.exit_config["stop_loss_pct"]) / 100.0
        take_profit_value = self.exit_config["take_profit_pct"]
        take_profit_pct = (float(take_profit_value) / 100.0) if take_profit_value is not None else None
        session_policy = self.obj.get_session_policy(self.obj.get_market_session())
        stop_loss_pct *= self.obj.safe_float_conversion(session_policy.get("protective_stop_multiplier"), 1.0)
        if take_profit_pct is not None:
            take_profit_pct *= self.obj.safe_float_conversion(session_policy.get("protective_take_profit_multiplier"), 1.0)
        if side == "BUY":
            stop_price = price * (1 - stop_loss_pct)
            take_price = price * (1 + take_profit_pct) if take_profit_pct is not None else None
        else:
            stop_price = price * (1 + stop_loss_pct)
            take_price = price * (1 - take_profit_pct) if take_profit_pct is not None else None

        if hasattr(self.obj, "get_structural_stop_price") and strategy_name != getattr(self.obj, "sideways_strategy_name", ""):
            structural_stop = self.obj.get_structural_stop_price(side, price, market_regime)
            if structural_stop is not None:
                stop_price = float(structural_stop)

        partial_take_price = None
        if PARTIAL_TAKE_PROFIT_ENABLED and strategy_name != getattr(self.obj, "sideways_strategy_name", ""):
            risk_distance = abs(price - stop_price)
            if risk_distance > 0:
                if side == "BUY":
                    partial_take_price = price + risk_distance * PARTIAL_TAKE_PROFIT_R
                else:
                    partial_take_price = price - risk_distance * PARTIAL_TAKE_PROFIT_R

        notional = price * quantity
        fee = notional * FEE_RATE
        self.obj.total_capital -= fee
        self.obj.trading_results["available_balance"] = self.obj.total_capital
        self.obj.trading_results["current_capital"] = self.obj.total_capital
        self.obj.refresh_strategy_capital_allocations()
        self.position_entry_times[symbol] = current_dt.isoformat()
        self.daily_entry_tracker[f"{strategy_name}:{current_dt.date().isoformat()}"] = self.daily_entry_tracker.get(
            f"{strategy_name}:{current_dt.date().isoformat()}",
            0,
        ) + 1
        self.obj.trading_results["active_positions"][symbol] = {
            "amount": quantity if side == "BUY" else -quantity,
            "entry_price": price,
            "mark_price": price,
            "unrealized_pnl": 0.0,
            "percentage": 0.0,
            "entry_time": current_dt.isoformat(),
            "strategy_name": strategy_name,
            "stop_price": stop_price,
            "take_price": take_price,
            "partial_take_price": partial_take_price,
            "partial_take_ratio": PARTIAL_TAKE_PROFIT_RATIO,
            "partial_take_done": False,
            "entry_side": side,
            "exit_mode": self.exit_mode,
        }
        self.obj.trading_results["real_orders"].append({
            "strategy": strategy_name,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "status": "FILLED",
            "timestamp": current_dt.isoformat(),
            "type": "ACTUAL_TRADE",
            "market_session": self.obj.get_market_session(),
        })

    def _partial_close_position(self, symbol: str, exit_price: float, ratio: float, reason: str, current_dt: datetime):
        position = self.obj.trading_results["active_positions"].get(symbol)
        if not position:
            return False
        amount = float(position["amount"])
        quantity = abs(amount) * max(0.0, min(1.0, ratio))
        if quantity <= 0:
            return False

        entry_price = float(position["entry_price"])
        side = "SELL" if amount > 0 else "BUY"
        gross_pnl = (exit_price - entry_price) * quantity * (1 if amount > 0 else -1)
        fee = exit_price * quantity * FEE_RATE
        net_pnl = gross_pnl - fee
        self.obj.total_capital += net_pnl
        remaining_quantity = abs(amount) - quantity
        position["amount"] = remaining_quantity if amount > 0 else -remaining_quantity
        position["partial_take_done"] = True
        self.obj.trading_results["current_capital"] = self.obj.total_capital
        self.obj.trading_results["available_balance"] = self.obj.total_capital
        self.obj.trading_results["total_pnl"] = self.obj.total_capital - INITIAL_CAPITAL
        self.obj.refresh_strategy_capital_allocations()
        self.obj.trading_results["real_orders"].append({
            "strategy": "position_manager",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": exit_price,
            "status": "FILLED",
            "timestamp": current_dt.isoformat(),
            "type": "ACTUAL_TRADE",
            "reduce_only": True,
            "entry_price": entry_price,
            "realized_pnl": net_pnl,
            "close_reason": reason,
            "market_session": self.obj.get_market_session(),
            "partial_exit": True,
        })
        if remaining_quantity <= 1e-12:
            self.obj.trading_results["active_positions"].pop(symbol, None)
        return True

    def _close_position(self, symbol: str, exit_price: float, reason: str, current_dt: datetime):
        position = self.obj.trading_results["active_positions"].pop(symbol, None)
        if not position:
            return
        amount = float(position["amount"])
        quantity = abs(amount)
        entry_price = float(position["entry_price"])
        side = "SELL" if amount > 0 else "BUY"
        gross_pnl = (exit_price - entry_price) * quantity * (1 if amount > 0 else -1)
        fee = exit_price * quantity * FEE_RATE
        net_pnl = gross_pnl - fee
        self.obj.total_capital += net_pnl
        self.obj.trading_results["current_capital"] = self.obj.total_capital
        self.obj.trading_results["available_balance"] = self.obj.total_capital
        self.obj.trading_results["total_pnl"] = self.obj.total_capital - INITIAL_CAPITAL
        self.obj.refresh_strategy_capital_allocations()
        self.obj.trading_results["real_orders"].append({
            "strategy": "position_manager",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": exit_price,
            "status": "FILLED",
            "timestamp": current_dt.isoformat(),
            "type": "ACTUAL_TRADE",
            "reduce_only": True,
            "entry_price": entry_price,
            "realized_pnl": net_pnl,
            "close_reason": reason,
            "market_session": self.obj.get_market_session(),
        })

    def _update_mark_to_market(self):
        total_unrealized = 0.0
        for symbol, position in self.obj.trading_results["active_positions"].items():
            current_price = self.obj.current_prices[symbol]
            entry_price = float(position["entry_price"])
            amount = float(position["amount"])
            direction = 1 if amount > 0 else -1
            unrealized = (current_price - entry_price) * abs(amount) * direction
            pct = ((current_price - entry_price) / entry_price) * 100 * direction if entry_price > 0 else 0.0
            position["mark_price"] = current_price
            position["unrealized_pnl"] = unrealized
            position["percentage"] = pct
            total_unrealized += unrealized
        self.obj.trading_results["current_capital"] = self.obj.total_capital + total_unrealized
        self.obj.trading_results["total_pnl"] = self.obj.trading_results["current_capital"] - INITIAL_CAPITAL

    def _check_protective_exit(self, symbol: str, current_dt: datetime):
        position = self.obj.trading_results["active_positions"].get(symbol)
        if not position:
            return False
        bar = self._current_bar(symbol)
        high_price = float(bar[2])
        low_price = float(bar[3])
        stop_price = float(position["stop_price"])
        take_price = float(position["take_price"]) if position.get("take_price") is not None else None
        partial_take_price = float(position["partial_take_price"]) if position.get("partial_take_price") is not None else None
        amount = float(position["amount"])

        if amount > 0:
            if low_price <= stop_price:
                self._close_position(symbol, stop_price, "protective_stop", current_dt)
                return True
            if (
                PARTIAL_TAKE_PROFIT_ENABLED and
                partial_take_price is not None and
                not bool(position.get("partial_take_done", False)) and
                high_price >= partial_take_price
            ):
                self._partial_close_position(
                    symbol,
                    partial_take_price,
                    float(position.get("partial_take_ratio", PARTIAL_TAKE_PROFIT_RATIO)),
                    "partial_take_profit_1r",
                    current_dt,
                )
            if take_price is not None and high_price >= take_price:
                self._close_position(symbol, take_price, "protective_take_profit", current_dt)
                return True
        else:
            if high_price >= stop_price:
                self._close_position(symbol, stop_price, "protective_stop", current_dt)
                return True
            if (
                PARTIAL_TAKE_PROFIT_ENABLED and
                partial_take_price is not None and
                not bool(position.get("partial_take_done", False)) and
                low_price <= partial_take_price
            ):
                self._partial_close_position(
                    symbol,
                    partial_take_price,
                    float(position.get("partial_take_ratio", PARTIAL_TAKE_PROFIT_RATIO)),
                    "partial_take_profit_1r",
                    current_dt,
                )
            if take_price is not None and low_price <= take_price:
                self._close_position(symbol, take_price, "protective_take_profit", current_dt)
                return True
        return False

    def _check_exit_mode_ma_trailing(self, symbol: str, market_regime: dict, current_dt: datetime) -> bool:
        if not self.exit_config.get("ema21_trailing"):
            return False
        position = self.obj.trading_results["active_positions"].get(symbol)
        if not position:
            return False
        amount = float(position["amount"])
        entry_price = float(position["entry_price"])
        current_price = self.obj.current_prices[symbol]
        unrealized = (current_price - entry_price) * abs(amount) * (1 if amount > 0 else -1)
        if unrealized <= 0:
            return False
        tf_5m = market_regime.get("timeframes", {}).get("5m", {})
        ema_mid = float(tf_5m.get("ema_mid") or 0.0)
        if ema_mid <= 0:
            return False
        if amount > 0 and current_price < ema_mid:
            self._close_position(symbol, current_price, "ema21_trailing_exit", current_dt)
            return True
        if amount < 0 and current_price > ema_mid:
            self._close_position(symbol, current_price, "ema21_trailing_exit", current_dt)
            return True
        return False

    def _strategy_entries_today(self, strategy_name: str, current_dt: datetime) -> int:
        return self.daily_entry_tracker.get(f"{strategy_name}:{current_dt.date().isoformat()}", 0)

    def _calculate_position_size(self, strategy_name: str, symbol: str) -> float:
        strategy = self.obj.strategies[strategy_name]
        capital = strategy["capital"]
        risk_per_trade = strategy["risk_per_trade"]
        leverage = strategy["leverage"]
        session_policy = self.obj.get_session_policy(self.obj.get_market_session())
        multiplier = float(session_policy.get("position_size_multiplier", 1.0))
        position_value = capital * risk_per_trade * leverage * multiplier
        current_price = self.obj.current_prices[symbol]
        if current_price <= 0:
            return 0.0
        return position_value / current_price

    def run(self):
        reference_interval = self.timeframe_config["reference_interval"]
        data_map = {"1m": self.data_1m, "5m": self.data_5m, "15m": self.data_15m, "1h": self.data_1h}
        index_map = {"1m": "index_1m", "5m": "index_5m", "15m": "index_15m", "1h": "index_1h"}
        rows_reference = data_map[reference_interval][BACKTEST_SYMBOLS[0]]
        interval_minutes = interval_to_milliseconds(reference_interval) // 60_000
        first_index = max(1, int(60 * 60 / interval_minutes))  # enough bars for all indicators and aggregations
        for idx in range(first_index, len(rows_reference), EVALUATION_STEP_BARS):
            current_close_time_ms = int(rows_reference[idx][6])
            current_dt = datetime.fromtimestamp(current_close_time_ms / 1000, tz=timezone.utc)
            self.obj.backtest_current_time = current_dt
            self.obj.trading_results["market_session"] = self.obj.get_market_session()
            self._set_indexes_for_time(current_close_time_ms)

            for symbol in BACKTEST_SYMBOLS:
                self.obj.current_prices[symbol] = float(data_map[reference_interval][symbol][getattr(self, index_map[reference_interval])][4])

            for symbol in list(self.obj.trading_results["active_positions"].keys()):
                self._check_protective_exit(symbol, current_dt)

            self._update_mark_to_market()

            regime_cache = {}
            active_positions = self.obj.trading_results["active_positions"]
            for symbol in BACKTEST_SYMBOLS:
                regime_cache[symbol] = self.obj.analyze_market_regime(symbol)

            for symbol, position in list(active_positions.items()):
                if self._check_exit_mode_ma_trailing(symbol, regime_cache[symbol], current_dt):
                    continue
                strategy = self.obj.strategies.get(position.get("strategy_name"))
                exit_reason = self.obj.should_exit_position_ma(position, regime_cache[symbol], strategy)
                if exit_reason:
                    self._close_position(symbol, self.obj.current_prices[symbol], exit_reason, current_dt)

            active_positions = self.obj.trading_results["active_positions"]
            if len(active_positions) >= self.obj.max_open_positions:
                continue

            for strategy_name, strategy in self.obj.strategies.items():
                if self._strategy_entries_today(strategy_name, current_dt) >= int(strategy.get("daily_entry_limit", 5)):
                    continue
                if not self.obj.get_session_policy(self.obj.get_market_session()).get("allow_new_entries", True):
                    continue

                available_symbols = [s for s in strategy["preferred_symbols"] if s in BACKTEST_SYMBOLS and s not in active_positions]
                if not available_symbols:
                    continue

                candidate_evaluations = []
                for symbol in self.obj.select_candidate_symbols(available_symbols, int(strategy.get("candidate_limit", 5))):
                    signal = self.obj.generate_strategy_signal(strategy_name, regime_cache[symbol], symbol)
                    if not signal:
                        continue
                    candidate_evaluations.append({
                        "symbol": symbol,
                        "signal": signal,
                        "score": self.obj.score_trade_candidate(regime_cache[symbol]),
                    })

                if not candidate_evaluations:
                    continue

                best_candidate = max(candidate_evaluations, key=lambda item: item["score"])
                symbol = best_candidate["symbol"]
                quantity = self._calculate_position_size(strategy_name, symbol)
                if quantity <= 0:
                    continue
                self._register_entry(
                    strategy_name,
                    symbol,
                    best_candidate["signal"],
                    self.obj.current_prices[symbol],
                    quantity,
                    current_dt,
                    regime_cache[symbol],
                )
                active_positions = self.obj.trading_results["active_positions"]
                if len(active_positions) >= self.obj.max_open_positions:
                    break

        final_dt = datetime.fromtimestamp(int(rows_reference[-1][6]) / 1000, tz=timezone.utc)
        for symbol in list(self.obj.trading_results["active_positions"].keys()):
            self._close_position(symbol, self.obj.current_prices[symbol], "end_of_backtest", final_dt)

        self._update_mark_to_market()
        return self._build_summary(final_dt)

    def _build_summary(self, final_dt: datetime) -> dict:
        order_count = len(self.obj.trading_results["real_orders"])
        entry_orders = [o for o in self.obj.trading_results["real_orders"] if not o.get("reduce_only")]
        exit_orders = [o for o in self.obj.trading_results["real_orders"] if o.get("reduce_only")]
        partial_exit_orders = [o for o in exit_orders if o.get("partial_exit")]
        winning_exits = [o for o in exit_orders if float(o.get("realized_pnl", 0.0)) > 0]
        losing_exits = [o for o in exit_orders if float(o.get("realized_pnl", 0.0)) < 0]
        session_counts = defaultdict(int)
        entry_strategy_counts = defaultdict(int)
        exit_reason_counts = defaultdict(int)
        for order in entry_orders:
            session_counts[order.get("market_session", "UNKNOWN")] += 1
            entry_strategy_counts[order.get("strategy", "UNKNOWN")] += 1
        for order in exit_orders:
            exit_reason_counts[order.get("close_reason", "UNKNOWN")] += 1

        return {
            "source": str(SOURCE_PATH),
            "exit_mode": self.exit_mode,
            "exit_mode_label": self.exit_config["label"],
            "timeframe_mode": self.timeframe_mode,
            "timeframe_mode_label": self.timeframe_config["label"],
            "strategy_interval_map": self.strategy_interval_map,
            "symbols": BACKTEST_SYMBOLS,
            "years": YEARS,
            "evaluation_step_bars": EVALUATION_STEP_BARS,
            "start_capital": INITIAL_CAPITAL,
            "end_capital": self.obj.total_capital,
            "net_pnl": self.obj.total_capital - INITIAL_CAPITAL,
            "entry_orders": len(entry_orders),
            "exit_orders": len(exit_orders),
            "partial_exit_orders": len(partial_exit_orders),
            "winning_exits": len(winning_exits),
            "losing_exits": len(losing_exits),
            "win_rate": (len(winning_exits) / len(exit_orders) * 100.0) if exit_orders else 0.0,
            "session_entry_counts": dict(session_counts),
            "entry_strategy_counts": dict(entry_strategy_counts),
            "exit_reason_counts": dict(exit_reason_counts),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "backtest_end_time": final_dt.isoformat(),
            "recent_orders": self.obj.trading_results["real_orders"][-25:],
            "total_order_records": order_count,
        }


def main():
    print("Running v2 five-year backtest without touching the live process.")
    module = load_strategy_module()
    if COMPARE_TIMEFRAME_MODES:
        modes = [mode.strip() for mode in COMPARE_TIMEFRAME_MODES.split(",") if mode.strip()]
        results = []
        for mode in modes:
            print(f"Running timeframe mode: {mode}")
            engine = BacktestEngine(module, EXIT_MODE, mode)
            engine.load_data()
            results.append(engine.run())
        comparison = {
            "source": str(SOURCE_PATH),
            "symbols": BACKTEST_SYMBOLS,
            "years": YEARS,
            "evaluation_step_bars": EVALUATION_STEP_BARS,
            "exit_mode": EXIT_MODE,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }
        OUTPUT_PATH.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
        print(json.dumps(comparison, indent=2))
    elif COMPARE_EXIT_MODES:
        modes = [mode.strip() for mode in COMPARE_EXIT_MODES.split(",") if mode.strip()]
        results = []
        for mode in modes:
            print(f"Running exit mode: {mode}")
            engine = BacktestEngine(module, mode, TIMEFRAME_MODE)
            engine.load_data()
            results.append(engine.run())
        comparison = {
            "source": str(SOURCE_PATH),
            "symbols": BACKTEST_SYMBOLS,
            "years": YEARS,
            "evaluation_step_bars": EVALUATION_STEP_BARS,
            "timeframe_mode": TIMEFRAME_MODE,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }
        OUTPUT_PATH.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
        print(json.dumps(comparison, indent=2))
    else:
        engine = BacktestEngine(module, EXIT_MODE, TIMEFRAME_MODE)
        engine.load_data()
        results = engine.run()
        OUTPUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(results, indent=2))
    print(f"Saved backtest report to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
