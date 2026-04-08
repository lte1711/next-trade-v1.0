#!/usr/bin/env python3
"""
TP/SL Monitoring Dashboard - Real-time TP/SL monitoring dashboard
"""

import json
from datetime import datetime

def tp_sl_monitoring_dashboard():
    """Real-time TP/SL monitoring dashboard"""
    print('=' * 80)
    print('TP/SL MONITORING DASHBOARD')
    print('=' * 80)
    
    print(f'Dashboard Update: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # 1. Active Positions Monitoring
    print('\n[ACTIVE POSITIONS MONITORING]')
    
    active_positions = results.get('active_positions', {})
    
    if not active_positions:
        print('  - No active positions')
    else:
        print(f'  - Monitoring {len(active_positions)} active positions:')
        
        for symbol, position in active_positions.items():
            # Extract position data
            entry_price = float(position.get('entry_price', 0))
            current_price = float(position.get('current_price', 0))
            amount = float(position.get('amount', 0))
            side = position.get('side', 'LONG')
            strategy = position.get('strategy', 'Unknown')
            
            # TP/SL settings
            stop_loss_pct = position.get('stop_loss_pct', 0)
            take_profit_pct = position.get('take_profit_pct', 0)
            
            # Calculate TP/SL prices
            if side == 'LONG':
                sl_price = entry_price * (1 - stop_loss_pct)
                tp_price = entry_price * (1 + take_profit_pct)
                
                # Distance percentages
                distance_to_sl_pct = ((current_price - sl_price) / entry_price) * 100
                distance_to_tp_pct = ((tp_price - current_price) / entry_price) * 100
                
                # Progress to TP/SL
                progress_to_sl = max(0, min(100, (1 - distance_to_sl_pct / 100) * 100))
                progress_to_tp = max(0, min(100, (distance_to_tp_pct / 100) * 100))
                
            else:  # SHORT
                sl_price = entry_price * (1 + stop_loss_pct)
                tp_price = entry_price * (1 - take_profit_pct)
                
                distance_to_sl_pct = ((sl_price - current_price) / entry_price) * 100
                distance_to_tp_pct = ((current_price - tp_price) / entry_price) * 100
                
                progress_to_sl = max(0, min(100, (1 - distance_to_sl_pct / 100) * 100))
                progress_to_tp = max(0, min(100, (distance_to_tp_pct / 100) * 100))
            
            # PnL calculation
            if side == 'LONG':
                pnl = (current_price - entry_price) * amount
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl = (entry_price - current_price) * amount
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Position value
            position_value = entry_price * amount
            
            # Alert levels
            alert_level = 'NORMAL'
            if distance_to_sl_pct < 1:
                alert_level = 'CRITICAL'
            elif distance_to_sl_pct < 2:
                alert_level = 'WARNING'
            elif distance_to_tp_pct < 1:
                alert_level = 'TP_NEAR'
            
            print(f'  {symbol}:')
            print(f'    - Strategy: {strategy} | Side: {side}')
            print(f'    - Entry: {entry_price:.6f} | Current: {current_price:.6f}')
            print(f'    - PnL: {pnl:+.2f} USDT ({pnl_pct:+.2f}%) | Value: {position_value:.2f} USDT')
            print(f'    - SL: {sl_price:.6f} ({distance_to_sl_pct:+.2f}%) | TP: {tp_price:.6f} ({distance_to_tp_pct:+.2f}%)')
            print(f'    - Progress: SL {progress_to_sl:.1f}% | TP {progress_to_tp:.1f}%')
            print(f'    - Alert: {alert_level}')
            
            # Visual progress bar
            sl_bar = '[' + '!' * int(progress_to_sl/5) + '-' * (20 - int(progress_to_sl/5)) + ']'
            tp_bar = '[' + '!' * int(progress_to_tp/5) + '-' * (20 - int(progress_to_tp/5)) + ']'
            print(f'    - SL Progress: {sl_bar}')
            print(f'    - TP Progress: {tp_bar}')
            print()
    
    # 2. Pending Trades Monitoring
    print('\n[PENDING TRADES MONITORING]')
    
    pending_trades = results.get('pending_trades', [])
    
    if not pending_trades:
        print('  - No pending trades')
    else:
        print(f'  - Monitoring {len(pending_trades)} pending trades:')
        
        for i, trade in enumerate(pending_trades, 1):
            symbol = trade.get('symbol', 'Unknown')
            side = trade.get('side', 'Unknown')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            strategy = trade.get('strategy', 'Unknown')
            confidence = trade.get('signal_confidence', 0)
            
            # Get strategy TP/SL
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
            price_float = float(price)
            if side == 'BUY':  # LONG
                sl_price = price_float * (1 - stop_loss_pct)
                tp_price = price_float * (1 + take_profit_pct)
            else:  # SHORT
                sl_price = price_float * (1 + stop_loss_pct)
                tp_price = price_float * (1 - take_profit_pct)
            
            position_value = price_float * float(quantity)
            
            print(f'  {i}. {symbol}:')
            print(f'    - Strategy: {strategy} | Side: {side}')
            print(f'    - Entry: {price:.6f} | Quantity: {quantity:.6f}')
            print(f'    - Value: {position_value:.2f} USDT | Confidence: {confidence:.2f}')
            print(f'    - Planned SL: {sl_price:.6f} ({stop_loss_pct*100:.1f}%)')
            print(f'    - Planned TP: {tp_price:.6f} ({take_profit_pct*100:.1f}%)')
            print(f'    - Status: PENDING EXECUTION')
            print()
    
    # 3. Risk Overview
    print('\n[RISK OVERVIEW]')
    
    if active_positions:
        total_position_value = 0
        total_unrealized_pnl = 0
        total_risk = 0
        
        positions_near_sl = 0
        positions_near_tp = 0
        
        for symbol, position in active_positions.items():
            try:
                entry_price = float(position.get('entry_price', 0))
                current_price = float(position.get('current_price', 0))
                amount = float(position.get('amount', 0))
                stop_loss_pct = position.get('stop_loss_pct', 0)
                take_profit_pct = position.get('take_profit_pct', 0)
                side = position.get('side', 'LONG')
                
                # Position value
                position_value = entry_price * amount
                total_position_value += position_value
                
                # Unrealized PnL
                if side == 'LONG':
                    pnl = (current_price - entry_price) * amount
                    sl_price = entry_price * (1 - stop_loss_pct)
                    tp_price = entry_price * (1 + take_profit_pct)
                    
                    distance_to_sl = (current_price - sl_price) / entry_price
                    distance_to_tp = (tp_price - current_price) / entry_price
                else:
                    pnl = (entry_price - current_price) * amount
                    sl_price = entry_price * (1 + stop_loss_pct)
                    tp_price = entry_price * (1 - take_profit_pct)
                    
                    distance_to_sl = (sl_price - current_price) / entry_price
                    distance_to_tp = (current_price - tp_price) / entry_price
                
                total_unrealized_pnl += pnl
                
                # Potential loss
                potential_loss = (entry_price - sl_price) * amount if side == 'LONG' else (sl_price - entry_price) * amount
                total_risk += potential_loss
                
                # Check proximity to TP/SL
                if distance_to_sl < 0.01:  # Within 1%
                    positions_near_sl += 1
                if distance_to_tp < 0.01:  # Within 1%
                    positions_near_tp += 1
                    
            except (ValueError, TypeError):
                continue
        
        print(f'  - Portfolio Summary:')
        print(f'    - Total Position Value: {total_position_value:.2f} USDT')
        print(f'    - Total Unrealized PnL: {total_unrealized_pnl:+.2f} USDT ({(total_unrealized_pnl/total_position_value*100):+.2f}%)')
        print(f'    - Total Risk Exposure: {total_risk:.2f} USDT')
        print(f'    - Risk as % of Portfolio: {(total_risk/total_position_value*100):.2f}%')
        
        print(f'  - Alert Summary:')
        print(f'    - Positions Near SL: {positions_near_sl}/{len(active_positions)}')
        print(f'    - Positions Near TP: {positions_near_tp}/{len(active_positions)}')
        
        # Risk level
        risk_percentage = (total_risk / total_position_value) * 100
        if risk_percentage > 10:
            risk_level = 'HIGH'
            risk_color = 'RED'
        elif risk_percentage > 5:
            risk_level = 'MEDIUM'
            risk_color = 'YELLOW'
        else:
            risk_level = 'LOW'
            risk_color = 'GREEN'
        
        print(f'    - Risk Level: {risk_level} ({risk_percentage:.2f}%)')
    
    # 4. Strategy Performance
    print('\n[STRATEGY PERFORMANCE]')
    
    strategy_stats = {}
    
    # Collect active positions by strategy
    for symbol, position in active_positions.items():
        strategy = position.get('strategy', 'Unknown')
        
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {
                'positions': 0,
                'total_value': 0,
                'total_pnl': 0,
                'avg_rr_ratio': 0
            }
        
        try:
            entry_price = float(position.get('entry_price', 0))
            current_price = float(position.get('current_price', 0))
            amount = float(position.get('amount', 0))
            stop_loss_pct = position.get('stop_loss_pct', 0)
            take_profit_pct = position.get('take_profit_pct', 0)
            
            strategy_stats[strategy]['positions'] += 1
            strategy_stats[strategy]['total_value'] += entry_price * amount
            
            if position.get('side', 'LONG') == 'LONG':
                pnl = (current_price - entry_price) * amount
            else:
                pnl = (entry_price - current_price) * amount
            
            strategy_stats[strategy]['total_pnl'] += pnl
            
            if stop_loss_pct > 0:
                rr_ratio = take_profit_pct / stop_loss_pct
                strategy_stats[strategy]['avg_rr_ratio'] += rr_ratio
                
        except (ValueError, TypeError):
            continue
    
    # Display strategy stats
    for strategy, stats in strategy_stats.items():
        if stats['positions'] > 0:
            avg_rr = stats['avg_rr_ratio'] / stats['positions']
            pnl_pct = (stats['total_pnl'] / stats['total_value']) * 100
            
            print(f'  - {strategy}:')
            print(f'    - Positions: {stats["positions"]}')
            print(f'    - Total Value: {stats["total_value"]:.2f} USDT')
            print(f'    - Total PnL: {stats["total_pnl"]:+.2f} USDT ({pnl_pct:+.2f}%)')
            print(f'    - Avg Risk/Reward: 1:{avg_rr:.1f}')
            print()
    
    # 5. Market Conditions Impact
    print('\n[MARKET CONDITIONS IMPACT]')
    
    regime_distribution = results.get('regime_distribution', {})
    
    if regime_distribution:
        print(f'  - Current Market Regime: {regime_distribution}')
        
        # Analyze regime impact on TP/SL
        total_positions = len(active_positions)
        if total_positions > 0:
            print(f'  - Regime Impact Analysis:')
            
            if 'RANGING' in regime_distribution and regime_distribution['RANGING'] > 0:
                ranging_percentage = (regime_distribution['RANGING'] / sum(regime_distribution.values())) * 100
                print(f'    - Ranging Market: {ranging_percentage:.1f}% - May increase SL triggers')
            
            if 'BULL_TREND' in regime_distribution and regime_distribution['BULL_TREND'] > 0:
                bull_percentage = (regime_distribution['BULL_TREND'] / sum(regime_distribution.values())) * 100
                print(f'    - Bull Trend: {bull_percentage:.1f}% - Favorable for LONG positions')
            
            if 'BEAR_TREND' in regime_distribution and regime_distribution['BEAR_TREND'] > 0:
                bear_percentage = (regime_distribution['BEAR_TREND'] / sum(regime_distribution.values())) * 100
                print(f'    - Bear Trend: {bear_percentage:.1f}% - Risk for LONG positions')
    else:
        print('  - Market regime data not available')
    
    # 6. Recommendations
    print('\n[REAL-TIME RECOMMENDATIONS]')
    
    recommendations = []
    
    # Check for immediate actions
    if active_positions:
        positions_near_sl = 0
        positions_near_tp = 0
        
        for symbol, position in active_positions.items():
            try:
                entry_price = float(position.get('entry_price', 0))
                current_price = float(position.get('current_price', 0))
                stop_loss_pct = position.get('stop_loss_pct', 0)
                take_profit_pct = position.get('take_profit_pct', 0)
                side = position.get('side', 'LONG')
                
                if side == 'LONG':
                    sl_price = entry_price * (1 - stop_loss_pct)
                    tp_price = entry_price * (1 + take_profit_pct)
                    
                    distance_to_sl = (current_price - sl_price) / entry_price
                    distance_to_tp = (tp_price - current_price) / entry_price
                else:
                    sl_price = entry_price * (1 + stop_loss_pct)
                    tp_price = entry_price * (1 - take_profit_pct)
                    
                    distance_to_sl = (sl_price - current_price) / entry_price
                    distance_to_tp = (current_price - tp_price) / entry_price
                
                if distance_to_sl < 0.005:  # Within 0.5%
                    positions_near_sl += 1
                    recommendations.append(f'URGENT: {symbol} within 0.5% of stop loss!')
                
                if distance_to_tp < 0.005:  # Within 0.5%
                    positions_near_tp += 1
                    recommendations.append(f'ALERT: {symbol} within 0.5% of take profit!')
                    
            except (ValueError, TypeError):
                continue
    
    # General recommendations
    if not recommendations:
        recommendations.append('All positions at safe distances from TP/SL')
        recommendations.append('Continue monitoring for price movements')
    
    # Risk management recommendations
    if active_positions:
        total_risk = 0
        for symbol, position in active_positions.items():
            try:
                entry_price = float(position.get('entry_price', 0))
                amount = float(position.get('amount', 0))
                stop_loss_pct = position.get('stop_loss_pct', 0)
                side = position.get('side', 'LONG')
                
                if side == 'LONG':
                    sl_price = entry_price * (1 - stop_loss_pct)
                    potential_loss = (entry_price - sl_price) * amount
                else:
                    sl_price = entry_price * (1 + stop_loss_pct)
                    potential_loss = (sl_price - entry_price) * amount
                
                total_risk += potential_loss
            except (ValueError, TypeError):
                continue
        
        if total_risk > 50:  # If total risk > 50 USDT
            recommendations.append('Consider reducing position sizes to lower risk exposure')
    
    for i, rec in enumerate(recommendations, 1):
        print(f'  {i}. {rec}')
    
    print('\n' + '=' * 80)
    print('[TP/SL DASHBOARD UPDATE COMPLETE]')
    print('=' * 80)
    print(f'Next update: Monitor price movements and TP/SL triggers')
    print('=' * 80)

if __name__ == "__main__":
    tp_sl_monitoring_dashboard()
