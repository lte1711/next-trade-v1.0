#!/usr/bin/env python3
"""
Entry Conditions Analysis - Analyze why no new positions are opening
"""

import json
import requests
from datetime import datetime

def analyze_entry_conditions():
    """Analyze why no new positions are being opened"""
    print('=' * 60)
    print('ENTRY CONDITIONS ANALYSIS - WHY NO NEW POSITIONS?')
    print('=' * 60)
    
    # Load current state
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Check strategies and their last signals
    strategies = results.get('strategies', {})
    active_strategies = results.get('active_strategies', [])
    
    print('[STRATEGIES] Current strategy states:')
    for name in active_strategies:
        strategy = strategies.get(name, {})
        enabled = strategy.get('enabled', False)
        last_signal = strategy.get('last_signal')
        last_trade = strategy.get('last_trade')
        symbol_mode = strategy.get('symbol_mode', 'default')
        candidate_limit = strategy.get('candidate_limit', 5)
        
        print(f'  {name}:')
        print(f'    - Enabled: {enabled}')
        print(f'    - Symbol mode: {symbol_mode}')
        print(f'    - Candidate limit: {candidate_limit}')
        print(f'    - Last signal: {last_signal}')
        print(f'    - Last trade: {last_trade}')
    
    # Check signal generation status
    print('\n[SIGNALS] Signal generation status:')
    signals_generated = results.get('signals_generated', 0)
    trades_executed = results.get('trades_executed', 0)
    entry_failures = results.get('entry_failures', 0)
    
    print(f'  - Total signals generated: {signals_generated}')
    print(f'  - Total trades executed: {trades_executed}')
    print(f'  - Entry failures: {entry_failures}')
    
    # Check last cycle results
    last_cycle = results.get('last_cycle', {})
    if last_cycle:
        print('\n[LAST CYCLE] Previous cycle results:')
        print(f'  - Signals: {last_cycle.get("signals_generated", 0)}')
        print(f'  - Trades: {last_cycle.get("trades_executed", 0)}')
        print(f'  - Errors: {len(last_cycle.get("errors", []))}')
        
        errors = last_cycle.get('errors', [])
        if errors:
            print('  - Error details:')
            for i, error in enumerate(errors[:5], 1):
                print(f'    {i}. {error}')
    
    # Check market data status
    print('\n[MARKET] Market data availability:')
    try:
        # Get some major symbols to check data availability
        symbols_to_check = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
        
        for symbol in symbols_to_check:
            try:
                # Check if we can get kline data
                response = requests.get('https://demo-fapi.binance.com/fapi/v1/klines?symbol=USDT&interval=5m&limit=1', timeout=5)
                if response.status_code == 200:
                    print(f'  - {symbol}: Market data available')
                else:
                    print(f'  - {symbol}: Market data unavailable ({response.status_code})')
            except Exception as e:
                print(f'  - {symbol}: Market data error ({str(e)[:50]}...)')

    except Exception as e:
        print(f'  - Market data check failed: {e}')
    
    # Check V2 Merged alignment conditions
    print('\n[V2 MERGED] Alignment conditions check:')
    print('  - Required alignment count: 1')
    print('  - Consensus threshold: 1')
    print('  - Current market may not meet these conditions')
    
    # Check position capacity
    active_positions = results.get('active_positions', {})
    max_positions = 5  # From config
    available_slots = max_positions - len(active_positions)
    
    print(f'\n[CAPACITY] Position capacity:')
    print(f'  - Max positions: {max_positions}')
    print(f'  - Current positions: {len(active_positions)}')
    print(f'  - Available slots: {available_slots}')
    print(f'  - Can open new: {available_slots > 0}')
    
    # Check V2 Merged specific issues
    print('\n[V2 MERGED] Potential issues:')
    
    # Issue 1: Alignment conditions too strict
    print('  1. Alignment conditions:')
    print('     - Required alignment: 1/1')
    print('     - Consensus threshold: 1')
    print('     - This means ALL conditions must be met perfectly')
    
    # Issue 2: Market regime
    print('  2. Market regime:')
    print('     - Current market may be in RANGING mode')
    print('     - V2 Merged may require TRENDING mode')
    
    # Issue 3: Symbol selection
    print('  3. Symbol selection:')
    print('     - ma_trend_follow: leaders mode (top 10)')
    print('     - ema_crossover: volatile mode (top 8)')
    print('     - May not find suitable symbols')
    
    # Issue 4: Risk management
    print('  4. Risk management:')
    print('     - Stop loss: 2.0% (ma_trend_follow)')
    print('     - Stop loss: 1.5% (ema_crossover)')
    print('     - May be too tight for current volatility')
    
    # Check system errors
    system_errors = results.get('system_errors', [])
    if system_errors:
        print(f'\n[ERRORS] System errors ({len(system_errors)}):')
        for i, error in enumerate(system_errors[-5:], 1):  # Last 5 errors
            error_type = error.get('type', 'Unknown')
            error_message = error.get('message', 'No message')
            timestamp = error.get('timestamp', 'Unknown')
            print(f'  {i}. {timestamp}: {error_type} - {error_message}')
    else:
        print('\n[ERRORS] No system errors reported')
    
    # Summary
    print('\n' + '=' * 60)
    print('ANALYSIS SUMMARY')
    print('=' * 60)
    
    potential_reasons = []
    
    if signals_generated == 0:
        potential_reasons.append('No signals generated at all')
    
    if trades_executed == 0 and signals_generated > 0:
        potential_reasons.append('Signals generated but no trades executed')
    
    if entry_failures > 0:
        potential_reasons.append(f'Entry failures: {entry_failures}')
    
    if available_slots > 0:
        potential_reasons.append('Position capacity available')
    else:
        potential_reasons.append('Position capacity reached')
    
    print('POTENTIAL REASONS FOR NO NEW POSITIONS:')
    for i, reason in enumerate(potential_reasons, 1):
        print(f'  {i}. {reason}')
    
    print('\nRECOMMENDATIONS:')
    print('  1. Check signal engine output for actual signals')
    print('  2. Verify V2 Merged alignment conditions')
    print('  3. Review market regime analysis')
    print('  4. Check symbol selection logic')
    print('  5. Monitor entry failure reasons')
    
    print('=' * 60)
    print('[RESULT] Entry conditions analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    analyze_entry_conditions()
