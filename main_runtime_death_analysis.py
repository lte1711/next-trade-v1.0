#!/usr/bin/env python3
"""
Main Runtime Death Analysis - Analyze why main runtime died
"""

import json
import os
import psutil
import subprocess
from datetime import datetime, timedelta
import glob

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
        # Find all Python processes
        python_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'create_time', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    create_time = datetime.fromtimestamp(proc.info['create_time'])
                    
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'cmdline': cmdline,
                        'create_time': create_time,
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print(f'  - Total Python Processes: {len(python_processes)}')
        
        # Check for main runtime
        main_runtime_found = False
        for proc in python_processes:
            cmdline = proc['cmdline']
            if 'main_runtime.py' in cmdline:
                main_runtime_found = True
                print(f'  - Main Runtime Process:')
                print(f'    PID: {proc["pid"]}')
                print(f'    Status: {proc["status"]}')
                print(f'    Started: {proc["create_time"]}')
                print(f'    CPU: {proc["cpu_percent"]:.1f}%')
                print(f'    Memory: {proc["memory_percent"]:.1f}%')
                print(f'    Command: {cmdline[:100]}...')
                break
        
        if not main_runtime_found:
            print(f'  - Main Runtime: NOT FOUND')
            print(f'  - Possible reasons:')
            print(f'    - Process crashed')
            print(f'    - Process was killed')
            print(f'    - Process never started')
            print(f'    - Process running under different name')
        
        # Show all Python processes
        print(f'\n  - All Python Processes:')
        for proc in python_processes:
            print(f'    PID {proc["pid"]}: {proc["status"]} - {proc["cmdline"][:80]}...')
    
    except Exception as e:
        print(f'  - Error checking processes: {e}')
    
    # 2. Check log files for errors
    print('\n[2] LOG FILE ANALYSIS')
    
    # Look for log files
    log_patterns = [
        '*.log',
        'main_runtime*.log',
        'trading*.log',
        'error*.log',
        'debug*.log'
    ]
    
    log_files = []
    for pattern in log_patterns:
        log_files.extend(glob.glob(pattern))
    
    print(f'  - Log Files Found: {len(log_files)}')
    
    for log_file in log_files:
        try:
            file_size = os.path.getsize(log_file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            
            print(f'\n    {log_file}:')
            print(f'      Size: {file_size:,} bytes')
            print(f'      Modified: {mod_time}')
            
            # Read last few lines
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                print(f'      Total Lines: {len(lines)}')
                
                # Show last 5 lines
                if lines:
                    print(f'      Last 5 Lines:')
                    for line in lines[-5:]:
                        print(f'        {line.strip()}')
                
                # Look for error patterns
                error_lines = []
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['error', 'exception', 'crash', 'fatal', 'killed', 'terminated']):
                        error_lines.append(line)
                
                if error_lines:
                    print(f'      Error Lines Found: {len(error_lines)}')
                    for line in error_lines[-3:]:  # Show last 3 errors
                        print(f'        ERROR: {line.strip()}')
            
            except Exception as e:
                print(f'      Error reading log: {e}')
        
        except Exception as e:
            print(f'    Error analyzing {log_file}: {e}')
    
    # 3. Check trading results for crash indicators
    print('\n[3] TRADING RESULTS CRASH ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Check for system errors
        system_errors = trading_results.get('system_errors', [])
        print(f'  - System Errors: {len(system_errors)}')
        
        if system_errors:
            print(f'  - Recent System Errors:')
            for error in system_errors[-5:]:
                error_type = error.get('type', 'Unknown')
                error_message = error.get('message', 'No message')
                timestamp = error.get('timestamp', 'No timestamp')
                print(f'    - {error_type}: {error_message}')
        
        # Check last cycle
        last_cycle = trading_results.get('last_cycle', {})
        if last_cycle:
            cycle_errors = last_cycle.get('errors', [])
            print(f'  - Last Cycle Errors: {len(cycle_errors)}')
            
            if cycle_errors:
                print(f'  - Last Cycle Error Details:')
                for error in cycle_errors:
                    print(f'    - {error}')
        
        # Check for abnormal termination indicators
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
    
    # 4. Check system resources
    print('\n[4] SYSTEM RESOURCE ANALYSIS')
    
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f'  - CPU Usage: {cpu_percent:.1f}%')
        
        # Memory usage
        memory = psutil.virtual_memory()
        print(f'  - Memory Usage: {memory.percent:.1f}%')
        print(f'    - Total: {memory.total / (1024**3):.1f} GB')
        print(f'    - Available: {memory.available / (1024**3):.1f} GB')
        
        # Disk usage
        disk = psutil.disk_usage('.')
        print(f'  - Disk Usage: {disk.percent:.1f}%')
        print(f'    - Total: {disk.total / (1024**3):.1f} GB')
        print(f'    - Free: {disk.free / (1024**3):.1f} GB')
        
        # Check for resource exhaustion
        if cpu_percent > 90:
            print(f'  - WARNING: High CPU usage')
        
        if memory.percent > 90:
            print(f'  - WARNING: High memory usage')
        
        if disk.percent > 90:
            print(f'  - WARNING: High disk usage')
    
    except Exception as e:
        print(f'  - Error checking system resources: {e}')
    
    # 5. Check main runtime file integrity
    print('\n[5] MAIN RUNTIME FILE INTEGRITY')
    
    try:
        main_runtime_file = 'main_runtime.py'
        
        if os.path.exists(main_runtime_file):
            file_size = os.path.getsize(main_runtime_file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(main_runtime_file))
            
            print(f'  - File Size: {file_size:,} bytes')
            print(f'  - Modified: {mod_time}')
            
            # Check for syntax errors
            try:
                result = subprocess.run(['python', '-m', 'py_compile', main_runtime_file], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f'  - Syntax Check: PASSED')
                else:
                    print(f'  - Syntax Check: FAILED')
                    print(f'    Error: {result.stderr}')
            
            except subprocess.TimeoutExpired:
                print(f'  - Syntax Check: TIMEOUT')
            except Exception as e:
                print(f'  - Syntax Check: ERROR - {e}')
            
            # Check for imports
            try:
                with open(main_runtime_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                imports = []
                for line in content.split('\n'):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        imports.append(line.strip())
                
                print(f'  - Imports Found: {len(imports)}')
                for imp in imports[:5]:  # Show first 5
                    print(f'    {imp}')
                
                if len(imports) > 5:
                    print(f'    ... and {len(imports) - 5} more')
            
            except Exception as e:
                print(f'  - Error reading imports: {e}')
        else:
            print(f'  - ERROR: main_runtime.py not found')
    
    except Exception as e:
        print(f'  - Error checking file integrity: {e}')
    
    # 6. Check for recent system events
    print('\n[6] RECENT SYSTEM EVENTS')
    
    try:
        # Check Windows Event Log (if available)
        try:
            result = subprocess.run(['wevtutil', 'qe', 'System', '/c:5', '/rd:true', '/f:text'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f'  - Recent System Events:')
                events = result.stdout.split('\n')
                for event in events[:10]:  # Show first 10
                    if event.strip():
                        print(f'    {event.strip()}')
            else:
                print(f'  - Event Log: Not accessible')
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f'  - Event Log: Not available')
        
        # Check for recent crashes in Python processes
        try:
            result = subprocess.run(['wmic', 'process', 'where', 'name="python.exe"', 'get', 'CreationDate,ProcessId,PageFileUsage'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f'  - Python Process Details:')
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        print(f'    {line.strip()}')
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f'  - Process Details: Not available')
    
    except Exception as e:
        print(f'  - Error checking system events: {e}')
    
    # 7. Check configuration for runtime issues
    print('\n[7] CONFIGURATION ANALYSIS')
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Check for problematic configurations
        trading_config = config.get('trading_config', {})
        
        print(f'  - Max Open Positions: {trading_config.get("max_open_positions", "N/A")}')
        print(f'  - Fast Entry Enabled: {trading_config.get("fast_entry_enabled", "N/A")}')
        print(f'  - Real Time Mode: {config.get("real_time_mode", "N/A")}')
        
        # Check for API configuration issues
        binance_config = config.get('binance_testnet', {})
        api_key = binance_config.get('api_key', '')
        api_secret = binance_config.get('api_secret', '')
        base_url = binance_config.get('base_url', '')
        
        print(f'  - API Key: {"SET" if api_key else "NOT SET"}')
        print(f'  - API Secret: {"SET" if api_secret else "NOT SET"}')
        print(f'  - Base URL: {base_url}')
        
        if not api_key or not api_secret:
            print(f'  - WARNING: API credentials not configured')
        
        if not base_url:
            print(f'  - WARNING: Base URL not configured')
    
    except Exception as e:
        print(f'  - Error analyzing configuration: {e}')
    
    # 8. Death cause analysis
    print('\n[8] DEATH CAUSE ANALYSIS')
    
    possible_causes = []
    
    # Analyze findings
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
    
    if time_since_cycle > timedelta(hours=1):
        possible_causes.append("Process stopped responding")
    
    print(f'  - Possible Death Causes:')
    for i, cause in enumerate(possible_causes, 1):
        print(f'    {i}. {cause}')
    
    if not possible_causes:
        print(f'    - No obvious death cause identified')
        print(f'    - Process may have been manually stopped')
    
    # 9. Recommendations
    print('\n[9] RECOMMENDATIONS')
    
    if possible_causes:
        print(f'  - IMMEDIATE ACTIONS:')
        
        if "Process crashed or terminated" in possible_causes:
            print(f'    1. Restart main runtime: python main_runtime.py')
            print(f'    2. Check for error logs in current directory')
            print(f'    3. Monitor process after restart')
        
        if "System errors detected" in possible_causes:
            print(f'    4. Fix system errors before restarting')
            print(f'    5. Check API connectivity and permissions')
        
        if "High CPU usage" in possible_causes:
            print(f'    6. Check for infinite loops or resource-intensive operations')
            print(f'    7. Optimize code for better performance')
        
        if "High memory usage" in possible_causes:
            print(f'    8. Check for memory leaks in the code")
            print(f'    9. Optimize memory usage patterns")
        
        if "Process never started properly" in possible_causes:
            print(f'    10. Check Python environment and dependencies")
            print(f'    11. Verify all required modules are installed")
        
        if "Process stopped responding" in possible_causes:
            print(f'    12. Check for network connectivity issues')
            print(f'    13. Verify API endpoints are accessible")
    
    else:
        print(f'  - GENERAL RECOMMENDATIONS:')
        print(f'    1. Restart main runtime: python main_runtime.py')
        print(f'    2. Monitor system resources after restart')
        print(f'    3. Check logs for any new errors')
        print(f'    4. Verify trading functionality works correctly')
    
    print(f'\n  - MONITORING AFTER RESTART:')
    print(f'    1. Use Task Manager or Process Monitor to track process')
    print(f'    2. Check trading_results.json for cycle updates')
    print(f'    3. Monitor system resources (CPU, Memory)')
    print(f'    4. Watch for new log files being created')
    
    print('\n' + '=' * 80)
    print('MAIN RUNTIME DEATH ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_main_runtime_death()
