#!/usr/bin/env python3
"""
수정된 선물 거래 테스트 - MIN_NOTIONAL 문제 해결
"""

import requests
import json
import hmac
import hashlib
import urllib.parse

def test_fixed_order():
    """수정된 주문 테스트"""
    
    api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
    api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
    base_url = "https://testnet.binancefuture.com"
    symbol = "BTCUSDT"
    
    print("🧪 수정된 주문 테스트 시작")
    print("=" * 50)
    
    try:
        # 서버 시간 가져오기
        response = requests.get(f"{base_url}/fapi/v1/time", timeout=10)
        server_time = response.json()["serverTime"]
        print(f"✅ 서버 시간: {server_time}")
        
        # 심볼 정보 가져오기
        response = requests.get(f"{base_url}/fapi/v1/exchangeInfo", timeout=10)
        exchange_info = response.json()
        
        symbol_info = None
        for s in exchange_info["symbols"]:
            if s["symbol"] == symbol:
                symbol_info = s
                break
        
        if not symbol_info:
            print("❌ 심볼 정보 없음")
            return
        
        # 필터 정보 추출
        filters = symbol_info["filters"]
        min_qty = 0.0
        max_qty = 0.0
        min_notional = 0.0
        qty_precision = 0
        
        for f in filters:
            if f["filterType"] == "LOT_SIZE":
                min_qty = float(f["minQty"])
                max_qty = float(f["maxQty"])
                if "stepQty" in f and "." in f["stepQty"]:
                    qty_precision = len(f["stepQty"].split('.')[1])
                else:
                    qty_precision = 8
            elif f["filterType"] == "MIN_NOTIONAL":
                if "notional" in f:
                    min_notional = float(f["notional"])
                else:
                    # 심볼별 최소 notional 기본값
                    symbol_defaults = {
                        "BTCUSDT": 100.0,
                        "ETHUSDT": 10.0,
                        "SOLUSDT": 5.0,
                        "DOGEUSDT": 10.0,
                        "ADAUSDT": 10.0,
                        "MATICUSDT": 10.0,
                        "AVAXUSDT": 10.0,
                        "DOTUSDT": 10.0,
                        "LINKUSDT": 10.0,
                        "LTCUSDT": 10.0
                    }
                    min_notional = symbol_defaults.get(symbol, 10.0)
        
        print(f"📋 필터 정보:")
        print(f"   최소 수량: {min_qty}")
        print(f"   최대 수량: {max_qty}")
        print(f"   최소 notional: {min_notional}")
        print(f"   수량 정밀도: {qty_precision}")
        
        # 현재 가격 확인
        response = requests.get(f"{base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=10)
        current_price = float(response.json()["price"])
        print(f"   현재 가격: {current_price}")
        
        # 최소 notional 만족하는 수량 계산
        quantity = min_notional / current_price
        
        # 최소 수량 보장
        if quantity < min_qty:
            quantity = min_qty
        
        # 최대 수량 확인
        if quantity > max_qty:
            quantity = max_qty
        
        # 수량 정밀도 조정
        quantity = round(quantity, qty_precision)
        
        # 최종 notional 확인
        final_notional = quantity * current_price
        
        print(f"📋 계산 결과:")
        print(f"   계산된 수량: {quantity}")
        print(f"   최종 notional: {final_notional}")
        print(f"   최소 notional 만족: {'✅' if final_notional >= min_notional else '❌'}")
        
        # 주문 파라미터 생성
        params = {
            "symbol": symbol,
            "side": "BUY",
            "type": "MARKET",
            "quantity": str(quantity),
            "timestamp": server_time,
            "recvWindow": 5000
        }
        
        print(f"📋 주문 파라미터:")
        for key, value in params.items():
            print(f"   {key}: {value}")
        
        # 서명 생성
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # 요청 URL
        url = f"{base_url}/fapi/v1/order?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        print(f"🔗 요청 URL 생성 완료")
        print(f"⚠️ 실제 주문은 실행하지 않음 (테스트용)")
        
        # 결과 요약
        print("\n🎯 테스트 결과:")
        print("=" * 30)
        print(f"MIN_NOTIONAL 필드: {'✅' if min_notional > 0 else '❌'}")
        print(f"수량 계산: {'✅' if quantity > 0 else '❌'}")
        print(f"notional 만족: {'✅' if final_notional >= min_notional else '❌'}")
        print(f"정밀도 조정: {'✅' if qty_precision > 0 else '❌'}")
        
        if final_notional >= min_notional:
            print(f"✅ 주문 성공 가능! (notional: {final_notional:.2f} >= {min_notional:.2f})")
        else:
            print(f"❌ 주문 실패 예상 (notional: {final_notional:.2f} < {min_notional:.2f})")
        
        return {
            "success": final_notional >= min_notional,
            "quantity": quantity,
            "notional": final_notional,
            "min_notional": min_notional
        }
        
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        return None

if __name__ == "__main__":
    result = test_fixed_order()
    
    if result and result["success"]:
        print("\n🚀 수정 완료! 실제 주문 실행 가능!")
    else:
        print("\n⚠️ 추가 수정 필요!")
