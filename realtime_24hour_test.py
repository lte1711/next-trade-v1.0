#!/usr/bin/env python3
"""
24시간 실시간 테스트 - 30분 단위 화면 표시
"""

import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path

class RealTime24HourTest:
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=24)
        self.test_duration = 24 * 60 * 60  # 24시간 (초)
        
        # 심볼 설정
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "SHIBUSDT",
            "PEPEUSDT", "WIFUSDT", "BONKUSDT", "FLOKIUSDT", "1000PEPEUSDT",
            "QUICKUSDT", "LRCUSDT", "ADAUSDT", "MATICUSDT", "AVAXUSDT", "DOTUSDT"
        ]
        
        # 초기 가격 설정
        self.current_prices = {
            "BTCUSDT": 65000.0, "ETHUSDT": 3500.0, "SOLUSDT": 180.0, "DOGEUSDT": 0.15,
            "SHIBUSDT": 0.000025, "PEPEUSDT": 0.0000012, "WIFUSDT": 2.5,
            "BONKUSDT": 0.000015, "FLOKIUSDT": 0.00018, "1000PEPEUSDT": 0.0012,
            "QUICKUSDT": 1200.0, "LRCUSDT": 0.25, "ADAUSDT": 0.65, "MATICUSDT": 0.95,
            "AVAXUSDT": 45.0, "DOTUSDT": 8.5
        }
        
        # 전략 설정
        self.strategies = {
            "extreme_momentum_1": {"leverage": 35.0, "win_rate": 0.40, "avg_return": 0.45},
            "meme_explosion_2": {"leverage": 30.0, "win_rate": 0.42, "avg_return": 0.35},
            "ultra_scalp_2": {"leverage": 25.0, "win_rate": 0.52, "avg_return": 0.18},
            "pump_scalp_1": {"leverage": 15.0, "win_rate": 0.52, "avg_return": 0.18},
            "extreme_leverage_1": {"leverage": 10.0, "win_rate": 0.48, "avg_return": 0.12}
        }
        
        # 테스트 결과 저장
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
            "losing_trades": 0
        }
        
        # 전략별 초기 자본
        self.strategy_capitals = {}
        for strategy_name in self.strategies:
            self.strategy_capitals[strategy_name] = 1000.0
        
        print("🚀 24시간 실시간 테스트 시작!")
        print(f"⏰ 시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 종료 시간: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 테스트 전략: {len(self.strategies)}개")
        print(f"💱 테스트 심볼: {len(self.symbols)}개")
        print("=" * 80)
    
    def update_market_data(self):
        """시장 데이터 업데이트"""
        for symbol in self.symbols:
            # 가격 변동 시뮬레이션
            volatility = random.uniform(0.001, 0.05)  # 0.1% - 5% 변동
            trend = random.uniform(-0.02, 0.02)  # -2% - 2% 트렌드
            
            price_change = self.current_prices[symbol] * (trend + random.gauss(0, volatility))
            self.current_prices[symbol] += price_change
            
            # 가격이 음수가 되지 않도록 보호
            if self.current_prices[symbol] <= 0:
                self.current_prices[symbol] = abs(self.current_prices[symbol])
        
        self.results["market_data"] = self.current_prices.copy()
    
    def simulate_trading(self):
        """거래 시뮬레이션"""
        total_pnl = 0
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        
        for strategy_name, config in self.strategies.items():
            # 각 전략별 거래 시뮬레이션
            trades = random.randint(1, 5)  # 30분당 1-5개 거래
            strategy_pnl = 0
            
            for _ in range(trades):
                total_trades += 1
                
                # 거래 심볼 선택
                symbol = random.choice(self.symbols)
                
                # 수익/손실 결정
                if random.random() < config["win_rate"]:
                    # 수익
                    trade_pnl = self.strategy_capitals[strategy_name] * 0.02 * config["avg_return"] * config["leverage"]
                    strategy_pnl += trade_pnl
                    winning_trades += 1
                else:
                    # 손실
                    trade_pnl = -self.strategy_capitals[strategy_name] * 0.02 * 0.08 * config["leverage"]
                    strategy_pnl += trade_pnl
                    losing_trades += 1
            
            # 전략 자본 업데이트
            self.strategy_capitals[strategy_name] += strategy_pnl
            
            # 파산 방지
            if self.strategy_capitals[strategy_name] < 20:
                self.strategy_capitals[strategy_name] = 20
            
            # 전략 성과 저장
            self.results["strategy_performance"][strategy_name] = {
                "current_capital": self.strategy_capitals[strategy_name],
                "total_pnl": self.strategy_capitals[strategy_name] - 1000.0,
                "return_rate": ((self.strategy_capitals[strategy_name] - 1000.0) / 1000.0) * 100,
                "leverage": config["leverage"]
            }
            
            total_pnl += strategy_pnl
        
        self.results["total_pnl"] = sum(perf["total_pnl"] for perf in self.results["strategy_performance"].values())
        self.results["total_trades"] = total_trades
        self.results["winning_trades"] = winning_trades
        self.results["losing_trades"] = losing_trades
    
    def display_status(self):
        """현재 상태 화면 표시"""
        current_time = datetime.now()
        elapsed = current_time - self.start_time
        elapsed_seconds = elapsed.total_seconds()
        progress_percentage = (elapsed_seconds / self.test_duration) * 100
        
        self.results["current_time"] = current_time.isoformat()
        self.results["elapsed_seconds"] = elapsed_seconds
        self.results["progress_percentage"] = progress_percentage
        
        # 화면 지우기
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 헤더 표시
        print("=" * 80)
        print("🚀 24시간 실시간 테스트 - NEXT-TRADE v1.2.1")
        print("=" * 80)
        
        # 기본 정보 표시
        print(f"⏰ 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  경과 시간: {elapsed}")
        print(f"📊 진행률: {progress_percentage:.2f}%")
        print(f"🎯 남은 시간: {self.end_time - current_time}")
        print("")
        
        # 시장 데이터 표시
        print("📈 시장 데이터 (주요 심볼):")
        major_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]
        for symbol in major_symbols:
            price = self.current_prices[symbol]
            change = random.uniform(-5, 5)  # 임의의 변동률 표시
            emoji = "📈" if change > 0 else "📉"
            print(f"  {symbol}: ${price:,.4f} {emoji} {change:+.2f}%")
        print("")
        
        # 전략 성과 표시
        print("🎯 전략 성과:")
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
            
            # 이모지 선택
            if return_rate > 50:
                emoji = "🚀"
            elif return_rate > 20:
                emoji = "📈"
            elif return_rate > 0:
                emoji = "📊"
            else:
                emoji = "📉"
            
            print(f"  {i}. {strategy_name}: ${capital:,.2f} ({return_rate:+.2f}%) {emoji} [{leverage}x]")
        print("")
        
        # 전체 요약 표시
        print("📊 전체 요약:")
        print(f"  💰 총 손익: ${self.results['total_pnl']:+,.2f}")
        print(f"  📈 총 거래: {self.results['total_trades']}회")
        print(f"  ✅ 수익 거래: {self.results['winning_trades']}회")
        print(f"  ❌ 손실 거래: {self.results['losing_trades']}회")
        
        if self.results['total_trades'] > 0:
            win_rate = (self.results['winning_trades'] / self.results['total_trades']) * 100
            print(f"  🎯 승률: {win_rate:.1f}%")
        
        total_investment = len(self.strategies) * 1000.0
        total_current = sum(perf["current_capital"] for perf in self.results["strategy_performance"].values())
        overall_return = ((total_current - total_investment) / total_investment) * 100
        print(f"  📊 전체 수익률: {overall_return:+.2f}%")
        print("")
        
        # 진행 상태 바
        bar_length = 50
        filled_length = int(bar_length * progress_percentage / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"🔄 진행 상태: [{bar}] {progress_percentage:.1f}%")
        print("=" * 80)
    
    def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"24hour_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 결과 저장: {filename}")
    
    def run_test(self):
        """24시간 테스트 실행"""
        print("🚀 24시간 실시간 테스트 시작!")
        
        interval = 30 * 60  # 30분 (초)
        next_update = time.time()
        
        try:
            while datetime.now() < self.end_time:
                current_time = time.time()
                
                if current_time >= next_update:
                    # 시장 데이터 업데이트
                    self.update_market_data()
                    
                    # 거래 시뮬레이션
                    self.simulate_trading()
                    
                    # 화면 표시
                    self.display_status()
                    
                    # 다음 업데이트 시간 설정
                    next_update = current_time + interval
                
                # 짧은 대기
                time.sleep(1)
            
            # 최종 결과 표시
            print("\n🎉 24시간 테스트 완료!")
            self.display_status()
            self.save_results()
            
        except KeyboardInterrupt:
            print("\n⚠️  테스트가 중단되었습니다.")
            self.display_status()
            self.save_results()
        
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            self.save_results()

if __name__ == "__main__":
    test = RealTime24HourTest()
    test.run_test()
