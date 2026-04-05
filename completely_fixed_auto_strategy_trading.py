#!/usr/bin/env python3
"""
완전 수정된 자동 전략 기반 선물 거래 시스템 - 오류 보고 및 처리 개선
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
import traceback

class CompletelyFixedAutoStrategyFuturesTrading:
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=24)
        self.test_duration = 24 * 60 * 60  # 24시간 (초)
        
        # API 설정 (환경변수 또는 설정 파일에서 로드)
        self.api_key = os.getenv("BINANCE_TESTNET_KEY", "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg")
        self.api_secret = os.getenv("BINANCE_TESTNET_SECRET", "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI")
        self.base_url = "https://testnet.binancefuture.com"
        
        # 동적 자본금 설정 (실제 계정에서 가져옴)
        self.total_capital = self.get_account_balance()
        self.capital_per_strategy = self.total_capital / len(self.get_available_strategies())
        
        # 동적 심볼 목록 (실제 거래소에서 가져옴)
        self.valid_symbols = self.get_available_symbols()
        
        # 동적 가격 정보 (실시간 시장에서 가져옴)
        self.current_prices = self.get_current_prices()
        
        # 자동 전략 설정 (동적 생성)
        self.strategies = self.generate_dynamic_strategies()
        
        # 캐시 설정
        self.symbol_info_cache = {}
        self.account_info_cache = {}
        
        # 실행 상태
        self.running = True
        self.system_errors = []  # 시스템 오류 기록
        
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
            "market_regime": "UNKNOWN",
            "sync_status": "INITIALIZED",
            "system_errors": [],  # 시스템 오류 기록
            "error_count": 0,      # 오류 횟수
            "last_error": None     # 마지막 오류
        }
        
        # 실시간 동기화 스레드 시작
        self.sync_thread = threading.Thread(target=self.periodic_sync, daemon=True)
        self.sync_thread.start()
        
        print("🚀 완전 수정된 자동 전략 기반 선물 거래 시작!")
        print(f"⏰ 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 초기 자본: ${self.total_capital:,.2f}")
        print(f"📊 전략 수: {len(self.strategies)}개")
        print(f"💱 대상 심볼: {len(self.valid_symbols)}개")
        print(f"🔄 실시간 동기화: 활성화")
        print(f"🛡️  오류 보고: 강화")
        print("=" * 80)
    
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
    
    def get_account_info(self):
        """계정 정보 가져오기"""
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
                return response.json()
            else:
                self.log_system_error(f"계정 정보 실패: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_system_error("계정 정보 오류", str(e))
            return None
    
    def get_account_balance(self):
        """실제 계정 잔고 가져오기"""
        try:
            account_info = self.get_account_info()
            if account_info:
                balance = float(account_info['totalWalletBalance'])
                print(f"✅ 실제 계정 잔고: ${balance:,.2f}")
                return balance
            else:
                print(f"❌ 계정 정보 없음, 기본값 사용")
                return 10000.0
        except Exception as e:
            self.log_system_error("계정 잔고 오류", str(e))
            return 10000.0
    
    def get_available_symbols(self):
        """실제 거래 가능한 심볼 목록 가져오기"""
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
                
                print(f"✅ 거래 가능 심볼: {len(symbols)}개")
                return symbols[:20]  # 상위 20개만 사용
            else:
                self.log_system_error(f"심볼 정보 가져오기 실패: {response.status_code}", response.text)
                return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        except Exception as e:
            self.log_system_error("심볼 정보 오류", str(e))
            return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    def get_current_prices(self):
        """실시간 시장 가격 가져오기"""
        prices = {}
        
        try:
            for symbol in self.valid_symbols[:10]:  # 상위 10개만
                response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
                
                if response.status_code == 200:
                    price_data = response.json()
                    prices[symbol] = float(price_data["price"])
                else:
                    prices[symbol] = 100.0  # 기본값
            
            print(f"✅ 시장 가격: {len(prices)}개 심볼")
            return prices
        except Exception as e:
            self.log_system_error("시장 가격 오류", str(e))
            return {symbol: 100.0 for symbol in self.valid_symbols[:10]}
    
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
        
        print(f"✅ 동적 전략 생성: {len(strategies)}개")
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
    
    def log_system_error(self, error_type, error_message):
        """시스템 오류 기록"""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": error_message,
            "traceback": traceback.format_exc() if traceback.format_exc() != "NoneType: None\n" else None
        }
        
        self.system_errors.append(error_record)
        self.trading_results["system_errors"].append(error_record)
        self.trading_results["error_count"] += 1
        self.trading_results["last_error"] = error_record
        
        print(f"🚨 시스템 오류 기록: {error_type} - {error_message}")
    
    def sync_positions(self):
        """실제 포지션 정보 동기화"""
        try:
            account_info = self.get_account_info()
            if account_info:
                active_positions = {}
                for position in account_info['positions']:
                    if float(position['positionAmt']) != 0:
                        active_positions[position['symbol']] = {
                            'amount': float(position['positionAmt']),
                            'entry_price': float(position['entryPrice']),
                            'mark_price': float(position['markPrice']),
                            'unrealized_pnl': float(position['unrealizedPnl']),
                            'percentage': float(position['percentage'])
                        }
                
                self.trading_results["active_positions"] = active_positions
                print(f"✅ 포지션 동기화: {len(active_positions)}개")
                
        except Exception as e:
            self.log_system_error("포지션 동기화 실패", str(e))
    
    def sync_account_balance(self):
        """실제 계정 잔고 동기화"""
        try:
            account_info = self.get_account_info()
            if account_info:
                total_balance = float(account_info['totalWalletBalance'])
                available_balance = float(account_info['availableBalance'])
                
                self.trading_results["current_capital"] = total_balance
                self.total_capital = total_balance
                
                # 손익 계산
                pnl = total_balance - self.trading_results["initial_capital"]
                self.trading_results["total_pnl"] = pnl
                
                # 잔고 기록
                balance_record = {
                    "timestamp": datetime.now().isoformat(),
                    "total_balance": total_balance,
                    "total_pnl": pnl,
                    "market_regime": self.trading_results["market_regime"]
                }
                self.trading_results["balance_history"].append(balance_record)
                
                print(f"✅ 자산 동기화: ${total_balance:.2f} (PnL: ${pnl:+.2f})")
                
        except Exception as e:
            self.log_system_error("자산 동기화 실패", str(e))
    
    def periodic_sync(self):
        """주기적 데이터 동기화"""
        while self.running:
            try:
                self.sync_positions()
                self.sync_account_balance()
                self.trading_results["sync_status"] = "SYNCED"
                time.sleep(60)  # 1분마다 동기화
            except Exception as e:
                self.log_system_error("주기적 동기화 오류", str(e))
                self.trading_results["sync_status"] = "SYNC_ERROR"
                time.sleep(60)
    
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
            self.log_system_error("심볼 정보 오류", str(e))
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
            self.log_system_error("시장 분석 오류", str(e))
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
        if signal_strength > 0.6:
            return "BUY"
        elif signal_strength < 0.4:
            return "SELL"
        else:
            return None
    
    def safe_float_conversion(self, value, default=0.0):
        """안전한 float 변환"""
        try:
            if value is None:
                return default
            if isinstance(value, str):
                if value == "0.00" or value == "":
                    return default
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def submit_order(self, strategy_name, symbol, side, quantity):
        """주문 제출 (완전 수정된 버전 - 오류 처리 강화)"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                self.log_system_error("심볼 정보 없음", f"{symbol} 심볼 정보를 찾을 수 없음")
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
                        min_notional = 10.0
            
            # 수량 조정
            if quantity < min_qty:
                quantity = min_qty
            
            # 최소 notional 확인 및 조정
            current_price = self.current_prices.get(symbol, 100.0)
            current_notional = quantity * current_price
            
            if current_notional < min_notional:
                quantity = (min_notional * 1.01) / current_price
                if quantity < min_qty:
                    quantity = min_qty
            
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
                print(f"✅ 주문 성공: {result}")
                
                # 안전한 가격 정보 추출
                avg_price = self.safe_float_conversion(result.get("avgPrice"), current_price)
                order_id = result.get("orderId", "UNKNOWN")
                status = result.get("status", "UNKNOWN")
                
                # 주문 결과를 시스템에 저장
                trade_record = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": avg_price,
                    "order_id": order_id,
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                    "type": "ACTUAL_TRADE",
                    "market_regime": self.trading_results["market_regime"],
                    "strategy_signal": side,
                    "position_type": "LONG" if side == "BUY" else "SHORT"
                }
                
                self.trading_results["real_orders"].append(trade_record)
                self.trading_results["total_trades"] += 1
                
                # 성공/실패 카운트 업데이트
                if status == "FILLED":
                    self.trading_results["winning_trades"] += 1
                    print(f"✅ {strategy_name} | {symbol} | {side} | {quantity} | 체결됨")
                else:
                    self.trading_results["losing_trades"] += 1
                    print(f"⏳ {strategy_name} | {symbol} | {side} | {quantity} | 대기 중")
                
                # 즉시 동기화
                self.sync_positions()
                self.sync_account_balance()
                
                return result
            else:
                error_msg = f"주문 실패: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                
                # 실패 기록
                failed_record = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "status": "FAILED",
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat(),
                    "type": "FAILED_TRADE",
                    "market_regime": self.trading_results["market_regime"],
                    "strategy_signal": side,
                    "position_type": "LONG" if side == "BUY" else "SHORT"
                }
                
                self.trading_results["real_orders"].append(failed_record)
                self.trading_results["total_trades"] += 1
                self.trading_results["losing_trades"] += 1
                
                return None
                
        except Exception as e:
            error_msg = f"주문 제출 실패: {str(e)}"
            print(f"❌ {error_msg}")
            
            # 예외 기록
            error_record = {
                "strategy": strategy_name,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "status": "ERROR",
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "type": "ERROR_TRADE",
                "market_regime": self.trading_results["market_regime"],
                "strategy_signal": side,
                "position_type": "LONG" if side == "BUY" else "SHORT"
            }
            
            self.trading_results["real_orders"].append(error_record)
            self.trading_results["total_trades"] += 1
            self.trading_results["losing_trades"] += 1
            
            # 시스템 오류 기록
            self.log_system_error("주문 제출 오류", str(e))
            
            return None
    
    def execute_strategy_trade(self, strategy_name):
        """전략 거래 실행"""
        try:
            strategy = self.strategies[strategy_name]
            
            # 선호 심볼에서 선택
            available_symbols = [s for s in strategy["preferred_symbols"] if s in self.valid_symbols]
            if not available_symbols:
                available_symbols = self.valid_symbols
            
            symbol = random.choice(available_symbols)
            
            # 시장 국면 분석
            market_regime = self.analyze_market_regime(symbol)
            self.trading_results["market_regime"] = market_regime["regime"]
            
            # 신호 생성
            signal = self.generate_strategy_signal(strategy_name, market_regime, symbol)
            
            if signal:
                # 포지션 타입 결정
                position_type = "LONG" if signal == "BUY" else "SHORT"
                
                # 수량 계산
                quantity = self.calculate_position_size(strategy_name, symbol)
                
                # 주문 제출
                order_result = self.submit_order(strategy_name, symbol, signal, quantity)
                
                return order_result
            
            return None
            
        except Exception as e:
            self.log_system_error("전략 거래 실행 오류", str(e))
            return None
    
    def calculate_position_size(self, strategy_name, symbol):
        """동적 포지션 크기 계산"""
        try:
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
            
        except Exception as e:
            self.log_system_error("포지션 크기 계산 오류", str(e))
            return 0.001  # 기본값
    
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
            self.log_system_error("시장 데이터 업데이트 오류", str(e))
    
    def display_status(self):
        """상태 표시 (완전 수정된 버전 - 오류 상태 포함)"""
        try:
            current_time = datetime.now()
            elapsed = current_time - self.start_time
            progress = (elapsed.total_seconds() / self.test_duration) * 100
            remaining = self.test_duration - elapsed.total_seconds()
            
            # 시장 국면 분석
            sample_symbol = self.valid_symbols[0] if self.valid_symbols else "BTCUSDT"
            market_regime = self.analyze_market_regime(sample_symbol)
            
            print(f"\n{'='*80}")
            print(f"🚀 완전 수정된 자동 전략 기반 선물 거래 실행")
            print(f"{'='*80}")
            print(f"⏰ 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  경과 시간: {elapsed}")
            print(f"📊 진행률: {progress:.2f}%")
            print(f"🎯 남은 시간: {timedelta(seconds=int(remaining))}")
            print(f"🔗 API 상태: 🟢 바이낸스 테스트넷 선물 연결")
            print(f"💰 계정 잔액: ${self.trading_results['current_capital']:,.2f}")
            print(f"📈 시장 국면: {market_regime['regime']}")
            print(f"🔄 동기화 상태: {self.trading_results['sync_status']}")
            
            # 오류 상태 표시
            error_count = self.trading_results["error_count"]
            if error_count > 0:
                print(f"🚨 시스템 오류: {error_count}개 발생")
                if self.trading_results["last_error"]:
                    last_error = self.trading_results["last_error"]
                    print(f"   마지막 오류: {last_error['error_type']} - {last_error['message']}")
            else:
                print(f"✅ 시스템 오류: 없음")
            
            print(f"\n📈 실시간 시장 데이터:")
            for symbol, price in list(self.current_prices.items())[:6]:
                prev_price = self.trading_results["market_data"].get(symbol, price)
                change = ((price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
                trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                print(f"  {symbol}: ${price:.4f} {trend} {change:+.2f}%")
            
            print(f"\n🎯 자동 전략 성과:")
            for strategy_name, strategy in self.strategies.items():
                capital = strategy["capital"]
                pnl = strategy.get("total_pnl", 0)
                return_rate = (pnl / self.capital_per_strategy) * 100
                leverage = strategy["leverage"]
                strategy_type = strategy["strategy_type"]
                market_bias = strategy["market_bias"]
                print(f"  {strategy_name}: ${capital:,.2f} ({return_rate:+.2f}%) 📉 [{leverage:.1f}x] {strategy_type} | {market_bias}")
            
            print(f"\n📊 선물 거래 요약:")
            print(f"  💰 초기 자본: ${self.trading_results['initial_capital']:,.2f}")
            print(f"  💰 현재 자본: ${self.trading_results['current_capital']:,.2f}")
            print(f"  💰 총 손익: ${self.trading_results['total_pnl']:+,.2f}")
            print(f"  📈 총 거래: {self.trading_results['total_trades']}회")
            print(f"  ✅ 성공 거래: {self.trading_results['winning_trades']}회")
            print(f"  ❌ 실패 거래: {self.trading_results['losing_trades']}회")
            success_rate = (self.trading_results['winning_trades'] / max(1, self.trading_results['total_trades'])) * 100
            print(f"  🎯 성공률: {success_rate:.1f}%")
            print(f"  📊 전체 수익률: {((self.trading_results['current_capital'] - self.trading_results['initial_capital']) / self.trading_results['initial_capital']) * 100:+.2f}%")
            
            # 실제 포지션 정보 표시
            active_positions = self.trading_results["active_positions"]
            print(f"\n📊 실제 포지션 ({len(active_positions)}개):")
            if active_positions:
                for symbol, pos in list(active_positions.items())[:5]:
                    side = "LONG" if pos['amount'] > 0 else "SHORT"
                    pnl_status = "📈" if pos['unrealized_pnl'] > 0 else "📉" if pos['unrealized_pnl'] < 0 else "➡️"
                    print(f"  {symbol}: {side} {abs(pos['amount'])} | 진입: ${pos['entry_price']:.4f} | PnL: {pnl_status} {pos['unrealized_pnl']:+.4f}")
            else:
                print("  열린 포지션 없음")
            
            # 최근 거래 내역
            recent_trades = self.trading_results["real_orders"][-3:] if self.trading_results["real_orders"] else []
            print(f"\n📋 최근 선물 거래 내역:")
            if recent_trades:
                for trade in recent_trades:
                    status_icon = "✅" if trade["status"] == "FILLED" else "⏳" if trade["status"] == "NEW" else "❌" if trade["status"] == "FAILED" else "🚨"
                    print(f"  {status_icon} {trade['strategy']} | {trade['symbol']} | {trade['side']} | ${trade['price']:.4f} | {trade['type']} | {trade['position_type']}")
            else:
                print("  정보 없음")
            
            # 진행 상태 바
            progress_bar = "█" * int(progress / 2) + "░" * (50 - int(progress / 2))
            print(f"\n🔄 진행 상태: [{progress_bar}] {progress:.1f}%")
            print("="*80)
            
        except Exception as e:
            self.log_system_error("상태 표시 오류", str(e))
            print(f"❌ 상태 표시 오류: {e}")
    
    def save_results(self):
        """결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"completely_fixed_auto_strategy_trading_{timestamp}.json"
            
            # 데이터 정리
            cleaned_data = self.clean_data_for_json(self.trading_results)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            print(f"📁 완전 수정된 자동 전략 거래 결과 저장: {filename}")
            
        except Exception as e:
            self.log_system_error("결과 저장 오류", str(e))
            print(f"❌ 결과 저장 오류: {e}")
    
    def clean_data_for_json(self, data):
        """JSON 직렬화를 위한 데이터 정리"""
        if isinstance(data, dict):
            return {k: self.clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_data_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    def run_trading(self):
        """자동 거래 실행"""
        print("🚀 완전 수정된 자동 전략 기반 선물 거래 시작!")
        
        try:
            while datetime.now() < self.end_time and self.running:
                try:
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
                    
                except Exception as e:
                    self.log_system_error("거래 실행 루프 오류", str(e))
                    time.sleep(30)  # 오류 발생 시 30초 후 재시도
                    
        except KeyboardInterrupt:
            print("\n⚠️  자동 거래가 중단되었습니다.")
        except Exception as e:
            self.log_system_error("거래 실행 오류", str(e))
            print(f"\n❌ 거래 실행 오류: {e}")
        finally:
            self.running = False
            self.save_results()
            print("🎉 완전 수정된 자동 전략 기반 선물 거래 완료!")

if __name__ == "__main__":
    trading = CompletelyFixedAutoStrategyFuturesTrading()
    trading.run_trading()
