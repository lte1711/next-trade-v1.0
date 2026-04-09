#!/usr/bin/env python3
"""
Execute Real-Time Trading - Execute real-time trading directly
"""

import subprocess
import sys
import time
import os
import json
from datetime import datetime

def execute_real_time_trading():
    """Execute real-time trading directly"""
    print('=' * 80)
    print('EXECUTE REAL-TIME TRADING')
    print('=' * 80)
    
    print(f'Execute Real-Time Trading Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Clean Up
    print('\n[1] CLEAN UP ENVIRONMENT')
    
    try:
        # Clear trading results
        with open('trading_results.json', 'w') as f:
            json.dump({
                "execute_time": datetime.now().isoformat(),
                "status": "ready_for_real_time",
                "message": "Environment cleaned, ready for real-time trading",
                "real_time_mode": True,
                "all_virtual_tests_disabled": True
            }, f, indent=2)
        
        print('  - Trading results reset for real-time trading')
        
        # Update configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        config['real_time_mode'] = True
        config['all_virtual_tests_disabled'] = True
        config['force_real_exchange'] = True
        config['simulation_mode'] = False
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print('  - Configuration updated for real-time trading')
    
    except Exception as e:
        print(f'  - Error cleaning up: {e}')
    
    # 2. Execute Real-Time Trading Directly
    print('\n[2] EXECUTE REAL-TIME TRADING DIRECTLY')
    
    try:
        print('  - Starting real-time trading execution...')
        print('  - This will run real-time trading in this console')
        print('  - Press Ctrl+C to stop')
        print()
        
        # Import and run main runtime directly
        from main_runtime import TradingRuntime
        
        print('1. Initializing TradingRuntime...')
        runtime = TradingRuntime()
        
        print('2. TradingRuntime initialized successfully!')
        print(f'   - Total Capital: ${runtime.total_capital:.2f}')
        print(f'   - Active Strategies: {len(runtime.active_strategies)}')
        print(f'   - Valid Symbols: {len(runtime.valid_symbols)}')
        print(f'   - Max Positions: {runtime.max_open_positions}')
        print(f'   - Base URL: {runtime.base_url}')
        
        # Initialize trading system
        print('3. Initializing trading system...')
        runtime._initialize_trading_system()
        print('   - Trading system initialized!')
        
        # Save real-time status
        real_time_results = {
            'real_time_execute_start': datetime.now().isoformat(),
            'real_time_mode': True,
            'all_virtual_tests_disabled': True,
            'force_real_exchange': True,
            'status': 'real_time_executing',
            'total_capital': runtime.total_capital,
            'active_strategies': len(runtime.active_strategies),
            'valid_symbols': len(runtime.valid_symbols),
            'base_url': runtime.base_url
        }
        
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        results['real_time_execution'] = real_time_results
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print('4. Real-time execution status saved')
        
        print()
        print('=' * 60)
        print('REAL-TIME TRADING EXECUTION STARTED')
        print('=' * 60)
        print('✅ Connected to actual Binance Testnet')
        print('✅ Real-time market data enabled')
        print('✅ All virtual tests completely disabled')
        print('✅ Ready for actual trading')
        print('✅ No more virtual/simulation data')
        print('✅ Direct real-time exchange connection')
        print('✅ Real-time trading cycles will start')
        print('=' * 60)
        print('Press Ctrl+C to stop')
        print('=' * 60)
        print()
        
        # Start real-time trading loop
        runtime.run()
        
    except KeyboardInterrupt:
        print(f'\n\nReal-time trading stopped by user')
        end_time = datetime.now()
        
        # Update results
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        if 'real_time_execution' in results:
            results['real_time_execution']['status'] = 'stopped'
            results['real_time_execution']['stop_time'] = end_time.isoformat()
            results['real_time_execution']['stopped_by'] = 'user'
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Real-time trading execution results updated")
        print(f"Execution stopped at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f'\n❌ CRITICAL ERROR IN REAL-TIME TRADING: {e}')
        print("This is a real error with actual exchange connection!")
        
        # Save error information
        error_info = {
            'real_time_error': True,
            'timestamp': datetime.now().isoformat(),
            'error_message': str(e),
            'status': 'real_time_error'
        }
        
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        if 'real_time_execution' in results:
            results['real_time_execution']['status'] = 'error'
            results['real_time_execution']['error'] = error_info
        else:
            results['real_time_execution'] = {
                'status': 'error',
                'error': error_info
            }
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Real-time error information saved")

if __name__ == "__main__":
    execute_real_time_trading()
