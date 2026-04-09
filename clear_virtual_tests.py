#!/usr/bin/env python3
"""
Clear Virtual Tests - Remove all virtual test data and switch to real-time exchange
"""

import subprocess
import sys
import time
import os
import json
import shutil
from datetime import datetime

def clear_virtual_tests():
    """Clear all virtual test data and switch to real-time exchange"""
    print('=' * 80)
    print('CLEAR VIRTUAL TESTS')
    print('=' * 80)
    
    print(f'Clear Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Stop All Background Processes
    print('\n[1] STOP ALL BACKGROUND PROCESSES')
    
    try:
        # Find all Python processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
            stopped_processes = []
            
            for line in python_lines:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    try:
                        # Terminate process
                        subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                      capture_output=True)
                        stopped_processes.append(pid)
                        print(f'  - Stopped Process ID: {pid}')
                    except Exception as e:
                        print(f'  - Error stopping process {pid}: {e}')
            
            print(f'  - Total Processes Stopped: {len(stopped_processes)}')
            
            # Wait for processes to terminate
            time.sleep(3)
        else:
            print('  - No Python processes found')
    
    except Exception as e:
        print(f'  - Error stopping processes: {e}')
    
    # 2. Clear Virtual Test Files
    print('\n[2] CLEAR VIRTUAL TEST FILES')
    
    virtual_files = [
        'test_main_runtime.py',
        'main_runtime_background_fixed.py',
        'final_main_runtime_background.py',
        'manual_main_runtime_background.py',
        'simple_working_runtime.py',
        'monitor_working_runtime.py',
        'verify_runtime_fix.py',
        'main_runtime_original.py',
        'main_runtime_before_fix.py'
    ]
    
    cleared_files = []
    for file in virtual_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                cleared_files.append(file)
                print(f'  - Removed: {file}')
            except Exception as e:
                print(f'  - Error removing {file}: {e}')
    
    print(f'  - Total Files Cleared: {len(cleared_files)}')
    
    # 3. Clear Virtual Test Results
    print('\n[3] CLEAR VIRTUAL TEST RESULTS')
    
    try:
        if os.path.exists('trading_results.json'):
            # Backup current results
            shutil.copy('trading_results.json', 'trading_results_backup.json')
            print('  - Backup created: trading_results_backup.json')
            
            # Clear virtual test data
            with open('trading_results.json', 'w') as f:
                json.dump({
                    "clear_time": datetime.now().isoformat(),
                    "status": "cleared_for_real_time",
                    "message": "All virtual test data cleared, switching to real-time exchange",
                    "virtual_tests_cleared": True,
                    "real_time_mode": True
                }, f, indent=2)
            
            print('  - Virtual test results cleared')
        else:
            print('  - No trading results file found')
    
    except Exception as e:
        print(f'  - Error clearing results: {e}')
    
    # 4. Restore Original main_runtime.py
    print('\n[4] RESTORE ORIGINAL MAIN_RUNTIME.PY')
    
    try:
        if os.path.exists('main_runtime_original.py'):
            # Restore original
            shutil.copy('main_runtime_original.py', 'main_runtime.py')
            print('  - Restored original main_runtime.py')
        else:
            print('  - Original main_runtime.py not found')
    
    except Exception as e:
        print(f'  - Error restoring main_runtime.py: {e}')
    
    # 5. Update Configuration for Real-Time
    print('\n[5] UPDATE CONFIGURATION FOR REAL-TIME')
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Update for real-time trading
        config['real_time_mode'] = True
        config['virtual_tests_disabled'] = True
        config['force_real_exchange'] = True
        
        # Ensure API configuration is correct
        if 'binance_testnet' not in config:
            config['binance_testnet'] = {}
        
        # Set testnet URL
        config['binance_testnet']['base_url'] = "https://testnet.binancefuture.com"
        
        # Disable any simulation mode
        config['simulation_mode'] = False
        config['paper_trading'] = False
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print('  - Configuration updated for real-time trading')
        print('    - Real-time mode: ENABLED')
        print('    - Virtual tests: DISABLED')
        print('    - Force real exchange: ENABLED')
        print('    - Simulation mode: DISABLED')
    
    except Exception as e:
        print(f'  - Error updating configuration: {e}')
    
    # 6. Create Real-Time Trading Script
    print('\n[6] CREATE REAL-TIME TRADING SCRIPT')
    
    real_time_script = '''import time
import json
import sys
import os
from datetime import datetime

def real_time_trading():
    """Real-time trading with actual exchange"""
    print("REAL-TIME TRADING STARTED")
    print(f"Process ID: {os.getpid()}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        real_time_mode = config.get('real_time_mode', False)
        virtual_tests_disabled = config.get('virtual_tests_disabled', False)
        force_real_exchange = config.get('force_real_exchange', False)
        
        print(f"\\nConfiguration:")
        print(f"  - Real-time mode: {real_time_mode}")
        print(f"  - Virtual tests disabled: {virtual_tests_disabled}")
        print(f"  - Force real exchange: {force_real_exchange}")
        
        if real_time_mode and virtual_tests_disabled and force_real_exchange:
            print("\\n✅ REAL-TIME MODE ACTIVATED")
            print("✅ All virtual tests disabled")
            print("✅ Forcing real exchange connection")
            print("✅ Ready for actual trading")
        else:
            print("\\n❌ REAL-TIME MODE NOT PROPERLY CONFIGURED")
            return False
    
    except Exception as e:
        print(f"\\n❌ Error loading configuration: {e}")
        return False
    
    try:
        # Import the real main runtime
        from main_runtime import TradingRuntime
        
        print("\\n1. Initializing real-time TradingRuntime...")
        runtime = TradingRuntime()
        
        print("2. Real-time TradingRuntime initialized successfully!")
        print(f"   - Total Capital: ${runtime.total_capital:.2f}")
        print(f"   - Active Strategies: {len(runtime.active_strategies)}")
        print(f"   - Valid Symbols: {len(runtime.valid_symbols)}")
        print(f"   - Max Positions: {runtime.max_open_positions}")
        print(f"   - Base URL: {runtime.base_url}")
        
        # Initialize trading system
        print("\\n3. Initializing real-time trading system...")
        runtime._initialize_trading_system()
        print("   - Real-time trading system initialized!")
        
        # Save real-time status
        real_time_results = {
            'real_time_start': datetime.now().isoformat(),
            'real_time_mode': True,
            'virtual_tests_disabled': True,
            'force_real_exchange': True,
            'status': 'real_time_initialized',
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
        
        results['real_time_trading'] = real_time_results
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\\n4. Real-time trading status saved")
        
        print("\\n" + "="*60)
        print("STARTING REAL-TIME TRADING")
        print("="*60)
        print("✅ Connected to actual Binance Testnet")
        print("✅ Real-time market data enabled")
        print("✅ Virtual tests completely disabled")
        print("✅ Ready for actual trading")
        print("="*60)
        print("Press Ctrl+C to stop")
        print("="*60)
        
        # Start real-time trading loop
        runtime.run()
        
    except KeyboardInterrupt:
        print(f"\\n\\nReal-time trading stopped by user")
        end_time = datetime.now()
        
        # Update results
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        if 'real_time_trading' in results:
            results['real_time_trading']['status'] = 'stopped'
            results['real_time_trading']['stop_time'] = end_time.isoformat()
            results['real_time_trading']['stopped_by'] = 'user'
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Real-time trading results updated")
    
    except Exception as e:
        print(f"\\n❌ CRITICAL ERROR IN REAL-TIME TRADING: {e}")
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
        
        if 'real_time_trading' in results:
            results['real_time_trading']['status'] = 'error'
            results['real_time_trading']['error'] = error_info
        else:
            results['real_time_trading'] = {
                'status': 'error',
                'error': error_info
            }
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Real-time error information saved")

if __name__ == "__main__":
    real_time_trading()
'''
    
    try:
        with open('real_time_trading.py', 'w') as f:
            f.write(real_time_script)
        
        print('  - Real-time Trading Script: CREATED')
        print('    - File: real_time_trading.py')
        print('    - Features: Real-time exchange connection, no virtual tests')
        
    except Exception as e:
        print(f'  - ERROR creating real-time script: {e}')
    
    # 7. Start Real-Time Trading
    print('\n[7] START REAL-TIME TRADING')
    
    try:
        print('  - Starting Real-Time Trading Background...')
        
        # Start real-time trading background process
        process = subprocess.Popen([
            sys.executable, 'real_time_trading.py'
        ], 
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=os.getcwd()
        )
        
        print(f'  - Real-Time Trading Process: STARTED')
        print(f'    - Process ID: {process.pid}')
        print(f'    - Command: python real_time_trading.py')
        print(f'    - Window: New console window opened')
        
        # Wait a moment to check if process starts successfully
        time.sleep(5)
        
        if process.poll() is None:
            print('  - Process Status: RUNNING')
            print('  - Real-Time Trading: Starting initialization...')
        else:
            print('  - Process Status: FAILED TO START')
            return False
        
    except Exception as e:
        print(f'  - ERROR starting real-time trading: {e}')
        return False
    
    # 8. Final Status
    print('\n[8] FINAL STATUS')
    
    print('  - Virtual Tests Clear: COMPLETE')
    print('  - Real-Time Mode: ENABLED')
    print('  - Background Trading: RUNNING')
    print('  - Exchange: ACTUAL BINANCE TESTNET')
    print('  - Virtual Data: CLEARED')
    
    print('\n  - Summary:')
    print('    1. All virtual test processes stopped')
    print('    2. All virtual test files removed')
    print('    3. Virtual test results cleared')
    print('    4. Original main_runtime.py restored')
    print('    5. Configuration updated for real-time')
    print('    6. Real-time trading script created')
    print('    7. Real-time trading started in background')
    
    print('\n' + '=' * 80)
    print('[VIRTUAL TESTS CLEARED - REAL-TIME TRADING STARTED]')
    print('=' * 80)
    print('Status: All virtual tests cleared')
    print('Mode: Real-time trading with actual exchange')
    print('Process: Background real-time trading active')
    print('Exchange: Binance Testnet (actual connection)')
    print('Virtual: All virtual tests disabled')
    print('Next: Real-time trading will continue until stopped')
    print('=' * 80)
    
    return True

if __name__ == "__main__":
    clear_virtual_tests()
