#!/usr/bin/env python3
"""
Current Market Logic Analysis - Analyze program's market analysis and execution logic
"""

import json
import os
from datetime import datetime

def analyze_current_market_logic():
    """Analyze current program's market analysis and execution logic"""
    print('=' * 80)
    print('CURRENT MARKET LOGIC ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # 1. Current system configuration
    print('\n[1] CURRENT SYSTEM CONFIGURATION')
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Trading configuration
        trading_config = config.get('trading_config', {})
        print(f'  - Max Open Positions: {trading_config.get("max_open_positions", "N/A")}')
        print(f'  - Fast Entry Enabled: {trading_config.get("fast_entry_enabled", "N/A")}')
        print(f'  - Stop Loss %: {trading_config.get("stop_loss_pct", "N/A")}')
        print(f'  - Take Profit %: {trading_config.get("take_profit_pct", "N/A")}')
        print(f'  - Position Hold Minutes: {trading_config.get("position_hold_minutes", "N/A")}')
        print(f'  - Max Position Size USDT: {trading_config.get("max_position_size_usdt", "N/A")}')
        
        # Mode configuration
        print(f'  - Real Time Mode: {config.get("real_time_mode", "N/A")}')
        print(f'  - Virtual Tests Disabled: {config.get("all_virtual_tests_disabled", "N/A")}')
        print(f'  - Force Real Exchange: {config.get("force_real_exchange", "N/A")}')
        print(f'  - Simulation Mode: {config.get("simulation_mode", "N/A")}')
        
    except Exception as e:
        print(f'  - Error reading config: {e}')
    
    # 2. Current trading results analysis
    print('\n[2] CURRENT TRADING RESULTS ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Active positions
        active_positions = trading_results.get('active_positions', {})
        print(f'  - Active Positions: {len(active_positions)}')
        
        for symbol, position in active_positions.items():
            side = position.get('side', 'Unknown')
            amount = position.get('amount', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            strategy = position.get('strategy', 'Unknown')
            
            print(f'    {symbol}: {side} {abs(amount):.0f} @ {entry_price:.6f}')
            print(f'      Current Price: {current_price:.6f}')
            print(f'      Unrealized PnL: {unrealized_pnl:+.4f}')
            print(f'      Strategy: {strategy}')
        
        # Recent trades
        closed_trades = trading_results.get('closed_trades', [])
        print(f'  - Total Closed Trades: {len(closed_trades)}')
        
        # Recent trades (last 5)
        recent_trades = closed_trades[-5:] if len(closed_trades) >= 5 else closed_trades
        print(f'  - Recent Trades (Last 5):')
        
        for i, trade in enumerate(recent_trades, 1):
            symbol = trade.get('symbol', 'Unknown')
            side = trade.get('side', 'Unknown')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            pnl = trade.get('realized_pnl', 0)
            
            print(f'    {i}. {symbol} {side} {quantity:.0f} @ {price:.6f} (PnL: {pnl:+.4f})')
        
        # System errors
        system_errors = trading_results.get('system_errors', [])
        print(f'  - System Errors: {len(system_errors)}')
        
        if system_errors:
            print(f'  - Recent Errors:')
            for error in system_errors[-3:]:
                error_type = error.get('type', 'Unknown')
                error_message = error.get('message', 'No message')
                timestamp = error.get('timestamp', 'No timestamp')
                print(f'    - {error_type}: {error_message}')
        
    except Exception as e:
        print(f'  - Error reading trading results: {e}')
    
    # 3. Strategy analysis
    print('\n[3] STRATEGY ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        strategies = trading_results.get('strategies', {})
        
        for strategy_name, strategy_config in strategies.items():
            enabled = strategy_config.get('enabled', False)
            name = strategy_config.get('name', 'Unknown')
            
            print(f'  Strategy: {strategy_name}')
            print(f'    - Name: {name}')
            print(f'    - Enabled: {enabled}')
            print(f'    - Stop Loss %: {strategy_config.get("stop_loss_pct", "N/A")}')
            print(f'    - Take Profit %: {strategy_config.get("take_profit_pct", "N/A")}')
            print(f'    - Max Position Size USDT: {strategy_config.get("max_position_size_usdt", "N/A")}')
            
            # Strategy performance
            performance = strategy_config.get('performance', {})
            if performance:
                print(f'    - Win Rate: {performance.get("win_rate", 0):.2%}')
                print(f'    - Avg Return: {performance.get("avg_return", 0):.4f}')
                print(f'    - Total Trades: {performance.get("total_trades", 0)}')
            
            print()
    
    except Exception as e:
        print(f'  - Error analyzing strategies: {e}')
    
    # 4. Market data analysis
    print('\n[4] MARKET DATA ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        market_data = trading_results.get('market_data', {})
        print(f'  - Available Market Data Symbols: {len(market_data)}')
        
        # Show sample market data
        if market_data:
            sample_symbols = list(market_data.keys())[:5]
            print(f'  - Sample Market Data:')
            
            for symbol in sample_symbols:
                data = market_data[symbol]
                price = data.get('price', 0)
                volume = data.get('volume', 0)
                volatility = data.get('volatility', 0)
                
                print(f'    {symbol}: Price ${price:.6f}, Volume {volume:.0f}, Vol {volatility:.4f}')
        
        # Regime distribution
        regime_distribution = trading_results.get('regime_distribution', {})
        if regime_distribution:
            print(f'  - Market Regime Distribution:')
            for regime, count in regime_distribution.items():
                print(f'    {regime}: {count} symbols')
    
    except Exception as e:
        print(f'  - Error analyzing market data: {e}')
    
    # 5. Signal analysis
    print('\n[5] SIGNAL ANALYSIS')
    
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
        
        # Last cycle analysis
        last_cycle = trading_results.get('last_cycle', {})
        if last_cycle:
            print(f'  - Last Cycle Analysis:')
            print(f'    - Signals Generated: {last_cycle.get("signals_generated", 0)}')
            print(f'    - Trades Executed: {last_cycle.get("trades_executed", 0)}')
            print(f'    - Entry Opportunities: {last_cycle.get("entry_opportunities", 0)}')
            print(f'    - Entry Failures: {last_cycle.get("entry_failures", 0)}')
            
            # Last cycle errors
            errors = last_cycle.get('errors', [])
            if errors:
                print(f'    - Last Cycle Errors: {len(errors)}')
                for error in errors[:3]:
                    print(f'      - {error}')
    
    except Exception as e:
        print(f'  - Error analyzing signals: {e}')
    
    # 6. Current execution logic
    print('\n[6] CURRENT EXECUTION LOGIC')
    
    # Analyze main runtime logic
    try:
        with open('main_runtime.py', 'r') as f:
            main_runtime_content = f.read()
        
        # Check key execution components
        execution_components = [
            'trade_orchestrator.run_trading_cycle',
            'signal_engine.generate_strategy_signal',
            'market_data_service.get_available_symbols',
            'position_manager.manage_positions',
            'order_executor.execute_order'
        ]
        
        print(f'  - Main Runtime Components:')
        for component in execution_components:
            if component in main_runtime_content:
                print(f'    - {component}: IMPLEMENTED')
            else:
                print(f'    - {component}: NOT FOUND')
        
        # Check trading cycle logic
        if 'while True:' in main_runtime_content and 'run_trading_cycle' in main_runtime_content:
            print(f'  - Trading Cycle: CONTINUOUS LOOP IMPLEMENTED')
        else:
            print(f'  - Trading Cycle: NOT PROPERLY IMPLEMENTED')
        
        # Check error handling
        if 'try:' in main_runtime_content and 'except' in main_runtime_content:
            print(f'  - Error Handling: IMPLEMENTED')
        else:
            print(f'  - Error Handling: NOT FOUND')
        
        # Check logging
        if 'log_system_error' in main_runtime_content:
            print(f'  - System Logging: IMPLEMENTED')
        else:
            print(f'  - System Logging: NOT FOUND')
    
    except Exception as e:
        print(f'  - Error analyzing main runtime: {e}')
    
    # 7. Current market condition analysis
    print('\n[7] CURRENT MARKET CONDITION ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Analyze current positions relative to market
        active_positions = trading_results.get('active_positions', {})
        
        if active_positions:
            print(f'  - Current Position Analysis:')
            
            total_unrealized_pnl = 0
            long_positions = 0
            short_positions = 0
            
            for symbol, position in active_positions.items():
                side = position.get('side', 'Unknown')
                unrealized_pnl = position.get('unrealized_pnl', 0)
                strategy = position.get('strategy', 'Unknown')
                
                total_unrealized_pnl += unrealized_pnl
                
                if side == 'LONG':
                    long_positions += 1
                elif side == 'SHORT':
                    short_positions += 1
            
            print(f'    - Total Unrealized PnL: {total_unrealized_pnl:+.4f}')
            print(f'    - Long Positions: {long_positions}')
            print(f'    - Short Positions: {short_positions}')
            print(f'    - Position Bias: {"LONG" if long_positions > short_positions else "SHORT" if short_positions > long_positions else "BALANCED"}')
            
            # Strategy distribution
            strategy_distribution = {}
            for position in active_positions.values():
                strategy = position.get('strategy', 'Unknown')
                strategy_distribution[strategy] = strategy_distribution.get(strategy, 0) + 1
            
            print(f'    - Strategy Distribution:')
            for strategy, count in strategy_distribution.items():
                print(f'      {strategy}: {count} positions')
        
        # Market regime analysis
        regime_distribution = trading_results.get('regime_distribution', {})
        if regime_distribution:
            print(f'  - Market Regime Analysis:')
            total_symbols = sum(regime_distribution.values())
            
            for regime, count in regime_distribution.items():
                percentage = (count / total_symbols) * 100 if total_symbols > 0 else 0
                print(f'    - {regime}: {count} symbols ({percentage:.1f}%)')
            
            # Dominant regime
            dominant_regime = max(regime_distribution, key=regime_distribution.get) if regime_distribution else 'UNKNOWN'
            print(f'    - Dominant Regime: {dominant_regime}')
    
    except Exception as e:
        print(f'  - Error analyzing market conditions: {e}')
    
    # 8. Current logic flow analysis
    print('\n[8] CURRENT LOGIC FLOW ANALYSIS')
    
    print(f'  - Program Execution Flow:')
    print(f'    1. Initialize TradingRuntime')
    print(f'    2. Load strategies (ma_trend_follow, ema_crossover)')
    print(f'    3. Load valid symbols from market data')
    print(f'    4. Enter continuous trading loop')
    print(f'    5. Sync account and positions')
    print(f'    6. Refresh pending orders')
    print(f'    7. Run trading cycle')
    print(f'    8. Generate signals for each symbol')
    print(f'    9. Execute trades based on signals')
    print(f'    10. Manage positions and risk')
    print(f'    11. Log results and repeat')
    
    print(f'\n  - Signal Generation Flow:')
    print(f'    1. Get market data for symbol')
    print(f'    2. Calculate indicators (SMA10, EMA12/21/26)')
    print(f'    3. Analyze market regime')
    print(f'    4. Generate signal based on MA logic')
    print(f'    5. Calculate confidence score')
    print(f'    6. Apply entry filters')
    print(f'    7. Return signal or HOLD')
    
    print(f'\n  - Position Management Flow:')
    print(f'    1. Monitor active positions')
    print(f'    2. Check stop-loss/take-profit conditions')
    print(f'    3. Apply partial take-profit if needed')
    print(f'    4. Close positions on exit conditions')
    print(f'    5. Update position states')
    
    # 9. Current issues and observations
    print('\n[9] CURRENT ISSUES AND OBSERVATIONS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        observations = []
        
        # Check for signal generation issues
        signals_generated = trading_results.get('signals_generated', 0)
        if signals_generated == 0:
            observations.append("No signals generated - possible market analysis issue")
        
        # Check for position management issues
        active_positions = trading_results.get('active_positions', {})
        if len(active_positions) > 0:
            total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in active_positions.values())
            if total_pnl < 0:
                observations.append(f"Active positions showing loss of ${total_pnl:.4f}")
        
        # Check for system errors
        system_errors = trading_results.get('system_errors', [])
        if len(system_errors) > 0:
            observations.append(f"{len(system_errors)} system errors detected")
        
        # Check for entry failures
        entry_failures = trading_results.get('entry_failures', 0)
        if entry_failures > 0:
            observations.append(f"{entry_failures} entry failures recorded")
        
        print(f'  - Observations:')
        for i, obs in enumerate(observations, 1):
            print(f'    {i}. {obs}')
        
        if not observations:
            print(f'    - No significant issues detected')
    
    except Exception as e:
        print(f'  - Error analyzing issues: {e}')
    
    # 10. Summary
    print('\n[10] CURRENT LOGIC SUMMARY')
    
    print(f'  - System Status: ACTIVE')
    print(f'  - Trading Mode: REAL-TIME')
    print(f'  - Strategies: ma_trend_follow, ema_crossover')
    print(f'  - Signal Logic: Moving Average based')
    print(f'  - Execution: Continuous loop with 10-second cycles')
    print(f'  - Risk Management: Stop-loss, take-profit, position limits')
    print(f'  - Market Analysis: SMA10, EMA12/21/26 calculations')
    print(f'  - Current Focus: Position management and signal generation')
    
    print('\n' + '=' * 80)
    print('CURRENT MARKET LOGIC ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_current_market_logic()
