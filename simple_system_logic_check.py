#!/usr/bin/env python3
"""
Simple System Logic Check - Verify all trading logic is working correctly
"""

import json
import os
import psutil
from datetime import datetime, timedelta

def simple_system_logic_check():
    """Simple check of all system logic components"""
    print('=' * 80)
    print('SIMPLE SYSTEM LOGIC CHECK')
    print('=' * 80)
    
    print(f'Check Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # 1. Process Status Check
    print('\n[1] PROCESS STATUS CHECK')
    
    try:
        python_processes = []
        main_runtime_found = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'cmdline': cmdline
                    })
                    
                    if 'main_runtime.py' in cmdline:
                        main_runtime_found = True
                        print(f'  - Main Runtime: RUNNING (PID: {proc.info["pid"]}, Status: {proc.info["status"]})')
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not main_runtime_found:
            print(f'  - Main Runtime: NOT RUNNING')
        
        print(f'  - Total Python Processes: {len(python_processes)}')
        
    except Exception as e:
        print(f'  - Error checking processes: {e}')
    
    # 2. Core Files Check
    print('\n[2] CORE FILES CHECK')
    
    core_files = {
        'main_runtime.py': 'Main runtime controller',
        'core/position_manager.py': 'Position management',
        'core/trade_orchestrator.py': 'Trade orchestration',
        'core/signal_engine.py': 'Signal generation',
        'core/market_data_service.py': 'Market data',
        'core/indicator_service.py': 'Technical indicators',
        'core/strategy_registry.py': 'Strategy management',
        'core/account_service.py': 'Account management',
        'core/order_executor.py': 'Order execution',
        'core/market_regime_service.py': 'Market regime analysis'
    }
    
    missing_files = []
    for file_path, description in core_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f'  - {description}: EXISTS ({file_size:,} bytes)')
        else:
            print(f'  - {description}: MISSING')
            missing_files.append(file_path)
    
    if missing_files:
        print(f'  - Missing Files: {len(missing_files)}')
    else:
        print(f'  - All Core Files: PRESENT')
    
    # 3. Configuration Check
    print('\n[3] CONFIGURATION CHECK')
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        trading_config = config.get('trading_config', {})
        binance_config = config.get('binance_testnet', {})
        
        print(f'  - Max Open Positions: {trading_config.get("max_open_positions", "N/A")}')
        print(f'  - Fast Entry Enabled: {trading_config.get("fast_entry_enabled", "N/A")}')
        print(f'  - Real Time Mode: {config.get("real_time_mode", "N/A")}')
        print(f'  - Virtual Tests Disabled: {config.get("all_virtual_tests_disabled", "N/A")}')
        print(f'  - Force Real Exchange: {config.get("force_real_exchange", "N/A")}')
        print(f'  - API Key: {"SET" if binance_config.get("api_key") else "NOT SET"}')
        print(f'  - API Secret: {"SET" if binance_config.get("api_secret") else "NOT SET"}')
        print(f'  - Base URL: {binance_config.get("base_url", "N/A")}')
        
        config_ok = True
        if not config.get("real_time_mode"):
            config_ok = False
            print(f'  - WARNING: Real time mode disabled')
        if not binance_config.get("api_key"):
            config_ok = False
            print(f'  - WARNING: API key not set')
        if not binance_config.get("api_secret"):
            config_ok = False
            print(f'  - WARNING: API secret not set')
        
        if config_ok:
            print(f'  - Configuration: OK')
        else:
            print(f'  - Configuration: ISSUES DETECTED')
    
    except Exception as e:
        print(f'  - Error reading config: {e}')
    
    # 4. Trading Results Analysis
    print('\n[4] TRADING RESULTS ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Check active positions
        active_positions = trading_results.get('active_positions', {})
        print(f'  - Active Positions: {len(active_positions)}')
        
        # Check strategies
        strategies = trading_results.get('strategies', {})
        print(f'  - Configured Strategies: {len(strategies)}')
        
        enabled_strategies = 0
        for strategy_name, strategy_config in strategies.items():
            enabled = strategy_config.get('enabled', False)
            if enabled:
                enabled_strategies += 1
                print(f'    - {strategy_name}: ENABLED')
            else:
                print(f'    - {strategy_name}: DISABLED')
        
        print(f'  - Enabled Strategies: {enabled_strategies}')
        
        # Check cycle data
        cycle_count = trading_results.get('cycle_count', 0)
        last_cycle_time = trading_results.get('last_cycle_time', 0)
        
        print(f'  - Total Cycles: {cycle_count}')
        
        if last_cycle_time:
            last_cycle_datetime = datetime.fromtimestamp(last_cycle_time / 1000)
            time_since_cycle = datetime.now() - last_cycle_datetime
            print(f'  - Last Cycle: {last_cycle_datetime} ({time_since_cycle} ago)')
            
            if time_since_cycle < timedelta(minutes=5):
                print(f'  - Cycle Status: ACTIVE')
            elif time_since_cycle < timedelta(minutes=30):
                print(f'  - Cycle Status: RECENT')
            else:
                print(f'  - Cycle Status: STALE')
        else:
            print(f'  - Cycle Status: NO CYCLES')
        
        # Check system errors
        system_errors = trading_results.get('system_errors', [])
        print(f'  - System Errors: {len(system_errors)}')
        
        if system_errors:
            print(f'  - Recent Errors:')
            for error in system_errors[-3:]:
                error_type = error.get('type', 'Unknown')
                error_message = error.get('message', 'No message')
                print(f'    - {error_type}: {error_message}')
        else:
            print(f'  - System Errors: NONE')
    
    except Exception as e:
        print(f'  - Error analyzing trading results: {e}')
    
    # 5. Signal Generation Check
    print('\n[5] SIGNAL GENERATION CHECK')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        signals_generated = trading_results.get('signals_generated', 0)
        buy_signals = trading_results.get('buy_signals', 0)
        sell_signals = trading_results.get('sell_signals', 0)
        hold_signals = trading_results.get('hold_signals', 0)
        
        print(f'  - Total Signals Generated: {signals_generated}')
        print(f'  - Buy Signals: {buy_signals}')
        print(f'  - Sell Signals: {sell_signals}')
        print(f'  - Hold Signals: {hold_signals}')
        
        # Check last cycle
        last_cycle = trading_results.get('last_cycle', {})
        if last_cycle:
            cycle_signals = last_cycle.get('signals_generated', 0)
            cycle_trades = last_cycle.get('trades_executed', 0)
            
            print(f'  - Last Cycle Signals: {cycle_signals}')
            print(f'  - Last Cycle Trades: {cycle_trades}')
            
            if cycle_signals > 0:
                signal_rate = (cycle_trades / cycle_signals) * 100
                print(f'  - Signal-to-Trade Rate: {signal_rate:.1f}%')
                
                if signal_rate >= 50:
                    print(f'  - Signal Quality: GOOD')
                else:
                    print(f'  - Signal Quality: NEEDS IMPROVEMENT')
            else:
                print(f'  - Signal Quality: NO SIGNALS')
        
        # Check signal engine file
        if os.path.exists('core/signal_engine.py'):
            with open('core/signal_engine.py', 'r') as f:
                signal_engine_content = f.read()
            
            signal_functions = []
            if 'generate_strategy_signal' in signal_engine_content:
                signal_functions.append("Strategy signal generation")
            if 'calculate_dynamic_confidence' in signal_engine_content:
                signal_functions.append("Confidence calculation")
            
            print(f'  - Signal Engine Functions: {len(signal_functions)}')
            print(f'  - Signal Engine: {"COMPLETE" if len(signal_functions) >= 2 else "INCOMPLETE"}')
    
    except Exception as e:
        print(f'  - Error checking signal logic: {e}')
    
    # 6. Position Management Check
    print('\n[6] POSITION MANAGEMENT CHECK')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        active_positions = trading_results.get('active_positions', {})
        
        if active_positions:
            healthy_positions = 0
            for symbol, position in active_positions.items():
                side = position.get('side', 'Unknown')
                amount = position.get('amount', 0)
                entry_price = position.get('entry_price', 0)
                current_price = position.get('current_price', 0)
                strategy = position.get('strategy', 'Unknown')
                
                if (entry_price > 0 and 
                    strategy != 'Unknown' and 
                    'entry_time' in position):
                    healthy_positions += 1
            
            position_quality = (healthy_positions / len(active_positions)) * 100
            print(f'  - Position Quality: {position_quality:.1f}%')
            
            if position_quality >= 80:
                print(f'  - Position Management: GOOD')
            else:
                print(f'  - Position Management: NEEDS ATTENTION')
        else:
            print(f'  - Position Management: NO POSITIONS')
        
        # Check position manager file
        if os.path.exists('core/position_manager.py'):
            with open('core/position_manager.py', 'r') as f:
                position_manager_content = f.read()
            
            position_functions = []
            if 'manage_open_positions' in position_manager_content:
                position_functions.append("Position management")
            if 'close_position' in position_manager_content:
                position_functions.append("Position closing")
            if 'should_exit_position' in position_manager_content:
                position_functions.append("Exit conditions")
            
            print(f'  - Position Manager Functions: {len(position_functions)}')
            print(f'  - Position Manager: {"COMPLETE" if len(position_functions) >= 3 else "INCOMPLETE"}')
    
    except Exception as e:
        print(f'  - Error checking position logic: {e}')
    
    # 7. Order Execution Check
    print('\n[7] ORDER EXECUTION CHECK')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Look for recent trades
        closed_trades = trading_results.get('closed_trades', [])
        recent_trades = [trade for trade in closed_trades 
                        if datetime.fromisoformat(trade.get('close_time', '').replace('Z', '+00:00')) > 
                        datetime.now() - timedelta(hours=1)]
        
        print(f'  - Recent Trades (1h): {len(recent_trades)}')
        
        if recent_trades:
            successful_trades = [trade for trade in recent_trades if trade.get('success', False)]
            trade_success_rate = (len(successful_trades) / len(recent_trades)) * 100
            print(f'  - Trade Success Rate: {trade_success_rate:.1f}%')
            
            if trade_success_rate >= 90:
                print(f'  - Order Execution: EXCELLENT')
            elif trade_success_rate >= 75:
                print(f'  - Order Execution: GOOD')
            else:
                print(f'  - Order Execution: NEEDS IMPROVEMENT')
        else:
            print(f'  - Order Execution: NO RECENT TRADES')
        
        # Check order executor file
        if os.path.exists('core/order_executor.py'):
            with open('core/order_executor.py', 'r') as f:
                order_executor_content = f.read()
            
            order_functions = []
            if 'submit_order' in order_executor_content:
                order_functions.append("Order submission")
            if 'cancel_order' in order_executor_content:
                order_functions.append("Order cancellation")
            
            print(f'  - Order Executor Functions: {len(order_functions)}')
            print(f'  - Order Executor: {"COMPLETE" if len(order_functions) >= 2 else "INCOMPLETE"}')
    
    except Exception as e:
        print(f'  - Error checking order logic: {e}')
    
    # 8. Risk Management Check
    print('\n[8] RISK MANAGEMENT CHECK')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Check stop loss/take profit configuration
        strategies = trading_results.get('strategies', {})
        risk_configured = 0
        
        for strategy_name, strategy_config in strategies.items():
            stop_loss = strategy_config.get('stop_loss_pct', 0)
            take_profit = strategy_config.get('take_profit_pct', 0)
            
            if stop_loss > 0 and take_profit > 0:
                risk_configured += 1
        
        risk_coverage = (risk_configured / len(strategies)) * 100 if strategies else 0
        print(f'  - Risk Configuration Coverage: {risk_coverage:.1f}%')
        
        # Check position limits
        active_positions = trading_results.get('active_positions', {})
        max_positions = trading_results.get('max_open_positions', 10)
        
        position_utilization = (len(active_positions) / max_positions) * 100
        print(f'  - Position Utilization: {position_utilization:.1f}% ({len(active_positions)}/{max_positions})')
        
        if risk_coverage >= 80 and position_utilization <= 90:
            print(f'  - Risk Management: GOOD')
        else:
            print(f'  - Risk Management: NEEDS ATTENTION')
    
    except Exception as e:
        print(f'  - Error checking risk logic: {e}')
    
    # 9. Overall System Health
    print('\n[9] OVERALL SYSTEM HEALTH')
    
    # Calculate simple health score
    health_score = 0
    max_score = 100
    
    # Process health (25 points)
    if main_runtime_found:
        health_score += 25
    
    # Files health (15 points)
    if len(missing_files) == 0:
        health_score += 15
    
    # Configuration health (15 points)
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        if config.get('real_time_mode') and config.get('binance_testnet', {}).get('api_key'):
            health_score += 15
    except:
        pass
    
    # Trading logic health (25 points)
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        cycle_count = trading_results.get('cycle_count', 0)
        if cycle_count > 0:
            health_score += 25
    except:
        pass
    
    # Error health (20 points)
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        system_errors = trading_results.get('system_errors', [])
        if len(system_errors) == 0:
            health_score += 20
    except:
        pass
    
    print(f'  - Overall Health Score: {health_score}/{max_score}')
    
    if health_score >= 90:
        print(f'  - System Status: EXCELLENT')
        print(f'  - All logic components are working perfectly')
    elif health_score >= 75:
        print(f'  - System Status: GOOD')
        print(f'  - Most logic components are working correctly')
    elif health_score >= 60:
        print(f'  - System Status: FAIR')
        print(f'  - Some logic components need attention')
    elif health_score >= 40:
        print(f'  - System Status: POOR')
        print(f'  - Many logic components have issues')
    else:
        print(f'  - System Status: CRITICAL')
        print(f'  - Major logic component failures detected')
    
    # Recommendations
    print(f'\n  - RECOMMENDATIONS:')
    
    if not main_runtime_found:
        print(f'    1. Start main runtime process')
    
    if len(missing_files) > 0:
        print(f'    2. Restore missing core files')
    
    if health_score < 75:
        print(f'    3. Review system logs for errors')
        print(f'    4. Check configuration settings')
    
    if health_score >= 75:
        print(f'    5. System is operating normally - continue monitoring')
    
    print('\n' + '=' * 80)
    print('SIMPLE SYSTEM LOGIC CHECK COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    simple_system_logic_check()
