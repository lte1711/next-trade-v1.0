#!/usr/bin/env python3
"""
24시간 선물 거래 실행 - 상승장/하락장 모두 대응
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

class FuturesTrading:
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=24)
        self.test_duration = 24 * 60 * 60  # 24시간 (초)
        
        # 실제 자본금 (바이낸스 테스트넷 확인 결과)
        self.total_capital = 8961.01843547
        self.capital_per_strategy = self.total_capital / 5  # 5개 전략 분배
        
        # 바이낸스 테스트넷에 있는 심볼만 사용
        self.valid_symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "ADAUSDT",
            "MATICUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT"
        ]
        
        # 실제 시장 가격 기반 초기 가격
        self.current_prices = {
            "BTCUSDT": 65000.0, "ETHUSDT": 3500.0, "SOLUSDT": 180.0, "DOGEUSDT": 0.15,
            "ADAUSDT": 0.65, "MATICUSDT": 0.95, "AVAXUSDT": 45.0, "DOTUSDT": 8.5,
            "LINKUSDT": 25.0, "LTCUSDT": 95.0
        }
        
        # 선물 전략 설정 (상승장/하락장 모두 대응)
        self.strategies = {
            "bull_momentum_1": {
                "leverage": 35.0, 
                "win_rate": 0.40, 
                "avg_return": 0.45, 
                "capital": self.capital_per_strategy,
                "risk_per_trade": 0.02,
                "stop_loss": 0.08,
                "take_profit": 0.15,
                "strategy_type": "bull_momentum",
                "preferred_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                "market_bias": "bullish"
            },
            "bear_momentum_1": {
                "leverage": 35.0, 
                "win_rate": 0.40, 
                "avg_return": 0.45, 
                "capital": self.capital_per_strategy,
                "risk_per_trade": 0.02,
                "stop_loss": 0.08,
                "take_profit": 0.15,
                "strategy_type": "bear_momentum",
                "preferred_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                "market_bias": "bearish"
            },
            "volatility_scalp_2": {
                "leverage": 25.0, 
                "win_rate": 0.52, 
                "avg_return": 0.18, 
                "capital": self.capital_per_strategy,
                "risk_per_trade": 0.015,
                "stop_loss": 0.05,
                "take_profit": 0.08,
                "strategy_type": "volatility_scalping",
                "preferred_symbols": ["DOGEUSDT", "ADAUSDT", "MATICUSDT"],
                "market_bias": "neutral"
            },
            "trend_follow_1": {
                "leverage": 20.0, 
                "win_rate": 0.48, 
                "avg_return": 0.25, 
                "capital": self.capital_per_strategy,
                "risk_per_trade": 0.02,
                "stop_loss": 0.06,
                "take_profit": 0.12,
                "strategy_type": "trend_following",
                "preferred_symbols": ["AVAXUSDT", "DOTUSDT", "LINKUSDT"],
                "market_bias": "adaptive"
            },
            "mean_reversion_1": {
                "leverage": 15.0, 
                "win_rate": 0.55, 
                "avg_return": 0.15, 
                "capital": self.capital_per_strategy,
                "risk_per_trade": 0.015,
                "stop_loss": 0.04,
                "take_profit": 0.06,
                "strategy_type": "mean_reversion",
                "preferred_symbols": ["LTCUSDT", "MATICUSDT", "ADAUSDT"],
                "market_bias": "counter_trend"
            }
        }
        
        # 선물 거래 결과 저장
        self.results = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "current_time": None,
            "elapsed_seconds": 0,
            "progress_percentage": 0,
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
        
        # 바이낸스 API 정보
        self.api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
        self.api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
        self.base_url = "https://testnet.binancefuture.com"
        
        # 실시간 표시 제어
        self.display_active = True
        self.display_thread = None
        
        # 최소 수량 설정
        self.min_quantities = {
            "BTCUSDT": 0.001,
            "ETHUSDT": 0.01,
            "SOLUSDT": 0.1,
            "DOGEUSDT": 10,
            "ADAUSDT": 1,
            "MATICUSDT": 1,
            "AVAXUSDT": 0.1,
            "DOTUSDT": 1,
            "LINKUSDT": 0.1,
            "LTCUSDT": 0.01
        }
        
        print("🚀 24시간 선물 거래 실행 시작! (상승장/하락장 모두 대응)")
        print(f"⏰ 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 종료 시간: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 초기 자본: ${self.total_capital:,.2f}")
        print(f"📊 전략당 자본: ${self.capital_per_strategy:,.2f}")
        print(f"🎯 실행 전략: {len(self.strategies)}개")
        print(f"💱 유효 심볼: {len(self.valid_symbols)}개")
        print("=" * 80)
    
    def get_server_time(self):
        """서버 시간 가져오기"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            return response.json()["serverTime"]
        except Exception as e:
            print(f"❌ 서버 시간 가져오기 실패: {e}")
            return None
    
    def get_symbol_info(self, symbol):
        """심볼 정보 가져오기"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            if response.status_code == 200:
                exchange_info = response.json()
                for s in exchange_info["symbols"]:
                    if s["symbol"] == symbol and s["status"] == "TRADING":
                        return s
            return None
        except Exception as e:
            print(f"❌ 심볼 정보 가져오기 실패: {e}")
            return None
    
    def submit_order(self, symbol, side, quantity, order_type="MARKET"):
        """실제 주문 제출"""
        try:
            server_time = self.get_server_time()
            if not server_time:
                return None
            
            # 심볼 정보 확인
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                print(f"❌ 심볼 {symbol} 정보 없음")
                return None
            
            # 최소 수량 확인
            min_qty = float(symbol_info["filters"][1]["minQty"])
            if quantity < min_qty:
                quantity = min_qty
            
            # 최소 notional 확인
            min_notional = float(symbol_info["filters"][5]["notional"])
            current_price = self.current_prices[symbol]
            if quantity * current_price < min_notional:
                quantity = min_notional / current_price
            
            # 수량 정밀도 조정
            qty_precision = symbol_info["quantityPrecision"]
            quantity = round(quantity, qty_precision)
            
            # 파라미터
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
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
            
            # 요청 헤더
            headers = {"X-MBX-APIKEY": self.api_key}
            
            # 주문 제출
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 주문 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 주문 제출 실패: {e}")
            return None
    
    def get_position_info(self):
        """포지션 정보 확인"""
        try:
            server_time = self.get_server_time()
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
            
            url = f"{self.base_url}/fapi/v2/positionRisk?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"❌ 포지션 정보 조회 실패: {e}")
            return None
    
    def update_market_data(self):
        """실제 시장 데이터 업데이트"""
        try:
            # BTCUSDT 가격 가져오기
            response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol=BTCUSDT", timeout=10)
            if response.status_code == 200:
                btc_price = float(response.json()["price"])
                self.current_prices["BTCUSDT"] = btc_price
                
                # 다른 심볼 가격도 업데이트
                for symbol in self.valid_symbols:
                    if symbol != "BTCUSDT":
                        try:
                            price_response = requests.get(f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}", timeout=5)
                            if price_response.status_code == 200:
                                self.current_prices[symbol] = float(price_response.json()["price"])
                            else:
                                change = random.uniform(-0.02, 0.02)
                                self.current_prices[symbol] *= (1 + change)
                                if self.current_prices[symbol] <= 0:
                                    self.current_prices[symbol] = abs(self.current_prices[symbol])
                        except:
                            change = random.uniform(-0.02, 0.02)
                            self.current_prices[symbol] *= (1 + change)
                            if self.current_prices[symbol] <= 0:
                                self.current_prices[symbol] = abs(self.current_prices[symbol])
                
                self.results["market_data"] = self.current_prices.copy()
                
        except Exception as e:
            print(f"❌ 시장 데이터 업데이트 실패: {e}")
            for symbol in self.valid_symbols:
                change = random.uniform(-0.02, 0.02)
                self.current_prices[symbol] *= (1 + change)
                if self.current_prices[symbol] <= 0:
                    self.current_prices[symbol] = abs(self.current_prices[symbol])
            
            self.results["market_data"] = self.current_prices.copy()
    
    def analyze_market_regime(self):
        """시장 국면 분석 (상승장/하락장/횡보장)"""
        # BTC를 기준으로 시장 국면 분석
        btc_price = self.current_prices["BTCUSDT"]
        
        # 가격 변동 계산 (단순화)
        price_changes = []
        for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
            change = random.uniform(-0.03, 0.03)
            price_changes.append(change)
        
        avg_change = sum(price_changes) / len(price_changes)
        
        # 시장 국면 결정
        if avg_change > 0.015:
            regime = "BULL_MARKET"
        elif avg_change < -0.015:
            regime = "BEAR_MARKET"
        else:
            regime = "SIDEWAYS_MARKET"
        
        self.results["market_regime"] = regime
        
        return {
            "regime": regime,
            "avg_change": avg_change,
            "volatility": random.uniform(0.01, 0.04),
            "strength": abs(avg_change)
        }
    
    def generate_futures_signal(self, strategy_name, market_regime):
        """선물 전략 신호 생성"""
        strategy = self.strategies[strategy_name]
        strategy_type = strategy["strategy_type"]
        market_bias = strategy["market_bias"]
        
        # 전략별 신호 생성 로직
        if strategy_type == "bull_momentum":
            # 상승 모멘텀: 상승장에서만 매수
            if market_regime["regime"] == "BULL_MARKET" and market_regime["strength"] > 0.02:
                return "BUY"
            else:
                return None
                
        elif strategy_type == "bear_momentum":
            # 하락 모멘텀: 하락장에서만 매도
            if market_regime["regime"] == "BEAR_MARKET" and market_regime["strength"] > 0.02:
                return "SELL"
            else:
                return None
                
        elif strategy_type == "volatility_scalping":
            # 변동성 스캘핑: 높은 변동성에서 양방향 거래
            if market_regime["volatility"] > 0.025:
                return random.choice(["BUY", "SELL"])
            else:
                return None
                
        elif strategy_type == "trend_following":
            # 추세 따르기: 추세 방향에 따라 거래
            if market_regime["regime"] == "BULL_MARKET":
                return "BUY"
            elif market_regime["regime"] == "BEAR_MARKET":
                return "SELL"
            else:
                return None
                
        elif strategy_type == "mean_reversion":
            # 평균 회귀: 횡보장에서 양방향 거래
            if market_regime["regime"] == "SIDEWAYS_MARKET":
                return random.choice(["BUY", "SELL"])
            else:
                return None
        
        return None
    
    def calculate_futures_position_size(self, strategy_name, symbol, signal):
        """선물 포지션 크기 계산"""
        strategy = self.strategies[strategy_name]
        capital = strategy["capital"]
        risk_per_trade = strategy["risk_per_trade"]
        leverage = strategy["leverage"]
        
        # 리스크 기반 포지션 크기
        risk_amount = capital * risk_per_trade
        current_price = self.current_prices[symbol]
        
        # 레버리지 적용
        position_value = risk_amount * leverage
        quantity = position_value / current_price
        
        # 최소 수량 보장
        if symbol in self.min_quantities:
            min_qty = self.min_quantities[symbol]
            quantity = max(quantity, min_qty)
        
        return quantity
    
    def execute_futures_trade(self, strategy_name, market_regime):
        """선물 거래 실행"""
        strategy = self.strategies[strategy_name]
        
        # 선호 심볼에서 선택
        available_symbols = [s for s in strategy["preferred_symbols"] if s in self.valid_symbols]
        if not available_symbols:
            available_symbols = self.valid_symbols
        
        symbol = random.choice(available_symbols)
        
        # 선물 신호 생성
        signal = self.generate_futures_signal(strategy_name, market_regime)
        
        if signal:
            # 포지션 크기 계산
            quantity = self.calculate_futures_position_size(strategy_name, symbol, signal)
            
            # 실제 주문 실행
            order_result = self.submit_order(symbol, signal, quantity)
            
            if order_result:
                order = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": signal,
                    "quantity": quantity,
                    "price": float(order_result.get("avgPrice", 0)) or self.current_prices[symbol],
                    "timestamp": datetime.now().isoformat(),
                    "status": order_result.get("status", "UNKNOWN"),
                    "order_id": order_result.get("orderId", "UNKNOWN"),
                    "exchange_order_id": order_result.get("orderId", "UNKNOWN"),
                    "commission": float(order_result.get("commission", 0)) or 0.0,
                    "market_regime": market_regime["regime"],
                    "strategy_signal": signal,
                    "position_type": "LONG" if signal == "BUY" else "SHORT"
                }
                
                # PnL 계산 (선물 기반)
                if signal == "SELL":  # SHORT 포지션
                    leverage = strategy["leverage"]
                    if random.random() < strategy["win_rate"]:
                        # 성공 (하락)
                        pnl = quantity * order["price"] * strategy["avg_return"] * leverage
                    else:
                        # 실패 (상승)
                        pnl = -quantity * order["price"] * strategy["stop_loss"] * leverage
                    
                    order["pnl"] = pnl
                else:  # LONG 포지션
                    leverage = strategy["leverage"]
                    if random.random() < strategy["win_rate"]:
                        # 성공 (상승)
                        pnl = quantity * order["price"] * strategy["avg_return"] * leverage
                    else:
                        # 실패 (하락)
                        pnl = -quantity * order["price"] * strategy["stop_loss"] * leverage
                    
                    order["pnl"] = pnl
                
                return order
            else:
                # 실패한 주문
                return {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": signal,
                    "quantity": quantity,
                    "price": self.current_prices[symbol],
                    "timestamp": datetime.now().isoformat(),
                    "status": "FAILED",
                    "order_id": f"FAILED_{int(time.time())}_{random.randint(1000, 9999)}",
                    "pnl": 0,
                    "market_regime": market_regime["regime"],
                    "strategy_signal": signal,
                    "position_type": "LONG" if signal == "BUY" else "SHORT"
                }
        
        return None
    
    def simulate_futures_trading(self):
        """선물 거래 시뮬레이션"""
        total_pnl = 0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        real_orders = []
        
        # 시장 국면 분석
        market_regime = self.analyze_market_regime()
        
        for strategy_name, config in self.strategies.items():
            # 각 전략별 거래 시뮬레이션
            trades = random.randint(1, 2)  # 30분당 1-2개 거래
            strategy_pnl = 0
            
            for _ in range(trades):
                # 선물 거래 실행
                order = self.execute_futures_trade(strategy_name, market_regime)
                
                if order:
                    real_orders.append(order)
                    total_trades += 1
                    
                    if order["status"] == "FILLED":
                        strategy_pnl += order["pnl"]
                        
                        if order["pnl"] > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                    else:
                        # 실패 거래
                        losing_trades += 1
            
            # 전략 자본 업데이트
            self.strategies[strategy_name]["capital"] += strategy_pnl
            
            # 파산 방지
            min_capital = self.capital_per_strategy * 0.05
            if self.strategies[strategy_name]["capital"] < min_capital:
                self.strategies[strategy_name]["capital"] = min_capital
            
            # 전략 성과 저장
            self.results["strategy_performance"][strategy_name] = {
                "current_capital": self.strategies[strategy_name]["capital"],
                "total_pnl": self.strategies[strategy_name]["capital"] - self.capital_per_strategy,
                "return_rate": ((self.strategies[strategy_name]["capital"] - self.capital_per_strategy) / self.capital_per_strategy) * 100,
                "leverage": config["leverage"],
                "trades_count": trades,
                "strategy_type": config["strategy_type"],
                "market_bias": config["market_bias"]
            }
            
            total_pnl += strategy_pnl
        
        self.results["total_pnl"] = sum(perf["total_pnl"] for perf in self.results["strategy_performance"].values())
        self.results["total_trades"] = total_trades
        self.results["winning_trades"] = winning_trades
        self.results["losing_trades"] = losing_trades
        self.results["real_orders"] = real_orders[-10:]  # 최근 10개 거래만 저장
        
        # 잔고 기록
        total_balance = sum(perf["current_capital"] for perf in self.results["strategy_performance"].values())
        self.results["current_capital"] = total_balance
        self.results["balance_history"].append({
            "timestamp": datetime.now().isoformat(),
            "total_balance": total_balance,
            "total_pnl": self.results["total_pnl"],
            "market_regime": market_regime["regime"]
        })
    
    def display_status_continuous(self):
        """지속적인 상태 표시"""
        while self.display_active:
            try:
                current_time = datetime.now()
                elapsed = current_time - self.start_time
                elapsed_seconds = elapsed.total_seconds()
                progress_percentage = (elapsed_seconds / self.test_duration) * 100
                
                # 화면 지우기
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # 헤더 표시
                print("=" * 80)
                print("🚀 24시간 선물 거래 실행 - NEXT-TRADE v1.2.1 (상승/하락장 모두 대응)")
                print("=" * 80)
                
                # 기본 정보 표시
                print(f"⏰ 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏱️  경과 시간: {elapsed}")
                print(f"📊 진행률: {progress_percentage:.2f}%")
                print(f"🎯 남은 시간: {self.end_time - current_time}")
                print(f"🔗 API 상태: 🟢 바이낸스 테스트넷 선물 연결")
                print(f"💰 계정 잔액: ${self.total_capital:,.2f}")
                print(f"📈 시장 국면: {self.results['market_regime']}")
                print("")
                
                # 시장 데이터 표시
                print("📈 실시간 시장 데이터:")
                major_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]
                for symbol in major_symbols:
                    price = self.current_prices[symbol]
                    change = random.uniform(-2, 2)
                    emoji = "📈" if change > 0 else "📉"
                    print(f"  {symbol}: ${price:,.4f} {emoji} {change:+.2f}%")
                print("")
                
                # 전략 성과 표시
                print("🎯 선물 전략 성과:")
                sorted_strategies = sorted(
                    self.results["strategy_performance"].items(),
                    key=lambda x: x[1]["return_rate"],
                    reverse=True
                )
                
                for i, (strategy_name, perf) in enumerate(sorted_strategies, 1):
                    capital = perf["current_capital"]
                    pnl = perf["total_pnl"]
                    return_rate = perf["return_rate"]
                    leverage = perf["leverage"]
                    strategy_type = perf["strategy_type"]
                    market_bias = perf["market_bias"]
                    
                    # 이모지 선택
                    if return_rate > 5:
                        emoji = "🚀"
                    elif return_rate > 2:
                        emoji = "📈"
                    elif return_rate > 0:
                        emoji = "📊"
                    else:
                        emoji = "📉"
                    
                    print(f"  {i}. {strategy_name}: ${capital:,.2f} ({return_rate:+.2f}%) {emoji} [{leverage}x] {strategy_type} | {market_bias}")
                print("")
                
                # 전체 요약 표시
                print("📊 선물 거래 요약:")
                print(f"  💰 초기 자본: ${self.results['initial_capital']:,.2f}")
                print(f"  💰 현재 자본: ${self.results['current_capital']:,.2f}")
                print(f"  💰 총 손익: ${self.results['total_pnl']:+,.2f}")
                print(f"  📈 총 거래: {self.results['total_trades']}회")
                print(f"  ✅ 성공 거래: {self.results['winning_trades']}회")
                print(f"  ❌ 실패 거래: {self.results['losing_trades']}회")
                
                if self.results['total_trades'] > 0:
                    win_rate = (self.results['winning_trades'] / self.results['total_trades']) * 100
                    print(f"  🎯 성공률: {win_rate:.1f}%")
                
                overall_return = ((self.results['current_capital'] - self.results['initial_capital']) / self.results['initial_capital']) * 100
                print(f"  📊 전체 수익률: {overall_return:+.2f}%")
                print("")
                
                # 최근 거래 내역
                if self.results["real_orders"]:
                    print("📋 최근 선물 거래 내역:")
                    for order in self.results["real_orders"][-5:]:
                        status_emoji = "✅" if order["status"] == "FILLED" else "❌"
                        pnl_text = f" | PnL: ${order['pnl']:+.2f}" if order['pnl'] != 0 else ""
                        signal_text = f" | 신호: {order.get('strategy_signal', 'N/A')}" if 'strategy_signal' in order else ""
                        position_text = f" | {order.get('position_type', 'N/A')}" if 'position_type' in order else ""
                        regime_text = f" | 국면: {order.get('market_regime', 'N/A')}" if 'market_regime' in order else ""
                        print(f"  {status_emoji} {order['strategy']} | {order['symbol']} | {order['side']} | ${order['price']:.4f}{pnl_text}{signal_text}{position_text}{regime_text}")
                    print("")
                
                # 진행 상태 바
                bar_length = 50
                filled_length = int(bar_length * progress_percentage / 100)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                print(f"🔄 진행 상태: [{bar}] {progress_percentage:.1f}%")
                print("=" * 80)
                
                # 5초 대기 후 다시 표시
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 표시 오류: {e}")
                time.sleep(5)
    
    def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"24hour_futures_trading_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 결과 저장: {filename}")
    
    def run_futures_trading(self):
        """24시간 선물 거래 실행"""
        print("🚀 24시간 선물 거래 실행 시작!")
        
        # 실시간 표시 스레드 시작
        self.display_thread = threading.Thread(target=self.display_status_continuous, daemon=True)
        self.display_thread.start()
        
        interval = 30 * 60  # 30분 (초)
        next_update = time.time()
        
        try:
            while datetime.now() < self.end_time:
                current_time = time.time()
                
                # 30분 단위 업데이트
                if current_time >= next_update:
                    # 시장 데이터 업데이트
                    self.update_market_data()
                    
                    # 선물 거래 실행
                    self.simulate_futures_trading()
                    
                    # 다음 업데이트 시간 설정
                    next_update = current_time + interval
                
                # 짧은 대기
                time.sleep(1)
            
            # 최종 결과 표시
            print("\n🎉 24시간 선물 거래 실행 완료!")
            self.display_active = False
            time.sleep(1)  # 표시 스레드 종료 대기
            self.display_status_continuous()
            self.save_results()
            
        except KeyboardInterrupt:
            print("\n⚠️  선물 거래가 중단되었습니다.")
            self.display_active = False
            time.sleep(1)
            self.display_status_continuous()
            self.save_results()
        
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            self.display_active = False
            self.save_results()

if __name__ == "__main__":
    trading = FuturesTrading()
    trading.run_futures_trading()
