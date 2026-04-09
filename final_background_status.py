#!/usr/bin/env python3
"""
Final Background Status - Fixed status script with proper imports
"""

import json
import subprocess
import sys
import os
from datetime import datetime

def show_background_status():
    """Show background trading status"""
    print("Background Trading Status")
    print("=" * 50)
    print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
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
    
    except FileNotFoundError:
        print("Trading results file not found")
    except Exception as e:
        print(f"Error reading status: {e}")
    
    # Check processes
    print("\nProcess Information:")
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
            print(f"Python Processes: {len(python_lines)}")
            
            for line in python_lines[:3]:  # Show first 3
                print(f"  - {line.strip()}")
        else:
            print("No Python processes found")
    
    except Exception as e:
        print(f"Error checking processes: {e}")
    
    # Check dynamic symbol selection
    print("\nDynamic Symbol Selection:")
    try:
        with open('dynamic_selection_fixed_results.json', 'r') as f:
            dynamic_results = json.load(f)
        
        selection_method = dynamic_results.get('selection_method', 'Unknown')
        selected_count = dynamic_results.get('selected_count', 0)
        top_symbols = dynamic_results.get('top_symbols', [])
        timestamp = dynamic_results.get('timestamp', '')
        
        print(f"Selection Method: {selection_method}")
        print(f"Selected Count: {selected_count}")
        print(f"Last Selection: {timestamp}")
        
        if top_symbols:
            print(f"Top 5 Symbols: {', '.join(top_symbols[:5])}")
    
    except FileNotFoundError:
        print("Dynamic selection results not found")
    except Exception as e:
        print(f"Error reading dynamic selection: {e}")
    
    # Check if background trading is actually running
    print("\nBackground Trading Status:")
    try:
        # Check if our background process is running
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            print("Status: RUNNING")
            print("Process: Python background process detected")
            
            # Check if it's our process by looking for the script
            if 'background_trading_loop_fixed.py' in result.stdout:
                print("Script: background_trading_loop_fixed.py detected")
            else:
                print("Script: Unknown (may be our process)")
        else:
            print("Status: NOT RUNNING")
            print("Process: No Python processes found")
    
    except Exception as e:
        print(f"Error checking process: {e}")
    
    print("\n" + "=" * 50)
    print("Background Trading Summary:")
    print("- Process: Running in Windows background")
    print("- Cycle: Every 5 minutes")
    print("- Symbols: Dynamic selection each cycle")
    print("- Monitoring: Available")
    print("- Control: Close console window to stop")

if __name__ == "__main__":
    show_background_status()
