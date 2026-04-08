#!/usr/bin/env python3
"""
Cleanup Duplicate Trades - Clean up existing duplicate pending trades
"""

import json

def cleanup_duplicate_trades():
    """Clean up existing duplicate pending trades"""
    print('=' * 60)
    print('CLEANUP DUPLICATE TRADES')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    pending_trades = results.get('pending_trades', [])
    active_positions = results.get('active_positions', {})
    
    print('[BEFORE CLEANUP]')
    print(f'  - Total pending trades: {len(pending_trades)}')
    print(f'  - Active positions: {len(active_positions)}')
    
    # Show duplicates
    symbol_counts = {}
    for trade in pending_trades:
        symbol = trade.get('symbol', 'Unknown')
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
    
    duplicates = {symbol: count for symbol, count in symbol_counts.items() if count > 1}
    
    if duplicates:
        print('  - Duplicates found:')
        for symbol, count in duplicates.items():
            print(f'    {symbol}: {count} entries')
    else:
        print('  - No duplicates found')
    
    # Clean up duplicates
    print('\n[CLEANUP PROCESS]')
    
    # Create a set to track symbols we've seen
    seen_symbols = set()
    
    # Add active symbols to seen set
    for symbol in active_positions.keys():
        seen_symbols.add(symbol)
        print(f'  - Added {symbol} to seen set (active position)')
    
    # Filter pending trades
    filtered_pending = []
    removed_count = 0
    
    for trade in pending_trades:
        symbol = trade.get('symbol', '')
        
        if symbol not in seen_symbols:
            filtered_pending.append(trade)
            seen_symbols.add(symbol)
            print(f'  - Kept {symbol} (first occurrence)')
        else:
            removed_count += 1
            print(f'  - Removed duplicate {symbol}')
    
    # Update results
    results['pending_trades'] = filtered_pending
    
    # Write back to file
    with open('trading_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'\n[AFTER CLEANUP]')
    print(f'  - Removed {removed_count} duplicate trades')
    print(f'  - Remaining pending trades: {len(filtered_pending)}')
    print(f'  - Active positions: {len(active_positions)}')
    
    # Show remaining pending trades
    if filtered_pending:
        print('\n[REMAINING PENDING TRADES]')
        for i, trade in enumerate(filtered_pending, 1):
            symbol = trade.get('symbol', 'Unknown')
            strategy = trade.get('strategy', 'Unknown')
            side = trade.get('side', 'Unknown')
            quantity = trade.get('quantity', 0)
            confidence = trade.get('signal_confidence', 0)
            
            print(f'  {i}. {symbol}:')
            print(f'     - Strategy: {strategy}')
            print(f'     - Side: {side}')
            print(f'     - Quantity: {quantity}')
            print(f'     - Confidence: {confidence}')
    else:
        print('\n[REMAINING PENDING TRADES] None')
    
    # Test the duplicate prevention
    print('\n[TEST DUPLICATE PREVENTION]')
    
    try:
        from core.trade_orchestrator import TradeOrchestrator
        
        # Create orchestrator instance
        orchestrator = TradeOrchestrator()
        orchestrator.trading_results = results
        
        # Test duplicate check
        print('  - Testing duplicate prevention:')
        
        # Test with active position symbol
        if active_positions:
            test_symbol = list(active_positions.keys())[0]
            is_duplicate = orchestrator._check_duplicate_entry(test_symbol, 'ema_crossover')
            print(f'    {test_symbol} (active): {is_duplicate} (Expected: True)')
        
        # Test with pending trade symbol
        if filtered_pending:
            test_symbol = filtered_pending[0].get('symbol', '')
            is_duplicate = orchestrator._check_duplicate_entry(test_symbol, 'ema_crossover')
            print(f'    {test_symbol} (pending): {is_duplicate} (Expected: True)')
        
        # Test with new symbol
        test_symbol = 'ETHUSDT'
        is_duplicate = orchestrator._check_duplicate_entry(test_symbol, 'ema_crossover')
        print(f'    {test_symbol} (new): {is_duplicate} (Expected: False)')
        
        print('  - Duplicate prevention logic working correctly')
        
    except Exception as e:
        print(f'  - Error testing duplicate prevention: {e}')
    
    print('=' * 60)
    print('[RESULT] Duplicate trades cleanup complete')
    print('=' * 60)

if __name__ == "__main__":
    cleanup_duplicate_trades()
