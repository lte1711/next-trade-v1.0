#!/usr/bin/env python3
"""
Execute Next Trading Cycle - Execute and monitor the next trading cycle
"""

import json
import time
from datetime import datetime

def execute_next_trading_cycle():
    """Execute and monitor the next trading cycle"""
    print('=' * 80)
    print('EXECUTE NEXT TRADING CYCLE')
    print('=' * 80)
    
    print(f'Cycle Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Pre-cycle checks
    print('\n[1. PRE-CYCLE CHECKS]')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Check system state
        active_positions = results.get('active_positions', {})
        pending_trades = results.get('pending_trades', [])
        market_data = results.get('market_data', {})
        
        print(f'  - Active Positions: {len(active_positions)}')
        print(f'  - Pending Trades: {len(pending_trades)}')
        print(f'  - Market Data Symbols: {len(market_data)}')
        print(f'  - Available Slots: {5 - len(active_positions)}')
        
        # Check if we can proceed
        if len(active_positions) >= 5:
            print('  - Status: AT CAPACITY - Cannot open new positions')
            return
        else:
            print('  - Status: READY - Can open new positions')
        
    except Exception as e:
        print(f'  - Error: {e}')
        return
    
    # 2. Market data update
    print('\n[2. MARKET DATA UPDATE]')
    
    try:
        from core.market_data_service import MarketDataService
        
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        # Get top symbols
        top_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        
        print(f'  - Updating market data for {len(top_symbols)} symbols...')
        
        # Update market data
        updated_market_data = mds.update_market_data(top_symbols)
        
        print(f'  - Market data updated: {len(updated_market_data)} symbols')
        
        # Update trading results
        results['market_data'] = {}
        for symbol, data in updated_market_data.items():
            prices = data.get('prices', {})
            current_price = prices.get('current', 0)
            if current_price > 0:
                results['market_data'][symbol] = str(current_price)
        
        print(f'  - Market data saved to trading results')
        
    except Exception as e:
        print(f'  - Error updating market data: {e}')
        return
    
    # 3. Regime analysis
    print('\n[3. REGIME ANALYSIS]')
    
    try:
        from core.market_regime_service import MarketRegimeService
        
        mrs = MarketRegimeService()
        
        regime_data = {}
        regime_distribution = {}
        
        print(f'  - Analyzing market regime for symbols...')
        
        for symbol, symbol_data in updated_market_data.items():
            prices = []
            volumes = []
            
            # Extract price data from klines
            klines_1h = symbol_data.get('klines', {}).get('1h', [])
            for kline in klines_1h[-20:]:  # Last 20 periods
                if kline:
                    prices.append(kline.get('close', 0))
                    volumes.append(kline.get('volume', 0))
            
            if len(prices) >= 14:  # Minimum for ADX calculation
                regime = mrs.analyze_market_regime(prices, volumes)
                regime_data[symbol] = regime
                
                # Update distribution
                regime_name = regime.get('regime', 'UNKNOWN')
                regime_distribution[regime_name] = regime_distribution.get(regime_name, 0) + 1
                
                print(f'    - {symbol}: {regime_name} (ADX: {regime.get("trend_strength", 0):.2f})')
        
        # Update regime distribution
        results['regime_distribution'] = regime_distribution
        
        print(f'  - Regime analysis completed: {len(regime_data)} symbols')
        print(f'  - Regime distribution: {regime_distribution}')
        
    except Exception as e:
        print(f'  - Error in regime analysis: {e}')
        return
    
    # 4. Signal generation
    print('\n[4. SIGNAL GENERATION]')
    
    try:
        from core.strategy_registry import StrategyRegistry
        from core.signal_engine import SignalEngine
        from core.indicator_service import IndicatorService
        
        sr = StrategyRegistry()
        signal_engine = SignalEngine()
        
        # Get strategies
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        generated_signals = []
        
        for strategy_name in strategies:
            print(f'  - Generating signals for {strategy_name}...')
            
            strategy_config = sr.get_strategy_profile(strategy_name)
            if not strategy_config:
                print(f'    - Strategy config not found')
                continue
            
            # Generate signals for each symbol
            for symbol, symbol_data in updated_market_data.items():
                # Skip if already in active positions or pending trades
                if symbol in active_positions or symbol in [t.get('symbol') for t in pending_trades]:
                    continue
                
                # Get market data
                market_data_dict = {
                    'prices': symbol_data.get('prices', {}),
                    'klines': symbol_data.get('klines', {})
                }
                
                # Get regime data
                regime = regime_data.get(symbol, {})
                
                # Calculate indicators
                indicators = {}
                try:
                    # Basic indicators
                    klines_1h = symbol_data.get('klines', {}).get('1h', [])
                    if klines_1h:
                        closes = [k['close'] for k in klines_1h]
                        if len(closes) >= 20:
                            # Simple moving averages
                            sma_20 = sum(closes[-20:]) / 20
                            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
                            
                            indicators['sma_20'] = sma_20
                            indicators['sma_50'] = sma_50
                            indicators['price'] = closes[-1]
                except Exception as e:
                    print(f'    - Error calculating indicators for {symbol}: {e}')
                    continue
                
                # Generate signal
                signal = signal_engine.generate_strategy_signal(
                    market_data_dict, indicators, regime, strategy_config
                )
                
                if signal and signal.get('signal') != 'HOLD':
                    signal['symbol'] = symbol
                    signal['strategy'] = strategy_name
                    signal['timestamp'] = datetime.now().isoformat()
                    
                    generated_signals.append(signal)
                    
                    print(f'    - {symbol}: {signal.get("signal")} (Confidence: {signal.get("confidence", 0):.2f})')
        
        print(f'  - Total signals generated: {len(generated_signals)}')
        
    except Exception as e:
        print(f'  - Error in signal generation: {e}')
        return
    
    # 5. Signal evaluation and filtering
    print('\n[5. SIGNAL EVALUATION]')
    
    if not generated_signals:
        print('  - No signals generated - cycle complete')
        return
    
    # Filter signals by confidence
    min_confidence = 0.5
    filtered_signals = [s for s in generated_signals if s.get('confidence', 0) >= min_confidence]
    
    print(f'  - Signals after confidence filter: {len(filtered_signals)}')
    
    # Sort by confidence
    filtered_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    # Select top signals (up to available slots)
    available_slots = 5 - len(active_positions)
    top_signals = filtered_signals[:available_slots]
    
    print(f'  - Top signals selected: {len(top_signals)}')
    
    for i, signal in enumerate(top_signals, 1):
        symbol = signal.get('symbol', 'Unknown')
        signal_type = signal.get('signal', 'Unknown')
        confidence = signal.get('confidence', 0)
        strategy = signal.get('strategy', 'Unknown')
        
        print(f'    {i}. {symbol}: {signal_type} ({strategy}) - Confidence: {confidence:.2f}')
    
    # 6. Trade execution simulation
    print('\n[6. TRADE EXECUTION]')
    
    if not top_signals:
        print('  - No signals to execute - cycle complete')
        return
    
    executed_trades = []
    
    for signal in top_signals:
        symbol = signal.get('symbol', 'Unknown')
        signal_type = signal.get('signal', 'Unknown')
        strategy = signal.get('strategy', 'Unknown')
        confidence = signal.get('confidence', 0)
        
        # Get current price
        current_price = float(results['market_data'].get(symbol, 0))
        
        if current_price <= 0:
            print(f'    - {symbol}: Invalid price - skipping')
            continue
        
        # Calculate position size (simplified)
        position_size_usdt = 100  # Fixed size for simulation
        
        if signal_type == 'BUY':
            quantity = position_size_usdt / current_price
        else:
            quantity = position_size_usdt / current_price
        
        # Create trade record
        trade = {
            'symbol': symbol,
            'side': signal_type,
            'quantity': quantity,
            'price': current_price,
            'strategy': strategy,
            'signal_confidence': confidence,
            'signal_reason': signal.get('reason', 'Generated signal'),
            'status': 'SIMULATED',
            'timestamp': datetime.now().isoformat(),
            'type': 'SIMULATED_TRADE',
            'position_type': 'LONG' if signal_type == 'BUY' else 'SHORT'
        }
        
        executed_trades.append(trade)
        
        print(f'    - {symbol}: {signal_type} {quantity:.6f} @ {current_price:.6f} USDT')
    
    print(f'  - Simulated trades executed: {len(executed_trades)}')
    
    # 7. Update trading results
    print('\n[7. UPDATE TRADING RESULTS]')
    
    # Update last cycle
    results['last_cycle'] = {
        'timestamp': datetime.now().isoformat(),
        'signals_generated': len(generated_signals),
        'trades_executed': len(executed_trades),
        'errors': [],
        'regime_distribution': regime_distribution
    }
    
    # Add simulated trades to pending trades
    for trade in executed_trades:
        pending_trades.append(trade)
    
    results['pending_trades'] = pending_trades
    
    # Save results
    with open('trading_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print('  - Trading results updated')
    
    # 8. Cycle summary
    print('\n[8. CYCLE SUMMARY]')
    
    print(f'  - Cycle Duration: Completed')
    print(f'  - Market Data Updated: {len(updated_market_data)} symbols')
    print(f'  - Regime Analysis: {len(regime_data)} symbols')
    print(f'  - Signals Generated: {len(generated_signals)}')
    print(f'  - Signals Filtered: {len(filtered_signals)}')
    print(f'  - Trades Executed: {len(executed_trades)}')
    print(f'  - Pending Trades: {len(pending_trades)}')
    
    if regime_distribution:
        print(f'  - Market Regime: {regime_distribution}')
    
    if executed_trades:
        print(f'  - Executed Trades:')
        for trade in executed_trades:
            symbol = trade.get('symbol', 'Unknown')
            side = trade.get('side', 'Unknown')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            strategy = trade.get('strategy', 'Unknown')
            
            print(f'    - {symbol}: {side} {quantity:.6f} @ {price:.6f} ({strategy})')
    
    print('\n' + '=' * 80)
    print('[TRADING CYCLE COMPLETE]')
    print('=' * 80)
    print(f'Next cycle will automatically process pending trades')
    print('=' * 80)

if __name__ == "__main__":
    execute_next_trading_cycle()
