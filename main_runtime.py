"""
Main Runtime - 통합 런타임 모듈
"""

import sys
import os
import json
from datetime import datetime
import time

# Core 모듈 임포트
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

# 필수 임포트
import requests
import hmac
import hashlib


class TradingRuntime:
    """통합 트레이딩 런타임"""
    
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
        
        # API 키 확인
        if not is_api_valid():
            print("[ERROR] API credentials not found. Please run: python setup_api.py")
            return
        
        self.api_key, self.api_secret = get_api_credentials()
        self.base_url = "https://testnet.binancefuture.com"
        
        # 새로운 모듈화 아키텍처 초기화
        self.market_data_service = MarketDataService(
            self.base_url, self.api_key, self.api_secret, self.log_system_error
        )
        
        self.indicator_service = IndicatorService(self.log_system_error)
        self.market_regime_service = MarketRegimeService(self.log_system_error)
        self.signal_engine = SignalEngine(self.log_system_error)
        self.strategy_registry = StrategyRegistry(self.log_system_error)
        self.allocation_service = AllocationService(self.log_system_error)
        
        # 기존 매니저들 (호환성 유지)
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
        
        # 메인 오케스트레이터
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
        
        # Load trading configuration
        trading_config = config.get("trading_config", {})
        self.max_open_positions = trading_config.get("max_open_positions", 1)
        self.fast_entry_enabled = trading_config.get("fast_entry_enabled", True)
        self.partial_tp1_pct = trading_config.get("partial_tp1_pct", 0.8)
        self.fast_tp1_pct = trading_config.get("fast_tp1_pct", 0.5)
        self.fast_tp2_pct = trading_config.get("fast_tp2_pct", 1.2)
        self.partial_tp2_pct = trading_config.get("partial_tp2_pct", 2.0)
        self.stop_loss_pct = trading_config.get("stop_loss_pct", 0.02)
        self.take_profit_pct = trading_config.get("take_profit_pct", 0.04)
        self.position_hold_minutes = trading_config.get("position_hold_minutes", 30)
        self.max_position_size_usdt = trading_config.get("max_position_size_usdt", 1000.0)
        
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
        """환경 설정 파일 로드"""
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
        """기본 URL 해결"""
        return "https://testnet.binancefuture.com"
    
    def log_system_error(self, error_type, error_message):
        """시스템 오류 로깅"""
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
        """전략 로드"""
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
        """유효 심볼 로드"""
        return [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
            "XRPUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "AVAXUSDT",
            "MATICUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT", "ICPUSDT",
            "VETUSDT", "THETAUSDT", "FTMUSDT", "SANDUSDT", "MANAUSDT",
            "ALGOUSDT", "ENJUSDT", "CRVUSDT", "AAVEUSDT", "MKRUSDT",
            "COMPUSDT", "SUSHIUSDT", "YFIUSDT", "SNXUSDT", "RUNEUSDT"
        ]
    
    def get_symbol_info(self, symbol):
        """심볼 정보 조회"""
        return get_symbol_info(self.base_url, self.api_key, self.api_secret, symbol)
    
    def get_order_status(self, symbol, order_id):
        """주문 상태 조회"""
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
        """포지션 관리 상태 정리"""
        try:
            if symbol in self.trading_results["partial_take_profit_state"]:
                del self.trading_results["partial_take_profit_state"][symbol]
        except Exception:
            pass
    
    def sync_positions(self):
        """실제 포지션 동기화 최소 구현"""
        try:
            # TODO: 실제 API 기반 포지션 동기화 로직 구현
            # 현재는 active_positions 타임스탬프 갱신과 기본 유효성 검사
            current_time = datetime.now().isoformat()
            
            for symbol in list(self.trading_results["active_positions"].keys()):
                position = self.trading_results["active_positions"][symbol]
                
                # 타임스탬프 갱신
                position["last_sync"] = current_time
                
                # 기본 유효성 검사: amount가 0이면 제거
                if abs(position.get("amount", 0.0)) == 0:
                    print(f"[TRACE] ZERO_POSITION_REMOVED | {symbol}")
                    del self.trading_results["active_positions"][symbol]
                
        except Exception as e:
            self.log_system_error("sync_positions_error", str(e))
        return None
    
    def display_status(self):
        """상태 표시"""
        print(f"[INFO] REFACTORED_RUNTIME: Modular architecture implemented")
        print(f"[INFO] CORE_MODULES: ProtectiveOrderManager, PendingOrderManager, OrderExecutor")
        print(f"[INFO] MONOLITHIC_REDUCED: Core responsibilities split into modules")
        print(f"[INFO] MAINTAINABILITY: Significantly improved")
        return None
    
    def run(self):
        """메인 실행 루프 - 완전한 거래 오케스트레이션"""
        try:
            print(f"[INFO] Complete Modular Trading Runtime Started")
            print(f"[INFO] Start time: {self.start_time}")
            print(f"[INFO] Initial capital: ${self.total_capital:.2f}")
            
            # 초기화 및 설정
            self._initialize_trading_system()
            
            # 메인 거래 루프
            while True:
                try:
                    # 1. 계정 및 포지션 동기화
                    self.account_service.periodic_sync(self.trading_results)
                    
                    # 2. 미체결 주문 새로고침
                    self.pending_order_manager.refresh_pending_orders()
                    
                    # 3. 전체 거래 사이클 실행
                    cycle_results = self.trade_orchestrator.run_trading_cycle(
                        self.valid_symbols, 
                        self.active_strategies
                    )
                    
                    # 4. 결과 처리
                    self._process_cycle_results(cycle_results)
                    
                    # 5. 상태 표시
                    self._display_cycle_status(cycle_results)
                    
                    time.sleep(10)  # 10초 주기
                    
                except KeyboardInterrupt:
                    print(f"[INFO] Trading runtime stopped by user")
                    break
                except Exception as e:
                    self.log_system_error("runtime_error", str(e))
                    time.sleep(10)
                    
            # 오류 처리
            for error in cycle_results.get('errors', []):
                self.log_system_error("cycle_error", error)
            
            # 통계 업데이트
            self.trading_results['last_cycle'] = cycle_results
            
        except Exception as e:
            self.log_system_error("cycle_results_process", str(e))
    
    def _process_cycle_results(self, cycle_results):
        """Process cycle results and update trading statistics"""
        try:
            # Update trading results
            self.trading_results.update(cycle_results)
            
            # Log cycle completion
            signals = cycle_results.get('signals_generated', 0)
            trades = cycle_results.get('trades_executed', 0)
            errors = len(cycle_results.get('errors', []))
            
            if signals > 0 or trades > 0:
                print(f"[INFO] Cycle completed - Signals: {signals}, Trades: {trades}, Errors: {errors}")
            
        except Exception as e:
            self.log_system_error("cycle_results_process", str(e))
    
    def _display_cycle_status(self, cycle_results):
        """사이클 상태 표시"""
        try:
            signals = cycle_results.get('signals_generated', 0)
            trades = cycle_results.get('trades_executed', 0)
            errors = len(cycle_results.get('errors', []))
            
            if signals > 0 or trades > 0 or errors > 0:
                print(f"[CYCLE] Signals: {signals}, Trades: {trades}, Errors: {errors}")
                
        except Exception as e:
            self.log_system_error("cycle_status_display", str(e))
        
        except Exception as e:
            self.log_system_error("critical_runtime_error", str(e))


if __name__ == "__main__":
    runtime = TradingRuntime()
    runtime.run()
