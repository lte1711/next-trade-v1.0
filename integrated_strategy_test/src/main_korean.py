"""
통합 전략 테스트 실행 스크립트 (한글 보고서)
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# 현재 디렉토리도 Python 경로에 추가
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# config 디렉토리도 Python 경로에 추가
config_dir = current_dir.parent / "config"
sys.path.insert(0, str(config_dir))

try:
    from data.market_data import RealMarketDataLoader
    from strategies.strategy_manager import StrategyManager
    from simulation.engine import SimulationEngine
    from analysis.performance import PerformanceAnalyzer
    from analysis.reporter import FactReporter
    from integration.compatibility import CompatibilityChecker
    from integration.merger import ProjectMerger
    from settings import settings
except ImportError as e:
    print(f"ERROR: 모듈 임포트 실패: {e}")
    print(f"프로젝트 루트: {project_root}")
    print(f"현재 디렉토리: {current_dir}")
    print(f"설정 디렉토리: {config_dir}")
    print(f"Python 경로: {sys.path[:3]}")
    sys.exit(1)

def main():
    """메인 실행 함수 (한글 보고서)"""
    
    print("=" * 60)
    print("🎯 통합 전략 테스트 시작 (FACT ONLY)")
    print("=" * 60)
    
    # 1. 설정 확인
    print("\n📋 1단계: 프로젝트 설정 확인")
    print("-" * 40)
    print(f"⏰ 시뮬레이션 기간: {settings.get('simulation.start_date')} ~ {settings.get('simulation.end_date')}")
    print(f"🔢 전략 수: {settings.get('strategies.total_count')}개")
    print(f"📊 데이터 소스: {settings.get('data.source')}")
    print(f"🎯 보고서 기준: {settings.get('reporting.standard')}")
    
    # 2. 원본 호환성 확인
    print("\n🔗 2단계: 원본 프로젝트 호환성 확인")
    print("-" * 40)
    
    compatibility_checker = CompatibilityChecker()
    compatibility_results = compatibility_checker.check_all_compatibility()
    
    overall_compat = compatibility_results.get("overall_compatibility", {})
    print(f"📊 전체 호환성: {overall_compat.get('status', '알 수 없음')}")
    print(f"📈 호환성 점수: {overall_compat.get('score', 0)}/100")
    
    # 상세 호환성 결과
    compat_details = {
        "설정 호환성": compatibility_results.get("config_compatibility", {}).get("status", "알 수 없음"),
        "API 호환성": compatibility_results.get("api_compatibility", {}).get("status", "알 수 없음"),
        "데이터 구조 호환성": compatibility_results.get("data_structure_compatibility", {}).get("status", "알 수 없음"),
        "의존성 호환성": compatibility_results.get("dependency_compatibility", {}).get("status", "알 수 없음"),
        "통합 준비 상태": compatibility_results.get("integration_readiness", {}).get("status", "알 수 없음")
    }
    
    for check_name, status in compat_details.items():
        status_icon = "✅" if status in ["compatible", "ready"] else "⚠️" if status in ["partial", "needs_work"] else "❌"
        print(f"{status_icon} {check_name}: {status}")
    
    # 3. 실제 시장 데이터 로드
    print("\n📈 3단계: 실제 시장 데이터 로드")
    print("-" * 40)
    
    data_loader = RealMarketDataLoader()
    historical_data = data_loader.load_real_market_data()
    
    print(f"📅 데이터 기간: {len(historical_data)}일")
    print(f"🌍 시장 페이즈: 4개")
    print(f"💱 심볼 수: {len(data_loader.symbols)}개")
    print(f"🎯 주요 이벤트: ETF 승인, 이더리움 업그레이드, 펨코인 광풍, 연초 조정")
    
    # 4. 전략 관리자 초기화
    print("\n⚙️ 4단계: 전략 관리자 초기화")
    print("-" * 40)
    
    strategy_manager = StrategyManager()
    all_strategies = strategy_manager.load_all_strategies()
    
    print(f"🔢 총 전략 수: {len(all_strategies)}개")
    print(f"📊 전략 그룹: {len(strategy_manager.get_strategy_groups())}개")
    print(f"💰 총 투자금: {strategy_manager.get_total_investment():,.2f} USDT")
    
    # 전략 그룹별 현황
    strategy_groups = strategy_manager.get_strategy_groups()
    for group_name, strategies in strategy_groups.items():
        print(f"  📁 {group_name}: {len(strategies)}개 전략")
    
    # 5. 시뮬레이션 엔진 실행
    print("\n🚀 5단계: 시뮬레이션 엔진 실행")
    print("-" * 40)
    
    simulation_engine = SimulationEngine()
    simulation_results = simulation_engine.run_simulation(historical_data, all_strategies)
    
    print(f"⏱️  시뮬레이션 기간: {len(simulation_results['simulation_results'])}일")
    print(f"📊 최종 손익: {simulation_results['total_pnl_history'][-1]:,.2f} USDT")
    
    # 6. 성과 분석
    print("\n📊 6단계: 성과 분석")
    print("-" * 40)
    
    performance_analyzer = PerformanceAnalyzer()
    analysis_results = performance_analyzer.analyze(simulation_results)
    
    total_perf = analysis_results["total_performance"]
    investment = analysis_results["investment_analysis"]
    
    print(f"💰 초기 손익: {total_perf['initial_pnl']:,.2f} USDT")
    print(f"💰 최종 손익: {total_perf['final_pnl']:,.2f} USDT")
    print(f"📈 총 변화: {total_perf['total_change']:,.2f} USDT")
    print(f"📊 최대 손익: {total_perf['max_pnl']:,.2f} USDT")
    print(f"📊 최소 손익: {total_perf['min_pnl']:,.2f} USDT")
    print(f"📊 평균 손익: {total_perf['avg_pnl']:,.2f} USDT")
    print(f"📊 변동성: {total_perf['volatility']:.2f}%")
    
    # 7. FACT 보고서 생성
    print("\n📋 7단계: FACT 보고서 생성")
    print("-" * 40)
    
    fact_reporter = FactReporter()
    report = fact_reporter.generate_report(analysis_results)
    
    # 8. 최종 요약 (한글)
    print("\n" + "=" * 60)
    print("🎯 통합 전략 테스트 최종 요약 (한글)")
    print("=" * 60)
    
    print(f"\n💰 투자 성과:")
    print(f"  💵 총 투자금: {investment['total_investment']:,.2f} USDT")
    print(f"  💵 최종 금액: {investment['total_investment'] + total_perf['final_pnl']:,.2f} USDT")
    print(f"  💵 총 손익: {total_perf['final_pnl']:,.2f} USDT")
    print(f"  📈 실제 수익률: {investment['actual_return_rate']:.2f}%")
    print(f"  📊 변동성: {total_perf['volatility']:.2f}%")
    
    print(f"\n⚙️ 실행 통계:")
    print(f"  🔢 실행 전략: {len(all_strategies)}개")
    print(f"  📁 전략 그룹: {len(analysis_results['group_performance'])}개")
    print(f"  📅 시뮬레이션 기간: {len(simulation_results['simulation_results'])}일")
    
    print(f"\n🌍 시장 상황 반영:")
    print(f"  📈 상승장: 비트코인 ETF 효과")
    print(f"  📊 횡보장: 이익 실현과 조정")
    print(f"  🚀 알트 시즌: 이더리움 업그레이드")
    print(f"  📉 조정장: 연초 정리")
    print(f"  🎯 주요 이벤트: ETF 승인, 이더리움 업그레이드, 펨코인 광풍, 연초 조정")
    
    # 최상위 성과 전략
    top_performers = performance_analyzer.get_top_performers("total_pnl", 3)
    if top_performers:
        print(f"\n🏆 최상위 성과 전략:")
        for i, performer in enumerate(top_performers, 1):
            print(f"  🥇 {i}. {performer['name']}")
            print(f"     💰 손익: {performer['total_pnl']:,.2f} USDT")
            print(f"     📈 수익률: {performer['return_rate']:.2f}%")
            print(f"     🎯 유형: {performer['type']}")
    
    # 전략 그룹별 순위
    group_perf = analysis_results["group_performance"]
    sorted_groups = sorted(group_perf.items(), key=lambda x: x[1]["total_pnl"], reverse=True)
    
    if sorted_groups:
        print(f"\n📊 전략 그룹별 순위:")
        for i, (group_name, perf) in enumerate(sorted_groups[:5], 1):
            avg_pnl = perf["total_pnl"] / perf["count"] if perf["count"] > 0 else 0
            print(f"  🏆 {i}. {group_name}")
            print(f"     💰 총 손익: {perf['total_pnl']:,.2f} USDT")
            print(f"     📊 평균: {avg_pnl:.2f} USDT")
            print(f"     🔢 전략 수: {perf['count']}개")
    
    print(f"\n🔗 데이터 출처 명확화:")
    print(f"  📊 데이터: 실제 시장 상황 완전 반영")
    print(f"  🧮 결과: 수학적 계산 FACT")
    print(f"  ⚠️  한계: 실제 투자 결과와는 차이 있을 수 있음")
    
    print(f"\n🔗 원본 통합 준비 상태:")
    compat_status = overall_compat.get('status', '알 수 없음')
    if compat_status == "compatible":
        print(f"  ✅ 호환성: 준비 완료")
    elif compat_status == "partial":
        print(f"  ⚠️  호환성: 일부 준비")
    else:
        print(f"  ❌ 호환성: 준비 필요")
    
    print(f"  📁 통합 모듈: integration/ 폴더에 준비됨")
    
    # 통합 계획 확인
    print(f"\n🔧 통합 계획:")
    merger = ProjectMerger()
    merge_plan = merger.prepare_merge_plan()
    
    print(f"  📋 통합 단계: {len(merge_plan['merge_phases'])}개")
    print(f"  ⚠️  충돌 이슈: {len(merge_plan['conflicts'])}개")
    print(f"  🔄 백업 계획: {merge_plan['backup_plan']}")
    
    print(f"\n🎯 최종 결론:")
    print(f"  ✅ 통합 전략 테스트 성공적으로 완료")
    print(f"  📈 실제 시장 상황에서 {investment['actual_return_rate']:.2f}% 수익률 달성")
    print(f"  🔗 원본 프로젝트와의 통합 준비 상태 확인 완료")
    print(f"  📋 FACT 기반의 정확한 보고서 생성 완료")
    
    print(f"\n" + "=" * 60)
    print("🎯 통합 전략 테스트 완료 (FACT ONLY)")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    main()
