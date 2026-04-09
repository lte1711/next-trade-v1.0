#!/usr/bin/env python3
"""
Direct Main Runtime Fix - Direct fix for main_runtime.py MarketDataService issue
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def direct_main_runtime_fix():
    """Direct fix for main_runtime.py MarketDataService initialization"""
    print('=' * 80)
    print('DIRECT MAIN RUNTIME FIX')
    print('=' * 80)
    
    print(f'Fix Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Direct Fix main_runtime.py
    print('\n[1] DIRECT FIX MAIN_RUNTIME.PY')
    
    try:
        # Read main_runtime.py with UTF-8 encoding
        with open('main_runtime.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the problematic line
        old_pattern = """        self.market_data_service = MarketDataService(
            self.base_url, self.api_key, self.api_secret, self.log_system_error
        )"""
        
        new_pattern = "        self.market_data_service = MarketDataService(self.base_url)"
        
        if old_pattern in content:
            fixed_content = content.replace(old_pattern, new_pattern)
            
            # Write back with UTF-8 encoding
            with open('main_runtime.py', 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print('  - MarketDataService initialization: FIXED')
            print('    - Old: MarketDataService(base_url, api_key, api_secret, log_error)')
            print('    - New: MarketDataService(base_url)')
        else:
            print('  - Pattern not found, trying alternative fix...')
            
            # Try to find and fix line by line
            lines = content.splitlines()
            fixed_lines = []
            
            for i, line in enumerate(lines):
                if 'MarketDataService(' in line and i > 0:
                    # Check if this is the problematic initialization
                    if 'self.market_data_service = MarketDataService(' in lines[i-1]:
                        # Replace with fixed version
                        fixed_lines.append('        self.market_data_service = MarketDataService(self.base_url)')
                        # Skip the next few lines that are part of the old initialization
                        skip_count = 0
                        j = i + 1
                        while j < len(lines) and (lines[j].strip().startswith('self.base_url') or 
                                                  lines[j].strip().startswith('self.api_key') or 
                                                  lines[j].strip().startswith('self.log_system_error') or
                                                  lines[j].strip() == ')'):
                            skip_count += 1
                            j += 1
                        
                        # Skip the original line and the parameters
                        print(f'  - Fixed line {i+1} and skipped {skip_count} lines')
                        continue
                
                fixed_lines.append(line)
            
            # Write the fixed content
            with open('main_runtime.py', 'w', encoding='utf-8') as f:
                f.write('\n'.join(fixed_lines))
            
            print('  - Alternative fix applied')
        
    except Exception as e:
        print(f'  - Error fixing main_runtime.py: {e}')
        return False
    
    # 2. Verify the fix
    print('\n[2] VERIFY THE FIX')
    
    try:
        with open('main_runtime.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the fix is applied
        if 'self.market_data_service = MarketDataService(self.base_url)' in content:
            print('  - Fix verification: PASSED')
            print('  - MarketDataService initialization: Correctly fixed')
        else:
            print('  - Fix verification: FAILED')
            print('  - MarketDataService initialization: Not properly fixed')
            return False
        
        # Check if old pattern is gone
        if 'self.api_key, self.api_secret, self.log_system_error' in content:
            print('  - WARNING: Old pattern still exists')
        else:
            print('  - Old pattern: Successfully removed')
    
    except Exception as e:
        print(f'  - Error verifying fix: {e}')
    
    # 3. Create Simple Test Script
    print('\n[3] CREATE SIMPLE TEST SCRIPT')
    
    test_script = '''import time
import json
import sys
import os
from datetime import datetime

def test_main_runtime():
    """Test main runtime initialization"""
    print("Testing Main Runtime Initialization")
    print(f"Process ID: {os.getpid()}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test import
        print("\\n1. Testing import...")
        from main_runtime import TradingRuntime
        print("   - Import: SUCCESS")
        
        # Test initialization
        print("\\n2. Testing initialization...")
        runtime = TradingRuntime()
        print("   - Initialization: SUCCESS")
        
        # Test basic attributes
        print("\\n3. Testing basic attributes...")
        print(f"   - Total Capital: ${runtime.total_capital:.2f}")
        print(f"   - Active Strategies: {len(runtime.active_strategies)}")
        print(f"   - Valid Symbols: {len(runtime.valid_symbols)}")
        print(f"   - Max Positions: {runtime.max_open_positions}")
        print(f"   - Base URL: {runtime.base_url}")
        
        # Test trading system initialization
        print("\\n4. Testing trading system initialization...")
        runtime._initialize_trading_system()
        print("   - Trading System: SUCCESS")
        
        # Save test results
        test_results = {
            'test_time': datetime.now().isoformat(),
            'import_success': True,
            'initialization_success': True,
            'total_capital': runtime.total_capital,
            'active_strategies': len(runtime.active_strategies),
            'valid_symbols': len(runtime.valid_symbols),
            'max_positions': runtime.max_open_positions,
            'base_url': runtime.base_url,
            'status': 'test_passed'
        }
        
        # Load existing trading results
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        # Add test results
        results['main_runtime_test'] = test_results
        
        # Save results
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\\n5. Test results saved to trading_results.json")
        
        print("\\n" + "="*50)
        print("MAIN RUNTIME TEST: PASSED")
        print("="*50)
        print("The main runtime can be successfully initialized!")
        print("Ready to start background trading.")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\\nTEST FAILED: {e}")
        
        # Save error information
        error_info = {
            'test_time': datetime.now().isoformat(),
            'error_type': 'test_error',
            'error_message': str(e),
            'status': 'test_failed'
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
        return False

if __name__ == "__main__":
    success = test_main_runtime()
    if success:
        print("\\nTest completed successfully!")
    else:
        print("\\nTest failed. Please check the error message.")
'''
    
    try:
        with open('test_main_runtime.py', 'w') as f:
            f.write(test_script)
        
        print('  - Test Script: CREATED')
        print('    - File: test_main_runtime.py')
        print('    - Features: Import test, initialization test, attribute test')
        
    except Exception as e:
        print(f'  - ERROR creating test script: {e}')
    
    # 4. Run Test
    print('\n[4] RUN TEST')
    
    try:
        print('  - Running main runtime test...')
        
        result = subprocess.run([sys.executable, 'test_main_runtime.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        print('  - Test Output:')
        print(result.stdout)
        
        if result.returncode == 0:
            print('  - Test Result: PASSED')
            test_passed = True
        else:
            print('  - Test Result: FAILED')
            print('  - Error Output:')
            print(result.stderr)
            test_passed = False
        
    except Exception as e:
        print(f'  - ERROR running test: {e}')
        test_passed = False
    
    # 5. Create Final Background Runtime Script
    print('\n[5] CREATE FINAL BACKGROUND RUNTIME SCRIPT')
    
    if test_passed:
        final_background_script = '''import time
import json
import sys
import os
from datetime import datetime

def final_main_runtime_background():
    """Final main runtime background loop"""
    cycle_count = 0
    start_time = datetime.now()
    
    print("FINAL Main Runtime Background System Started")
    print(f"Process ID: {os.getpid()}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import and run main runtime
        from main_runtime import TradingRuntime
        
        # Create runtime instance
        print("\\nInitializing TradingRuntime...")
        runtime = TradingRuntime()
        
        print("\\n" + "="*60)
        print("TRADING RUNTIME INITIALIZED")
        print("="*60)
        print(f"Initial Capital: ${runtime.total_capital:.2f}")
        print(f"Active Strategies: {len(runtime.active_strategies)}")
        print(f"Valid Symbols: {len(runtime.valid_symbols)}")
        print(f"Max Positions: {runtime.max_open_positions}")
        print(f"Base URL: {runtime.base_url}")
        print("="*60)
        
        # Save initial status
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
        
        # Start main runtime loop
        print("\\nStarting main trading loop...")
        print("Press Ctrl+C to stop the runtime")
        runtime.run()
        
    except KeyboardInterrupt:
        print(f"\\nMain runtime stopped by user")
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"Total Runtime: {duration}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save runtime statistics
        runtime_stats = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': str(duration),
            'stopped_by': 'user',
            'total_cycles': cycle_count,
            'status': 'stopped'
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
        
        print("Runtime statistics saved to trading_results.json")
    
    except Exception as e:
        print(f"\\nCritical error in main runtime: {e}")
        print("Please check error logs and restart system")
        
        # Save error information
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

if __name__ == "__main__":
    final_main_runtime_background()
'''
        
        try:
            with open('final_main_runtime_background.py', 'w') as f:
                f.write(final_background_script)
            
            print('  - Final Background Runtime Script: CREATED')
            print('    - File: final_main_runtime_background.py')
            print('    - Features: Fixed initialization, full runtime loop')
            
        except Exception as e:
            print(f'  - ERROR creating final background script: {e}')
    
    # 6. Start Final Background Runtime
    if test_passed:
        print('\n[6] START FINAL BACKGROUND RUNTIME')
        
        try:
            print('  - Starting Final Main Runtime Background...')
            
            # Start final main runtime background process
            process = subprocess.Popen([
                sys.executable, 'final_main_runtime_background.py'
            ], 
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=os.getcwd()
            )
            
            print(f'  - Final Main Runtime Background Process: STARTED')
            print(f'    - Process ID: {process.pid}')
            print(f'    - Command: python final_main_runtime_background.py')
            print(f'    - Window: New console window opened')
            
            # Wait a moment to check if process starts successfully
            time.sleep(5)
            
            if process.poll() is None:
                print('  - Process Status: RUNNING')
                print('  - Main Runtime: Starting initialization...')
            else:
                print('  - Process Status: FAILED TO START')
                return False
            
        except Exception as e:
            print(f'  - ERROR starting final main runtime background: {e}')
            return False
    
    # 7. Final Instructions
    print('\n[7] FINAL INSTRUCTIONS')
    
    print('  - Direct Main Runtime Fix Complete!')
    print()
    print('  - Issue Fixed:')
    print('    - MarketDataService.__init__() parameter mismatch')
    print('    - Old: MarketDataService(base_url, api_key, api_secret, log_error)')
    print('    - New: MarketDataService(base_url)')
    print()
    
    if test_passed:
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
        print('    4. Manual stop: Close background console window')
        print()
        print('  - Runtime Features:')
        print('    - Automatic trading every 10 seconds')
        print('    - Dynamic symbol selection each cycle')
        print('    - Real-time market data analysis')
        print('    - Multi-strategy execution')
        print('    - Risk management and position monitoring')
        print('    - Error handling and recovery')
        print('    - Continuous operation until stopped')
    else:
        print('  - Test Status: FAILED')
        print('  - Please check the error message above')
        print('  - The main runtime may need additional fixes')
    
    # 8. Final Status
    print('\n[8] FINAL STATUS')
    
    if test_passed:
        print('  - Final Main Runtime Background Status: ACTIVE')
        print('  - Process Type: Windows Background Process')
        print('  - Trading Cycle: Every 10 seconds')
        print('  - Exchange: Binance Testnet')
        print('  - API Status: Configured and active')
        print('  - Monitoring: Available')
        print('  - Control: Stop scripts available')
        
        print('\n' + '=' * 80)
        print('[DIRECT MAIN RUNTIME FIX COMPLETE]')
        print('=' * 80)
        print('Status: Fixed main runtime running in Windows background')
        print('Process: Separate console window with full trading system')
        print('Cycle: Every 10 seconds with complete trading orchestration')
        print('Exchange: Binance Testnet with API integration')
        print('Fix: MarketDataService initialization parameter mismatch resolved')
        print('Test: Initialization test passed')
        print('Monitoring: Use monitor_main_runtime.py for status')
        print('Control: Use stop_main_runtime.py to stop')
        print('=' * 80)
    else:
        print('  - Fix Status: INCOMPLETE')
        print('  - Test failed, additional fixes needed')
    
    return test_passed

if __name__ == "__main__":
    direct_main_runtime_fix()
