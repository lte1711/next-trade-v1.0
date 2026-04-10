#!/usr/bin/env python3
"""
Symbol Market Analysis - Analyze current market conditions for each symbol
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

def get_binance_ticker_24hr(symbol):
    """Get 24hr ticker data"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        base_url = config['binance_testnet']['base_url']
        
        url = f"{base_url}/fapi/v1/ticker/24hr"
        params = {'symbol': symbol}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting ticker for {symbol}: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error getting ticker for {symbol}: {e}")
        return None

def calculate_technical_indicators(prices, volumes):
    """Calculate technical indicators"""
    if len(prices) < 20:
        return {}
    
    try:
        # Price changes
        price_changes = [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]
        
        # Moving averages
        sma_10 = sum(prices[-10:]) / 10
        sma_20 = sum(prices[-20:]) / 20
        current_price = prices[-1]
        
        # EMA calculation
        def calculate_ema(prices, period):
            multiplier = 2 / (period + 1)
            ema = [sum(prices[:period]) / period]
            for i in range(period, len(prices)):
                current_ema = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
                ema.append(current_ema)
            return ema[-1]
        
        ema_12 = calculate_ema(prices, 12)
        ema_26 = calculate_ema(prices, 26)
        
        # RSI calculation
        gains = []
        losses = []
        for change in price_changes[-14:]:
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0
        
        if avg_loss > 0:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 100 if avg_gain > 0 else 50
        
        # Volatility (standard deviation)
        avg_price = sum(prices[-20:]) / 20
        variance = sum((price - avg_price) ** 2 for price in prices[-20:]) / 20
        volatility = (variance ** 0.5) / avg_price * 100
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Price momentum
        price_momentum_5 = ((prices[-1] - prices[-6]) / prices[-6] * 100) if len(prices) >= 6 else 0
        price_momentum_10 = ((prices[-1] - prices[-11]) / prices[-11] * 100) if len(prices) >= 11 else 0
        
        # Support and resistance levels (simplified)
        recent_highs = sorted(prices[-20:], reverse=True)[:5]
        recent_lows = sorted(prices[-20:])[:5]
        resistance = sum(recent_highs) / 5
        support = sum(recent_lows) / 5
        
        return {
            'current_price': current_price,
            'sma_10': sma_10,
            'sma_20': sma_20,
            'ema_12': ema_12,
            'ema_26': ema_26,
            'rsi': rsi,
            'volatility': volatility,
            'volume_ratio': volume_ratio,
            'price_momentum_5': price_momentum_5,
            'price_momentum_10': price_momentum_10,
            'support': support,
            'resistance': resistance,
            'price_vs_sma10': ((current_price - sma_10) / sma_10) * 100,
            'price_vs_sma20': ((current_price - sma_20) / sma_20) * 100,
            'price_vs_ema12': ((current_price - ema_12) / ema_12) * 100,
            'price_vs_ema26': ((current_price - ema_26) / ema_26) * 100
        }
    
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        return {}

