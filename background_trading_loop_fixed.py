import time
import json
import sys
import os
from datetime import datetime

def background_trading_loop():
    """Main background trading loop"""
    cycle_count = 0
    
    print("Background Trading System Started")
    print(f"Process ID: {os.getpid()}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    
    while True:
        try:
            cycle_count += 1
            cycle_start = datetime.now()
            
            print(f"\n{'='*50}")
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
                
                print(f"\nCycle #{cycle_count} Completed:")
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
            print(f"\nWaiting 5 minutes for next cycle...")
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            print(f"\nBackground trading stopped by user")
            print(f"Total cycles completed: {cycle_count}")
            break
        except Exception as e:
            print(f"\nCritical error in background trading: {e}")
            print(f"Waiting 1 minute before retry...")
            time.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    background_trading_loop()
