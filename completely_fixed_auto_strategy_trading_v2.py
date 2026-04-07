#!/usr/bin/env python3
"""
Auto futures trading system with improved error reporting and handling.
"""

import json
import time
from datetime import datetime, timedelta, timezone
import sys
import os
import threading
import requests
import hmac
import hashlib
import urllib.parse
import traceback
from decimal import Decimal, ROUND_DOWN, ROUND_UP

_builtin_print = print

def print(*args, **kwargs):
    """Safe print wrapper that tolerates console encoding issues on Windows."""
    try:
        _builtin_print(*args, **kwargs)
    except UnicodeEncodeError:
        file = kwargs.get("file", sys.stdout)
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        flush = kwargs.get("flush", False)
        encoding = getattr(file, "encoding", None) or "utf-8"
        text = sep.join(str(arg) for arg in args)
        sanitized = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        _builtin_print(sanitized, end=end, file=file, flush=flush)

def configure_console_output():
    """Reconfigure stdout/stderr to UTF-8 when supported."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

configure_console_output()

class CompletelyFixedAutoStrategyFuturesTrading:
    def __init__(self):
        self.load_local_env_file()
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=24)
        self.test_duration = 24 * 60 * 60
        self.max_open_positions = 20
        self.default_stop_loss_pct = 2.0
        self.default_take_profit_pct = 0.0
        self.symbol_refresh_interval_sec = int(self.safe_float_conversion(os.getenv("SYMBOL_REFRESH_INTERVAL_SEC"), 3600))
        self.max_ranked_symbols = int(self.safe_float_conversion(os.getenv("MAX_RANKED_SYMBOLS"), 20))
        self.min_hold_seconds = int(self.safe_float_conversion(os.getenv("MIN_HOLD_SECONDS"), 180))
        self.reentry_cooldown_seconds = int(self.safe_float_conversion(os.getenv("REENTRY_COOLDOWN_SECONDS"), 900))
        self.dead_zone_entry_blocked = os.getenv("DEAD_ZONE_ENTRY_BLOCKED", "true").lower() == "true"
        self.pullback_lookback_bars = int(self.safe_float_conversion(os.getenv("PULLBACK_LOOKBACK_BARS"), 3))
        self.pullback_proximity_pct = self.safe_float_conversion(os.getenv("PULLBACK_PROXIMITY_PCT"), 0.35) / 100.0
        self.last_symbol_refresh = None
        self.running = True
        self.system_errors = []
        self.symbol_info_cache = {}
        self.account_info_cache = {}
        self.account_data_available = True
        self.position_entry_times = {}
        self.recently_closed_symbols = {}
        self.signal_diagnostic_log_interval_sec = int(
            self.safe_float_conversion(os.getenv("SIGNAL_DIAGNOSTIC_LOG_INTERVAL_SEC"), 300)
        )
        self.last_signal_diagnostic_log = {}
        self.trading_results = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "strategy_performance": {},
            "market_data": {},
            "total_pnl": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "pending_trades": 0,
            "closed_trades": 0,
            "entry_failures": 0,
            "real_orders": [],
            "balance_history": [],
            "initial_capital": 0.0,
            "current_capital": 0.0,
            "available_balance": 0.0,
            "active_positions": {},
            "market_regime": "UNKNOWN",
            "market_session": "UNKNOWN",
            "sync_status": "INITIALIZED",
            "symbol_universe_updated_at": None,
            "system_errors": [],
            "error_count": 0,
            "last_error": None
        }
        self.api_key, self.api_secret = self.resolve_exchange_credentials()
        self.base_url = self.resolve_base_url()
        self.total_capital = self.get_account_balance()
        self.capital_per_strategy = self.get_dynamic_capital_per_strategy()
        self.valid_symbols = self.get_available_symbols()
        self.current_prices = self.get_current_prices()
        self.strategies = self.generate_dynamic_strategies()
        self.refresh_symbol_universe(force=True)

        self.trading_results["initial_capital"] = self.total_capital
        self.trading_results["current_capital"] = self.total_capital
        self.sync_thread = threading.Thread(target=self.periodic_sync, daemon=True)
        self.sync_thread.start()

        print("[INFO] Auto futures trading started")
        print(f"[INFO] Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[INFO] Initial capital: ${self.total_capital:,.2f}")
        print(f"[INFO] Strategy count: {len(self.strategies)}")
        print(f"[INFO] Symbol count: {len(self.valid_symbols)}")
        print("[INFO] Real-time sync: enabled")
        print("[INFO] Error reporting: enabled")
        print("=" * 80)

    def load_local_env_file(self, env_path=".env"):
        """Load a simple local .env file into process environment if present."""
        if not os.path.exists(env_path):
            return
        try:
            with open(env_path, "r", encoding="utf-8-sig") as env_file:
                for raw_line in env_file:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip().lstrip("\ufeff")
                    value = value.strip().strip('"').strip("'")
                    if key and not os.getenv(key, "").strip():
                        os.environ[key] = value
        except Exception:
            pass

    def resolve_exchange_credentials(self):
        """Resolve exchange credentials using the workspace's preferred env names."""
        key_candidates = [
            "BINANCE_TESTNET_TRADING_API_KEY",
            "BINANCE_TESTNET_ACCOUNT_API_KEY",
            "BINANCE_TESTNET_API_KEY",
            "BINANCE_TESTNET_KEY",
            "BINANCE_API_KEY",
        ]
        secret_candidates = [
            "BINANCE_TESTNET_TRADING_API_SECRET",
            "BINANCE_TESTNET_ACCOUNT_API_SECRET",
            "BINANCE_TESTNET_API_SECRET",
            "BINANCE_TESTNET_SECRET",
            "BINANCE_API_SECRET",
        ]

        api_key = ""
        api_secret = ""
        for env_name in key_candidates:
            value = os.getenv(env_name, "").strip()
            if value:
                api_key = value
                break
        for env_name in secret_candidates:
            value = os.getenv(env_name, "").strip()
            if value:
                api_secret = value
                break
        return api_key, api_secret

    def resolve_base_url(self):
        """Resolve the Binance futures base URL from environment or fallback defaults."""
        base_candidates = [
            "BINANCE_TESTNET_URL",
            "BINANCE_FUTURES_TESTNET_BASE_URL",
            "BINANCE_TESTNET_BASE_URL",
            "BINANCE_BASE_URL",
        ]
        for env_name in base_candidates:
            value = os.getenv(env_name, "").strip()
            if value:
                return value.rstrip("/")
        return "https://demo-fapi.binance.com"

    def get_server_time(self):
        """Fetch Binance server time."""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                return response.json()["serverTime"]
            else:
                return int(time.time() * 1000)
        except:
            return int(time.time() * 1000)

    def get_account_info(self):
        """Return futures account info from Binance."""
        try:
            if not self.api_key or not self.api_secret:
                self.account_data_available = False
                self.log_system_error("account_info_error", "BINANCE_TESTNET_KEY or BINANCE_TESTNET_SECRET is missing")
                return None

            server_time = self.get_server_time()
            params = {
                "timestamp": server_time,
                "recvWindow": 5000
            }

            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            url = f"{self.base_url}/fapi/v2/account?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()

            self.log_system_error(f"account_info_failed: {response.status_code}", response.text)
            return None
        except Exception as e:
            self.log_system_error("account_info_error", str(e))
            return None

    def get_account_balance(self):
        """Fetch the current futures wallet balance."""
        try:
            account_info = self.get_account_info()
            if account_info:
                balance = float(account_info['totalWalletBalance'])
                self.account_data_available = True
                print(f"[INFO] Wallet balance: ${balance:,.2f}")
                return balance
            else:
                print("[WARN] Account info unavailable; using fallback balance")
                self.account_data_available = False
                return self.safe_float_conversion(getattr(self, "total_capital", 0.0), 0.0)
        except Exception as e:
            self.log_system_error("account_balance_error", str(e))
            self.account_data_available = False
            return self.safe_float_conversion(getattr(self, "total_capital", 0.0), 0.0)

    def get_available_symbols(self):
        """Fetch ranked tradable symbols using liquidity and volatility."""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            ticker_response = requests.get(f"{self.base_url}/fapi/v1/ticker/24hr", timeout=10)

            if response.status_code == 200 and ticker_response.status_code == 200:
                exchange_info = response.json()
                ticker_24hr = ticker_response.json()

                tradable_symbols = set()
                for symbol_info in exchange_info["symbols"]:
                    if (
                        symbol_info["status"] == "TRADING" and
                        symbol_info["contractType"] == "PERPETUAL" and
                        symbol_info["symbol"].endswith("USDT") and
                        symbol_info["symbol"].isascii() and
                        symbol_info["symbol"].replace("USDT", "").isalnum()
                    ):
                        tradable_symbols.add(symbol_info["symbol"])

                ranked = []
                for ticker in ticker_24hr:
                    symbol = ticker.get("symbol")
                    if symbol not in tradable_symbols:
                        continue

                    quote_volume = self.safe_float_conversion(ticker.get("quoteVolume"), 0.0)
                    price_change_pct = abs(self.safe_float_conversion(ticker.get("priceChangePercent"), 0.0))
                    count = self.safe_float_conversion(ticker.get("count"), 0.0)
                    score = ((quote_volume ** 0.5) * 100.0) + (price_change_pct * 50.0) + (count * 0.05)
                    ranked.append((score, symbol, quote_volume, price_change_pct))

                ranked.sort(key=lambda item: item[0], reverse=True)
                selected = [item[1] for item in ranked[:self.max_ranked_symbols]]

                print(f"[INFO] Tradable symbols: {len(tradable_symbols)}")
                print(f"[INFO] Ranked symbols selected: {len(selected)}")
                return selected if selected else ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

            error_text = f"exchange={response.status_code}, ticker24hr={ticker_response.status_code}"
            self.log_system_error("symbol_rank_fetch_failed", error_text)
            return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        except Exception as e:
            self.log_system_error("symbol_fetch_error", str(e))
            return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    def get_current_prices(self):
        """Fetch current prices for the active symbol universe."""
        prices = {}

        try:
            for symbol in self.valid_symbols[:10]:
                response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
                if response.status_code == 200:
                    price_data = response.json()
                    prices[symbol] = float(price_data["price"])

            print(f"[INFO] Market prices cached: {len(prices)} symbols")
            return prices
        except Exception as e:
            self.log_system_error("market_price_error", str(e))
            return {}

    def get_current_price(self, symbol, default=0.0):
        """Fetch the latest price for one symbol and refresh the local cache."""
        cached_price = self.safe_float_conversion(self.current_prices.get(symbol), None) if hasattr(self, "current_prices") else None
        if cached_price is not None and cached_price > 0:
            return cached_price

        try:
            response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
            if response.status_code == 200:
                price_data = response.json()
                price = self.safe_float_conversion(price_data.get("price"), default)
                if not hasattr(self, "current_prices"):
                    self.current_prices = {}
                self.current_prices[symbol] = price
                return price
        except Exception as e:
            self.log_system_error("price_lookup_error", f"{symbol}: {e}")

        return default

    def refresh_symbol_universe(self, force=False):
        """Refresh the symbol universe and strategy symbol preferences."""
        now = datetime.now()
        if (
            not force and
            self.last_symbol_refresh and
            (now - self.last_symbol_refresh).total_seconds() < self.symbol_refresh_interval_sec
        ):
            return

        try:
            previous_symbols = set(getattr(self, "valid_symbols", []))
            self.valid_symbols = self.get_available_symbols()
            self.current_prices = self.get_current_prices()

            if hasattr(self, "strategies") and self.strategies:
                self.refresh_strategy_capital_allocations()
                for strategy_name, strategy in self.strategies.items():
                    strategy["preferred_symbols"] = self.select_preferred_symbols(strategy["strategy_type"])
                    strategy["updated_at"] = now.isoformat()

            self.last_symbol_refresh = now
            self.trading_results["symbol_universe_updated_at"] = now.isoformat()
            changed = len(set(self.valid_symbols) ^ previous_symbols)
            print(f"[INFO] Symbol universe refreshed | count={len(self.valid_symbols)} | changed={changed}")
        except Exception as e:
            self.log_system_error("symbol_universe_refresh_error", str(e))

    def get_available_strategies(self):
        """Return the list of supported strategy types."""
        base_strategies = [
            "momentum_strategy",
            "pullback_confirmation_strategy",
            "moving_average_strategy",
            "volatility_strategy",
            "trend_following_strategy",
            "balanced_rotation_strategy"
        ]
        return base_strategies

    def get_dynamic_capital_per_strategy(self):
        """Return current capital allocated per strategy."""
        strategy_count = max(1, len(self.get_available_strategies()))
        return self.safe_float_conversion(self.total_capital, 0.0) / strategy_count

    def refresh_strategy_capital_allocations(self):
        """Refresh per-strategy capital after balance changes."""
        self.capital_per_strategy = self.get_dynamic_capital_per_strategy()
        for strategy in getattr(self, "strategies", {}).values():
            strategy["capital"] = self.capital_per_strategy

    def get_market_session(self):
        """Classify the current UTC session for liquidity-aware behavior."""
        hour = datetime.now(timezone.utc).hour
        if 19 <= hour < 21 or 22 <= hour < 24:
            return "US_PEAK"
        if 16 <= hour < 18:
            return "EU_PEAK"
        if 8 <= hour < 10:
            return "ASIA_PEAK"
        if 2 <= hour < 7:
            return "DEAD_ZONE"
        return "NORMAL"

    def get_session_policy(self, session_name):
        """Return session-specific entry and sizing rules."""
        policies = {
            "US_PEAK": {
                "allow_new_entries": True,
                "position_size_multiplier": 1.2,
                "consensus_adjustment": 0,
                "protective_stop_multiplier": 1.15,
                "protective_take_profit_multiplier": 1.2,
            },
            "EU_PEAK": {
                "allow_new_entries": True,
                "position_size_multiplier": 1.0,
                "consensus_adjustment": 0,
                "protective_stop_multiplier": 1.0,
                "protective_take_profit_multiplier": 1.0,
            },
            "ASIA_PEAK": {
                "allow_new_entries": True,
                "position_size_multiplier": 1.0,
                "consensus_adjustment": 0,
                "protective_stop_multiplier": 1.0,
                "protective_take_profit_multiplier": 1.0,
            },
            "DEAD_ZONE": {
                "allow_new_entries": not self.dead_zone_entry_blocked,
                "position_size_multiplier": 0.5,
                "consensus_adjustment": 1,
                "protective_stop_multiplier": 0.95,
                "protective_take_profit_multiplier": 0.9,
            },
            "NORMAL": {
                "allow_new_entries": True,
                "position_size_multiplier": 0.85,
                "consensus_adjustment": 0,
                "protective_stop_multiplier": 1.0,
                "protective_take_profit_multiplier": 1.0,
            },
        }
        return policies.get(session_name, policies["NORMAL"])

    def get_strategy_profile(self, strategy_name):
        """Deterministic EMA + Heikin Ashi + fractal strategy profiles."""
        profiles = {
            "momentum_strategy": {
                "leverage": 14.0,
                "risk_per_trade": 0.018,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "exit_signal_threshold": 3,
                "daily_entry_limit": 8,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": True,
                "require_strong_5m_ha": True,
                "fractal_intervals": ["5m"],
                "candidate_limit": 6,
                "symbol_mode": "leaders",
                "market_bias": "adaptive",
            },
            "pullback_confirmation_strategy": {
                "leverage": 8.0,
                "risk_per_trade": 0.012,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "exit_signal_threshold": 2,
                "daily_entry_limit": 6,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": True,
                "require_strong_5m_ha": False,
                "fractal_intervals": ["5m"],
                "candidate_limit": 8,
                "symbol_mode": "pullback",
                "market_bias": "adaptive",
            },
            "moving_average_strategy": {
                "leverage": 12.0,
                "risk_per_trade": 0.015,
                "required_alignment_count": 1,
                "consensus_threshold": 3,
                "exit_signal_threshold": 3,
                "daily_entry_limit": 5,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": True,
                "require_strong_5m_ha": False,
                "fractal_intervals": ["5m", "15m"],
                "candidate_limit": 5,
                "symbol_mode": "leaders",
                "market_bias": "adaptive",
            },
            "volatility_strategy": {
                "leverage": 10.0,
                "risk_per_trade": 0.010,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "exit_signal_threshold": 2,
                "daily_entry_limit": 7,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": True,
                "require_strong_5m_ha": False,
                "fractal_intervals": ["5m"],
                "candidate_limit": 8,
                "symbol_mode": "volatile",
                "market_bias": "adaptive",
            },
            "trend_following_strategy": {
                "leverage": 11.0,
                "risk_per_trade": 0.016,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "exit_signal_threshold": 3,
                "daily_entry_limit": 5,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": True,
                "require_strong_5m_ha": False,
                "fractal_intervals": ["15m"],
                "candidate_limit": 6,
                "symbol_mode": "leaders",
                "market_bias": "adaptive",
            },
            "balanced_rotation_strategy": {
                "leverage": 7.0,
                "risk_per_trade": 0.008,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "exit_signal_threshold": 2,
                "daily_entry_limit": 4,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": True,
                "require_strong_5m_ha": False,
                "fractal_intervals": ["5m", "15m"],
                "candidate_limit": 10,
                "symbol_mode": "balanced",
                "market_bias": "adaptive",
            },
        }
        return profiles.get(strategy_name, profiles["moving_average_strategy"])

    def generate_dynamic_strategies(self):
        """Build runtime strategy configurations."""
        strategies = {}
        self.refresh_strategy_capital_allocations()

        for i, strategy_name in enumerate(self.get_available_strategies()):
            strategy_config = self.generate_strategy_config(i, strategy_name)
            strategies[f"{strategy_name}_{i+1}"] = strategy_config

        print(f"[INFO] Dynamic strategies created: {len(strategies)}")
        return strategies

    def select_preferred_symbols(self, strategy_name):
        """Select preferred symbols for a strategy profile."""
        if not self.valid_symbols:
            return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

        candidates = list(self.valid_symbols)
        profile = self.get_strategy_profile(strategy_name)
        symbol_mode = profile.get("symbol_mode", "leaders")

        if symbol_mode == "leaders":
            return candidates[:min(8, len(candidates))]
        if symbol_mode == "volatile":
            return candidates[:min(12, len(candidates)):2] or candidates[:min(4, len(candidates))]
        if symbol_mode == "pullback":
            return candidates[min(3, len(candidates)):min(11, len(candidates))] or candidates[:min(6, len(candidates))]
        if symbol_mode == "balanced":
            merged = []
            for symbol in candidates[:min(5, len(candidates))] + candidates[-min(5, len(candidates)):]:
                if symbol not in merged:
                    merged.append(symbol)
            return merged
        return candidates[:min(6, len(candidates))]

    def generate_strategy_config(self, index, strategy_name):
        """Build a deterministic strategy config from the EMA/HA/fractal profile."""
        market_volatility = self.calculate_market_volatility()
        profile = self.get_strategy_profile(strategy_name)
        preferred_symbols = self.select_preferred_symbols(strategy_name)

        return {
            "leverage": profile["leverage"],
            "win_rate": 0.0,
            "avg_return": 0.0,
            "capital": self.capital_per_strategy,
            "risk_per_trade": profile["risk_per_trade"],
            "stop_loss": self.default_stop_loss_pct / 100.0,
            "take_profit": (self.default_take_profit_pct / 100.0) if self.default_take_profit_pct > 0 else None,
            "strategy_type": strategy_name,
            "preferred_symbols": preferred_symbols,
            "market_bias": profile["market_bias"],
            "created_at": datetime.now().isoformat(),
            "market_volatility": market_volatility,
            "required_alignment_count": profile["required_alignment_count"],
            "consensus_threshold": profile["consensus_threshold"],
            "exit_signal_threshold": profile["exit_signal_threshold"],
            "daily_entry_limit": profile["daily_entry_limit"],
            "require_volume_expansion": profile["require_volume_expansion"],
            "require_cross": profile["require_cross"],
            "require_ha_alignment": profile["require_ha_alignment"],
            "require_strong_5m_ha": profile["require_strong_5m_ha"],
            "fractal_intervals": profile["fractal_intervals"],
            "candidate_limit": profile["candidate_limit"],
            "symbol_mode": profile["symbol_mode"]
        }

    def calculate_market_volatility(self):
        """Estimate market volatility from cached prices."""
        if len(self.current_prices) < 2:
            return 0.02
        prices = list(self.current_prices.values())
        avg_price = sum(prices) / len(prices)
        variance = sum((price - avg_price) ** 2 for price in prices) / len(prices)
        volatility = (variance ** 0.5) / avg_price

        return min(max(volatility, 0.01), 0.1)

    def log_system_error(self, error_type, error_message):
        """Record a system error in memory and trading results."""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": error_message,
            "traceback": traceback.format_exc() if traceback.format_exc() != "NoneType: None\n" else None
        }

        if not hasattr(self, "system_errors"):
            self.system_errors = []
        self.system_errors.append(error_record)

        if not hasattr(self, "trading_results"):
            self.trading_results = {
                "system_errors": [],
                "error_count": 0,
                "last_error": None
            }

        self.trading_results.setdefault("system_errors", []).append(error_record)
        self.trading_results["error_count"] = self.trading_results.get("error_count", 0) + 1
        self.trading_results["last_error"] = error_record

        print(f"[ERROR] {error_type} - {error_message}")

    def sync_positions(self):
        """Synchronize active positions from the exchange."""
        try:
            account_info = self.get_account_info()
            if account_info:
                previous_active_positions = self.trading_results.get("active_positions", {})
                active_positions = {}
                for position in account_info['positions']:
                    amount = self.safe_float_conversion(position.get('positionAmt'), 0.0)
                    if amount != 0:
                        entry_price = self.safe_float_conversion(position.get('entryPrice'), 0.0)
                        mark_price = self.safe_float_conversion(
                            position.get('markPrice'),
                            self.get_current_price(position.get('symbol'), entry_price)
                        )
                        unrealized_pnl = self.safe_float_conversion(position.get('unRealizedProfit'), None)
                        if unrealized_pnl is None:
                            unrealized_pnl = self.safe_float_conversion(position.get('unrealizedPnl'), 0.0)

                        percentage = self.safe_float_conversion(position.get('percentage'), None)
                        if percentage is None and entry_price > 0:
                            direction = 1 if amount > 0 else -1
                            percentage = ((mark_price - entry_price) / entry_price) * 100 * direction
                        if percentage is None:
                            percentage = 0.0

                        inferred_entry_time = (
                            previous_active_positions.get(position['symbol'], {}).get('entry_time') or
                            self.position_entry_times.get(position['symbol']) or
                            datetime.now().isoformat()
                        )

                        active_positions[position['symbol']] = {
                            'amount': amount,
                            'entry_price': entry_price,
                            'mark_price': mark_price,
                            'unrealized_pnl': unrealized_pnl,
                            'percentage': percentage,
                            'entry_time': inferred_entry_time
                        }

                self.trading_results["active_positions"] = active_positions
                print(f"[INFO] Positions synced: {len(active_positions)}")

        except Exception as e:
            self.log_system_error("periodic_sync_error", str(e))

    def sync_account_balance(self):
        """Synchronize account balance from the exchange."""
        try:
            account_info = self.get_account_info()
            if account_info:
                total_balance = float(account_info['totalWalletBalance'])
                available_balance = float(account_info['availableBalance'])
                self.account_data_available = True

                self.trading_results["current_capital"] = total_balance
                self.trading_results["available_balance"] = available_balance
                self.total_capital = total_balance
                self.refresh_strategy_capital_allocations()
                pnl = total_balance - self.trading_results["initial_capital"]
                self.trading_results["total_pnl"] = pnl
                balance_record = {
                    "timestamp": datetime.now().isoformat(),
                    "total_balance": total_balance,
                    "total_pnl": pnl,
                    "market_regime": self.trading_results["market_regime"]
                }
                self.trading_results["balance_history"].append(balance_record)

                print(f"[INFO] Balance synced: ${total_balance:.2f} (PnL: ${pnl:+.2f})")

        except Exception as e:
            self.log_system_error("balance_sync_error", str(e))

    def get_symbol_info(self, symbol):
        """Fetch exchange symbol metadata with caching."""
        if symbol in self.symbol_info_cache:
            return self.symbol_info_cache[symbol]

        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)

            if response.status_code == 200:
                exchange_info = response.json()

                for symbol_info in exchange_info["symbols"]:
                    if symbol_info["symbol"] == symbol:
                        self.symbol_info_cache[symbol] = symbol_info
                        return symbol_info

            return None
        except Exception as e:
            self.log_system_error("symbol_info_error", str(e))
            return None

    def get_klines(self, symbol, interval, limit):
        """Fetch kline data for a symbol and interval."""
        try:
            response = requests.get(
                f"{self.base_url}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.log_system_error("kline_fetch_error", f"{symbol} {interval}: {e}")
        return []

    def calculate_sma(self, values, period):
        """Calculate a simple moving average."""
        if len(values) < period or period <= 0:
            return None
        window = values[-period:]
        return sum(window) / len(window)

    def calculate_ema(self, values, period):
        """Calculate an exponential moving average."""
        if len(values) < period or period <= 0:
            return None

        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period
        for price in values[period:]:
            ema = (price - ema) * multiplier + ema
        return ema

    def calculate_recent_fractals(self, highs, lows, lookback=40):
        """Find the most recent confirmed upper and lower fractals."""
        if len(highs) < 5 or len(lows) < 5:
            return None, None

        upper_fractal = None
        lower_fractal = None
        start_idx = max(2, len(highs) - lookback)
        end_idx = len(highs) - 2

        for idx in range(start_idx, end_idx):
            if (
                highs[idx] > highs[idx - 1] and
                highs[idx] > highs[idx - 2] and
                highs[idx] > highs[idx + 1] and
                highs[idx] > highs[idx + 2]
            ):
                upper_fractal = highs[idx]

            if (
                lows[idx] < lows[idx - 1] and
                lows[idx] < lows[idx - 2] and
                lows[idx] < lows[idx + 1] and
                lows[idx] < lows[idx + 2]
            ):
                lower_fractal = lows[idx]

        return upper_fractal, lower_fractal

    def calculate_heikin_ashi(self, ohlc_rows):
        """Convert OHLC rows into Heikin Ashi candles."""
        if not ohlc_rows:
            return []

        ha_rows = []
        prev_ha_open = None
        prev_ha_close = None

        for row in ohlc_rows:
            open_price = row["open"]
            high_price = row["high"]
            low_price = row["low"]
            close_price = row["close"]
            ha_close = (open_price + high_price + low_price + close_price) / 4

            if prev_ha_open is None or prev_ha_close is None:
                ha_open = (open_price + close_price) / 2
            else:
                ha_open = (prev_ha_open + prev_ha_close) / 2

            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            ha_rows.append({
                "open": ha_open,
                "high": ha_high,
                "low": ha_low,
                "close": ha_close
            })
            prev_ha_open = ha_open
            prev_ha_close = ha_close

        return ha_rows

    def analyze_heikin_ashi(self, ha_rows):
        """Summarize recent Heikin Ashi trend and reversal state."""
        if len(ha_rows) < 3:
            return None

        current = ha_rows[-1]
        previous = ha_rows[-2]
        epsilon = max(abs(current["close"]) * 0.00001, 1e-8)

        def candle_side(row):
            if row["close"] > row["open"]:
                return "BULLISH"
            if row["close"] < row["open"]:
                return "BEARISH"
            return "NEUTRAL"

        trend = candle_side(current)
        strong_bullish = trend == "BULLISH" and abs(current["open"] - current["low"]) <= epsilon
        strong_bearish = trend == "BEARISH" and abs(current["open"] - current["high"]) <= epsilon

        bull_count = 0
        bear_count = 0
        for row in reversed(ha_rows[-5:]):
            side = candle_side(row)
            if side == "BULLISH" and bear_count == 0:
                bull_count += 1
            elif side == "BEARISH" and bull_count == 0:
                bear_count += 1
            else:
                break

        body = abs(current["close"] - current["open"])
        total_range = max(current["high"] - current["low"], epsilon)
        upper_wick = current["high"] - max(current["open"], current["close"])
        lower_wick = min(current["open"], current["close"]) - current["low"]
        reversal = body <= (total_range * 0.25) and upper_wick > body and lower_wick > body
        flipped = candle_side(previous) != trend and trend != "NEUTRAL"

        return {
            "trend": trend,
            "strong_bullish": strong_bullish,
            "strong_bearish": strong_bearish,
            "bull_count": bull_count,
            "bear_count": bear_count,
            "reversal": reversal,
            "flipped": flipped
        }

    def analyze_timeframe_ma(self, symbol, interval, limit=120):
        """Analyze moving averages, crossovers, fractals, and volume for one timeframe."""
        klines = self.get_klines(symbol, interval, limit)
        if len(klines) > 1:
            klines = klines[:-1]
        closes = [self.safe_float_conversion(kline[4], 0.0) for kline in klines]
        closes = [price for price in closes if price > 0]
        highs = [self.safe_float_conversion(kline[2], 0.0) for kline in klines]
        highs = [price for price in highs if price > 0]
        lows = [self.safe_float_conversion(kline[3], 0.0) for kline in klines]
        lows = [price for price in lows if price > 0]
        opens = [self.safe_float_conversion(kline[1], 0.0) for kline in klines]
        opens = [price for price in opens if price > 0]
        volumes = [self.safe_float_conversion(kline[5], 0.0) for kline in klines]
        volumes = [volume for volume in volumes if volume >= 0]

        if len(closes) < 60 or len(highs) < 60 or len(lows) < 60 or len(opens) < 60:
            return None

        current_price = closes[-1]
        previous_close = closes[-2] if len(closes) >= 2 else current_price
        ohlc_rows = []
        for idx in range(min(len(opens), len(highs), len(lows), len(closes))):
            ohlc_rows.append({
                "open": opens[idx],
                "high": highs[idx],
                "low": lows[idx],
                "close": closes[idx]
            })
        ma_fast = self.calculate_sma(closes, 5)
        ma_mid = self.calculate_sma(closes, 20)
        ma_slow = self.calculate_sma(closes, 60)
        ema_fast = self.calculate_ema(closes, 9)
        ema_mid = self.calculate_ema(closes, 21)
        ema_slow = self.calculate_ema(closes, 55)
        last_fractal_high, last_fractal_low = self.calculate_recent_fractals(highs, lows)
        ha_rows = self.calculate_heikin_ashi(ohlc_rows)
        ha_summary = self.analyze_heikin_ashi(ha_rows)

        if None in (ma_fast, ma_mid, ma_slow, ema_fast, ema_mid, ema_slow) or ha_summary is None:
            return None

        returns = []
        for idx in range(1, len(closes)):
            prev = closes[idx - 1]
            curr = closes[idx]
            if prev > 0:
                returns.append((curr - prev) / prev)

        avg_change = sum(returns) / len(returns) if returns else 0.0
        variance = sum((change - avg_change) ** 2 for change in returns) / len(returns) if returns else 0.0
        volatility = variance ** 0.5

        avg_volume = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 0.0
        current_volume = volumes[-1] if volumes else 0.0
        volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 1.0
        volume_expansion = volume_ratio >= 1.2

        alignment = "NEUTRAL"
        trend_score = 0
        if ma_fast > ma_mid > ma_slow and ema_fast > ema_mid > ema_slow:
            alignment = "BULLISH"
            trend_score = 1
        elif ma_fast < ma_mid < ma_slow and ema_fast < ema_mid < ema_slow:
            alignment = "BEARISH"
            trend_score = -1

        price_vs_ma = "ABOVE"
        if current_price < ma_mid and current_price < ema_mid:
            price_vs_ma = "BELOW"

        previous_ema_fast = self.calculate_ema(closes[:-1], 9) if len(closes) > 55 else None
        previous_ema_mid = self.calculate_ema(closes[:-1], 21) if len(closes) > 55 else None
        cross_signal = "NONE"
        if previous_ema_fast is not None and previous_ema_mid is not None:
            if previous_ema_fast <= previous_ema_mid and ema_fast > ema_mid:
                cross_signal = "BULLISH_CROSS"
            elif previous_ema_fast >= previous_ema_mid and ema_fast < ema_mid:
                cross_signal = "BEARISH_CROSS"

        fractal_breakout_up = False
        fractal_breakout_down = False
        if last_fractal_high is not None:
            fractal_breakout_up = current_price > last_fractal_high and previous_close <= last_fractal_high
        if last_fractal_low is not None:
            fractal_breakout_down = current_price < last_fractal_low and previous_close >= last_fractal_low

        recent_breakout_up = False
        recent_breakout_down = False
        pullback_entry_up = False
        pullback_entry_down = False
        if last_fractal_high is not None:
            recent_breakout_up = any(close > last_fractal_high for close in closes[-self.pullback_lookback_bars:])
            pullback_entry_up = (
                recent_breakout_up and
                current_price >= ema_mid and
                abs(current_price - ema_mid) / max(abs(ema_mid), 1e-8) <= self.pullback_proximity_pct
            )
        if last_fractal_low is not None:
            recent_breakout_down = any(close < last_fractal_low for close in closes[-self.pullback_lookback_bars:])
            pullback_entry_down = (
                recent_breakout_down and
                current_price <= ema_mid and
                abs(current_price - ema_mid) / max(abs(ema_mid), 1e-8) <= self.pullback_proximity_pct
            )

        return {
            "interval": interval,
            "current_price": current_price,
            "previous_close": previous_close,
            "ma_fast": ma_fast,
            "ma_mid": ma_mid,
            "ma_slow": ma_slow,
            "ema_fast": ema_fast,
            "ema_mid": ema_mid,
            "ema_slow": ema_slow,
            "alignment": alignment,
            "price_vs_ma": price_vs_ma,
            "avg_change": avg_change,
            "volatility": volatility,
            "trend_score": trend_score,
            "cross_signal": cross_signal,
            "current_volume": current_volume,
            "avg_volume": avg_volume,
            "volume_ratio": volume_ratio,
            "volume_expansion": volume_expansion,
            "last_fractal_high": last_fractal_high,
            "last_fractal_low": last_fractal_low,
            "fractal_breakout_up": fractal_breakout_up,
            "fractal_breakout_down": fractal_breakout_down,
            "recent_breakout_up": recent_breakout_up,
            "recent_breakout_down": recent_breakout_down,
            "pullback_entry_up": pullback_entry_up,
            "pullback_entry_down": pullback_entry_down,
            "ha_trend": ha_summary["trend"],
            "ha_strong_bullish": ha_summary["strong_bullish"],
            "ha_strong_bearish": ha_summary["strong_bearish"],
            "ha_bull_count": ha_summary["bull_count"],
            "ha_bear_count": ha_summary["bear_count"],
            "ha_reversal": ha_summary["reversal"],
            "ha_flipped": ha_summary["flipped"]
        }

    def analyze_market_regime(self, symbol):
        """Analyze market regime from multi-timeframe moving averages."""
        try:
            timeframe_order = [("5m", 120), ("15m", 120), ("1h", 120)]
            timeframe_data = {}
            trend_scores = []
            volatilities = []
            avg_changes = []

            for interval, limit in timeframe_order:
                data = self.analyze_timeframe_ma(symbol, interval, limit)
                if data:
                    timeframe_data[interval] = data
                    trend_scores.append(data["trend_score"])
                    volatilities.append(data["volatility"])
                    avg_changes.append(data["avg_change"])

            if not timeframe_data:
                return {
                    "regime": "SIDEWAYS_MARKET",
                    "avg_change": 0,
                    "volatility": 0.02,
                    "strength": 0,
                    "timeframes": {},
                    "trend_consensus": 0
                }

            trend_consensus = sum(trend_scores)
            avg_change = sum(avg_changes) / len(avg_changes) if avg_changes else 0.0
            volatility = sum(volatilities) / len(volatilities) if volatilities else 0.02
            strength = abs(avg_change) + (abs(trend_consensus) / max(1, len(trend_scores))) * 0.01

            if trend_consensus >= 2:
                regime = "BULL_MARKET"
            elif trend_consensus <= -2:
                regime = "BEAR_MARKET"
            else:
                regime = "SIDEWAYS_MARKET"

            return {
                "regime": regime,
                "avg_change": avg_change,
                "volatility": volatility,
                "strength": strength,
                "timeframes": timeframe_data,
                "trend_consensus": trend_consensus
            }
        except Exception as e:
            self.log_system_error("trading_runtime_error", str(e))
            return {
                "regime": "SIDEWAYS_MARKET",
                "avg_change": 0,
                "volatility": 0.02,
                "strength": 0,
                "timeframes": {},
                "trend_consensus": 0
            }

    def get_ma_trade_decision(self, strategy, market_regime):
        """Return a trade decision using the shared EMA + Heikin Ashi + fractal framework."""
        timeframe_data = market_regime.get("timeframes", {})
        tf_5m = timeframe_data.get("5m", {})
        tf_15m = timeframe_data.get("15m", {})
        tf_1h = timeframe_data.get("1h", {})
        fractal_intervals = strategy.get("fractal_intervals", ["5m", "15m"])
        session_name = self.get_market_session()
        session_policy = self.get_session_policy(session_name)
        if not session_policy.get("allow_new_entries", True):
            return None

        bullish_alignment_count = sum(1 for tf in timeframe_data.values() if tf.get("alignment") == "BULLISH")
        bearish_alignment_count = sum(1 for tf in timeframe_data.values() if tf.get("alignment") == "BEARISH")
        bullish_cross_count = sum(1 for tf in timeframe_data.values() if tf.get("cross_signal") == "BULLISH_CROSS")
        bearish_cross_count = sum(1 for tf in timeframe_data.values() if tf.get("cross_signal") == "BEARISH_CROSS")
        volume_expansion_count = sum(1 for tf in timeframe_data.values() if tf.get("volume_expansion"))

        bullish_fractal_trigger = any(timeframe_data.get(interval, {}).get("fractal_breakout_up") for interval in fractal_intervals)
        bearish_fractal_trigger = any(timeframe_data.get(interval, {}).get("fractal_breakout_down") for interval in fractal_intervals)
        bullish_breakout_context = any(
            timeframe_data.get(interval, {}).get("recent_breakout_up") or
            timeframe_data.get(interval, {}).get("fractal_breakout_up")
            for interval in fractal_intervals
        )
        bearish_breakout_context = any(
            timeframe_data.get(interval, {}).get("recent_breakout_down") or
            timeframe_data.get(interval, {}).get("fractal_breakout_down")
            for interval in fractal_intervals
        )
        bullish_pullback_ready = any(timeframe_data.get(interval, {}).get("pullback_entry_up") for interval in fractal_intervals)
        bearish_pullback_ready = any(timeframe_data.get(interval, {}).get("pullback_entry_down") for interval in fractal_intervals)

        bullish_ha_ready = (
            tf_1h.get("ha_trend") == "BULLISH" and
            tf_15m.get("ha_trend") == "BULLISH" and
            (tf_5m.get("ha_trend") == "BULLISH" or tf_5m.get("ha_strong_bullish"))
        )
        bearish_ha_ready = (
            tf_1h.get("ha_trend") == "BEARISH" and
            tf_15m.get("ha_trend") == "BEARISH" and
            (tf_5m.get("ha_trend") == "BEARISH" or tf_5m.get("ha_strong_bearish"))
        )

        if strategy.get("require_strong_5m_ha"):
            bullish_ha_ready = bullish_ha_ready and bool(tf_5m.get("ha_strong_bullish"))
            bearish_ha_ready = bearish_ha_ready and bool(tf_5m.get("ha_strong_bearish"))

        volume_ready = (volume_expansion_count >= 1) if strategy.get("require_volume_expansion") else True
        bullish_cross_ready = (bullish_cross_count >= 1) if strategy.get("require_cross") else True
        bearish_cross_ready = (bearish_cross_count >= 1) if strategy.get("require_cross") else True
        required_alignment_count = strategy.get("required_alignment_count", 2)
        consensus_threshold = max(1, strategy.get("consensus_threshold", 2) + session_policy.get("consensus_adjustment", 0))

        long_ready = (
            bullish_alignment_count >= required_alignment_count and
            tf_1h.get("alignment") == "BULLISH" and
            tf_5m.get("price_vs_ma") == "ABOVE" and
            tf_15m.get("price_vs_ma") == "ABOVE" and
            tf_5m.get("ema_fast", 0) > tf_5m.get("ema_mid", 0) and
            tf_15m.get("ema_fast", 0) > tf_15m.get("ema_mid", 0) and
            market_regime.get("trend_consensus", 0) >= consensus_threshold and
            bullish_ha_ready and
            bullish_cross_ready and
            volume_ready and
            bullish_breakout_context and
            bullish_pullback_ready
        )

        short_ready = (
            bearish_alignment_count >= required_alignment_count and
            tf_1h.get("alignment") == "BEARISH" and
            tf_5m.get("price_vs_ma") == "BELOW" and
            tf_15m.get("price_vs_ma") == "BELOW" and
            tf_5m.get("ema_fast", 0) < tf_5m.get("ema_mid", 0) and
            tf_15m.get("ema_fast", 0) < tf_15m.get("ema_mid", 0) and
            market_regime.get("trend_consensus", 0) <= -consensus_threshold and
            bearish_ha_ready and
            bearish_cross_ready and
            volume_ready and
            bearish_breakout_context and
            bearish_pullback_ready
        )

        if long_ready and not short_ready:
            return "BUY"
        if short_ready and not long_ready:
            return "SELL"
        return None

    def should_exit_position_ma(self, position, market_regime, strategy=None):
        """Determine whether a position should exit on MA reversal conditions."""
        timeframe_data = market_regime.get("timeframes", {})
        tf_5m = timeframe_data.get("5m", {})
        tf_15m = timeframe_data.get("15m", {})
        tf_1h = timeframe_data.get("1h", {})
        amount = self.safe_float_conversion(position.get("amount"), 0.0)
        if amount == 0:
            return None

        is_long = amount > 0
        trend_consensus = market_regime.get("trend_consensus", 0)
        exit_signal_threshold = 2
        if strategy:
            exit_signal_threshold = max(2, int(strategy.get("exit_signal_threshold", 2)))

        if is_long:
            exit_signals = 0
            if tf_5m.get("fractal_breakout_down") or tf_15m.get("fractal_breakout_down"):
                exit_signals += 1
            if tf_5m.get("cross_signal") == "BEARISH_CROSS":
                exit_signals += 1
            if tf_15m.get("alignment") == "BEARISH":
                exit_signals += 1
            if tf_5m.get("price_vs_ma") == "BELOW":
                exit_signals += 1
            if tf_5m.get("ha_trend") == "BEARISH" and tf_15m.get("ha_trend") == "BEARISH":
                exit_signals += 1
            if trend_consensus <= -2:
                exit_signals += 1
            if exit_signals >= exit_signal_threshold:
                return "ma_fractal_bearish_reversal"
        else:
            exit_signals = 0
            if tf_5m.get("fractal_breakout_up") or tf_15m.get("fractal_breakout_up"):
                exit_signals += 1
            if tf_5m.get("cross_signal") == "BULLISH_CROSS":
                exit_signals += 1
            if tf_15m.get("alignment") == "BULLISH":
                exit_signals += 1
            if tf_5m.get("price_vs_ma") == "ABOVE":
                exit_signals += 1
            if tf_5m.get("ha_trend") == "BULLISH" and tf_15m.get("ha_trend") == "BULLISH":
                exit_signals += 1
            if trend_consensus >= 2:
                exit_signals += 1
            if exit_signals >= exit_signal_threshold:
                return "ma_fractal_bullish_reversal"
        if is_long and tf_1h.get("alignment") == "BEARISH":
            return "ma_1h_trend_break"
        if (not is_long) and tf_1h.get("alignment") == "BULLISH":
            return "ma_1h_trend_break"

        return None

    def should_exit_position_ema21_trailing(self, position, market_regime):
        """Exit profitable positions when price loses the 5m EMA21 trail."""
        amount = self.safe_float_conversion(position.get("amount"), 0.0)
        entry_price = self.safe_float_conversion(position.get("entry_price"), 0.0)
        mark_price = self.safe_float_conversion(position.get("mark_price"), 0.0)
        if amount == 0 or entry_price <= 0 or mark_price <= 0:
            return None

        is_long = amount > 0
        direction = 1 if is_long else -1
        unrealized = (mark_price - entry_price) * abs(amount) * direction
        if unrealized <= 0:
            return None

        tf_5m = market_regime.get("timeframes", {}).get("5m", {})
        ema_mid = self.safe_float_conversion(tf_5m.get("ema_mid"), 0.0)
        if ema_mid <= 0:
            return None

        if is_long and mark_price < ema_mid:
            return "ema21_trailing_exit"
        if (not is_long) and mark_price > ema_mid:
            return "ema21_trailing_exit"
        return None

    def generate_strategy_signal(self, strategy_name, market_regime, symbol):
        """Generate a signal from the shared EMA + Heikin Ashi + fractal framework."""
        strategy = self.strategies[strategy_name]
        signal = self.get_ma_trade_decision(strategy, market_regime)

        market_bias = strategy.get("market_bias", "adaptive")
        if signal == "BUY" and market_bias == "bearish":
            return None
        if signal == "SELL" and market_bias == "bullish":
            return None
        return signal

    def score_trade_candidate(self, market_regime):
        """Rank candidate symbols so we do not rely on random selection."""
        timeframe_data = market_regime.get("timeframes", {})
        score = self.safe_float_conversion(market_regime.get("strength"), 0.0) * 100.0
        score += abs(self.safe_float_conversion(market_regime.get("trend_consensus"), 0.0)) * 5.0

        for tf in timeframe_data.values():
            if tf.get("alignment") in {"BULLISH", "BEARISH"}:
                score += 3.0
            if tf.get("cross_signal") in {"BULLISH_CROSS", "BEARISH_CROSS"}:
                score += 2.0
            if tf.get("volume_expansion"):
                score += 1.5
            if tf.get("fractal_breakout_up") or tf.get("fractal_breakout_down"):
                score += 2.5
            if tf.get("ha_trend") in {"BULLISH", "BEARISH"}:
                score += 1.0

        return score

    def get_default_entry_time(self):
        """Return a conservative fallback entry time for unknown positions."""
        return datetime.now().isoformat()

    def get_position_entry_time(self, symbol):
        """Return the tracked entry time for an active position."""
        active_position = self.trading_results.get("active_positions", {}).get(symbol, {})
        for trade in reversed(self.trading_results.get("real_orders", [])):
            if trade.get("symbol") != symbol:
                continue
            if trade.get("reduce_only"):
                continue
            if trade.get("status") not in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                continue
            return trade.get("timestamp") or self.get_default_entry_time()
        return (
            active_position.get("entry_time") or
            self.position_entry_times.get(symbol) or
            self.get_default_entry_time()
        )

    def get_last_entry_trade(self, symbol):
        """Return the latest non-reduce-only trade record for a symbol."""
        for trade in reversed(self.trading_results.get("real_orders", [])):
            if trade.get("symbol") != symbol:
                continue
            if trade.get("reduce_only"):
                continue
            if trade.get("status") not in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                continue
            return trade
        return None

    def get_position_strategy(self, symbol):
        """Return the strategy config associated with an active symbol."""
        last_entry_trade = self.get_last_entry_trade(symbol)
        if not last_entry_trade:
            return None
        return self.strategies.get(last_entry_trade.get("strategy"))

    def get_strategy_entries_today(self, strategy_name):
        """Count today's non-reduce-only entry attempts for a strategy."""
        today = datetime.now().date()
        count = 0
        for trade in self.trading_results.get("real_orders", []):
            if trade.get("strategy") != strategy_name:
                continue
            if trade.get("reduce_only"):
                continue
            status = trade.get("status")
            if status not in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                continue
            try:
                trade_day = datetime.fromisoformat(trade.get("timestamp")).date()
            except Exception:
                continue
            if trade_day == today:
                count += 1
        return count

    def has_reached_daily_entry_limit(self, strategy_name):
        """Return whether the strategy has reached its daily entry limit."""
        strategy = self.strategies.get(strategy_name, {})
        limit = max(1, int(strategy.get("daily_entry_limit", 5)))
        return self.get_strategy_entries_today(strategy_name) >= limit

    def is_past_min_hold(self, symbol):
        """Return whether the minimum hold time has elapsed."""
        entry_time_str = self.get_position_entry_time(symbol)
        try:
            entry_time = datetime.fromisoformat(entry_time_str)
        except Exception:
            return True
        return (datetime.now() - entry_time).total_seconds() >= self.min_hold_seconds

    def is_symbol_in_cooldown(self, symbol):
        """Return whether a symbol is still in re-entry cooldown."""
        cooldown_time_str = self.recently_closed_symbols.get(symbol)
        if not cooldown_time_str:
            for trade in reversed(self.trading_results.get("real_orders", [])):
                if trade.get("symbol") != symbol:
                    continue
                if not trade.get("reduce_only"):
                    continue
                if trade.get("status") != "FILLED":
                    continue
                cooldown_time_str = trade.get("timestamp")
                break
        if not cooldown_time_str:
            return False
        try:
            cooldown_time = datetime.fromisoformat(cooldown_time_str)
        except Exception:
            return False
        return (datetime.now() - cooldown_time).total_seconds() < self.reentry_cooldown_seconds

    def safe_float_conversion(self, value, default=0.0):
        """Safely convert a value to float."""
        try:
            if value is None:
                return default
            if isinstance(value, str):
                if value == "0.00" or value == "":
                    return default
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            return default

    def round_to_step(self, value, step_size, rounding=ROUND_DOWN):
        """Round quantity to the exchange step size safely."""
        try:
            value_dec = Decimal(str(value))
            step_dec = Decimal(str(step_size))
            if step_dec <= 0:
                return float(value_dec)
            units = (value_dec / step_dec).quantize(Decimal("1"), rounding=rounding)
            return float(units * step_dec)
        except Exception:
            return float(value)

    def get_order_status(self, symbol, order_id):
        """Fetch the latest order status."""
        try:
            server_time = self.get_server_time()
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": server_time,
                "recvWindow": 5000
            }

            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.log_system_error("trading_loop_error", str(e))

        return None

    def get_open_orders(self, symbol):
        """Fetch current open orders for a symbol."""
        try:
            server_time = self.get_server_time()
            params = {
                "symbol": symbol,
                "timestamp": server_time,
                "recvWindow": 5000
            }
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            url = f"{self.base_url}/fapi/v1/openOrders?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.log_system_error("open_orders_error", f"{symbol}: {e}")
        return []

    def cancel_order(self, symbol, order_id):
        """Cancel a single order."""
        try:
            server_time = self.get_server_time()
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": server_time,
                "recvWindow": 5000
            }
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.delete(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.log_system_error("cancel_order_error", f"{symbol}/{order_id}: {e}")
            return False

    def cancel_symbol_protective_orders(self, symbol):
        """Cancel remaining protective orders for a symbol."""
        open_orders = self.get_open_orders(symbol)
        for order in open_orders:
            if order.get("type") not in {"STOP_MARKET", "TAKE_PROFIT_MARKET"}:
                continue
            order_id = order.get("orderId")
            if order_id:
                self.cancel_order(symbol, order_id)

    def format_price_for_symbol(self, symbol, price):
        """Round a price using symbol precision metadata when available."""
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return str(price)
        price_precision = int(symbol_info.get("pricePrecision", 4))
        return f"{float(price):.{max(0, price_precision)}f}"

    def submit_protective_order(self, symbol, side, order_type, stop_price):
        """Submit a protective close-position order."""
        try:
            server_time = self.get_server_time()
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "stopPrice": self.format_price_for_symbol(symbol, stop_price),
                "closePosition": "true",
                "workingType": "MARK_PRICE",
                "timestamp": server_time,
                "recvWindow": 5000
            }
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            self.log_system_error("protective_order_error", f"{symbol} {order_type}: {response.status_code} {response.text}")
        except Exception as e:
            self.log_system_error("protective_order_error", f"{symbol} {order_type}: {e}")
        return None

    def place_protective_orders(self, strategy_name, symbol, entry_side, entry_price):
        """Place a protective stop-loss order immediately after entry."""
        strategy = self.strategies.get(strategy_name, {})
        session_name = self.get_market_session()
        session_policy = self.get_session_policy(session_name)
        stop_multiplier = session_policy.get("protective_stop_multiplier", 1.0)
        stop_loss_pct = self.safe_float_conversion(strategy.get("stop_loss"), self.default_stop_loss_pct / 100.0) * stop_multiplier
        take_profit_pct = self.safe_float_conversion(strategy.get("take_profit"), 0.0)
        if take_profit_pct and take_profit_pct > 0:
            take_profit_pct *= self.safe_float_conversion(session_policy.get("protective_take_profit_multiplier"), 1.0)
        if entry_price <= 0:
            return

        exit_side = "SELL" if entry_side == "BUY" else "BUY"
        if entry_side == "BUY":
            stop_price = entry_price * (1 - stop_loss_pct)
            take_price = entry_price * (1 + take_profit_pct) if take_profit_pct and take_profit_pct > 0 else None
        else:
            stop_price = entry_price * (1 + stop_loss_pct)
            take_price = entry_price * (1 - take_profit_pct) if take_profit_pct and take_profit_pct > 0 else None

        self.cancel_symbol_protective_orders(symbol)
        self.submit_protective_order(symbol, exit_side, "STOP_MARKET", stop_price)
        if take_price is not None:
            self.submit_protective_order(symbol, exit_side, "TAKE_PROFIT_MARKET", take_price)

    def can_open_new_positions(self):
        """Return whether the system has enough verified account state to open new positions."""
        available_balance = self.safe_float_conversion(
            self.trading_results.get("available_balance"),
            self.safe_float_conversion(self.total_capital, 0.0)
        )
        return (
            self.account_data_available and
            self.safe_float_conversion(self.total_capital, 0.0) > 0 and
            self.safe_float_conversion(self.capital_per_strategy, 0.0) > 0 and
            available_balance > 0
        )

    def estimate_realized_pnl(self, trade_record):
        """Estimate realized PnL for reduce-only filled trades."""
        if not trade_record.get("reduce_only"):
            return None
        if trade_record.get("status") != "FILLED":
            return None

        entry_price = self.safe_float_conversion(trade_record.get("entry_price"), 0.0)
        exit_price = self.safe_float_conversion(trade_record.get("price"), 0.0)
        executed_qty = self.safe_float_conversion(trade_record.get("executed_qty"), trade_record.get("quantity"))
        if entry_price <= 0 or exit_price <= 0 or executed_qty <= 0:
            return None

        direction = 1 if trade_record.get("side") == "SELL" else -1
        return (exit_price - entry_price) * executed_qty * direction

    def recompute_trade_counters(self):
        """Recompute aggregate trade counters from the current order ledger."""
        real_orders = self.trading_results.get("real_orders", [])
        total_trades = 0
        pending_trades = 0
        winning_trades = 0
        losing_trades = 0
        closed_trades = 0
        entry_failures = 0

        for trade in real_orders:
            if trade.get("reduce_only"):
                realized_pnl = self.safe_float_conversion(trade.get("realized_pnl"), None)
                if realized_pnl is None and trade.get("status") == "FILLED":
                    realized_pnl = self.estimate_realized_pnl(trade)
                    if realized_pnl is not None:
                        trade["realized_pnl"] = realized_pnl

                if trade.get("status") == "FILLED":
                    closed_trades += 1
                    if realized_pnl is not None:
                        if realized_pnl > 0:
                            winning_trades += 1
                        elif realized_pnl < 0:
                            losing_trades += 1
                continue

            total_trades += 1
            status = trade.get("status")
            if status in {"NEW", "PARTIALLY_FILLED"}:
                pending_trades += 1
            if status in {"FAILED", "ERROR", "CANCELED", "EXPIRED", "REJECTED"}:
                entry_failures += 1

        self.trading_results["total_trades"] = total_trades
        self.trading_results["pending_trades"] = pending_trades
        self.trading_results["winning_trades"] = winning_trades
        self.trading_results["losing_trades"] = losing_trades
        self.trading_results["closed_trades"] = closed_trades
        self.trading_results["entry_failures"] = entry_failures

    def refresh_pending_orders(self):
        """Refresh pending order records so counters and cooldowns stay consistent."""
        for trade in self.trading_results.get("real_orders", []):
            if trade.get("status") not in {"NEW", "PARTIALLY_FILLED"}:
                continue
            order_id = trade.get("order_id")
            symbol = trade.get("symbol")
            if not order_id or order_id == "UNKNOWN" or not symbol:
                continue

            refreshed_status = self.get_order_status(symbol, order_id)
            if not refreshed_status:
                continue

            trade["status"] = refreshed_status.get("status", trade.get("status"))
            trade["executed_qty"] = self.safe_float_conversion(
                refreshed_status.get("executedQty"),
                trade.get("executed_qty", 0.0)
            )
            refreshed_price = self.safe_float_conversion(refreshed_status.get("avgPrice"), trade.get("price", 0.0))
            if refreshed_price > 0:
                trade["price"] = refreshed_price

            if trade["status"] in {"NEW", "PARTIALLY_FILLED"}:
                trade["type"] = "PENDING_TRADE"
            elif trade["status"] == "FILLED":
                trade["type"] = "ACTUAL_TRADE"
            else:
                trade["type"] = "FAILED_TRADE"

            if trade.get("reduce_only"):
                if trade["status"] == "FILLED":
                    trade["realized_pnl"] = self.estimate_realized_pnl(trade)
                    self.recently_closed_symbols[symbol] = datetime.now().isoformat()
                    self.position_entry_times.pop(symbol, None)
            else:
                if trade["status"] == "FILLED":
                    self.position_entry_times[symbol] = trade.get("timestamp", datetime.now().isoformat())

        self.recompute_trade_counters()

    def submit_order(self, strategy_name, symbol, side, quantity, reduce_only=False, metadata=None):
        """Submit a market order with validation and error handling."""
        try:
            metadata = metadata or {}
            metadata.setdefault("market_session", self.get_market_session())
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                self.log_system_error("symbol_info_missing", f"No symbol metadata found for {symbol}")
                return None
            if (not reduce_only) and not self.account_data_available:
                self.log_system_error("account_data_unavailable", f"Blocked order for {symbol} because account data is unavailable")
                return None

            filters = symbol_info["filters"]
            min_qty = 0.0
            max_qty = 0.0
            min_notional = 0.0
            qty_precision = 0
            step_size = 0.0

            for f in filters:
                if f["filterType"] == "LOT_SIZE":
                    min_qty = float(f["minQty"])
                    max_qty = float(f["maxQty"])
                    if "stepSize" in f:
                        step_size = float(f["stepSize"])
                        step_size_str = format(Decimal(str(step_size)).normalize(), "f")
                        if "." in step_size_str:
                            qty_precision = len(step_size_str.rstrip("0").split('.')[1])
                        else:
                            qty_precision = 0
                    else:
                        qty_precision = 8
                elif f["filterType"] == "MIN_NOTIONAL":
                    min_notional = self.safe_float_conversion(f.get("notional"), min_notional)
                elif f["filterType"] == "NOTIONAL":
                    min_notional = self.safe_float_conversion(f.get("minNotional"), min_notional)

            if min_notional <= 0:
                min_notional = 5.0
            if quantity < min_qty:
                quantity = min_qty
            current_price = self.get_current_price(symbol, 0.0)
            if current_price <= 0:
                self.log_system_error("price_lookup_failed", f"Blocked order for {symbol} because price lookup failed")
                return None

            if step_size > 0:
                quantity = self.round_to_step(quantity, step_size, ROUND_UP)
            else:
                quantity = round(quantity, qty_precision)

            current_notional = quantity * current_price
            if current_notional < min_notional:
                required_qty = (min_notional * 1.05) / current_price
                quantity = max(quantity, required_qty, min_qty)
                if step_size > 0:
                    quantity = self.round_to_step(quantity, step_size, ROUND_UP)
                else:
                    quantity = round(quantity, qty_precision)
            if quantity > max_qty:
                quantity = max_qty
            if step_size > 0:
                quantity = self.round_to_step(quantity, step_size, ROUND_DOWN)
            else:
                quantity = round(quantity, qty_precision)

            if quantity < min_qty:
                quantity = min_qty
                if step_size > 0:
                    quantity = self.round_to_step(quantity, step_size, ROUND_UP)

            final_notional = quantity * current_price
            if final_notional < min_notional:
                error_msg = f"{symbol} order quantity validation failed: quantity={quantity}, notional={final_notional:.6f}, min_notional={min_notional:.6f}"
                self.log_system_error("min_notional_not_met", error_msg)
                return None

            available_balance = self.safe_float_conversion(
                self.trading_results.get("available_balance"),
                self.safe_float_conversion(self.total_capital, 0.0)
            )
            if (not reduce_only) and available_balance > 0:
                max_affordable_notional = max((available_balance * 0.9), min_notional * 1.05)
                if final_notional > max_affordable_notional:
                    quantity = max_affordable_notional / current_price
                    if step_size > 0:
                        quantity = self.round_to_step(quantity, step_size, ROUND_DOWN)
                    else:
                        quantity = round(quantity, qty_precision)
                    final_notional = quantity * current_price
                    if final_notional < min_notional:
                        self.log_system_error(
                            "insufficient_available_balance",
                            f"Skipped order for {symbol}: available={available_balance:.6f}, requested_notional={quantity * current_price:.6f}, min_notional={min_notional:.6f}"
                        )
                        return None

            headers = {"X-MBX-APIKEY": self.api_key}
            response = None
            last_error_msg = None

            for _ in range(4):
                server_time = self.get_server_time()
                params = {
                    "symbol": symbol,
                    "side": side,
                    "type": "MARKET",
                    "quantity": str(quantity),
                    "reduceOnly": "true" if reduce_only else "false",
                    "timestamp": server_time,
                    "recvWindow": 5000
                }

                query_string = urllib.parse.urlencode(params)
                signature = hmac.new(
                    self.api_secret.encode("utf-8"),
                    query_string.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()

                url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
                response = requests.post(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    break

                last_error_msg = f"Order failed: {response.status_code} - {response.text}"
                if response.status_code == 400 and '"code":-2019' in response.text:
                    reduced_quantity = quantity * 0.5
                    if step_size > 0:
                        reduced_quantity = self.round_to_step(reduced_quantity, step_size, ROUND_DOWN)
                    else:
                        reduced_quantity = round(reduced_quantity, qty_precision)

                    if reduced_quantity < min_qty or (reduced_quantity * current_price) < min_notional:
                        break

                    quantity = reduced_quantity
                    continue

                break
            if response is not None and response.status_code == 200:
                result = response.json()
                print(f"[ORDER_OK] {result}")

                order_id = result.get("orderId", "UNKNOWN")
                order_status = result
                if order_id != "UNKNOWN":
                    time.sleep(1)
                    refreshed_status = self.get_order_status(symbol, order_id)
                    if refreshed_status:
                        order_status = refreshed_status

                avg_price = self.safe_float_conversion(order_status.get("avgPrice"), current_price)
                executed_qty = self.safe_float_conversion(order_status.get("executedQty"), 0.0)
                status = order_status.get("status", result.get("status", "UNKNOWN"))
                record_type = "ACTUAL_TRADE"
                if status in {"NEW", "PARTIALLY_FILLED"}:
                    record_type = "PENDING_TRADE"
                elif status in {"CANCELED", "EXPIRED", "REJECTED"}:
                    record_type = "FAILED_TRADE"

                record_timestamp = datetime.now().isoformat()
                trade_record = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": avg_price,
                    "order_id": order_id,
                    "status": status,
                    "executed_qty": executed_qty,
                    "timestamp": record_timestamp,
                    "type": record_type,
                    "market_regime": self.trading_results["market_regime"],
                    "strategy_signal": side,
                    "position_type": "LONG" if side == "BUY" else "SHORT"
                }
                trade_record.update(metadata)
                if reduce_only:
                    trade_record["reduce_only"] = True

                self.trading_results["real_orders"].append(trade_record)

                if reduce_only and status == "FILLED":
                    trade_record["realized_pnl"] = self.estimate_realized_pnl(trade_record)
                    self.recently_closed_symbols[symbol] = record_timestamp
                    self.position_entry_times.pop(symbol, None)
                    self.cancel_symbol_protective_orders(symbol)
                elif (not reduce_only) and status in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                    self.position_entry_times[symbol] = record_timestamp

                if reduce_only:
                    print(f"[CLOSE] {strategy_name} | {symbol} | {side} | {quantity} | {status}")
                elif status == "FILLED":
                    print(f"[FILLED] {strategy_name} | {symbol} | {side} | {quantity}")
                    self.place_protective_orders(strategy_name, symbol, side, avg_price)
                elif status in {"NEW", "PARTIALLY_FILLED"}:
                    print(f"[PENDING] {strategy_name} | {symbol} | {side} | {quantity} | {status} | executed={executed_qty}")
                else:
                    print(f"[FAILED] {strategy_name} | {symbol} | {side} | {quantity} | {status}")

                self.refresh_pending_orders()
                self.recompute_trade_counters()
                self.sync_positions()
                self.sync_account_balance()
                return result
            else:
                error_msg = last_error_msg or f"Order failed: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_msg}")
                failed_record = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "status": "FAILED",
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat(),
                    "type": "FAILED_TRADE",
                    "market_regime": self.trading_results["market_regime"],
                    "strategy_signal": side,
                    "position_type": "LONG" if side == "BUY" else "SHORT"
                }
                if reduce_only:
                    failed_record["reduce_only"] = True

                self.trading_results["real_orders"].append(failed_record)
                self.recompute_trade_counters()
                return None

        except Exception as e:
            error_msg = f"Order submission failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            error_record = {
                "strategy": strategy_name,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "status": "ERROR",
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "type": "ERROR_TRADE",
                "market_regime": self.trading_results["market_regime"],
                "strategy_signal": side,
                "position_type": "LONG" if side == "BUY" else "SHORT"
            }
            if reduce_only:
                error_record["reduce_only"] = True

            self.trading_results["real_orders"].append(error_record)
            self.recompute_trade_counters()
            self.log_system_error("trading_runtime_error", str(e))

            return None

    def execute_strategy_trade(self, strategy_name):
        """Evaluate candidate symbols and trade the best qualified one for the strategy."""
        try:
            strategy = self.strategies[strategy_name]
            self.refresh_strategy_capital_allocations()
            if not self.can_open_new_positions():
                self.emit_signal_diagnostic(strategy_name, "account_blocked", [])
                return None
            if self.has_reached_daily_entry_limit(strategy_name):
                self.emit_signal_diagnostic(strategy_name, "daily_entry_limit", [])
                return None

            available_symbols = [s for s in strategy["preferred_symbols"] if s in self.valid_symbols]
            if not available_symbols:
                available_symbols = list(self.valid_symbols)

            active_positions = self.trading_results.get("active_positions", {})
            available_symbols = [s for s in available_symbols if s not in active_positions]
            available_symbols = [s for s in available_symbols if not self.is_symbol_in_cooldown(s)]
            if not available_symbols:
                self.emit_signal_diagnostic(strategy_name, "no_available_symbols", [])
                return None

            candidate_limit = max(1, int(strategy.get("candidate_limit", 5)))
            candidate_evaluations = []
            diagnostic_candidates = []
            for symbol in self.select_candidate_symbols(available_symbols, candidate_limit):
                market_regime = self.analyze_market_regime(symbol)
                signal = self.generate_strategy_signal(strategy_name, market_regime, symbol)
                diagnostic_candidates.append({
                    "symbol": symbol,
                    "signal": signal,
                    "market_regime": market_regime,
                })
                if not signal:
                    continue
                candidate_evaluations.append({
                    "symbol": symbol,
                    "signal": signal,
                    "market_regime": market_regime,
                    "score": self.score_trade_candidate(market_regime),
                })

            if not candidate_evaluations:
                self.emit_signal_diagnostic(strategy_name, "no_qualified_signal", diagnostic_candidates)
                return None

            best_candidate = max(candidate_evaluations, key=lambda item: item["score"])
            self.trading_results["market_regime"] = best_candidate["market_regime"]["regime"]
            quantity = self.calculate_position_size(strategy_name, best_candidate["symbol"])
            if quantity <= 0:
                self.emit_signal_diagnostic(strategy_name, "quantity_zero", [best_candidate])
                return None

            return self.submit_order(
                strategy_name,
                best_candidate["symbol"],
                best_candidate["signal"],
                quantity,
                metadata={"market_session": self.get_market_session()},
            )

        except Exception as e:
            self.log_system_error("trading_loop_error", str(e))
            return None

    def emit_signal_diagnostic(self, strategy_name, reason, candidates):
        """Log a throttled diagnostic summary when no trade can be opened."""
        now = datetime.now()
        key = f"{strategy_name}:{reason}"
        last_logged = self.last_signal_diagnostic_log.get(key)
        if last_logged and (now - last_logged).total_seconds() < self.signal_diagnostic_log_interval_sec:
            return
        self.last_signal_diagnostic_log[key] = now

        summary = self.build_signal_diagnostic_summary(strategy_name, reason, candidates)
        print(f"[DIAG] {json.dumps(summary, ensure_ascii=True, sort_keys=True)}")

    def build_signal_diagnostic_summary(self, strategy_name, reason, candidates):
        """Build a compact signal diagnostic payload for operations logs."""
        session_name = self.get_market_session()
        payload = {
            "strategy": strategy_name,
            "reason": reason,
            "session": session_name,
            "can_open": bool(self.can_open_new_positions()),
            "account_data_available": bool(getattr(self, "account_data_available", False)),
            "available_balance": round(self.safe_float_conversion(self.trading_results.get("available_balance"), 0.0), 6),
            "active_positions": len(self.trading_results.get("active_positions", {})),
            "candidate_count": len(candidates or []),
            "regime_counts": {},
            "trend_consensus_counts": {},
            "signal_counts": {},
            "sample": [],
        }

        for item in candidates or []:
            market_regime = item.get("market_regime") or {}
            signal = item.get("signal")
            regime = market_regime.get("regime", "UNKNOWN")
            consensus = str(market_regime.get("trend_consensus", "UNKNOWN"))
            signal_key = str(signal) if signal else "None"
            payload["regime_counts"][regime] = payload["regime_counts"].get(regime, 0) + 1
            payload["trend_consensus_counts"][consensus] = payload["trend_consensus_counts"].get(consensus, 0) + 1
            payload["signal_counts"][signal_key] = payload["signal_counts"].get(signal_key, 0) + 1

            if len(payload["sample"]) < 3:
                timeframe_data = market_regime.get("timeframes", {})
                tf_5m = timeframe_data.get("5m", {})
                tf_15m = timeframe_data.get("15m", {})
                tf_1h = timeframe_data.get("1h", {})
                payload["sample"].append({
                    "symbol": item.get("symbol"),
                    "signal": signal_key,
                    "regime": regime,
                    "trend_consensus": market_regime.get("trend_consensus"),
                    "tf_5m": {
                        "alignment": tf_5m.get("alignment"),
                        "price_vs_ma": tf_5m.get("price_vs_ma"),
                        "ha_trend": tf_5m.get("ha_trend"),
                        "fractal_up": bool(tf_5m.get("fractal_breakout_up")),
                        "fractal_down": bool(tf_5m.get("fractal_breakout_down")),
                    },
                    "tf_15m": {
                        "alignment": tf_15m.get("alignment"),
                        "price_vs_ma": tf_15m.get("price_vs_ma"),
                        "ha_trend": tf_15m.get("ha_trend"),
                        "fractal_up": bool(tf_15m.get("fractal_breakout_up")),
                        "fractal_down": bool(tf_15m.get("fractal_breakout_down")),
                    },
                    "tf_1h": {
                        "alignment": tf_1h.get("alignment"),
                        "price_vs_ma": tf_1h.get("price_vs_ma"),
                        "ha_trend": tf_1h.get("ha_trend"),
                    },
                })
        return payload

    def select_candidate_symbols(self, available_symbols, candidate_limit):
        """Select candidate symbols evenly across the available universe."""
        symbols = list(available_symbols)
        if candidate_limit >= len(symbols):
            return symbols

        selected = []
        max_index = len(symbols) - 1
        for idx in range(candidate_limit):
            position = round((idx * max_index) / max(1, candidate_limit - 1))
            symbol = symbols[position]
            if symbol not in selected:
                selected.append(symbol)

        if len(selected) < candidate_limit:
            for symbol in symbols:
                if symbol not in selected:
                    selected.append(symbol)
                if len(selected) >= candidate_limit:
                    break
        return selected

    def calculate_position_size(self, strategy_name, symbol):
        """Calculate the position size for a strategy and symbol."""
        try:
            strategy = self.strategies[strategy_name]
            capital = strategy["capital"]
            risk_per_trade = strategy["risk_per_trade"]
            leverage = strategy["leverage"]
            session_policy = self.get_session_policy(self.get_market_session())
            session_size_multiplier = self.safe_float_conversion(session_policy.get("position_size_multiplier"), 1.0)
            risk_amount = capital * risk_per_trade
            position_value = risk_amount * leverage * session_size_multiplier

            current_price = self.get_current_price(symbol, 0.0)
            if current_price <= 0:
                return 0.0
            quantity = position_value / current_price
            min_quantities = {
                "BTCUSDT": 0.001, "ETHUSDT": 0.01, "SOLUSDT": 0.1, "DOGEUSDT": 10,
                "ADAUSDT": 1, "MATICUSDT": 1, "AVAXUSDT": 0.1, "DOTUSDT": 1,
                "LINKUSDT": 0.1, "LTCUSDT": 0.01
            }

            if symbol in min_quantities:
                min_qty = min_quantities[symbol]
                quantity = max(quantity, min_qty)

            return quantity

        except Exception as e:
            self.log_system_error("position_size_error", str(e))
            return 0.0

    def close_position(self, symbol, position, reason):
        """Close an open position with a reduce-only market order."""
        amount = abs(self.safe_float_conversion(position.get("amount"), 0.0))
        if amount <= 0:
            return None

        bypass_hold_reasons = {
            "full_reset",
            "full_reset_retry",
            "restart_after_hold_fix",
            "restart_after_entry_time_fix"
        }
        if reason not in bypass_hold_reasons and not self.is_past_min_hold(symbol):
            return None

        side = "SELL" if self.safe_float_conversion(position.get("amount"), 0.0) > 0 else "BUY"
        self.cancel_symbol_protective_orders(symbol)
        metadata = {
            "entry_price": self.safe_float_conversion(position.get("entry_price"), 0.0),
            "close_reason": reason
        }
        return self.submit_order("position_manager", symbol, side, amount, reduce_only=True, metadata=metadata)

    def manage_open_positions(self):
        """Manage open positions and exit on moving-average reversal."""
        try:
            self.sync_positions()
            active_positions = self.trading_results.get("active_positions", {})
            if not active_positions:
                return
            for symbol, position in list(active_positions.items()):
                hold_ready = self.is_past_min_hold(symbol)
                if not hold_ready:
                    continue
                market_regime = self.analyze_market_regime(symbol)
                strategy = self.get_position_strategy(symbol)
                exit_reason = (
                    self.should_exit_position_ema21_trailing(position, market_regime) or
                    self.should_exit_position_ma(position, market_regime, strategy)
                )

                if exit_reason and hold_ready:
                    self.close_position(symbol, position, exit_reason)
            active_positions = self.trading_results.get("active_positions", {})
            if len(active_positions) > self.max_open_positions:
                excess = len(active_positions) - self.max_open_positions
                ranked = sorted(
                    active_positions.items(),
                    key=lambda item: self.safe_float_conversion(item[1].get("percentage"), 0.0)
                )
                for symbol, position in ranked[:excess]:
                    self.close_position(symbol, position, "position_limit")

        except Exception as e:
            self.log_system_error("position_management_error", str(e))

    def update_market_data(self):
        """Refresh cached market prices."""
        try:
            for symbol in self.valid_symbols[:10]:
                response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=3)
                if response.status_code == 200:
                    price_data = response.json()
                    self.current_prices[symbol] = float(price_data["price"])

            self.trading_results["market_data"] = self.current_prices.copy()

        except Exception as e:
            self.log_system_error("market_data_update_error", str(e))

    def display_status(self):
        """Status output removed by request."""
        return None

    def save_results(self):
        """Save trading results to disk."""
        try:
            self.refresh_pending_orders()
            self.recompute_trade_counters()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"completely_fixed_auto_strategy_trading_{timestamp}.json"
            cleaned_data = self.clean_data_for_json(self.trading_results)

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

            print(f"[INFO] Trading results saved: {filename}")

        except Exception as e:
            self.log_system_error("result_save_error", str(e))
            print(f"[ERROR] Result save error: {e}")

    def clean_data_for_json(self, data):
        """Prepare data for JSON serialization."""
        if isinstance(data, dict):
            return {k: self.clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_data_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    def periodic_sync(self):
        """Periodically synchronize positions and balance."""
        while self.running:
            try:
                self.refresh_pending_orders()
                self.sync_positions()
                self.sync_account_balance()
                self.recompute_trade_counters()
                self.trading_results["sync_status"] = "SYNCED"
                time.sleep(60)
            except Exception as e:
                self.log_system_error("periodic_sync_error", str(e))
                self.trading_results["sync_status"] = "SYNC_ERROR"
                time.sleep(60)

    def run_trading(self):
        """Run the main trading loop."""
        print("[INFO] Auto futures trading started")

        try:
            while datetime.now() < self.end_time and self.running:
                try:
                    self.trading_results["market_session"] = self.get_market_session()
                    self.refresh_symbol_universe()
                    self.update_market_data()
                    self.refresh_pending_orders()
                    self.manage_open_positions()

                    if self.can_open_new_positions():
                        for strategy_name in self.strategies:
                            if len(self.trading_results.get("active_positions", {})) >= self.max_open_positions:
                                break
                            self.execute_strategy_trade(strategy_name)
                    else:
                        self.trading_results["sync_status"] = "ACCOUNT_DATA_UNAVAILABLE"

                    time.sleep(30)

                except Exception as e:
                    self.log_system_error("trading_loop_error", str(e))
                    time.sleep(30)

        except KeyboardInterrupt:
            print("\n[WARN] Auto trading interrupted")
        except Exception as e:
            self.log_system_error("result_save_error", str(e))
            print(f"\n[ERROR] Trading runtime error: {e}")
        finally:
            self.running = False
            self.save_results()
            print("[INFO] Auto futures trading finished")

if __name__ == "__main__":
    trading = CompletelyFixedAutoStrategyFuturesTrading()
    trading.run_trading()
