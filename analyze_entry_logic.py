#!/usr/bin/env python3
"""
Analyze Entry Logic - Precise analysis of entry logic
"""

import json
from datetime import datetime

def analyze_entry_logic():
    """Precise analysis of entry logic"""
    print('=' * 80)
    print('ENTRY LOGIC PRECISE ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Strategy Registry Entry Logic Analysis
    print('\n[1. STRATEGY REGISTRY ENTRY LOGIC]')
    
    try:
        from core.strategy_registry import StrategyRegistry
        
        sr = StrategyRegistry()
        
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        print(f'  - Strategy Entry Logic Analysis:')
        
        for strategy_name in strategies:
            strategy_config = sr.get_strategy_profile(strategy_name)
            
            if strategy_config:
                print(f'\n    {strategy_name.upper()} Strategy:')
                
                # Entry filters
                entry_filters = strategy_config.get('entry_filters', {})
                min_confidence = entry_filters.get('min_confidence', 0)
                min_trend_strength = entry_filters.get('min_trend_strength', 0)
                max_volatility = entry_filters.get('max_volatility', 1.0)
                required_alignment_count = entry_filters.get('required_alignment_count', 0)
                consensus_threshold = entry_filters.get('consensus_threshold', 0)
                
                print(f'      - Entry Filters:')
                print(f'        * Min Confidence: {min_confidence}')
                print(f'        * Min Trend Strength: {min_trend_strength}')
                print(f'        * Max Volatility: {max_volatility}')
                print(f'        * Required Alignment Count: {required_alignment_count}')
                print(f'        * Consensus Threshold: {consensus_threshold}')
                
                # Fast entry filters
                fast_entry_min_quality = entry_filters.get('fast_entry_min_quality_score', 0)
                fast_entry_consensus = entry_filters.get('fast_entry_consensus_relief', 0)
                fast_entry_min_trend = entry_filters.get('fast_entry_min_trend_consensus_abs', 0)
                
                print(f'      - Fast Entry Filters:')
                print(f'        * Min Quality Score: {fast_entry_min_quality}')
                print(f'        * Consensus Relief: {fast_entry_consensus}')
                print(f'        * Min Trend Consensus: {fast_entry_min_trend}')
                
                # Symbol selection
                symbol_selection = strategy_config.get('symbol_selection', {})
                candidate_limit = symbol_selection.get('candidate_limit', 0)
                symbol_mode = symbol_selection.get('symbol_mode', 'unknown')
                market_bias = symbol_selection.get('market_bias', 'unknown')
                
                print(f'      - Symbol Selection:')
                print(f'        * Candidate Limit: {candidate_limit}')
                print(f'        * Symbol Mode: {symbol_mode}')
                print(f'        * Market Bias: {market_bias}')
                
                # Risk config
                risk_config = strategy_config.get('risk_config', {})
                stop_loss_pct = risk_config.get('stop_loss_pct', 0)
                take_profit_pct = risk_config.get('take_profit_pct', 0)
                max_position_size = risk_config.get('max_position_size_usdt', 0)
                leverage = risk_config.get('leverage', 1)
                
                print(f'      - Risk Configuration:')
                print(f'        * Stop Loss: {stop_loss_pct * 100:.1f}%')
                print(f'        * Take Profit: {take_profit_pct * 100:.1f}%')
                print(f'        * Max Position Size: {max_position_size} USDT')
                print(f'        * Leverage: {leverage}x')
                
            else:
                print(f'    - {strategy_name}: Configuration not found')
    
    except Exception as e:
        print(f'  - Error analyzing strategy registry: {e}')
    
    # 2. Signal Engine Entry Logic Analysis
    print('\n[2. SIGNAL ENGINE ENTRY LOGIC]')
    
    try:
        from core.signal_engine import SignalEngine
        
        se = SignalEngine()
        
        print(f'  - Signal Engine Entry Logic:')
        
        # Check the generate_strategy_signal method
        import inspect
        sig_source = inspect.getsource(se.generate_strategy_signal)
        
        print(f'  - Entry Signal Generation Process:')
        
        # Analyze the signal generation logic
        if 'generate_strategy_signal' in sig_source:
            print(f'    - Method: generate_strategy_signal')
            print(f'    - Parameters: market_data, indicators, regime, strategy_config')
            
            # Check for V2 merged logic
            if 'V2' in sig_source or 'merged' in sig_source.lower():
                print(f'    - Logic Type: V2 Merged')
                
                # Look for specific conditions
                if 'bullish_alignment_count' in sig_source:
                    print(f'    - Uses: Bullish alignment count')
                
                if 'consensus_threshold' in sig_source:
                    print(f'    - Uses: Consensus threshold')
                
                if 'volume_ready' in sig_source:
                    print(f'    - Uses: Volume conditions')
                
                if 'fractal' in sig_source.lower():
                    print(f'    - Uses: Fractal analysis')
                
                if 'heikin' in sig_source.lower():
                    print(f'    - Uses: Heikin Ashi')
                
                if 'ema' in sig_source.lower():
                    print(f'    - Uses: EMA analysis')
                
                # Check for specific conditions
                conditions = []
                if 'price_vs_ma' in sig_source:
                    conditions.append('Price vs MA')
                if 'ema_fast > ema_mid' in sig_source:
                    conditions.append('EMA Fast > Mid')
                if 'bullish_ha_ready' in sig_source:
                    conditions.append('Bullish Heikin Ashi')
                if 'bullish_cross_ready' in sig_source:
                    conditions.append('Bullish Cross')
                if 'volume_ready' in sig_source:
                    conditions.append('Volume Ready')
                if 'bullish_fractal_trigger' in sig_source:
                    conditions.append('Bullish Fractal')
                
                if conditions:
                    print(f'    - Entry Conditions:')
                    for condition in conditions:
                        print(f'      * {condition}')
                
                # Check for AND logic
                if 'and' in sig_source and 'all(' in sig_source:
                    print(f'    - Logic: AND (All conditions must be met)')
                elif 'or' in sig_source:
                    print(f'    - Logic: OR (Any condition can be met)')
                else:
                    print(f'    - Logic: Mixed/Complex')
                
                # Check for minimum requirements
                if 'required_alignment_count' in sig_source:
                    print(f'    - Minimum Alignment: Required count check')
                
                if 'consensus_threshold' in sig_source:
                    print(f'    - Consensus Threshold: Minimum consensus required')
                
            else:
                print(f'    - Logic Type: Standard/Simple')
        
        else:
            print(f'    - Signal generation method not found')
    
    except Exception as e:
        print(f'  - Error analyzing signal engine: {e}')
    
    # 3. Trade Orchestrator Entry Logic Analysis
    print('\n[3. TRADE ORCHESTRATOR ENTRY LOGIC]')
    
    try:
        from core.trade_orchestrator import TradeOrchestrator
        
        # Check the execute_strategy_trade method
        import inspect
        to_source = inspect.getsource(TradeOrchestrator.execute_strategy_trade)
        
        print(f'  - Trade Execution Entry Logic:')
        
        # Analyze the execution logic
        if 'execute_strategy_trade' in to_source:
            print(f'    - Method: execute_strategy_trade')
            print(f'    - Entry Validation Process:')
            
            # Check for duplicate prevention
            if '_check_duplicate_entry' in to_source:
                print(f'      * Duplicate Entry Prevention: ENABLED')
            else:
                print(f'      * Duplicate Entry Prevention: DISABLED')
            
            # Check for strategy configuration validation
            if 'strategy_config' in to_source:
                print(f'      * Strategy Configuration Validation: ENABLED')
            
            # Check for signal generation
            if 'generate_strategy_signal' in to_source:
                print(f'      * Signal Generation: ENABLED')
            
            # Check for confidence filtering
            if 'confidence' in to_source and 'min_confidence' in to_source:
                print(f'      * Confidence Filtering: ENABLED')
            
            # Check for position limits
            if 'can_open_new_positions' in to_source:
                print(f'      * Position Limits Check: ENABLED')
            
            # Check for account service validation
            if 'account_service' in to_source:
                print(f'      * Account Service Validation: ENABLED')
            
            # Check for order execution
            if 'execute_order' in to_source or 'place_order' in to_source:
                print(f'      * Order Execution: ENABLED')
            
            # Check for protective orders
            if 'protective_order_manager' in to_source:
                print(f'      * Protective Orders: ENABLED')
            
            # Check for partial take profit
            if 'partial_take_profit_manager' in to_source:
                print(f'      * Partial Take Profit: ENABLED')
        
        else:
            print(f'    - Execute method not found')
    
    except Exception as e:
        print(f'  - Error analyzing trade orchestrator: {e}')
    
    # 4. Current Entry Logic Performance Analysis
    print('\n[4. CURRENT ENTRY LOGIC PERFORMANCE]')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Check recent activity
        last_cycle = results.get('last_cycle', {})
        
        if last_cycle:
            signals_generated = last_cycle.get('signals_generated', 0)
            trades_executed = last_cycle.get('trades_executed', 0)
            
            print(f'  - Recent Performance:')
            print(f'    - Signals Generated: {signals_generated}')
            print(f'    - Trades Executed: {trades_executed}')
            
            if signals_generated > 0:
                execution_rate = (trades_executed / signals_generated) * 100
                print(f'    - Execution Rate: {execution_rate:.1f}%')
            else:
                print(f'    - Execution Rate: N/A (no signals)')
        
        # Check active positions
        active_positions = results.get('active_positions', {})
        
        print(f'  - Active Positions Analysis:')
        print(f'    - Total Active Positions: {len(active_positions)}')
        
        if active_positions:
            strategy_performance = {}
            
            for symbol, position in active_positions.items():
                strategy = position.get('strategy', 'Unknown')
                entry_price = position.get('entry_price', 0)
                current_price = position.get('current_price', 0)
                amount = position.get('amount', 0)
                
                # Calculate PnL
                try:
                    entry_float = float(entry_price)
                    current_float = float(current_price)
                    amount_float = float(amount)
                    
                    pnl = (current_float - entry_float) * amount_float
                    pnl_pct = ((current_float - entry_float) / entry_float) * 100
                    
                    if strategy not in strategy_performance:
                        strategy_performance[strategy] = {
                            'positions': 0,
                            'total_pnl': 0,
                            'total_value': 0
                        }
                    
                    strategy_performance[strategy]['positions'] += 1
                    strategy_performance[strategy]['total_pnl'] += pnl
                    strategy_performance[strategy]['total_value'] += entry_float * amount_float
                    
                except (ValueError, TypeError):
                    continue
            
            print(f'    - Strategy Performance:')
            for strategy, perf in strategy_performance.items():
                if perf['positions'] > 0:
                    avg_pnl_pct = (perf['total_pnl'] / perf['total_value']) * 100
                    print(f'      * {strategy}: {perf["positions"]} positions, PnL: {avg_pnl_pct:+.2f}%')
        
        # Check pending trades
        pending_trades = results.get('pending_trades', [])
        
        print(f'  - Pending Trades Analysis:')
        print(f'    - Total Pending Trades: {len(pending_trades)}')
        
        if pending_trades:
            pending_strategies = {}
            
            for trade in pending_trades:
                strategy = trade.get('strategy', 'Unknown')
                confidence = trade.get('signal_confidence', 0)
                
                if strategy not in pending_strategies:
                    pending_strategies[strategy] = {
                        'count': 0,
                        'total_confidence': 0
                    }
                
                pending_strategies[strategy]['count'] += 1
                pending_strategies[strategy]['total_confidence'] += confidence
            
            print(f'    - Pending Strategy Analysis:')
            for strategy, pending in pending_strategies.items():
                avg_confidence = pending['total_confidence'] / pending['count']
                print(f'      * {strategy}: {pending["count"]} trades, Avg Confidence: {avg_confidence:.2f}')
    
    except Exception as e:
        print(f'  - Error analyzing performance: {e}')
    
    # 5. Entry Logic Issues Identification
    print('\n[5. ENTRY LOGIC ISSUES IDENTIFICATION]')
    
    issues = []
    
    # Check for signal generation issues
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        last_cycle = results.get('last_cycle', {})
        signals_generated = last_cycle.get('signals_generated', 0)
        
        if signals_generated == 0:
            issues.append("No signals generated in last cycle")
        
        # Check for execution issues
        trades_executed = last_cycle.get('trades_executed', 0)
        
        if signals_generated > 0 and trades_executed == 0:
            issues.append("Signals generated but no trades executed")
        
        # Check for strategy configuration issues
        try:
            from core.strategy_registry import StrategyRegistry
            sr = StrategyRegistry()
            
            for strategy_name in ['ma_trend_follow', 'ema_crossover']:
                strategy_config = sr.get_strategy_profile(strategy_name)
                
                if strategy_config:
                    entry_filters = strategy_config.get('entry_filters', {})
                    min_confidence = entry_filters.get('min_confidence', 0)
                    min_trend_strength = entry_filters.get('min_trend_strength', 0)
                    
                    if min_confidence > 0.8:
                        issues.append(f"{strategy_name}: Very high confidence threshold ({min_confidence})")
                    
                    if min_trend_strength > 25:
                        issues.append(f"{strategy_name}: Very high trend strength requirement ({min_trend_strength})")
                else:
                    issues.append(f"{strategy_name}: Strategy configuration not found")
        
        except Exception as e:
            issues.append(f"Strategy registry error: {e}")
        
        # Check for market data issues
        market_data = results.get('market_data', {})
        
        if not market_data:
            issues.append("No market data available")
        elif len(market_data) < 10:
            issues.append("Limited market data available")
        
        # Check for regime analysis issues
        regime_distribution = results.get('regime_distribution', {})
        
        if not regime_distribution:
            issues.append("No regime analysis performed")
        
    except Exception as e:
        issues.append(f"Error checking issues: {e}")
    
    if issues:
        print(f'  - Identified Issues:')
        for i, issue in enumerate(issues, 1):
            print(f'    {i}. {issue}')
    else:
        print(f'  - No critical issues identified')
    
    # 6. Entry Logic Optimization Recommendations
    print('\n[6. ENTRY LOGIC OPTIMIZATION RECOMMENDATIONS]')
    
    recommendations = []
    
    # Based on issues identified
    if "No signals generated in last cycle" in issues:
        recommendations.append("Lower confidence thresholds to generate more signals")
        recommendations.append("Review market data quality and availability")
        recommendations.append("Check if entry conditions are too strict")
    
    if "Signals generated but no trades executed" in issues:
        recommendations.append("Check trade execution logic")
        recommendations.append("Verify position limits and account balance")
        recommendations.append("Review order execution process")
    
    if "No regime analysis performed" in issues:
        recommendations.append("Implement regime analysis in trading cycle")
        recommendations.append("Add market regime data to signal generation")
    
    # General recommendations
    recommendations.append("Monitor entry logic performance regularly")
    recommendations.append("Test entry conditions with different market scenarios")
    recommendations.append("Consider adaptive entry thresholds based on market conditions")
    recommendations.append("Implement entry logic backtesting for optimization")
    
    for i, rec in enumerate(recommendations, 1):
        print(f'  {i}. {rec}')
    
    print('\n' + '=' * 80)
    print('[ENTRY LOGIC ANALYSIS COMPLETE]')
    print('=' * 80)

if __name__ == "__main__":
    analyze_entry_logic()
