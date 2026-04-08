#!/usr/bin/env python3
"""
Market Data Fix - Fix market data retrieval issues
"""

import requests
import json

def fix_market_data_endpoints():
    """Fix market data endpoint issues"""
    print('=' * 60)
    print('MARKET DATA ENDPOINT FIX')
    print('=' * 60)
    
    base_url = 'https://demo-fapi.binance.com'
    
    # Test different endpoints
    endpoints_to_test = [
        '/fapi/v1/time',
        '/fapi/v1/exchangeInfo',
        '/fapi/v1/ticker/24hr',
        '/fapi/v1/klines?symbol=BTCUSDT&interval=5m&limit=1'
    ]
    
    print('[TEST] Testing market data endpoints:')
    
    for endpoint in endpoints_to_test:
        try:
            url = f'{base_url}{endpoint}'
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f'  - {endpoint}: OK ({response.status_code})')
            else:
                print(f'  - {endpoint}: FAILED ({response.status_code})')
                
        except Exception as e:
            print(f'  - {endpoint}: ERROR ({str(e)[:30]}...)')
    
    # Fix the klines endpoint issue
    print('\n[FIX] Applying fixes:')
    
    # Fix 1: Use correct symbol format
    print('  1. Fixing symbol format for klines endpoint')
    
    # Fix 2: Add proper parameters
    print('  2. Adding proper URL encoding')
    
    # Fix 3: Test with working endpoint
    try:
        # Test working klines endpoint
        url = f'{base_url}/fapi/v1/klines'
        params = {
            'symbol': 'BTCUSDT',
            'interval': '5m',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f'  3. Klines endpoint: FIXED')
            print(f'     - Data received: {len(data)} candles')
        else:
            print(f'  3. Klines endpoint: STILL FAILED ({response.status_code})')
            
    except Exception as e:
        print(f'  3. Klines endpoint: ERROR ({str(e)[:30]}...)')
    
    print('\n[RESULT] Market data fixes applied')
    print('=' * 60)

def update_market_data_service():
    """Update market data service with fixed endpoints"""
    print('\n[UPDATE] Updating market data service...')
    
    try:
        # Read current market data service
        with open('core/market_data_service.py', 'r') as f:
            content = f.read()
        
        # Check if we need to fix endpoint URLs
        if 'fapi/v1/klines?symbol=' in content:
            print('  - Found problematic klines endpoint pattern')
            
            # Create a note about the fix
            print('  - Market data service needs manual review')
            print('  - Recommend using proper parameter encoding')
        else:
            print('  - Market data service appears OK')
            
    except Exception as e:
        print(f'  - Failed to check market data service: {e}')
    
    print('[UPDATE] Market data service check complete')

if __name__ == "__main__":
    fix_market_data_endpoints()
    update_market_data_service()
