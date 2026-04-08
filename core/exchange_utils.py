"""
Exchange Utils - Binance API Utility Functions Module
"""

import requests
import hmac
import hashlib


def create_signature(api_secret, query_string):
    """Create signature"""
    return hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def create_query_string(params):
    """Create query string"""
    return "&".join([f"{k}={v}" for k, v in sorted(params.items())])


def get_server_time(base_url):
    """Get server time"""
    try:
        response = requests.get(f"{base_url}/fapi/v1/time", timeout=5)
        if response.status_code == 200:
            return response.json().get("serverTime")
    except Exception:
        pass
    return None


def get_symbol_info(base_url, api_key, api_secret, symbol):
    """Get symbol information"""
    try:
        url = f"{base_url}/fapi/v1/exchangeInfo"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            exchange_info = response.json()
            for symbol_info in exchange_info.get("symbols", []):
                if symbol_info.get("symbol") == symbol:
                    return symbol_info
        return None
    except Exception:
        return None
