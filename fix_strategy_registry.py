#!/usr/bin/env python3
"""
Fix Strategy Registry - Fix the indentation and method structure
"""

def fix_strategy_registry():
    """Fix the strategy registry file"""
    print('=' * 60)
    print('FIX STRATEGY REGISTRY')
    print('=' * 60)
    
    # Read the current file
    with open('core/strategy_registry.py', 'r') as f:
        lines = f.readlines()
    
    # Find the problematic method and fix it
    fixed_lines = []
    in_method = False
    method_indent = 0
    
    for i, line in enumerate(lines):
        if 'def select_preferred_symbols(self, strategy_name: str,' in line:
            # Found the method, check its indentation
            method_indent = len(line) - len(line.lstrip())
            in_method = True
            fixed_lines.append(line)
            continue
        
        if in_method:
            # Check if this is the docstring
            if '"""V2 Merged: Select preferred symbols for a strategy"""' in line:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= method_indent:
                    # Fix indentation
                    fixed_line = ' ' * (method_indent + 4) + line.lstrip()
                    fixed_lines.append(fixed_line)
                    continue
            
            # Check if we've reached the next method
            if line.strip().startswith('def ') and len(line) - len(line.lstrip()) <= method_indent:
                in_method = False
                fixed_lines.append(line)
                continue
        
        fixed_lines.append(line)
    
    # Write the fixed file
    with open('core/strategy_registry.py', 'w') as f:
        f.writelines(fixed_lines)
    
    print('[SUCCESS] Strategy registry fixed')
    
    # Test the fix
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
        import traceback
        traceback.print_exc()
    
    print('=' * 60)
    print('[RESULT] Strategy registry fix complete')
    print('=' * 60)

if __name__ == "__main__":
    fix_strategy_registry()
