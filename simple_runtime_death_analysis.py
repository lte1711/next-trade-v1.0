#!/usr/bin/env python3
"""
Simple Main Runtime Death Analysis - Analyze why main runtime died
"""

import json
import os
import psutil
from datetime import datetime, timedelta

def analyze_main_runtime_death():
    """Analyze why main runtime process died"""
    print('=' * 80)
    print('MAIN RUNTIME DEATH ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # 1. Check current process status
    print('\n[1] CURRENT PROCESS STATUS')
    
    try:
        python_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'create_time']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    create_time = datetime.fromtimestamp(proc.info['create_time'])
                    
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'cmdline': cmdline,
                        'create_time': create_time
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print(f'  - Total Python Processes: {len(python_processes)}')
        
        main_runtime_found = False
        for proc in python_processes:
            if 'main_runtime.py' in proc['cmdline']:
                main_runtime_found = True
                print(f'  - Main Runtime Process:')
                print(f'    PID: {proc["pid"]}')
                print(f'    Status: {proc["status"]}')
                print(f'    Started: {proc["create_time"]}')
                print(f'    Command: {proc["cmdline"][:100]}...')
                break
        
        if not main_runtime_found:
            print(f'  - Main Runtime: NOT FOUND')
            print(f'  - Possible reasons:')
            print(f'    - Process crashed')
            print(f'    - Process was killed')
            print(f'    - Process never started')
        
        print(f'\n  - All Python Processes:')
        for proc in python_processes:
            print(f'    PID {proc["pid"]}: {proc["status"]} - {proc["cmdline"][:80]}...')
    
    except Exception as e:
        print(f'  - Error checking processes: {e}')
    
    # 2. Check trading results for crash indicators
    print('\n[2] TRADING RESULTS CRASH ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        system_errors = trading_results.get('system_errors', [])
        print(f'  - System Errors: {len(system_errors)}')
        
        if system_errors:
            print(f'  - Recent System Errors:')
            for error in system_errors[-5:]:
                error_type = error.get('type', 'Unknown')
                error_message = error.get('message', 'No message')
                print(f'    - {error_type}: {error_message}')
        
        last_cycle = trading_results.get('last_cycle', {})
        if last_cycle:
            cycle_errors = last_cycle.get('errors', [])
            print(f'  - Last Cycle Errors: {len(cycle_errors)}')
            
            if cycle_errors:
                print(f'  - Last Cycle Error Details:')
                for error in cycle_errors:
                    print(f'    - {error}')
        
        cycle_count = trading_results.get('cycle_count', 0)
        last_cycle_time = trading_results.get('last_cycle_time', 0)
        
        print(f'  - Total Cycles: {cycle_count}')
        
        if last_cycle_time:
            last_cycle_datetime = datetime.fromtimestamp(last_cycle_time / 1000)
            time_since_cycle = datetime.now() - last_cycle_datetime
            print(f'  - Last Cycle: {last_cycle_datetime}')
            print(f'  - Time Since Last Cycle: {time_since_cycle}')
            
            if time_since_cycle > timedelta(hours=1):
                print(f'  - WARNING: No cycles for {time_since_cycle}')
        else:
            print(f'  - WARNING: No cycle history found')
    
    except Exception as e:
        print(f'  - Error analyzing trading results: {e}')
    
    # 3. Check system resources
    print('\n[3] SYSTEM RESOURCE ANALYSIS')
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f'  - CPU Usage: {cpu_percent:.1f}%')
        
        memory = psutil.virtual_memory()
        print(f'  - Memory Usage: {memory.percent:.1f}%')
        print(f'    - Total: {memory.total / (1024**3):.1f} GB')
        print(f'    - Available: {memory.available / (1024**3):.1f} GB')
        
        disk = psutil.disk_usage('.')
        print(f'  - Disk Usage: {disk.percent:.1f}%')
        print(f'    - Total: {disk.total / (1024**3):.1f} GB')
        print(f'    - Free: {disk.free / (1024**3):.1f} GB')
        
        if cpu_percent > 90:
            print(f'  - WARNING: High CPU usage')
        
        if memory.percent > 90:
            print(f'  - WARNING: High memory usage')
        
        if disk.percent > 90:
            print(f'  - WARNING: High disk usage')
    
    except Exception as e:
        print(f'  - Error checking system resources: {e}')
    
    # 4. Check main runtime file integrity
    print('\n[4] MAIN RUNTIME FILE INTEGRITY')
    
    try:
        main_runtime_file = 'main_runtime.py'
        
        if os.path.exists(main_runtime_file):
            file_size = os.path.getsize(main_runtime_file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(main_runtime_file))
            
            print(f'  - File Size: {file_size:,} bytes')
            print(f'  - Modified: {mod_time}')
            print(f'  - File Status: EXISTS')
        else:
            print(f'  - ERROR: main_runtime.py not found')
    
    except Exception as e:
        print(f'  - Error checking file integrity: {e}')
    
    # 5. Death cause analysis
    print('\n[5] DEATH CAUSE ANALYSIS')
    
    possible_causes = []
    
    if not main_runtime_found:
        possible_causes.append("Process crashed or terminated")
    
    if len(system_errors) > 0:
        possible_causes.append(f"System errors detected ({len(system_errors)} errors)")
    
    if cpu_percent > 90:
        possible_causes.append("High CPU usage causing crash")
    
    if memory.percent > 90:
        possible_causes.append("High memory usage causing crash")
    
    if cycle_count == 0:
        possible_causes.append("Process never started properly")
    
    if 'last_cycle_time' in locals() and last_cycle_time > 0:
        if time_since_cycle > timedelta(hours=1):
            possible_causes.append("Process stopped responding")
    
    print(f'  - Possible Death Causes:')
    for i, cause in enumerate(possible_causes, 1):
        print(f'    {i}. {cause}')
    
    if not possible_causes:
        print(f'    - No obvious death cause identified')
        print(f'    - Process may have been manually stopped')
    
    # 6. Recommendations
    print('\n[6] RECOMMENDATIONS')
    
    if possible_causes:
        print(f'  - IMMEDIATE ACTIONS:')
        print(f'    1. Restart main runtime: python main_runtime.py')
        print(f'    2. Monitor process after restart')
        
        if "System errors detected" in possible_causes:
            print(f'    3. Fix system errors before restarting')
        
        if "High CPU usage" in possible_causes:
            print(f'    4. Check for infinite loops or resource-intensive operations')
        
        if "High memory usage" in possible_causes:
            print(f'    5. Check for memory leaks in the code')
        
        if "Process never started properly" in possible_causes:
            print(f'    6. Check Python environment and dependencies')
        
        if "Process stopped responding" in possible_causes:
            print(f'    7. Check for network connectivity issues')
    else:
        print(f'  - GENERAL RECOMMENDATIONS:')
        print(f'    1. Restart main runtime: python main_runtime.py')
        print(f'    2. Monitor system resources after restart')
        print(f'    3. Check trading functionality works correctly')
    
    print(f'\n  - MONITORING AFTER RESTART:')
    print(f'    1. Use Task Manager to track process')
    print(f'    2. Check trading_results.json for cycle updates')
    print(f'    3. Monitor system resources (CPU, Memory)')
    
    print('\n' + '=' * 80)
    print('MAIN RUNTIME DEATH ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_main_runtime_death()
