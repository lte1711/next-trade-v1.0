#!/usr/bin/env python3
"""
Fix Signal Engine Init - Fix the SignalEngine initialization issue
"""

def fix_signal_engine_init():
    """Fix the SignalEngine initialization issue"""
    print('=' * 60)
    print('FIX SIGNAL ENGINE INITIALIZATION')
    print('=' * 60)
    
    # Check SignalEngine constructor
    try:
        from core.signal_engine import SignalEngine
        
        # Check the constructor signature
        import inspect
        sig = inspect.signature(SignalEngine.__init__)
        print(f'  - SignalEngine.__init__ signature: {sig}')
        
        # Try to create with correct arguments
        try:
            se = SignalEngine()
            print('  - SignalEngine created with no arguments')
        except Exception as e:
            print(f'  - Error with no arguments: {e}')
            
            try:
                from core.indicator_service import IndicatorService
                from core.market_regime_service import MarketRegimeService
                
                se = SignalEngine(IndicatorService(), MarketRegimeService())
                print('  - SignalEngine created with 2 arguments')
            except Exception as e2:
                print(f'  - Error with 2 arguments: {e2}')
        
    except Exception as e:
        print(f'  - Error checking SignalEngine: {e}')
    
    # Fix the trading cycle script
    print('\n[FIX] Updating trading cycle script...')
    
    try:
        with open('execute_next_trading_cycle.py', 'r') as f:
            content = f.read()
        
        # Fix the SignalEngine initialization
        old_line = 'signal_engine = SignalEngine(IndicatorService(), MarketRegimeService())'
        new_line = 'signal_engine = SignalEngine()'
        
        if old_line in content:
            new_content = content.replace(old_line, new_line)
            
            with open('execute_next_trading_cycle.py', 'w') as f:
                f.write(new_content)
            
            print('  - SignalEngine initialization fixed')
        else:
            print('  - SignalEngine initialization line not found')
    
    except Exception as e:
        print(f'  - Error fixing script: {e}')
    
    print('=' * 60)
    print('[FIX COMPLETE]')
    print('=' * 60)

if __name__ == "__main__":
    fix_signal_engine_init()
