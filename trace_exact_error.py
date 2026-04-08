#!/usr/bin/env python3
"""
Trace Exact Error - Trace the exact line causing the error
"""

import json
import traceback

def trace_exact_error():
    """Trace the exact line causing the symbol selection error"""
    print('=' * 60)
    print('TRACE EXACT ERROR LINE')
    print('=' * 60)
    
    # Load strategy registry and add detailed logging
    from core.strategy_registry import StrategyRegistry
    
    # Create a custom version with detailed logging
    class DebugStrategyRegistry(StrategyRegistry):
        def select_preferred_symbols(self, strategy_name: str, 
                                    available_symbols: list, 
                                    max_symbols: int = 10):
            print(f'[DEBUG] select_preferred_symbols called with:')
            print(f'  strategy_name: {strategy_name}')
            print(f'  available_symbols type: {type(available_symbols)}')
            print(f'  available_symbols count: {len(available_symbols)}')
            print(f'  max_symbols: {max_symbols}')
            
            try:
                strategy_config = self.get_strategy_profile(strategy_name)
                print(f'  strategy_config type: {type(strategy_config)}')
                
                if not strategy_config:
                    print('  ERROR: strategy_config is None')
                    return []
                
                symbol_selection = strategy_config.get('symbol_selection', {})
                print(f'  symbol_selection type: {type(symbol_selection)}')
                print(f'  symbol_selection: {symbol_selection}')
                
                # This is where the error occurs
                print('  About to access symbol_mode...')
                symbol_mode = symbol_selection.get('symbol_mode', 'leaders')
                print(f'  symbol_mode: {symbol_mode}')
                
                print('  About to access candidate_limit...')
                candidate_limit = symbol_selection.get('candidate_limit', 6)
                print(f'  candidate_limit: {candidate_limit}')
                
                # Continue with the rest
                if not available_symbols:
                    return []
                
                symbols = []
                for s in available_symbols:
                    if isinstance(s, dict):
                        symbols.append(s.get('symbol', str(s)))
                    elif isinstance(s, str):
                        symbols.append(s)
                    else:
                        symbols.append(str(s))
                
                candidates = symbols[:50]
                print(f'  candidates: {len(candidates)} symbols')
                
                if symbol_mode == 'leaders':
                    result = candidates[:min(candidate_limit, len(candidates))]
                    print(f'  result: {result}')
                    return result
                else:
                    result = candidates[:min(candidate_limit, len(candidates))]
                    print(f'  result: {result}')
                    return result
                    
            except Exception as e:
                print(f'  ERROR: {e}')
                print('  Full traceback:')
                traceback.print_exc()
                return []
    
    # Test with debug version
    debug_sr = DebugStrategyRegistry()
    
    # Get actual symbols
    from core.market_data_service import MarketDataService
    mds = MarketDataService('https://demo-fapi.binance.com')
    symbols = mds.get_available_symbols()
    
    # Convert like trade_orchestrator does
    symbol_list = []
    for symbol_data in symbols:
        if isinstance(symbol_data, dict):
            symbol_list.append(symbol_data.get('symbol', ''))
        elif isinstance(symbol_data, str):
            symbol_list.append(symbol_data)
        else:
            symbol_list.append(str(symbol_data))
    
    print('[TEST] Testing ma_trend_follow:')
    result = debug_sr.select_preferred_symbols('ma_trend_follow', symbol_list, 10)
    print(f'Final result: {result}')
    
    print('=' * 60)
    print('[RESULT] Trace complete')
    print('=' * 60)

if __name__ == "__main__":
    trace_exact_error()
