import json
import subprocess
import sys
import os
import time
from datetime import datetime


def _find_main_runtime_processes():
    """Find python processes whose command line includes the runtime loop script."""
    try:
        script_name = 'main_runtime_background_loop.py'
        ps_command = (
            "Get-CimInstance Win32_Process "
            "| Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*main_runtime_background_loop.py*' } "
            "| Select-Object ProcessId, CommandLine "
            "| ConvertTo-Json -Compress"
        )
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_command],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        parsed = json.loads(result.stdout)
        if isinstance(parsed, dict):
            parsed = [parsed]

        processes = []
        for item in parsed:
            pid = item.get('ProcessId')
            if pid:
                processes.append({
                    'pid': str(pid),
                    'command_line': item.get('CommandLine', ''),
                })
        return processes
    except Exception:
        return []

def stop_main_runtime():
    """Stop main runtime background process"""
    print("Stopping Main Runtime Background Process...")
    
    stopped_processes = []
    
    # Find and stop main runtime processes
    try:
        for process in _find_main_runtime_processes():
            pid = process['pid']
            try:
                subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
                stopped_processes.append(pid)
                print(f"  - Stopped Process ID: {pid}")
            except Exception as e:
                print(f"  - Error stopping process {pid}: {e}")
        
        # Wait for processes to terminate
        time.sleep(2)
        
        # Check if any processes are still running
        remaining_processes = [process['pid'] for process in _find_main_runtime_processes()]
        
        if remaining_processes:
            print(f"  - WARNING: {len(remaining_processes)} processes still running")
            for pid in remaining_processes:
                print(f"    - Process ID: {pid}")
        else:
            print("  - All main runtime processes stopped successfully")
    
    except Exception as e:
        print(f"  - Error stopping processes: {e}")
    
    # Update trading results
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Update main runtime background status
        if 'main_runtime_background' not in results:
            results['main_runtime_background'] = {}
        
        results['main_runtime_background']['stopped_at'] = datetime.now().isoformat()
        results['main_runtime_background']['stopped_processes'] = stopped_processes
        results['main_runtime_background']['status'] = 'stopped'
        
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("  - Trading results updated")
    
    except Exception as e:
        print(f"  - Error updating results: {e}")
    
    print(f"\nMain Runtime Stop Complete")
    print(f"Stopped Processes: {len(stopped_processes)}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    stop_main_runtime()
