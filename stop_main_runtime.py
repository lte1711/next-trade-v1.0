import subprocess
import sys
import os
from datetime import datetime

def stop_main_runtime():
    """Stop main runtime background process"""
    print("Stopping Main Runtime Background Process...")
    
    stopped_processes = []
    
    # Find and stop main runtime processes
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
            
            for line in python_lines:
                if 'main_runtime_background_loop.py' in line:
                    # Extract PID from the line
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        try:
                            # Terminate the process
                            subprocess.run(['taskkill', '/PID', pid, '/F'], 
                                          capture_output=True)
                            stopped_processes.append(pid)
                            print(f"  - Stopped Process ID: {pid}")
                        except Exception as e:
                            print(f"  - Error stopping process {pid}: {e}")
        
        # Wait for processes to terminate
        time.sleep(2)
        
        # Check if any processes are still running
        remaining_processes = []
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        
        if 'python.exe' in result.stdout:
            python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
            for line in python_lines:
                if 'main_runtime_background_loop.py' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remaining_processes.append(parts[1])
        
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
