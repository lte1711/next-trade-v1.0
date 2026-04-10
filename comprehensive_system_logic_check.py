#!/usr/bin/env python3
"""
Comprehensive System Logic Check - Verify all trading logic is working correctly
"""

import json
import os
import psutil
from datetime import datetime, timedelta
import glob

def comprehensive_system_logic_check():
    """Comprehensive check of all system logic components"""
    print('=' * 80)
    print('COMPREHENSIVE SYSTEM LOGIC CHECK')
    print('=' * 80)
    
    print(f'Check Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # 1. Process Status Check
    print('\n[1] PROCESS STATUS CHECK')
    
    try:
        python_processes = []
        main_runtime_found = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'create_time']):
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
    
    # 2. Core Components Check
    print('\n[2] CORE COMPONENTS CHECK')
    
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
    
    for file_path, description in core_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f'  - {description}: EXISTS ({file_size:,} bytes, Modified: {mod_time.strftime("%H:%M:%S")})')
        else:
            print(f'  - {description}: MISSING')
    
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
        
        # Check for critical configuration issues
        issues = []
        if not trading_config.get("max_open_positions"):
            issues.append("Max open positions not set")
        if not config.get("real_time_mode"):
            issues.append("Real time mode disabled")
        if not binance_config.get("api_key"):
            issues.append("API key not set")
        if not binance_config.get("api_secret"):
            issues.append("API secret not set")
        
        if issues:
            print(f'  - Configuration Issues: {", ".join(issues)}')
        else:
            print(f'  - Configuration: OK')
    
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
        
        # Analyze position health
        healthy_positions = 0
        problematic_positions = 0
        
        for symbol, position in active_positions.items():
            side = position.get('side', 'Unknown')
            amount = position.get('amount', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            strategy = position.get('strategy', 'Unknown')
            
            # Calculate PnL percentage
            if amount != 0 and entry_price > 0 and current_price > 0:
                if side == 'LONG':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
            else:
                pnl_pct = 0
            
            # Check for problems
            problems = []
            if pnl_pct < -2:
                problems.append(f"Loss: {pnl_pct:.2f}%")
            if unrealized_pnl == 0 and current_price > 0:
                problems.append("Zero PnL")
            if strategy == 'Unknown' or strategy == 'None':
                problems.append("No strategy")
            
            if problems:
                problematic_positions += 1
            else:
                healthy_positions += 1
        
        print(f'  - Healthy Positions: {healthy_positions}')
        print(f'  - Problematic Positions: {problematic_positions}')
        
        # Check strategies
        strategies = trading_results.get('strategies', {})
        print(f'  - Configured Strategies: {len(strategies)}')
        
        for strategy_name, strategy_config in strategies.items():
            enabled = strategy_config.get('enabled', False)
            stop_loss = strategy_config.get('stop_loss_pct', 0)
            take_profit = strategy_config.get('take_profit_pct', 0)
            
            print(f'    - {strategy_name}: {"ENABLED" if enabled else "DISABLED"} (SL: {stop_loss:.3f}, TP: {take_profit:.3f})')
        
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
                print(f'  - Cycle Status: RECENT")
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
    
    except Exception as e:
        print(f'  - Error analyzing trading results: {e}')
    
    # 5. Signal Generation Logic Check
    print('\n[5] SIGNAL GENERATION LOGIC CHECK')
    
    try:
        # Check recent signal generation
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Look for recent signal diagnostics
        signals_generated = trading_results.get('signals_generated', 0)
        buy_signals = trading_results.get('buy_signals', 0)
        sell_signals = trading_results.get('sell_signals', 0)
        hold_signals = trading_results.get('hold_signals', 0)
        
        print(f'  - Total Signals Generated: {signals_generated}')
        print(f'  - Buy Signals: {buy_signals}')
        print(f'  - Sell Signals: {sell_signals}')
        print(f'  - Hold Signals: {hold_signals}')
        
        # Check last cycle signal quality
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
                elif signal_rate >= 25:
                    print(f'  - Signal Quality: FAIR')
                else:
                    print(f'  - Signal Quality: POOR')
            else:
                print(f'  - Signal Quality: NO SIGNALS')
        
        # Check signal engine file
        if os.path.exists('core/signal_engine.py'):
            with open('core/signal_engine.py', 'r') as f:
                signal_engine_content = f.read()
            
            # Check for key signal generation functions
            signal_functions = []
            if 'generate_strategy_signal' in signal_engine_content:
                signal_functions.append("Strategy signal generation")
            if 'calculate_dynamic_confidence' in signal_engine_content:
                signal_functions.append("Confidence calculation")
            if 'market_alignment_score' in signal_engine_content:
                signal_functions.append("Market alignment")
            
            print(f'  - Signal Engine Functions: {", ".join(signal_functions)}')
            
            if len(signal_functions) >= 3:
                print(f'  - Signal Engine: COMPLETE')
            elif len(signal_functions) >= 2:
                print(f'  - Signal Engine: PARTIAL')
            else:
                print(f'  - Signal Engine: INCOMPLETE')
    
    except Exception as e:
        print(f'  - Error checking signal logic: {e}')
    
    # 6. Position Management Logic Check
    print('\n[6] POSITION MANAGEMENT LOGIC CHECK')
    
    try:
        if os.path.exists('core/position_manager.py'):
            with open('core/position_manager.py', 'r') as f:
                position_manager_content = f.read()
            
            # Check for key position management functions
            position_functions = []
            if 'manage_open_positions' in position_manager_content:
                position_functions.append("Position management")
            if 'close_position' in position_manager_content:
                position_functions.append("Position closing")
            if 'should_exit_position' in position_manager_content:
                position_functions.append("Exit conditions")
            if 'manage_profit_targets' in position_manager_content:
                position_functions.append("Profit targets")
            
            print(f'  - Position Manager Functions: {", ".join(position_functions)}')
            
            if len(position_functions) >= 4:
                print(f'  - Position Manager: COMPLETE')
            elif len(position_functions) >= 3:
                print(f'  - Position Manager: PARTIAL')
            else:
                print(f'  - Position Manager: INCOMPLETE')
            
            # Check for protective order integration
            if 'protective_order_manager' in position_manager_content:
                print(f'  - Protective Orders: INTEGRATED')
            else:
                print(f'  - Protective Orders: NOT INTEGRATED')
        
        # Check actual position management in trading results
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        active_positions = trading_results.get('active_positions', {})
        
        if active_positions:
            # Check if positions have proper metadata
            proper_positions = 0
            for symbol, position in active_positions.items():
                if (position.get('entry_price', 0) > 0 and 
                    position.get('strategy', '') and 
                    'entry_time' in position):
                    proper_positions += 1
            
            position_quality = (proper_positions / len(active_positions)) * 100
            print(f'  - Position Quality: {position_quality:.1f}%')
            
            if position_quality >= 80:
                print(f'  - Position Management: GOOD')
            elif position_quality >= 60:
                print(f'  - Position Management: FAIR')
            else:
                print(f'  - Position Management: POOR')
        else:
            print(f'  - Position Management: NO POSITIONS')
    
    except Exception as e:
        print(f'  - Error checking position logic: {e}')
    
    # 7. Order Execution Logic Check
    print('\n[7] ORDER EXECUTION LOGIC CHECK')
    
    try:
        if os.path.exists('core/order_executor.py'):
            with open('core/order_executor.py', 'r') as f:
                order_executor_content = f.read()
            
            # Check for key order execution functions
            order_functions = []
            if 'submit_order' in order_executor_content:
                order_functions.append("Order submission")
            if 'cancel_order' in order_executor_content:
                order_functions.append("Order cancellation")
            if 'check_order_status' in order_executor_content:
                order_functions.append("Order status check")
            
            print(f'  - Order Executor Functions: {", ".join(order_functions)}')
            
            if len(order_functions) >= 3:
                print(f'  - Order Executor: COMPLETE')
            elif len(order_functions) >= 2:
                print(f'  - Order Executor: PARTIAL')
            else:
                print(f'  - Order Executor: INCOMPLETE')
        
        # Check recent trade execution
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Look for recent trades
        closed_trades = trading_results.get('closed_trades', [])
        recent_trades = [trade for trade in closed_trades 
                        if datetime.fromisoformat(trade.get('close_time', '').replace('Z', '+00:00')) > 
                        datetime.now() - timedelta(hours=1)]
        
        print(f'  - Recent Trades (1h): {len(recent_trades)}')
        
        if recent_trades:
            # Check trade quality
            successful_trades = [trade for trade in recent_trades if trade.get('success', False)]
            trade_success_rate = (len(successful_trades) / len(recent_trades)) * 100
            print(f'  - Trade Success Rate: {trade_success_rate:.1f}%')
            
            if trade_success_rate >= 90:
                print(f'  - Order Execution: EXCELLENT')
            elif trade_success_rate >= 75:
                print(f'  - Order Execution: GOOD')
            elif trade_success_rate >= 50:
                print(f'  - Order Execution: FAIR')
            else:
                print(f'  - Order Execution: POOR')
        else:
            print(f'  - Order Execution: NO RECENT TRADES')
    
    except Exception as e:
        print(f'  - Error checking order logic: {e}')
    
    # 8. Risk Management Logic Check
    print('\n[8] RISK MANAGEMENT LOGIC CHECK')
    
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
        
        # Check for over-leveraged positions
        overleveraged = 0
        for symbol, position in active_positions.items():
            position_size = position.get('position_amount_usdt', 0)
            max_size = position.get('max_position_size_usdt', 1000)
            
            if position_size > max_size * 1.1:  # 10% tolerance
                overleveraged += 1
        
        if overleveraged > 0:
            print(f'  - Over-leveraged Positions: {overleveraged}')
            print(f'  - Risk Management: VIOLATION')
        else:
            print(f'  - Risk Management: COMPLIANT')
        
        # Overall risk score
        risk_score = (risk_coverage + (100 - position_utilization)) / 2
        print(f'  - Overall Risk Score: {risk_score:.1f}/100')
        
        if risk_score >= 80:
            print(f'  - Risk Management: EXCELLENT')
        elif risk_score >= 60:
            print(f'  - Risk Management: GOOD')
        elif risk_score >= 40:
            print(f'  - Risk Management: FAIR')
        else:
            print(f'  - Risk Management: POOR')
    
    except Exception as e:
        print(f'  - Error checking risk logic: {e}')
    
    # 9. Market Data Logic Check
    print('\n[9] MARKET DATA LOGIC CHECK')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Check market data availability
        market_data = trading_results.get('market_data', {})
        print(f'  - Market Data Symbols: {len(market_data)}')
        
        if market_data:
            # Check data quality
            quality_symbols = 0
            for symbol, data in market_data.items():
                price = data.get('price', 0)
                volume = data.get('volume', 0)
                
                if price > 0 and volume > 0:
                    quality_symbols += 1
            
            data_quality = (quality_symbols / len(market_data)) * 100
            print(f'  - Data Quality: {data_quality:.1f}%')
            
            if data_quality >= 90:
                print(f'  - Market Data: EXCELLENT')
            elif data_quality >= 75:
                print(f'  - Market Data: GOOD')
            elif data_quality >= 50:
                print(f'  - Market Data: FAIR')
            else:
                print(f'  - Market Data: POOR')
        else:
            print(f'  - Market Data: NO DATA')
        
        # Check market data service
        if os.path.exists('core/market_data_service.py'):
            with open('core/market_data_service.py', 'r') as f:
                market_data_content = f.read()
            
            data_functions = []
            if 'get_market_data' in market_data_content:
                data_functions.append("Data retrieval")
            if 'update_market_data' in market_data_content:
                data_functions.append("Data update")
            if 'validate_data' in market_data_content:
                data_functions.append("Data validation")
            
            print(f'  - Market Data Functions: {", ".join(data_functions)}')
            
            if len(data_functions) >= 3:
                print(f'  - Market Data Service: COMPLETE')
            elif len(data_functions) >= 2:
                print(f'  - Market Data Service: PARTIAL')
            else:
                print(f'  - Market Data Service: INCOMPLETE')
    
    except Exception as e:
        print(f'  - Error checking market data logic: {e}')
    
    # 10. Overall System Health
    print('\n[10] OVERALL SYSTEM HEALTH')
    
    # Calculate overall health score
    health_scores = []
    
    # Process health (20 points)
    if main_runtime_found:
        health_scores.append(20)
    else:
        health_scores.append(0)
    
    # Configuration health (15 points)
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        if config.get('real_time_mode') and config.get('binance_testnet', {}).get('api_key'):
            health_scores.append(15)
        else:
            health_scores.append(5)
    except:
        health_scores.append(0)
    
    # Trading logic health (25 points)
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        cycle_count = trading_results.get('cycle_count', 0)
        if cycle_count > 0:
            health_scores.append(25)
        else:
            health_scores.append(10)
    except:
        health_scores.append(0)
    
    # Position health (20 points)
    if active_positions:
        if problematic_positions == 0:
            health_scores.append(20)
        elif problematic_positions < len(active_positions) / 2:
            health_scores.append(15)
        else:
            health_scores.append(5)
    else:
        health_scores.append(20)  # No positions is OK
    
    # Error health (20 points)
    if len(system_errors) == 0:
        health_scores.append(20)
    elif len(system_errors) < 5:
        health_scores.append(15)
    else:
        health_scores.append(5)
    
    total_score = sum(health_scores)
    max_score = 100
    
    print(f'  - Overall Health Score: {total_score}/{max_score}')
    
    if total_score >= 90:
        print(f'  - System Status: EXCELLENT')
        print(f'  - All logic components are working perfectly')
    elif total_score >= 75:
        print(f'  - System Status: GOOD')
        print(f'  - Most logic components are working correctly')
    elif total_score >= 60:
        print(f'  - System Status: FAIR')
        print(f'  - Some logic components need attention')
    elif total_score >= 40:
        print(f'  - System Status: POOR')
        print(f'  - Many logic components have issues')
    else:
        print(f'  - System Status: CRITICAL')
        print(f'  - Major logic component failures detected')
    
    # Recommendations
    print(f'\n  - RECOMMENDATIONS:')
    
    if not main_runtime_found:
        print(f'    1. Start main runtime process')
    
    if total_score < 75:
        print(f'    2. Review system logs for errors')
        print(f'    3. Check configuration settings')
        print(f'    4. Monitor trading cycle execution')
    
    if problematic_positions > 0:
        print(f'    5. Address problematic positions')
    
    if len(system_errors) > 0:
        print(f'    6. Fix system errors')
    
    if total_score >= 75:
        print(f'    7. System is operating normally - continue monitoring')
    
    print('\n' + '=' * 80)
    print('COMPREHENSIVE SYSTEM LOGIC CHECK COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    comprehensive_system_logic_check()
