#!/usr/bin/env python3
"""
v3.1 Debug Test Script
===============================
Debug v3.1 with detailed logging to identify blocking conditions.
"""

import sys
import os
import time
import math
from datetime import datetime, timedelta
from pathlib import Path

# Add project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Mock API credentials for testing
os.environ['BINANCE_TESTNET_KEY'] = 'test_key'
os.environ['BINANCE_TESTNET_SECRET'] = 'test_secret'

from auto_strategy_futures_trading_v3_dynamic import (
    AutoStrategyFuturesTrading, 
    MarketState, 
    MarketRegime,
    Signal,
    TradeSignal
)

class MockBinanceClient:
    """Mock Binance client for testing"""
    
    def __init__(self, testnet=True):
        self.testnet = testnet
        self.mock_prices = {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "BNBUSDT": 600.0,
            "SOLUSDT": 150.0,
            "XRPUSDT": 0.5,
            "ADAUSDT": 0.4,
            "DOGEUSDT": 0.08,
            "AVAXUSDT": 35.0,
            "LINKUSDT": 15.0,
            "DOTUSDT": 7.0,
            "LTCUSDT": 70.0,
            "BCHUSDT": 250.0,
            "MATICUSDT": 0.9,
            "ATOMUSDT": 10.0,
            "UNIUSDT": 8.0,
            "ETCUSDT": 3.0
        }
    
    def get_all_prices(self):
        return self.mock_prices.copy()
    
    def get_klines(self, symbol, interval, limit):
        # Generate mock kline data with diverse market conditions per symbol
        base_price = self.mock_prices[symbol]
        klines = []
        current_price = base_price
        
        # v3.2: Create different market conditions for different symbols
        symbol_index = list(self.mock_prices.keys()).index(symbol)
        
        for i in range(limit):
            # Different patterns for different symbols
            if symbol_index % 4 == 0:  # BTC, ETH - Strong trend
                base_change = 0.006 * (1 if i % 2 == 0 else -0.3)  # Strong upward bias
                trend_component = 0.002 * (i / limit)  # Strong uptrend
            elif symbol_index % 4 == 1:  # BNB, SOL - Sideways with volatility
                base_change = 0.004 * (1 if i % 3 == 0 else -1)  # Balanced
                trend_component = 0.0001 * math.sin(i * 0.5)  # Oscillating
            elif symbol_index % 4 == 2:  # XRP, ADA - Mean reversion
                base_change = 0.003 * (1 if i % 4 == 0 else -1)  # Regular reversals
                trend_component = 0.0005 * math.cos(i * 0.3)  # Mean reverting
            else:  # DOGE, AVAX - High volatility
                base_change = 0.008 * (1 if i % 2 == 0 else -0.8)  # High volatility
                trend_component = 0.001 * (i % 3 - 1)  # Random walk
            
            # Add volatility spikes
            if i % 6 == 0:
                base_change *= 1.8
            
            change = base_change + trend_component
            current_price *= (1 + change)
            
            klines.append([
                str(int(current_price * 1000)),  # Open
                str(int(current_price * 1000 * 1.002)),  # High
                str(int(current_price * 1000 * 0.998)),  # Low
                str(int(current_price * 1000)),  # Close
                "1000000",  # Volume
                str(int(time.time()) - (limit - i) * 3600)  # Close time
            ])
        
        return klines
    
    def get_ticker_24h(self):
        return {
            symbol: {"priceChangePercent": str(abs(0.3 + (i % 5) * 0.1))} 
            for i, symbol in enumerate(self.mock_prices.keys())
        }
    
    def submit_order(self, symbol, side, qty):
        print(f"[DEBUG] Order submitted: {symbol} {side} {qty}")
        return {
            'avgPrice': str(self.mock_prices[symbol]),
            'executedQty': str(qty),
            'symbol': symbol,
            'side': side
        }
    
    def submit_stop_market(self, symbol, side, qty, price):
        print(f"[DEBUG] Stop market order submitted: {symbol} {side} {qty} @ {price}")
    
    def submit_take_profit_limit(self, symbol, side, qty, price):
        print(f"[DEBUG] Take profit order submitted: {symbol} {side} {qty} @ {price}")
    
    def get_valid_symbols(self):
        return list(self.mock_prices.keys())
    
    def get_balance(self):
        return 10000.0  # Mock balance
    
    def get_symbol_info(self, symbol):
        """Mock symbol info for quantity calculation"""
        return {
            'symbol': symbol,
            'pricePrecision': 4,
            'quantityPrecision': 4,
            'minQty': '0.001',
            'maxQty': '1000',
            'stepSize': '0.001',
            'minNotional': '5.0'
        }

def debug_v3_1():
    """Debug v3.1 with detailed logging"""
    print("[DEBUG] v3.1 Detailed Debug Test")
    print("=" * 60)
    
    # Initialize trading system
    trading_system = AutoStrategyFuturesTrading(
        testnet=True,
        duration_hours=1,  # Short test
        loop_interval_sec=10  # Slower for debugging
    )
    
    # Replace client with mock
    trading_system.client = MockBinanceClient(testnet=True)
    
    # Set valid symbols
    trading_system.valid_symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
        "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
        "LINKUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT",
        "MATICUSDT", "ATOMUSDT", "UNIUSDT", "ETCUSDT"
    ]
    trading_system.total_capital = 10000.0
    
    # Set end time
    trading_system.start_time = datetime.now()
    trading_system.end_time = trading_system.start_time + timedelta(minutes=1)  # 1 minute test
    
    print(f"[TEST] Starting 1-minute debug test with {len(trading_system.valid_symbols)} symbols")
    from auto_strategy_futures_trading_v3_dynamic import CONFIG
    print(f"[DEBUG] SIGNAL_THRESHOLD: {CONFIG.SIGNAL_THRESHOLD}")
    print(f"[DEBUG] bull_threshold: {CONFIG.get_threshold('bull_threshold')}")
    print(f"[DEBUG] bear_threshold: {CONFIG.get_threshold('bear_threshold')}")
    print(f"[DEBUG] mean_rev_max: {CONFIG.get_threshold('mean_rev_max')}")
    print(f"[DEBUG] vol_high_threshold: {CONFIG.get_threshold('vol_high_threshold')}")
    
    try:
        # Override run method with detailed logging
        debug_run(trading_system)
        
    except Exception as e:
        print(f"[ERROR] Debug test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[DEBUG] v3.1 Debug Test Completed")
    print("=" * 60)

