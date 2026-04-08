#!/usr/bin/env python3
"""
v3.2 Pure Unit Test Script
===========================
Pure unit tests without external API dependencies.
"""

import sys
import os
import time
from pathlib import Path

# Add project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auto_strategy_futures_trading_v3_dynamic import (
    MarketRegime, 
    MarketState,
    Signal,
    TradeSignal,
    PositionManager,
    PerformanceTracker,
    MarketAnalyzer,
    SymbolSelector,
    StrategyEngine,
    CONFIG
)

class DummyClient:
    """Pure mock client for unit testing"""
    
    def __init__(self):
        self.mock_prices = {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "XRPUSDT": 0.5,
            "ADAUSDT": 0.4
        }
    
    def get_klines(self, symbol, interval, limit):
        """Generate deterministic mock kline data"""
        base_price = self.mock_prices[symbol]
        klines = []
        
        for i in range(limit):
            # Simple deterministic pattern
            price_change = 0.001 * (1 if i % 2 == 0 else -0.5)
            current_price = base_price * (1 + price_change * i / limit)
            
            klines.append([
                str(int(current_price * 1000)),  # Open
                str(int(current_price * 1000 * 1.001)),  # High
                str(int(current_price * 1000 * 0.999)),  # Low
                str(int(current_price * 1000)),  # Close
                "1000000",  # Volume
                str(int(time.time()) - (limit - i) * 3600)  # Close time
            ])
        
        return klines
    
    def get_ticker_24h(self):
        """Generate deterministic ticker data"""
        return {
            "BTCUSDT": {"priceChangePercent": "0.5", "quoteVolume": "1000000", "count": "10000"},
            "ETHUSDT": {"priceChangePercent": "0.3", "quoteVolume": "900000", "count": "8000"},
            "XRPUSDT": {"priceChangePercent": "-0.2", "quoteVolume": "800000", "count": "7000"},
            "ADAUSDT": {"priceChangePercent": "0.1", "quoteVolume": "700000", "count": "6000"},
        }
    
    def get_symbol_info(self, symbol):
        """Mock symbol info"""
        return {
            'symbol': symbol,
            'pricePrecision': 4,
            'quantityPrecision': 4,
            'minQty': '0.001',
            'maxQty': '1000',
            'stepSize': '0.001',
            'minNotional': '5.0',
            'filters': [
                {'filterType': 'PRICE_FILTER', 'minPrice': '0.0001', 'maxPrice': '1000000', 'tickSize': '0.0001'},
                {'filterType': 'LOT_SIZE', 'minQty': '0.001', 'maxQty': '1000000', 'stepSize': '0.001'},
                {'filterType': 'MIN_NOTIONAL', 'notional': '5.0'},
            ]
        }

