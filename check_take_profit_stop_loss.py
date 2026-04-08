#!/usr/bin/env python3
"""
Check Take Profit and Stop Loss - Analyze current TP/SL settings
"""

import json

def check_take_profit_stop_loss():
    """Check current take profit and stop loss settings"""
    print('=' * 60)
    print('TAKE PROFIT AND STOP LOSS ANALYSIS')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Check active positions
    active_positions = results.get('active_positions', {})
    
    print('[ACTIVE POSITIONS] Current TP/SL settings:')
    
    for symbol, position in active_positions.items():
        print(f'\n  {symbol}:')
        
        # Basic position info
        amount = position.get('amount', 0)
        entry_price = position.get('entry_price', 0)
        current_price = position.get('current_price', 0)
        side = position.get('side', 'UNKNOWN')
        strategy = position.get('strategy', 'None')
        
        print(f'    - Side: {side}')
        print(f'    - Amount: {amount}')
        print(f'    - Entry Price: {entry_price}')
        print(f'    - Current Price: {current_price}')
        print(f'    - Strategy: {strategy}')
        
        # TP/SL settings
        stop_loss_pct = position.get('stop_loss_pct')
        take_profit_pct = position.get('take_profit_pct')
        
        if stop_loss_pct is not None:
            print(f'    - Stop Loss: {stop_loss_pct:.2%}')
            
            # Calculate stop loss price
            if side == 'LONG':
                stop_loss_price = entry_price * (1 - stop_loss_pct)
                print(f'    - Stop Loss Price: {stop_loss_price:.6f}')
            else:
                stop_loss_price = entry_price * (1 + stop_loss_pct)
                print(f'    - Stop Loss Price: {stop_loss_price:.6f}')
        else:
            print(f'    - Stop Loss: NOT SET')
        
        if take_profit_pct is not None:
            print(f'    - Take Profit: {take_profit_pct:.2%}')
            
            # Calculate take profit price
            if side == 'LONG':
                take_profit_price = entry_price * (1 + take_profit_pct)
                print(f'    - Take Profit Price: {take_profit_price:.6f}')
            else:
                take_profit_price = entry_price * (1 - take_profit_pct)
                print(f'    - Take Profit Price: {take_profit_price:.6f}')
        else:
            print(f'    - Take Profit: NOT SET')
        
        # Partial take profit state
        partial_tp_state = position.get('partial_tp_state', {})
        if partial_tp_state:
            print(f'    - Partial TP State: {partial_tp_state}')
        else:
            print(f'    - Partial TP State: Empty')
        
        # Managed stop price
        managed_stop_price = position.get('managed_stop_price')
        if managed_stop_price is not None:
            print(f'    - Managed Stop Price: {managed_stop_price}')
        else:
            print(f'    - Managed Stop Price: NOT SET')
    
    # Check pending trades
    pending_trades = results.get('pending_trades', [])
    
    print(f'\n[PENDING TRADES] TP/SL settings:')
    
    for trade in pending_trades:
        symbol = trade.get('symbol', 'Unknown')
        strategy = trade.get('strategy', 'Unknown')
        side = trade.get('side', 'Unknown')
        stop_loss_pct = trade.get('stop_loss_pct')
        take_profit_pct = trade.get('take_profit_pct')
        
        print(f'\n  {symbol} (Pending):')
        print(f'    - Strategy: {strategy}')
        print(f'    - Side: {side}')
        
        if stop_loss_pct is not None:
            print(f'    - Stop Loss: {stop_loss_pct:.2%}')
        else:
            print(f'    - Stop Loss: NOT SET')
        
        if take_profit_pct is not None:
            print(f'    - Take Profit: {take_profit_pct:.2%}')
        else:
            print(f'    - Take Profit: NOT SET')
    
    # Check strategy configurations
    strategies = results.get('strategies', {})
    
    print(f'\n[STRATEGY CONFIGURATIONS] Default TP/SL settings:')
    
    for name, strategy in strategies.items():
        enabled = strategy.get('enabled', False)
        stop_loss_pct = strategy.get('stop_loss_pct')
        take_profit_pct = strategy.get('take_profit_pct')
        
        print(f'\n  {name}:')
        print(f'    - Enabled: {enabled}')
        
        if stop_loss_pct is not None:
            print(f'    - Default Stop Loss: {stop_loss_pct:.2%}')
        else:
            print(f'    - Default Stop Loss: NOT SET')
        
        if take_profit_pct is not None:
            print(f'    - Default Take Profit: {take_profit_pct:.2%}')
        else:
            print(f'    - Default Take Profit: NOT SET')
    
    # Check V2 Merged risk configurations
    print(f'\n[V2 MERGED RISK CONFIGURATIONS] Advanced TP/SL settings:')
    
    for name, strategy in strategies.items():
        risk_config = strategy.get('risk_config', {})
        
        if risk_config:
            print(f'\n  {name} (V2 Merged):')
            
            # Basic TP/SL
            stop_loss_pct = risk_config.get('stop_loss_pct')
            take_profit_pct = risk_config.get('take_profit_pct')
            
            if stop_loss_pct is not None:
                print(f'    - Stop Loss: {stop_loss_pct:.2%}')
            
            if take_profit_pct is not None:
                print(f'    - Take Profit: {take_profit_pct:.2%}')
            
            # Partial take profit settings
            partial_tp1_pct = risk_config.get('partial_tp1_pct')
            partial_tp2_pct = risk_config.get('partial_tp2_pct')
            fast_tp1_pct = risk_config.get('fast_tp1_pct')
            fast_tp2_pct = risk_config.get('fast_tp2_pct')
            fast_tight_stop_loss_pct = risk_config.get('fast_tight_stop_loss_pct')
            fast_tp1_close_ratio = risk_config.get('fast_tp1_close_ratio')
            
            if partial_tp1_pct is not None:
                print(f'    - Partial TP1: {partial_tp1_pct:.2%}')
            
            if partial_tp2_pct is not None:
                print(f'    - Partial TP2: {partial_tp2_pct:.2%}')
            
            if fast_tp1_pct is not None:
                print(f'    - Fast TP1: {fast_tp1_pct:.2%}')
            
            if fast_tp2_pct is not None:
                print(f'    - Fast TP2: {fast_tp2_pct:.2%}')
            
            if fast_tight_stop_loss_pct is not None:
                print(f'    - Fast Tight Stop Loss: {fast_tight_stop_loss_pct:.2%}')
            
            if fast_tp1_close_ratio is not None:
                print(f'    - Fast TP1 Close Ratio: {fast_tp1_close_ratio:.2%}')
            
            # Session multipliers
            session_multipliers = risk_config.get('session_multipliers', {})
            if session_multipliers:
                print(f'    - Session Multipliers:')
                for session, multipliers in session_multipliers.items():
                    stop_mult = multipliers.get('stop', 1.0)
                    take_mult = multipliers.get('take', 1.0)
                    print(f'      {session}: Stop x{stop_mult}, Take x{take_mult}')
    
    print('=' * 60)
    print('[RESULT] Take profit and stop loss analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    check_take_profit_stop_loss()
