"""Main Runtime - Integrated Runtime Module - FIXED VERSION"""

import sys
import os
import json
from datetime import datetime
import time

# Core module imports
from core.protective_order_manager import ProtectiveOrderManager
from core.pending_order_manager import PendingOrderManager
from core.order_executor import OrderExecutor
from core.numeric_utils import safe_float_conversion, round_to_step
from core.exchange_utils import get_server_time, get_symbol_info
from core.market_data_service import MarketDataService
from core.indicator_service import IndicatorService
from core.market_regime_service import MarketRegimeService
from core.signal_engine import SignalEngine
from core.strategy_registry import StrategyRegistry
from core.allocation_service import AllocationService
from core.position_manager import PositionManager
from core.account_service import AccountService
from core.trade_orchestrator import TradeOrchestrator
from core.partial_take_profit_manager import PartialTakeProfitManager
from api_config import get_api_credentials, is_api_valid

# Essential imports
import requests
import hmac
import hashlib


class TradingRuntime:
    """Integrated Trading Runtime - FIXED VERSION"""
    
    def __init__(self):
        self.load_local_env_file()
        self.start_time = datetime.now()
        self.initialized = False
        self._system_initialized_once = False
        self.runtime_status_path = os.path.join("runtime", "main_runtime_testnet_status.json")
        self._cycle_index = 0
        self._consecutive_runtime_errors = 0
        self._consecutive_cycle_errors = 0
        
        # 초기화
        self.trading_results = {
            "strategies": {},
            "active_positions": {},
            "pending_trades": [],
            "closed_trades": [],
            "real_orders": [],
            "realized_pnl_journal": [],
            "symbol_performance": {},
            "total_trades": 0,
            "entry_failures": 0,
            "available_balance": 0.0,
            "market_regime": {},
            "market_data": {},
            "system_errors": [],
            "operational_events": [],
            "error_count": 0,
            "last_error": None,
            "entry_mode_performance": {},
            "recently_closed_symbols": {},
            "position_entry_times": {},
            "position_state_journal": {},
            "partial_take_profit_state": {},
            "managed_stop_prices": {},
            "runtime_health": {}
        }
        self._load_persisted_trading_results()
        
        # Load configuration and initialize
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}

        # Resolve API credentials and runtime endpoint before service creation
        config_api_key = config.get("binance_testnet", {}).get("api_key", "")
        config_api_secret = config.get("binance_testnet", {}).get("api_secret", "")
        config_base_url = config.get("binance_testnet", {}).get("base_url", "")

        runtime_api_key, runtime_api_secret = get_api_credentials()
        self.api_key = runtime_api_key or config_api_key
        self.api_secret = runtime_api_secret or config_api_secret
        self.base_url = config_base_url or "https://testnet.binancefuture.com"
        self.execution_mode = config.get("binance_execution_mode", "testnet")
        self.simulation_mode = bool(config.get("simulation_mode", False))
        self.force_real_exchange = bool(config.get("force_real_exchange", True))

        # API key verification
        if not self.api_key or not self.api_secret or not is_api_valid():
            print("[ERROR] API credentials not found. Please run: python setup_api.py")
            return
        
        # Load V2 Merged trading configuration
        trading_config = config.get("trading_config", {})
        self.max_open_positions = trading_config.get("max_open_positions", 10)
        self.fast_entry_enabled = trading_config.get("fast_entry_enabled", True)
        self.partial_tp1_pct = trading_config.get("partial_tp1_pct", 0.8)
        self.fast_tp1_pct = trading_config.get("fast_tp1_pct", 0.5)
        self.fast_tp2_pct = trading_config.get("fast_tp2_pct", 1.2)
        self.partial_tp2_pct = trading_config.get("partial_tp2_pct", 2.0)
        self.stop_loss_pct = trading_config.get("stop_loss_pct", 0.02)
        self.take_profit_pct = trading_config.get("take_profit_pct", 0.04)
        self.position_hold_minutes = trading_config.get("position_hold_minutes", 30)
        self.max_position_size_usdt = trading_config.get("max_position_size_usdt", 1000.0)
        
        # V2 Merged: Additional position management settings
        self.position_sync_interval = trading_config.get("position_sync_interval", 5)
        self.position_limit_check = trading_config.get("position_limit_check", True)
        self.excess_position_close = trading_config.get("excess_position_close", True)
        
        # Load API configuration
        api_config = config.get("api_config", {})
        self.recv_window = api_config.get("recv_window", 5000)
        self.min_volume_threshold = api_config.get("min_volume_threshold", 1000000)

        # New modular architecture initialization
        self.market_data_service = MarketDataService(self.base_url)
        self.indicator_service = IndicatorService()
        self.market_regime_service = MarketRegimeService()
        self.signal_engine = SignalEngine()
        self.strategy_registry = StrategyRegistry()
        self.allocation_service = AllocationService()

        self.order_executor = OrderExecutor(
            self.api_key, self.api_secret, self.base_url, self.trading_results,
            self.get_symbol_info, self.log_system_error, safe_float_conversion, round_to_step,
            capital_getter=lambda: self.total_capital
        )

        self.protective_order_manager = ProtectiveOrderManager(
            self.api_key, self.api_secret, self.base_url, self.trading_results,
            self.get_symbol_info, self.log_system_error
        )

        self.account_service = AccountService(
            self.base_url, self.api_key, self.api_secret, self.log_system_error
        )
        self.account_service.recv_window = self.recv_window

        self.position_manager = PositionManager(
            self.trading_results, self.order_executor, self.protective_order_manager, self.log_system_error
        )

        self.partial_take_profit_manager = PartialTakeProfitManager(
            self.trading_results,
            self.log_system_error,
        )
        self.position_entry_times = self.trading_results["position_entry_times"]
        self.pending_order_manager = PendingOrderManager(
            self.trading_results, self.get_order_status, self.log_system_error,
            self.position_entry_times, self.protective_order_manager, self.clear_position_management_state,
            sync_positions_callback=lambda: self.account_service.sync_positions(self.trading_results)
        )

        self.valid_symbols = self.load_valid_symbols()
        
        # Load strategies
        self.load_strategies()

        self.trade_orchestrator = TradeOrchestrator(
            self.trading_results,
            self.market_data_service,
            self.indicator_service,
            self.market_regime_service,
            self.signal_engine,
            self.strategy_registry,
            self.allocation_service,
            self.position_manager,
            self.order_executor,
            self.account_service,
            self.protective_order_manager,
            self.partial_take_profit_manager,
            self.log_system_error
        )
        
        # Initial capital from real-time API data only
        try:
            # Get real-time account balance
            if self.account_service.periodic_sync(self.trading_results):
                actual_balance = self.trading_results.get("available_balance", 0.0)
                if actual_balance > 0:
                    self.total_capital = actual_balance
                else:
                    print(f"[ERROR] Failed to get real-time balance, using 0.0")
                    self.total_capital = 0.0
            else:
                print(f"[ERROR] Failed to sync account, using 0.0")
                self.total_capital = 0.0
        except Exception as e:
            print(f"[ERROR] Exception getting real-time balance: {e}, using 0.0")
            self.total_capital = 0.0
        
        self.trading_results["available_balance"] = self.total_capital
        
        # Initialize trading components (after all attributes are set)
        self._initialize_trading_system()
        self.initialized = True
    
    def _initialize_trading_system(self):
        """Initialize trading system components"""
        try:
            if self._system_initialized_once:
                return

            # 1. Update capital from actual account data
            if self.account_service.periodic_sync(self.trading_results):
                actual_balance = self.trading_results.get("available_balance", self.total_capital)
                if actual_balance != self.total_capital:
                    self.total_capital = actual_balance
                    print(f"[INFO] Capital updated from account: ${self.total_capital:.2f}")
            
            # 2. Refresh valid symbols
            if not self.valid_symbols:
                refreshed_symbols = self.load_valid_symbols()
                if refreshed_symbols:
                    self.valid_symbols = refreshed_symbols
            print(f"[INFO] Active strategies: {self.active_strategies}")
            
            # 3. Capital allocation initialization
            self.allocation_service.refresh_strategy_capital_allocations(
                self.total_capital, self.active_strategies, {}
            )
            
            print(f"[INFO] Trading system initialized")
            self._system_initialized_once = True
            
        except Exception as e:
            self.log_system_error("system_init_error", str(e))
    
    def load_local_env_file(self):
        """Load environment configuration file"""
        try:
            if os.path.exists('.env'):
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            if key.strip() == 'BINANCE_API_KEY':
                                self.api_key = value.strip()
                            elif key.strip() == 'BINANCE_API_SECRET':
                                self.api_secret = value.strip()
        except Exception:
            pass

    def _load_persisted_trading_results(self):
        """Restore persisted runtime state that helps restart resilience."""
        try:
            if not os.path.exists("trading_results.json"):
                return

            with open("trading_results.json", "r", encoding="utf-8") as file_handle:
                persisted = json.load(file_handle)

            for key in [
                "real_orders",
                "closed_trades",
                "realized_pnl_journal",
                "recently_closed_symbols",
                "position_entry_times",
                "position_state_journal",
                "partial_take_profit_state",
                "managed_stop_prices",
                "operational_events",
                "symbol_performance",
            ]:
                persisted_value = persisted.get(key)
                if isinstance(self.trading_results.get(key), dict) and isinstance(persisted_value, dict):
                    self.trading_results[key].update(persisted_value)
                elif isinstance(self.trading_results.get(key), list) and isinstance(persisted_value, list):
                    self.trading_results[key] = persisted_value[-500:]

            if persisted.get("active_positions"):
                self.trading_results["active_positions"] = persisted.get("active_positions", {})
        except Exception:
            pass
    def log_system_error(self, error_type, error_message):
        """System error logging"""
        try:
            if error_type == "order_preflight_blocked":
                event_record = {
                    "timestamp": datetime.now().isoformat(),
                    "type": error_type,
                    "message": error_message
                }
                self.trading_results.setdefault("operational_events", []).append(event_record)
                print(f"[INFO] {error_type} - {error_message}")
                return

            error_record = {
                "timestamp": datetime.now().isoformat(),
                "type": error_type,
                "message": error_message
            }
            self.trading_results.setdefault("system_errors", []).append(error_record)
            self.trading_results["error_count"] = self.trading_results.get("error_count", 0) + 1
            self.trading_results["last_error"] = error_record
            
            print(f"[ERROR] {error_type} - {error_message}")
        except Exception:
            pass

    def log_operational_event(self, event_type, message, details=None):
        """Record non-fatal runtime events without treating them as system errors."""
        try:
            event_record = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "message": message,
                "details": details or {}
            }
            events = self.trading_results.setdefault("operational_events", [])
            events.append(event_record)
            self.trading_results["operational_events"] = events[-500:]
            print(f"[INFO] {event_type} - {message}")
        except Exception:
            pass

    def _persist_runtime_status(self, status="running", extra=None):
        """Write a small heartbeat file so ops checks can see whether the loop is progressing."""
        try:
            os.makedirs(os.path.dirname(self.runtime_status_path), exist_ok=True)
            payload = {
                "status": status,
                "pid": os.getpid(),
                "started_at": self.start_time.isoformat(),
                "safety": {
                    "base_url": self.base_url,
                    "execution_mode": self.execution_mode,
                    "simulation_mode": self.simulation_mode,
                    "force_real_exchange": self.force_real_exchange,
                    "max_open_positions": self.max_open_positions,
                },
                "initialized": self.initialized,
                "active_strategies": self.active_strategies,
                "valid_symbols_count": len(self.valid_symbols or []),
                "max_open_positions": self.max_open_positions,
                "available_balance": self.trading_results.get("available_balance"),
                "cycle_index": self._cycle_index,
                "consecutive_runtime_errors": self._consecutive_runtime_errors,
                "consecutive_cycle_errors": self._consecutive_cycle_errors,
                "runtime_health": self.trading_results.get("runtime_health", {}),
                "updated_at": datetime.now().isoformat(),
            }
            if extra:
                payload.update(extra)
            with open(self.runtime_status_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception as e:
            print(f"[ERROR] runtime_status_write - {e}")

    def _run_continuity_health_check(self, phase):
        """Verify core runtime prerequisites and repair recoverable issues before continuing."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "ok": True,
            "problems": [],
            "actions": [],
            "cycle_index": self._cycle_index,
            "valid_symbols_count": len(self.valid_symbols or []),
            "active_strategies": list(self.active_strategies or []),
            "active_positions_count": len(self.trading_results.get("active_positions", {}) or {}),
            "pending_trades_count": len(self.trading_results.get("pending_trades", []) or []),
            "available_balance": self.trading_results.get("available_balance"),
            "consecutive_runtime_errors": self._consecutive_runtime_errors,
            "consecutive_cycle_errors": self._consecutive_cycle_errors,
        }

        try:
            if not self.valid_symbols:
                health["ok"] = False
                health["problems"].append("valid_symbols_empty")
                refreshed_symbols = self.load_valid_symbols()
                if refreshed_symbols:
                    self.valid_symbols = refreshed_symbols
                    health["actions"].append("valid_symbols_reloaded")
                    health["valid_symbols_count"] = len(self.valid_symbols)

            if not self.active_strategies:
                health["ok"] = False
                health["problems"].append("active_strategies_empty")
                self.load_strategies()
                health["actions"].append("strategies_reloaded")
                health["active_strategies"] = list(self.active_strategies or [])

            if self.trading_results.get("available_balance") is None:
                health["ok"] = False
                health["problems"].append("available_balance_missing")
                if self.account_service.periodic_sync(self.trading_results):
                    health["actions"].append("account_resynced")
                    health["available_balance"] = self.trading_results.get("available_balance")

            if self._consecutive_runtime_errors >= 3:
                health["ok"] = False
                health["problems"].append("consecutive_runtime_errors_high")
                try:
                    self.account_service.sync_positions(self.trading_results)
                    self.pending_order_manager.refresh_pending_orders()
                    health["actions"].append("positions_and_pending_orders_resynced")
                except Exception as e:
                    health["problems"].append(f"recovery_sync_failed:{e}")

            if self._consecutive_cycle_errors >= 3:
                health["ok"] = False
                health["problems"].append("consecutive_cycle_errors_high")
                try:
                    self.account_service.sync_positions(self.trading_results)
                    health["actions"].append("positions_resynced_after_cycle_errors")
                except Exception as e:
                    health["problems"].append(f"cycle_error_recovery_failed:{e}")

            self.trading_results["runtime_health"] = health
            if not health["ok"] or health["actions"]:
                self.log_operational_event("runtime_health_check", "continuity check completed", health)
            return health
        except Exception as e:
            health["ok"] = False
            health["problems"].append(f"health_check_error:{e}")
            self.trading_results["runtime_health"] = health
            self.log_system_error("runtime_health_check", str(e))
            return health
    
    def load_strategies(self):
        """Load strategies"""
        self.trading_results["strategies"] = {
            "ma_trend_follow": {
                "name": "MA Trend Following",
                "enabled": True,
                "stop_loss_pct": self.stop_loss_pct,
                "take_profit_pct": self.take_profit_pct,
                "position_hold_minutes": self.position_hold_minutes,
                "max_position_size_usdt": self.max_position_size_usdt
            },
            "ema_crossover": {
                "name": "EMA Crossover",
                "enabled": True,
                "stop_loss_pct": self.stop_loss_pct * 0.75,  # 75% of base stop loss
                "take_profit_pct": self.take_profit_pct * 0.75,  # 75% of base take profit
                "position_hold_minutes": self.position_hold_minutes,
                "max_position_size_usdt": self.max_position_size_usdt * 0.8  # 80% of base size
            }
        }
        
        # Set active strategies
        self.active_strategies = [s for s in self.trading_results["strategies"].keys() 
                                if self.trading_results["strategies"][s].get("enabled", False)]
    
    def load_valid_symbols(self):
        """Load valid symbols using market data service"""
        try:
            # V2 Merged: Use market data service for symbol ranking
            dynamic_symbols = self.market_data_service.get_available_symbols()
            if dynamic_symbols:
                print(f"[INFO] Loaded {len(dynamic_symbols)} dynamic symbols")
                return [s['symbol'] for s in dynamic_symbols]
            else:
                print(f"[ERROR] No symbols available from dynamic ranking")
                return []
        except Exception as e:
            print(f"[ERROR] Failed to load symbols: {e}")
            return []
    
    def get_symbol_info(self, symbol):
        """Get symbol information"""
        return get_symbol_info(self.base_url, self.api_key, self.api_secret, symbol)
    
    def get_order_status(self, symbol, order_id):
        """Get order status"""
        try:
            server_time = get_server_time(self.base_url)
            if not server_time:
                return None
            
            timestamp = int(server_time)
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": timestamp,
                "recvWindow": 5000
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    def cancel_order(self, symbol, order_id):
        """Cancel a standard futures order"""
        return self.order_executor.cancel_order(symbol, order_id)
    
    def clear_position_management_state(self, symbol):
        """Clear position management state across managers"""
        self.position_manager.clear_position_management_state(symbol)
        self.partial_take_profit_manager.clear_position_management_state(symbol)
        self.trading_results.get("position_state_journal", {}).pop(symbol, None)
        return True
    
    def get_position_management_state(self, symbol):
        """Get position management state using position manager"""
        return self.position_manager.get_position_management_state(symbol)
    
    def should_exit_position_ma(self, position, market_regime, strategy=None):
        """Determine position exit using position manager"""
        return self.position_manager.should_exit_position_ma(position, market_regime, strategy)
    
    def sync_positions(self):
        """V2 Merged: Synchronize active positions from exchange"""
        try:
            # V2 Merged: Use account service for real API-based synchronization
            if self.account_service.sync_positions(self.trading_results):
                active_positions = self.trading_results.get("active_positions", {})
                self._rehydrate_position_metadata(active_positions)
                self._restore_protective_state(active_positions)
                print(f"[TRACE] SYNC_POSITIONS_COMPLETE | symbols={len(active_positions)}")
                print(f"[INFO] Positions synced: {len(active_positions)}")
                
                dynamic_limit = self.trading_results.get("dynamic_position_limit", {}) or {}
                active_position_limit = int(dynamic_limit.get("limit") or self.max_open_positions)

                # V2 Merged: Check for position limit exceeded
                if len(active_positions) > active_position_limit:
                    excess = len(active_positions) - active_position_limit
                    print(f"[WARN] POSITION_LIMIT_EXCEEDED | excess={excess}")
                    
                    # Sort by performance and close worst performing
                    sorted_positions = sorted(
                        active_positions.items(),
                        key=lambda item: abs(item[1].get("percentage", 0.0))
                    )
                    
                    for symbol, position in sorted_positions[:excess]:
                        print(f"[INFO] CLOSING_EXCESS_POSITION | {symbol}")
                        # Note: Actual closing logic would be handled by position manager
                
                return True
            else:
                print(f"[ERROR] Position sync failed")
                return False
                
        except Exception as e:
            self.log_system_error("sync_positions_error", str(e))
            return False

    def _rehydrate_position_metadata(self, active_positions):
        """Restore local position metadata from recent trade records after a restart."""
        try:
            if not active_positions:
                return

            position_journal = self.trading_results.get("position_state_journal", {})
            recent_orders = list(reversed(self.trading_results.get("real_orders", [])))
            for symbol, position in active_positions.items():
                journal_entry = position_journal.get(symbol, {})
                if journal_entry:
                    position["strategy"] = position.get("strategy") or journal_entry.get("strategy")
                    position["entry_time"] = position.get("entry_time") or journal_entry.get("entry_time")
                    position["signal_confidence"] = position.get("signal_confidence") or journal_entry.get("signal_confidence")
                    if position.get("stop_loss_pct") is None:
                        position["stop_loss_pct"] = journal_entry.get("stop_loss_pct")
                    if position.get("take_profit_pct") is None:
                        position["take_profit_pct"] = journal_entry.get("take_profit_pct")
                    for metadata_key in ["allocation_context", "position_amount_usdt", "risk_amount_usdt"]:
                        if position.get(metadata_key) is None and journal_entry.get(metadata_key) is not None:
                            position[metadata_key] = journal_entry.get(metadata_key)
                    if symbol not in self.position_entry_times and journal_entry.get("entry_time"):
                        self.position_entry_times[symbol] = journal_entry.get("entry_time")

                if (
                    position.get("strategy")
                    and position.get("entry_time")
                    and position.get("stop_loss_pct") is not None
                    and position.get("take_profit_pct") is not None
                ):
                    continue

                for order in recent_orders:
                    if order.get("symbol") != symbol or order.get("reduce_only"):
                        continue
                    if order.get("status") not in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                        continue

                    position["strategy"] = position.get("strategy") or order.get("strategy")
                    position["entry_time"] = position.get("entry_time") or order.get("timestamp")
                    position["signal_confidence"] = position.get("signal_confidence") or order.get("signal_confidence")
                    if position.get("stop_loss_pct") is None:
                        position["stop_loss_pct"] = order.get("stop_loss_pct")
                    if position.get("take_profit_pct") is None:
                        position["take_profit_pct"] = order.get("take_profit_pct")
                    for metadata_key in ["allocation_context", "position_amount_usdt", "risk_amount_usdt"]:
                        if position.get(metadata_key) is None and order.get(metadata_key) is not None:
                            position[metadata_key] = order.get(metadata_key)
                    if symbol not in self.position_entry_times and order.get("timestamp"):
                        self.position_entry_times[symbol] = order.get("timestamp")
                    position_journal[symbol] = {
                        "strategy": position.get("strategy"),
                        "entry_time": position.get("entry_time"),
                        "signal_confidence": position.get("signal_confidence"),
                        "stop_loss_pct": position.get("stop_loss_pct"),
                        "take_profit_pct": position.get("take_profit_pct"),
                        "allocation_context": position.get("allocation_context"),
                        "position_amount_usdt": position.get("position_amount_usdt"),
                        "risk_amount_usdt": position.get("risk_amount_usdt"),
                        "entry_price": position.get("entry_price"),
                        "side": position.get("side"),
                    }
                    break

                if position.get("strategy") and position.get("entry_time"):
                    continue

                exchange_order = self._fetch_recent_exchange_entry_order(symbol)
                if not exchange_order:
                    continue

                position["strategy"] = position.get("strategy") or exchange_order.get("strategy")
                position["entry_time"] = position.get("entry_time") or exchange_order.get("timestamp")
                position["signal_confidence"] = position.get("signal_confidence") or exchange_order.get("signal_confidence")
                if position.get("stop_loss_pct") is None:
                    position["stop_loss_pct"] = exchange_order.get("stop_loss_pct")
                if position.get("take_profit_pct") is None:
                    position["take_profit_pct"] = exchange_order.get("take_profit_pct")
                if symbol not in self.position_entry_times and exchange_order.get("timestamp"):
                    self.position_entry_times[symbol] = exchange_order.get("timestamp")

                position_journal[symbol] = {
                    "strategy": position.get("strategy"),
                    "entry_time": position.get("entry_time"),
                    "signal_confidence": position.get("signal_confidence"),
                    "stop_loss_pct": position.get("stop_loss_pct"),
                    "take_profit_pct": position.get("take_profit_pct"),
                    "entry_price": position.get("entry_price"),
                    "side": position.get("side"),
                }
        except Exception as e:
            self.log_system_error("rehydrate_position_metadata", str(e))

    def _fetch_recent_exchange_entry_order(self, symbol):
        """Fetch the latest non-reduce-only exchange order as a metadata fallback."""
        try:
            server_time = get_server_time(self.base_url)
            if not server_time:
                return None

            params = {
                "symbol": symbol,
                "limit": 20,
                "timestamp": int(server_time),
                "recvWindow": self.recv_window,
            }
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            url = f"{self.base_url}/fapi/v1/allOrders?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None

            for order in reversed(response.json()):
                if order.get("reduceOnly"):
                    continue
                if order.get("status") not in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                    continue

                side = order.get("side")
                return {
                    "strategy": "ma_trend_follow",
                    "timestamp": int(order.get("time", 0)) or None,
                    "signal_confidence": None,
                    "stop_loss_pct": 0.03,
                    "take_profit_pct": 0.045,
                    "side": "LONG" if side == "BUY" else "SHORT",
                }
        except Exception:
            return None
        return None

    def _restore_protective_state(self, active_positions):
        """Rebuild managed stop prices from live algo orders after a restart."""
        try:
            managed_stop_prices = self.trading_results.setdefault("managed_stop_prices", {})
            for symbol in list(managed_stop_prices.keys()):
                if symbol not in active_positions:
                    managed_stop_prices.pop(symbol, None)

            for symbol in active_positions.keys():
                if symbol in managed_stop_prices:
                    continue

                open_orders = self.protective_order_manager.get_open_orders(symbol)
                for order in open_orders:
                    order_type = order.get("orderType") or order.get("type")
                    if order_type != "STOP_MARKET":
                        continue
                    trigger_price = safe_float_conversion(order.get("triggerPrice"), 0.0)
                    if trigger_price > 0:
                        managed_stop_prices[symbol] = trigger_price
                        active_positions[symbol]["managed_stop_price"] = trigger_price
                        break
        except Exception as e:
            self.log_system_error("restore_protective_state", str(e))
    
    def run(self):
        """Main execution loop - Complete trading orchestration"""
        try:
            if not self.initialized:
                self.log_system_error("runtime_not_initialized", "Trading runtime was not initialized successfully")
                return
            print(f"[INFO] Complete Modular Trading Runtime Started")
            print(f"[INFO] Start time: {self.start_time}")
            print(f"[INFO] Initial capital: ${self.total_capital:.2f}")
            
            cycle_results = {
                'signals_generated': 0,
                'trades_executed': 0,
                'errors': []
            }
            
            # Main trading loop
            while True:
                try:
                    self._cycle_index += 1
                    self._run_continuity_health_check("pre_cycle")
                    self._persist_runtime_status("running")

                    # 1. Account and position synchronization
                    self.account_service.periodic_sync(self.trading_results)
                    
                    # 2. Refresh pending orders
                    self.pending_order_manager.refresh_pending_orders()
                    
                    # 3. Execute complete trading cycle
                    cycle_results = self.trade_orchestrator.run_trading_cycle(
                        self.valid_symbols, 
                        self.active_strategies
                    )
                    self._persist_runtime_status("processing_cycle_results", {
                        "last_cycle_signals": cycle_results.get("signals_generated", 0),
                        "last_cycle_trades": cycle_results.get("trades_executed", 0),
                        "last_cycle_errors": len(cycle_results.get("errors", []) or []),
                    })
                    
                    # 4. Process results
                    self._process_cycle_results(cycle_results)
                    self._consecutive_runtime_errors = 0
                    
                    # 5. Display status
                    self._display_cycle_status(cycle_results)
                    self._run_continuity_health_check("post_cycle")
                    self._persist_runtime_status("running")
                    
                    time.sleep(10)  # 10초 주기
                    
                except KeyboardInterrupt:
                    print(f"[INFO] Trading runtime stopped by user")
                    break
                except Exception as e:
                    self._consecutive_runtime_errors += 1
                    self.log_system_error("runtime_error", str(e))
                    self._run_continuity_health_check("runtime_exception")
                    self._persist_runtime_status("degraded", {"last_exception": str(e)})
                    time.sleep(10)
            
        except Exception as e:
            self.log_system_error("cycle_results_process", str(e))
    
    def _process_cycle_results(self, cycle_results):
        """Process cycle results with robust error handling"""
        try:
            # Validate cycle results
            if not isinstance(cycle_results, dict):
                self.log_system_error("invalid_cycle_results", f"Expected dict, got {type(cycle_results)}")
                return
            
            # Safe update with validation
            for key, value in cycle_results.items():
                if key in self.trading_results and isinstance(self.trading_results[key], dict) and isinstance(value, dict):
                    self.trading_results[key].update(value)
                else:
                    self.trading_results[key] = value
            
            # Extract stats safely
            signals = cycle_results.get('signals_generated', 0)
            trades = cycle_results.get('trades_executed', 0)
            errors = cycle_results.get('errors', [])
            error_count = len(errors) if isinstance(errors, list) else 0
            if error_count > 0:
                self._consecutive_cycle_errors += 1
            else:
                self._consecutive_cycle_errors = 0
            
            if signals > 0 or trades > 0 or error_count > 0:
                print(f"[INFO] Cycle completed - Signals: {signals}, Trades: {trades}, Errors: {error_count}")

            self.trading_results["runtime_health"] = {
                **(self.trading_results.get("runtime_health", {}) or {}),
                "phase": "reduce_only_reconciliation",
                "last_cycle_signals": signals,
                "last_cycle_trades": trades,
                "last_cycle_errors": error_count,
                "updated_at": datetime.now().isoformat(),
            }
            self._persist_runtime_status("processing_reduce_only_reconciliation")
            reconciliation_summary = self.order_executor.reconcile_pending_reduce_only_fills()
            if reconciliation_summary.get("filled") or reconciliation_summary.get("terminal"):
                self.trading_results["last_reduce_only_reconciliation"] = reconciliation_summary
                print(f"[INFO] Reduce-only reconciliation: {reconciliation_summary}")

            self.trading_results["runtime_health"] = {
                **(self.trading_results.get("runtime_health", {}) or {}),
                "phase": "exchange_realized_pnl_sync",
                "updated_at": datetime.now().isoformat(),
            }
            self._persist_runtime_status("processing_exchange_realized_pnl_sync")
            exchange_pnl_summary = self.order_executor.sync_exchange_realized_pnl()
            if exchange_pnl_summary.get("recorded") or exchange_pnl_summary.get("errors"):
                self.trading_results["last_exchange_realized_pnl_sync"] = exchange_pnl_summary
                print(f"[INFO] Exchange realized PnL sync: {exchange_pnl_summary}")

            # Protective orders can close positions while a long signal cycle is
            # running. Sync again before persisting so local active_positions
            # does not retain exchange-closed symbols until the next cycle.
            self.trading_results["runtime_health"] = {
                **(self.trading_results.get("runtime_health", {}) or {}),
                "phase": "final_position_sync",
                "updated_at": datetime.now().isoformat(),
            }
            self._persist_runtime_status("processing_final_position_sync")
            self.account_service.sync_positions(self.trading_results)
            self.trading_results["runtime_health"] = {
                **(self.trading_results.get("runtime_health", {}) or {}),
                "last_cycle_processed_at": datetime.now().isoformat(),
                "last_cycle_signals": signals,
                "last_cycle_trades": trades,
                "last_cycle_errors": error_count,
                "consecutive_cycle_errors": self._consecutive_cycle_errors,
                "consecutive_runtime_errors": self._consecutive_runtime_errors,
            }
            
            # Save results periodically
            try:
                with open('trading_results.json', 'w') as f:
                    json.dump(self.trading_results, f, indent=2, default=str)
            except Exception as save_error:
                self.log_system_error("save_results", str(save_error))
            
        except Exception as e:
            self.log_system_error("cycle_results_process", str(e))
    
    def _display_cycle_status(self, cycle_results):
        """Display cycle status"""
        try:
            signals = cycle_results.get('signals_generated', 0)
            trades = cycle_results.get('trades_executed', 0)
            errors = len(cycle_results.get('errors', []))
            
            if signals > 0 or trades > 0 or errors > 0:
                print(f"[CYCLE] Signals: {signals}, Trades: {trades}, Errors: {errors}")
                
        except Exception as e:
            self.log_system_error("cycle_status_display", str(e))


if __name__ == "__main__":
    runtime = TradingRuntime()
    if runtime.initialized:
        runtime.run()
    else:
        sys.exit(1)