def debug_run(trading_system):
    """Debug run with detailed logging"""
    trade_count = 0
    error_count = 0
    new_trades_this_loop = 0
    n_strategies = 4
    syms_per_strategy = max(1, len(trading_system.valid_symbols) // n_strategies)
    
    print(f"[DEBUG] Strategies: {n_strategies}, Symbols per strategy: {syms_per_strategy}")
    
    while datetime.now() < trading_system.end_time:
        try:
            trading_system.current_prices = trading_system.client.get_all_prices()
            
            # Update symbol rankings for liquidity bonus
            tickers = trading_system.client.get_ticker_24h()
            from auto_strategy_futures_trading_v3_dynamic import CONFIG
            CONFIG.update_symbol_rankings(tickers)
            
            market = trading_system.analyzer.get_market_state()
            signals = trading_system.engine.run_all(market)
            _final = trading_system.engine.aggregate(signals)
            
            print(f"[DEBUG] Market: {market.regime.name}, Vol: {market.volatility:.4f}, Strength: {market.strength:.4f}")
            print(f"[DEBUG] Global signals: {[(k, v.signal.name, v.strength) for k, v in signals.items()]}")
            
            for i, (name, sig) in enumerate(signals.items()):
                print(f"\n[DEBUG] Processing strategy: {name}")
                
                if new_trades_this_loop >= trading_system.max_new_trades_per_loop:
                    print(f"[DEBUG] Max trades per loop reached: {new_trades_this_loop}")
                    break
                
                # Check loss streak pause
                if trading_system.recent_losses[name] >= trading_system.loss_streak_pause:
                    print(f"[DEBUG] Strategy {name} paused - Loss streak: {trading_system.recent_losses[name]}")
                    continue
                
                # Get candidates for this strategy
                start = i * syms_per_strategy
                batch = trading_system.valid_symbols[start:start + syms_per_strategy] or trading_system.valid_symbols[:1]
                print(f"[DEBUG] Strategy {name} candidates: {batch}")
                
                # Select best symbol for strategy (individual symbol evaluation)
                symbol, best_signal, score = trading_system.selector.select_best_symbol_for_strategy(
                    name, batch, trading_system.analyzer, trading_system.engine
                )
                
                print(f"[DEBUG] Best selection: {symbol}, score: {score:.4f}, signal: {best_signal.signal.name if best_signal else 'None'}")
                if best_signal:
                    print(f"[DEBUG] Best signal strength: {best_signal.strength:.4f}")
                
                # Check if individual symbol signal is valid
                if not symbol or score < relaxed_score_min:
                    print(f"[BLOCK] {name} {symbol} | reason=entry_score_low | value={score:.3f}")
                    continue
                    
                # Check individual signal strength
                if best_signal.strength < relaxed_strength_min:
                    print(f"[BLOCK] {name} {symbol} | reason=signal_strength_low | value={best_signal.strength:.3f}")
                    continue
                
                # Check position limits
                if not trading_system.position_manager.can_enter(symbol, time.time()):
                    print(f"[BLOCK] {name} {symbol} | reason=cooldown_active")
                    continue
                
                print(f"[DEBUG] Attempting trade: {name} | {symbol} | {best_signal.signal.name}")
                
                result = trading_system.executor.execute(symbol, best_signal, trading_system.total_capital)
                
                if result:
                    new_trades_this_loop += 1
                    trade_count += 1
                    
                    # Register position
                    entry_price = float(result.get('avgPrice', 0))
                    trading_system.position_manager.register_entry(
                        symbol, best_signal.signal.value, 
                        float(result.get('executedQty', 0)),
                        entry_price,
                        name
                    )
                    
                    # Track position for realized PnL calculation
                    trading_system.open_positions[symbol] = {
                        "entry_price": entry_price,
                        "entry_time": time.time(),
                        "strategy": name,
                        "qty": float(result.get('executedQty', 0))
                    }
                    
                    print(f"[DEBUG] SUCCESS: {name} | {symbol} | {best_signal.signal.name} | score: {score:.4f}")
                    trading_system.recent_losses[name] = 0
                else:
                    error_count += 1
                    trading_system.recent_losses[name] += 1
                    print(f"[DEBUG] FAILED: {name} | {symbol} order rejected")
            
            new_trades_this_loop = 0
            time.sleep(trading_system.loop_interval_sec)
            
        except KeyboardInterrupt:
            print(f"\n[STOP] User interrupt at {datetime.now()}")
            break
        except Exception as e:
            print(f"[ERROR] Main loop error: {e}")
            error_count += 1
            time.sleep(10)
    
    print(f"\n[DEBUG] Final: Trades={trade_count}, Errors={error_count}")

if __name__ == "__main__":
    debug_v3_1()
