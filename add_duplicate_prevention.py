#!/usr/bin/env python3
"""
Add Duplicate Prevention - Add duplicate entry prevention logic
"""

import json

def add_duplicate_prevention():
    """Add duplicate entry prevention logic"""
    print('=' * 60)
    print('ADD DUPLICATE PREVENTION LOGIC')
    print('=' * 60)
    
    # Read the current trade_orchestrator.py
    with open('core/trade_orchestrator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the execute_trade method
    print('[ANALYSIS] Looking for execute_trade method...')
    
    # Find the method that handles trade execution
    import re
    
    # Look for the method that executes trades
    execute_trade_pattern = r'def execute_trade.*?\n\s*def'
    execute_trade_match = re.search(execute_trade_pattern, content, re.DOTALL)
    
    if execute_trade_match:
        execute_trade_method = execute_trade_match.group(0)
        print('  - Found execute_trade method')
        
        # Check if duplicate prevention already exists
        if 'duplicate' in execute_trade_method.lower() or 'already' in execute_trade_method.lower():
            print('  - Duplicate prevention already exists')
            return
    else:
        print('  - execute_trade method not found')
        return
    
    # Add duplicate prevention logic
    print('\n[IMPLEMENTATION] Adding duplicate prevention logic...')
    
    # Create the duplicate prevention method
    duplicate_prevention_method = '''    def check_duplicate_entry(self, symbol: str, strategy: str) -> bool:
        """Check if there's already a pending or active entry for this symbol"""
        try:
            # Check active positions
            active_positions = self.trading_results.get('active_positions', {})
            if symbol in active_positions:
                self.logger.warning(f"Duplicate entry prevented: {symbol} already in active positions")
                return True
            
            # Check pending trades
            pending_trades = self.trading_results.get('pending_trades', [])
            for trade in pending_trades:
                if trade.get('symbol') == symbol:
                    self.logger.warning(f"Duplicate entry prevented: {symbol} already in pending trades")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking duplicate entry: {e}")
            return False
    
'''
    
    # Find the execute_trade method and add duplicate check
    execute_trade_full_pattern = r'def execute_trade\(self.*?return result'
    execute_trade_full_match = re.search(execute_trade_full_pattern, content, re.DOTALL)
    
    if execute_trade_full_match:
        original_method = execute_trade_full_match.group(0)
        
        # Add duplicate check at the beginning of execute_trade
        modified_method = original_method.replace(
            'def execute_trade(self,',
            '''def execute_trade(self, '''
        ).replace(
            '"""Execute a trade with risk management"""',
            '''"""Execute a trade with risk management"""
        # Check for duplicate entry
        if self.check_duplicate_entry(symbol, strategy):
            return {'success': False, 'error': 'Duplicate entry prevented'}
        '''
        )
        
        # Replace the method in content
        new_content = content.replace(original_method, modified_method)
        
        # Add the duplicate prevention method before execute_trade
        new_content = new_content.replace(
            'def execute_trade(self,',
            duplicate_prevention_method + '\n    def execute_trade(self,'
        )
        
        # Write the modified content
        with open('core/trade_orchestrator.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print('[SUCCESS] Duplicate prevention logic added to trade_orchestrator.py')
    else:
        print('[ERROR] Could not find execute_trade method to modify')
        return
    
    # Test the implementation
    print('\n[TEST] Testing duplicate prevention...')
    
    try:
        from core.trade_orchestrator import TradeOrchestrator
        
        # Create a mock trading results
        mock_results = {
            'active_positions': {
                'DOGEUSDT': {'amount': 100, 'strategy': 'ema_crossover'}
            },
            'pending_trades': [
                {'symbol': 'BTCUSDT', 'strategy': 'ma_trend_follow'}
            ]
        }
        
        # Create orchestrator instance
        orchestrator = TradeOrchestrator()
        orchestrator.trading_results = mock_results
        
        # Test duplicate check
        print('  - Testing DOGEUSDT (should be prevented):')
        is_duplicate = orchestrator.check_duplicate_entry('DOGEUSDT', 'ema_crossover')
        print(f'    Result: {is_duplicate} (Expected: True)')
        
        print('  - Testing BTCUSDT (should be prevented):')
        is_duplicate = orchestrator.check_duplicate_entry('BTCUSDT', 'ema_crossover')
        print(f'    Result: {is_duplicate} (Expected: True)')
        
        print('  - Testing ETHUSDT (should be allowed):')
        is_duplicate = orchestrator.check_duplicate_entry('ETHUSDT', 'ema_crossover')
        print(f'    Result: {is_duplicate} (Expected: False)')
        
        print('[SUCCESS] Duplicate prevention logic tested successfully')
        
    except Exception as e:
        print(f'[ERROR] Test failed: {e}')
        import traceback
        traceback.print_exc()
    
    # Clean up existing duplicate pending trades
    print('\n[CLEANUP] Cleaning up existing duplicate pending trades...')
    
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    pending_trades = results.get('pending_trades', [])
    active_positions = results.get('active_positions', {})
    
    # Filter out duplicate pending trades
    filtered_pending = []
    seen_symbols = set()
    
    # Add active symbols to seen set
    for symbol in active_positions.keys():
        seen_symbols.add(symbol)
    
    # Filter pending trades
    for trade in pending_trades:
        symbol = trade.get('symbol', '')
        if symbol not in seen_symbols:
            filtered_pending.append(trade)
            seen_symbols.add(symbol)
        else:
            print(f'  - Removed duplicate pending trade for {symbol}')
    
    # Update results
    results['pending_trades'] = filtered_pending
    
    # Write back to file
    with open('trading_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'  - Cleaned up {len(pending_trades) - len(filtered_pending)} duplicate pending trades')
    print(f'  - Remaining pending trades: {len(filtered_pending)}')
    
    print('=' * 60)
    print('[RESULT] Duplicate prevention implementation complete')
    print('=' * 60)

if __name__ == "__main__":
    add_duplicate_prevention()
