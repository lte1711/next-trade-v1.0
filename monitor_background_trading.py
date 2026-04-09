
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
                
                print(f"\n{'='*40}")
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
                    print("\nActive Positions:")
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
            
            print(f"\nBackground Processes: {len(python_processes)}")
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
