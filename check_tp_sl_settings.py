#!/usr/bin/env python3
"""
Check TP/SL Settings - Detailed analysis of take profit and stop loss settings
"""

import json
from datetime import datetime

def check_tp_sl_settings():
    """Detailed analysis of take profit and stop loss settings"""
    print('=' * 80)
    print('TAKE PROFIT AND STOP LOSS SETTINGS ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # 1. Active Positions TP/SL Analysis
    print('\n[1. ACTIVE POSITIONS TP/SL ANALYSIS]')
    
    active_positions = results.get('active_positions', {})
    
    if not active_positions:
        print('  - No active positions found')
    else:
        print(f'  - Total Active Positions: {len(active_positions)}')
        print(f'  - TP/SL Settings Analysis:')
        
        total_position_value = 0
        total_unrealized_pnl = 0
        
        for symbol, position in active_positions.items():
            # Extract position data
            amount = position.get('amount', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            side = position.get('side', 'UNKNOWN')
            strategy = position.get('strategy', 'Unknown')
            
            # TP/SL settings
            stop_loss_pct = position.get('stop_loss_pct', 0)
            take_profit_pct = position.get('take_profit_pct', 0)
            
            # Calculate position value
            try:
                entry_float = float(entry_price)
                current_float = float(current_price)
                amount_float = float(amount)
                
                position_value = entry_float * amount_float
                total_position_value += position_value
                
                # Calculate unrealized PnL
                if side == 'LONG':
                    unrealized_pnl = (current_float - entry_float) * amount_float
                else:
                    unrealized_pnl = (entry_float - current_float) * amount_float
                
                total_unrealized_pnl += unrealized_pnl
                
            except (ValueError, TypeError):
                position_value = 0
                unrealized_pnl = 0
            
            # Calculate TP/SL prices
            try:
                if side == 'LONG':
                    sl_price = entry_float * (1 - stop_loss_pct)
                    tp_price = entry_float * (1 + take_profit_pct)
                    
                    # Distance to TP/SL
                    distance_to_sl_pct = ((current_float - sl_price) / entry_float) * 100
                    distance_to_tp_pct = ((tp_price - current_float) / entry_float) * 100
                    
                else:  # SHORT
                    sl_price = entry_float * (1 + stop_loss_pct)
                    tp_price = entry_float * (1 - take_profit_pct)
                    
                    # Distance to TP/SL
                    distance_to_sl_pct = ((sl_price - current_float) / entry_float) * 100
                    distance_to_tp_pct = ((current_float - tp_price) / entry_float) * 100
                
            except (ValueError, TypeError):
                sl_price = 0
                tp_price = 0
                distance_to_sl_pct = 0
                distance_to_tp_pct = 0
            
            # Risk/Reward ratio
            risk_reward_ratio = take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 0
            
            print(f'    {symbol}:')
            print(f'      - Strategy: {strategy}')
            print(f'      - Side: {side}')
            print(f'      - Amount: {amount}')
            print(f'      - Entry Price: {entry_price}')
            print(f'      - Current Price: {current_price}')
            print(f'      - Position Value: {position_value:.2f} USDT')
            print(f'      - Unrealized PnL: {unrealized_pnl:+.2f} USDT ({(unrealized_pnl/position_value*100):+.2f}%)')
            print(f'      - Stop Loss: {stop_loss_pct*100:.1f}% @ {sl_price:.6f}')
            print(f'      - Take Profit: {take_profit_pct*100:.1f}% @ {tp_price:.6f}')
            print(f'      - Distance to SL: {distance_to_sl_pct:+.2f}%')
            print(f'      - Distance to TP: {distance_to_tp_pct:+.2f}%')
            print(f'      - Risk/Reward Ratio: 1:{risk_reward_ratio:.1f}')
            
            # Check if TP or SL is triggered
            if side == 'LONG':
                if current_float <= sl_price:
                    print(f'      - STATUS: STOP LOSS TRIGGERED!')
                elif current_float >= tp_price:
                    print(f'      - STATUS: TAKE PROFIT TRIGGERED!')
                else:
                    print(f'      - STATUS: ACTIVE')
            else:  # SHORT
                if current_float >= sl_price:
                    print(f'      - STATUS: STOP LOSS TRIGGERED!')
                elif current_float <= tp_price:
                    print(f'      - STATUS: TAKE PROFIT TRIGGERED!')
                else:
                    print(f'      - STATUS: ACTIVE')
            
            print()
        
        print(f'  - Portfolio Summary:')
        print(f'    - Total Position Value: {total_position_value:.2f} USDT')
        print(f'    - Total Unrealized PnL: {total_unrealized_pnl:+.2f} USDT ({(total_unrealized_pnl/total_position_value*100):+.2f}%)')
    
    # 2. Pending Trades TP/SL Analysis
    print('\n[2. PENDING TRADES TP/SL ANALYSIS]')
    
    pending_trades = results.get('pending_trades', [])
    
    if not pending_trades:
        print('  - No pending trades found')
    else:
        print(f'  - Total Pending Trades: {len(pending_trades)}')
        print(f'  - Pending Trades TP/SL Settings:')
        
        for i, trade in enumerate(pending_trades, 1):
            symbol = trade.get('symbol', 'Unknown')
            side = trade.get('side', 'Unknown')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            strategy = trade.get('strategy', 'Unknown')
            confidence = trade.get('signal_confidence', 0)
            
            # Get strategy config for TP/SL
            try:
                from core.strategy_registry import StrategyRegistry
                sr = StrategyRegistry()
                strategy_config = sr.get_strategy_profile(strategy)
                
                if strategy_config:
                    risk_config = strategy_config.get('risk_config', {})
                    stop_loss_pct = risk_config.get('stop_loss_pct', 0.03)
                    take_profit_pct = risk_config.get('take_profit_pct', 0.045)
                else:
                    stop_loss_pct = 0.03
                    take_profit_pct = 0.045
                    
            except:
                stop_loss_pct = 0.03
                take_profit_pct = 0.045
            
            # Calculate TP/SL prices
            try:
                price_float = float(price)
                quantity_float = float(quantity)
                
                if side == 'BUY':  # LONG position
                    sl_price = price_float * (1 - stop_loss_pct)
                    tp_price = price_float * (1 + take_profit_pct)
                else:  # SHORT position
                    sl_price = price_float * (1 + stop_loss_pct)
                    tp_price = price_float * (1 - take_profit_pct)
                
                position_value = price_float * quantity_float
                
            except (ValueError, TypeError):
                sl_price = 0
                tp_price = 0
                position_value = 0
            
            # Risk/Reward ratio
            risk_reward_ratio = take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 0
            
            print(f'    {i}. {symbol}:')
            print(f'      - Strategy: {strategy}')
            print(f'      - Side: {side}')
            print(f'      - Quantity: {quantity}')
            print(f'      - Entry Price: {price}')
            print(f'      - Position Value: {position_value:.2f} USDT')
            print(f'      - Signal Confidence: {confidence:.2f}')
            print(f'      - Planned Stop Loss: {stop_loss_pct*100:.1f}% @ {sl_price:.6f}')
            print(f'      - Planned Take Profit: {take_profit_pct*100:.1f}% @ {tp_price:.6f}')
            print(f'      - Risk/Reward Ratio: 1:{risk_reward_ratio:.1f}')
            print()
    
    # 3. Strategy Configuration TP/SL Analysis
    print('\n[3. STRATEGY CONFIGURATION TP/SL ANALYSIS]')
    
    try:
        from core.strategy_registry import StrategyRegistry
        
        sr = StrategyRegistry()
        
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        print(f'  - Strategy TP/SL Configurations:')
        
        for strategy_name in strategies:
            strategy_config = sr.get_strategy_profile(strategy_name)
            
            if strategy_config:
                risk_config = strategy_config.get('risk_config', {})
                
                stop_loss_pct = risk_config.get('stop_loss_pct', 0)
                take_profit_pct = risk_config.get('take_profit_pct', 0)
                max_position_size = risk_config.get('max_position_size_usdt', 0)
                leverage = risk_config.get('leverage', 1)
                
                # Session multipliers
                session_multipliers = risk_config.get('session_multipliers', {})
                
                # Partial TP settings
                partial_tp1_pct = risk_config.get('partial_tp1_pct', 0)
                partial_tp2_pct = risk_config.get('partial_tp2_pct', 0)
                fast_tp1_pct = risk_config.get('fast_tp1_pct', 0)
                fast_tp2_pct = risk_config.get('fast_tp2_pct', 0)
                
                print(f'    - {strategy_name.upper()}:')
                print(f'      - Stop Loss: {stop_loss_pct*100:.1f}%')
                print(f'      - Take Profit: {take_profit_pct*100:.1f}%')
                print(f'      - Risk/Reward: 1:{(take_profit_pct/stop_loss_pct):.1f}' if stop_loss_pct > 0 else '      - Risk/Reward: N/A')
                print(f'      - Max Position Size: {max_position_size} USDT')
                print(f'      - Leverage: {leverage}x')
                print(f'      - Partial TP1: {partial_tp1_pct*100:.1f}%')
                print(f'      - Partial TP2: {partial_tp2_pct*100:.1f}%')
                print(f'      - Fast TP1: {fast_tp1_pct*100:.1f}%')
                print(f'      - Fast TP2: {fast_tp2_pct*100:.1f}%')
                
                if session_multipliers:
                    print(f'      - Session Multipliers:')
                    for session, multipliers in session_multipliers.items():
                        stop_mult = multipliers.get('stop', 1.0)
                        take_mult = multipliers.get('take', 1.0)
                        print(f'        - {session}: SL x{stop_mult}, TP x{take_mult}')
                
                print()
        
    except Exception as e:
        print(f'  - Error analyzing strategy configurations: {e}')
    
    # 4. Risk Assessment
    print('\n[4. RISK ASSESSMENT]')
    
    if active_positions:
        print(f'  - Current Risk Exposure:')
        
        total_risk = 0
        positions_at_risk = 0
        
        for symbol, position in active_positions.items():
            try:
                entry_price = float(position.get('entry_price', 0))
                current_price = float(position.get('current_price', 0))
                amount = float(position.get('amount', 0))
                stop_loss_pct = position.get('stop_loss_pct', 0)
                side = position.get('side', 'LONG')
                
                # Calculate potential loss
                if side == 'LONG':
                    sl_price = entry_price * (1 - stop_loss_pct)
                    potential_loss = (entry_price - sl_price) * amount
                else:
                    sl_price = entry_price * (1 + stop_loss_pct)
                    potential_loss = (sl_price - entry_price) * amount
                
                total_risk += potential_loss
                
                # Check if position is close to stop loss
                if side == 'LONG':
                    distance_to_sl = (current_price - sl_price) / entry_price
                else:
                    distance_to_sl = (sl_price - current_price) / entry_price
                
                if distance_to_sl < 0.01:  # Within 1% of stop loss
                    positions_at_risk += 1
                
            except (ValueError, TypeError):
                continue
        
        print(f'    - Total Risk Exposure: {total_risk:.2f} USDT')
        print(f'    - Positions Near Stop Loss: {positions_at_risk}/{len(active_positions)}')
        
        # Risk as percentage of total portfolio
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            initial_equity = config.get('trading', {}).get('initial_equity', 10000)
            risk_percentage = (total_risk / initial_equity) * 100
            
            print(f'    - Risk as % of Portfolio: {risk_percentage:.2f}%')
            
            if risk_percentage > 10:
                print(f'    - Risk Level: HIGH')
            elif risk_percentage > 5:
                print(f'    - Risk Level: MEDIUM')
            else:
                print(f'    - Risk Level: LOW')
                
        except Exception as e:
            print(f'    - Could not calculate risk percentage: {e}')
    
    # 5. Recommendations
    print('\n[5. RECOMMENDATIONS]')
    
    recommendations = []
    
    if active_positions:
        # Check for positions near stop loss
        positions_near_sl = 0
        for symbol, position in active_positions.items():
            try:
                entry_price = float(position.get('entry_price', 0))
                current_price = float(position.get('current_price', 0))
                stop_loss_pct = position.get('stop_loss_pct', 0)
                side = position.get('side', 'LONG')
                
                if side == 'LONG':
                    sl_price = entry_price * (1 - stop_loss_pct)
                    distance_to_sl = (current_price - sl_price) / entry_price
                else:
                    sl_price = entry_price * (1 + stop_loss_pct)
                    distance_to_sl = (sl_price - current_price) / entry_price
                
                if distance_to_sl < 0.01:  # Within 1% of stop loss
                    positions_near_sl += 1
                    
            except (ValueError, TypeError):
                continue
        
        if positions_near_sl > 0:
            recommendations.append(f'Monitor {positions_near_sl} positions near stop loss')
        
        # Check for consistent TP/SL ratios
        tp_sl_ratios = []
        for symbol, position in active_positions.items():
            stop_loss_pct = position.get('stop_loss_pct', 0)
            take_profit_pct = position.get('take_profit_pct', 0)
            
            if stop_loss_pct > 0:
                ratio = take_profit_pct / stop_loss_pct
                tp_sl_ratios.append(ratio)
        
        if tp_sl_ratios:
            avg_ratio = sum(tp_sl_ratios) / len(tp_sl_ratios)
            if avg_ratio < 1.5:
                recommendations.append('Consider increasing take profit for better risk/reward')
            elif avg_ratio > 3:
                recommendations.append('Consider reducing take profit for more realistic targets')
    
    # Check pending trades
    if pending_trades:
        recommendations.append('Monitor pending trades for execution and TP/SL setup')
    
    # General recommendations
    recommendations.append('Continue monitoring all positions for TP/SL triggers')
    recommendations.append('Review strategy TP/SL settings for optimization')
    
    for i, rec in enumerate(recommendations, 1):
        print(f'  {i}. {rec}')
    
    print('\n' + '=' * 80)
    print('[TP/SL ANALYSIS COMPLETE]')
    print('=' * 80)

if __name__ == "__main__":
    check_tp_sl_settings()
