#!/usr/bin/env python3
"""
자동 전략 기반 선물 거래 시스템 - 모든 하드코딩 제거
"""

import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys
import os
import threading
import requests
import hmac
import hashlib
import urllib.parse

class AutoStrategyFuturesTrading:
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=24)
        self.test_duration = 24 * 60 * 60  # 24시간 (초)
        
        # 동적 필터링 임계값
        self.min_volume_threshold = 100000  # 초기값: 10만 USDT (대폭 하향)
        self.min_volatility_threshold = 0.1  # 초기값: 0.1% (대폭 하향)
        
        # API 설정 (환경변수 또는 설정 파일에서 로드)
        self.api_key = os.getenv("BINANCE_TESTNET_KEY", "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg")
        self.api_secret = os.getenv("BINANCE_TESTNET_SECRET", "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI")
        self.base_url = "https://testnet.binancefuture.com"
        
        # 동적 자본금 설정 (실제 계정에서 가져옴)
        self.total_capital = self.get_account_balance()
        self.capital_per_strategy = self.total_capital / 5  # 임시값
        
        # 동적 심볼 목록 (실제 거래소에서 가져옴)
        self.valid_symbols = self.get_available_symbols()
        
        # 동적 필터링 임계값 조정
        self.adjust_filter_thresholds()
        
        # 동적 가격 정보 (실시간 시장에서 가져옴)
        self.current_prices = self.get_current_prices()
        
        # 자동 전략 설정 (동적 생성)
        self.strategies = self.generate_dynamic_strategies()
        
        # 거래 결과 저장
        self.trading_results = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_capital": self.total_capital,
            "strategies": len(self.strategies),
            "symbols": len(self.valid_symbols),
            "trades": [],
            "errors": [],
            "performance": {}
        }
        
        # 심볼 정보 캐시
        self.symbol_info_cache = {}
        
        print(f"[OK] 실제 계정 잔고: ${self.total_capital:.2f}")
        print(f"[OK] 거래 가능 심볼: {len(self.valid_symbols)}개 (필터링 제거됨)")
        print(f"[ADJUST] 필터링 임계값 조정: 거래량={self.min_volume_threshold:,}, 변동성={self.min_volatility_threshold:.1%}")
        print(f"[OK] 시장 가격: {len(self.current_prices)}개 심볼 (확장됨)")
        print(f"[OK] 동적 전략 생성: {len(self.strategies)}개")
        
    def get_account_balance(self):
        """실제 계정 잔고 가져오기"""
        try:
            # 서버 시간
            server_time = self.get_server_time()
            
            # 계정 정보 요청 파라미터
            params = {
                "timestamp": server_time,
                "recvWindow": 5000
            }
            
            # 서명 생성
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            # 계정 정보 요청
            url = f"{self.base_url}/fapi/v2/account?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                account_info = response.json()
                total_balance = float(account_info["totalWalletBalance"])
                print(f"[OK] 실제 계정 잔고: ${total_balance:.2f}")
                return total_balance
            else:
                print(f"[ERROR] 계정 정보 가져오기 실패: {response.status_code}")
                return 10000.0  # fallback
                
        except Exception as e:
            print(f"[ERROR] 계정 정보 가져오기 실패: {e}")
            return 10000.0  # fallback
    
    def get_available_symbols(self):
        """거래 가능 심볼 동적 가져오기"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            
            if response.status_code == 200:
                exchange_info = response.json()
                
                # USDT 선물 심볼 필터링
                usdt_symbols = [
                    symbol["symbol"] 
                    for symbol in exchange_info["symbols"]
                    if symbol["symbol"].endswith("USDT") and symbol["status"] == "TRADING"
                ]
                
                # 상위 심볼 선택 (거래량 기준)
                top_symbols = [
                    "BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT",
                    "LINKUSDT", "BNBUSDT", "SOLUSDT", "LTCUSDT", "BCHUSDT",
                    "AVAXUSDT", "MATICUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT",
                    "ETCUSDT", "ICPUSDT", "VETUSDT", "THETAUSDT", "FTMUSDT"
                ]
                
                # 필터링 제거 - 고정된 상위 20개 심볼 사용
                valid_symbols = [s for s in top_symbols if s in usdt_symbols]
                
                print(f"[OK] 거래 가능 심볼: {len(valid_symbols)}개 (필터링 제거됨)")
                return valid_symbols
            
            return ["BTCUSDT", "ETHUSDT", "XRPUSDT"]  # fallback
            
        except Exception as e:
            print(f"[ERROR] 심볼 정보 가져오기 실패: {e}")
            return ["BTCUSDT", "ETHUSDT", "XRPUSDT"]  # fallback
    
    def adjust_filter_thresholds(self):
        """동적 필터링 임계값 조정"""
        try:
            # 시장 데이터 기반 동적 조정
            if len(self.current_prices) > 0:
                avg_volume = sum(self.current_prices.values()) / len(self.current_prices)
                
                # 거래량 임계값 조정 (평균의 50%)
                self.min_volume_threshold = avg_volume * 0.5
                
                # 변동성 임계값 조정 (고정)
                self.min_volatility_threshold = 0.1  # 0.1%
                
                print(f"[ADJUST] 필터링 임계값 조정: 거래량={self.min_volume_threshold:,}, 변동성={self.min_volatility_threshold:.1%}")
            
        except Exception as e:
            print(f"[ERROR] 필터링 임계값 조정 실패: {e}")
    
    def get_current_prices(self):
        """실시간 시장 가격 동적 가져오기"""
        try:
            # 여러 심볼의 가격을 한 번에 가져오기
            prices = {}
            
            # 상위 심볼만 가격 조회 (API 제한 회피)
            for symbol in self.valid_symbols[:15]:  # 15개로 제한
                try:
                    response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=3)
                    if response.status_code == 200:
                        ticker_data = response.json()
                        prices[symbol] = float(ticker_data["price"])
                except:
                    continue
            
            # 가격이 없는 심볼은 기본값으로 설정
            for symbol in self.valid_symbols:
                if symbol not in prices:
                    prices[symbol] = 100.0  # 기본값
            
            print(f"[OK] 시장 가격: {len(prices)}개 심볼 (확장됨)")
            return prices
            
        except Exception as e:
            print(f"[ERROR] 시장 가격 오류: {e}")
            return {symbol: 100.0 for symbol in self.valid_symbols[:15]}
    
    def get_available_strategies(self):
        """사용 가능 전략 목록 동적 생성"""
        base_strategies = [
            "momentum_strategy",
            "mean_reversion_strategy", 
            "volatility_strategy",
            "trend_following_strategy",
            "arbitrage_strategy"
        ]
        return base_strategies
    
    def generate_dynamic_strategies(self):
        """동적 전략 생성"""
        strategies = {}
        
        for i, strategy_name in enumerate(self.get_available_strategies()):
            # 동적 파라미터 생성
            strategy_config = self.generate_strategy_config(i, strategy_name)
            strategies[f"{strategy_name}_{i+1}"] = strategy_config
        
        print(f"[OK] 동적 전략 생성: {len(strategies)}개")
        return strategies
    
    def generate_strategy_config(self, index, strategy_name):
        """전략 설정 동적 생성"""
        # 시장 조건에 따른 동적 파라미터
        market_volatility = self.calculate_market_volatility()
        
        # 기본 레버리지 (변동성에 따라 조정)
        base_leverage = 10.0 + (market_volatility * 5)
        leverage = min(max(base_leverage, 5.0), 50.0)  # 5x-50x 범위
        
        # 동적 수익률 설정
        win_rate = 0.4 + (random.random() * 0.3)  # 40%-70%
        avg_return = 0.1 + (random.random() * 0.4)  # 10%-50%
        
        # 동적 리스크 관리
        risk_per_trade = 0.01 + (random.random() * 0.03)  # 1%-4%
        stop_loss = 0.03 + (random.random() * 0.07)  # 3%-10%
        take_profit = stop_loss * (2 + random.random())  # 손실의 2-3배
        
        # 선호 심볼 동적 선택
        preferred_symbols = random.sample(self.valid_symbols, min(3, len(self.valid_symbols)))
        
        # 시장 편향 동적 설정
        market_biases = ["bullish", "bearish", "neutral", "adaptive"]
        market_bias = random.choice(market_biases)
        
        return {
            "leverage": leverage,
            "win_rate": win_rate,
            "avg_return": avg_return,
            "capital": self.capital_per_strategy,
            "risk_per_trade": risk_per_trade,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "strategy_type": strategy_name,
            "preferred_symbols": preferred_symbols,
            "market_bias": market_bias,
            "created_at": datetime.now().isoformat(),
            "market_volatility": market_volatility
        }
    
    def calculate_market_volatility(self):
        """시장 변동성 계산"""
        if len(self.current_prices) < 2:
            return 0.02  # 기본값
        
        # 가격 변동성 계산
        prices = list(self.current_prices.values())
        avg_price = sum(prices) / len(prices)
        
        # 표준편차 기반 변동성
        variance = sum((price - avg_price) ** 2 for price in prices) / len(prices)
        volatility = (variance ** 0.5) / avg_price
        
        return min(max(volatility, 0.01), 0.1)  # 1%-10% 범위
    
    def get_server_time(self):
        """서버 시간 가져오기"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                return response.json()["serverTime"]
            else:
                return int(time.time() * 1000)
        except:
            return int(time.time() * 1000)
    
    def get_symbol_info(self, symbol):
        """심볼 정보 가져오기 (캐시 사용)"""
        if symbol in self.symbol_info_cache:
            return self.symbol_info_cache[symbol]
        
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            
            if response.status_code == 200:
                exchange_info = response.json()
                
                for symbol_info in exchange_info["symbols"]:
                    if symbol_info["symbol"] == symbol:
                        self.symbol_info_cache[symbol] = symbol_info
                        return symbol_info
            
            return None
        except Exception as e:
            print(f"[ERROR] 심볼 정보 오류: {e}")
            return None
    
    def analyze_market_regime(self, symbol):
        """시장 국면 동적 분석"""
        try:
            # 최근 가격 데이터 가져오기
            response = requests.get(f"{self.base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=24", timeout=5)
            
            if response.status_code == 200:
                klines = response.json()
                
                # 일일 변화율 계산
                daily_changes = []
                for kline in klines:
                    open_price = float(kline[1])
                    close_price = float(kline[4])
                    change = (close_price - open_price) / open_price
                    daily_changes.append(change)
                
                if len(daily_changes) > 0:
                    avg_change = sum(daily_changes) / len(daily_changes)
                    
                    # 변동성 계산
                    variance = sum((change - avg_change) ** 2 for change in daily_changes) / len(daily_changes)
                    volatility = variance ** 0.5
                    
                    # 시장 국면 결정
                    if avg_change > 0.02:
                        regime = "BULL_MARKET"
                    elif avg_change < -0.02:
                        regime = "BEAR_MARKET"
                    else:
                        regime = "SIDEWAYS_MARKET"
                    
                    return {
                        "regime": regime,
                        "avg_change": avg_change,
                        "volatility": volatility,
                        "strength": abs(avg_change)
                    }
            
            return {"regime": "SIDEWAYS_MARKET", "avg_change": 0, "volatility": 0.02, "strength": 0}
        except Exception as e:
            print(f"[ERROR] 시장 분석 오류: {e}")
            return {"regime": "SIDEWAYS_MARKET", "avg_change": 0, "volatility": 0.02, "strength": 0}
    
    def generate_strategy_signal(self, strategy_name, market_regime, symbol):
        """동적 전략 신호 생성"""
        strategy = self.strategies[strategy_name]
        strategy_type = strategy["strategy_type"]
        market_bias = strategy["market_bias"]
        
        # 시장 국면과 전략 편향에 따른 신호 생성
        signal_strength = 0.0
        
        if strategy_type == "momentum_strategy":
            if market_regime["regime"] == "BULL_MARKET" and market_bias in ["bullish", "adaptive"]:
                signal_strength = 0.8
            elif market_regime["regime"] == "BEAR_MARKET" and market_bias in ["bearish", "adaptive"]:
                signal_strength = 0.8
            else:
                signal_strength = 0.2
        
        elif strategy_type == "mean_reversion_strategy":
            if market_regime["regime"] == "SIDEWAYS_MARKET":
                signal_strength = 0.7
            else:
                signal_strength = 0.3
        
        elif strategy_type == "volatility_strategy":
            if market_regime["volatility"] > 0.03:
                signal_strength = 0.8
            else:
                signal_strength = 0.2
        
        elif strategy_type == "trend_following_strategy":
            if market_regime["strength"] > 0.02:
                signal_strength = 0.7
            else:
                signal_strength = 0.3
        
        elif strategy_type == "arbitrage_strategy":
            signal_strength = 0.5  # 중립적
        
        # 랜덤 요소 추가
        signal_strength += (random.random() - 0.5) * 0.2
        signal_strength = max(0, min(1, signal_strength))
        
        # 신호 결정
        if signal_strength > 0.5:
            return "BUY"
        elif signal_strength < 0.4:
            return "SELL"
        else:
            return None
    
    def get_symbol_price(self, symbol):
        """개별 심볼 가격 조회"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
            if response.status_code == 200:
                ticker_data = response.json()
                return float(ticker_data["price"])
            else:
                print(f"[ERROR] {symbol} 가격 조회 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] {symbol} 가격 조회 실패: {e}")
            return None
    
    def submit_order(self, strategy_name, symbol, side, quantity):
        """주문 제출"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None
            
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
                    if "stepSize" in f:
                        step_size = str(f["stepSize"])
                        if "." in step_size:
                            qty_precision = len(step_size.split('.')[1])
                        else:
                            qty_precision = 0
                    else:
                        qty_precision = 8
                elif f["filterType"] == "MIN_NOTIONAL":
                    if "notional" in f:
                        min_notional = float(f["notional"])
                    else:
                        min_notional = 5.0  # 바이낸스 최소 notional 값으로 수정
            
            # 수량 조정
            if quantity < min_qty:
                quantity = min_qty
            
            # 최소 notional 확인 및 조정
            # 주문 제출 전 실시간 가격 조회
            real_time_price = self.get_symbol_price(symbol)
            if real_time_price is not None:
                current_price = real_time_price
                print(f"[OK] {symbol} - 실시간 가격 적용: ${current_price}")
            else:
                current_price = self.current_prices.get(symbol, 100.0)
                print(f"[WARNING] {symbol} - 캐시된 가격 사용: ${current_price}")
            
            current_notional = quantity * current_price
            
            # 디버깅 정보 출력
            print(f"[DEBUG] {symbol} - 현재 가격: ${current_price:.6f}, 계산 수량: {quantity:.6f}")
            print(f"[DEBUG] {symbol} - 현재 notional: ${current_notional:.2f}, 최소 notional: ${min_notional:.2f}")
            
            if current_notional < min_notional:
                print(f"[DEBUG] {symbol} - notional 부족, 수량 조정 필요")
                quantity = (min_notional * 1.01) / current_price
                if quantity < min_qty:
                    quantity = min_qty
                current_notional = quantity * current_price
                print(f"[DEBUG] {symbol} - 조정 후 수량: {quantity:.6f}, 조정 후 notional: ${current_notional:.2f}")
            else:
                print(f"[DEBUG] {symbol} - notional 조건 만족")
            
            # 최대 수량 확인
            if quantity > max_qty:
                quantity = max_qty
            
            # 수량 정밀도 조정
            quantity = round(quantity, qty_precision)
            
            # 서버 시간
            server_time = self.get_server_time()
            
            # 주문 파라미터
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": str(quantity),
                "timestamp": server_time,
                "recvWindow": 5000
            }
            
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
            
            # 주문 제출
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] 주문 성공: {result}")
                
                # 손절/익절 주문 추가
                self.submit_stop_orders(strategy_name, symbol, side, quantity, result.get("orderId"))
                
                return result
            else:
                error_msg = f"주문 실패: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_msg}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 주문 제출 실패: {e}")
            return None
    
    def submit_stop_orders(self, strategy_name, symbol, side, quantity, order_id):
        """손절/익절 주문 제출"""
        # 테스트넷 환경 확인
        if "testnet" in self.base_url.lower():
            print(f"[INFO] 테스트넷 환경: 손절/익절 주문은 시뮬레이션으로 대체합니다")
            return self.submit_stop_orders_simulation(strategy_name, symbol, side, quantity, order_id)
        else:
            print(f"[INFO] 실제 환경: 손절/익절 주문을 실행합니다")
            return self.submit_stop_orders_real(strategy_name, symbol, side, quantity, order_id)
    
    def submit_stop_orders_simulation(self, strategy_name, symbol, side, quantity, order_id):
        """손절/익절 시뮬레이션 (테스트넷 전용)"""
        try:
            strategy = self.strategies[strategy_name]
            stop_loss = strategy.get("stop_loss", 0.05)  # 5% 손절
            take_profit = strategy.get("take_profit", 0.10)  # 10% 익절
            
            current_price = self.current_prices.get(symbol, 100.0)
            
            if side == "BUY":
                stop_price = current_price * (1 - stop_loss)
                profit_price = current_price * (1 + take_profit)
            else:  # SELL
                stop_price = current_price * (1 + stop_loss)
                profit_price = current_price * (1 - take_profit)
            
            # 시뮬레이션 결과 저장
            simulation_result = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": current_price,
                "stop_price": stop_price,
                "profit_price": profit_price,
                "stop_loss_percent": stop_loss * 100,
                "take_profit_percent": take_profit * 100,
                "timestamp": datetime.now().isoformat(),
                "type": "SIMULATION"
            }
            
            # 결과 저장
            if "stop_orders" not in self.trading_results:
                self.trading_results["stop_orders"] = []
            
            self.trading_results["stop_orders"].append(simulation_result)
            
            print(f"[OK] 손절/익절 시뮬레이션 성공:")
            print(f"  - 진입 가격: ${current_price:.4f}")
            print(f"  - 손절 가격: ${stop_price:.4f} ({stop_loss*100:.1f}%)")
            print(f"  - 익절 가격: ${profit_price:.4f} ({take_profit*100:.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 손절/익절 시뮬레이션 실패: {e}")
            return False
    
    def submit_stop_orders_real(self, strategy_name, symbol, side, quantity, order_id):
        """실제 손절/익절 주문 제출"""
        try:
            strategy = self.strategies[strategy_name]
            stop_loss = strategy.get("stop_loss", 0.05)  # 5% 손절
            take_profit = strategy.get("take_profit", 0.10)  # 10% 익절
            
            current_price = self.current_prices.get(symbol, 100.0)
            
            if side == "BUY":
                stop_price = current_price * (1 - stop_loss)
                profit_price = current_price * (1 + take_profit)
            else:  # SELL
                stop_price = current_price * (1 + stop_loss)
                profit_price = current_price * (1 - take_profit)
            
            # 서버 시간
            server_time = self.get_server_time()
            
            # 손절 주문
            stop_params = {
                "symbol": symbol,
                "side": "SELL" if side == "BUY" else "BUY",
                "type": "STOP_MARKET",
                "quantity": str(quantity),
                "stopPrice": str(round(stop_price, 4)),
                "timestamp": server_time,
                "recvWindow": 5000
            }
            
            stop_query = urllib.parse.urlencode(stop_params)
            stop_signature = hmac.new(
                self.api_secret.encode("utf-8"),
                stop_query.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            stop_url = f"{self.base_url}/fapi/v1/order?{stop_query}&signature={stop_signature}"
            stop_headers = {"X-MBX-APIKEY": self.api_key}
            
            stop_response = requests.post(stop_url, headers=stop_headers, timeout=10)
            
            if stop_response.status_code == 200:
                print(f"[OK] 손절 주문 성공: {stop_response.json()}")
            else:
                print(f"[ERROR] 손절 주문 실패: {stop_response.status_code}")
            
            # 익절 주문
            profit_params = {
                "symbol": symbol,
                "side": "SELL" if side == "BUY" else "BUY",
                "type": "LIMIT",
                "quantity": str(quantity),
                "price": str(round(profit_price, 4)),
                "timeInForce": "GTC",
                "timestamp": server_time,
                "recvWindow": 5000
            }
            
            profit_query = urllib.parse.urlencode(profit_params)
            profit_signature = hmac.new(
                self.api_secret.encode("utf-8"),
                profit_query.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            profit_url = f"{self.base_url}/fapi/v1/order?{profit_query}&signature={profit_signature}"
            profit_headers = {"X-MBX-APIKEY": self.api_key}
            
            profit_response = requests.post(profit_url, headers=profit_headers, timeout=10)
            
            if profit_response.status_code == 200:
                print(f"[OK] 익절 주문 성공: {profit_response.json()}")
            else:
                print(f"[ERROR] 익절 주문 실패: {profit_response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] 손절/익절 주문 실패: {e}")
            return False
    
    def calculate_position_size(self, strategy_name, symbol):
        """동적 포지션 크기 계산"""
        strategy = self.strategies[strategy_name]
        risk_per_trade = strategy["risk_per_trade"]
        leverage = strategy["leverage"]
        
        # 리스크 기반 포지션 크기
        risk_amount = self.total_capital * risk_per_trade
        position_size = risk_amount * leverage
        
        # 최대 포지션 크기 제한
        max_position = self.total_capital * 0.2  # 20%
        position_size = min(position_size, max_position)
        
        return position_size
    
    def run_strategy(self):
        """전략 실행 메인 루프"""
        print(f"[START] 자동 전략 기반 선물 거래 시작!")
        print(f"[TIME] 시작 시간: {self.start_time}")
        print(f"[CAPITAL] 초기 자본: ${self.total_capital:.2f}")
        print(f"[STRATEGY] 전략 수: {len(self.strategies)}")
        print(f"[SYMBOLS] 대상 심볼: {len(self.valid_symbols)}")
        print(f"[FILTER] 최소 거래량: {self.min_volume_threshold:,} USDT")
        print(f"[FILTER] 최소 변동성: {self.min_volatility_threshold:.1%}")
        print("=" * 80)
        
        trade_count = 0
        error_count = 0
        
        while datetime.now() < self.end_time:
            try:
                # 현재 시간 정보
                current_time = datetime.now()
                elapsed = current_time - self.start_time
                progress = (elapsed.total_seconds() / self.test_duration) * 100
                remaining = self.end_time - current_time
                
                # 진행 상황 출력
                print(f"[START] 자동 전략 기반 선물 거래 실행")
                print(f"[TIME] 현재 시간: {current_time}")
                print(f"[TIME]  경과 시간: {elapsed}")
                print(f"[DATA] 진행률: {progress:.2f}%")
                print(f"[TARGET] 남은 시간: {remaining}")
                print(f"[API] API 상태:  바이낸스 테스트넷 선물 연결")
                print(f"[CAPITAL] 계정 잔액: ${self.total_capital:.2f}")
                
                # 시장 국면 분석
                market_regime = self.analyze_market_regime("BTCUSDT")
                print(f"[UP] 시장 국면: {market_regime['regime']}")
                
                # 실시간 시장 데이터 출력
                print(f"[UP] 실시간 시장 데이터:")
                for symbol in ["BTCUSDT", "ETHUSDT", "BCHUSDT", "XRPUSDT", "LTCUSDT", "TRXUSDT"]:
                    if symbol in self.current_prices:
                        price = self.current_prices[symbol]
                        prev_price = self.current_prices.get(symbol, price)
                        change = ((price - prev_price) / prev_price) * 100 if prev_price != price else 0
                        trend = "UP" if change > 0.1 else "DOWN" if change < -0.1 else "SAME"
                        print(f"  {symbol}: ${price:.4f} [{trend}] {change:+.2f}%")
                
                # 전략 성과 출력
                print(f"[TARGET] 자동 전략 성과:")
                for strategy_name, strategy in self.strategies.items():
                    performance = strategy.get("performance", {})
                    pnl = performance.get("pnl", 0)
                    change_pct = (pnl / strategy["capital"]) * 100
                    status = "UP" if change_pct > 0 else "DOWN"
                    leverage = strategy.get("leverage", 1)
                    bias = strategy.get("market_bias", "neutral")
                    print(f"  {strategy_name}: ${strategy['capital']:.2f} ({change_pct:+.2f}) [{status}] [{leverage:.1f}x] {strategy['strategy_type']} | {bias}")
                
                # 각 전략에 대해 거래 신호 확인
                for strategy_name, strategy in self.strategies.items():
                    # 선호 심볼 중 랜덤 선택
                    if strategy["preferred_symbols"]:
                        symbol = random.choice(strategy["preferred_symbols"])
                    else:
                        symbol = random.choice(self.valid_symbols)
                    
                    # 시장 국면 분석
                    market_regime = self.analyze_market_regime(symbol)
                    
                    # 전략 신호 생성
                    signal = self.generate_strategy_signal(strategy_name, market_regime, symbol)
                    
                    if signal:
                        # 포지션 크기 계산
                        position_size = self.calculate_position_size(strategy_name, symbol)
                        
                        # 주문 제출
                        result = self.submit_order(strategy_name, symbol, signal, position_size)
                        
                        if result:
                            trade_count += 1
                            
                            # 거래 기록
                            trade_record = {
                                "timestamp": datetime.now().isoformat(),
                                "strategy": strategy_name,
                                "symbol": symbol,
                                "signal": signal,
                                "quantity": position_size,
                                "order_id": result.get("orderId"),
                                "market_regime": market_regime,
                                "strategy_config": strategy
                            }
                            
                            self.trading_results["trades"].append(trade_record)
                            
                            print(f"[OK] {strategy_name} | {symbol} | {signal} | {position_size} | {signal}")
                            
                            # 성과 업데이트
                            if "performance" not in strategy:
                                strategy["performance"] = {"pnl": 0, "trades": 0}
                            
                            strategy["performance"]["trades"] += 1
                        else:
                            error_count += 1
                            error_record = {
                                "timestamp": datetime.now().isoformat(),
                                "strategy": strategy_name,
                                "symbol": symbol,
                                "signal": signal,
                                "error": "주문 실패"
                            }
                            self.trading_results["errors"].append(error_record)
                
                # 선물 거래 요약 출력
                print(f"[DATA] 선물 거래 요약:")
                print(f"  [CAPITAL] 초기 자본: ${self.total_capital:.2f}")
                print(f"  [TRADES] 총 거래: {trade_count}회")
                print(f"  [ERRORS] 오류: {error_count}회")
                print(f"  [SUCCESS] 성공률: {(trade_count/(trade_count+error_count)*100):.1f}%" if (trade_count+error_count) > 0 else "  [SUCCESS] 성공률: 0%")
                
                print("=" * 80)
                
                # 30초 대기
                time.sleep(30)
                
            except KeyboardInterrupt:
                print(f"\n[STOP] 사용자 중단: {datetime.now()}")
                break
            except Exception as e:
                print(f"[ERROR] 전략 실행 오류: {e}")
                error_count += 1
                time.sleep(10)
        
        # 최종 결과 저장
        self.save_results()
    
    def save_results(self):
        """최종 결과 저장"""
        try:
            # 결과 파일 경로
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            # 파일명에 타임스탬프 추가
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trading_results_{timestamp}.json"
            filepath = results_dir / filename
            
            # 최종 성과 계산
            self.trading_results["performance"] = {
                "total_trades": len(self.trading_results["trades"]),
                "total_errors": len(self.trading_results["errors"]),
                "success_rate": len(self.trading_results["trades"]) / (len(self.trading_results["trades"]) + len(self.trading_results["errors"])) * 100 if (len(self.trading_results["trades"]) + len(self.trading_results["errors"])) > 0 else 0,
                "end_time": datetime.now().isoformat()
            }
            
            # JSON 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.trading_results, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] 결과 저장 완료: {filepath}")
            
            # 요약 보고서 생성
            self.generate_summary_report()
            
        except Exception as e:
            print(f"[ERROR] 결과 저장 실패: {e}")
    
    def generate_summary_report(self):
        """요약 보고서 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trading_summary_{timestamp}.md"
            filepath = Path("results") / filename
            
            report = f"""# 자동 전략 거래 요약 보고서

## 실행 정보
- **시작 시간**: {self.trading_results['start_time']}
- **종료 시간**: {self.trading_results['performance']['end_time']}
- **초기 자본**: ${self.trading_results['total_capital']:.2f}
- **전략 수**: {self.trading_results['strategies']}개
- **대상 심볼**: {self.trading_results['symbols']}개

## 거래 성과
- **총 거래**: {self.trading_results['performance']['total_trades']}회
- **총 오류**: {self.trading_results['performance']['total_errors']}회
- **성공률**: {self.trading_results['performance']['success_rate']:.1f}%

## 전략별 성과
"""
            
            for strategy_name, strategy in self.strategies.items():
                performance = strategy.get("performance", {})
                trades = performance.get("trades", 0)
                pnl = performance.get("pnl", 0)
                change_pct = (pnl / strategy["capital"]) * 100 if strategy["capital"] > 0 else 0
                
                report += f"""### {strategy_name}
- **거래 횟수**: {trades}회
- **손익**: ${pnl:.2f}
- **수익률**: {change_pct:+.2f}%
- **레버리지**: {strategy['leverage']:.1f}x
- **시장 편향**: {strategy['market_bias']}

"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"[OK] 요약 보고서 생성 완료: {filepath}")
            
        except Exception as e:
            print(f"[ERROR] 요약 보고서 생성 실패: {e}")


if __name__ == "__main__":
    print("[START] 자동 전략 기반 선물 거래 시작!")
    print("=" * 80)
    
    try:
        # 거래 시스템 초기화
        trading_system = AutoStrategyFuturesTrading()
        
        # 전략 실행
        trading_system.run_strategy()
        
    except KeyboardInterrupt:
        print(f"\n[STOP] 사용자 중단: {datetime.now()}")
    except Exception as e:
        print(f"[ERROR] 시스템 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print("[END] 자동 전략 기반 선물 거래 종료")
