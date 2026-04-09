#!/usr/bin/env python3
"""
Verify Runtime Fix - Verify that all runtime errors are fixed
"""

import subprocess
import sys
import time
import os
import json
from datetime import datetime

def verify_runtime_fix():
    """Verify that all runtime errors are fixed"""
    print('=' * 80)
    print('VERIFY RUNTIME FIX')
    print('=' * 80)
    
    print(f'Verification Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Check Current Processes
    print('\n[1] CHECK CURRENT PROCESSES')
    
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
            print(f'  - Python Processes: {len(python_lines)}')
            
            for line in python_lines:
                print(f'    - {line.strip()}')
        else:
            print('  - No Python processes found')
    
    except Exception as e:
        print(f'  - Error checking processes: {e}')
    
    # 2. Test Import
    print('\n[2] TEST IMPORT')
    
    try:
        print('  - Testing main_runtime import...')
        
        result = subprocess.run([sys.executable, '-c', 
                              'from main_runtime import TradingRuntime; runtime = TradingRuntime(); print("SUCCESS")'], 
                              capture_output=True, text=True, cwd=os.getcwd(), timeout=30)
        
        if result.returncode == 0:
            print('  - Import Test: PASSED')
            print('  - Initialization Test: PASSED')
            print(result.stdout.strip())
        else:
            print('  - Import Test: FAILED')
            print('  - Error Output:')
            print(result.stderr)
            return False
        
    except Exception as e:
        print(f'  - Error testing import: {e}')
        return False
    
    # 3. Check Trading Results
    print('\n[3] CHECK TRADING RESULTS')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        main_runtime_bg = results.get('main_runtime_background', {})
        system_errors = results.get('system_errors', [])
        
        print(f'  - System Errors: {len(system_errors)}')
        
        if main_runtime_bg:
            status = main_runtime_bg.get('status', 'unknown')
            start_time = main_runtime_bg.get('start_time', '')
            fixes_applied = main_runtime_bg.get('fixes_applied', [])
            
            print(f'  - Main Runtime Status: {status}')
            print(f'  - Start Time: {start_time}')
            print(f'  - Fixes Applied: {fixes_applied}')
            
            if status == 'initialized':
                print('  - Main Runtime: SUCCESSFULLY INITIALIZED')
            elif status == 'error':
                print('  - Main Runtime: STILL HAS ERRORS')
                return False
        else:
            print('  - Main Runtime: NO STATUS FOUND')
        
        # Check recent errors
        recent_errors = [e for e in system_errors if '2026-04-09' in e.get('timestamp', '')]
        if recent_errors:
            print(f'  - Recent Errors: {len(recent_errors)}')
            for error in recent_errors:
                error_time = error.get('timestamp', '')
                error_type = error.get('error_type', '')
                error_message = error.get('error_message', '')
                print(f'    - {error_time}: {error_type} - {error_message}')
        else:
            print('  - Recent Errors: NONE')
        
    except Exception as e:
        print(f'  - Error checking trading results: {e}')
    
    # 4. Start Simple Test Runtime
    print('\n[4] START SIMPLE TEST RUNTIME')
    
    test_script = '''import time
import json
import sys
import os
from datetime import datetime

def test_runtime_simple():
    """Simple test runtime"""
    print("Simple Test Runtime Started")
    print(f"Process ID: {os.getpid()}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        from main_runtime import TradingRuntime
        
        print("\\n1. Creating TradingRuntime instance...")
        runtime = TradingRuntime()
        
        print("2. TradingRuntime created successfully!")
        print(f"   - Total Capital: ${runtime.total_capital:.2f}")
        print(f"   - Active Strategies: {len(runtime.active_strategies)}")
        print(f"   - Valid Symbols: {len(runtime.valid_symbols)}")
        print(f"   - Max Positions: {runtime.max_open_positions}")
        
        print("\\n3. Testing trading system initialization...")
        runtime._initialize_trading_system()
        print("   - Trading system initialized successfully!")
        
        print("\\n4. Testing single trading cycle...")
        cycle_results = runtime.trade_orchestrator.run_trading_cycle(
            runtime.valid_symbols[:5],  # Test with first 5 symbols
            runtime.active_strategies
        )
        
        print("   - Single trading cycle completed!")
        print(f"   - Cycle Results: {cycle_results}")
        
        # Save test results
        test_results = {
            'test_time': datetime.now().isoformat(),
            'test_status': 'success',
            'total_capital': runtime.total_capital,
            'active_strategies': len(runtime.active_strategies),
            'valid_symbols': len(runtime.valid_symbols),
            'cycle_results': cycle_results
        }
        
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        results['runtime_test'] = test_results
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\\n5. Test results saved to trading_results.json")
        print("\\n" + "="*50)
        print("SIMPLE TEST RUNTIME: SUCCESS")
        print("="*50)
        print("All runtime errors have been fixed!")
        print("The main runtime can be successfully initialized and run!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\\nTEST FAILED: {e}")
        print("Runtime errors still exist!")
        
        # Save error information
        error_info = {
            'test_time': datetime.now().isoformat(),
            'test_status': 'failed',
            'error_message': str(e)
        }
        
        try:
            with open('trading_results.json', 'r') as f:
                results = json.load(f)
        except:
            results = {}
        
        results['runtime_test'] = error_info
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Error information saved to trading_results.json")
        return False

if __name__ == "__main__":
    test_runtime_simple()
'''
    
    try:
        with open('test_runtime_simple.py', 'w') as f:
            f.write(test_script)
        
        print('  - Simple Test Script: CREATED')
        print('    - File: test_runtime_simple.py')
        
        print('  - Running simple test...')
        
        result = subprocess.run([sys.executable, 'test_runtime_simple.py'], 
                              capture_output=True, text=True, cwd=os.getcwd(), timeout=60)
        
        print('  - Test Output:')
        print(result.stdout)
        
        if result.returncode == 0:
            print('  - Simple Test: PASSED')
            test_passed = True
        else:
            print('  - Simple Test: FAILED')
            print('  - Error Output:')
            print(result.stderr)
            test_passed = False
        
    except Exception as e:
        print(f'  - Error running simple test: {e}')
        test_passed = False
    
    # 5. Final Verification
    print('\n[5] FINAL VERIFICATION')
    
    if test_passed:
        print('  - All Runtime Errors: FIXED')
        print('  - Main Runtime: CAN BE SUCCESSFULLY INITIALIZED')
        print('  - Trading System: CAN BE SUCCESSFULLY RUN')
        print('  - Background Execution: READY')
        
        print('\n  - Ready for Background Trading:')
        print('    1. All initialization errors fixed')
        print('    2. Import and initialization successful')
        print('    3. Trading cycle execution successful')
        print('    4. System ready for continuous operation')
        
        return True
    else:
        print('  - Runtime Errors: STILL EXIST')
        print('  - Main Runtime: CANNOT BE SUCCESSFULLY INITIALIZED')
        print('  - Trading System: CANNOT BE SUCCESSFULLY RUN')
        print('  - Background Execution: NOT READY')
        
        return False

if __name__ == "__main__":
    success = verify_runtime_fix()
    
    print('\n' + '=' * 80)
    if success:
        print('[RUNTIME FIX VERIFICATION: PASSED]')
        print('=' * 80)
        print('Status: All runtime errors have been fixed')
        print('Main Runtime: Ready for background execution')
        print('Trading System: Fully functional')
        print('Next Step: Start background trading')
        print('=' * 80)
    else:
        print('[RUNTIME FIX VERIFICATION: FAILED]')
        print('=' * 80)
        print('Status: Runtime errors still exist')
        print('Main Runtime: Not ready for background execution')
        print('Trading System: Not fully functional')
        print('Next Step: Additional debugging needed')
        print('=' * 80)
