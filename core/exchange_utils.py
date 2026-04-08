"""
Exchange Utils - 바이낸스 API 관련 유틸 함수 모듈
"""

import requests
import hmac
import hashlib


def create_signature(api_secret, query_string):
    """서명 생성"""
    return hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def create_query_string(params):
    """쿼리 스트링 생성"""
    return "&".join([f"{k}={v}" for k, v in sorted(params.items())])


def get_server_time(base_url):
    """서버 시간 조회"""
    try:
        response = requests.get(f"{base_url}/fapi/v1/time", timeout=5)
        if response.status_code == 200:
            return response.json().get("serverTime")
    except Exception:
        pass
    return None


def get_symbol_info(base_url, api_key, api_secret, symbol):
    """심볼 정보 조회"""
    try:
        server_time = get_server_time(base_url)
        if not server_time:
            return None
        
        timestamp = int(server_time * 1000)
        params = {
            "symbol": symbol,
            "timestamp": timestamp,
            "recvWindow": 5000
        }
        
        query_string = create_query_string(params)
        signature = create_signature(api_secret, query_string)
        
        url = f"{base_url}/fapi/v1/exchangeInfo?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            exchange_info = response.json()
            for symbol_info in exchange_info.get("symbols", []):
                if symbol_info.get("symbol") == symbol:
                    return symbol_info
        return None
    except Exception:
        return None
