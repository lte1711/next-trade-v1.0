#!/usr/bin/env python3
"""
Moving Average Symbol Evaluation - Evaluate each symbol based on moving averages
"""

import json
import requests
import hmac
import hashlib
from datetime import datetime
import time

def get_binance_klines(symbol, interval='1h', limit=50):
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

def evaluate_symbol_ma_status(symbol):
    """Evaluate symbol based on moving averages"""
    try:
        # Get kline data
        klines = get_binance_klines(symbol)
        
        if not klines:
            return None
        
        # Extract prices
        closes = [float(kline[4]) for kline in klines]
        highs = [float(kline[2]) for kline in klines]
        lows = [float(kline[3]) for kline in klines]
        volumes = [float(kline[5]) for kline in klines]
        
        current_price = closes[-1]
        
        # Calculate moving averages
        sma_10 = calculate_sma(closes, 10)
        sma_20 = calculate_sma(closes, 20)
        ema_12 = calculate_ema(closes, 12)
        ema_21 = calculate_ema(closes, 21)
        ema_26 = calculate_ema(closes, 26)
        
        if not all([sma_10, sma_20, ema_12, ema_21, ema_26]):
            return None
        
        # Calculate price vs MA percentages
        price_vs_sma10 = ((current_price - sma_10) / sma_10) * 100
        price_vs_sma20 = ((current_price - sma_20) / sma_20) * 100
        price_vs_ema12 = ((current_price - ema_12) / ema_12) * 100
        price_vs_ema21 = ((current_price - ema_21) / ema_21) * 100
        price_vs_ema26 = ((current_price - ema_26) / ema_26) * 100
        
        # Calculate MA alignments
        sma_alignment = "BULLISH" if sma_10 > sma_20 else "BEARISH"
        ema_alignment = "BULLISH" if ema_12 > ema_21 > ema_26 else "BEARISH"
        
        # Calculate crossovers
        ema_12_21_crossover = "BULLISH" if ema_12 > ema_21 else "BEARISH"
        ema_21_26_crossover = "BULLISH" if ema_21 > ema_26 else "BEARISH"
        
        # Calculate trend strength
        trend_strength = 0
        if price_vs_sma10 > 0:
            trend_strength += abs(price_vs_sma10)
        if price_vs_ema12 > 0:
            trend_strength += abs(price_vs_ema12)
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Generate trading signal based on MA logic
        signal = "HOLD"
        confidence = 0.0
        reason = "No clear MA signal"
        
        # MA-based signal logic (similar to system logic)
        if abs(price_vs_sma10) > 0.1:  # 0.1% threshold
            if price_vs_sma10 > 0:
                signal = "BUY"
                confidence = min(0.8, 0.3 + abs(price_vs_sma10) * 10)
                reason = f"Price {price_vs_sma10:.2f}% above SMA10"
            else:
                signal = "SELL"
                confidence = min(0.8, 0.3 + abs(price_vs_sma10) * 10)
                reason = f"Price {price_vs_sma10:.2f}% below SMA10"
        
        # Volume confirmation
        if volume_ratio > 1.2:
            confidence += 0.1
            reason += " with high volume"
        elif volume_ratio < 0.8:
            confidence -= 0.1
            reason += " with low volume"
        
        confidence = max(0, min(1, confidence))
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'sma_10': sma_10,
            'sma_20': sma_20,
            'ema_12': ema_12,
            'ema_21': ema_21,
            'ema_26': ema_26,
            'price_vs_sma10': price_vs_sma10,
            'price_vs_sma20': price_vs_sma20,
            'price_vs_ema12': price_vs_ema12,
            'price_vs_ema21': price_vs_ema21,
            'price_vs_ema26': price_vs_ema26,
            'sma_alignment': sma_alignment,
            'ema_alignment': ema_alignment,
            'ema_12_21_crossover': ema_12_21_crossover,
            'ema_21_26_crossover': ema_21_26_crossover,
            'trend_strength': trend_strength,
            'volume_ratio': volume_ratio,
            'signal': signal,
            'confidence': confidence,
            'reason': reason
        }
    
    except Exception as e:
        print(f"Error evaluating {symbol}: {e}")
        return None

