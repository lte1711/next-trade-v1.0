#!/usr/bin/env python3
"""
선물 전략 백테스트 - 바이낸스 테스트넷 5년치 데이터
"""

import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
import requests
import hmac
import hashlib
import urllib.parse

class FuturesBacktest:
    def __init__(self):
        self.start_time = datetime.now()
        
        # 실제 자본금 (바이낸스 테스트넷 확인 결과)
        self.total_capital = 8961.01843547
        self.capital_per_strategy = self.total_capital / 5  # 5개 전략 분배
        
        # 바이낸스 테스트넷 심볼
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "ADAUSDT",
            "MATICUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT"
        ]
        
        # 선물 전략 설정 (실제 전략과 동일)
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
        
        # 백테스트 결과 저장
        self.backtest_results = {
            "start_time": self.start_time.isoformat(),
            "end_time": None,
            "total_capital": self.total_capital,
            "strategy_performance": {},
            "market_data": {},
            "total_pnl": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "all_trades": [],
            "daily_performance": [],
            "monthly_performance": [],
            "yearly_performance": [],
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "volatility": 0
        }
        
        # 바이낸스 API 정보
        self.api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
        self.api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
        self.base_url = "https://testnet.binancefuture.com"
        
        print("🚀 선물 전략 백테스트 시작! (5년치 데이터)")
        print(f"⏰ 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 초기 자본: ${self.total_capital:,.2f}")
        print(f"📊 전략당 자본: ${self.capital_per_strategy:,.2f}")
        print(f"🎯 실행 전략: {len(self.strategies)}개")
        print(f"💱 대상 심볼: {len(self.symbols)}개")
        print("=" * 80)
    
    def get_historical_data(self, symbol, interval="1d", years=5):
        """바이낸스 테스트넷에서 5년치 데이터 가져오기"""
        try:
            # 종료 시간 (현재)
            end_time = int(time.time() * 1000)
            
            # 시작 시간 (5년 전)
            start_time = end_time - (years * 365 * 24 * 60 * 60 * 1000)
            
            # 파라미터
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1000
            }
            
            # 요청 URL
            url = f"{self.base_url}/fapi/v1/klines"
            
            # 데이터 요청
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 데이터프레임 대신 리스트로 처리
                processed_data = []
                for row in data:
                    processed_data.append({
                        'timestamp': datetime.fromtimestamp(int(row[0]) / 1000),
                        'open': float(row[1]),
                        'high': float(row[2]),
                        'low': float(row[3]),
                        'close': float(row[4]),
                        'volume': float(row[5])
                    })
                
                print(f"✅ {symbol} 데이터 {len(processed_data)}개 가져옴")
                return processed_data
            else:
                print(f"❌ {symbol} 데이터 가져오기 실패: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ {symbol} 데이터 가져오기 실패: {e}")
            return None
    
    def generate_realistic_market_data(self, symbol, years=5):
        """현실적인 시장 데이터 생성 (API 실패 시)"""
        # 기본 가격 설정
        base_prices = {
            "BTCUSDT": 30000, "ETHUSDT": 2000, "SOLUSDT": 100, "DOGEUSDT": 0.05,
            "ADAUSDT": 0.5, "MATICUSDT": 0.8, "AVAXUSDT": 30, "DOTUSDT": 6,
            "LINKUSDT": 15, "LTCUSDT": 80
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # 날짜 생성 (5년치)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        current_date = start_date
        
        data = []
        current_price = base_price
        
        while current_date <= end_date:
            # 일일 변동성 (현실적인 시장 변동)
            daily_change = random.gauss(0, 0.03)  # 3% 일일 변동성
            volatility = abs(random.gauss(0, 0.02))  # 2% 변동성
            
            # 추세 추가 (장기적인 상승/하락 트렌드)
            days_passed = (current_date - start_date).days
            trend = 0.0001 * days_passed  # 시간 경과에 따른 미세한 상승 트렌드
            
            # 가격 업데이트
            price_change = current_price * (daily_change + trend)
            current_price += price_change
            
            # OHLCV 생성
            open_price = current_price
            high_price = open_price * (1 + volatility)
            low_price = open_price * (1 - volatility)
            close_price = open_price * (1 + daily_change)
            volume = random.uniform(1000000, 10000000)  # 거래량
            
            # 가격이 음수가 되지 않도록 보호
            if low_price <= 0:
                low_price = 0.001
                open_price = max(open_price, low_price)
                high_price = max(high_price, low_price)
                close_price = max(close_price, low_price)
            
            data.append({
                'timestamp': current_date,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_date += timedelta(days=1)
        
        print(f"✅ {symbol} 시뮬레이션 데이터 {len(data)}개 생성됨")
        
        return data
    
    def analyze_market_regime(self, data, current_index):
        """시장 국면 분석"""
        if current_index < 20:
            return {"regime": "SIDEWAYS_MARKET", "avg_change": 0, "volatility": 0.02, "strength": 0}
        
        # 최근 20일 데이터
        recent_data = data[current_index-20:current_index]
        
        # 일일 변화율 계산
        daily_changes = []
        for i in range(1, len(recent_data)):
            change = (recent_data[i]['close'] - recent_data[i-1]['close']) / recent_data[i-1]['close']
            daily_changes.append(change)
        
        if not daily_changes:
            return {"regime": "SIDEWAYS_MARKET", "avg_change": 0, "volatility": 0.02, "strength": 0}
        
        # 평균과 표준편차 계산
        avg_change = sum(daily_changes) / len(daily_changes)
        
        # 표준편차 계산
        variance = sum((x - avg_change) ** 2 for x in daily_changes) / len(daily_changes)
        volatility = variance ** 0.5
        strength = abs(avg_change)
        
        # 시장 국면 결정
        if avg_change > 0.015:
            regime = "BULL_MARKET"
        elif avg_change < -0.015:
            regime = "BEAR_MARKET"
        else:
            regime = "SIDEWAYS_MARKET"
        
        return {
            "regime": regime,
            "avg_change": avg_change,
            "volatility": volatility,
            "strength": strength
        }
    
    def generate_futures_signal(self, strategy_name, market_regime):
        """선물 전략 신호 생성 (실제 전략과 동일)"""
        strategy = self.strategies[strategy_name]
        strategy_type = strategy["strategy_type"]
        market_bias = strategy["market_bias"]
        
        # 전략별 신호 생성 로직
        if strategy_type == "bull_momentum":
            if market_regime["regime"] == "BULL_MARKET" and market_regime["strength"] > 0.02:
                return "BUY"
            else:
                return None
                
        elif strategy_type == "bear_momentum":
            if market_regime["regime"] == "BEAR_MARKET" and market_regime["strength"] > 0.02:
                return "SELL"
            else:
                return None
                
        elif strategy_type == "volatility_scalping":
            if market_regime["volatility"] > 0.025:
                return random.choice(["BUY", "SELL"])
            else:
                return None
                
        elif strategy_type == "trend_following":
            if market_regime["regime"] == "BULL_MARKET":
                return "BUY"
            elif market_regime["regime"] == "BEAR_MARKET":
                return "SELL"
            else:
                return None
                
        elif strategy_type == "mean_reversion":
            if market_regime["regime"] == "SIDEWAYS_MARKET":
                return random.choice(["BUY", "SELL"])
            else:
                return None
        
        return None
    
    def calculate_position_size(self, strategy_name, symbol, current_price):
        """포지션 크기 계산"""
        strategy = self.strategies[strategy_name]
        capital = strategy["capital"]
        risk_per_trade = strategy["risk_per_trade"]
        leverage = strategy["leverage"]
        
        # 리스크 기반 포지션 크기
        risk_amount = capital * risk_per_trade
        position_value = risk_amount * leverage
        quantity = position_value / current_price
        
        # 최소 수량 보장 (단순화)
        min_quantities = {
            "BTCUSDT": 0.001, "ETHUSDT": 0.01, "SOLUSDT": 0.1, "DOGEUSDT": 10,
            "ADAUSDT": 1, "MATICUSDT": 1, "AVAXUSDT": 0.1, "DOTUSDT": 1,
            "LINKUSDT": 0.1, "LTCUSDT": 0.01
        }
        
        if symbol in min_quantities:
            min_qty = min_quantities[symbol]
            quantity = max(quantity, min_qty)
        
        return quantity
    
    def execute_backtest_trade(self, strategy_name, symbol, side, entry_price, data, entry_index):
        """백테스트 거래 실행"""
        strategy = self.strategies[strategy_name]
        leverage = strategy["leverage"]
        stop_loss = strategy["stop_loss"]
        take_profit = strategy["take_profit"]
        win_rate = strategy["win_rate"]
        avg_return = strategy["avg_return"]
        
        quantity = self.calculate_position_size(strategy_name, symbol, entry_price)
        
        # 포지션 타입 결정
        position_type = "LONG" if side == "BUY" else "SHORT"
        
        # 손절/익절 가격 계산
        if position_type == "LONG":
            stop_loss_price = entry_price * (1 - stop_loss)
            take_profit_price = entry_price * (1 + take_profit)
        else:  # SHORT
            stop_loss_price = entry_price * (1 + stop_loss)
            take_profit_price = entry_price * (1 - take_profit)
        
        # 거래 결과 시뮬레이션
        for i in range(entry_index + 1, min(entry_index + 100, len(data))):
            current_price = data[i]['close']
            current_date = data[i]['timestamp']
            
            # 손절 청산
            if position_type == "LONG" and current_price <= stop_loss_price:
                pnl = -quantity * entry_price * stop_loss * leverage
                return {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "entry_time": data[entry_index]['timestamp'],
                    "exit_time": current_date,
                    "position_type": position_type,
                    "pnl": pnl,
                    "status": "STOP_LOSS",
                    "holding_days": i - entry_index
                }
            
            # 익절 청산
            elif position_type == "LONG" and current_price >= take_profit_price:
                pnl = quantity * entry_price * avg_return * leverage
                return {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "entry_time": data[entry_index]['timestamp'],
                    "exit_time": current_date,
                    "position_type": position_type,
                    "pnl": pnl,
                    "status": "TAKE_PROFIT",
                    "holding_days": i - entry_index
                }
            
            # SHORT 손절 청산
            elif position_type == "SHORT" and current_price >= stop_loss_price:
                pnl = -quantity * entry_price * stop_loss * leverage
                return {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "entry_time": data[entry_index]['timestamp'],
                    "exit_time": current_date,
                    "position_type": position_type,
                    "pnl": pnl,
                    "status": "STOP_LOSS",
                    "holding_days": i - entry_index
                }
            
            # SHORT 익절 청산
            elif position_type == "SHORT" and current_price <= take_profit_price:
                pnl = quantity * entry_price * avg_return * leverage
                return {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "entry_time": data[entry_index]['timestamp'],
                    "exit_time": current_date,
                    "position_type": position_type,
                    "pnl": pnl,
                    "status": "TAKE_PROFIT",
                    "holding_days": i - entry_index
                }
            
            # 최대 보유 기간 (30일) 초과 시 강제 청산
            elif i - entry_index >= 30:
                if position_type == "LONG":
                    pnl = quantity * entry_price * (current_price - entry_price) / entry_price * leverage
                else:
                    pnl = quantity * entry_price * (entry_price - current_price) / entry_price * leverage
                
                return {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "entry_time": data[entry_index]['timestamp'],
                    "exit_time": current_date,
                    "position_type": position_type,
                    "pnl": pnl,
                    "status": "TIMEOUT",
                    "holding_days": i - entry_index
                }
        
        # 데이터 종료 시 청산
        final_price = data[-1]['close']
        if position_type == "LONG":
            pnl = quantity * entry_price * (final_price - entry_price) / entry_price * leverage
        else:
            pnl = quantity * entry_price * (entry_price - final_price) / entry_price * leverage
        
        return {
            "strategy": strategy_name,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
            "exit_price": final_price,
            "entry_time": data[entry_index]['timestamp'],
            "exit_time": data[-1]['timestamp'],
            "position_type": position_type,
            "pnl": pnl,
            "status": "DATA_END",
            "holding_days": len(data) - entry_index - 1
        }
    
    def run_backtest(self):
        """백테스트 실행"""
        print("📊 5년치 데이터 백테스트 시작!")
        
        # 모든 심볼 데이터 가져오기
        all_data = {}
        
        for symbol in self.symbols:
            print(f"📈 {symbol} 데이터 가져오는 중...")
            
            # 실제 API 시도
            data = self.get_historical_data(symbol)
            
            # 실패 시 시뮬레이션 데이터
            if data is None:
                print(f"⚠️ {symbol} API 실패, 시뮬레이션 데이터 생성")
                data = self.generate_realistic_market_data(symbol)
            
            all_data[symbol] = data
        
        print(f"✅ {len(all_data)}개 심볼 데이터 준비 완료!")
        
        # 백테스트 실행
        all_trades = []
        strategy_performance = {}
        
        # 전략별 자본 초기화
        for strategy_name in self.strategies:
            strategy_performance[strategy_name] = {
                "capital": self.capital_per_strategy,
                "trades": [],
                "total_pnl": 0,
                "win_rate": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0
            }
        
        # 일별 백테스트 실행
        total_days = len(all_data[self.symbols[0]])
        
        for day in range(0, total_days, 7):  # 주 단위로 실행 (성능 향상)
            current_date = all_data[self.symbols[0]][day]['timestamp']
            
            print(f"📅 {current_date.strftime('%Y-%m-%d')} 백테스트 중... ({day}/{total_days})")
            
            # 각 전략별 거래 실행
            for strategy_name, strategy in self.strategies.items():
                # 시장 국면 분석
                market_regime = self.analyze_market_regime(all_data[self.symbols[0]], day)
                
                # 선호 심볼에서 선택
                available_symbols = [s for s in strategy["preferred_symbols"] if s in self.symbols]
                if not available_symbols:
                    available_symbols = self.symbols
                
                symbol = random.choice(available_symbols)
                symbol_data = all_data[symbol]
                
                # 신호 생성
                signal = self.generate_futures_signal(strategy_name, market_regime)
                
                if signal and day < len(symbol_data) - 1:
                    # 거래 실행
                    entry_price = symbol_data[day]['close']
                    trade = self.execute_backtest_trade(strategy_name, symbol, signal, entry_price, symbol_data, day)
                    
                    if trade:
                        all_trades.append(trade)
                        strategy_performance[strategy_name]["trades"].append(trade)
                        strategy_performance[strategy_name]["capital"] += trade["pnl"]
                        strategy_performance[strategy_name]["total_pnl"] += trade["pnl"]
        
        # 최종 성과 계산
        total_pnl = 0
        total_trades = len(all_trades)
        winning_trades = 0
        losing_trades = 0
        
        for trade in all_trades:
            total_pnl += trade["pnl"]
            if trade["pnl"] > 0:
                winning_trades += 1
            else:
                losing_trades += 1
        
        # 전략별 성과 계산
        for strategy_name, perf in strategy_performance.items():
            trades = perf["trades"]
            if trades:
                wins = sum(1 for t in trades if t["pnl"] > 0)
                perf["win_rate"] = (wins / len(trades)) * 100
                perf["total_trades"] = len(trades)
                perf["final_capital"] = perf["capital"]
                perf["return_rate"] = ((perf["capital"] - self.capital_per_strategy) / self.capital_per_strategy) * 100
        
        # 결과 저장
        self.backtest_results.update({
            "end_time": datetime.now().isoformat(),
            "strategy_performance": strategy_performance,
            "total_pnl": total_pnl,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "all_trades": all_trades[-100:],  # 최근 100개 거래만 저장
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_return": (total_pnl / self.total_capital) * 100
        })
        
        return self.backtest_results
    
    def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"futures_backtest_5years_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.backtest_results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 백테스트 결과 저장: {filename}")
        
        # CSV로도 저장
        csv_filename = f"futures_backtest_5years_{timestamp}.csv"
        
        if self.backtest_results["all_trades"]:
            # CSV 파일로 저장
            with open(csv_filename, 'w', encoding='utf-8') as f:
                # 헤더 작성
                f.write("strategy,symbol,side,quantity,entry_price,exit_price,entry_time,exit_time,position_type,pnl,status,holding_days\n")
                
                # 데이터 작성
                for trade in self.backtest_results["all_trades"]:
                    f.write(f"{trade['strategy']},{trade['symbol']},{trade['side']},{trade['quantity']},{trade['entry_price']},{trade['exit_price']},{trade['entry_time']},{trade['exit_time']},{trade['position_type']},{trade['pnl']},{trade['status']},{trade['holding_days']}\n")
            
            print(f"📁 거래 내역 CSV 저장: {csv_filename}")
    
    def print_results(self):
        """결과 출력"""
        results = self.backtest_results
        
        print("\n" + "=" * 80)
        print("🎉 5년치 선물 전략 백테스트 결과")
        print("=" * 80)
        
        print(f"⏰ 테스트 기간: {results['start_time']} ~ {results['end_time']}")
        print(f"💰 초기 자본: ${results['total_capital']:,.2f}")
        print(f"💰 최종 자본: ${results['total_capital'] + results['total_pnl']:,.2f}")
        print(f"💰 총 손익: ${results['total_pnl']:+,.2f}")
        print(f"📈 총 수익률: {results['total_return']:+.2f}%")
        print(f"📊 총 거래: {results['total_trades']}회")
        print(f"✅ 성공 거래: {results['winning_trades']}회")
        print(f"❌ 실패 거래: {results['losing_trades']}회")
        print(f"🎯 성공률: {results['win_rate']:.1f}%")
        print("")
        
        print("🎯 전략별 성과:")
        sorted_strategies = sorted(
            results['strategy_performance'].items(),
            key=lambda x: x[1]['return_rate'],
            reverse=True
        )
        
        for i, (strategy_name, perf) in enumerate(sorted_strategies, 1):
            strategy = self.strategies[strategy_name]
            print(f"  {i}. {strategy_name}:")
            print(f"     초기 자본: ${self.capital_per_strategy:,.2f}")
            print(f"     최종 자본: ${perf['final_capital']:,.2f}")
            print(f"     손익: ${perf['total_pnl']:+,.2f}")
            print(f"     수익률: {perf['return_rate']:+.2f}%")
            print(f"     거래: {perf['total_trades']}회")
            print(f"     성공률: {perf['win_rate']:.1f}%")
            print(f"     레버리지: {strategy['leverage']}x")
            print(f"     전략: {strategy['strategy_type']}")
            print("")
        
        # 최근 거래 내역
        if results['all_trades']:
            print("📋 최근 거래 내역:")
            for trade in results['all_trades'][-10:]:
                pnl_emoji = "📈" if trade['pnl'] > 0 else "📉"
                print(f"  {pnl_emoji} {trade['strategy']} | {trade['symbol']} | {trade['position_type']} | ${trade['entry_price']:.4f} → ${trade['exit_price']:.4f} | PnL: ${trade['pnl']:+.2f} | {trade['status']} | {trade['holding_days']}일")
        
        print("=" * 80)

if __name__ == "__main__":
    backtest = FuturesBacktest()
    results = backtest.run_backtest()
    backtest.print_results()
    backtest.save_results()
