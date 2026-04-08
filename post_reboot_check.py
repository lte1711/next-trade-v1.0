#!/usr/bin/env python3
"""
Post-Reboot System Check - Verify system after hardware reboot
"""

import json
import os
import time
from datetime import datetime

def post_reboot_check():
    """Comprehensive system check after reboot"""
    print('=' * 60)
    print('NEXT-TRADE V1.2.1 - POST-REBOOT SYSTEM CHECK')
    print('=' * 60)
    print(f'Check time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Check system state file
    print('\n1. SYSTEM STATE VERIFICATION')
    print('-' * 30)
    
    try:
        with open('system_state.json', 'r') as f:
            state = json.load(f)
        
        print(f'[OK] System state file found')
        print(f'[INFO] Previous reboot: {state.get("reboot_time", "Unknown")}')
        print(f'[INFO] V2 Merged integration: {state.get("v2_merged_integration", "Unknown")}')
        print(f'[INFO] Core modules status: {state.get("core_modules", "Unknown")}')
        print(f'[INFO] Binance testnet: {state.get("binance_testnet", "Unknown")}')
        print(f'[INFO] Error status: {state.get("error_status", "Unknown")}')
        
    except FileNotFoundError:
        print('[WARN] System state file not found (fresh start)')
    except Exception as e:
        print(f'[ERROR] System state check failed: {e}')
    
    # 2. Check core modules
    print('\n2. CORE MODULES VERIFICATION')
    print('-' * 30)
    
    modules_to_check = [
        'core.market_data_service',
        'core.position_manager', 
        'core.account_service',
        'core.strategy_registry',
        'core.trade_orchestrator',
        'core.signal_engine',
        'core.allocation_service',
        'core.indicator_service',
        'core.market_regime_service',
        'core.order_executor',
        'core.protective_order_manager',
        'core.pending_order_manager'
    ]
    
    modules_ok = 0
    for module in modules_to_check:
        try:
            __import__(module)
            print(f'[OK] {module}')
            modules_ok += 1
        except ImportError as e:
            print(f'[ERROR] {module}: {e}')
    
    print(f'[RESULT] {modules_ok}/{len(modules_to_check)} modules loaded')
    
    # 3. Check configuration
    print('\n3. CONFIGURATION VERIFICATION')
    print('-' * 30)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config.get('binance_testnet', {}).get('api_key', '')
        base_url = config.get('binance_testnet', {}).get('base_url', '')
        max_positions = config.get('trading_config', {}).get('max_open_positions', 1)
        
        print(f'[OK] Configuration loaded')
        print(f'[INFO] API Key: {api_key[:10]}...' if api_key else '[ERROR] No API key')
        print(f'[INFO] Base URL: {base_url}')
        print(f'[INFO] Max positions: {max_positions}')
        
    except Exception as e:
        print(f'[ERROR] Configuration check failed: {e}')
    
    # 4. Check API connectivity
    print('\n4. API CONNECTIVITY VERIFICATION')
    print('-' * 30)
    
    try:
        import requests
        response = requests.get('https://demo-fapi.binance.com/fapi/v1/time', timeout=5)
        if response.status_code == 200:
            print('[OK] Binance API reachable')
        else:
            print(f'[WARN] Binance API status: {response.status_code}')
    except Exception as e:
        print(f'[ERROR] Binance API unreachable: {e}')
    
    # 5. Check trading results
    print('\n5. TRADING STATE VERIFICATION')
    print('-' * 30)
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        active_positions = len(results.get('active_positions', {}))
        strategies = len(results.get('strategies', {}))
        last_error = results.get('last_error')
        
        print(f'[OK] Trading results loaded')
        print(f'[INFO] Active positions: {active_positions}')
        print(f'[INFO] Configured strategies: {strategies}')
        print(f'[INFO] Last error: {last_error if last_error else "None"}')
        
    except FileNotFoundError:
        print('[WARN] Trading results file not found')
    except Exception as e:
        print(f'[ERROR] Trading results check failed: {e}')
    
    # 6. Final readiness check
    print('\n6. SYSTEM READINESS')
    print('-' * 30)
    
    if modules_ok == len(modules_to_check):
        print('[READY] All core modules loaded')
    else:
        print('[NOT READY] Some modules failed to load')
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        if config.get('binance_testnet', {}).get('api_key'):
            print('[READY] API configuration available')
        else:
            print('[NOT READY] API key missing')
    except:
        print('[NOT READY] Configuration missing')
    
    print('\n' + '=' * 60)
    print('POST-REBOOT CHECK COMPLETE')
    print('=' * 60)
    print('[NEXT STEP] Run: python main_runtime.py')
    print('[NEXT STEP] Monitor with: python check_trading_status.py')
    print('=' * 60)

if __name__ == "__main__":
    post_reboot_check()
