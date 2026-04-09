import time
import json
import sys
import os
from datetime import datetime

def main_runtime_background_loop():
    """Fixed main runtime background loop"""
    cycle_count = 0
    start_time = datetime.now()
    
    print("Fixed Main Runtime Background System Started")
    print(f"Process ID: {os.getpid()}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import and run main runtime
        from main_runtime import TradingRuntime
        
        # Create runtime instance
        print("\nInitializing TradingRuntime...")
        runtime = TradingRuntime()
        
        print("\n" + "="*60)
        print("TRADING RUNTIME INITIALIZED")
        print("="*60)
        print(f"Initial Capital: ${runtime.total_capital:.2f}")
        print(f"Active Strategies: {len(runtime.active_strategies)}")
        print(f"Valid Symbols: {len(runtime.valid_symbols)}")
        print(f"Max Positions: {runtime.max_open_positions}")
        print(f"Base URL: {runtime.base_url}")
        print("="*60)
        
        # Save initial status
        try:
            runtime_stats = {
                'start_time': start_time.isoformat(),
                'initial_capital': runtime.total_capital,
                'active_strategies': len(runtime.active_strategies),
                'valid_symbols': len(runtime.valid_symbols),
                'max_positions': runtime.max_open_positions,
                'base_url': runtime.base_url,
                'status': 'initialized',
                'total_cycles': cycle_count
            }
            
            # Load existing trading results
            try:
                with open('trading_results.json', 'r') as f:
                    results = json.load(f)
            except:
                results = {}
            
            # Add runtime statistics
            results['main_runtime_background'] = runtime_stats
            
            # Save results
            with open('trading_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            print("Initial status saved to trading_results.json")
            
        except Exception as save_error:
            print(f"Error saving initial status: {save_error}")
        
        # Start main runtime loop
        print("\nStarting main trading loop...")
        runtime.run()
        
    except KeyboardInterrupt:
        print(f"\nMain runtime stopped by user")
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
        print(f"\nCritical error in main runtime: {e}")
        print("Please check error logs and restart system")
        
        # Save error information
        try:
            error_info = {
                'timestamp': datetime.now().isoformat(),
                'error_type': 'runtime_critical_error',
                'error_message': str(e),
                'status': 'error'
            }
            
            # Load existing trading results
            try:
                with open('trading_results.json', 'r') as f:
                    results = json.load(f)
            except:
                results = {}
            
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
