#!/usr/bin/env python3
import requests
import time
import hmac
import hashlib

# API credentials from config.json
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
    import urllib.parse
    query_string = urllib.parse.urlencode(params)
    return hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def test_account_info():
    timestamp = get_server_time()
    params = {
        "timestamp": timestamp,
        "recvWindow": 5000
    }
    params["signature"] = sign_params(params)
    
    headers = {
        "X-MBX-APIKEY": api_key
    }
    
    try:
        r = requests.get(f"{base_url}/fapi/v2/account", params=params, headers=headers, timeout=10)
        print(f"Status Code: {r.status_code}")
        print(f"Response: {r.text[:200]}...")
        
        if r.status_code == 200:
            print("SUCCESS: Account info retrieved")
            return True
        else:
            print(f"ERROR: {r.status_code} - {r.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_order():
    timestamp = get_server_time()
    params = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.001",
        "timestamp": timestamp,
        "recvWindow": 5000
    }
    params["signature"] = sign_params(params)
    
    headers = {
        "X-MBX-APIKEY": api_key
    }
    
    try:
        r = requests.post(f"{base_url}/fapi/v1/order", params=params, headers=headers, timeout=10)
        print(f"Order Status Code: {r.status_code}")
        print(f"Order Response: {r.text[:200]}...")
        
        if r.status_code == 200:
            print("SUCCESS: Order placed")
            return True
        else:
            print(f"ORDER ERROR: {r.status_code} - {r.text}")
            return False
            
    except Exception as e:
        print(f"Order Exception: {e}")
        return False

if __name__ == "__main__":
    print("=== API Key Test ===")
    print(f"API Key: {api_key[:10]}...")
    print(f"Base URL: {base_url}")
    print()
    
    print("1. Testing Account Info...")
    account_ok = test_account_info()
    print()
    
    print("2. Testing Order...")
    order_ok = test_order()
    print()
    
    print("=== Results ===")
    print(f"Account Info: {'PASS' if account_ok else 'FAIL'}")
    print(f"Order Test: {'PASS' if order_ok else 'FAIL'}")
