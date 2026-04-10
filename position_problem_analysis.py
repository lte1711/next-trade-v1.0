#!/usr/bin/env python3
"""
Position Problem Analysis - Analyze why problematic positions are not being processed
"""

import json
import os
from datetime import datetime, timedelta

def analyze_position_problem_handling():
    """Analyze why problematic positions are not being processed"""
    print('=' * 80)
    print('POSITION PROBLEM HANDLING ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # 1. Check current active positions
    print('\n[1] CURRENT ACTIVE POSITIONS ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        active_positions = trading_results.get('active_positions', {})
        print(f'  - Total Active Positions: {len(active_positions)}')
        
        # Analyze each position for problems
        problematic_positions = []
        
        for symbol, position in active_positions.items():
            side = position.get('side', 'Unknown')
            amount = position.get('amount', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            strategy = position.get('strategy', 'Unknown')
            entry_time = position.get('entry_time', 0)
            
            # Calculate position age
            if entry_time:
                entry_datetime = datetime.fromtimestamp(entry_time / 1000)
                position_age = datetime.now() - entry_datetime
                age_minutes = position_age.total_seconds() / 60
            else:
                age_minutes = 0
            
            # Calculate PnL percentage
            if amount != 0 and entry_price > 0:
                if side == 'LONG':
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
            else:
                pnl_pct = 0
            
            # Identify problems
            problems = []
            
            # Check for significant losses
            if pnl_pct < -2:
                problems.append(f"Significant loss: {pnl_pct:.2f}%")
            elif pnl_pct < -1:
                problems.append(f"Loss: {pnl_pct:.2f}%")
            
            # Check for long holding time
            if age_minutes > 60:  # More than 1 hour
                problems.append(f"Long hold: {age_minutes:.0f} minutes")
            elif age_minutes > 30:  # More than 30 minutes
                problems.append(f"Extended hold: {age_minutes:.0f} minutes")
            
            # Check for no strategy
            if strategy == 'Unknown' or strategy == 'None':
                problems.append("No strategy assigned")
            
            # Check for zero PnL (might indicate stuck position)
            if unrealized_pnl == 0 and age_minutes > 10:
                problems.append("Zero PnL with age")
            
            # Check for price deviation
            if current_price > 0:
                price_deviation = abs(current_price - entry_price) / entry_price * 100
                if price_deviation > 5:
                    problems.append(f"High price deviation: {price_deviation:.2f}%")
            
            print(f'\n  [{symbol}] Position Analysis:')
            print(f'    - Side: {side}')
            print(f'    - Amount: {abs(amount):.0f}')
            print(f'    - Entry Price: ${entry_price:.6f}')
            print(f'    - Current Price: ${current_price:.6f}')
            print(f'    - PnL: ${unrealized_pnl:+.4f} ({pnl_pct:+.2f}%)')
            print(f'    - Strategy: {strategy}')
            print(f'    - Age: {age_minutes:.0f} minutes')
            
            if problems:
                print(f'    - Problems: {", ".join(problems)}')
                problematic_positions.append({
                    'symbol': symbol,
                    'problems': problems,
                    'pnl_pct': pnl_pct,
                    'age_minutes': age_minutes,
                    'strategy': strategy,
                    'unrealized_pnl': unrealized_pnl
                })
            else:
                print(f'    - Status: Normal')
        
        print(f'\n  - Problematic Positions: {len(problematic_positions)}')
        
    except Exception as e:
        print(f'  - Error analyzing positions: {e}')
    
    # 2. Check position management logic
    print('\n[2] POSITION MANAGEMENT LOGIC ANALYSIS')
    
    try:
        with open('core/position_manager.py', 'r') as f:
            position_manager_content = f.read()
        
        # Check for position closing logic
        closing_conditions = []
        
        if 'stop_loss' in position_manager_content.lower():
            closing_conditions.append("Stop loss triggers")
        
        if 'take_profit' in position_manager_content.lower():
            closing_conditions.append("Take profit triggers")
        
        if 'close_position' in position_manager_content:
            closing_conditions.append("Manual close function")
        
        if 'should_exit_position' in position_manager_content:
            closing_conditions.append("Exit condition checks")
        
        if 'ma_crossover' in position_manager_content.lower():
            closing_conditions.append("MA crossover exit")
        
        print(f'  - Closing Conditions Found: {len(closing_conditions)}')
        for condition in closing_conditions:
            print(f'    - {condition}')
        
        # Check for automatic closing logic
        if 'automatic' in position_manager_content.lower():
            print(f'  - Automatic Closing: YES')
        else:
            print(f'  - Automatic Closing: NO (may need manual intervention)')
        
        # Check for risk management
        if 'risk_management' in position_manager_content.lower():
            print(f'  - Risk Management: YES')
        else:
            print(f'  - Risk Management: NO')
        
    except Exception as e:
        print(f'  - Error reading position manager: {e}')
    
    # 3. Check recent trading cycles for position actions
    print('\n[3] RECENT CYCLE POSITION ACTIONS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Check last cycle
        last_cycle = trading_results.get('last_cycle', {})
        
        if last_cycle:
            trades_executed = last_cycle.get('trades_executed', 0)
            positions_closed = last_cycle.get('positions_closed', 0)
            positions_opened = last_cycle.get('positions_opened', 0)
            
            print(f'  - Last Cycle Trades: {trades_executed}')
            print(f'  - Positions Closed: {positions_closed}')
            print(f'  - Positions Opened: {positions_opened}')
            
            if trades_executed == 0 and len(problematic_positions) > 0:
                print(f'  - WARNING: No trades executed despite {len(problematic_positions)} problematic positions')
        
        # Check cycle count
        cycle_count = trading_results.get('cycle_count', 0)
        print(f'  - Total Cycles: {cycle_count}')
        
        if cycle_count == 0:
            print(f'  - WARNING: No cycles completed - position management not active')
    
    except Exception as e:
        print(f'  - Error analyzing cycle data: {e}')
    
    # 4. Check stop loss and take profit settings
    print('\n[4] STOP LOSS / TAKE PROFIT SETTINGS')
    
    try:
        strategies = trading_results.get('strategies', {})
        
        for strategy_name, strategy_config in strategies.items():
            enabled = strategy_config.get('enabled', False)
            stop_loss = strategy_config.get('stop_loss_pct', 0)
            take_profit = strategy_config.get('take_profit_pct', 0)
            
            print(f'  Strategy: {strategy_name}')
            print(f'    - Enabled: {enabled}')
            print(f'    - Stop Loss: {stop_loss:.3f} ({stop_loss*100:.1f}%)')
            print(f'    - Take Profit: {take_profit:.3f} ({take_profit*100:.1f}%)')
            
            # Check if settings are reasonable
            if stop_loss == 0:
                print(f'    - WARNING: No stop loss set')
            elif stop_loss > 0.1:
                print(f'    - WARNING: Very high stop loss ({stop_loss*100:.1f}%)')
            
            if take_profit == 0:
                print(f'    - WARNING: No take profit set')
            elif take_profit < stop_loss:
                print(f'    - WARNING: Take profit lower than stop loss')
    
    except Exception as e:
        print(f'  - Error analyzing strategy settings: {e}')
    
    # 5. Check for position-specific issues
    print('\n[5] POSITION-SPECIFIC ISSUE ANALYSIS')
    
    for pos in problematic_positions:
        symbol = pos['symbol']
        problems = pos['problems']
        pnl_pct = pos['pnl_pct']
        age_minutes = pos['age_minutes']
        strategy = pos['strategy']
        unrealized_pnl = pos['unrealized_pnl']
        
        print(f'\n  [{symbol}] Issue Analysis:')
        print(f'    - Problems: {", ".join(problems)}')
        print(f'    - PnL: {pnl_pct:+.2f}%')
        print(f'    - Age: {age_minutes:.0f} minutes')
        print(f'    - Strategy: {strategy}')
        
        # Determine why not closed
        reasons_not_closed = []
        
        # Check stop loss
        if 'Significant loss' in str(problems) or 'Loss' in str(problems):
            strategies = trading_results.get('strategies', {})
            position_strategy = strategies.get(strategy, {})
            stop_loss_pct = position_strategy.get('stop_loss_pct', 0)
            
            if stop_loss_pct > 0:
                required_loss = stop_loss_pct * 100
                if pnl_pct > -required_loss:
                    reasons_not_closed.append(f"Loss {pnl_pct:.2f}% not below stop loss {required_loss:.1f}%")
                else:
                    reasons_not_closed.append(f"Stop loss should have triggered at {required_loss:.1f}%")
            else:
                reasons_not_closed.append("No stop loss configured")
        
        # Check take profit
        if pnl_pct > 0:
            position_strategy = strategies.get(strategy, {})
            take_profit_pct = position_strategy.get('take_profit_pct', 0)
            
            if take_profit_pct > 0:
                required_profit = take_profit_pct * 100
                if pnl_pct < required_profit:
                    reasons_not_closed.append(f"Profit {pnl_pct:.2f}% not above take profit {required_profit:.1f}%")
            else:
                reasons_not_closed.append("No take profit configured")
        
        # Check age
        if 'Long hold' in str(problems) or 'Extended hold' in str(problems):
            reasons_not_closed.append(f"No time-based exit configured")
        
        # Check strategy
        if strategy == 'Unknown' or strategy == 'None':
            reasons_not_closed.append("No strategy means no exit rules")
        
        # Check for stuck position
        if 'Zero PnL with age' in str(problems):
            reasons_not_closed.append("Position may be stuck or not updating")
        
        print(f'    - Reasons not closed: {", ".join(reasons_not_closed)}')
    
    # 6. Check system errors
    print('\n[6] SYSTEM ERROR ANALYSIS')
    
    try:
        system_errors = trading_results.get('system_errors', [])
        print(f'  - Total System Errors: {len(system_errors)}')
        
        if system_errors:
            print(f'  - Recent System Errors:')
            for error in system_errors[-5:]:
                error_type = error.get('type', 'Unknown')
                error_message = error.get('message', 'No message')
                timestamp = error.get('timestamp', 'No timestamp')
                print(f'    - {error_type}: {error_message}')
                
                if 'position' in error_message.lower():
                    print(f'      -> Position-related error detected')
        
        # Check last cycle errors
        last_cycle = trading_results.get('last_cycle', {})
        last_cycle_errors = last_cycle.get('errors', [])
        
        if last_cycle_errors:
            print(f'  - Last Cycle Errors: {len(last_cycle_errors)}')
            for error in last_cycle_errors:
                print(f'    - {error}')
                
                if 'position' in str(error).lower():
                    print(f'      -> Position-related error in last cycle')
    
    except Exception as e:
        print(f'  - Error analyzing system errors: {e}')
    
    # 7. Summary and recommendations
    print('\n[7] SUMMARY AND RECOMMENDATIONS')
    
    if problematic_positions:
        print(f'  - Problematic Positions: {len(problematic_positions)}')
        print(f'  - Main Issues:')
        
        # Categorize problems
        loss_positions = [p for p in problematic_positions if 'Loss' in str(p['problems'])]
        old_positions = [p for p in problematic_positions if 'hold' in str(p['problems'])]
        no_strategy_positions = [p for p in problematic_positions if p['strategy'] in ['Unknown', 'None']]
        stuck_positions = [p for p in problematic_positions if 'Zero PnL' in str(p['problems'])]
        
        if loss_positions:
            print(f'    - Loss Positions: {len(loss_positions)} (stop loss not triggering)')
        
        if old_positions:
            print(f'    - Old Positions: {len(old_positions)} (no time-based exit)')
        
        if no_strategy_positions:
            print(f'    - No Strategy Positions: {len(no_strategy_positions)} (no exit rules)')
        
        if stuck_positions:
            print(f'    - Stuck Positions: {len(stuck_positions)} (not updating)')
        
        print(f'\n  - RECOMMENDATIONS:')
        
        if loss_positions:
            print(f'    1. Check stop loss configuration and triggers')
            print(f'    2. Verify stop loss is being properly calculated')
            print(f'    3. Consider manual closure of significant losses')
        
        if old_positions:
            print(f'    4. Implement time-based exit rules')
            print(f'    5. Set maximum holding time limits')
        
        if no_strategy_positions:
            print(f'    6. Assign strategies to unmanaged positions')
            print(f'    7. Set default exit rules for orphan positions')
        
        if stuck_positions:
            print(f'    8. Check price feed updates')
            print(f'    9. Verify PnL calculation logic')
            print(f'    10. Force position refresh if needed')
        
        print(f'\n  - IMMEDIATE ACTIONS:')
        print(f'    1. Review position manager logs for errors')
        print(f'    2. Check if stop loss/take profit are being triggered')
        print(f'    3. Verify price data is updating correctly')
        print(f'    4. Consider manual intervention for critical positions')
    
    else:
        print(f'  - No problematic positions detected')
        print(f'  - All positions appear to be within normal parameters')
    
    print('\n' + '=' * 80)
    print('POSITION PROBLEM HANDLING ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_position_problem_handling()
