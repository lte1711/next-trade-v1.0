#!/usr/bin/env python3
"""
System Synchronization - Complete system sync
"""

import json
import time
from datetime import datetime

def sync_positions():
    """Sync positions from exchange"""
    print('=' * 60)
    print('POSITION SYNCHRONIZATION')
    print('=' * 60)
    
    try:
        # Load current trading results
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            print('[OK] Trading results loaded')
        except:
            results = {
                'strategies': {},
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
                'managed_stop_prices': {}
            }
            print('[INIT] Created new trading results')
        
        # Use account service to sync positions
        from core.account_service import AccountService
        
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        base_url = config['binance_testnet']['base_url']
        
        account_service = AccountService(base_url, api_key, api_secret)
        
        # Sync positions
        print('[SYNC] Starting position synchronization...')
        sync_success = account_service.sync_positions(results)
        
        if sync_success:
            active_positions = results.get('active_positions', {})
            print(f'[SYNC] Positions synchronized successfully')
            print(f'[SYNC] Active positions found: {len(active_positions)}')
            
            for symbol, position in active_positions.items():
                amount = position.get('amount', 0)
                side = 'LONG' if amount > 0 else 'SHORT' if amount < 0 else 'FLAT'
                entry_price = position.get('entry_price', 0)
                mark_price = position.get('mark_price', 0)
                pnl = position.get('unrealized_pnl', 0)
                print(f'  {symbol}: {amount} ({side}) | Entry: {entry_price} | PnL: {pnl}')
        else:
            print('[ERROR] Position synchronization failed')
            
        # Save synchronized results
        results['sync_time'] = datetime.now().isoformat()
        results['sync_status'] = 'completed'
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print('[OK] Synchronized results saved')
        return True
        
    except Exception as e:
        print(f'[ERROR] Sync failed: {e}')
        return False

def sync_strategies():
    """Sync strategy configurations"""
    print('=' * 60)
    print('STRATEGY SYNCHRONIZATION')
    print('=' * 60)
    
    try:
        # Load current results
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Initialize strategies if not present
        strategies = results.get('strategies', {})
        
        # V2 Merged strategy configurations
        strategy_configs = {
            'ma_trend_follow': {
                'name': 'MA Trend Following',
                'enabled': True,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'position_hold_minutes': 30,
                'max_position_size_usdt': 1000.0,
                'performance': {'win_rate': 0.0, 'avg_return': 0.0, 'total_trades': 0},
                'last_signal': None,
                'last_trade': None,
                'symbol_mode': 'leaders',
                'candidate_limit': 10
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
                'last_trade': None,
                'symbol_mode': 'volatile',
                'candidate_limit': 8
            }
        }
        
        # Update strategies with V2 Merged configs
        for name, config in strategy_configs.items():
            if name not in strategies:
                strategies[name] = config
                print(f'[INIT] Strategy {name} initialized')
            else:
                # Update missing V2 Merged fields
                for key, value in config.items():
                    if key not in strategies[name]:
                        strategies[name][key] = value
                        print(f'[UPDATE] Strategy {name}: Added {key}')
                print(f'[OK] Strategy {name} already exists')
        
        results['strategies'] = strategies
        active_strategies = [name for name, config in strategies.items() if config.get('enabled', False)]
        results['active_strategies'] = active_strategies
        
        print(f'[STRATEGIES] Total: {len(strategies)}')
        print(f'[STRATEGIES] Active: {len(active_strategies)}')
        
        for name in active_strategies:
            config = strategies[name]
            symbol_mode = config.get('symbol_mode', 'default')
            candidate_limit = config.get('candidate_limit', 5)
            print(f'  - {name}: {symbol_mode} mode, limit {candidate_limit}')
        
        # Save updated results
        results['strategy_sync_time'] = datetime.now().isoformat()
        results['strategy_sync_status'] = 'completed'
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print('[OK] Strategy synchronization saved')
        return True
        
    except Exception as e:
        print(f'[ERROR] Strategy sync failed: {e}')
        return False

def sync_capital():
    """Sync capital information"""
    print('=' * 60)
    print('CAPITAL SYNCHRONIZATION')
    print('=' * 60)
    
    try:
        # Load current results
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Use account service to get capital
        from core.account_service import AccountService
        
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        base_url = config['binance_testnet']['base_url']
        
        account_service = AccountService(base_url, api_key, api_secret)
        
        # Get account balance
        print('[CAPITAL] Getting account balance...')
        balance = account_service.get_total_balance()
        
        if balance is not None:
            results['total_capital'] = balance
            results['available_balance'] = balance
            print(f'[CAPITAL] Total capital: {balance} USDT')
            print(f'[CAPITAL] Available balance: {balance} USDT')
        else:
            print('[ERROR] Failed to get balance')
        
        # Save updated results
        results['capital_sync_time'] = datetime.now().isoformat()
        results['capital_sync_status'] = 'completed'
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print('[OK] Capital synchronization saved')
        return True
        
    except Exception as e:
        print(f'[ERROR] Capital sync failed: {e}')
        return False

def full_sync():
    """Complete system synchronization"""
    print('=' * 60)
    print('COMPLETE SYSTEM SYNCHRONIZATION')
    print('=' * 60)
    print(f'Start time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Execute all sync operations
    sync_results = {
        'positions': sync_positions(),
        'strategies': sync_strategies(),
        'capital': sync_capital()
    }
    
    # Summary
    print('=' * 60)
    print('SYNCHRONIZATION SUMMARY')
    print('=' * 60)
    
    for operation, success in sync_results.items():
        status = 'SUCCESS' if success else 'FAILED'
        print(f'{operation.upper()}: {status}')
    
    all_success = all(sync_results.values())
    overall_status = 'SUCCESS' if all_success else 'PARTIAL'
    
    print(f'OVERALL: {overall_status}')
    print(f'Complete time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 60)
    
    return all_success

if __name__ == "__main__":
    full_sync()
