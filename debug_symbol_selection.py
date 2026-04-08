#!/usr/bin/env python3
"""
Debug Symbol Selection - Find the exact source of the error
"""

import json

def debug_symbol_selection():
    """Debug symbol selection error"""
    print('=' * 60)
    print('DEBUG SYMBOL SELECTION ERROR')
    print('=' * 60)
    
    # Load strategy registry
    from core.strategy_registry import StrategyRegistry
    sr = StrategyRegistry()
    
    # Test with sample data
    print('[TEST] Testing symbol selection with sample data:')
    
    # Test 1: Empty list
    try:
        result = sr.select_preferred_symbols('ma_trend_follow', [], 10)
        print(f'  Test 1 (empty list): OK - {len(result)} symbols')
    except Exception as e:
        print(f'  Test 1 (empty list): ERROR - {e}')
    
    # Test 2: String list
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
        result = sr.select_preferred_symbols('ma_trend_follow', symbols, 10)
        print(f'  Test 2 (string list): OK - {len(result)} symbols')
    except Exception as e:
        print(f'  Test 2 (string list): ERROR - {e}')
    
    # Test 3: Dict list
    try:
        symbols = [{'symbol': 'BTCUSDT'}, {'symbol': 'ETHUSDT'}, {'symbol': 'XRPUSDT'}]
        result = sr.select_preferred_symbols('ma_trend_follow', symbols, 10)
        print(f'  Test 3 (dict list): OK - {len(result)} symbols')
    except Exception as e:
        print(f'  Test 3 (dict list): ERROR - {e}')
    
    # Test 4: Mixed list
    try:
        symbols = ['BTCUSDT', {'symbol': 'ETHUSDT'}, 'XRPUSDT']
        result = sr.select_preferred_symbols('ma_trend_follow', symbols, 10)
        print(f'  Test 4 (mixed list): OK - {len(result)} symbols')
    except Exception as e:
        print(f'  Test 4 (mixed list): ERROR - {e}')
    
    # Test 5: Invalid data
    try:
        symbols = [None, 123, 'BTCUSDT']
        result = sr.select_preferred_symbols('ma_trend_follow', symbols, 10)
        print(f'  Test 5 (invalid data): OK - {len(result)} symbols')
    except Exception as e:
        print(f'  Test 5 (invalid data): ERROR - {e}')
    
    # Test 6: What the market data service actually returns
    try:
        from core.market_data_service import MarketDataService
        
        # Initialize with test callback
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        # Get actual symbols
        actual_symbols = mds.get_available_symbols()
        print(f'  Test 6 (actual symbols): {len(actual_symbols)} symbols returned')
        
        if actual_symbols:
            print(f'    First symbol type: {type(actual_symbols[0])}')
            print(f'    First symbol: {actual_symbols[0]}')
            
            # Test with actual symbols
            try:
                result = sr.select_preferred_symbols('ma_trend_follow', actual_symbols, 10)
                print(f'    Selection result: OK - {len(result)} symbols')
            except Exception as e:
                print(f'    Selection result: ERROR - {e}')
                print(f'    Error details: {str(e)}')
                
                # Find exact line causing error
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f'  Test 6 (actual symbols): ERROR - {e}')
    
    print('=' * 60)
    print('[RESULT] Debug complete')
    print('=' * 60)

if __name__ == "__main__":
    debug_symbol_selection()
