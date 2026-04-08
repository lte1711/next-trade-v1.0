#!/usr/bin/env python3
import requests
import json
import hmac
import hashlib
import urllib.parse

# API credentials
api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
base_url = "https://testnet.binancefuture.com"

def get_server_time():
    try:
        r = requests.get(f"{base_url}/fapi/v1/time", timeout=10)
        r.raise_for_status()
        return r.json()["serverTime"]
    except Exception as e:
        print(f"Error getting server time: {e}")
        return int(time.time() * 1000)

def sign_params(params):
    query_string = urllib.parse.urlencode(params)
    return hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def test_order_response():
    """Test order and check response structure"""
    timestamp = get_server_time()
    
    # Test with minimum valid quantity
    params = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.002",  # Minimum notional 100 USDT, BTC ~ 68000, so 0.002 = 136 USDT
        "timestamp": timestamp,
        "recvWindow": 5000
    }
    params["signature"] = sign_params(params)
    
    headers = {"X-MBX-APIKEY": api_key}
    
    try:
        print("Testing order submission...")
        print(f"Parameters: {params}")
        
        r = requests.post(f"{base_url}/fapi/v1/order", params=params, headers=headers, timeout=10)
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            response = r.json()
            print("Order Response:")
            print(json.dumps(response, indent=2))
            
            # Check for avgPrice
            if 'avgPrice' in response:
                print(f"avgPrice found: {response['avgPrice']}")
            else:
                print("avgPrice NOT found in response")
                print("Available fields:", list(response.keys()))
                
        else:
            print(f"Order Error: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"Order Exception: {e}")

def get_current_price(symbol):
    """Get current price for symbol"""
    try:
        r = requests.get(f"{base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=10)
        r.raise_for_status()
        return float(r.json()["price"])
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return 0.0

if __name__ == "__main__":
    print("=== Order Response Debug ===")
    print()
    
    # Get current BTC price
    btc_price = get_current_price("BTCUSDT")
    print(f"Current BTCUSDT price: {btc_price}")
    
    # Calculate minimum quantity for 100 USDT notional
    min_qty = 100 / btc_price
    print(f"Minimum quantity for 100 USDT: {min_qty:.6f}")
    print()
    
    test_order_response()
