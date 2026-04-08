#!/usr/bin/env python3
"""
Trading Status Checker - Monitor trading system status
"""

import json
import time
from datetime import datetime

def check_trading_status():
    """Check and display current trading status"""
    try:
        # Read trading results
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        print('=' * 60)
        print('TRADING TEST STATUS')
        print('=' * 60)
        print(f'Check time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Basic stats
        active_positions = results.get('active_positions', {})
        print(f'Active positions: {len(active_positions)}')
        
        if active_positions:
            print('Position details:')
            for symbol, pos in active_positions.items():
                amount = pos.get('amount', 0)
                side = 'LONG' if amount > 0 else 'SHORT' if amount < 0 else 'FLAT'
                pnl = pos.get('unrealized_pnl', 0)
                print(f'  {symbol}: {amount} ({side}) | PnL: {pnl:.4f} USDT')
        
        print(f'Total trades: {results.get("total_trades", 0)}')
        print(f'Entry failures: {results.get("entry_failures", 0)}')
        print(f'Available balance: {results.get("available_balance", 0):.2f} USDT')
        print(f'Total capital: {results.get("total_capital", 0):.2f} USDT')
        
        # Strategy status
        strategies = results.get('strategies', {})
        print(f'Active strategies: {len(strategies)}')
        
        for name, strategy in strategies.items():
            enabled = strategy.get('enabled', False)
            last_signal = strategy.get('last_signal')
            print(f'  {name}: enabled={enabled}, last_signal={last_signal}')
        
        # Error status
        last_error = results.get('last_error')
        if last_error:
            print(f'Last error: {last_error}')
        else:
            print('No errors reported')
        
        # Recent activity
        recent_closed = results.get('recently_closed_symbols', {})
        if recent_closed:
            print(f'Recently closed: {len(recent_closed)} symbols')
        
        # Partial take profit state
        partial_tp = results.get('partial_take_profit_state', {})
        if partial_tp:
            print(f'Partial TP active: {len(partial_tp)} positions')
        
        print('=' * 60)
        
        return True
        
    except FileNotFoundError:
        print('[ERROR] trading_results.json not found')
        return False
    except json.JSONDecodeError:
        print('[ERROR] Invalid JSON in trading_results.json')
        return False
    except Exception as e:
        print(f'[ERROR] Status check failed: {e}')
        return False

def check_system_health():
    """Check system health indicators"""
    try:
        print('SYSTEM HEALTH CHECK')
        print('-' * 30)
        
        # Check core modules
        try:
            from core.market_data_service import MarketDataService
            from core.position_manager import PositionManager
            from core.account_service import AccountService
            from core.strategy_registry import StrategyRegistry
            print('[OK] Core modules available')
        except ImportError as e:
            print(f'[ERROR] Core module import failed: {e}')
        
        # Check configuration
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            print('[OK] Configuration loaded')
        except Exception as e:
            print(f'[ERROR] Configuration failed: {e}')
        
        # Check API connectivity
        try:
            import requests
            response = requests.get('https://demo-fapi.binance.com/fapi/v1/time', timeout=5)
            if response.status_code == 200:
                print('[OK] Binance API reachable')
            else:
                print(f'[WARN] Binance API status: {response.status_code}')
        except Exception as e:
            print(f'[ERROR] Binance API unreachable: {e}')
        
        print('-' * 30)
        
    except Exception as e:
        print(f'[ERROR] Health check failed: {e}')

if __name__ == "__main__":
    check_system_health()
    check_trading_status()
