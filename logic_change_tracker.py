#!/usr/bin/env python3
"""
Logic Change Tracker - Monitor trading logic changes
"""

import os
import json
import hashlib
from datetime import datetime
import glob

def get_file_hash(filepath):
    """Get file hash to detect changes"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def get_file_modification_time(filepath):
    """Get file modification time"""
    try:
        return os.path.getmtime(filepath)
    except:
        return None

def track_logic_changes():
    """Track changes in trading logic files"""
    print('=' * 80)
    print('LOGIC CHANGE TRACKER')
    print('=' * 80)
    
    print(f'Monitoring Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # Key files to monitor
    key_files = [
        'main_runtime.py',
        'core/signal_engine.py',
        'core/trade_orchestrator.py',
        'core/strategy_registry.py',
        'core/market_data_service.py',
        'core/indicator_service.py',
        'core/position_manager.py',
        'config.json',
        'trading_results.json'
    ]
    
    # Store current state
    current_state = {}
    
    print('\n[1] CURRENT LOGIC FILES STATUS')
    
    for filepath in key_files:
        if os.path.exists(filepath):
            file_hash = get_file_hash(filepath)
            mod_time = get_file_modification_time(filepath)
            file_size = os.path.getsize(filepath)
            
            current_state[filepath] = {
                'hash': file_hash,
                'mod_time': mod_time,
                'size': file_size
            }
            
            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S') if mod_time else 'Unknown'
            
            print(f'  {filepath}:')
            print(f'    - Hash: {file_hash[:16]}...')
            print(f'    - Modified: {mod_time_str}')
            print(f'    - Size: {file_size:,} bytes')
        else:
            print(f'  {filepath}: NOT FOUND')
    
    # Load previous state if exists
    previous_state = {}
    state_file = 'logic_change_state.json'
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                previous_state = json.load(f)
        except:
            pass
    
    # Compare states
    print('\n[2] LOGIC CHANGES DETECTED')
    
    changes_found = False
    
    for filepath, current_info in current_state.items():
        if filepath in previous_state:
            prev_info = previous_state[filepath]
            
            # Check for changes
            if current_info['hash'] != prev_info['hash']:
                changes_found = True
                print(f'  🔄 CHANGED: {filepath}')
                print(f'    - Previous Hash: {prev_info["hash"][:16]}...')
                print(f'    - Current Hash:  {current_info["hash"][:16]}...')
                print(f'    - Previous Modified: {datetime.fromtimestamp(prev_info["mod_time"]).strftime("%Y-%m-%d %H:%M:%S")}')
                print(f'    - Current Modified:  {datetime.fromtimestamp(current_info["mod_time"]).strftime("%Y-%m-%d %H:%M:%S")}')
                print(f'    - Size Change: {current_info["size"] - prev_info["size"]:+,} bytes')
                
                # Analyze file type and potential impact
                if 'signal_engine' in filepath:
                    print(f'    - Impact: 🎯 SIGNAL LOGIC CHANGED - Trading signals may be affected')
                elif 'trade_orchestrator' in filepath:
                    print(f'    - Impact: 🔄 TRADING EXECUTION CHANGED - Order execution may be affected')
                elif 'strategy_registry' in filepath:
                    print(f'    - Impact: 📋 STRATEGY CONFIGURATION CHANGED - Strategy parameters may be affected')
                elif 'market_data_service' in filepath:
                    print(f'    - Impact: 📊 MARKET DATA PROCESSING CHANGED - Data analysis may be affected')
                elif 'indicator_service' in filepath:
                    print(f'    - Impact: 📈 INDICATOR CALCULATIONS CHANGED - Technical analysis may be affected')
                elif 'position_manager' in filepath:
                    print(f'    - Impact: 💰 POSITION MANAGEMENT CHANGED - Risk management may be affected')
                elif 'config.json' in filepath:
                    print(f'    - Impact: ⚙️ CONFIGURATION CHANGED - System settings may be affected')
                elif 'trading_results.json' in filepath:
                    print(f'    - Impact: 📊 TRADING DATA UPDATED - Normal operation')
                elif 'main_runtime.py' in filepath:
                    print(f'    - Impact: 🚀 MAIN RUNTIME CHANGED - Core system logic may be affected')
                
            elif current_info['mod_time'] != prev_info['mod_time']:
                print(f'  📅 MODIFIED: {filepath}')
                print(f'    - Previous Modified: {datetime.fromtimestamp(prev_info["mod_time"]).strftime("%Y-%m-%d %H:%M:%S")}')
                print(f'    - Current Modified:  {datetime.fromtimestamp(current_info["mod_time"]).strftime("%Y-%m-%d %H:%M:%S")}')
                print(f'    - Note: File timestamp changed but content hash is same')
        else:
            print(f'  ➕ NEW FILE: {filepath}')
            print(f'    - Hash: {current_info["hash"][:16]}...')
            print(f'    - Modified: {datetime.fromtimestamp(current_info["mod_time"]).strftime("%Y-%m-%d %H:%M:%S")}')
            print(f'    - Size: {current_info["size"]:,} bytes')
    
    if not changes_found:
        print('  ✅ NO LOGIC CHANGES DETECTED')
    
    # Check for deleted files
    for filepath in previous_state:
        if filepath not in current_state:
            print(f'  🗑️  DELETED: {filepath}')
    
    # Save current state
    try:
        with open(state_file, 'w') as f:
            json.dump(current_state, f, indent=2)
    except:
        pass
    
    # Check recent trading activity
    print('\n[3] RECENT TRADING ACTIVITY')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        active_positions = trading_results.get('active_positions', {})
        closed_trades = trading_results.get('closed_trades', [])
        
        print(f'  - Active Positions: {len(active_positions)}')
        print(f'  - Total Closed Trades: {len(closed_trades)}')
        
        # Check recent trades (last hour)
        one_hour_ago = datetime.now().timestamp() - 3600
        recent_trades = []
        
        for trade in closed_trades[-10:]:  # Check last 10 trades
            trade_time = trade.get('close_time', trade.get('time', 0))
            if trade_time and trade_time / 1000 > one_hour_ago:
                recent_trades.append(trade)
        
        print(f'  - Trades in Last Hour: {len(recent_trades)}')
        
        if recent_trades:
            print(f'  - Recent Trades:')
            for trade in recent_trades[-3:]:  # Show last 3
                symbol = trade.get('symbol', 'Unknown')
                side = trade.get('side', 'Unknown')
                pnl = trade.get('realized_pnl', 0)
                trade_time = datetime.fromtimestamp(trade.get('close_time', 0) / 1000).strftime('%H:%M:%S')
                print(f'    - {trade_time}: {symbol} {side} (PnL: {pnl:+.4f})')
    
    except:
        print('  - Error reading trading results')
    
    # Check system processes
    print('\n[4] SYSTEM PROCESS STATUS')
    
    try:
        import psutil
        python_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'next-trade' in cmdline.lower() or 'main_runtime' in cmdline.lower():
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline
                        })
            except:
                pass
        
        print(f'  - Python Trading Processes: {len(python_processes)}')
        
        for proc in python_processes:
            print(f'    - PID {proc["pid"]}: {proc["cmdline"][:80]}...')
    
    except ImportError:
        print('  - psutil not available for process monitoring')
    
    # Configuration summary
    print('\n[5] CURRENT CONFIGURATION SUMMARY')
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        trading_config = config.get('trading_config', {})
        
        print(f'  - Real-Time Mode: {config.get("real_time_mode", "Unknown")}')
        print(f'  - Virtual Tests Disabled: {config.get("all_virtual_tests_disabled", "Unknown")}')
        print(f'  - Force Real Exchange: {config.get("force_real_exchange", "Unknown")}')
        print(f'  - Max Open Positions: {trading_config.get("max_open_positions", "Unknown")}')
        print(f'  - Fast Entry Enabled: {trading_config.get("fast_entry_enabled", "Unknown")}')
        print(f'  - Stop Loss %: {trading_config.get("stop_loss_pct", "Unknown")}')
        print(f'  - Take Profit %: {trading_config.get("take_profit_pct", "Unknown")}')
    
    except:
        print('  - Error reading configuration')
    
    print('\n' + '=' * 80)
    print('LOGIC CHANGE TRACKING COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    track_logic_changes()
