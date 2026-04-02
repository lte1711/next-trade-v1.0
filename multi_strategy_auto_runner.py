#!/usr/bin/env python3
"""
멀티 전략 자동 실행 모듈
프로젝트 시작 시 멀티 전략 시스템을 자동으로 실행하고 관리
"""

import sys
import time
import threading
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from strategies.multi_strategy_manager import MultiStrategyManager


class MultiStrategyAutoRunner:
    """멀티 전략 자동 실행기"""
    
    def __init__(self):
        self.manager = MultiStrategyManager()
        self.is_running = False
        self.thread = None
        self.evaluation_interval = 60  # 60초마다 평가
        self.active_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        self.performance_log = []
    
    def start_auto_run(self):
        """자동 실행 시작"""
        if self.is_running:
            print("FACT: 멀티 전략 자동 실행이 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._auto_run_loop, daemon=True)
        self.thread.start()
        print("FACT: 멀티 전략 자동 실행이 시작되었습니다.")
    
    def stop_auto_run(self):
        """자동 실행 중지"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("FACT: 멀티 전략 자동 실행이 중지되었습니다.")
    
    def _auto_run_loop(self):
        """자동 실행 루프"""
        print(f"FACT: 멀티 전략 자동 실행 루프 시작 - {datetime.now()}")
        
        while self.is_running:
            try:
                # 각 심볼별 전략 평가
                for symbol in self.active_symbols:
                    self._evaluate_symbol_strategies(symbol)
                
                # 성과 로그 기록
                self._log_performance()
                
                # 대기
                time.sleep(self.evaluation_interval)
                
            except Exception as e:
                print(f"FACT: 자동 실행 루프 오류 - {e}")
                time.sleep(10)  # 오류 시 10초 대기
    
    def _evaluate_symbol_strategies(self, symbol: str):
        """심볼별 전략 평가"""
        try:
            # 테스트 데이터 생성 (실제로는 시장 데이터 API에서 가져옴)
            test_closes = self._generate_test_prices()
            test_volumes = self._generate_test_volumes()
            
            # 전략 평가
            result = self.manager.evaluate_strategies(symbol, test_closes, test_volumes)
            
            # 신호 처리
            signal = result["aggregated_signal"]["signal"]
            confidence = result["aggregated_signal"]["confidence"]
            
            if signal != "HOLD" and confidence > 0.5:
                print(f"FACT: [{symbol}] {signal} 신호 생성 (확신도: {confidence:.2f})")
                self._handle_signal(symbol, signal, result)
            
        except Exception as e:
            print(f"FACT: {symbol} 전략 평가 오류 - {e}")
    
    def _generate_test_prices(self) -> List[float]:
        """테스트 가격 데이터 생성"""
        base_price = 50000.0  # BTC 기준 가격
        volatility = 0.02  # 2% 변동성
        
        prices = []
        current_price = base_price
        
        for i in range(50):
            # 랜덤 변동 생성
            import random
            change = random.uniform(-volatility, volatility) * current_price
            current_price += change
            prices.append(current_price)
        
        return prices
    
    def _generate_test_volumes(self) -> List[float]:
        """테스트 거래량 데이터 생성"""
        base_volume = 1000.0
        volumes = []
        
        for i in range(50):
            import random
            volume = base_volume * random.uniform(0.5, 2.0)
            volumes.append(volume)
        
        return volumes
    
    def _handle_signal(self, symbol: str, signal: str, result: Dict[str, Any]):
        """신호 처리"""
        signal_info = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "signal": signal,
            "confidence": result["aggregated_signal"]["confidence"],
            "contributing_strategies": result["aggregated_signal"]["contributing_strategies"],
            "market_regime": result["market_regime"]
        }
        
        # 실제로는 여기서 주문 실행 또는 알림 전송
        print(f"FACT: 신호 처리 - {signal_info}")
    
    def _log_performance(self):
        """성과 로그 기록"""
        performance = self.manager.get_strategy_performance()
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_strategies": performance["active_strategies"],
            "total_strategies": performance["total_strategies"],
            "market_regime": performance["current_market_regime"]
        }
        
        self.performance_log.append(log_entry)
        
        # 로그 크기 제한
        if len(self.performance_log) > 100:
            self.performance_log = self.performance_log[-50:]
    
    def get_status(self) -> Dict[str, Any]:
        """실행 상태 반환"""
        return {
            "is_running": self.is_running,
            "active_symbols": self.active_symbols,
            "evaluation_interval": self.evaluation_interval,
            "performance": self.manager.get_strategy_performance(),
            "log_count": len(self.performance_log)
        }


class MultiStrategyInitializer:
    """멀티 전략 초기화기"""
    
    @staticmethod
    def initialize():
        """멀티 전략 시스템 초기화"""
        print("FACT: 멀티 전략 시스템 초기화 시작")
        
        try:
            # 멀티 전략 관리자 생성
            manager = MultiStrategyManager()
            performance = manager.get_strategy_performance()
            
            print(f"FACT: 활성 전략 수: {performance['total_strategies']}")
            print(f"FACT: 활성 전략 목록: {performance['active_strategies']}")
            print(f"FACT: 시장 레짐: {performance['current_market_regime']}")
            
            # 자동 실행기 생성
            auto_runner = MultiStrategyAutoRunner()
            
            print("FACT: 멀티 전략 시스템 초기화 완료")
            return manager, auto_runner
            
        except Exception as e:
            print(f"FACT: 멀티 전략 시스템 초기화 실패 - {e}")
            return None, None


# 전역 변수
_global_manager = None
_global_auto_runner = None


def get_multi_strategy_manager():
    """전역 멀티 전략 관리자 가져오기"""
    global _global_manager
    if _global_manager is None:
        _global_manager, _global_auto_runner = MultiStrategyInitializer.initialize()
    return _global_manager


def get_auto_runner():
    """전역 자동 실행기 가져오기"""
    global _global_auto_runner
    if _global_auto_runner is None:
        _global_manager, _global_auto_runner = MultiStrategyInitializer.initialize()
    return _global_auto_runner


def start_multi_strategy_system():
    """멀티 전략 시스템 시작"""
    print("FACT: 멀티 전략 시스템 시작 요청")
    
    manager = get_multi_strategy_manager()
    auto_runner = get_auto_runner()
    
    if manager and auto_runner:
        auto_runner.start_auto_run()
        print("FACT: 멀티 전략 시스템이 성공적으로 시작되었습니다.")
        return True
    else:
        print("FACT: 멀티 전략 시스템 시작 실패")
        return False


def stop_multi_strategy_system():
    """멀티 전략 시스템 중지"""
    print("FACT: 멀티 전략 시스템 중지 요청")
    
    auto_runner = get_auto_runner()
    if auto_runner:
        auto_runner.stop_auto_run()
        print("FACT: 멀티 전략 시스템이 중지되었습니다.")
        return True
    else:
        print("FACT: 멀티 전략 시스템이 실행 중이 아님")
        return False


if __name__ == "__main__":
    # 테스트 실행
    print("FACT: 멀티 전략 자동 실행 테스트")
    
    # 시스템 시작
    if start_multi_strategy_system():
        print("FACT: 10초 후 자동 중지")
        time.sleep(10)
        stop_multi_strategy_system()
    
    print("FACT: 테스트 완료")
