#!/usr/bin/env python3
"""
New Entry Analysis - Analyze why new entries are not happening
"""

import json
import os
from datetime import datetime
import time

def analyze_new_entry_blockers():
    """Analyze why new entries are not happening"""
    print('=' * 80)
    print('NEW ENTRY BLOCKER ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # 1. Check current system configuration
    print('\n[1] SYSTEM CONFIGURATION ANALYSIS')
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        trading_config = config.get('trading_config', {})
        
        print(f'  - Max Open Positions: {trading_config.get("max_open_positions", "N/A")}')
        print(f'  - Fast Entry Enabled: {trading_config.get("fast_entry_enabled", "N/A")}')
        print(f'  - Real Time Mode: {config.get("real_time_mode", "N/A")}')
        print(f'  - Virtual Tests Disabled: {config.get("all_virtual_tests_disabled", "N/A")}')
        print(f'  - Force Real Exchange: {config.get("force_real_exchange", "N/A")}')
        
        # Check for potential blockers
        max_positions = trading_config.get('max_open_positions', 10)
        fast_entry = trading_config.get('fast_entry_enabled', False)
        
        if not fast_entry:
            print(f'  - BLOCKER: Fast entry is DISABLED')
        
    except Exception as e:
        print(f'  - Error reading config: {e}')
    
    # 2. Check current positions
    print('\n[2] CURRENT POSITIONS ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        active_positions = trading_results.get('active_positions', {})
        
        print(f'  - Current Active Positions: {len(active_positions)}')
        print(f'  - Max Allowed Positions: {max_positions}')
        print(f'  - Position Capacity: {max_positions - len(active_positions)}')
        
        if len(active_positions) >= max_positions:
            print(f'  - BLOCKER: Maximum position limit reached ({len(active_positions)}/{max_positions})')
        
        # Show position details
        for symbol, position in active_positions.items():
            side = position.get('side', 'Unknown')
            amount = position.get('amount', 0)
            strategy = position.get('strategy', 'Unknown')
            entry_time = position.get('entry_time', 0)
            
            if entry_time:
                entry_datetime = datetime.fromtimestamp(entry_time / 1000)
                time_held = datetime.now() - entry_datetime
                print(f'    {symbol}: {side} {abs(amount):.0f} ({strategy}) - Held: {time_held}')
            else:
                print(f'    {symbol}: {side} {abs(amount):.0f} ({strategy})')
    
    except Exception as e:
        print(f'  - Error reading trading results: {e}')
    
    # 3. Check recent signal generation
    print('\n[3] SIGNAL GENERATION ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Signal statistics
        signals_generated = trading_results.get('signals_generated', 0)
        buy_signals = trading_results.get('buy_signals', 0)
        sell_signals = trading_results.get('sell_signals', 0)
        hold_signals = trading_results.get('hold_signals', 0)
        high_confidence_signals = trading_results.get('high_confidence_signals', 0)
        average_confidence = trading_results.get('average_confidence', 0)
        
        print(f'  - Total Signals Generated: {signals_generated}')
        print(f'  - Buy Signals: {buy_signals}')
        print(f'  - Sell Signals: {sell_signals}')
        print(f'  - Hold Signals: {hold_signals}')
        print(f'  - High Confidence Signals: {high_confidence_signals}')
        print(f'  - Average Confidence: {average_confidence:.3f}')
        
        if signals_generated == 0:
            print(f'  - BLOCKER: No signals generated at all')
        elif buy_signals == 0 and sell_signals == 0:
            print(f'  - BLOCKER: No trading signals generated (only HOLD signals)')
        elif high_confidence_signals == 0:
            print(f'  - BLOCKER: No high confidence signals (threshold not met)')
        
        # Check last cycle
        last_cycle = trading_results.get('last_cycle', {})
        if last_cycle:
            print(f'  - Last Cycle Analysis:')
            print(f'    - Signals Generated: {last_cycle.get("signals_generated", 0)}')
            print(f'    - Entry Opportunities: {last_cycle.get("entry_opportunities", 0)}')
            print(f'    - Entry Failures: {last_cycle.get("entry_failures", 0)}')
            print(f'    - Trades Executed: {last_cycle.get("trades_executed", 0)}')
            
            entry_failures = last_cycle.get('entry_failures', 0)
            if entry_failures > 0:
                print(f'  - BLOCKER: {entry_failures} entry failures in last cycle')
    
    except Exception as e:
        print(f'  - Error analyzing signals: {e}')
    
    # 4. Check strategy configurations
    print('\n[4] STRATEGY CONFIGURATION ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        strategies = trading_results.get('strategies', {})
        
        for strategy_name, strategy_config in strategies.items():
            enabled = strategy_config.get('enabled', False)
            stop_loss = strategy_config.get('stop_loss_pct', 0)
            take_profit = strategy_config.get('take_profit_pct', 0)
            max_position_size = strategy_config.get('max_position_size_usdt', 0)
            
            print(f'  Strategy: {strategy_name}')
            print(f'    - Enabled: {enabled}')
            print(f'    - Stop Loss: {stop_loss:.3f}')
            print(f'    - Take Profit: {take_profit:.3f}')
            print(f'    - Max Position Size: ${max_position_size:.2f}')
            
            if not enabled:
                print(f'    - BLOCKER: Strategy is disabled')
        
        # Check strategy registry for filters
        try:
            with open('core/strategy_registry.py', 'r') as f:
                registry_content = f.read()
            
            if 'min_confidence' in registry_content:
                print(f'  - Strategy Registry: Confidence filters detected')
            
            if 'min_trend_strength' in registry_content:
                print(f'  - Strategy Registry: Trend strength filters detected')
            
            if 'max_volatility' in registry_content:
                print(f'  - Strategy Registry: Volatility filters detected')
        
        except Exception as e:
            print(f'  - Error reading strategy registry: {e}')
    
    except Exception as e:
        print(f'  - Error analyzing strategies: {e}')
    
    # 5. Check market data availability
    print('\n[5] MARKET DATA ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        market_data = trading_results.get('market_data', {})
        
        print(f'  - Available Market Data Symbols: {len(market_data)}')
        
        if len(market_data) == 0:
            print(f'  - BLOCKER: No market data available')
        else:
            # Check sample market data quality
            sample_symbols = list(market_data.keys())[:5]
            print(f'  - Sample Market Data:')
            
            for symbol in sample_symbols:
                data = market_data[symbol]
                price = data.get('price', 0)
                volume = data.get('volume', 0)
                volatility = data.get('volatility', 0)
                
                print(f'    {symbol}: Price ${price:.6f}, Volume {volume:.0f}, Vol {volatility:.4f}')
                
                if price == 0:
                    print(f'      - ISSUE: Price is 0')
                if volume == 0:
                    print(f'      - ISSUE: Volume is 0')
                if volatility == 0:
                    print(f'      - ISSUE: Volatility is 0')
        
        # Check symbol list
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            symbol_list = config.get('trading_config', {}).get('symbol_list', [])
            print(f'  - Configured Symbol List: {len(symbol_list)} symbols')
            
            if len(symbol_list) == 0:
                print(f'  - BLOCKER: No symbols configured for trading')
        
        except Exception as e:
            print(f'  - Error reading symbol list: {e}')
    
    except Exception as e:
        print(f'  - Error analyzing market data: {e}')
    
    # 6. Check account balance and margin
    print('\n[6] ACCOUNT BALANCE ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Use latest monitoring data
        account_balance = 8621.98  # From latest monitoring
        available_balance = 8604.93  # From latest monitoring
        
        print(f'  - Total Balance: ${account_balance:.2f}')
        print(f'  - Available Balance: ${available_balance:.2f}')
        
        # Check minimum balance requirements
        min_balance_per_position = 100  # Assuming minimum $100 per position
        max_new_positions = int(available_balance / min_balance_per_position)
        
        print(f'  - Estimated Max New Positions: {max_new_positions}')
        
        if available_balance < min_balance_per_position:
            print(f'  - BLOCKER: Insufficient balance for new positions')
        elif max_new_positions <= 0:
            print(f'  - BLOCKER: Balance too low for new positions')
        
        # Check position sizing
        strategies = trading_results.get('strategies', {})
        for strategy_name, strategy_config in strategies.items():
            max_position_size = strategy_config.get('max_position_size_usdt', 0)
            if available_balance < max_position_size:
                print(f'  - BLOCKER: Insufficient balance for {strategy_name} (need ${max_position_size:.2f}, have ${available_balance:.2f})')
    
    except Exception as e:
        print(f'  - Error analyzing account balance: {e}')
    
    # 7. Check recent errors
    print('\n[7] ERROR ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        system_errors = trading_results.get('system_errors', [])
        
        print(f'  - Total System Errors: {len(system_errors)}')
        
        if len(system_errors) > 0:
            print(f'  - Recent Errors:')
            for error in system_errors[-5:]:  # Show last 5 errors
                error_type = error.get('type', 'Unknown')
                error_message = error.get('message', 'No message')
                timestamp = error.get('timestamp', 'No timestamp')
                print(f'    - {error_type}: {error_message}')
            
            print(f'  - BLOCKER: {len(system_errors)} system errors detected')
        
        # Check last cycle errors
        last_cycle = trading_results.get('last_cycle', {})
        last_cycle_errors = last_cycle.get('errors', [])
        
        if len(last_cycle_errors) > 0:
            print(f'  - Last Cycle Errors: {len(last_cycle_errors)}')
            for error in last_cycle_errors:
                print(f'    - {error}')
    
    except Exception as e:
        print(f'  - Error analyzing system errors: {e}')
    
    # 8. Check trading cycle status
    print('\n[8] TRADING CYCLE STATUS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        last_cycle_time = trading_results.get('last_cycle_time', 0)
        if last_cycle_time:
            last_cycle_datetime = datetime.fromtimestamp(last_cycle_time / 1000)
            time_since_cycle = datetime.now() - last_cycle_datetime
            print(f'  - Last Trading Cycle: {last_cycle_datetime}')
            print(f'  - Time Since Last Cycle: {time_since_cycle}')
            
            if time_since_cycle.total_seconds() > 300:  # 5 minutes
                print(f'  - BLOCKER: Trading cycle not running recently ({time_since_cycle} ago)')
        else:
            print(f'  - BLOCKER: No trading cycles recorded')
        
        # Check cycle frequency
        cycle_count = trading_results.get('cycle_count', 0)
        print(f'  - Total Cycles Completed: {cycle_count}')
        
        if cycle_count == 0:
            print(f'  - BLOCKER: No trading cycles completed')
    
    except Exception as e:
        print(f'  - Error analyzing trading cycles: {e}')
    
    # 9. Summary of blockers
    print('\n[9] BLOCKER SUMMARY')
    
    blockers = []
    
    # Collect all potential blockers
    if not fast_entry:
        blockers.append("Fast entry is disabled")
    
    if len(active_positions) >= max_positions:
        blockers.append(f"Position limit reached ({len(active_positions)}/{max_positions})")
    
    if signals_generated == 0:
        blockers.append("No signals generated")
    elif buy_signals == 0 and sell_signals == 0:
        blockers.append("No trading signals (only HOLD)")
    elif high_confidence_signals == 0:
        blockers.append("No high confidence signals")
    
    if len(market_data) == 0:
        blockers.append("No market data available")
    
    if available_balance < min_balance_per_position:
        blockers.append("Insufficient balance")
    
    if len(system_errors) > 0:
        blockers.append(f"{len(system_errors)} system errors")
    
    if cycle_count == 0:
        blockers.append("No trading cycles completed")
    
    print(f'  - Total Blockers Identified: {len(blockers)}')
    
    if blockers:
        print(f'\n  - BLOCKERS:')
        for i, blocker in enumerate(blockers, 1):
            print(f'    {i}. {blocker}')
    else:
        print(f'  - No critical blockers identified')
    
    # 10. Recommendations
    print('\n[10] RECOMMENDATIONS')
    
    if blockers:
        print(f'  - IMMEDIATE ACTIONS:')
        
        if "Fast entry is disabled" in blockers:
            print(f'    1. Enable fast entry in config.json')
        
        if "Position limit reached" in blockers:
            print(f'    2. Increase max_open_positions or close existing positions')
        
        if "No signals generated" in blockers:
            print(f'    3. Check signal engine and market data feed')
        
        if "No trading signals" in blockers:
            print(f'    4. Lower signal confidence thresholds')
        
        if "No market data available" in blockers:
            print(f'    5. Fix market data service connection')
        
        if "Insufficient balance" in blockers:
            print(f'    6. Add funds or reduce position sizes')
        
        if "system errors" in blockers:
            print(f'    7. Fix system errors in trading logic')
        
        if "No trading cycles completed" in blockers:
            print(f'    8. Restart trading runtime')
        
        print(f'\n  - GENERAL RECOMMENDATIONS:')
        print(f'    1. Check system logs for detailed error information')
        print(f'    2. Verify API connections and permissions')
        print(f'    3. Review strategy parameters and thresholds')
        print(f'    4. Monitor system performance and resource usage')
        print(f'    5. Test with smaller position sizes first')
    else:
        print(f'  - System appears to be functioning normally')
        print(f'  - New entries may be blocked by market conditions')
        print(f'  - Consider waiting for better trading opportunities')
    
    print('\n' + '=' * 80)
    print('NEW ENTRY BLOCKER ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_new_entry_blockers()
