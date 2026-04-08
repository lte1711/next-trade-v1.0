#!/usr/bin/env python3
"""
Check Realtime Data - Analyze why realtime data is not being fetched
"""

import json
import requests
from datetime import datetime

def check_realtime_data():
    """Check why realtime data is not being fetched"""
    print('=' * 60)
    print('REALTIME DATA ISSUE ANALYSIS')
    print('=' * 60)
    
    # Check current market data in trading_results.json
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    market_data = results.get('market_data', {})
    
    print('[CURRENT MARKET DATA] Status:')
    print(f'  - Total symbols: {len(market_data)}')
    
    if market_data:
        # Check some key symbols
        key_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
        for symbol in key_symbols:
            if symbol in market_data:
                price = market_data[symbol]
                print(f'  - {symbol}: {price} USDT')
            else:
                print(f'  - {symbol}: NOT FOUND')
        
        # Check if prices are updating
        print(f'\n[DATA FRESHNESS] Check if data is updating:')
        
        # Check last sync time
        last_sync = results.get('last_sync_time')
        if last_sync:
            print(f'  - Last sync time: {last_sync}')
        else:
            print(f'  - Last sync time: NOT FOUND')
        
        # Check start time
        start_time = results.get('start_time')
        if start_time:
            print(f'  - Start time: {start_time}')
        
        # Check if current prices look realistic
        print(f'\n[DATA VALIDITY] Check if prices are realistic:')
        
        unrealistic_prices = []
        for symbol, price in market_data.items():
            try:
                price_float = float(price)
                if price_float <= 0 or price_float > 1000000:
                    unrealistic_prices.append((symbol, price))
            except (ValueError, TypeError):
                unrealistic_prices.append((symbol, price))
        
        if unrealistic_prices:
            print(f'  - Unrealistic prices found: {len(unrealistic_prices)}')
            for symbol, price in unrealistic_prices[:5]:
                print(f'    {symbol}: {price}')
        else:
            print(f'  - All prices appear realistic')
    
    else:
        print(f'  - No market data found')
    
    # Check API connectivity
    print(f'\n[API CONNECTIVITY] Test Binance API:')
    
    base_url = 'https://demo-fapi.binance.com'
    
    # Test server time
    try:
        response = requests.get(f'{base_url}/fapi/v1/time', timeout=5)
        if response.status_code == 200:
            server_time = response.json()['serverTime']
            print(f'  - Server time: OK ({response.status_code})')
            print(f'  - Server timestamp: {server_time}')
        else:
            print(f'  - Server time: FAILED ({response.status_code})')
    except Exception as e:
        print(f'  - Server time: ERROR ({str(e)[:50]}...)')
    
    # Test ticker data
    try:
        response = requests.get(f'{base_url}/fapi/v1/ticker/24hr?symbol=BTCUSDT', timeout=5)
        if response.status_code == 200:
            ticker = response.json()
            current_price = ticker['lastPrice']
            print(f'  - BTCUSDT ticker: OK ({response.status_code})')
            print(f'  - Current price: {current_price}')
        else:
            print(f'  - BTCUSDT ticker: FAILED ({response.status_code})')
    except Exception as e:
        print(f'  - BTCUSDT ticker: ERROR ({str(e)[:50]}...)')
    
    # Test klines data
    try:
        response = requests.get(f'{base_url}/fapi/v1/klines?symbol=BTCUSDT&interval=1m&limit=1', timeout=5)
        if response.status_code == 200:
            klines = response.json()
            if klines:
                latest_price = klines[0][4]
                print(f'  - BTCUSDT klines: OK ({response.status_code})')
                print(f'  - Latest price: {latest_price}')
            else:
                print(f'  - BTCUSDT klines: EMPTY DATA')
        else:
            print(f'  - BTCUSDT klines: FAILED ({response.status_code})')
    except Exception as e:
        print(f'  - BTCUSDT klines: ERROR ({str(e)[:50]}...)')
    
    # Check market data service
    print(f'\n[MARKET DATA SERVICE] Check service status:')
    
    try:
        from core.market_data_service import MarketDataService
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        # Test get_available_symbols
        symbols = mds.get_available_symbols()
        print(f'  - Available symbols: {len(symbols)}')
        
        # Test update_market_data
        test_symbols = symbols[:5]  # Test with first 5 symbols
        market_data = mds.update_market_data(test_symbols)
        print(f'  - Updated market data: {len(market_data)} symbols')
        
        # Check if data is fresh
        if market_data:
            for symbol in test_symbols[:3]:
                if symbol in market_data:
                    data = market_data[symbol]
                    prices = data.get('prices', {})
                    current_price = prices.get('current', 0)
                    print(f'    {symbol}: {current_price}')
                else:
                    print(f'    {symbol}: NO DATA')
        
    except Exception as e:
        print(f'  - Market data service: ERROR ({str(e)[:50]}...)')
        import traceback
        traceback.print_exc()
    
    # Check if trading system is running cycles
    print(f'\n[TRADING CYCLES] Check cycle execution:')
    
    # Check last cycle results
    last_cycle = results.get('last_cycle', {})
    if last_cycle:
        cycle_time = last_cycle.get('timestamp')
        signals_generated = last_cycle.get('signals_generated', 0)
        trades_executed = last_cycle.get('trades_executed', 0)
        errors = last_cycle.get('errors', [])
        
        print(f'  - Last cycle time: {cycle_time}')
        print(f'  - Signals generated: {signals_generated}')
        print(f'  - Trades executed: {trades_executed}')
        print(f'  - Errors: {len(errors)}')
        
        if errors:
            print(f'  - Recent errors:')
            for i, error in enumerate(errors[-3:], 1):
                error_type = error.get('type', 'Unknown')
                error_message = error.get('message', 'No message')
                print(f'    {i}. {error_type}: {error_message}')
    else:
        print(f'  - No recent cycles found')
    
    # Check system errors
    system_errors = results.get('system_errors', [])
    recent_errors = [e for e in system_errors if 'data' in e.get('message', '').lower() or 'api' in e.get('message', '').lower()]
    
    if recent_errors:
        print(f'\n[DATA ERRORS] Recent data-related errors:')
        for i, error in enumerate(recent_errors[-5:], 1):
            timestamp = error.get('timestamp', 'Unknown')
            error_type = error.get('type', 'Unknown')
            error_message = error.get('message', 'No message')
            print(f'  {i}. {timestamp}: {error_type} - {error_message}')
    else:
        print(f'\n[DATA ERRORS] No recent data-related errors')
    
    # Check if prices are actually updating
    print(f'\n[PRICE UPDATES] Check if prices are updating over time:')
    
    # Compare with previous cycle if available
    previous_market_data = results.get('previous_market_data', {})
    if previous_market_data:
        updated_symbols = []
        unchanged_symbols = []
        
        for symbol in market_data:
            if symbol in previous_market_data:
                current_price = market_data.get(symbol, 0)
                previous_price = previous_market_data.get(symbol, 0)
                
                try:
                    current_float = float(current_price)
                    previous_float = float(previous_price)
                    
                    if abs(current_float - previous_float) > 0.001:  # Small threshold
                        updated_symbols.append(symbol)
                    else:
                        unchanged_symbols.append(symbol)
                except (ValueError, TypeError):
                    unchanged_symbols.append(symbol)
        
        print(f'  - Updated symbols: {len(updated_symbols)}')
        print(f'  - Unchanged symbols: {len(unchanged_symbols)}')
        
        if updated_symbols:
            print(f'  - Recently updated: {updated_symbols[:5]}')
    else:
        print(f'  - No previous data to compare')
    
    print('=' * 60)
    print('[RESULT] Realtime data analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    check_realtime_data()
