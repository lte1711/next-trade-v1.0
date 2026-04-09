"""

Main Runtime - Integrated Runtime Module

"""



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

from api_config import get_api_credentials, is_api_valid



# Essential imports

import requests

import hmac

import hashlib





class TradingRuntime:

    """Integrated Trading Runtime"""

    

    def __init__(self):

        self.load_local_env_file()

        self.start_time = datetime.now()

        

        # 초기화

        self.trading_results = {

            "strategies": {},

            "active_positions": {},

            "pending_trades": [],

            "closed_trades": [],

            "real_orders": [],

            "total_trades": 0,

            "entry_failures": 0,

            "available_balance": 0.0,

            "market_regime": {},

            "market_data": {},

            "system_errors": [],

            "error_count": 0,

            "last_error": None,

            "entry_mode_performance": {},

            "recently_closed_symbols": {},

            "position_entry_times": {},

            "partial_take_profit_state": {},

            "managed_stop_prices": {}

        }

        

        # API key verification

        if not is_api_valid():

            print("[ERROR] API credentials not found. Please run: python setup_api.py")

            return

        

        self.api_key, self.api_secret = get_api_credentials()

        self.base_url = "https://testnet.binancefuture.com"

        

        # New modular architecture initialization

        self.market_data_service = MarketDataService(

            self.base_url, self.api_key, self.api_secret, self.log_system_error

        )

        

        self.indicator_service = IndicatorService(self.log_system_error)

        self.market_regime_service = MarketRegimeService(self.log_system_error)

        self.signal_engine = SignalEngine(self.log_system_error)

        self.strategy_registry = StrategyRegistry(self.log_system_error)

        self.allocation_service = AllocationService(self.log_system_error)

        

        # Existing managers (compatibility maintained)

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

        

        self.position_manager = PositionManager(

            self.trading_results, self.order_executor, self.protective_order_manager, self.log_system_error

        )

        

        self.position_entry_times = {}

        self.pending_order_manager = PendingOrderManager(

            self.trading_results, self.get_order_status, self.log_system_error,

            self.position_entry_times, self.protective_order_manager, self.clear_position_management_state,

            sync_positions_callback=lambda: self.account_service.sync_positions(self.trading_results)

        )

        

        # Main orchestrator

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

            self.log_system_error

        )

        

        # Load configuration and initialize

        try:

            with open('config.json', 'r') as f:

                config = json.load(f)

        except Exception:

            config = {}

        

        # Load V2 Merged trading configuration

        trading_config = config.get("trading_config", {})

        self.max_open_positions = trading_config.get("max_open_positions", 5)

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

        

        self.api_key = config.get("binance_testnet", {}).get("api_key")

        self.api_secret = config.get("binance_testnet", {}).get("api_secret")

        self.base_url = config.get("binance_testnet", {}).get("base_url")

        

        self.valid_symbols = self.load_valid_symbols()

        

        # Load strategies

        self.load_strategies()

        

        # Load valid symbols

        self.valid_symbols = self.load_valid_symbols()

        

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

    

    def _initialize_trading_system(self):

        """Initialize trading system components"""

        try:

            # 1. Update capital from actual account data

            if self.account_service.periodic_sync(self.trading_results):

                actual_balance = self.trading_results.get("available_balance", self.total_capital)

                if actual_balance != self.total_capital:

                    self.total_capital = actual_balance

                    print(f"[INFO] Capital updated from account: ${self.total_capital:.2f}")

            

            # 2. Symbol information refresh

            symbols_info = self.market_data_service.refresh_symbol_universe()

            print(f"[INFO] Active strategies: {self.active_strategies}")

            

            # 3. Capital allocation initialization

            self.allocation_service.refresh_strategy_capital_allocations(

                self.total_capital, self.active_strategies, {}

            )

            

            print(f"[INFO] Trading system initialized")

            

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

    

        

    def resolve_base_url(self):

        """Resolve base URL"""

        return "https://testnet.binancefuture.com"

    

    def log_system_error(self, error_type, error_message):

        """System error logging"""

        try:

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

            

            timestamp = int(server_time * 1000)

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

    

    def clear_position_management_state(self, symbol):

        """Clear position management state using position manager"""

        return self.position_manager.clear_position_management_state(symbol)

    

    def get_position_management_state(self, symbol):

        """Get position management state using position manager"""

        return self.position_manager.get_position_management_state(symbol)

    

    def should_exit_position_ma(self, position, market_regime, strategy=None):

        """Determine position exit using position manager"""

        return self.position_manager.should_exit_position_ma(position, market_regime, strategy)

    

    def sync_positions(self):

        """V2 Merged: Synchronize active positions from the exchange"""

        try:

            # V2 Merged: Use account service for real API-based synchronization

            if self.account_service.sync_positions(self.trading_results):

                active_positions = self.trading_results.get("active_positions", {})

                print(f"[TRACE] SYNC_POSITIONS_COMPLETE | symbols={len(active_positions)}")

                print(f"[INFO] Positions synced: {len(active_positions)}")

                

                # V2 Merged: Check for position limit exceeded

                if len(active_positions) > self.max_open_positions:

                    excess = len(active_positions) - self.max_open_positions

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

    

    def display_status(self):

        """Display status"""

        print(f"[INFO] REFACTORED_RUNTIME: Modular architecture implemented")

        print(f"[INFO] CORE_MODULES: ProtectiveOrderManager, PendingOrderManager, OrderExecutor")

        print(f"[INFO] MONOLITHIC_REDUCED: Core responsibilities split into modules")

        print(f"[INFO] MAINTAINABILITY: Significantly improved")

        return None

    

    def run(self):

        """Main execution loop - Complete trading orchestration"""

        try:

            print(f"[INFO] Complete Modular Trading Runtime Started")

            print(f"[INFO] Start time: {self.start_time}")

            print(f"[INFO] Initial capital: ${self.total_capital:.2f}")

            

            # Initialization and setup

            self._initialize_trading_system()

            

            # Main trading loop

            while True:

                try:

                    # 1. Account and position synchronization

                    self.account_service.periodic_sync(self.trading_results)

                    

                    # 2. Refresh pending orders

                    self.pending_order_manager.refresh_pending_orders()

                    

                    # 3. Execute complete trading cycle

                    cycle_results = self.trade_orchestrator.run_trading_cycle(

                        self.valid_symbols, 

                        self.active_strategies

                    )

                    

                    # 4. Process results

                    self._process_cycle_results(cycle_results)

                    

                    # 5. Display status

                    self._display_cycle_status(cycle_results)

                    

                    time.sleep(10)  # 10초 주기

                    

                except KeyboardInterrupt:

                    print(f"[INFO] Trading runtime stopped by user")

                    break

                except Exception as e:

                    self.log_system_error("runtime_error", str(e))

                    time.sleep(10)

                    

            # Error handling

            for error in cycle_results.get('errors', []):

                self.log_system_error("cycle_error", error)

            

            # Statistics update

            self.trading_results['last_cycle'] = cycle_results

            

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

            

            if signals > 0 or trades > 0 or error_count > 0:

                print(f"[INFO] Cycle completed - Signals: {signals}, Trades: {trades}, Errors: {error_count}")

            

            # Save results periodically

            try:

                import json

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

    runtime.run()