def evaluate_all_symbols():
    """Evaluate all symbols based on moving averages"""
    print('=' * 80)
    print('MOVING AVERAGE SYMBOL EVALUATION')
    print('=' * 80)
    
    print(f'Evaluation Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # Get symbols from trading results or use default
    symbols = []
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Get active positions symbols
        active_positions = trading_results.get('active_positions', {})
        symbols.extend(list(active_positions.keys()))
        
        # Add common symbols if none
        if not symbols:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT', 
                      'LINKUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'MATICUSDT']
    
    except:
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT', 
                  'LINKUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'MATICUSDT']
    
    print(f'Evaluating {len(symbols)} symbols...')
    print('=' * 80)
    
    # Evaluate each symbol
    evaluations = []
    
    for symbol in symbols:
        print(f'\n[{symbol}] Evaluating...')
        evaluation = evaluate_symbol_ma_status(symbol)
        
        if evaluation:
            evaluations.append(evaluation)
            print(f'  Price: ${evaluation["current_price"]:.6f}')
            print(f'  SMA10: ${evaluation["sma_10"]:.6f} ({evaluation["price_vs_sma10"]:+.2f}%)')
            print(f'  SMA20: ${evaluation["sma_20"]:.6f} ({evaluation["price_vs_sma20"]:+.2f}%)')
            print(f'  EMA12: ${evaluation["ema_12"]:.6f} ({evaluation["price_vs_ema12"]:+.2f}%)')
            print(f'  EMA21: ${evaluation["ema_21"]:.6f} ({evaluation["price_vs_ema21"]:+.2f}%)')
            print(f'  EMA26: ${evaluation["ema_26"]:.6f} ({evaluation["price_vs_ema26"]:+.2f}%)')
            print(f'  SMA Alignment: {evaluation["sma_alignment"]}')
            print(f'  EMA Alignment: {evaluation["ema_alignment"]}')
            print(f'  Volume Ratio: {evaluation["volume_ratio"]:.2f}')
            print(f'  Signal: {evaluation["signal"]} (Confidence: {evaluation["confidence"]:.2f})')
            print(f'  Reason: {evaluation["reason"]}')
        else:
            print(f'  Failed to evaluate {symbol}')
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    # Summary analysis
    print('\n' + '=' * 80)
    print('SUMMARY ANALYSIS')
    print('=' * 80)
    
    if evaluations:
        # Count signals
        buy_signals = [e for e in evaluations if e['signal'] == 'BUY']
        sell_signals = [e for e in evaluations if e['signal'] == 'SELL']
        hold_signals = [e for e in evaluations if e['signal'] == 'HOLD']
        
        print(f'\n[SIGNAL SUMMARY]')
        print(f'  - BUY Signals: {len(buy_signals)}')
        print(f'  - SELL Signals: {len(sell_signals)}')
        print(f'  - HOLD Signals: {len(hold_signals)}')
        print(f'  - Total Evaluated: {len(evaluations)}')
        
        # Best buy opportunities
        if buy_signals:
            buy_signals.sort(key=lambda x: x['confidence'], reverse=True)
            print(f'\n[BEST BUY OPPORTUNITIES]')
            for i, eval in enumerate(buy_signals[:5], 1):
                print(f'  {i}. {eval["symbol"]}: {eval["signal"]} (Conf: {eval["confidence"]:.2f})')
                print(f'     Price: ${eval["current_price"]:.6f}, SMA10: {eval["price_vs_sma10"]:+.2f}%')
                print(f'     Reason: {eval["reason"]}')
        
        # Best sell opportunities
        if sell_signals:
            sell_signals.sort(key=lambda x: x['confidence'], reverse=True)
            print(f'\n[BEST SELL OPPORTUNITIES]')
            for i, eval in enumerate(sell_signals[:5], 1):
                print(f'  {i}. {eval["symbol"]}: {eval["signal"]} (Conf: {eval["confidence"]:.2f})')
                print(f'     Price: ${eval["current_price"]:.6f}, SMA10: {eval["price_vs_sma10"]:+.2f}%')
                print(f'     Reason: {eval["reason"]}')
        
        # Trend analysis
        bullish_ma = [e for e in evaluations if e['sma_alignment'] == 'BULLISH']
        bearish_ma = [e for e in evaluations if e['sma_alignment'] == 'BEARISH']
        
        print(f'\n[TREND ANALYSIS]')
        print(f'  - Bullish SMA Alignment: {len(bullish_ma)} ({len(bullish_ma)/len(evaluations)*100:.1f}%)')
        print(f'  - Bearish SMA Alignment: {len(bearish_ma)} ({len(bearish_ma)/len(evaluations)*100:.1f}%)')
        
        # High confidence signals
        high_confidence = [e for e in evaluations if e['confidence'] > 0.5]
        print(f'  - High Confidence Signals: {len(high_confidence)} ({len(high_confidence)/len(evaluations)*100:.1f}%)')
        
        # Volume analysis
        high_volume = [e for e in evaluations if e['volume_ratio'] > 1.5]
        print(f'  - High Volume Symbols: {len(high_volume)} ({len(high_volume)/len(evaluations)*100:.1f}%)')
    
    print('\n' + '=' * 80)
    print('MOVING AVERAGE SYMBOL EVALUATION COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    evaluate_all_symbols()