def analyze_symbol_market(symbol):
    """Analyze market conditions for a specific symbol"""
    print(f"\n[{symbol}] Analyzing market conditions...")
    
    # Get kline data
    klines = get_binance_klines(symbol, '1h', 100)
    if not klines:
        return None
    
    # Get 24hr ticker data
    ticker = get_binance_ticker_24hr(symbol)
    
    # Extract data
    closes = [float(kline[4]) for kline in klines]
    volumes = [float(kline[5]) for kline in klines]
    highs = [float(kline[2]) for kline in klines]
    lows = [float(kline[3]) for kline in klines]
    
    current_price = closes[-1]
    
    # Calculate technical indicators
    indicators = calculate_technical_indicators(closes, volumes)
    
    if not indicators:
        return None
    
    # Market regime analysis
    regime = "UNKNOWN"
    regime_strength = 0
    
    if indicators['sma_10'] > indicators['sma_20'] and indicators['ema_12'] > indicators['ema_26']:
        regime = "BULLISH"
        regime_strength = min(1.0, (indicators['price_vs_sma10'] + indicators['price_vs_ema12']) / 10)
    elif indicators['sma_10'] < indicators['sma_20'] and indicators['ema_12'] < indicators['ema_26']:
        regime = "BEARISH"
        regime_strength = min(1.0, -(indicators['price_vs_sma10'] + indicators['price_vs_ema12']) / 10)
    else:
        regime = "SIDEWAYS"
        regime_strength = 0.5
    
    # Signal generation
    signal = "HOLD"
    signal_strength = 0
    signal_reason = "No clear signal"
    
    # RSI signals
    if indicators['rsi'] > 70:
        signal = "SELL"
        signal_strength = 0.7
        signal_reason = "RSI overbought"
    elif indicators['rsi'] < 30:
        signal = "BUY"
        signal_strength = 0.7
        signal_reason = "RSI oversold"
    
    # MA crossover signals
    if indicators['price_vs_sma10'] > 2 and indicators['price_vs_sma20'] > 1:
        signal = "BUY"
        signal_strength = 0.8
        signal_reason = "Price above MAs"
    elif indicators['price_vs_sma10'] < -2 and indicators['price_vs_sma20'] < -1:
        signal = "SELL"
        signal_strength = 0.8
        signal_reason = "Price below MAs"
    
    # Momentum signals
    if indicators['price_momentum_5'] > 3 and indicators['price_momentum_10'] > 5:
        if signal != "BUY":
            signal = "BUY"
            signal_strength = 0.6
            signal_reason = "Strong upward momentum"
    elif indicators['price_momentum_5'] < -3 and indicators['price_momentum_10'] < -5:
        if signal != "SELL":
            signal = "SELL"
            signal_strength = 0.6
            signal_reason = "Strong downward momentum"
    
    # Risk assessment
    risk_level = "LOW"
    if indicators['volatility'] > 5:
        risk_level = "HIGH"
    elif indicators['volatility'] > 3:
        risk_level = "MEDIUM"
    
    # Trading recommendation
    trading_recommendation = "HOLD"
    if signal == "BUY" and signal_strength > 0.6 and risk_level != "HIGH":
        trading_recommendation = "BUY"
    elif signal == "SELL" and signal_strength > 0.6 and risk_level != "HIGH":
        trading_recommendation = "SELL"
    
    return {
        'symbol': symbol,
        'current_price': current_price,
        'indicators': indicators,
        'regime': regime,
        'regime_strength': regime_strength,
        'signal': signal,
        'signal_strength': signal_strength,
        'signal_reason': signal_reason,
        'risk_level': risk_level,
        'trading_recommendation': trading_recommendation,
        'ticker_data': ticker
    }

