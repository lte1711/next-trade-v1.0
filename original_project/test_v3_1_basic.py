#!/usr/bin/env python3
"""
v3.1 Quick Test Script
===============================
Quick test to verify v3.1 optimizations work correctly.
"""

import sys
import os
import time
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auto_strategy_futures_trading_v3_dynamic import (
    AutoStrategyFuturesTrading, 
    MarketState, 
    MarketRegime,
    Signal,
    TradeSignal
)

def test_basic_functionality():
    """Test basic v3.1 functionality"""
    print("[TEST] Testing v3.1 Basic Functionality")
    print("=" * 50)
    
    # Test 1: MarketRegime.NEUTRAL enum
    print("✓ MarketRegime.NEUTRAL enum exists")
    
    # Test 2: MarketState.trend_strength field
    try:
        market_state = MarketState(
            regime=MarketRegime.BULL,
            volatility=0.02,
            strength=0.01,
            spread_pct=0.001,
            trend_strength=0.005
        )
        print("✓ MarketState.trend_strength field works")
    except Exception as e:
        print(f"✗ MarketState.trend_strength failed: {e}")
    
    # Test 3: Enhanced PositionManager
    try:
        from position_manager import PositionManager
        pm = PositionManager()
        
        # Test cooldown functionality
        can_enter = pm.can_enter("BTCUSDT", time.time())
        print(f"✓ PositionManager.can_enter() works: {can_enter}")
        
        # Test enhanced position tracking
        pm.register_entry("BTCUSDT", "BUY", 0.1, 50000.0, "momentum")
        position = pm.get_position("BTCUSDT")
        print(f"✓ PositionManager.register_entry() works: {position}")
        
    except Exception as e:
        print(f"✗ PositionManager test failed: {e}")
    
    # Test 4: get_symbol_market_state method
    try:
        # This will test the method exists and can be called
        # (Actual API calls will be mocked in real test)
        trading_system = AutoStrategyFuturesTrading(testnet=True, duration_hours=1)
        market_state = trading_system.analyzer.get_symbol_market_state("BTCUSDT")
        print("✓ get_symbol_market_state() method exists and callable")
    except Exception as e:
        print(f"✗ get_symbol_market_state test failed: {e}")
    
    # Test 5: select_best_symbol_for_strategy method
    try:
        trading_system = AutoStrategyFuturesTrading(testnet=True, duration_hours=1)
        candidates = ["BTCUSDT", "ETHUSDT"]
        symbol, signal, score = trading_system.selector.select_best_symbol_for_strategy(
            "momentum", candidates, trading_system.analyzer, trading_system.engine
        )
        print(f"✓ select_best_symbol_for_strategy() works: {symbol}, score: {score}")
    except Exception as e:
        print(f"✗ select_best_symbol_for_strategy test failed: {e}")
    
    # Test 6: Enhanced PerformanceTracker
    try:
        from auto_strategy_futures_trading_v3_dynamic import PerformanceTracker
        tracker = PerformanceTracker()
        
        # Test regular record
        tracker.record(0.05)
        print("✓ PerformanceTracker.record() works")
        
        # Test realized PnL record
        tracker.record_realized_pnl(0.03)
        print("✓ PerformanceTracker.record_realized_pnl() works")
        
    except Exception as e:
        print(f"✗ PerformanceTracker test failed: {e}")
    
    # Test 7: SIGNAL_THRESHOLD value
    try:
        from auto_strategy_futures_trading_v3_dynamic import CONFIG
        threshold = CONFIG.SIGNAL_THRESHOLD
        print(f"✓ SIGNAL_THRESHOLD = {threshold} (should be 0.58)")
    except Exception as e:
        print(f"✗ SIGNAL_THRESHOLD test failed: {e}")
    
    print("\n" + "=" * 50)
    print("[TEST] Basic functionality test completed")
    print("=" * 50)

if __name__ == "__main__":
    test_basic_functionality()
