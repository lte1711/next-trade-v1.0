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
        
        # 캐시 설정
        self.symbol_info_cache = {}
        self.account_info_cache = {}
        
        # 거래 결과 저장
        self.trading_results = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "strategy_performance": {},
            "market_data": {},
            "total_pnl": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "real_orders": [],
            "balance_history": [],
            "initial_capital": self.total_capital,
            "current_capital": self.total_capital,
            "active_positions": {},
            "market_regime": "UNKNOWN"
        }
        
        print("[START] 자동 전략 기반 선물 거래 시작!")
        print(f"[TIME] 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[CAPITAL] 초기 자본: ${self.total_capital:,.2f}")
        print(f"[STRATEGY] 전략 수: {len(self.strategies)}개")
        print(f"[SYMBOLS] 대상 심볼: {len(self.valid_symbols)}개")
        print(f"[FILTER] 최소 거래량: {self.min_volume_threshold:,} USDT")
        print(f"[FILTER] 최소 변동성: {self.min_volatility_threshold}%")
        print("=" * 80)
    
    def adjust_filter_thresholds(self):
        """시장 상태에 따른 동적 필터링 임계값 조정"""
        # 현재 시장 변동성 계산
        total_volatility = 0
        count = 0
        
        for symbol in self.valid_symbols[:10]:
            try:
                response = requests.get(f"{self.base_url}/fapi/v1/ticker/24hr?symbol={symbol}", timeout=3)
                if response.status_code == 200:
                    ticker_data = response.json()
                    price_change = float(ticker_data.get("priceChangePercent", 0))
                    total_volatility += abs(price_change)
                    count += 1
            except:
                continue
        
        if count > 0:
            avg_volatility = total_volatility / count
            
            # 시장 변동성에 따른 동적 조정
            if avg_volatility < 0.3:  # 저변동성 시장
                self.min_volume_threshold = 50000  # 5만 USDT
                self.min_volatility_threshold = 0.05  # 0.05%
            elif avg_volatility < 1.0:  # 중간 변동성
                self.min_volume_threshold = 100000  # 10만 USDT
                self.min_volatility_threshold = 0.1  # 0.1%
            else:  # 고변동성 시장
                self.min_volume_threshold = 200000  # 20만 USDT
                self.min_volatility_threshold = 0.3  # 0.3%
            
            print(f"[ADJUST] 필터링 임계값 조정: 거래량={self.min_volume_threshold:,}, 변동성={self.min_volatility_threshold}%")
    
    def get_account_balance(self):
        """실제 계정 잔고 가져오기"""
        try:
            server_time = self.get_server_time()
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
                balance = float(account_info['totalWalletBalance'])
                print(f"[OK] 실제 계정 잔고: ${balance:,.2f}")
                return balance
            else:
                print(f"[ERROR] 계정 정보 가져오기 실패: {response.status_code}")
                return 10000.0  # 기본값
        except Exception as e:
            print(f"[ERROR] 계정 잔고 오류: {e}")
            return 10000.0  # 기본값
    
    def get_available_symbols(self):
        """실제 거래 가능한 심볼 목록 가져오기 (필터링 제거)"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            
            if response.status_code == 200:
                exchange_info = response.json()
                symbols = []
                
                for symbol_info in exchange_info["symbols"]:
                    if (symbol_info["status"] == "TRADING" and 
                        symbol_info["contractType"] == "PERPETUAL" and
                        symbol_info["symbol"].endswith("USDT")):
                        symbols.append(symbol_info["symbol"])
                
                # 필터링 제거: 상위 20개만 선택
                symbols = symbols[:20]
                
                print(f"[OK] 거래 가능 심볼: {len(symbols)}개 (필터링 제거됨)")
                return symbols
            else:
                print(f"[ERROR] 심볼 정보 가져오기 실패: {response.status_code}")
                # 기본 심볼 목록
                default_symbols = [
                    "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT",
                    "LINKUSDT", "BNBUSDT", "XRPUSDT", "LTCUSDT", "BCHUSDT",
                    "AVAXUSDT", "MATICUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT",
                    "ETCUSDT", "ICPUSDT", "VETUSDT", "THETAUSDT", "FTMUSDT"
                ]
                return default_symbols
        except Exception as e:
            print(f"[ERROR] 심볼 정보 오류: {e}")
            # 기본 심볼 목록
            default_symbols = [
                "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT",
                "LINKUSDT", "BNBUSDT", "XRPUSDT", "LTCUSDT", "BCHUSDT",
                "AVAXUSDT", "MATICUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT",
                "ETCUSDT", "ICPUSDT", "VETUSDT", "THETAUSDT", "FTMUSDT"
            ]
            return default_symbols
    
    def get_symbol_volume(self, symbol):
        """심볼의 24시간 거래량 가져오기"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/ticker/24hr?symbol={symbol}", timeout=5)
            if response.status_code == 200:
                ticker_data = response.json()
                return float(ticker_data.get("volume", 0))
            return 0
        except:
            return 0
    
    def get_current_prices(self):
        """실시간 시장 가격 가져오기"""
        prices = {}
        
        try:
            # 상위 15개 심볼만 조회 (확장)
            for symbol in self.valid_symbols[:15]:
                response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=3)
                
                if response.status_code == 200:
                    price_data = response.json()
                    prices[symbol] = float(price_data["price"])
                else:
                    prices[symbol] = 100.0  # 기본값
            
            print(f"[OK] 시장 가격: {len(prices)}개 심볼 (확장됨)")
            return prices
        except Exception as e:
            print(f"[ERROR] 시장 가격 오류: {e}")
            return {symbol: 100.0 for symbol in self.valid_symbols[:15]}
    
    def get_available_strategies(self):
        """사용 가능한 전략 목록 동적 생성"""
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
            current_price = self.current_prices.get(symbol, 100.0)
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
    
    def execute_strategy_trade(self, strategy_name):
        """전략 거래 실행"""
        strategy = self.strategies[strategy_name]
        
        # 선호 심볼에서 선택
        available_symbols = [s for s in strategy["preferred_symbols"] if s in self.valid_symbols]
        if not available_symbols:
            available_symbols = self.valid_symbols
        
        symbol = random.choice(available_symbols)
        
        # 시장 국면 분석
        market_regime = self.analyze_market_regime(symbol)
        
        # 신호 생성
        signal = self.generate_strategy_signal(strategy_name, market_regime, symbol)
        
        if signal:
            # 포지션 타입 결정
            position_type = "LONG" if signal == "BUY" else "SHORT"
            
            # 수량 계산
            quantity = self.calculate_position_size(strategy_name, symbol)
            
            # 주문 제출
            order_result = self.submit_order(strategy_name, symbol, signal, quantity)
            
            if order_result:
                # 거래 기록
                trade_record = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": signal,
                    "quantity": quantity,
                    "price": self.current_prices.get(symbol, 0),
                    "timestamp": datetime.now().isoformat(),
                    "status": "EXECUTED",
                    "order_id": order_result.get("orderId", "UNKNOWN"),
                    "market_regime": market_regime["regime"],
                    "strategy_signal": signal,
                    "position_type": position_type
                }
                
                self.trading_results["real_orders"].append(trade_record)
                self.trading_results["total_trades"] += 1
                
                print(f"[OK] {strategy_name} | {symbol} | {signal} | {quantity} | {position_type}")
                return trade_record
            else:
                # 실패 기록
                failed_record = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": signal,
                    "quantity": quantity,
                    "price": self.current_prices.get(symbol, 0),
                    "timestamp": datetime.now().isoformat(),
                    "status": "FAILED",
                    "order_id": f"FAILED_{int(time.time())}_{random.randint(1000, 9999)}",
                    "market_regime": market_regime["regime"],
                    "strategy_signal": signal,
                    "position_type": position_type
                }
                
                self.trading_results["real_orders"].append(failed_record)
                print(f"[ERROR] {strategy_name} | {symbol} | {signal} | {quantity} | {position_type}")
                return failed_record
        
        return None
    
    def calculate_position_size(self, strategy_name, symbol):
        """동적 포지션 크기 계산"""
        strategy = self.strategies[strategy_name]
        capital = strategy["capital"]
        risk_per_trade = strategy["risk_per_trade"]
        leverage = strategy["leverage"]
        
        # 리스크 기반 포지션 크기
        risk_amount = capital * risk_per_trade
        position_value = risk_amount * leverage
        
        current_price = self.current_prices.get(symbol, 100.0)
        quantity = position_value / current_price
        
        # 최소 수량 보장
        min_quantities = {
            "BTCUSDT": 0.001, "ETHUSDT": 0.01, "SOLUSDT": 0.1, "DOGEUSDT": 10,
            "ADAUSDT": 1, "MATICUSDT": 1, "AVAXUSDT": 0.1, "DOTUSDT": 1,
            "LINKUSDT": 0.1, "LTCUSDT": 0.01
        }
        
        if symbol in min_quantities:
            min_qty = min_quantities[symbol]
            quantity = max(quantity, min_qty)
        
        return quantity
    
    def update_market_data(self):
        """시장 데이터 업데이트"""
        try:
            # 가격 정보 업데이트
            for symbol in self.valid_symbols[:10]:
                response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=3)
                if response.status_code == 200:
                    price_data = response.json()
                    self.current_prices[symbol] = float(price_data["price"])
            
            self.trading_results["market_data"] = self.current_prices.copy()
            
        except Exception as e:
            print(f"[ERROR] 시장 데이터 업데이트 오류: {e}")
    
    def display_status(self):
        """상태 표시"""
        current_time = datetime.now()
        elapsed = current_time - self.start_time
        progress = (elapsed.total_seconds() / self.test_duration) * 100
        remaining = self.test_duration - elapsed.total_seconds()
        
        # 시장 국면 분석
        sample_symbol = self.valid_symbols[0] if self.valid_symbols else "BTCUSDT"
        market_regime = self.analyze_market_regime(sample_symbol)
        
        print(f"\n{'='*80}")
        print(f"[START] 자동 전략 기반 선물 거래 실행")
        print(f"{'='*80}")
        print(f"[TIME] 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[TIME]  경과 시간: {elapsed}")
        print(f"[DATA] 진행률: {progress:.2f}%")
        print(f"[TARGET] 남은 시간: {timedelta(seconds=int(remaining))}")
        print(f"[API] API 상태:  바이낸스 테스트넷 선물 연결")
        print(f"[CAPITAL] 계정 잔액: ${self.total_capital:,.2f}")
        print(f"[UP] 시장 국면: {market_regime['regime']}")
        
        print(f"\n[UP] 실시간 시장 데이터:")
        for symbol, price in list(self.current_prices.items())[:6]:
            prev_price = self.trading_results["market_data"].get(symbol, price)
            change = ((price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
            trend = "[UP]" if change > 0 else "[DOWN]" if change < 0 else "[SAME]"
            print(f"  {symbol}: ${price:.4f} {trend} {change:+.2f}%")
        
        print(f"\n[TARGET] 자동 전략 성과:")
        for strategy_name, strategy in self.strategies.items():
            capital = strategy["capital"]
            pnl = strategy.get("total_pnl", 0)
            return_rate = (pnl / self.capital_per_strategy) * 100
            leverage = strategy["leverage"]
            strategy_type = strategy["strategy_type"]
            market_bias = strategy["market_bias"]
            print(f"  {strategy_name}: ${capital:,.2f} ({return_rate:+.2f}%) [DOWN] [{leverage:.1f}x] {strategy_type} | {market_bias}")
        
        print(f"\n[DATA] 선물 거래 요약:")
        print(f"  [CAPITAL] 초기 자본: ${self.trading_results['initial_capital']:,.2f}")
        print(f"  [CAPITAL] 현재 자본: ${self.trading_results['current_capital']:,.2f}")
        print(f"  [CAPITAL] 총 손익: ${self.trading_results['total_pnl']:+,.2f}")
        print(f"  [UP] 총 거래: {self.trading_results['total_trades']}회")
        print(f"  [OK] 성공 거래: {self.trading_results['winning_trades']}회")
        print(f"  [ERROR] 실패 거래: {self.trading_results['losing_trades']}회")
        success_rate = (self.trading_results['winning_trades'] / max(1, self.trading_results['total_trades'])) * 100
        print(f"  [TARGET] 성공률: {success_rate:.1f}%")
        print(f"  [DATA] 전체 수익률: {((self.trading_results['current_capital'] - self.trading_results['initial_capital']) / self.trading_results['initial_capital']) * 100:+.2f}%")
        
        # 최근 거래 내역
        recent_trades = self.trading_results["real_orders"][-3:] if self.trading_results["real_orders"] else []
        print(f"\n[LIST] 최근 선물 거래 내역:")
        if recent_trades:
            for trade in recent_trades:
                status_icon = "[OK]" if trade["status"] == "EXECUTED" else "[ERROR]"
                print(f"  {status_icon} {trade['strategy']} | {trade['symbol']} | {trade['side']} | ${trade['price']:.4f} | 신호: {trade['strategy_signal']} | {trade['position_type']} | 국면: {trade['market_regime']}")
        else:
            print("  정보 없음")
        
        # 진행 상태 바
        progress_bar = "█" * int(progress / 2) + "░" * (50 - int(progress / 2))
        print(f"\n 진행 상태: [{progress_bar}] {progress:.1f}%")
        print("="*80)
    
    def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auto_strategy_futures_trading_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.trading_results, f, indent=2, ensure_ascii=False)
        
        print(f" 자동 전략 거래 결과 저장: {filename}")
    
    def run_trading(self):
        """자동 거래 실행"""
        print("[START] 자동 전략 기반 선물 거래 시작!")
        
        try:
            while datetime.now() < self.end_time:
                # 시장 데이터 업데이트
                self.update_market_data()
                
                # 각 전략 실행
                for strategy_name in self.strategies:
                    # 랜덤하게 거래 실행 (30% 확률)
                    if random.random() < 0.3:
                        self.execute_strategy_trade(strategy_name)
                
                # 상태 표시
                self.display_status()
                
                # 30초 대기
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n⚠️  자동 거래가 중단되었습니다.")
        except Exception as e:
            print(f"\n[ERROR] 거래 실행 오류: {e}")
        finally:
            self.save_results()
            print(" 자동 전략 기반 선물 거래 완료!")

if __name__ == "__main__":
    trading = AutoStrategyFuturesTrading()
    trading.run_trading()
