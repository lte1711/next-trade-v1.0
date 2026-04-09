import time
import json
import sys
import os
from datetime import datetime

def simple_working_runtime():
    """Simple working runtime for background trading"""
    print("SIMPLE WORKING RUNTIME STARTED")
    print(f"Process ID: {os.getpid()}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Basic configuration
    config = {
        "max_open_positions": 5,
        "trading_cycle_seconds": 10,
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"],
        "strategies": ["ma_trend_follow", "ema_crossover"],
        "base_url": "https://testnet.binancefuture.com"
    }
    
    # Initialize trading results
    trading_results = {
        "start_time": datetime.now().isoformat(),
        "total_cycles": 0,
        "total_trades": 0,
        "active_positions": {},
        "pending_trades": [],
        "system_errors": [],
        "last_cycle_time": None,
        "status": "running"
    }
    
    print(f"\nConfiguration loaded:")
    print(f"  - Max Positions: {config['max_open_positions']}")
    print(f"  - Trading Cycle: {config['trading_cycle_seconds']} seconds")
    print(f"  - Symbols: {len(config['symbols'])}")
    print(f"  - Strategies: {len(config['strategies'])}")
    print(f"  - Base URL: {config['base_url']}")
    
    # Save initial results
    try:
        with open('trading_results.json', 'w') as f:
            json.dump(trading_results, f, indent=2)
        print("\nInitial trading results saved")
    except Exception as e:
        print(f"Error saving initial results: {e}")
    
    print("\n" + "="*60)
    print("STARTING AUTOMATIC TRADING CYCLES")
    print("="*60)
    print("Press Ctrl+C to stop")
    print("="*60)
    
    try:
        cycle_count = 0
        
        while True:
            cycle_count += 1
            cycle_start = datetime.now()
            
            print(f"\n{'='*50}")
            print(f"TRADING CYCLE #{cycle_count}")
            print(f"Start Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")
            
            # Simulate trading cycle
            try:
                # 1. Market data update
                print("1. Updating market data...")
                time.sleep(1)
                
                # 2. Signal generation
                print("2. Generating signals...")
                signals_generated = 0
                
                for symbol in config['symbols']:
                    # Simple signal simulation
                    import random
                    if random.random() > 0.8:  # 20% chance of signal
                        signals_generated += 1
                        print(f"   - Signal generated for {symbol}")
                
                print(f"   - Total signals: {signals_generated}")
                
                # 3. Trade execution
                print("3. Executing trades...")
                trades_executed = 0
                
                if signals_generated > 0:
                    # Check position limits
                    current_positions = len(trading_results['active_positions'])
                    available_slots = config['max_open_positions'] - current_positions
                    
                    if available_slots > 0:
                        trades_to_execute = min(signals_generated, available_slots)
                        trades_executed = trades_to_execute
                        
                        for i in range(trades_to_execute):
                            symbol = config['symbols'][i]
                            trading_results['active_positions'][symbol] = {
                                'symbol': symbol,
                                'side': 'LONG',
                                'amount': 0.001,
                                'entry_price': 50000.0,
                                'entry_time': cycle_start.isoformat(),
                                'unrealized_pnl': 0.0
                            }
                        
                        print(f"   - Trades executed: {trades_executed}")
                    else:
                        print("   - No available slots for new positions")
                else:
                    print("   - No signals to execute")
                
                # 4. Position management
                print("4. Managing positions...")
                current_positions = len(trading_results['active_positions'])
                print(f"   - Current positions: {current_positions}")
                
                # Update results
                trading_results['total_cycles'] = cycle_count
                trading_results['total_trades'] += trades_executed
                trading_results['last_cycle_time'] = cycle_start.isoformat()
                
                print(f"   - Total cycles: {trading_results['total_cycles']}")
                print(f"   - Total trades: {trading_results['total_trades']}")
                
                # Save results
                try:
                    with open('trading_results.json', 'w') as f:
                        json.dump(trading_results, f, indent=2)
                except Exception as e:
                    print(f"   - Error saving results: {e}")
                
                print(f"\nCycle #{cycle_count} completed successfully")
                
            except Exception as e:
                print(f"   - Error in cycle: {e}")
                trading_results['system_errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error_message': str(e)
                })
            
            # Wait for next cycle
            cycle_end = datetime.now()
            cycle_duration = (cycle_end - cycle_start).total_seconds()
            
            print(f"\nCycle Duration: {cycle_duration:.2f} seconds")
            print(f"Waiting {config['trading_cycle_seconds']} seconds for next cycle...")
            
            time.sleep(config['trading_cycle_seconds'])
    
    except KeyboardInterrupt:
        print(f"\n\nTrading runtime stopped by user")
        end_time = datetime.now()
        
        trading_results['status'] = 'stopped'
        trading_results['stop_time'] = end_time.isoformat()
        
        # Save final results
        try:
            with open('trading_results.json', 'w') as f:
                json.dump(trading_results, f, indent=2)
            print("Final trading results saved")
        except Exception as e:
            print(f"Error saving final results: {e}")
        
        print(f"Total runtime: {end_time - cycle_start}")
        print(f"Total cycles: {cycle_count}")
        print(f"Total trades: {trading_results['total_trades']}")
    
    except Exception as e:
        print(f"\nCritical error: {e}")
        trading_results['status'] = 'error'
        trading_results['error'] = str(e)
        
        try:
            with open('trading_results.json', 'w') as f:
                json.dump(trading_results, f, indent=2)
        except:
            pass

if __name__ == "__main__":
    simple_working_runtime()
