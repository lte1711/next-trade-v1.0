import time
import json
import subprocess
import os
from datetime import datetime

def monitor_working_runtime():
    """Monitor working runtime"""
    print("Working Runtime Monitor Started")
    print(f"Monitor Process ID: {os.getpid()}")
    
    while True:
        try:
            # Check trading results
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
            
            status = results.get('status', 'unknown')
            start_time = results.get('start_time', '')
            total_cycles = results.get('total_cycles', 0)
            total_trades = results.get('total_trades', 0)
            last_cycle_time = results.get('last_cycle_time', '')
            active_positions = results.get('active_positions', {})
            system_errors = results.get('system_errors', [])
            
            print(f"\n{'='*50}")
            print(f"WORKING RUNTIME MONITORING REPORT")
            print(f"{'='*50}")
            print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Status: {status}")
            print(f"Start Time: {start_time}")
            print(f"Total Cycles: {total_cycles}")
            print(f"Total Trades: {total_trades}")
            print(f"Last Cycle: {last_cycle_time}")
            print(f"Active Positions: {len(active_positions)}")
            print(f"System Errors: {len(system_errors)}")
            
            if active_positions:
                print("\nActive Positions:")
                for symbol, position in active_positions.items():
                    side = position.get('side', 'UNKNOWN')
                    amount = position.get('amount', 0)
                    entry_price = position.get('entry_price', 0)
                    pnl = position.get('unrealized_pnl', 0)
                    print(f"  - {symbol}: {side} {amount} @ {entry_price} (PnL: {pnl:+.4f})")
            
            if system_errors:
                print("\nSystem Errors:")
                for error in system_errors[-3:]:  # Show last 3 errors
                    error_time = error.get('timestamp', '')
                    error_message = error.get('error_message', '')
                    print(f"  - {error_time}: {error_message}")
            
            # Check if process is running
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                      capture_output=True, text=True)
                
                if 'simple_working_runtime.py' in result.stdout:
                    print("\nWorking Runtime Process: RUNNING")
                else:
                    print("\nWorking Runtime Process: NOT FOUND")
            
            except Exception as e:
                print(f"\nError checking process: {e}")
        
        except Exception as e:
            print(f"Error in monitoring: {e}")
        
        # Wait for next check
        print("\nWaiting 30 seconds for next check...")
        time.sleep(30)

if __name__ == "__main__":
    monitor_working_runtime()
