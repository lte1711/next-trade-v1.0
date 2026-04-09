import time
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
                
                print(f"\n{'='*50}")
                print(f"MAIN RUNTIME MONITORING REPORT")
                print(f"{'='*50}")
                print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Main runtime status
                if main_runtime_bg:
                    start_time = main_runtime_bg.get('start_time', '')
                    total_cycles = main_runtime_bg.get('total_cycles', 0)
                    status = main_runtime_bg.get('status', 'unknown')
                    
                    print(f"\nMain Runtime Status:")
                    print(f"  - Start Time: {start_time}")
                    print(f"  - Total Cycles: {total_cycles}")
                    print(f"  - Status: {status}")
                else:
                    print("\nMain Runtime Status: NOT STARTED")
                
                # Background trading status (if also running)
                if bg_trading:
                    last_cycle = bg_trading.get('last_cycle', {})
                    bg_total_cycles = bg_trading.get('total_cycles', 0)
                    
                    print(f"\nBackground Trading Status:")
                    print(f"  - Total Cycles: {bg_total_cycles}")
                    
                    if last_cycle:
                        end_time = last_cycle.get('end_time', '')
                        duration = last_cycle.get('duration', 0)
                        
                        print(f"  - Last Cycle End: {end_time}")
                        print(f"  - Last Duration: {duration:.2f} seconds")
                else:
                    print("\nBackground Trading Status: NOT RUNNING")
                
                # Check active positions
                active_positions = results.get('active_positions', {})
                pending_trades = results.get('pending_trades', [])
                total_trades = results.get('total_trades', 0)
                available_balance = results.get('available_balance', 0.0)
                
                print(f"\nTrading Status:")
                print(f"  - Active Positions: {len(active_positions)}")
                print(f"  - Pending Trades: {len(pending_trades)}")
                print(f"  - Total Trades: {total_trades}")
                print(f"  - Available Balance: ${available_balance:.2f}")
                
                # Show active positions
                if active_positions:
                    print("\nActive Positions:")
                    for symbol, position in list(active_positions.items())[:5]:
                        amount = position.get('amount', 0)
                        entry_price = position.get('entry_price', 0)
                        pnl = position.get('unrealized_pnl', 0)
                        
                        pos_type = "LONG" if amount > 0 else "SHORT"
                        print(f"  - {symbol}: {pos_type} {abs(amount):.6f} @ {entry_price:.6f} (PnL: {pnl:+.4f})")
                
                # Check system errors
                system_errors = results.get('system_errors', [])
                if system_errors:
                    print(f"\nSystem Errors: {len(system_errors)}")
                    for error in system_errors[-3:]:  # Show last 3 errors
                        error_time = error.get('timestamp', '')
                        error_type = error.get('error_type', '')
                        error_message = error.get('error_message', '')
                        print(f"  - {error_time}: {error_type} - {error_message}")
                else:
                    print("\nSystem Errors: None")
            
            except FileNotFoundError:
                print("\nTrading results file not found")
            except Exception as e:
                print(f"\nError reading trading results: {e}")
            
            # Check if main runtime process is running
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                      capture_output=True, text=True)
                
                if 'python.exe' in result.stdout:
                    python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
                    print(f"\nPython Processes: {len(python_lines)}")
                    
                    for line in python_lines[:3]:  # Show first 3
                        print(f"  - {line.strip()}")
                    
                    # Check for our main runtime process
                    main_runtime_found = False
                    for line in python_lines:
                        if 'main_runtime_background_loop.py' in line:
                            main_runtime_found = True
                            break
                    
                    if main_runtime_found:
                        print("\nMain Runtime Process: RUNNING")
                    else:
                        print("\nMain Runtime Process: NOT FOUND")
                else:
                    print("\nNo Python processes found")
            
            except Exception as e:
                print(f"\nError checking processes: {e}")
        
        except Exception as e:
            print(f"Error in monitoring: {e}")
        
        # Wait for next check (2 minutes)
        print("\nWaiting 2 minutes for next check...")
        time.sleep(120)  # 2 minutes

if __name__ == "__main__":
    monitor_main_runtime()
