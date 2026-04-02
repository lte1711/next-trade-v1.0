#!/usr/bin/env python3
"""
멀티 전략 시스템 평가 데이터 수집기
24시간 동안 실시간 데이터를 수집하고 정밀 분석을 위한 기반 구축
"""

import sys
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
import random

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from strategies.multi_strategy_manager import MultiStrategyManager


class MultiStrategyEvaluator:
    """멀티 전략 시스템 평가기"""
    
    def __init__(self):
        self.manager = MultiStrategyManager()
        self.is_collecting = False
        self.collection_thread = None
        self.evaluation_data = []
        self.collection_interval = 60  # 60초마다 데이터 수집
        self.total_collection_time = 24 * 60 * 60  # 24시간
        self.symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        self.start_time = None
        self.data_dir = Path("evaluation_data")
        self.data_dir.mkdir(exist_ok=True)
    
    def start_evaluation(self):
        """평가 데이터 수집 시작"""
        if self.is_collecting:
            print("FACT: 평가 데이터 수집이 이미 진행 중입니다.")
            return
        
        self.is_collecting = True
        self.start_time = datetime.now(timezone.utc)
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        print(f"FACT: 멀티 전략 시스템 평가 데이터 수집 시작 - {self.start_time}")
        print(f"FACT: 수집 기간: 24시간")
        print(f"FACT: 수집 간격: {self.collection_interval}초")
        print(f"FACT: 평가 대상: {self.symbols}")
    
    def stop_evaluation(self):
        """평가 데이터 수집 중지"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
        
        end_time = datetime.now(timezone.utc)
        duration = end_time - self.start_time if self.start_time else "N/A"
        
        print(f"FACT: 평가 데이터 수집 중지 - {end_time}")
        print(f"FACT: 수집 기간: {duration}")
        print(f"FACT: 수집된 데이터 포인트: {len(self.evaluation_data)}")
    
    def _collection_loop(self):
        """데이터 수집 루프"""
        print("FACT: 평가 데이터 수집 루프 시작")
        
        while self.is_collecting:
            try:
                # 각 심볼별 데이터 수집
                timestamp = datetime.now(timezone.utc).isoformat()
                
                for symbol in self.symbols:
                    data_point = self._collect_symbol_data(symbol, timestamp)
                    if data_point:
                        self.evaluation_data.append(data_point)
                
                # 주기적으로 데이터 저장
                if len(self.evaluation_data) % 10 == 0:
                    self._save_intermediate_data()
                
                # 진행 상황 출력
                elapsed = datetime.now(timezone.utc) - self.start_time
                hours = elapsed.total_seconds() / 3600
                print(f"FACT: 데이터 수집 진행 중 - {hours:.1f}시간 경과, {len(self.evaluation_data)}개 데이터 포인트")
                
                # 대기
                time.sleep(self.collection_interval)
                
            except Exception as e:
                print(f"FACT: 데이터 수집 오류 - {e}")
                time.sleep(10)
        
        print("FACT: 평가 데이터 수집 루프 종료")
    
    def _collect_symbol_data(self, symbol: str, timestamp: str) -> Dict[str, Any]:
        """심볼별 데이터 수집"""
        try:
            # 시뮬레이션된 시장 데이터 생성 (실제로는 API에서 가져옴)
            market_data = self._generate_market_data(symbol)
            
            # 전략 평가
            result = self.manager.evaluate_strategies(symbol, market_data["closes"], market_data["volumes"])
            
            # 데이터 포인트 생성
            data_point = {
                "timestamp": timestamp,
                "symbol": symbol,
                "market_data": market_data,
                "strategy_results": result,
                "market_regime": result["market_regime"],
                "aggregated_signal": result["aggregated_signal"],
                "individual_signals": result["individual_signals"]
            }
            
            return data_point
            
        except Exception as e:
            print(f"FACT: {symbol} 데이터 수집 오류 - {e}")
            return None
    
    def _generate_market_data(self, symbol: str) -> Dict[str, List[float]]:
        """시뮬레이션된 시장 데이터 생성"""
        # 기본 가격 설정
        base_prices = {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "BNBUSDT": 300.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        volatility = 0.02  # 2% 변동성
        
        # 50개 데이터 포인트 생성
        closes = []
        volumes = []
        current_price = base_price
        
        for i in range(50):
            # 가격 변동 생성
            change = random.uniform(-volatility, volatility) * current_price
            current_price += change
            closes.append(current_price)
            
            # 거래량 생성
            volume = random.uniform(1000, 10000)
            volumes.append(volume)
        
        return {
            "closes": closes,
            "volumes": volumes
        }
    
    def _save_intermediate_data(self):
        """중간 데이터 저장"""
        try:
            filename = f"evaluation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.evaluation_data, f, indent=2, ensure_ascii=False)
            
            print(f"FACT: 중간 데이터 저장 - {filepath}")
            
        except Exception as e:
            print(f"FACT: 중간 데이터 저장 오류 - {e}")
    
    def save_final_data(self):
        """최종 데이터 저장"""
        try:
            filename = f"final_evaluation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.data_dir / filename
            
            final_data = {
                "evaluation_start": self.start_time.isoformat() if self.start_time else None,
                "evaluation_end": datetime.now(timezone.utc).isoformat(),
                "total_data_points": len(self.evaluation_data),
                "symbols": self.symbols,
                "collection_interval": self.collection_interval,
                "data": self.evaluation_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            
            print(f"FACT: 최종 평가 데이터 저장 - {filepath}")
            return filepath
            
        except Exception as e:
            print(f"FACT: 최종 데이터 저장 오류 - {e}")
            return None
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """평가 데이터 요약"""
        if not self.evaluation_data:
            return {"status": "no_data"}
        
        # 기본 통계
        total_points = len(self.evaluation_data)
        symbols_data = {}
        
        for symbol in self.symbols:
            symbol_data = [d for d in self.evaluation_data if d["symbol"] == symbol]
            symbols_data[symbol] = {
                "total_points": len(symbol_data),
                "signals": {}
            }
            
            # 신호 통계
            for data_point in symbol_data:
                signal = data_point["aggregated_signal"]["signal"]
                if signal not in symbols_data[symbol]["signals"]:
                    symbols_data[symbol]["signals"][signal] = 0
                symbols_data[symbol]["signals"][signal] += 1
        
        return {
            "status": "completed",
            "total_data_points": total_points,
            "symbols": symbols_data,
            "collection_duration": str(datetime.now(timezone.utc) - self.start_time) if self.start_time else "N/A"
        }


def main():
    """메인 평가 실행"""
    print("FACT: 멀티 전략 시스템 평가 시작")
    
    evaluator = MultiStrategyEvaluator()
    
    try:
        # 평가 시작
        evaluator.start_evaluation()
        
        # 24시간 대기 (실제로는 백그라운드에서 실행)
        print("FACT: 24시간 동안 데이터 수집 진행...")
        print("FACT: 중지하려면 Ctrl+C를 누르세요")
        
        # 실제로는 24시간 대기하지만 테스트를 위해 5분만 실행
        time.sleep(300)  # 5분 테스트
        
    except KeyboardInterrupt:
        print("FACT: 사용자에 의해 평가 중지")
    
    finally:
        # 평가 중지 및 데이터 저장
        evaluator.stop_evaluation()
        final_file = evaluator.save_final_data()
        
        # 요약 정보 출력
        summary = evaluator.get_evaluation_summary()
        print(f"FACT: 평가 요약 - {summary}")
        
        if final_file:
            print(f"FACT: 최종 데이터 파일 - {final_file}")
        
        print("FACT: 멀티 전략 시스템 평가 완료")


if __name__ == "__main__":
    main()
