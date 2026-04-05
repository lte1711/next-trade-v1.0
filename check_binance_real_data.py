#!/usr/bin/env python3
"""
바이낸스 테스트넷 실제 포지션 및 거래 확인
"""

import requests
import hmac
import hashlib
import urllib.parse
import time
import json
from datetime import datetime

def get_binance_testnet_account_info():
    """바이낸스 테스트넷 계정 정보 직접 조회"""
    
    # API 키 정보 (config.json에서 가져옴)
    api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
    api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
    
    # 기본 URL (선물 시장)
    base_url = "https://testnet.binancefuture.com"
    
    # 서버 시간 가져오기
    try:
        server_time_url = f"{base_url}/fapi/v1/time"
        response = requests.get(server_time_url)
        server_time = response.json()["serverTime"]
        print(f"✅ 서버 시간: {server_time}")
    except Exception as e:
        print(f"❌ 서버 시간 가져오기 실패: {e}")
        return None
    
    # 계정 정보 조회
    try:
        endpoint = "/fapi/v2/account"
        timestamp = server_time
        
        # 파라미터
        params = {
            "timestamp": timestamp,
            "recvWindow": 5000
        }
        
        # 서명 생성
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # 요청 URL
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        
        # 요청 헤더
        headers = {
            "X-MBX-APIKEY": api_key
        }
        
        # API 요청
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 계정 정보 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            account_info = response.json()
            return account_info
        else:
            print(f"❌ API 요청 실패: {response.status_code}")
            print(f"❌ 응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 계정 정보 조회 실패: {e}")
        return None

def check_positions():
    """포지션 정보 확인"""
    
    # API 키 정보
    api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
    api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
    
    base_url = "https://testnet.binancefuture.com"
    
    try:
        # 서버 시간
        server_time_url = f"{base_url}/fapi/v1/time"
        response = requests.get(server_time_url)
        server_time = response.json()["serverTime"]
        
        # 포지션 정보 조회
        endpoint = "/fapi/v2/positionRisk"
        timestamp = server_time
        
        params = {
            "timestamp": timestamp,
            "recvWindow": 5000
        }
        
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 포지션 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            positions = response.json()
            return positions
        else:
            print(f"❌ 포지션 조회 실패: {response.status_code}")
            print(f"❌ 응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 포지션 정보 조회 실패: {e}")
        return None

def check_orders():
    """주문 정보 확인"""
    
    # API 키 정보
    api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
    api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
    
    base_url = "https://testnet.binancefuture.com"
    
    try:
        # 서버 시간
        server_time_url = f"{base_url}/fapi/v1/time"
        response = requests.get(server_time_url)
        server_time = response.json()["serverTime"]
        
        # 주문 정보 조회
        endpoint = "/fapi/v1/allOrders"
        timestamp = server_time
        
        params = {
            "symbol": "BTCUSDT",
            "timestamp": timestamp,
            "recvWindow": 5000
        }
        
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 주문 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            return orders
        else:
            print(f"❌ 주문 조회 실패: {response.status_code}")
            print(f"❌ 응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 주문 정보 조회 실패: {e}")
        return None

def check_recent_trades():
    """최근 거래 내역 확인"""
    
    # API 키 정보
    api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
    api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
    
    base_url = "https://testnet.binancefuture.com"
    
    try:
        # 서버 시간
        server_time_url = f"{base_url}/fapi/v1/time"
        response = requests.get(server_time_url)
        server_time = response.json()["serverTime"]
        
        # 최근 거래 조회
        endpoint = "/fapi/v1/userTrades"
        timestamp = server_time
        
        params = {
            "symbol": "BTCUSDT",
            "timestamp": timestamp,
            "recvWindow": 5000
        }
        
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 거래 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            trades = response.json()
            return trades
        else:
            print(f"❌ 거래 조회 실패: {response.status_code}")
            print(f"❌ 응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 거래 정보 조회 실패: {e}")
        return None

