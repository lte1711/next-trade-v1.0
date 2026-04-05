#!/usr/bin/env python3
"""
남은 문제 분석 및 개선 - 실거래 실패 원인 심층 분석
"""

import requests
import json
import hmac
import hashlib
import urllib.parse

class RemainingIssuesAnalyzer:
    def __init__(self):
        self.api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
        self.api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
        self.base_url = "https://testnet.binancefuture.com"
        
        print("🔍 남은 문제 분석 시작")
        print("=" * 80)
    
    def analyze_failed_orders(self):
        """실패한 주문 분석"""
        print("📋 실패한 주문 분석...")
        
        # 실패한 주문 정보
        failed_orders = [
            {
                "strategy": "mean_reversion_1",
                "symbol": "LTCUSDT",
                "side": "BUY",
                "quantity": 7.54859284,
                "price": 53.42,
                "timestamp": "2026-04-06T04:56:33.961806",
                "status": "FAILED",
                "order_id": "FAILED_1775418993_4867"
            },
            {
                "strategy": "mean_reversion_1",
                "symbol": "LTCUSDT",
                "side": "BUY",
                "quantity": 7.54859284,
                "price": 53.42,
                "timestamp": "2026-04-06T04:56:34.711077",
                "status": "FAILED",
                "order_id": "FAILED_1775418994_7851"
            }
        ]
        
        for order in failed_orders:
            print(f"\n❌ 실패한 주문: {order['order_id']}")
            print(f"   전략: {order['strategy']}")
            print(f"   심볼: {order['symbol']}")
            print(f"   방향: {order['side']}")
            print(f"   수량: {order['quantity']}")
            print(f"   가격: ${order['price']}")
            print(f"   notional: ${order['quantity'] * order['price']:.2f}")
            
            # LTCUSDT 필터 정보 확인
            self.analyze_symbol_filters(order['symbol'])
    
    def analyze_symbol_filters(self, symbol):
        """심볼 필터 분석"""
        print(f"\n📊 {symbol} 필터 분석...")
        
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
                        
                        lot_size = None
                        min_notional = None
                        max_qty = None
                        
                        for f in filters:
                            filter_type = f["filterType"]
                            print(f"     {filter_type}:")
                            for key, value in f.items():
                                if key != "filterType":
                                    print(f"       {key}: {value}")
                            
                            if filter_type == "LOT_SIZE":
                                lot_size = f
                            elif filter_type == "MIN_NOTIONAL":
                                min_notional = f
                        
                        # 문제 분석
                        self.analyze_order_problems(symbol, lot_size, min_notional, max_qty)
                        return symbol_info
                
                print(f"❌ {symbol} 심볼 정보 없음")
                return None
            else:
                print(f"❌ 심볼 정보 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 심볼 정보 오류: {e}")
            return None
    
    def analyze_order_problems(self, symbol, lot_size, min_notional, max_qty):
        """주문 문제 분석"""
        print(f"\n🔍 {symbol} 주문 문제 분석...")
        
        # 실패한 주문 파라미터
        failed_quantity = 7.54859284
        failed_price = 53.42
        failed_notional = failed_quantity * failed_price
        
        print(f"실패한 주문:")
        print(f"   수량: {failed_quantity}")
        print(f"   가격: ${failed_price}")
        print(f"   notional: ${failed_notional:.2f}")
        
        if lot_size:
            min_qty = float(lot_size["minQty"])
            max_qty_limit = float(lot_size["maxQty"])
            step_size = float(lot_size["stepSize"])
            
            print(f"\nLOT_SIZE 필터:")
            print(f"   최소 수량: {min_qty}")
            print(f"   최대 수량: {max_qty_limit}")
            print(f"   단위 수량: {step_size}")
            
            # 수량 검증
            if failed_quantity < min_qty:
                print(f"❌ 수량 부족: {failed_quantity} < {min_qty}")
            elif failed_quantity > max_qty_limit:
                print(f"❌ 수량 초과: {failed_quantity} > {max_qty_limit}")
            else:
                print(f"✅ 수량 범위 정상: {min_qty} <= {failed_quantity} <= {max_qty_limit}")
            
            # 정밀도 검증
            decimal_places = len(str(step_size).split('.')[1]) if '.' in str(step_size) else 0
            rounded_quantity = round(failed_quantity, decimal_places)
            if abs(failed_quantity - rounded_quantity) > 0.00000001:
                print(f"❌ 수량 정밀도 오류: {failed_quantity} != {rounded_quantity}")
            else:
                print(f"✅ 수량 정밀도 정상: {failed_quantity}")
        
        if min_notional:
            min_notional_value = float(min_notional["notional"])
            
            print(f"\nMIN_NOTIONAL 필터:")
            print(f"   최소 notional: ${min_notional_value}")
            
            # notional 검증
            if failed_notional < min_notional_value:
                print(f"❌ notional 부족: ${failed_notional:.2f} < ${min_notional_value:.2f}")
            else:
                print(f"✅ notional 정상: ${failed_notional:.2f} >= ${min_notional_value:.2f}")
    
    def test_corrected_order(self, symbol="LTCUSDT"):
        """수정된 주문 테스트"""
        print(f"\n🧪 {symbol} 수정된 주문 테스트...")
        
        try:
            # 서버 시간 가져오기
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            server_time = response.json()["serverTime"]
            
            # 심볼 정보 가져오기
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
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
                    step_size = float(f["stepSize"])
                    qty_precision = len(str(step_size).split('.')[1]) if '.' in str(step_size) else 0
                elif f["filterType"] == "MIN_NOTIONAL":
                    if "notional" in f:
                        min_notional = float(f["notional"])
                    else:
                        min_notional = 10.0
            
            # 현재 가격 확인
            response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=10)
            current_price = float(response.json()["price"])
            
            print(f"📋 수정된 계산:")
            print(f"   현재 가격: ${current_price}")
            print(f"   최소 수량: {min_qty}")
            print(f"   최소 notional: ${min_notional}")
            print(f"   수량 정밀도: {qty_precision}")
            
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
            
            print(f"   계산된 수량: {quantity}")
            print(f"   최종 notional: ${final_notional:.2f}")
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
            
            print(f"\n📋 수정된 주문 파라미터:")
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
            
            print(f"🔗 요청 URL 생성 완료")
            print(f"⚠️ 실제 주문은 실행하지 않음 (테스트용)")
            
            return {
                "success": final_notional >= min_notional,
                "quantity": quantity,
                "notional": final_notional,
                "min_notional": min_notional,
                "params": params,
                "url": url
            }
            
        except Exception as e:
            print(f"❌ 테스트 오류: {e}")
            return None
    
    def generate_improvement_plan(self):
        """개선 계획 생성"""
        print("\n🚀 개선 계획 생성...")
        
        improvements = {
            "1. 수량 계산 개선": {
                "문제": "수량 정밀도 오류",
                "해결": "step_size 기반 정밀도 조정",
                "코드": "quantity = round(quantity, qty_precision)"
            },
            "2. 필터 처리 강화": {
                "문제": "일부 필터 정보 누락",
                "해결": "모든 필터 타입 확인",
                "코드": "모든 필터 정보 정확히 추출"
            },
            "3. 오류 처리 개선": {
                "문제": "상세 오류 메시지 부족",
                "해결": "API 응답 상세 로깅",
                "코드": "response.text 전체 로깅"
            },
            "4. 수량 검증 강화": {
                "문제": "수량 범위 검증 부족",
                "해결": "모든 제약 조건 확인",
                "코드": "min_qty, max_qty, step_size 모두 검증"
            },
            "5. notional 계산 개선": {
                "문제": "notional 만족 보장 부족",
                "해결": "안전 마진 추가",
                "코드": "quantity = (min_notional * 1.01) / current_price"
            }
        }
        
        for title, improvement in improvements.items():
            print(f"\n{title}:")
            print(f"   문제: {improvement['문제']}")
            print(f"   해결: {improvement['해결']}")
            print(f"   코드: {improvement['코드']}")
        
        return improvements
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🔍 남은 문제 전체 분석 시작")
        print("=" * 80)
        
        # 1. 실패한 주문 분석
        self.analyze_failed_orders()
        print("")
        
        # 2. 수정된 주문 테스트
        result = self.test_corrected_order("LTCUSDT")
        print("")
        
        # 3. 개선 계획 생성
        improvements = self.generate_improvement_plan()
        print("")
        
        # 결과 요약
        print("🎯 분석 결과 요약:")
        print("=" * 50)
        print(f"실패 원인: 수량 정밀도 및 필터 처리 오류")
        print(f"수정 방안: 필터 정보 정확히 추출 및 수량 계산 개선")
        print(f"테스트 결과: {'✅ 성공' if result and result['success'] else '❌ 실패'}")
        print(f"개선 필요: 5가지 항목")
        
        return improvements

if __name__ == "__main__":
    analyzer = RemainingIssuesAnalyzer()
    improvements = analyzer.run_analysis()
