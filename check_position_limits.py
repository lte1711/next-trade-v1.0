#!/usr/bin/env python3
"""
Position Limits Check - Verify maximum positions configuration
"""

import json

def check_position_limits():
    """Check maximum positions configuration and current status"""
    print('=' * 60)
    print('MAXIMUM POSITIONS CONFIGURATION CHECK')
    print('=' * 60)
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Check trading config
    trading_config = config.get('trading_config', {})
    max_open_positions = trading_config.get('max_open_positions', 1)
    position_sync_interval = trading_config.get('position_sync_interval', 30)
    position_limit_check = trading_config.get('position_limit_check', True)
    excess_position_close = trading_config.get('excess_position_close', True)
    
    print(f'[CONFIG] Max open positions: {max_open_positions}')
    print(f'[CONFIG] Position sync interval: {position_sync_interval}s')
    print(f'[CONFIG] Position limit check: {position_limit_check}')
    print(f'[CONFIG] Excess position close: {excess_position_close}')
    
    # Load current state
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    active_positions = results.get('active_positions', {})
    current_positions = len(active_positions)
    
    print(f'[CURRENT] Active positions: {current_positions}')
    print(f'[CURRENT] Available slots: {max_open_positions - current_positions}')
    
    # Show position details
    if active_positions:
        print('[POSITIONS] Current positions:')
        for i, (symbol, position) in enumerate(active_positions.items(), 1):
            amount = position.get('amount', 0)
            side = 'LONG' if amount > 0 else 'SHORT' if amount < 0 else 'FLAT'
            entry_price = position.get('entry_price', 0)
            pnl = position.get('unrealized_pnl', 0)
            value = abs(amount * entry_price) if entry_price > 0 else 0
            print(f'  {i}. {symbol}: {amount} ({side}) | Entry: {entry_price} | PnL: {pnl} | Value: {value:.2f} USDT')
    
    # Check strategy-specific limits
    strategies = results.get('strategies', {})
    print(f'[STRATEGIES] Strategy configurations:')
    for name, strategy in strategies.items():
        enabled = strategy.get('enabled', False)
        max_size = strategy.get('max_position_size_usdt', 0)
        print(f'  - {name}: enabled={enabled}, max_size={max_size} USDT')
    
    # Check if we can open new positions
    available_slots = max_open_positions - current_positions
    can_open_new = available_slots > 0
    
    print(f'[CAPACITY] Can open new positions: {can_open_new}')
    print(f'[CAPACITY] Available slots: {available_slots}')
    
    # Simulate position opening
    if can_open_new:
        print(f'[SIMULATION] Can open up to {available_slots} more positions')
        print('[SIMULATION] New entries will be allowed')
    else:
        print('[SIMULATION] Position limit reached')
        print('[SIMULATION] New entries will be blocked')
        print('[SIMULATION] Excess position handling will trigger')
    
    # Check V2 Merged position limit logic
    print('=' * 60)
    print('V2 MERGED POSITION LIMIT LOGIC')
    print('=' * 60)
    
    try:
        with open('main_runtime.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'len(active_positions) > self.max_open_positions' in content:
            print('[SYSTEM] Position limit check: FOUND in main_runtime.py')
            print('[SYSTEM] V2 Merged excess position handling: ENABLED')
        else:
            print('[SYSTEM] Position limit check: NOT FOUND')
            print('[WARNING] May need to implement position limit logic')
        
        if 'excess_position_close' in content:
            print('[SYSTEM] Excess position close: CONFIGURED')
        else:
            print('[SYSTEM] Excess position close: NOT CONFIGURED')
            
    except Exception as e:
        print(f'[ERROR] Failed to check main_runtime.py: {e}')
    
    print('=' * 60)
    print('SUMMARY')
    print('=' * 60)
    print(f'[SUMMARY] Maximum positions allowed: {max_open_positions}')
    print(f'[SUMMARY] Currently open: {current_positions}')
    print(f'[SUMMARY] Available for new entries: {available_slots}')
    print(f'[SUMMARY] Can accept new positions: {can_open_new}')
    print('=' * 60)
    
    return {
        'max_positions': max_open_positions,
        'current_positions': current_positions,
        'available_slots': available_slots,
        'can_open_new': can_open_new
    }

if __name__ == "__main__":
    check_position_limits()
