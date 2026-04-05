#!/usr/bin/env python3
"""
선물 전략 백테스트 - 연도별 분석 및 시장 국면 진입 평가
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

class FuturesBacktestYearly:
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
        
        # 연도별 백테스트 결과 저장
        self.yearly_results = {
            "start_time": self.start_time.isoformat(),
            "end_time": None,
            "total_capital": self.total_capital,
            "years": {},
            "strategy_performance": {},
            "market_regime_analysis": {},
            "entry_evaluation": {}
        }
        
        print("🚀 선물 전략 연도별 백테스트 시작!")
        print(f"⏰ 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 초기 자본: ${self.total_capital:,.2f}")
        print(f"📊 전략당 자본: ${self.capital_per_strategy:,.2f}")
        print(f"🎯 실행 전략: {len(self.strategies)}개")
        print(f"💱 대상 심볼: {len(self.symbols)}개")
        print("=" * 80)
    
    def generate_yearly_data(self, year):
        """연도별 시장 데이터 생성"""
        # 기본 가격 설정 (연도별 특성 반영)
        base_prices = {
            "BTCUSDT": 30000, "ETHUSDT": 2000, "SOLUSDT": 100, "DOGEUSDT": 0.05,
            "ADAUSDT": 0.5, "MATICUSDT": 0.8, "AVAXUSDT": 30, "DOTUSDT": 6,
            "LINKUSDT": 15, "LTCUSDT": 80
        }
        
        # 연도별 시장 특성
        year_characteristics = {
            2021: {"trend": "BULL", "volatility": 0.04, "base_multiplier": 1.0},  # 강한 상승장
            2022: {"trend": "BEAR", "volatility": 0.05, "base_multiplier": 0.8},  # 강한 하락장
            2023: {"trend": "SIDEWAYS", "volatility": 0.03, "base_multiplier": 0.9},  # 횡보장
            2024: {"trend": "BULL", "volatility": 0.035, "base_multiplier": 1.2},  # 상승장
            2025: {"trend": "BULL", "volatility": 0.03, "base_multiplier": 1.5},  # 강한 상승장
            2026: {"trend": "SIDEWAYS", "volatility": 0.025, "base_multiplier": 1.3}   # 횡보장 (부분)
        }
        
        characteristics = year_characteristics.get(year, {"trend": "SIDEWAYS", "volatility": 0.03, "base_multiplier": 1.0})
        
        yearly_data = {}
        
        for symbol in self.symbols:
            base_price = base_prices.get(symbol, 100) * characteristics["base_multiplier"]
            
            # 해당 연도의 날짜 생성
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            current_date = start_date
            
            data = []
            current_price = base_price
            
            while current_date <= end_date:
                # 연도별 특성에 따른 변동성
                daily_change = random.gauss(0, characteristics["volatility"])
                
                # 추세 추가
                if characteristics["trend"] == "BULL":
                    trend = 0.001  # 상승 트렌드
                elif characteristics["trend"] == "BEAR":
                    trend = -0.001  # 하락 트렌드
                else:
                    trend = 0  # 횡보 트렌드
                
                # 가격 업데이트
                price_change = current_price * (daily_change + trend)
                current_price += price_change
                
                # OHLCV 생성
                open_price = current_price
                volatility = abs(random.gauss(0, characteristics["volatility"]))
                high_price = open_price * (1 + volatility)
                low_price = open_price * (1 - volatility)
                close_price = open_price * (1 + daily_change)
                volume = random.uniform(1000000, 10000000)
                
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
                    'volume': volume,
                    'market_regime': characteristics["trend"]
                })
                
                current_date += timedelta(days=1)
            
            yearly_data[symbol] = data
        
        return yearly_data, characteristics
    
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
        """선물 전략 신호 생성"""
        strategy = self.strategies[strategy_name]
        strategy_type = strategy["strategy_type"]
        
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
    
    def execute_backtest_trade(self, strategy_name, symbol, side, entry_price, data, entry_index):
        """백테스트 거래 실행"""
        strategy = self.strategies[strategy_name]
        leverage = strategy["leverage"]
        stop_loss = strategy["stop_loss"]
        take_profit = strategy["take_profit"]
        
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
                pnl = quantity * entry_price * strategy["avg_return"] * leverage
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
                pnl = quantity * entry_price * strategy["avg_return"] * leverage
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
    
    def run_yearly_backtest(self, year):
        """연도별 백테스트 실행"""
        print(f"📅 {year}년 백테스트 시작!")
        
        # 연도별 데이터 생성
        yearly_data, characteristics = self.generate_yearly_data(year)
        
        # 전략별 자본 초기화
        strategy_performance = {}
        for strategy_name in self.strategies:
            strategy_performance[strategy_name] = {
                "capital": self.capital_per_strategy,
                "trades": [],
                "total_pnl": 0,
                "win_rate": 0,
                "max_drawdown": 0,
                "entry_count": {"BULL_MARKET": 0, "BEAR_MARKET": 0, "SIDEWAYS_MARKET": 0},
                "entry_success": {"BULL_MARKET": 0, "BEAR_MARKET": 0, "SIDEWAYS_MARKET": 0}
            }
        
        # 시장 국면 분석
        market_regime_analysis = {
            "BULL_MARKET": {"days": 0, "percentage": 0},
            "BEAR_MARKET": {"days": 0, "percentage": 0},
            "SIDEWAYS_MARKET": {"days": 0, "percentage": 0}
        }
        
        # 진입 평가
        entry_evaluation = {
            "total_signals": 0,
            "executed_trades": 0,
            "bull_market_entries": 0,
            "bear_market_entries": 0,
            "bull_market_success": 0,
            "bear_market_success": 0,
            "bull_market_success_rate": 0,
            "bear_market_success_rate": 0
        }
        
        # 일별 백테스트 실행
        total_days = len(yearly_data[self.symbols[0]])
        
        for day in range(0, total_days, 7):  # 주 단위로 실행
            current_date = yearly_data[self.symbols[0]][day]['timestamp']
            
            # 시장 국면 분석
            market_regime = self.analyze_market_regime(yearly_data[self.symbols[0]], day)
            market_regime_analysis[market_regime["regime"]]["days"] += 1
            
            # 각 전략별 거래 실행
            for strategy_name, strategy in self.strategies.items():
                # 선호 심볼에서 선택
                available_symbols = [s for s in strategy["preferred_symbols"] if s in self.symbols]
                if not available_symbols:
                    available_symbols = self.symbols
                
                symbol = random.choice(available_symbols)
                symbol_data = yearly_data[symbol]
                
                # 신호 생성
                signal = self.generate_futures_signal(strategy_name, market_regime)
                
                if signal and day < len(symbol_data) - 1:
                    # 진입 기록
                    strategy_performance[strategy_name]["entry_count"][market_regime["regime"]] += 1
                    entry_evaluation["total_signals"] += 1
                    
                    if market_regime["regime"] == "BULL_MARKET":
                        entry_evaluation["bull_market_entries"] += 1
                    elif market_regime["regime"] == "BEAR_MARKET":
                        entry_evaluation["bear_market_entries"] += 1
                    
                    # 거래 실행
                    entry_price = symbol_data[day]['close']
                    trade = self.execute_backtest_trade(strategy_name, symbol, signal, entry_price, symbol_data, day)
                    
                    if trade:
                        strategy_performance[strategy_name]["trades"].append(trade)
                        strategy_performance[strategy_name]["capital"] += trade["pnl"]
                        strategy_performance[strategy_name]["total_pnl"] += trade["pnl"]
                        entry_evaluation["executed_trades"] += 1
                        
                        # 성공 여부 기록
                        if trade["pnl"] > 0:
                            strategy_performance[strategy_name]["entry_success"][market_regime["regime"]] += 1
                            
                            if market_regime["regime"] == "BULL_MARKET":
                                entry_evaluation["bull_market_success"] += 1
                            elif market_regime["regime"] == "BEAR_MARKET":
                                entry_evaluation["bear_market_success"] += 1
        
        # 시장 국면 비율 계산
        total_days_analyzed = sum(market_regime_analysis[regime]["days"] for regime in market_regime_analysis)
        for regime in market_regime_analysis:
            if total_days_analyzed > 0:
                market_regime_analysis[regime]["percentage"] = (market_regime_analysis[regime]["days"] / total_days_analyzed) * 100
        
        # 진입 성공률 계산
        if entry_evaluation["bull_market_entries"] > 0:
            entry_evaluation["bull_market_success_rate"] = (entry_evaluation["bull_market_success"] / entry_evaluation["bull_market_entries"]) * 100
        
        if entry_evaluation["bear_market_entries"] > 0:
            entry_evaluation["bear_market_success_rate"] = (entry_evaluation["bear_market_success"] / entry_evaluation["bear_market_entries"]) * 100
        
        # 전략별 성과 계산
        for strategy_name, perf in strategy_performance.items():
            trades = perf["trades"]
            if trades:
                wins = sum(1 for t in trades if t["pnl"] > 0)
                perf["win_rate"] = (wins / len(trades)) * 100
                perf["final_capital"] = perf["capital"]
                perf["return_rate"] = ((perf["capital"] - self.capital_per_strategy) / self.capital_per_strategy) * 100
                perf["total_trades"] = len(trades)
            else:
                perf["win_rate"] = 0
                perf["final_capital"] = perf["capital"]
                perf["return_rate"] = 0
                perf["total_trades"] = 0
        
        # 연도별 결과 저장 (datetime 객체 제외)
        year_result = {
            "year": year,
            "characteristics": characteristics,
            "strategy_performance": strategy_performance,
            "market_regime_analysis": market_regime_analysis,
            "entry_evaluation": entry_evaluation,
            "total_pnl": sum(perf["total_pnl"] for perf in strategy_performance.values()),
            "total_trades": sum(perf.get("total_trades", 0) for perf in strategy_performance.values()),
            "total_return": ((sum(perf.get("final_capital", perf["capital"]) for perf in strategy_performance.values()) - self.total_capital) / self.total_capital) * 100
        }
        
        return year_result
    
    def run_all_years_backtest(self):
        """전체 연도 백테스트 실행"""
        print("📊 5년치 연도별 백테스트 시작!")
        
        # 각 연도별 백테스트 실행
        for year in [2021, 2022, 2023, 2024, 2025]:
            year_result = self.run_yearly_backtest(year)
            self.yearly_results["years"][year] = year_result
            
            print(f"✅ {year}년 백테스트 완료!")
        
        # 전체 결과 계산
        total_pnl = sum(year["total_pnl"] for year in self.yearly_results["years"].values())
        total_trades = sum(year["total_trades"] for year in self.yearly_results["years"].values())
        
        self.yearly_results.update({
            "end_time": datetime.now().isoformat(),
            "total_pnl": total_pnl,
            "total_trades": total_trades,
            "total_return": (total_pnl / self.total_capital) * 100
        })
        
        return self.yearly_results
    
    def print_yearly_results(self):
        """연도별 결과 출력"""
        results = self.yearly_results
        
        print("\n" + "=" * 100)
        print("🎉 5년치 연도별 선물 전략 백테스트 결과")
        print("=" * 100)
        
        print(f"⏰ 테스트 기간: {results['start_time']} ~ {results['end_time']}")
        print(f"💰 초기 자본: ${results['total_capital']:,.2f}")
        print(f"💰 총 손익: ${results['total_pnl']:+,.2f}")
        print(f"📈 총 수익률: {results['total_return']:+.2f}%")
        print(f"📊 총 거래: {results['total_trades']}회")
        print("")
        
        # 연도별 요약
        print("📅 연도별 성과 요약:")
        print("-" * 80)
        print(f"{'연도':<8} {'시장 특성':<12} {'손익':<12} {'수익률':<10} {'거래':<8} {'상승장':<8} {'하락장':<8} {'횡보장':<8}")
        print("-" * 80)
        
        for year, year_data in results["years"].items():
            characteristics = year_data["characteristics"]
            print(f"{year:<8} {characteristics['trend']:<12} ${year_data['total_pnl']:>+10,.2f} {year_data['total_return']:+8.1f}% {year_data['total_trades']:<8} {year_data['market_regime_analysis']['BULL_MARKET']['days']:<8} {year_data['market_regime_analysis']['BEAR_MARKET']['days']:<8} {year_data['market_regime_analysis']['SIDEWAYS_MARKET']['days']:<8}")
        
        print("")
        
        # 연도별 상세 분석
        for year, year_data in results["years"].items():
            print(f"\n📅 {year}년 상세 분석")
            print("=" * 50)
            
            characteristics = year_data["characteristics"]
            market_analysis = year_data["market_regime_analysis"]
            entry_eval = year_data["entry_evaluation"]
            
            print(f"🎯 시장 특성: {characteristics['trend']} (변동성: {characteristics['volatility']:.1%})")
            print(f"📊 시장 국면 분포:")
            print(f"   상승장: {market_analysis['BULL_MARKET']['days']}일 ({market_analysis['BULL_MARKET']['percentage']:.1f}%)")
            print(f"   하락장: {market_analysis['BEAR_MARKET']['days']}일 ({market_analysis['BEAR_MARKET']['percentage']:.1f}%)")
            print(f"   횡보장: {market_analysis['SIDEWAYS_MARKET']['days']}일 ({market_analysis['SIDEWAYS_MARKET']['percentage']:.1f}%)")
            
            print(f"\n🎯 진입 평가:")
            print(f"   총 신호: {entry_eval['total_signals']}회")
            print(f"   실행 거래: {entry_eval['executed_trades']}회")
            print(f"   상승장 진입: {entry_eval['bull_market_entries']}회 (성공: {entry_eval['bull_market_success']:.0f}회)")
            print(f"   하락장 진입: {entry_eval['bear_market_entries']}회 (성공: {entry_eval['bear_market_success']:.0f}회)")
            print(f"   상승장 성공률: {entry_eval['bull_market_success_rate']:.1f}%")
            print(f"   하락장 성공률: {entry_eval['bear_market_success_rate']:.1f}%")
            
            print(f"\n🎯 전략별 성과:")
            sorted_strategies = sorted(
                year_data['strategy_performance'].items(),
                key=lambda x: x[1]['return_rate'],
                reverse=True
            )
            
            for i, (strategy_name, perf) in enumerate(sorted_strategies, 1):
                strategy = self.strategies[strategy_name]
                print(f"   {i}. {strategy_name}:")
                print(f"      손익: ${perf['total_pnl']:+,.2f} ({perf['return_rate']:+.1f}%)")
                print(f"      거래: {perf['total_trades']}회 (성공률: {perf['win_rate']:.1f}%)")
                print(f"      레버리지: {strategy['leverage']}x")
                print(f"      진입: 상승장 {perf['entry_count']['BULL_MARKET']}회, 하락장 {perf['entry_count']['BEAR_MARKET']}회, 횡보장 {perf['entry_count']['SIDEWAYS_MARKET']}회")
                print(f"      성공: 상승장 {perf['entry_success']['BULL_MARKET']}회, 하락장 {perf['entry_success']['BEAR_MARKET']}회, 횡보장 {perf['entry_success']['SIDEWAYS_MARKET']}회")
        
        print("\n" + "=" * 100)
    
    def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"futures_backtest_yearly_{timestamp}.json"
        
        # datetime 객체를 문자열로 변환
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # 재귀적으로 datetime 객체 변환
        def clean_data(data):
            if isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_data(item) for item in data]
            else:
                return convert_datetime(data)
        
        cleaned_results = clean_data(self.yearly_results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 연도별 백테스트 결과 저장: {filename}")

if __name__ == "__main__":
    backtest = FuturesBacktestYearly()
    results = backtest.run_all_years_backtest()
    backtest.print_yearly_results()
    backtest.save_results()
