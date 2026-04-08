#!/usr/bin/env python3
"""
Find Exact Error - Pinpoint the exact location of the error
"""

import json
import traceback

def find_exact_error():
    """Find the exact location of the symbol selection error"""
    print('=' * 60)
    print('FIND EXACT ERROR LOCATION')
    print('=' * 60)
    
    # Load strategy registry and test step by step
    from core.strategy_registry import StrategyRegistry
    sr = StrategyRegistry()
    
    print('[DEBUG] Step-by-step analysis:')
    
    # Step 1: Check strategy config
    strategy_name = 'ma_trend_follow'
    print(f'  Step 1: Getting strategy config for {strategy_name}')
    
    try:
        strategy_config = sr.get_strategy_profile(strategy_name)
        print(f'    Strategy config type: {type(strategy_config)}')
        print(f'    Strategy config: {strategy_config}')
        
        if strategy_config:
            print(f'    Strategy config keys: {list(strategy_config.keys())}')
        else:
            print('    ERROR: Strategy config is None')
            return
            
    except Exception as e:
        print(f'    ERROR in step 1: {e}')
        traceback.print_exc()
        return
    
    # Step 2: Check symbol_selection
    print('  Step 2: Getting symbol_selection config')
    
    try:
        symbol_selection = strategy_config.get('symbol_selection', {})
        print(f'    Symbol selection type: {type(symbol_selection)}')
        print(f'    Symbol selection: {symbol_selection}')
        
        if symbol_selection:
            print(f'    Symbol selection keys: {list(symbol_selection.keys())}')
        else:
            print('    Symbol selection is empty or None')
            
    except Exception as e:
        print(f'    ERROR in step 2: {e}')
        traceback.print_exc()
        return
    
    # Step 3: Check symbol_mode
    print('  Step 3: Getting symbol_mode')
    
    try:
        if symbol_selection and isinstance(symbol_selection, dict):
            symbol_mode = symbol_selection.get('symbol_mode', 'leaders')
        else:
            symbol_mode = 'leaders'
        print(f'    Symbol mode: {symbol_mode}')
        
    except Exception as e:
        print(f'    ERROR in step 3: {e}')
        traceback.print_exc()
        return
    
    # Step 4: Check candidate_limit
    print('  Step 4: Getting candidate_limit')
    
    try:
        if symbol_selection and isinstance(symbol_selection, dict):
            candidate_limit = symbol_selection.get('candidate_limit', 6)
        else:
            candidate_limit = 6
        print(f'    Candidate limit: {candidate_limit}')
        
    except Exception as e:
        print(f'    ERROR in step 4: {e}')
        traceback.print_exc()
        return
    
    # Step 5: Test with actual symbols
    print('  Step 5: Testing with actual symbols')
    
    try:
        # Get actual symbols from market data service
        from core.market_data_service import MarketDataService
        mds = MarketDataService('https://demo-fapi.binance.com')
        actual_symbols = mds.get_available_symbols()
        
        print(f'    Actual symbols count: {len(actual_symbols)}')
        if actual_symbols:
            print(f'    First symbol type: {type(actual_symbols[0])}')
            print(f'    First symbol: {actual_symbols[0]}')
        
        # Test selection
        result = sr.select_preferred_symbols(strategy_name, actual_symbols, 10)
        print(f'    Selection result: {len(result)} symbols')
        print(f'    Selected symbols: {result}')
        
    except Exception as e:
        print(f'    ERROR in step 5: {e}')
        print('    Full traceback:')
        traceback.print_exc()
        return
    
    print('=' * 60)
    print('[RESULT] Error analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    find_exact_error()
