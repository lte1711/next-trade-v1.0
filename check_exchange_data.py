#!/usr/bin/env python3
"""
거래소 데이터 확인 - 실제 거래 진행 여부 확인
"""

import requests
import hmac
import hashlib
import urllib.parse
from datetime import datetime

def check_exchange_data():
    """거래소 데이터 확인"""
    
    api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
    api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
    base_url = "https://testnet.binancefuture.com"
    
    print("🔍 거래소 데이터 확인 시작")
    print("=" * 80)
    
    try:
        # 1. 서버 시간 확인
        print("⏰ 서버 시간 확인...")
        response = requests.get(f"{base_url}/fapi/v1/time", timeout=10)
        if response.status_code == 200:
            server_time = response.json()["serverTime"]
            print(f"✅ 서버 시간: {server_time}")
        else:
            print(f"❌ 서버 시간 실패: {response.status_code}")
            return
        
        # 2. 계정 정보 확인
        print("\n💰 계정 정보 확인...")
        params = {
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}/fapi/v2/account?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            account_info = response.json()
            print(f"✅ 계정 정보 조회 성공")
            print(f"   총 자산: {account_info['totalWalletBalance']} USDT")
            print(f"   사용 가능: {account_info['availableBalance']} USDT")
            
            # totalUnrealizedPnl 필드가 있는지 확인
            if 'totalUnrealizedPnl' in account_info:
                print(f"   총 미실현 손익: {account_info['totalUnrealizedPnl']} USDT")
            else:
                print(f"   총 미실현 손익: 정보 없음")
            
            # totalMarginBalance 필드가 있는지 확인
            if 'totalMarginBalance' in account_info:
                print(f"   총 마진 잔고: {account_info['totalMarginBalance']} USDT")
            else:
                print(f"   총 마진 잔고: 정보 없음")
            
            # 포지션 정보 확인
            print(f"\n📊 포지션 정보:")
            active_positions = []
            for position in account_info['positions']:
                if float(position['positionAmt']) != 0:
                    active_positions.append(position)
                    print(f"   {position['symbol']}: {position['positionAmt']} ({position['entryPrice']})")
            
            if not active_positions:
                print("   열린 포지션 없음")
            
        else:
            print(f"❌ 계정 정보 실패: {response.status_code} - {response.text}")
            return
        
        # 3. 최근 거래 내역 확인
        print("\n📋 최근 거래 내역 확인...")
        params = {
            "timestamp": server_time,
            "recvWindow": 5000,
            "limit": 20
        }
        
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}/fapi/v1/userTrades?{query_string}&signature={signature}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            trades = response.json()
            print(f"✅ 최근 거래 내역: {len(trades)}개")
            
            if trades:
                print(f"\n📈 최근 거래 상세:")
                for i, trade in enumerate(trades[-10:], 1):  # 최근 10개
                    trade_time = datetime.fromtimestamp(int(trade['time']) / 1000)
                    print(f"   {i}. {trade['symbol']} | {trade['side']} | {trade['qty']} | ${trade['price']} | {trade_time.strftime('%H:%M:%S')}")
            else:
                print("   최근 거래 없음")
        else:
            print(f"❌ 거래 내역 실패: {response.status_code} - {response.text}")
        
        # 4. 최근 주문 내역 확인
        print("\n📋 최근 주문 내역 확인...")
        params = {
            "timestamp": server_time,
            "recvWindow": 5000,
            "limit": 20
        }
        
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}/fapi/v1/allOrders?{query_string}&signature={signature}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ 최근 주문 내역: {len(orders)}개")
            
            if orders:
                print(f"\n📈 최근 주문 상세:")
                for i, order in enumerate(orders[-10:], 1):  # 최근 10개
                    order_time = datetime.fromtimestamp(int(order['time']) / 1000)
                    status_icon = "✅" if order['status'] == 'FILLED' else "⏳" if order['status'] == 'NEW' else "❌"
                    print(f"   {i}. {order['symbol']} | {order['side']} | {order['origQty']} | {order['type']} | {status_icon} {order['status']} | {order_time.strftime('%H:%M:%S')}")
            else:
                print("   최근 주문 없음")
        else:
            print(f"❌ 주문 내역 실패: {response.status_code} - {response.text}")
        
        # 5. 특정 심볼 거래 내역 확인
        symbols_to_check = ["BTCUSDT", "ETHUSDT", "DASHUSDT", "ETCUSDT", "XRPUSDT"]
        
        print(f"\n📊 특정 심볼 거래 내역 확인:")
        for symbol in symbols_to_check:
            params = {
                "symbol": symbol,
                "timestamp": server_time,
                "recvWindow": 5000,
                "limit": 5
            }
            
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{base_url}/fapi/v1/userTrades?{query_string}&signature={signature}"
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                trades = response.json()
                if trades:
                    latest_trade = trades[-1]
                    trade_time = datetime.fromtimestamp(int(latest_trade['time']) / 1000)
                    print(f"   {symbol}: {latest_trade['side']} {latest_trade['qty']} @ ${latest_trade['price']} | {trade_time.strftime('%H:%M:%S')}")
                else:
                    print(f"   {symbol}: 거래 없음")
            else:
                print(f"   {symbol}: 조회 실패")
        
        # 6. 계정 자산 변동 확인
        print(f"\n💰 자산 변동 확인:")
        if response.status_code == 200:
            account_info = response.json()
            assets = account_info.get('assets', [])
            for asset in assets:
                if float(asset['walletBalance']) > 0:
                    print(f"   {asset['asset']}: {asset['walletBalance']} (미실현: {asset['unrealizedPnl']})")
        
        print(f"\n🎯 거래소 데이터 확인 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 거래소 데이터 확인 오류: {e}")

if __name__ == "__main__":
    check_exchange_data()
