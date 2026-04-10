"""
Trading Runtime - Main Trading Execution Engine
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List

from core.account_service import AccountService
from core.allocation_service import AllocationService
from core.market_data_service import MarketDataService
from core.indicator_service import IndicatorService
from core.market_regime_service import MarketRegimeService
from core.signal_engine import SignalEngine
from core.strategy_registry import StrategyRegistry
from core.trade_orchestrator import TradeOrchestrator
from core.position_manager import PositionManager
from core.order_executor import OrderExecutor
from core.protective_order_manager import ProtectiveOrderManager
from core.pending_order_manager import PendingOrderManager
from api_config import get_api_credentials, is_api_valid


class TradingRuntime:
    """Main Trading Runtime - Orchestrates all trading activities"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.trading_results = {
            "strategies": {},
            "active_positions": {},
            "pending_trades": [],
            "closed_trades": [],
            "real_orders": [],
            "available_balance": 0.0,
            "total_capital": 0.0,
            "last_error": None,
            "entry_mode_performance": {},
            "recently_closed_symbols": {},
            "position_entry_times": {},
            "partial_take_profit_state": {},
            "managed_stop_prices": {}
        }
        
        # Load configuration
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception:
            config = {}
        
        # Load API configuration
        api_config = config.get("binance_testnet", {})
        self.api_key = api_config.get("api_key")
        self.api_secret = api_config.get("api_secret")
        self.base_url = api_config.get("base_url", "https://testnet.binancefuture.com")
        
        # Load trading configuration
        trading_config = config.get("trading_config", {})
        self.max_open_positions = trading_config.get("max_open_positions", 10)
        self.position_sync_interval = trading_config.get("position_sync_interval", 5)
        self.position_limit_check = trading_config.get("position_limit_check", True)
        self.excess_position_close = trading_config.get("excess_position_close", True)
        
        # Initialize core services
        self._initialize_services()
        
        # Load strategies and symbols
        self._load_trading_configuration()
    
    def _initialize_services(self):
        """Initialize all core trading services"""
        # Core services
        self.account_service = AccountService(
            self.base_url, self.api_key, self.api_secret, self.log_system_error
        )
        
        self.market_data_service = MarketDataService(
            self.base_url, self.api_key, self.api_secret, self.log_system_error
        )
        
        self.indicator_service = IndicatorService(self.log_system_error)
        self.market_regime_service = MarketRegimeService(self.log_system_error)
        
        # Strategy and execution services
        self.strategy_registry = StrategyRegistry(self.log_system_error)
        self.allocation_service = AllocationService(self.log_system_error)
        self.signal_engine = SignalEngine(
            self.indicator_service, self.market_regime_service, self.log_system_error
        )
        
        # Execution services
        self.order_executor = OrderExecutor(
            self.api_key, self.api_secret, self.base_url, self.trading_results,
            self.get_symbol_info, self.log_system_error, self.safe_float_conversion,
            self.round_to_step, self.get_total_capital
        )
        
        self.protective_order_manager = ProtectiveOrderManager(
            self.base_url, self.api_key, self.api_secret, self.log_system_error
        )
        
        self.position_manager = PositionManager(
            self.trading_results, self.order_executor, self.protective_order_manager, self.log_system_error
        )
        
        self.pending_order_manager = PendingOrderManager(
            self.trading_results, self.get_order_status, self.log_system_error,
            self.position_entry_times, self.protective_order_manager, 
            self.clear_position_management_state,
            sync_positions_callback=lambda: self.account_service.sync_positions(self.trading_results)
        )
        
        # Main orchestrator
        self.trade_orchestrator = TradeOrchestrator(
            self.trading_results, self.market_data_service, self.indicator_service,
            self.market_regime_service, self.signal_engine, self.strategy_registry,
            self.allocation_service, self.position_manager, self.order_executor,
            self.account_service, self.protective_order_manager, self.pending_order_manager,
            self.log_system_error
        )
        
        # Position entry times
        self.position_entry_times = {}
    
    def _load_trading_configuration(self):
        """Load strategies and symbols"""
        try:
            # Load strategies
            strategies = self.strategy_registry.get_available_strategies()
            for strategy_name in strategies:
                strategy_config = self.strategy_registry.get_strategy_profile(strategy_name)
                self.trading_results["strategies"][strategy_name] = {
                    "enabled": True,
                    "config": strategy_config,
                    "performance": {"win_rate": 0.0, "avg_return": 0.0, "total_trades": 0},
                    "last_signal": None,
                    "last_trade": None
                }
            
            # Set active strategies
            self.active_strategies = [s for s in self.trading_results["strategies"].keys() 
                                    if self.trading_results["strategies"][s].get("enabled", False)]
            
            # Load symbols (using dynamic ranking)
            self.valid_symbols = self._load_valid_symbols()
            
            # Initialize capital
            self.total_capital = self.account_service.get_total_balance() or 10000.0
            self.trading_results["total_capital"] = self.total_capital
            
            print(f"[INFO] Initialized {len(self.active_strategies)} strategies")
            print(f"[INFO] Loaded {len(self.valid_symbols)} symbols")
            print(f"[INFO] Initial capital: ${self.total_capital:.2f}")
            
        except Exception as e:
            self.log_system_error("initialization_error", str(e))
    
    def _load_valid_symbols(self):
        """Load valid symbols using V2 Merged dynamic ranking"""
        try:
            dynamic_symbols = self._get_available_symbols()
            if dynamic_symbols:
                print(f"[INFO] Loaded {len(dynamic_symbols)} dynamic symbols")
                return [s['symbol'] for s in dynamic_symbols]
            else:
                print(f"[ERROR] No symbols available from dynamic ranking")
                return []
        except Exception as e:
            print(f"[ERROR] Failed to load symbols: {e}")
            return []
    
    def _get_available_symbols(self):
        """V2 Merged: Fetch ranked tradable symbols"""
        try:
            import requests
            url = f"{self.base_url}/fapi/v1/exchangeInfo"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                exchange_info = response.json()
                symbols = []
                
                for symbol_info in exchange_info['symbols']:
                    if (symbol_info['status'] == 'TRADING' and 
                        symbol_info['quoteAsset'] == 'USDT' and
                        symbol_info['contractType'] == 'PERPETUAL'):
                        
                        symbols.append({
                            'symbol': symbol_info['symbol'],
                            'base_asset': symbol_info['baseAsset'],
                            'quote_asset': symbol_info['quoteAsset'],
                            'status': symbol_info['status'],
                            'contract_type': symbol_info['contractType']
                        })
                
                # Rank symbols by liquidity
                ranked_symbols = self._rank_symbols_by_liquidity(symbols)
                return ranked_symbols[:50]
            else:
                print(f"[ERROR] Failed to fetch symbols: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] get_available_symbols: {e}")
            return []
    
    def _rank_symbols_by_liquidity(self, symbols):
        """V2 Merged: Rank symbols by liquidity and volatility"""
        try:
            import requests
            
            url = f"{self.base_url}/fapi/v1/ticker/24hr"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                ticker_data = response.json()
                volume_map = {}
                
                for ticker in ticker_data:
                    symbol = ticker['symbol']
                    volume = float(ticker['volume']) * float(ticker['lastPrice'])
                    price_change_percent = abs(float(ticker['priceChangePercent']))
                    
                    volume_map[symbol] = {
                        'volume': volume,
                        'volatility': price_change_percent,
                        'price': float(ticker['lastPrice'])
                    }
                
                ranked_symbols = []
                for symbol_info in symbols:
                    symbol = symbol_info['symbol']
                    if symbol in volume_map:
                        symbol_info.update(volume_map[symbol])
                        ranked_symbols.append(symbol_info)
                
                ranked_symbols.sort(key=lambda x: (x.get('volume', 0), x.get('volatility', 0)), reverse=True)
                return ranked_symbols
            else:
                return symbols
                
        except Exception as e:
            print(f"[ERROR] rank_symbols_by_liquidity: {e}")
            return symbols
    
    def run(self):
        """Main execution loop"""
        try:
            print(f"[INFO] Trading Runtime Started")
            print(f"[INFO] Start time: {self.start_time}")
            print(f"[INFO] Initial capital: ${self.total_capital:.2f}")
            
            # Main trading loop
            while True:
                try:
                    # 1. Account and position synchronization
                    self.account_service.periodic_sync(self.trading_results)
                    
                    # 2. Refresh pending orders
                    self.pending_order_manager.refresh_pending_orders()
                    
                    # 3. Execute trading cycle
                    cycle_results = self.trade_orchestrator.run_trading_cycle(
                        self.valid_symbols, self.active_strategies
                    )
                    
                    # 4. Process results
                    self._process_cycle_results(cycle_results)
                    
                    # 5. Display status
                    self._display_cycle_status(cycle_results)
                    
                    time.sleep(10)  # 10 second cycle
                    
                except KeyboardInterrupt:
                    print(f"[INFO] Trading runtime stopped by user")
                    break
                except Exception as e:
                    self.log_system_error("runtime_error", str(e))
                    time.sleep(10)
                    
        except Exception as e:
            self.log_system_error("critical_runtime_error", str(e))
    
    def _process_cycle_results(self, cycle_results):
        """Process cycle results"""
        try:
            self.trading_results.update(cycle_results)
            
            signals = cycle_results.get('signals_generated', 0)
            trades = cycle_results.get('trades_executed', 0)
            errors = len(cycle_results.get('errors', []))
            
            if signals > 0 or trades > 0:
                print(f"[INFO] Cycle completed - Signals: {signals}, Trades: {trades}, Errors: {errors}")
            
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
    
    # Helper methods
    def log_system_error(self, error_type, error_message):
        """System error logging"""
        print(f"[ERROR] {error_type}: {error_message}")
        self.trading_results["last_error"] = f"{error_type}: {error_message}"
    
    def get_symbol_info(self, symbol):
        """Get symbol information"""
        return self.market_data_service.get_symbol_info(symbol)
    
    def get_order_status(self, symbol, order_id):
        """Get order status"""
        return self.order_executor.get_order_status(symbol, order_id)

    def cancel_order(self, symbol, order_id):
        """Cancel a standard futures order"""
        return self.order_executor.cancel_order(symbol, order_id)
    
    def clear_position_management_state(self, symbol):
        """Clear position management state"""
        try:
            if symbol in self.trading_results["partial_take_profit_state"]:
                del self.trading_results["partial_take_profit_state"][symbol]
            if symbol in self.trading_results["managed_stop_prices"]:
                del self.trading_results["managed_stop_prices"][symbol]
            if symbol in self.position_entry_times:
                del self.position_entry_times[symbol]
            if hasattr(self, "partial_take_profit_manager"):
                self.partial_take_profit_manager.clear_position_management_state(symbol)
        except Exception as e:
            self.log_system_error("clear_position_state", str(e))
    
    def get_total_capital(self):
        """Get total capital"""
        return self.total_capital
    
    def safe_float_conversion(self, value, default=0.0):
        """Safe float conversion"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def round_to_step(self, value, step_size, rounding_mode):
        """Round to step size"""
        try:
            from decimal import Decimal, ROUND_DOWN, ROUND_UP
            if step_size <= 0:
                return round(value, 8)
            
            decimal_value = Decimal(str(value))
            decimal_step = Decimal(str(step_size))
            
            if rounding_mode == ROUND_DOWN:
                rounded = (decimal_value // decimal_step) * decimal_step
            else:
                rounded = (decimal_value // decimal_step + 1) * decimal_step
            
            return float(rounded)
        except Exception:
            return value


if __name__ == "__main__":
    runtime = TradingRuntime()
    runtime.run()
