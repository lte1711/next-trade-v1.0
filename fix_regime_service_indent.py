#!/usr/bin/env python3
"""
Fix Regime Service Indentation - Fix the indentation issue
"""

def fix_regime_service_indent():
    """Fix the indentation issue in market_regime_service.py"""
    print('=' * 60)
    print('FIX REGIME SERVICE INDENTATION')
    print('=' * 60)
    
    # Read the current file
    with open('core/market_regime_service.py', 'r') as f:
        lines = f.readlines()
    
    print('[ANALYSIS] Fixing indentation issues:')
    
    # Find the problematic line
    for i, line in enumerate(lines):
        if '_calculate_adx' in line and 'def' in line:
            print(f'  - Found _calculate_adx at line {i+1}')
            
            # Check if the next line is properly indented
            if i+1 < len(lines):
                next_line = lines[i+1]
                if '"""Calculate ADX' in next_line:
                    if not next_line.startswith('        '):  # Should be 8 spaces
                        print(f'  - Fixing indentation at line {i+2}')
                        lines[i+1] = '        ' + next_line.strip() + '\n'
    
    # Write back the fixed file
    with open('core/market_regime_service.py', 'w') as f:
        f.writelines(lines)
    
    print('[SUCCESS] Indentation fixed')
    
    # Test the fix
    print('\n[TEST] Testing the fixed service:')
    
    try:
        from core.market_regime_service import MarketRegimeService
        
        mrs = MarketRegimeService()
        
        # Test with simple data
        test_prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138]
        test_volumes = [1000000] * len(test_prices)
        
        result = mrs.analyze_market_regime(test_prices, test_volumes)
        
        print(f'  - Test result: {result.get("regime", "UNKNOWN")}')
        print(f'  - ADX: {result.get("trend_strength", 0):.2f}')
        print(f'  - Volatility: {result.get("volatility_level", 0):.4f}')
        
        if result.get('trend_strength', 0) > 0:
            print('  - Status: ADX calculation working')
        else:
            print('  - Status: ADX calculation still has issues')
        
    except Exception as e:
        print(f'  - Error: {e}')
    
    print('=' * 60)
    print('[RESULT] Regime service indentation fix complete')
    print('=' * 60)

if __name__ == "__main__":
    fix_regime_service_indent()
