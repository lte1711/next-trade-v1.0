import subprocess
import sys
import os
from datetime import datetime

def show_background_status():
    """Show background trading status"""
    print("Background Trading Status")
    print("=" * 50)
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        bg_trading = results.get('background_trading', {})
        
        if bg_trading:
            last_cycle = bg_trading.get('last_cycle', {})
            total_cycles = bg_trading.get('total_cycles', 0)
            process_start = bg_trading.get('process_start', '')
            
            print(f"Total Cycles: {total_cycles}")
            print(f"Process Start: {process_start}")
            
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
            
            print(f"\nActive Positions: {len(active_positions)}")
            print(f"Pending Trades: {len(pending_trades)}")
            
            if active_positions:
                print("\nActive Positions:")
                for symbol, position in list(active_positions.items())[:3]:
                    amount = position.get('amount', 0)
                    entry_price = position.get('entry_price', 0)
                    pnl = position.get('unrealized_pnl', 0)
                    
                    pos_type = "LONG" if amount > 0 else "SHORT"
                    print(f"  - {symbol}: {pos_type} {abs(amount):.6f} @ {entry_price:.6f} (PnL: {pnl:+.4f})")
        else:
            print("No background trading data found")
    
    except Exception as e:
        print(f"Error reading status: {e}")
    
    # Check processes
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
            print(f"\nPython Processes: {len(python_lines)}")
            
            for line in python_lines[:3]:  # Show first 3
                print(f"  - {line.strip()}")
    
    except Exception as e:
        print(f"Error checking processes: {e}")

if __name__ == "__main__":
    show_background_status()