def main():
    """메인 실행 함수"""
    
    print("🔍 바이낸스 테스트넷 실제 포지션 및 거래 확인!")
    print("=" * 60)
    
    # 계정 정보 확인
    print("\n📊 1. 계정 정보 확인...")
    account_info = get_binance_testnet_account_info()
    
    if account_info:
        print("\n✅ 계정 정보 확인 성공!")
        print(f"💰 총 자산: {account_info.get('totalWalletBalance', 'N/A')} USDT")
        print(f"📈 총 미실현 손익: {account_info.get('totalUnrealizedProfit', 'N/A')} USDT")
        print(f"💎 총 마진: {account_info.get('totalMarginBalance', 'N/A')} USDT")
        print(f"📊 총 포지션 마진: {account_info.get('totalPositionInitialMargin', 'N/A')} USDT")
        print(f"📋 미결제 주문 마진: {account_info.get('totalOpenOrderInitialMargin', 'N/A')} USDT")
        
        # 자산 정보
        assets = account_info.get('assets', [])
        if assets:
            print(f"\n💱 보유 자산 ({len(assets)}개):")
            for asset in assets:
                symbol = asset.get('asset', 'N/A')
                balance = asset.get('walletBalance', '0')
                if float(balance) > 0:
                    print(f"  {symbol}: {balance}")
    else:
        print("\n❌ 계정 정보 확인 실패!")
        return
    
    # 포지션 정보 확인
    print("\n📊 2. 포지션 정보 확인...")
    positions = check_positions()
    
    if positions:
        print(f"\n✅ 포지션 정보 확인 성공! (총 {len(positions)}개)")
        
        active_positions = [p for p in positions if float(p.get('positionAmt', '0')) != 0]
        if active_positions:
            print(f"\n🎯 활성 포지션 ({len(active_positions)}개):")
            for pos in active_positions:
                symbol = pos.get('symbol', 'N/A')
                side = "LONG" if float(pos.get('positionAmt', '0')) > 0 else "SHORT"
                size = pos.get('positionAmt', '0')
                entry_price = pos.get('entryPrice', '0')
                unrealized_pnl = pos.get('unrealizedProfit', '0')
                print(f"  {symbol}: {side} {size} @ {entry_price} | PnL: {unrealized_pnl}")
        else:
            print("\n🎯 활성 포지션: 없음")
    else:
        print("\n❌ 포지션 정보 확인 실패!")
    
    # 주문 정보 확인
    print("\n📊 3. 주문 정보 확인...")
    orders = check_orders()
    
    if orders:
        print(f"\n✅ 주문 정보 확인 성공! (총 {len(orders)}개)")
        
        if orders:
            print(f"\n📋 최근 주문 내역:")
            for order in orders[-5:]:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                order_type = order.get('type', 'N/A')
                quantity = order.get('origQty', '0')
                price = order.get('price', '0')
                status = order.get('status', 'N/A')
                time_str = datetime.fromtimestamp(int(order.get('time', 0))/1000).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {time_str} | {symbol} | {side} {order_type} | {quantity} @ {price} | {status}")
        else:
            print("\n📋 주문 내역: 없음")
    else:
        print("\n❌ 주문 정보 확인 실패!")
    
    # 거래 정보 확인
    print("\n📊 4. 거래 정보 확인...")
    trades = check_recent_trades()
    
    if trades:
        print(f"\n✅ 거래 정보 확인 성공! (총 {len(trades)}개)")
        
        if trades:
            print(f"\n📋 최근 거래 내역:")
            for trade in trades[-5:]:
                symbol = trade.get('symbol', 'N/A')
                side = trade.get('side', 'N/A')
                quantity = trade.get('qty', '0')
                price = trade.get('price', '0')
                commission = trade.get('commission', '0')
                time_str = datetime.fromtimestamp(int(trade.get('time', 0))/1000).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {time_str} | {symbol} | {side} | {quantity} @ {price} | 수수료: {commission}")
        else:
            print("\n📋 거래 내역: 없음")
    else:
        print("\n❌ 거래 정보 확인 실패!")
    
    print("\n" + "=" * 60)
    print("🔍 바이낸스 테스트넷 실제 포지션 및 거래 확인 완료!")

if __name__ == "__main__":
    main()
