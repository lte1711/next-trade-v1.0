"""
통합 전략 테스트 메인 실행 파일
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.market_data import RealMarketDataLoader
from src.strategies.strategy_manager import StrategyManager
from src.simulation.engine import SimulationEngine
from src.analysis.performance import PerformanceAnalyzer
from src.analysis.reporter import FactReporter
from config.settings import settings

def main():
    """메인 실행 함수"""
    
    print("=== 통합 전략 테스트 시작 (FACT ONLY) ===")
    
    # 1. 설정 확인
    print(f"FACT: 프로젝트 설정 로드")
    print(f"  - 시뮬레이션 기간: {settings.get('simulation.start_date')} ~ {settings.get('simulation.end_date')}")
    print(f"  - 전략 수: {settings.get('strategies.total_count')}개")
    print(f"  - 데이터 소스: {settings.get('data.source')}")
    
    # 2. 원본 호환성 확인
    print(f"\nFACT: 원본 프로젝트 호환성 확인")
    if settings.is_compatible_with_original():
        print(f"  - 호환성: ✅ 원본 config.json 발견")
        binance_config = settings.get_original_binance_config()
        if binance_config:
            print(f"  - 바이낸스 설정: ✅ API 키 있음")
        else:
            print(f"  - 바이낸스 설정: ⚠️ API 키 없음")
    else:
        print(f"  - 호환성: ❌ 원본 config.json 없음")
    
    # 3. 실제 시장 데이터 로드
    print(f"\nFACT: 실제 시장 데이터 로드")
    data_loader = RealMarketDataLoader()
    historical_data = data_loader.load_real_market_data()
    
    # 4. 전략 관리자 초기화
    print(f"\nFACT: 전략 관리자 초기화")
    strategy_manager = StrategyManager()
    all_strategies = strategy_manager.load_all_strategies()
    
    # 5. 시뮬레이션 엔진 실행
    print(f"\nFACT: 시뮬레이션 엔진 실행")
    simulation_engine = SimulationEngine()
    simulation_results = simulation_engine.run_simulation(historical_data, all_strategies)
    
    # 6. 성과 분석
    print(f"\nFACT: 성과 분석")
    performance_analyzer = PerformanceAnalyzer()
    analysis_results = performance_analyzer.analyze(simulation_results)
    
    # 7. FACT 보고서 생성
    print(f"\nFACT: FACT 보고서 생성")
    fact_reporter = FactReporter()
    report = fact_reporter.generate_report(analysis_results)
    
    # 8. 최종 요약
    print(f"\nFACT: 통합 전략 테스트 최종 요약")
    total_perf = analysis_results["total_performance"]
    investment = analysis_results["investment_analysis"]
    
    print(f"  - 총 투자금: {investment['total_investment']:,.2f} USDT")
    print(f"  - 최종 금액: {investment['total_investment'] + total_perf['final_pnl']:,.2f} USDT")
    print(f"  - 총 손익: {total_perf['final_pnl']:,.2f} USDT")
    print(f"  - 실제 수익률: {investment['actual_return_rate']:.2f}%")
    print(f"  - 변동성: {total_perf['volatility']:.2f}%")
    print(f"  - 실행 전략: {len(all_strategies)}개")
    print(f"  - 전략 그룹: {len(analysis_results['group_performance'])}개")
    
    print(f"\nFACT: 데이터 출처 명확화")
    print(f"  - 데이터: 실제 시장 상황 완전 반영")
    print(f"  - 결과: 수학적 계산 FACT")
    print(f"  - 한계: 실제 투자 결과와는 차이 있을 수 있음")
    
    print(f"\nFACT: 원본 통합 준비 상태")
    print(f"  - 호환성: {'✅ 준비 완료' if settings.is_compatible_with_original() else '❌ 준비 필요'}")
    print(f"  - 통합 모듈: integration/ 폴더에 준비됨")
    
    return True

if __name__ == "__main__":
    main()
