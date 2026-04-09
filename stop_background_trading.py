
import psutil
import time
from datetime import datetime

def stop_background_trading():
    """Stop background trading processes"""
    print("Stopping Background Trading Processes...")
    
    stopped_processes = []
    
    # Find and stop background trading processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'background_trading_loop.py' in cmdline:
                    pid = proc.info['pid']
                    proc.terminate()
                    stopped_processes.append(pid)
                    print(f"  - Stopped Process ID: {pid}")
        except:
            continue
    
    # Wait for processes to terminate
    time.sleep(2)
    
    # Check if any processes are still running
    remaining_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'background_trading_loop.py' in cmdline:
                    remaining_processes.append(proc.info['pid'])
        except:
            continue
    
    if remaining_processes:
        print(f"  - WARNING: {len(remaining_processes)} processes still running")
        for pid in remaining_processes:
            print(f"    - Process ID: {pid}")
    else:
        print("  - All background trading processes stopped successfully")
    
    # Update trading results
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        if 'background_trading' in results:
            results['background_trading']['stopped_at'] = datetime.now().isoformat()
            results['background_trading']['stopped_processes'] = stopped_processes
            
            with open('trading_results.json', 'w') as f:
                json.dump(results, f, indent=2)
        
        print("  - Trading results updated")
    
    except Exception as e:
        print(f"  - Error updating results: {e}")
    
    print(f"\nBackground Trading Stop Complete")
    print(f"Stopped Processes: {len(stopped_processes)}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    stop_background_trading()
