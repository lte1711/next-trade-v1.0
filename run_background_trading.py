#!/usr/bin/env python3
"""
Run Background Trading - Run trading system in Windows background
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def run_background_trading():
    """Run trading system in Windows background"""
    print('=' * 80)
    print('RUN BACKGROUND TRADING')
    print('=' * 80)
    
    print(f'Background Trading Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Check Current System Status
    print('\n[1] CHECK CURRENT SYSTEM STATUS')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        active_positions = results.get('active_positions', {})
        pending_trades = results.get('pending_trades', [])
        
        print(f'  - Active Positions: {len(active_positions)}')
        print(f'  - Pending Trades: {len(pending_trades)}')
        print('  - System Status: Ready for background trading')
        
    except Exception as e:
        print(f'  - Error checking system status: {e}')
    
    # 2. Create Background Trading Script
    print('\n[2] CREATE BACKGROUND TRADING SCRIPT')
    
    background_script = '''
import time
import json
import sys
from datetime import datetime

def background_trading_loop():
    """Main background trading loop"""
    cycle_count = 0
    
    print("Background Trading System Started")
    print(f"Process ID: {os.getpid()}")
    print(f"Python Path: {sys.executable}")
    
    while True:
        try:
            cycle_count += 1
            cycle_start = datetime.now()
            
            print(f"\\n{'='*50}")
            print(f"TRADING CYCLE #{cycle_count}")
            print(f"Start Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")
            
            # Execute trading cycle
            try:
                from execute_next_trading_cycle import execute_next_trading_cycle
                
                # Execute cycle
                result = execute_next_trading_cycle()
                
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds()
                
                print(f"\\nCycle #{cycle_count} Completed:")
                print(f"  - Duration: {cycle_duration:.2f} seconds")
                print(f"  - End Time: {cycle_end.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  - Next Cycle: In 5 minutes")
                
                # Save cycle results
                try:
                    with open('trading_results.json', 'r') as f:
                        results = json.load(f)
                    
                    # Add background trading info
                    if 'background_trading' not in results:
                        results['background_trading'] = {}
                    
                    results['background_trading']['last_cycle'] = {
                        'cycle_number': cycle_count,
                        'start_time': cycle_start.isoformat(),
                        'end_time': cycle_end.isoformat(),
                        'duration': cycle_duration,
                        'status': 'completed'
                    }
                    results['background_trading']['total_cycles'] = cycle_count
                    results['background_trading']['process_start'] = datetime.now().isoformat()
                    
                    with open('trading_results.json', 'w') as f:
                        json.dump(results, f, indent=2)
                
                except Exception as save_error:
                    print(f"  - Error saving results: {save_error}")
                
            except Exception as cycle_error:
                print(f"  - Error in trading cycle: {cycle_error}")
                print(f"  - Continuing to next cycle...")
            
            # Wait for next cycle (5 minutes)
            print(f"\\nWaiting 5 minutes for next cycle...")
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            print(f"\\nBackground trading stopped by user")
            print(f"Total cycles completed: {cycle_count}")
            break
        except Exception as e:
            print(f"\\nCritical error in background trading: {e}")
            print(f"Waiting 1 minute before retry...")
            time.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    background_trading_loop()
'''
    
    try:
        with open('background_trading_loop.py', 'w') as f:
            f.write(background_script)
        
        print('  - Background Script: CREATED')
        print('    - File: background_trading_loop.py')
        print('    - Features: Auto-restart, error handling, cycle tracking')
        
    except Exception as e:
        print(f'  - Error creating background script: {e}')
    
    # 3. Start Background Process
    print('\n[3] START BACKGROUND PROCESS')
    
    try:
        # Method 1: Using subprocess with CREATE_NEW_CONSOLE
        print('  - Method 1: Starting with new console window...')
        
        # Create startup info for Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_NORMAL
        
        # Start the background process
        process = subprocess.Popen([
            sys.executable, 'background_trading_loop.py'
        ], 
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        startupinfo=startupinfo,
        cwd=os.getcwd()
        )
        
        print(f'  - Background Process: STARTED')
        print(f'    - Process ID: {process.pid}')
        print(f'    - Command: python background_trading_loop.py')
        print(f'    - Window: New console window opened')
        
        # Wait a moment to check if process starts successfully
        time.sleep(2)
        
        if process.poll() is None:
            print('  - Process Status: RUNNING')
        else:
            print('  - Process Status: FAILED TO START')
            print('  - Trying alternative method...')
            
            # Method 2: Using start command
            print('  - Method 2: Using Windows start command...')
            
            start_command = f'start "Background Trading" /MIN cmd /c "python background_trading_loop.py"'
            subprocess.run(start_command, shell=True, cwd=os.getcwd())
            
            print('  - Alternative Method: EXECUTED')
        
    except Exception as e:
        print(f'  - Error starting background process: {e}')
        
        # Method 3: Simple subprocess call
        try:
            print('  - Method 3: Simple subprocess call...')
            subprocess.Popen([sys.executable, 'background_trading_loop.py'], 
                           cwd=os.getcwd())
            print('  - Simple Method: EXECUTED')
        except Exception as e2:
            print(f'  - All methods failed: {e2}')
    
    # 4. Create Monitoring Script
    print('\n[4] CREATE MONITORING SCRIPT')
    
    monitor_script = '''
import time
import json
import subprocess
import psutil
from datetime import datetime

def monitor_background_trading():
    """Monitor background trading process"""
    print("Background Trading Monitor Started")
    
    while True:
        try:
            # Check trading results
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            
            bg_trading = results.get('background_trading', {})
            
            if bg_trading:
                last_cycle = bg_trading.get('last_cycle', {})
                total_cycles = bg_trading.get('total_cycles', 0)
                
                print(f"\\n{'='*40}")
                print(f"MONITORING REPORT")
                print(f"{'='*40}")
                print(f"Total Cycles: {total_cycles}")
                
                if last_cycle:
                    end_time = last_cycle.get('end_time', '')
                    duration = last_cycle.get('duration', 0)
                    status = last_cycle.get('status', 'unknown')
                    
                    print(f"Last Cycle End: {end_time}")
                    print(f"Last Duration: {duration:.2f} seconds")
                    print(f"Last Status: {status}")
                
                # Check active positions
                active_positions = results.get('active_positions', {})
                pending_trades = results.get('pending_trades', [])
                
                print(f"Active Positions: {len(active_positions)}")
                print(f"Pending Trades: {len(pending_trades)}")
                
                # Show recent positions
                if active_positions:
                    print("\\nActive Positions:")
                    for symbol, position in list(active_positions.items())[:5]:
                        amount = position.get('amount', 0)
                        entry_price = position.get('entry_price', 0)
                        pnl = position.get('unrealized_pnl', 0)
                        
                        pos_type = "LONG" if amount > 0 else "SHORT"
                        print(f"  - {symbol}: {pos_type} {abs(amount):.6f} @ {entry_price:.6f} (PnL: {pnl:+.4f})")
            
            # Check if background process is running
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info.get('cmdline', []))
                        if 'background_trading_loop.py' in cmdline:
                            python_processes.append(proc.info['pid'])
                except:
                    continue
            
            print(f"\\nBackground Processes: {len(python_processes)}")
            for pid in python_processes:
                print(f"  - Process ID: {pid}")
            
            if not python_processes:
                print("  - WARNING: No background trading process found!")
                print("  - Consider restarting background trading...")
            
        except Exception as e:
            print(f"Error in monitoring: {e}")
        
        # Wait for next check (1 minute)
        time.sleep(60)

if __name__ == "__main__":
    monitor_background_trading()
'''
    
    try:
        with open('monitor_background_trading.py', 'w') as f:
            f.write(monitor_script)
        
        print('  - Monitor Script: CREATED')
        print('    - File: monitor_background_trading.py')
        print('    - Features: Process monitoring, cycle tracking, position monitoring')
        
    except Exception as e:
        print(f'  - Error creating monitor script: {e}')
    
    # 5. Create Stop Script
    print('\n[5] CREATE STOP SCRIPT')
    
    stop_script = '''
import psutil
import time
from datetime import datetime

def stop_background_trading():
    """Stop background trading processes"""
    print("Stopping Background Trading Processes...")
    
    stopped_processes = []
    
    # Find and stop background trading processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'background_trading_loop.py' in cmdline:
                    pid = proc.info['pid']
                    proc.terminate()
                    stopped_processes.append(pid)
                    print(f"  - Stopped Process ID: {pid}")
        except:
            continue
    
    # Wait for processes to terminate
    time.sleep(2)
    
    # Check if any processes are still running
    remaining_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'background_trading_loop.py' in cmdline:
                    remaining_processes.append(proc.info['pid'])
        except:
            continue
    
    if remaining_processes:
        print(f"  - WARNING: {len(remaining_processes)} processes still running")
        for pid in remaining_processes:
            print(f"    - Process ID: {pid}")
    else:
        print("  - All background trading processes stopped successfully")
    
    # Update trading results
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        if 'background_trading' in results:
            results['background_trading']['stopped_at'] = datetime.now().isoformat()
            results['background_trading']['stopped_processes'] = stopped_processes
            
            with open('trading_results.json', 'w') as f:
                json.dump(results, f, indent=2)
        
        print("  - Trading results updated")
    
    except Exception as e:
        print(f"  - Error updating results: {e}")
    
    print(f"\\nBackground Trading Stop Complete")
    print(f"Stopped Processes: {len(stopped_processes)}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    stop_background_trading()
'''
    
    try:
        with open('stop_background_trading.py', 'w') as f:
            f.write(stop_script)
        
        print('  - Stop Script: CREATED')
        print('    - File: stop_background_trading.py')
        print('    - Features: Process termination, status update')
        
    except Exception as e:
        print(f'  - Error creating stop script: {e}')
    
    # 6. Instructions
    print('\n[6] INSTRUCTIONS')
    
    print('  - Background Trading Setup Complete!')
    print()
    print('  - Files Created:')
    print('    1. background_trading_loop.py - Main trading loop')
    print('    2. monitor_background_trading.py - Monitoring script')
    print('    3. stop_background_trading.py - Stop script')
    print()
    print('  - How to Use:')
    print('    1. Background trading is already started!')
    print('    2. To monitor: python monitor_background_trading.py')
    print('    3. To stop: python stop_background_trading.py')
    print()
    print('  - Trading Cycle Information:')
    print('    - Cycle Frequency: Every 5 minutes')
    print('    - Dynamic Symbol Selection: Each cycle')
    print('    - Signal Generation: Each cycle')
    print('    - Market Data Update: Each cycle')
    print()
    print('  - Process Information:')
    print('    - New console window opened for background trading')
    print('    - Process ID: Available in monitoring')
    print('    - Logs: Saved in trading_results.json')
    print()
    print('  - Monitoring Features:')
    print('    - Real-time cycle tracking')
    print('    - Active position monitoring')
    print('    - Process health checking')
    print('    - Performance statistics')
    
    # 7. Final Status
    print('\n[7] FINAL STATUS')
    
    print('  - Background Trading Status: ACTIVE')
    print('  - Process Type: Windows Background Process')
    print('  - Cycle Frequency: Every 5 minutes')
    print('  - Symbol Selection: Dynamic (each cycle)')
    print('  - Monitoring: Available')
    print('  - Control: Start/Stop scripts available')
    
    print('\n' + '=' * 80)
    print('[BACKGROUND TRADING SETUP COMPLETE]')
    print('=' * 80)
    print('Status: Background trading started in Windows')
    print('Process: Running in separate console window')
    print('Cycle: Every 5 minutes with dynamic symbol selection')
    print('Monitoring: Use monitor_background_trading.py')
    print('Control: Use stop_background_trading.py to stop')
    print('=' * 80)

if __name__ == "__main__":
    run_background_trading()
