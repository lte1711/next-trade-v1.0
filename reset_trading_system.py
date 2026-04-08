#!/usr/bin/env python3
"""
Trading System Reset - Clean reset for trading system
"""

import json
import os
from datetime import datetime

def reset_trading_system():
    """Reset trading system to clean state"""
    print('=' * 60)
    print('TRADING SYSTEM RESET')
    print('=' * 60)
    
    # 1. Clear trading results
    trading_state = {
        'strategies': {
            'ma_trend_follow': {
                'name': 'MA Trend Following',
                'enabled': True,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'position_hold_minutes': 30,
                'max_position_size_usdt': 1000.0,
                'performance': {'win_rate': 0.0, 'avg_return': 0.0, 'total_trades': 0},
                'last_signal': None,
                'last_trade': None
            },
            'ema_crossover': {
                'name': 'EMA Crossover',
                'enabled': True,
                'stop_loss_pct': 0.015,
                'take_profit_pct': 0.03,
                'position_hold_minutes': 30,
                'max_position_size_usdt': 800.0,
                'performance': {'win_rate': 0.0, 'avg_return': 0.0, 'total_trades': 0},
                'last_signal': None,
                'last_trade': None
            }
        },
        'active_positions': {},
        'pending_trades': [],
        'closed_trades': [],
        'real_orders': [],
        'total_trades': 0,
        'entry_failures': 0,
        'available_balance': 0.0,
        'total_capital': 0.0,
        'last_error': None,
        'error_count': 0,
        'system_errors': [],
        'entry_mode_performance': {},
        'recently_closed_symbols': {},
        'position_entry_times': {},
        'partial_take_profit_state': {},
        'managed_stop_prices': {},
        'last_cycle': None,
        'reset_time': datetime.now().isoformat()
    }
    
    # Save clean state
    with open('trading_results.json', 'w') as f:
        json.dump(trading_state, f, indent=2, default=str)
    
    print('[CLEAN] Trading results reset to clean state')
    print('[CLEAN] Strategies initialized: ma_trend_follow, ema_crossover')
    print('[CLEAN] All counters reset to 0')
    
    # 2. Clean any temporary files
    temp_files = [
        'temp_orders.json',
        'temp_positions.json',
        'error_log.json'
    ]
    
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f'[CLEAN] Removed temporary file: {temp_file}')
    
    print('=' * 60)
    print('[READY] Trading system reset complete')
    print('[READY] Ready for fresh trading session')
    print('=' * 60)

if __name__ == "__main__":
    reset_trading_system()
