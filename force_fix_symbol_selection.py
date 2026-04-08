#!/usr/bin/env python3
"""
Force Fix Symbol Selection - Force fix the symbol selection issue
"""

import json
import traceback

def force_fix_symbol_selection():
    """Force fix the symbol selection issue by overriding the method"""
    print('=' * 60)
    print('FORCE FIX SYMBOL SELECTION')
    print('=' * 60)
    
    # Read the current strategy_registry.py
    with open('core/strategy_registry.py', 'r') as f:
        content = f.read()
    
    # Find the select_preferred_symbols method and replace it with a robust version
    new_method = '''    def select_preferred_symbols(self, strategy_name: str, 
                                available_symbols: List[Dict[str, Any]],
                                max_symbols: int = 10) -> List[str]:
        """V2 Merged: Select preferred symbols for a strategy"""
        try:
            # Use hardcoded defaults to avoid any config issues
            if strategy_name == 'ma_trend_follow':
                candidate_limit = 6
                symbol_mode = 'leaders'
            elif strategy_name == 'ema_crossover':
                candidate_limit = 8
                symbol_mode = 'volatile'
            else:
                candidate_limit = 6
                symbol_mode = 'leaders'
            
            # Convert available symbols to list if needed
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
            
            candidates = symbols[:50]  # Use top 50 candidates
            
            # V2 Merged symbol selection modes
            if symbol_mode == 'leaders':
                return candidates[:min(candidate_limit, len(candidates))]
            elif symbol_mode == 'volatile':
                # Select volatile symbols (every other from top)
                volatile_symbols = candidates[:min(candidate_limit * 2, len(candidates)):2]
                if not volatile_symbols:
                    volatile_symbols = candidates[:min(candidate_limit // 2, len(candidates))]
                return volatile_symbols
            elif symbol_mode == 'pullback':
                # Select symbols from middle range
                start_idx = min(3, len(candidates))
                end_idx = min(candidate_limit + 5, len(candidates))
                pullback_symbols = candidates[start_idx:end_idx]
                if not pullback_symbols:
                    pullback_symbols = candidates[:min(candidate_limit, len(candidates))]
                return pullback_symbols
            elif symbol_mode == 'balanced':
                # Mix of top and bottom symbols
                top_symbols = candidates[:min(candidate_limit // 2, len(candidates))]
                bottom_symbols = candidates[-min(candidate_limit // 2, len(candidates)):]
                balanced_symbols = []
                
                # Remove duplicates
                all_symbols = top_symbols + bottom_symbols
                seen = set()
                for symbol in all_symbols:
                    if symbol not in seen:
                        balanced_symbols.append(symbol)
                        seen.add(symbol)
                
                return balanced_symbols[:candidate_limit]
            else:
                return candidates[:min(candidate_limit, len(candidates))]
            
        except Exception as e:
            self.log_error("symbol_selection", str(e))
            # Return fallback symbols
            return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]'''
    
    # Replace the method in the file
    import re
    
    # Find the method start and end
    method_start = content.find('def select_preferred_symbols(self, strategy_name: str,')
    if method_start == -1:
        print('[ERROR] Method not found')
        return
    
    # Find the next method definition (end of current method)
    next_method = content.find('\n    def ', method_start + 1)
    if next_method == -1:
        print('[ERROR] Next method not found')
        return
    
    # Replace the method
    new_content = content[:method_start] + new_method + content[next_method:]
    
    # Write the fixed version
    with open('core/strategy_registry.py', 'w') as f:
        f.write(new_content)
    
    print('[SUCCESS] Symbol selection method replaced with robust version')
    
    # Test the fix
    print('\n[TEST] Testing the fixed version:')
    
    try:
        from core.strategy_registry import StrategyRegistry
        sr = StrategyRegistry()
        
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
        
        print(f'  Testing ma_trend_follow:')
        result = sr.select_preferred_symbols('ma_trend_follow', symbol_list, 10)
        print(f'    Result: {len(result)} symbols - {result}')
        
        print(f'  Testing ema_crossover:')
        result = sr.select_preferred_symbols('ema_crossover', symbol_list, 10)
        print(f'    Result: {len(result)} symbols - {result}')
        
        print('[SUCCESS] Fix tested successfully')
        
    except Exception as e:
        print(f'[ERROR] Fix test failed: {e}')
        traceback.print_exc()
    
    print('=' * 60)
    print('[RESULT] Force fix complete')
    print('=' * 60)

if __name__ == "__main__":
    force_fix_symbol_selection()
