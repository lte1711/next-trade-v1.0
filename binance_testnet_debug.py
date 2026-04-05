#!/usr/bin/env python3
"""
바이낸스 테스트넷 API 디버깅 - 실거래 실패 원인 분석
"""

import requests
import json
import hmac
import hashlib
import urllib.parse

class BinanceTestnetDebugger:
    def __init__(self):
        self.api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
        self.api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
        self.base_url = "https://testnet.binancefuture.com"
        
        print("🔍 바이낸스 테스트넷 API 디버깅 시작")
        print("=" * 80)
    
    def test_server_time(self):
        """서버 시간 테스트"""
        print("⏰ 서버 시간 테스트...")
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            if response.status_code == 200:
                server_time = response.json()["serverTime"]
                print(f"✅ 서버 시간: {server_time}")
                return server_time
            else:
                print(f"❌ 서버 시간 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 서버 시간 오류: {e}")
            return None
    
    def test_exchange_info(self):
        """거래소 정보 테스트"""
        print("📊 거래소 정보 테스트...")
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            if response.status_code == 200:
                exchange_info = response.json()
                print(f"✅ 거래소 정보: {len(exchange_info['symbols'])}개 심볼")
                
                # BTCUSDT 심볼 정보 확인
                for symbol_info in exchange_info["symbols"]:
                    if symbol_info["symbol"] == "BTCUSDT":
                        print(f"✅ BTCUSDT 상태: {symbol_info['status']}")
                        
                        # 필터 정보 확인
                        filters = symbol_info["filters"]
                        print(f"📋 필터 수: {len(filters)}")
                        
                        for f in filters:
                            filter_type = f["filterType"]
                            print(f"   {filter_type}: {f}")
                        
                        return symbol_info
                
                print("❌ BTCUSDT 심볼 정보 없음")
                return None
            else:
                print(f"❌ 거래소 정보 실패: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ 거래소 정보 오류: {e}")
            return None
    
    def test_account_info(self):
        """계정 정보 테스트"""
        print("💰 계정 정보 테스트...")
        try:
            server_time = self.test_server_time()
            if not server_time:
                return None
            
            params = {
                "timestamp": server_time,
                "recvWindow": 5000
            }
            
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v2/account?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                account_info = response.json()
                print(f"✅ 계정 정보:")
                print(f"   총 자산: {account_info['totalWalletBalance']} USDT")
                print(f"   사용 가능: {account_info['availableBalance']} USDT")
                print(f"   포지션 수: {len(account_info['positions'])}")
                
                # 포지션 정보 확인
                for position in account_info['positions']:
                    if position['positionAmt'] != '0':
                        print(f"   포지션: {position['symbol']} {position['positionAmt']}")
                
                return account_info
            else:
                print(f"❌ 계정 정보 실패: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ 계정 정보 오류: {e}")
            return None
    
    def test_symbol_info(self, symbol="BTCUSDT"):
        """심볼 정보 테스트"""
        print(f"📊 {symbol} 심볼 정보 테스트...")
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            if response.status_code == 200:
                exchange_info = response.json()
                
                for symbol_info in exchange_info["symbols"]:
                    if symbol_info["symbol"] == symbol:
                        print(f"✅ {symbol} 심볼 정보:")
                        print(f"   상태: {symbol_info['status']}")
                        print(f"   기본 가격 정밀도: {symbol_info['pricePrecision']}")
                        print(f"   기본 수량 정밀도: {symbol_info['quantityPrecision']}")
                        
                        # 필터 정보 상세 확인
                        filters = symbol_info["filters"]
                        print(f"   필터 정보:")
                        
                        for f in filters:
                            filter_type = f["filterType"]
                            print(f"     {filter_type}:")
                            for key, value in f.items():
                                if key != "filterType":
                                    print(f"       {key}: {value}")
                        
                        return symbol_info
                
                print(f"❌ {symbol} 심볼 정보 없음")
                return None
            else:
                print(f"❌ 심볼 정보 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 심볼 정보 오류: {e}")
            return None
    
    def test_order_book(self, symbol="BTCUSDT"):
        """오더북 테스트"""
        print(f"📚 {symbol} 오더북 테스트...")
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/depth?symbol={symbol}&limit=5", timeout=10)
            if response.status_code == 200:
                order_book = response.json()
                print(f"✅ {symbol} 오더북:")
                print(f"   최고 매수가: {order_book['bids'][0][0]}")
                print(f"   최고 매도가: {order_book['asks'][0][0]}")
                return order_book
            else:
                print(f"❌ 오더북 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 오더북 오류: {e}")
            return None
    
    def test_sample_order(self, symbol="BTCUSDT"):
        """샘플 주문 테스트 (가격 확인용)"""
        print(f"🧪 {symbol} 샘플 주문 테스트...")
        try:
            server_time = self.test_server_time()
            if not server_time:
                return None
            
            # 최소 수량 계산
            symbol_info = self.test_symbol_info(symbol)
            if not symbol_info:
                return None
            
            # 필터 정보 추출
            filters = symbol_info["filters"]
            min_qty = 0.0
            min_notional = 0.0
            qty_precision = 0
            
            for f in filters:
                if f["filterType"] == "LOT_SIZE":
                    min_qty = float(f["minQty"])
                    if "stepQty" in f and "." in f["stepQty"]:
                        qty_precision = len(f["stepQty"].split('.')[1])
                    else:
                        qty_precision = 8
                elif f["filterType"] == "MIN_NOTIONAL":
                    if "minNotional" in f:
                        min_notional = float(f["minNotional"])
                    else:
                        min_notional = 10.0
            
            print(f"📋 주문 파라미터:")
            print(f"   최소 수량: {min_qty}")
            print(f"   최소 notional: {min_notional}")
            print(f"   수량 정밀도: {qty_precision}")
            
            # 현재 가격 확인
            order_book = self.test_order_book(symbol)
            if not order_book:
                return None
            
            current_price = float(order_book['asks'][0][0])
            print(f"   현재 가격: {current_price}")
            
            # 최소 수량으로 notional 계산
            min_notional_from_qty = min_qty * current_price
            print(f"   최소 수량 notional: {min_notional_from_qty}")
            
            # 필요한 최소 수량 계산
            if min_notional > 0:
                required_qty = min_notional / current_price
                print(f"   필요한 최소 수량: {required_qty}")
                
                if required_qty > min_qty:
                    final_qty = required_qty
                else:
                    final_qty = min_qty
            else:
                final_qty = min_qty
            
            # 수량 정밀도 조정
            final_qty = round(final_qty, qty_precision)
            print(f"   최종 수량: {final_qty}")
            
            # 파라미터 생성
            params = {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quantity": str(final_qty),
                "timestamp": server_time,
                "recvWindow": 5000
            }
            
            print(f"📋 주문 파라미터:")
            for key, value in params.items():
                print(f"   {key}: {value}")
            
            # 서명 생성
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            # 요청 URL
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            print(f"🔗 요청 URL: {url}")
            
            # 실제 주문은 실행하지 않고 파라미터만 확인
            print("⚠️ 실제 주문은 실행하지 않음 (디버깅용)")
            
            return {
                "params": params,
                "url": url,
                "final_qty": final_qty,
                "min_qty": min_qty,
                "min_notional": min_notional
            }
            
        except Exception as e:
            print(f"❌ 샘플 주문 오류: {e}")
            return None
    
    def run_debug_tests(self):
        """전체 디버깅 테스트 실행"""
        print("🔍 전체 디버깅 테스트 시작")
        print("=" * 80)
        
        # 1. 서버 시간 테스트
        server_time = self.test_server_time()
        print("")
        
        # 2. 거래소 정보 테스트
        exchange_info = self.test_exchange_info()
        print("")
        
        # 3. 계정 정보 테스트
        account_info = self.test_account_info()
        print("")
        
        # 4. 심볼 정보 테스트
        symbol_info = self.test_symbol_info("BTCUSDT")
        print("")
        
        # 5. 오더북 테스트
        order_book = self.test_order_book("BTCUSDT")
        print("")
        
        # 6. 샘플 주문 테스트
        order_params = self.test_sample_order("BTCUSDT")
        print("")
        
        # 결과 요약
        print("🎯 디버깅 결과 요약:")
        print("=" * 50)
        print(f"서버 시간: {'✅' if server_time else '❌'}")
        print(f"거래소 정보: {'✅' if exchange_info else '❌'}")
        print(f"계정 정보: {'✅' if account_info else '❌'}")
        print(f"심볼 정보: {'✅' if symbol_info else '❌'}")
        print(f"오더북: {'✅' if order_book else '❌'}")
        print(f"주문 파라미터: {'✅' if order_params else '❌'}")
        
        if account_info:
            print(f"계정 잔고: {account_info['totalWalletBalance']} USDT")
        
        if order_params:
            print(f"최소 수량: {order_params['min_qty']}")
            print(f"최소 notional: {order_params['min_notional']}")
            print(f"최종 수량: {order_params['final_qty']}")

if __name__ == "__main__":
    debugger = BinanceTestnetDebugger()
    debugger.run_debug_tests()
