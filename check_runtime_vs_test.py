#!/usr/bin/env python3
"""
Check Runtime vs Test - Compare runtime execution with test execution
"""

import json

def check_runtime_vs_test():
    """Check why runtime fails but test passes"""
    print('=' * 60)
    print('RUNTIME VS TEST COMPARISON')
    print('=' * 60)
    
    # Check what trade_orchestrator is actually passing
    print('[ANALYSIS] What trade_orchestrator passes to strategy_registry:')
    
    # Simulate what trade_orchestrator does
    try:
        from core.market_data_service import MarketDataService
        from core.strategy_registry import StrategyRegistry
        
        # Get symbols like trade_orchestrator does
        mds = MarketDataService('https://demo-fapi.binance.com')
        symbols = mds.get_available_symbols()
        
        print(f'  Symbols from market_data_service: {len(symbols)}')
        print(f'  First symbol type: {type(symbols[0])}')
        print(f'  First symbol: {symbols[0]}')
        
        # Simulate trade_orchestrator's conversion
        symbol_list = []
        for symbol_data in symbols:
            if isinstance(symbol_data, dict):
                symbol_list.append(symbol_data.get('symbol', ''))
            elif isinstance(symbol_data, str):
                symbol_list.append(symbol_data)
            else:
                symbol_list.append(str(symbol_data))
        
        print(f'  Converted symbol list: {len(symbol_list)}')
        print(f'  First converted: {symbol_list[0]}')
        print(f'  Converted list type: {type(symbol_list[0])}')
        
        # Test with strategy_registry
        sr = StrategyRegistry()
        
        print('  Testing ma_trend_follow:')
        try:
            result = sr.select_preferred_symbols('ma_trend_follow', symbol_list, 10)
            print(f'    Result: {len(result)} symbols - {result}')
        except Exception as e:
            print(f'    ERROR: {e}')
            import traceback
            traceback.print_exc()
        
        print('  Testing ema_crossover:')
        try:
            result = sr.select_preferred_symbols('ema_crossover', symbol_list, 10)
            print(f'    Result: {len(result)} symbols - {result}')
        except Exception as e:
            print(f'    ERROR: {e}')
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f'  ERROR in analysis: {e}')
        import traceback
        traceback.print_exc()
    
    # Check if there's a difference in strategy configs
    print('\n[ANALYSIS] Strategy config comparison:')
    
    try:
        from core.strategy_registry import StrategyRegistry
        sr = StrategyRegistry()
        
        # Check ma_trend_follow
        ma_config = sr.get_strategy_profile('ma_trend_follow')
        ma_symbol_selection = ma_config.get('symbol_selection', {})
        print(f'  ma_trend_follow symbol_selection: {ma_symbol_selection}')
        print(f'  ma_trend_follow symbol_selection type: {type(ma_symbol_selection)}')
        
        # Check ema_crossover
        ema_config = sr.get_strategy_profile('ema_crossover')
        ema_symbol_selection = ema_config.get('symbol_selection', {})
        print(f'  ema_crossover symbol_selection: {ema_symbol_selection}')
        print(f'  ema_crossover symbol_selection type: {type(ema_symbol_selection)}')
        
    except Exception as e:
        print(f'  ERROR in config check: {e}')
    
    # Check if there are multiple instances or caching issues
    print('\n[ANALYSIS] Instance and caching check:')
    
    try:
        # Create new instances
        sr1 = StrategyRegistry()
        sr2 = StrategyRegistry()
        
        ma_config1 = sr1.get_strategy_profile('ma_trend_follow')
        ma_config2 = sr2.get_strategy_profile('ma_trend_follow')
        
        print(f'  Instance 1 ma_trend_follow: {id(ma_config1)}')
        print(f'  Instance 2 ma_trend_follow: {id(ma_config2)}')
        print(f'  Same instance: {ma_config1 is ma_config2}')
        
    except Exception as e:
        print(f'  ERROR in instance check: {e}')
    
    print('=' * 60)
    print('[RESULT] Runtime vs test comparison complete')
    print('=' * 60)

if __name__ == "__main__":
    check_runtime_vs_test()