def analyze_all_symbols():
    """Analyze market conditions for all symbols"""
    print('=' * 80)
    print('SYMBOL MARKET ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # Get symbols from trading results and add popular ones
    symbols = []
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Add active positions symbols
        active_positions = trading_results.get('active_positions', {})
        symbols.extend(list(active_positions.keys()))
        
        # Add some popular symbols if none
        if not symbols:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    except:
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    # Add some additional symbols for comprehensive analysis
    additional_symbols = ['SOLUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT', 'ATOMUSDT']
    for symbol in additional_symbols:
        if symbol not in symbols:
            symbols.append(symbol)
    
    print(f'Analyzing {len(symbols)} symbols...')
    print('=' * 80)
    
    # Analyze each symbol
    analyses = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f'[{i}/{len(symbols)}] Analyzing {symbol}...')
        
        analysis = analyze_symbol_market(symbol)
        if analysis:
            analyses.append(analysis)
            print(f'  Price: ${analysis["current_price"]:.6f}')
            print(f'  Regime: {analysis["regime"]} (Strength: {analysis["regime_strength"]:.2f})')
            print(f'  Signal: {analysis["signal"]} (Strength: {analysis["signal_strength"]:.2f})')
            print(f'  Risk: {analysis["risk_level"]}')
            print(f'  Recommendation: {analysis["trading_recommendation"]}')
        else:
            print(f'  Failed to analyze {symbol}')
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    # Summary analysis
    print('\n' + '=' * 80)
    print('MARKET ANALYSIS SUMMARY')
    print('=' * 80)
    
    if analyses:
        # Regime distribution
        regime_counts = {}
        for analysis in analyses:
            regime = analysis['regime']
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        print(f'\n[MARKET REGIME DISTRIBUTION]')
        total_symbols = len(analyses)
        for regime, count in regime_counts.items():
            percentage = (count / total_symbols) * 100
            print(f'  - {regime}: {count} symbols ({percentage:.1f}%)')
        
        # Signal distribution
        signal_counts = {}
        for analysis in analyses:
            signal = analysis['signal']
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        print(f'\n[SIGNAL DISTRIBUTION]')
        for signal, count in signal_counts.items():
            percentage = (count / total_symbols) * 100
            print(f'  - {signal}: {count} symbols ({percentage:.1f}%)')
        
        # Risk distribution
        risk_counts = {}
        for analysis in analyses:
            risk = analysis['risk_level']
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        print(f'\n[RISK DISTRIBUTION]')
        for risk, count in risk_counts.items():
            percentage = (count / total_symbols) * 100
            print(f'  - {risk}: {count} symbols ({percentage:.1f}%)')
        
        # Trading recommendations
        recommendation_counts = {}
        for analysis in analyses:
            rec = analysis['trading_recommendation']
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        print(f'\n[TRADING RECOMMENDATIONS]')
        for rec, count in recommendation_counts.items():
            percentage = (count / total_symbols) * 100
            print(f'  - {rec}: {count} symbols ({percentage:.1f}%)')
        
        # Top opportunities
        buy_opportunities = [a for a in analyses if a['trading_recommendation'] == 'BUY']
        sell_opportunities = [a for a in analyses if a['trading_recommendation'] == 'SELL']
        
        if buy_opportunities:
            buy_opportunities.sort(key=lambda x: x['signal_strength'], reverse=True)
            print(f'\n[TOP BUY OPPORTUNITIES]')
            for i, analysis in enumerate(buy_opportunities[:5], 1):
                print(f'  {i}. {analysis["symbol"]}: {analysis["signal"]} (Strength: {analysis["signal_strength"]:.2f})')
                print(f'     Price: ${analysis["current_price"]:.6f}, Reason: {analysis["signal_reason"]}')
        
        if sell_opportunities:
            sell_opportunities.sort(key=lambda x: x['signal_strength'], reverse=True)
            print(f'\n[TOP SELL OPPORTUNITIES]')
            for i, analysis in enumerate(sell_opportunities[:5], 1):
                print(f'  {i}. {analysis["symbol"]}: {analysis["signal"]} (Strength: {analysis["signal_strength"]:.2f})')
                print(f'     Price: ${analysis["current_price"]:.6f}, Reason: {analysis["signal_reason"]}')
        
        # Market sentiment
        bullish_count = regime_counts.get('BULLISH', 0)
        bearish_count = regime_counts.get('BEARISH', 0)
        sideways_count = regime_counts.get('SIDEWAYS', 0)
        
        print(f'\n[MARKET SENTIMENT]')
        if bullish_count > bearish_count and bullish_count > sideways_count:
            sentiment = "BULLISH"
            sentiment_strength = bullish_count / total_symbols
        elif bearish_count > bullish_count and bearish_count > sideways_count:
            sentiment = "BEARISH"
            sentiment_strength = bearish_count / total_symbols
        else:
            sentiment = "NEUTRAL/SIDEWAYS"
            sentiment_strength = sideways_count / total_symbols
        
        print(f'  - Overall Sentiment: {sentiment}')
        print(f'  - Sentiment Strength: {sentiment_strength:.2f}')
        
        # Volatility analysis
        volatilities = [a['indicators']['volatility'] for a in analyses]
        avg_volatility = sum(volatilities) / len(volatilities)
        high_volatility_symbols = [a for a in analyses if a['indicators']['volatility'] > avg_volatility * 1.5]
        
        print(f'\n[VOLATILITY ANALYSIS]')
        print(f'  - Average Volatility: {avg_volatility:.2f}%')
        print(f'  - High Volatility Symbols: {len(high_volatility_symbols)}')
        
        if high_volatility_symbols:
            print(f'  - Most Volatile:')
            high_volatility_symbols.sort(key=lambda x: x['indicators']['volatility'], reverse=True)
            for analysis in high_volatility_symbols[:3]:
                print(f'    - {analysis["symbol"]}: {analysis["indicators"]["volatility"]:.2f}%')
    
    print('\n' + '=' * 80)
    print('SYMBOL MARKET ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_all_symbols()
