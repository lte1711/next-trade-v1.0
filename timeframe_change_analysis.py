#!/usr/bin/env python3
"""
Timeframe Change Analysis - Analyze effects of changing 1h to 30m timeframe
"""

import json
import requests
import hmac
import hashlib
from datetime import datetime
import time

def get_binance_klines(symbol, interval='1h', limit=100):
    """Get kline data from Binance"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        base_url = config['binance_testnet']['base_url']
        
        # Get klines
        url = f"{base_url}/fapi/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting klines for {symbol}: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error getting klines for {symbol}: {e}")
        return None

def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    
    return sum(prices[-period:]) / period

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return None
    
    multiplier = 2 / (period + 1)
    
    # Start with SMA
    ema = [sum(prices[:period]) / period]
    
    # Calculate EMA
    for i in range(period, len(prices)):
        current_ema = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
        ema.append(current_ema)
    
    return ema[-1]

def analyze_timeframe_impact(symbol):
    """Analyze impact of timeframe change on a symbol"""
    print(f"\n[{symbol}] Analyzing timeframe impact...")
    
    # Get 1h data
    klines_1h = get_binance_klines(symbol, '1h', 50)
    # Get 30m data
    klines_30m = get_binance_klines(symbol, '30m', 100)  # More data for 30m
    
    if not klines_1h or not klines_30m:
        print(f"  - Error: Could not get kline data for {symbol}")
        return None
    
    # Extract prices
    closes_1h = [float(kline[4]) for kline in klines_1h]
    closes_30m = [float(kline[4]) for kline in klines_30m]
    
    current_price_1h = closes_1h[-1]
    current_price_30m = closes_30m[-1]
    
    print(f"  - Current Price (1h): ${current_price_1h:.6f}")
    print(f"  - Current Price (30m): ${current_price_30m:.6f}")
    
    # Calculate indicators for 1h
    sma_10_1h = calculate_sma(closes_1h, 10)
    ema_12_1h = calculate_ema(closes_1h, 12)
    ema_21_1h = calculate_ema(closes_1h, 21)
    ema_26_1h = calculate_ema(closes_1h, 26)
    
    # Calculate indicators for 30m
    sma_10_30m = calculate_sma(closes_30m, 10)
    ema_12_30m = calculate_ema(closes_30m, 12)
    ema_21_30m = calculate_ema(closes_30m, 21)
    ema_26_30m = calculate_ema(closes_30m, 26)
    
    if not all([sma_10_1h, ema_12_1h, ema_21_1h, ema_26_1h,
                sma_10_30m, ema_12_30m, ema_21_30m, ema_26_30m]):
        print(f"  - Error: Could not calculate indicators for {symbol}")
        return None
    
    # Calculate price vs MA percentages for 1h
    price_vs_sma10_1h = ((current_price_1h - sma_10_1h) / sma_10_1h) * 100
    price_vs_ema12_1h = ((current_price_1h - ema_12_1h) / ema_12_1h) * 100
    price_vs_ema21_1h = ((current_price_1h - ema_21_1h) / ema_21_1h) * 100
    price_vs_ema26_1h = ((current_price_1h - ema_26_1h) / ema_26_1h) * 100
    
    # Calculate price vs MA percentages for 30m
    price_vs_sma10_30m = ((current_price_30m - sma_10_30m) / sma_10_30m) * 100
    price_vs_ema12_30m = ((current_price_30m - ema_12_30m) / ema_12_30m) * 100
    price_vs_ema21_30m = ((current_price_30m - ema_21_30m) / ema_21_30m) * 100
    price_vs_ema26_30m = ((current_price_30m - ema_26_30m) / ema_26_30m) * 100
    
    # Generate signals for 1h
    signal_1h = "HOLD"
    confidence_1h = 0.0
    reason_1h = "No clear signal"
    
    if abs(price_vs_sma10_1h) > 0.1:
        if price_vs_sma10_1h > 0:
            signal_1h = "BUY"
            confidence_1h = min(0.8, 0.3 + abs(price_vs_sma10_1h) * 10)
            reason_1h = f"Price {price_vs_sma10_1h:.2f}% above SMA10"
        else:
            signal_1h = "SELL"
            confidence_1h = min(0.8, 0.3 + abs(price_vs_sma10_1h) * 10)
            reason_1h = f"Price {price_vs_sma10_1h:.2f}% below SMA10"
    
    # Generate signals for 30m
    signal_30m = "HOLD"
    confidence_30m = 0.0
    reason_30m = "No clear signal"
    
    if abs(price_vs_sma10_30m) > 0.1:
        if price_vs_sma10_30m > 0:
            signal_30m = "BUY"
            confidence_30m = min(0.8, 0.3 + abs(price_vs_sma10_30m) * 10)
            reason_30m = f"Price {price_vs_sma10_30m:.2f}% above SMA10"
        else:
            signal_30m = "SELL"
            confidence_30m = min(0.8, 0.3 + abs(price_vs_sma10_30m) * 10)
            reason_30m = f"Price {price_vs_sma10_30m:.2f}% below SMA10"
    
    # Calculate alignments
    sma_alignment_1h = "BULLISH" if sma_10_1h > calculate_sma(closes_1h, 20) else "BEARISH"
    sma_alignment_30m = "BULLISH" if sma_10_30m > calculate_sma(closes_30m, 20) else "BEARISH"
    
    ema_alignment_1h = "BULLISH" if ema_12_1h > ema_21_1h > ema_26_1h else "BEARISH"
    ema_alignment_30m = "BULLISH" if ema_12_30m > ema_21_30m > ema_26_30m else "BEARISH"
    
    # Calculate volatility
    def calculate_volatility(prices):
        if len(prices) < 2:
            return 0.0
        returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        return (variance ** 0.5) * 100
    
    volatility_1h = calculate_volatility(closes_1h[-20:])
    volatility_30m = calculate_volatility(closes_30m[-20:])
    
    # Calculate trend strength
    trend_strength_1h = abs(price_vs_sma10_1h) + abs(price_vs_ema12_1h)
    trend_strength_30m = abs(price_vs_sma10_30m) + abs(price_vs_ema12_30m)
    
    return {
        'symbol': symbol,
        'current_price_1h': current_price_1h,
        'current_price_30m': current_price_30m,
        'sma_10_1h': sma_10_1h,
        'sma_10_30m': sma_10_30m,
        'ema_12_1h': ema_12_1h,
        'ema_12_30m': ema_12_30m,
        'ema_21_1h': ema_21_1h,
        'ema_21_30m': ema_21_30m,
        'ema_26_1h': ema_26_1h,
        'ema_26_30m': ema_26_30m,
        'price_vs_sma10_1h': price_vs_sma10_1h,
        'price_vs_sma10_30m': price_vs_sma10_30m,
        'signal_1h': signal_1h,
        'signal_30m': signal_30m,
        'confidence_1h': confidence_1h,
        'confidence_30m': confidence_30m,
        'reason_1h': reason_1h,
        'reason_30m': reason_30m,
        'sma_alignment_1h': sma_alignment_1h,
        'sma_alignment_30m': sma_alignment_30m,
        'ema_alignment_1h': ema_alignment_1h,
        'ema_alignment_30m': ema_alignment_30m,
        'volatility_1h': volatility_1h,
        'volatility_30m': volatility_30m,
        'trend_strength_1h': trend_strength_1h,
        'trend_strength_30m': trend_strength_30m
    }

def analyze_timeframe_change_impact():
    """Analyze impact of changing from 1h to 30m timeframe"""
    print('=' * 80)
    print('TIMEFRAME CHANGE ANALYSIS: 1h → 30m')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # Get symbols from current positions
    symbols = []
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        active_positions = trading_results.get('active_positions', {})
        symbols.extend(list(active_positions.keys()))
        
        if not symbols:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    except:
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    print(f'Analyzing {len(symbols)} symbols for timeframe impact...')
    print('=' * 80)
    
    # Analyze each symbol
    analyses = []
    
    for symbol in symbols:
        analysis = analyze_timeframe_impact(symbol)
        if analysis:
            analyses.append(analysis)
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    # Detailed comparison
    print('\n[DETAILED TIMEFRAME COMPARISON]')
    
    for analysis in analyses:
        symbol = analysis['symbol']
        
        print(f'\n[{symbol}] Timeframe Comparison:')
        print(f'  1H Timeframe:')
        print(f'    - Price: ${analysis["current_price_1h"]:.6f}')
        print(f'    - SMA10: ${analysis["sma_10_1h"]:.6f} ({analysis["price_vs_sma10_1h"]:+.2f}%)')
        print(f'    - EMA12: ${analysis["ema_12_1h"]:.6f}')
        print(f'    - EMA21: ${analysis["ema_21_1h"]:.6f}')
        print(f'    - EMA26: ${analysis["ema_26_1h"]:.6f}')
        print(f'    - Signal: {analysis["signal_1h"]} (Conf: {analysis["confidence_1h"]:.2f})')
        print(f'    - Reason: {analysis["reason_1h"]}')
        print(f'    - SMA Alignment: {analysis["sma_alignment_1h"]}')
        print(f'    - EMA Alignment: {analysis["ema_alignment_1h"]}')
        print(f'    - Volatility: {analysis["volatility_1h"]:.2f}%')
        print(f'    - Trend Strength: {analysis["trend_strength_1h"]:.2f}')
        
        print(f'  30M Timeframe:')
        print(f'    - Price: ${analysis["current_price_30m"]:.6f}')
        print(f'    - SMA10: ${analysis["sma_10_30m"]:.6f} ({analysis["price_vs_sma10_30m"]:+.2f}%)')
        print(f'    - EMA12: ${analysis["ema_12_30m"]:.6f}')
        print(f'    - EMA21: ${analysis["ema_21_30m"]:.6f}')
        print(f'    - EMA26: ${analysis["ema_26_30m"]:.6f}')
        print(f'    - Signal: {analysis["signal_30m"]} (Conf: {analysis["confidence_30m"]:.2f})')
        print(f'    - Reason: {analysis["reason_30m"]}')
        print(f'    - SMA Alignment: {analysis["sma_alignment_30m"]}')
        print(f'    - EMA Alignment: {analysis["ema_alignment_30m"]}')
        print(f'    - Volatility: {analysis["volatility_30m"]:.2f}%')
        print(f'    - Trend Strength: {analysis["trend_strength_30m"]:.2f}')
        
        # Signal comparison
        if analysis['signal_1h'] != analysis['signal_30m']:
            print(f'  ⚠️  SIGNAL DIFFERENCE: {analysis["signal_1h"]} → {analysis["signal_30m"]}')
        else:
            print(f'  ✅ SIGNAL CONSISTENT: {analysis["signal_1h"]}')
        
        # Confidence comparison
        conf_diff = analysis['confidence_30m'] - analysis['confidence_1h']
        if abs(conf_diff) > 0.1:
            print(f'  📊 CONFIDENCE CHANGE: {conf_diff:+.2f} ({analysis["confidence_1h"]:.2f} → {analysis["confidence_30m"]:.2f})')
        
        # Volatility comparison
        vol_diff = analysis['volatility_30m'] - analysis['volatility_1h']
        print(f'  📈 VOLATILITY CHANGE: {vol_diff:+.2f}% ({analysis["volatility_1h"]:.2f}% → {analysis["volatility_30m"]:.2f}%)')
    
    # Summary analysis
    print('\n' + '=' * 80)
    print('TIMEFRAME CHANGE IMPACT SUMMARY')
    print('=' * 80)
    
    if analyses:
        # Signal comparison
        signal_changes = 0
        signal_consistent = 0
        
        buy_signals_1h = 0
        sell_signals_1h = 0
        hold_signals_1h = 0
        
        buy_signals_30m = 0
        sell_signals_30m = 0
        hold_signals_30m = 0
        
        for analysis in analyses:
            if analysis['signal_1h'] != analysis['signal_30m']:
                signal_changes += 1
            else:
                signal_consistent += 1
            
            if analysis['signal_1h'] == 'BUY':
                buy_signals_1h += 1
            elif analysis['signal_1h'] == 'SELL':
                sell_signals_1h += 1
            else:
                hold_signals_1h += 1
            
            if analysis['signal_30m'] == 'BUY':
                buy_signals_30m += 1
            elif analysis['signal_30m'] == 'SELL':
                sell_signals_30m += 1
            else:
                hold_signals_30m += 1
        
        print(f'\n[SIGNAL COMPARISON]')
        print(f'  - Signal Changes: {signal_changes}/{len(analyses)} ({signal_changes/len(analyses)*100:.1f}%)')
        print(f'  - Signal Consistent: {signal_consistent}/{len(analyses)} ({signal_consistent/len(analyses)*100:.1f}%)')
        
        print(f'\n[1H SIGNAL DISTRIBUTION]')
        print(f'  - BUY: {buy_signals_1h} ({buy_signals_1h/len(analyses)*100:.1f}%)')
        print(f'  - SELL: {sell_signals_1h} ({sell_signals_1h/len(analyses)*100:.1f}%)')
        print(f'  - HOLD: {hold_signals_1h} ({hold_signals_1h/len(analyses)*100:.1f}%)')
        
        print(f'\n[30M SIGNAL DISTRIBUTION]')
        print(f'  - BUY: {buy_signals_30m} ({buy_signals_30m/len(analyses)*100:.1f}%)')
        print(f'  - SELL: {sell_signals_30m} ({sell_signals_30m/len(analyses)*100:.1f}%)')
        print(f'  - HOLD: {hold_signals_30m} ({hold_signals_30m/len(analyses)*100:.1f}%)')
        
        # Confidence analysis
        avg_confidence_1h = sum(a['confidence_1h'] for a in analyses) / len(analyses)
        avg_confidence_30m = sum(a['confidence_30m'] for a in analyses) / len(analyses)
        
        print(f'\n[CONFIDENCE ANALYSIS]')
        print(f'  - Average Confidence (1h): {avg_confidence_1h:.3f}')
        print(f'  - Average Confidence (30m): {avg_confidence_30m:.3f}')
        print(f'  - Confidence Change: {avg_confidence_30m - avg_confidence_1h:+.3f}')
        
        # Volatility analysis
        avg_volatility_1h = sum(a['volatility_1h'] for a in analyses) / len(analyses)
        avg_volatility_30m = sum(a['volatility_30m'] for a in analyses) / len(analyses)
        
        print(f'\n[VOLATILITY ANALYSIS]')
        print(f'  - Average Volatility (1h): {avg_volatility_1h:.2f}%')
        print(f'  - Average Volatility (30m): {avg_volatility_30m:.2f}%')
        print(f'  - Volatility Change: {avg_volatility_30m - avg_volatility_1h:+.2f}%')
        
        # Trend strength analysis
        avg_trend_1h = sum(a['trend_strength_1h'] for a in analyses) / len(analyses)
        avg_trend_30m = sum(a['trend_strength_30m'] for a in analyses) / len(analyses)
        
        print(f'\n[TREND STRENGTH ANALYSIS]')
        print(f'  - Average Trend Strength (1h): {avg_trend_1h:.2f}')
        print(f'  - Average Trend Strength (30m): {avg_trend_30m:.2f}')
        print(f'  - Trend Strength Change: {avg_trend_30m - avg_trend_1h:+.2f}')
        
        # Key insights
        print(f'\n[KEY INSIGHTS]')
        
        if signal_changes > len(analyses) * 0.5:
            print(f'  ⚠️  HIGH SIGNAL SENSITIVITY: {signal_changes/len(analyses)*100:.1f}% of signals change')
        elif signal_changes > len(analyses) * 0.3:
            print(f'  ⚡ MODERATE SIGNAL SENSITIVITY: {signal_changes/len(analyses)*100:.1f}% of signals change')
        else:
            print(f'  ✅ LOW SIGNAL SENSITIVITY: {signal_changes/len(analyses)*100:.1f}% of signals change')
        
        if avg_volatility_30m > avg_volatility_1h * 1.2:
            print(f'  📈 HIGHER VOLATILITY: 30m shows {((avg_volatility_30m/avg_volatility_1h)-1)*100:.1f}% more volatility')
        elif avg_volatility_30m < avg_volatility_1h * 0.8:
            print(f'  📉 LOWER VOLATILITY: 30m shows {((1-avg_volatility_30m/avg_volatility_1h)*100):.1f}% less volatility')
        else:
            print(f'  📊 SIMILAR VOLATILITY: 30m and 1h show similar volatility')
        
        if avg_confidence_30m > avg_confidence_1h * 1.1:
            print(f'  🎯 HIGHER CONFIDENCE: 30m shows {((avg_confidence_30m/avg_confidence_1h)-1)*100:.1f}% higher confidence')
        elif avg_confidence_30m < avg_confidence_1h * 0.9:
            print(f'  🎯 LOWER CONFIDENCE: 30m shows {((1-avg_confidence_30m/avg_confidence_1h)*100):.1f}% lower confidence')
        else:
            print(f'  🎯 SIMILAR CONFIDENCE: 30m and 1h show similar confidence levels')
    
    print('\n' + '=' * 80)
    print('TIMEFRAME CHANGE ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_timeframe_change_impact()
