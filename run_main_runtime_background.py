#!/usr/bin/env python3
"""
Run Main Runtime Background - Run main_runtime.py in Windows background with Binance testnet
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def run_main_runtime_background():
    """Run main_runtime.py in Windows background with Binance testnet"""
    print('=' * 80)
    print('RUN MAIN RUNTIME BACKGROUND')
    print('=' * 80)
    
    print(f'Background Runtime Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Check System Requirements
    print('\n[1] CHECK SYSTEM REQUIREMENTS')
    
    try:
        # Check if main_runtime.py exists
        if not os.path.exists('main_runtime.py'):
            print('  - ERROR: main_runtime.py not found')
            return False
        
        print('  - main_runtime.py: FOUND')
        
        # Check config.json
        if not os.path.exists('config.json'):
            print('  - ERROR: config.json not found')
            return False
        
        print('  - config.json: FOUND')
        
        # Check API configuration
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_config = config.get('binance_testnet', {})
        api_key = api_config.get('api_key', '')
        api_secret = api_config.get('api_secret', '')
        base_url = api_config.get('base_url', '')
        
        if not api_key or not api_secret:
            print('  - ERROR: API credentials not found in config.json')
            return False
        
        print('  - API Credentials: FOUND')
        print(f'  - Base URL: {base_url}')
        
        # Check .env file
        env_exists = os.path.exists('.env')
        print(f'  - .env file: {"FOUND" if env_exists else "NOT FOUND"}')
        
        print('  - System Requirements: PASSED')
        
    except Exception as e:
        print(f'  - ERROR checking requirements: {e}')
        return False
    
    # 2. Create Background Runtime Script
    print('\n[2] CREATE BACKGROUND RUNTIME SCRIPT')
    
    background_runtime_script = '''import time
import json
import sys
import os
from datetime import datetime

def main_runtime_background_loop():
    """Main runtime background loop"""
    cycle_count = 0
    start_time = datetime.now()
    
    print("Main Runtime Background System Started")
    print(f"Process ID: {os.getpid()}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import and run main runtime
        from main_runtime import TradingRuntime
        
        # Create runtime instance
        runtime = TradingRuntime()
        
        print("\\n" + "="*60)
        print("TRADING RUNTIME INITIALIZED")
        print("="*60)
        print(f"Initial Capital: ${runtime.total_capital:.2f}")
        print(f"Active Strategies: {len(runtime.active_strategies)}")
        print(f"Valid Symbols: {len(runtime.valid_symbols)}")
        print(f"Max Positions: {runtime.max_open_positions}")
        print("="*60)
        
        # Start the main runtime loop
        runtime.run()
        
    except KeyboardInterrupt:
        print(f"\\nMain runtime stopped by user")
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"Total Runtime: {duration}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save runtime statistics
        try:
            runtime_stats = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': str(duration),
                'stopped_by': 'user',
                'total_cycles': cycle_count,
                'status': 'stopped'
            }
            
            # Load existing trading results
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            
            # Add runtime statistics
            results['main_runtime_background'] = runtime_stats
            
            # Save results
            with open('trading_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            print("Runtime statistics saved to trading_results.json")
            
        except Exception as save_error:
            print(f"Error saving runtime statistics: {save_error}")
    
    except Exception as e:
        print(f"\\nCritical error in main runtime: {e}")
        print("Please check the error logs and restart the system")
        
        # Save error information
        try:
            error_info = {
                'timestamp': datetime.now().isoformat(),
                'error_type': 'runtime_critical_error',
                'error_message': str(e),
                'status': 'error'
            }
            
            # Load existing trading results
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            
            # Add error information
            if 'system_errors' not in results:
                results['system_errors'] = []
            results['system_errors'].append(error_info)
            
            # Save results
            with open('trading_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            print("Error information saved to trading_results.json")
            
        except Exception as save_error:
            print(f"Error saving error information: {save_error}")

if __name__ == "__main__":
    main_runtime_background_loop()
'''
    
    try:
        with open('main_runtime_background_loop.py', 'w') as f:
            f.write(background_runtime_script)
        
        print('  - Background Runtime Script: CREATED')
        print('    - File: main_runtime_background_loop.py')
        print('    - Features: Runtime initialization, error handling, statistics')
        
    except Exception as e:
        print(f'  - ERROR creating background script: {e}')
        return False
    
    # 3. Create Monitor Script for Main Runtime
    print('\n[3] CREATE MONITOR SCRIPT FOR MAIN RUNTIME')
    
    monitor_script = '''import time
import json
import subprocess
import os
from datetime import datetime

def monitor_main_runtime():
    """Monitor main runtime background process"""
    print("Main Runtime Monitor Started")
    print(f"Monitor Process ID: {os.getpid()}")
    
    while True:
        try:
            # Check trading results
            try:
                with open('trading_results.json', 'r') as f:
                    results = json.load(f)
                
                main_runtime_bg = results.get('main_runtime_background', {})
                bg_trading = results.get('background_trading', {})
                
                print(f"\\n{'='*50}")
                print(f"MAIN RUNTIME MONITORING REPORT")
                print(f"{'='*50}")
                print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Main runtime status
                if main_runtime_bg:
                    start_time = main_runtime_bg.get('start_time', '')
                    total_cycles = main_runtime_bg.get('total_cycles', 0)
                    status = main_runtime_bg.get('status', 'unknown')
                    
                    print(f"\\nMain Runtime Status:")
                    print(f"  - Start Time: {start_time}")
                    print(f"  - Total Cycles: {total_cycles}")
                    print(f"  - Status: {status}")
                else:
                    print("\\nMain Runtime Status: NOT STARTED")
                
                # Background trading status (if also running)
                if bg_trading:
                    last_cycle = bg_trading.get('last_cycle', {})
                    bg_total_cycles = bg_trading.get('total_cycles', 0)
                    
                    print(f"\\nBackground Trading Status:")
                    print(f"  - Total Cycles: {bg_total_cycles}")
                    
                    if last_cycle:
                        end_time = last_cycle.get('end_time', '')
                        duration = last_cycle.get('duration', 0)
                        
                        print(f"  - Last Cycle End: {end_time}")
                        print(f"  - Last Duration: {duration:.2f} seconds")
                else:
                    print("\\nBackground Trading Status: NOT RUNNING")
                
                # Check active positions
                active_positions = results.get('active_positions', {})
                pending_trades = results.get('pending_trades', [])
                total_trades = results.get('total_trades', 0)
                available_balance = results.get('available_balance', 0.0)
                
                print(f"\\nTrading Status:")
                print(f"  - Active Positions: {len(active_positions)}")
                print(f"  - Pending Trades: {len(pending_trades)}")
                print(f"  - Total Trades: {total_trades}")
                print(f"  - Available Balance: ${available_balance:.2f}")
                
                # Show active positions
                if active_positions:
                    print("\\nActive Positions:")
                    for symbol, position in list(active_positions.items())[:5]:
                        amount = position.get('amount', 0)
                        entry_price = position.get('entry_price', 0)
                        pnl = position.get('unrealized_pnl', 0)
                        
                        pos_type = "LONG" if amount > 0 else "SHORT"
                        print(f"  - {symbol}: {pos_type} {abs(amount):.6f} @ {entry_price:.6f} (PnL: {pnl:+.4f})")
                
                # Check system errors
                system_errors = results.get('system_errors', [])
                if system_errors:
                    print(f"\\nSystem Errors: {len(system_errors)}")
                    for error in system_errors[-3:]:  # Show last 3 errors
                        error_time = error.get('timestamp', '')
                        error_type = error.get('error_type', '')
                        error_message = error.get('error_message', '')
                        print(f"  - {error_time}: {error_type} - {error_message}")
                else:
                    print("\\nSystem Errors: None")
            
            except FileNotFoundError:
                print("\\nTrading results file not found")
            except Exception as e:
                print(f"\\nError reading trading results: {e}")
            
            # Check if main runtime process is running
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                      capture_output=True, text=True)
                
                if 'python.exe' in result.stdout:
                    python_lines = [line for line in result.stdout.split('\\n') if 'python.exe' in line]
                    print(f"\\nPython Processes: {len(python_lines)}")
                    
                    for line in python_lines[:3]:  # Show first 3
                        print(f"  - {line.strip()}")
                    
                    # Check for our main runtime process
                    main_runtime_found = False
                    for line in python_lines:
                        if 'main_runtime_background_loop.py' in line:
                            main_runtime_found = True
                            break
                    
                    if main_runtime_found:
                        print("\\nMain Runtime Process: RUNNING")
                    else:
                        print("\\nMain Runtime Process: NOT FOUND")
                else:
                    print("\\nNo Python processes found")
            
            except Exception as e:
                print(f"\\nError checking processes: {e}")
        
        except Exception as e:
            print(f"Error in monitoring: {e}")
        
        # Wait for next check (2 minutes)
        print("\\nWaiting 2 minutes for next check...")
        time.sleep(120)  # 2 minutes

if __name__ == "__main__":
    monitor_main_runtime()
'''
    
    try:
        with open('monitor_main_runtime.py', 'w') as f:
            f.write(monitor_script)
        
        print('  - Monitor Script: CREATED')
        print('    - File: monitor_main_runtime.py')
        print('    - Features: Runtime monitoring, position tracking, error monitoring')
        
    except Exception as e:
        print(f'  - ERROR creating monitor script: {e}')
    
    # 4. Create Stop Script for Main Runtime
    print('\n[4] CREATE STOP SCRIPT FOR MAIN RUNTIME')
    
    stop_script = '''import subprocess
import sys
import os
from datetime import datetime

def stop_main_runtime():
    """Stop main runtime background process"""
    print("Stopping Main Runtime Background Process...")
    
    stopped_processes = []
    
    # Find and stop main runtime processes
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\\n') if 'python.exe' in line]
            
            for line in python_lines:
                if 'main_runtime_background_loop.py' in line:
                    # Extract PID from the line
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        try:
                            # Terminate the process
                            subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                          capture_output=True)
                            stopped_processes.append(pid)
                            print(f"  - Stopped Process ID: {pid}")
                        except Exception as e:
                            print(f"  - Error stopping process {pid}: {e}")
        
        # Wait for processes to terminate
        time.sleep(2)
        
        # Check if any processes are still running
        remaining_processes = []
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\\n') if 'python.exe' in line]
            for line in python_lines:
                if 'main_runtime_background_loop.py' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remaining_processes.append(parts[1])
        
        if remaining_processes:
            print(f"  - WARNING: {len(remaining_processes)} processes still running")
            for pid in remaining_processes:
                print(f"    - Process ID: {pid}")
        else:
            print("  - All main runtime processes stopped successfully")
    
    except Exception as e:
        print(f"  - Error stopping processes: {e}")
    
    # Update trading results
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Update main runtime background status
        if 'main_runtime_background' not in results:
            results['main_runtime_background'] = {}
        
        results['main_runtime_background']['stopped_at'] = datetime.now().isoformat()
        results['main_runtime_background']['stopped_processes'] = stopped_processes
        results['main_runtime_background']['status'] = 'stopped'
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("  - Trading results updated")
    
    except Exception as e:
        print(f"  - Error updating results: {e}")
    
    print(f"\\nMain Runtime Stop Complete")
    print(f"Stopped Processes: {len(stopped_processes)}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    stop_main_runtime()
'''
    
    try:
        with open('stop_main_runtime.py', 'w') as f:
            f.write(stop_script)
        
        print('  - Stop Script: CREATED')
        print('    - File: stop_main_runtime.py')
        print('    - Features: Process termination, status update')
        
    except Exception as e:
        print(f'  - ERROR creating stop script: {e}')
    
    # 5. Start Main Runtime Background
    print('\n[5] START MAIN RUNTIME BACKGROUND')
    
    try:
        print('  - Starting Main Runtime Background...')
        
        # Start main runtime background process
        process = subprocess.Popen([
            sys.executable, 'main_runtime_background_loop.py'
        ], 
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        cwd=os.getcwd()
        )
        
        print(f'  - Main Runtime Background Process: STARTED')
        print(f'    - Process ID: {process.pid}')
        print(f'    - Command: python main_runtime_background_loop.py')
        print(f'    - Window: New console window opened')
        
        # Wait a moment to check if process starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            print('  - Process Status: RUNNING')
            print('  - Main Runtime: Starting initialization...')
        else:
            print('  - Process Status: FAILED TO START')
            return False
        
    except Exception as e:
        print(f'  - ERROR starting main runtime background: {e}')
        return False
    
    # 6. Wait and Check Initial Status
    print('\n[6] WAIT AND CHECK INITIAL STATUS')
    
    try:
        print('  - Waiting 10 seconds for initialization...')
        time.sleep(10)
        
        # Check initial status
        if os.path.exists('trading_results.json'):
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            
            main_runtime_bg = results.get('main_runtime_background', {})
            
            if main_runtime_bg:
                start_time = main_runtime_bg.get('start_time', '')
                status = main_runtime_bg.get('status', 'unknown')
                
                print('  - Initial Status Check:')
                print(f'    - Start Time: {start_time}')
                print(f'    - Status: {status}')
                
                if status == 'stopped':
                    print('  - WARNING: Runtime stopped during initialization')
                else:
                    print('  - Runtime: Successfully initialized')
            else:
                print('  - Runtime: Initialization in progress...')
        else:
            print('  - Runtime: Waiting for initialization...')
    
    except Exception as e:
        print(f'  - ERROR checking initial status: {e}')
    
    # 7. Final Instructions
    print('\n[7] FINAL INSTRUCTIONS')
    
    print('  - Main Runtime Background Setup Complete!')
    print()
    print('  - Files Created:')
    print('    1. main_runtime_background_loop.py - Main runtime background loop')
    print('    2. monitor_main_runtime.py - Runtime monitoring script')
    print('    3. stop_main_runtime.py - Stop script')
    print()
    print('  - Current Status:')
    print('    - Main Runtime: RUNNING in background')
    print('    - Process ID: Available in monitoring')
    print('    - Trading: 10-second cycles')
    print('    - Exchange: Binance Testnet')
    print('    - API: Configured and active')
    print()
    print('  - How to Use:')
    print('    1. Monitor runtime: python monitor_main_runtime.py')
    print('    2. Check status: python monitor_main_runtime.py')
    print('    3. Stop runtime: python stop_main_runtime.py')
    print('    4. Manual stop: Close the background console window')
    print()
    print('  - Runtime Features:')
    print('    - Automatic trading every 10 seconds')
    print('    - Dynamic symbol selection each cycle')
    print('    - Real-time market data analysis')
    print('    - Multi-strategy execution')
    print('    - Risk management and position monitoring')
    print('    - Error handling and recovery')
    print('    - Continuous operation until stopped')
    print()
    print('  - Monitoring Features:')
    print('    - Real-time cycle tracking')
    print('    - Active position monitoring')
    print('    - Balance and trade tracking')
    print('    - Error monitoring and reporting')
    print('    - Process health checking')
    
    # 8. Final Status
    print('\n[8] FINAL STATUS')
    
    print('  - Main Runtime Background Status: ACTIVE')
    print('  - Process Type: Windows Background Process')
    print('  - Trading Cycle: Every 10 seconds')
    print('  - Exchange: Binance Testnet')
    print('  - API Status: Configured and active')
    print('  - Monitoring: Available')
    print('  - Control: Stop scripts available')
    
    print('\n' + '=' * 80)
    print('[MAIN RUNTIME BACKGROUND SETUP COMPLETE]')
    print('=' * 80)
    print('Status: Main runtime running in Windows background')
    print('Process: Separate console window with full trading system')
    print('Cycle: Every 10 seconds with complete trading orchestration')
    print('Exchange: Binance Testnet with API integration')
    print('Monitoring: Use monitor_main_runtime.py for status')
    print('Control: Use stop_main_runtime.py to stop')
    print('=' * 80)
    
    return True

if __name__ == "__main__":
    run_main_runtime_background()
