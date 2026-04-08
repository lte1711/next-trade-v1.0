#!/usr/bin/env python3
"""
Check Duplicate Management - Check if there's duplicate entry management
"""

import json

def check_duplicate_management():
    """Check if there's duplicate entry management"""
    print('=' * 60)
    print('DUPLICATE ENTRY MANAGEMENT CHECK')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Check pending trades for duplicates
    pending_trades = results.get('pending_trades', [])
    
    print('[PENDING TRADES] Checking for duplicates:')
    
    # Group by symbol
    symbol_trades = {}
    for trade in pending_trades:
        symbol = trade.get('symbol', 'Unknown')
        if symbol not in symbol_trades:
            symbol_trades[symbol] = []
        symbol_trades[symbol].append(trade)
    
    # Check for duplicates
    duplicates_found = False
    for symbol, trades in symbol_trades.items():
        if len(trades) > 1:
            duplicates_found = True
            print(f'  - {symbol}: {len(trades)} duplicate entries')
            
            for i, trade in enumerate(trades, 1):
                timestamp = trade.get('timestamp', 'Unknown')
                strategy = trade.get('strategy', 'Unknown')
                confidence = trade.get('signal_confidence', 0)
                order_id = trade.get('order_id', 'N/A')
                
                print(f'    {i}. Timestamp: {timestamp}')
                print(f'       Strategy: {strategy}')
                print(f'       Confidence: {confidence}')
                print(f'       Order ID: {order_id}')
                print()
    
    if not duplicates_found:
        print('  - No duplicates found')
    
    # Check active positions
    active_positions = results.get('active_positions', {})
    
    print(f'[ACTIVE POSITIONS] Checking for conflicts with pending trades:')
    
    for symbol in symbol_trades:
        if symbol in active_positions:
            print(f'  - {symbol}: Already in active positions!')
            position = active_positions[symbol]
            amount = position.get('amount', 0)
            strategy = position.get('strategy', 'None')
            print(f'    - Amount: {amount}')
            print(f'    - Strategy: {strategy}')
            print(f'    - Pending entries: {len(symbol_trades[symbol])}')
            print()
    
    # Check if there's any duplicate prevention logic
    print('[DUPLICATE PREVENTION] Checking for prevention logic:')
    
    # Check main_runtime.py for duplicate prevention
    try:
        with open('main_runtime.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for duplicate prevention keywords
        prevention_keywords = [
            'duplicate',
            'already',
            'exists',
            'check',
            'prevent',
            'avoid',
            'unique'
        ]
        
        found_prevention = False
        for keyword in prevention_keywords:
            if keyword in content.lower():
                found_prevention = True
                print(f'  - Found "{keyword}" in main_runtime.py')
                
                # Find the lines containing the keyword
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if keyword.lower() in line.lower():
                        print(f'    Line {i}: {line.strip()[:100]}...')
                        break
        
        if not found_prevention:
            print('  - No duplicate prevention logic found in main_runtime.py')
    
    except Exception as e:
        print(f'  - Error checking main_runtime.py: {e}')
    
    # Check trade orchestrator for duplicate prevention
    print('\n[TRADE ORCHESTRATOR] Checking for duplicate prevention:')
    
    try:
        with open('core/trade_orchestrator.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        found_prevention = False
        for keyword in prevention_keywords:
            if keyword in content.lower():
                found_prevention = True
                print(f'  - Found "{keyword}" in trade_orchestrator.py')
                
                # Find the lines containing the keyword
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if keyword.lower() in line.lower():
                        print(f'    Line {i}: {line.strip()[:100]}...')
                        break
        
        if not found_prevention:
            print('  - No duplicate prevention logic found in trade_orchestrator.py')
    
    except Exception as e:
        print(f'  - Error checking trade_orchestrator.py: {e}')
    
    # Check position manager for duplicate prevention
    print('\n[POSITION MANAGER] Checking for duplicate prevention:')
    
    try:
        with open('core/position_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        found_prevention = False
        for keyword in prevention_keywords:
            if keyword in content.lower():
                found_prevention = True
                print(f'  - Found "{keyword}" in position_manager.py')
                
                # Find the lines containing the keyword
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if keyword.lower() in line.lower():
                        print(f'    Line {i}: {line.strip()[:100]}...')
                        break
        
        if not found_prevention:
            print('  - No duplicate prevention logic found in position_manager.py')
    
    except Exception as e:
        print(f'  - Error checking position_manager.py: {e}')
    
    # Summary
    print('\n[SUMMARY]')
    print(f'  - Duplicate entries found: {duplicates_found}')
    print(f'  - Total pending trades: {len(pending_trades)}')
    print(f'  - Unique symbols: {len(symbol_trades)}')
    print(f'  - Active positions: {len(active_positions)}')
    
    if duplicates_found:
        print('\n[ISSUES]')
        print('  - Multiple entries for same symbol detected')
        print('  - No duplicate prevention logic found')
        print('  - This can lead to over-leveraging and risk issues')
        print('  - RECOMMENDATION: Implement duplicate prevention logic')
    
    print('=' * 60)
    print('[RESULT] Duplicate management check complete')
    print('=' * 60)

if __name__ == "__main__":
    check_duplicate_management()