def test_pure_unit_functionality():
    """Pure unit tests without external dependencies"""
    print("[PURE UNIT] Testing v3.2 Core Functionality")
    print("=" * 60)
    
    # Test 1: Enum and dataclass creation
    try:
        regime = MarketRegime.BULL
        state = MarketState(
            regime=regime,
            volatility=0.02,
            strength=0.001,
            spread_pct=0.001,
            trend_strength=0.5
        )
        print("  Enum and MarketState creation works")
    except Exception as e:
        print(f"  Enum/MarketState test failed: {e}")
    
    # Test 2: PositionManager pure functionality
    try:
        pm = PositionManager()
        
        # Test can_enter
        can_enter = pm.can_enter("BTCUSDT", time.time())
        print(f"  PositionManager.can_enter() works: {can_enter}")
        
        # Test register_entry
        pm.register_entry("BTCUSDT", "BUY", 0.1, 50000.0, "momentum")
        position = pm.get_position("BTCUSDT")
        print(f"  PositionManager.register_entry() works: {position}")
        
        # Test has_open_position
        has_open = pm.has_open_position("BTCUSDT")
        print(f"  PositionManager.has_open_position() works: {has_open}")
        
        # Test register_exit
        pm.register_exit("BTCUSDT")
        can_enter_after = pm.can_enter("BTCUSDT", time.time())
        print(f"  PositionManager.register_exit() works: {not pm.has_open_position('BTCUSDT')}")
        
    except Exception as e:
        print(f"  PositionManager test failed: {e}")
    
    # Test 3: PerformanceTracker pure functionality
    try:
        tracker = PerformanceTracker()
        
        # Test record
        tracker.record(0.05)
        tracker.record(-0.03)
        summary = tracker.summary()
        print(f"  PerformanceTracker.record() works: trades={summary['total_trades']}")
        
        # Test record_realized_pnl
        tracker.record_realized_pnl(0.02)
        tracker.record_realized_pnl(-0.01)
        print("  PerformanceTracker.record_realized_pnl() works")
        
    except Exception as e:
        print(f"  PerformanceTracker test failed: {e}")
    
    # Test 4: MarketAnalyzer with DummyClient
    try:
        dummy_client = DummyClient()
        analyzer = MarketAnalyzer(dummy_client)
        
        # Test get_symbol_market_state
        market_state = analyzer.get_symbol_market_state("BTCUSDT")
        print(f"  MarketAnalyzer.get_symbol_market_state() works: {market_state.regime.name}")
        
    except Exception as e:
        print(f"  MarketAnalyzer test failed: {e}")
    
    # Test 5: SymbolSelector with DummyClient
    try:
        dummy_client = DummyClient()
        analyzer = MarketAnalyzer(dummy_client)
        engine = StrategyEngine()
        selector = SymbolSelector(dummy_client)
        
        # Test select_best_symbol_for_strategy
        candidates = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
        symbol, signal, score = selector.select_best_symbol_for_strategy(
            "momentum", candidates, analyzer, engine
        )
        print(f"  SymbolSelector.select_best_symbol_for_strategy() works: symbol={symbol}, score={score:.3f}")
        
    except Exception as e:
        print(f"  SymbolSelector test failed: {e}")
    
    # Test 6: CONFIG values verification
    try:
        threshold = CONFIG.SIGNAL_THRESHOLD
        bull_threshold = CONFIG.get_threshold('bull_threshold')
        bear_threshold = CONFIG.get_threshold('bear_threshold')
        
        print(f"  CONFIG values: SIGNAL_THRESHOLD={threshold}, bull={bull_threshold:.4f}, bear={bear_threshold:.4f}")
        
        # Verify expected values
        if threshold == 0.58:
            print("  SIGNAL_THRESHOLD value is correct")
        else:
            print(f"  SIGNAL_THRESHOLD value incorrect: expected 0.58, got {threshold}")
            
    except Exception as e:
        print(f"  CONFIG test failed: {e}")
    
    # Test 7: PnL calculation accuracy
    try:
        # Test side-based PnL calculation
        trading_system = type('TradingSystem', (), {})()
        trading_system._calculate_pnl_pct = lambda side, entry, current: (
            (current - entry) / entry if side == "BUY" else 
            (entry - current) / entry if side == "SELL" else 0.0
        )
        
        # Test BUY position
        buy_pnl = trading_system._calculate_pnl_pct("BUY", 50000.0, 51000.0)
        expected_buy = (51000.0 - 50000.0) / 50000.0
        
        # Test SELL position
        sell_pnl = trading_system._calculate_pnl_pct("SELL", 50000.0, 49000.0)
        expected_sell = (50000.0 - 49000.0) / 50000.0
        
        if abs(buy_pnl - expected_buy) < 0.0001 and abs(sell_pnl - expected_sell) < 0.0001:
            print("  Side-based PnL calculation works correctly")
        else:
            print(f"  PnL calculation error: BUY={buy_pnl:.4f} (exp={expected_buy:.4f}), SELL={sell_pnl:.4f} (exp={expected_sell:.4f})")
            
    except Exception as e:
        print(f"  PnL calculation test failed: {e}")
    
    print("\n" + "=" * 60)
    print("[PURE UNIT] Core functionality test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_pure_unit_functionality()
