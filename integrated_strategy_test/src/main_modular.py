"""
모듈화된 테스트 프로그램 - 메인 실행 파일
모듈화된 시뮬레이터를 실행하는 메인 엔트리 포인트
"""

from modules.simulator import ModularTradingSimulator
import json
from pathlib import Path


def main():
    """메인 실행 함수"""
    print("🎯 모듈화된 트레이딩 시뮬레이터 v1.1")
    print("모듈화된 특징:")
    print("  📊 시장 분석 모듈")
    print("  💰 포트폴리오 관리 모듈")
    print("  🔄 실시간 데이터 수집 모듈")
    print("  🎯 통합 시뮬레이터 모듈")
    print("  📊 모듈화된 구조")
    print("  ⚡ 진입 가능 심볼 없으면 계속 분석 (3분 주기)")
    print()
    
    # 모듈화된 시뮬레이터 생성
    simulator = ModularTradingSimulator(
        symbol_count=10,  # 최대 10개 심볼
        replacement_threshold=-0.8  # -0.8% 교체 기준
    )
    
    # 30분 시뮬레이션 실행 (3분 주기)
    print("🚀 30분 시뮬레이션 시작...")
    result = simulator.run_simulation(duration_minutes=30, update_interval=3)
    
    if "error" not in result:
        # 최종 결과 출력
        print("\n" + "=" * 80)
        print("🎯 최종 모듈화된 시뮬레이션 결과")
        print("=" * 80)
        
        metadata = result["simulation_metadata"]
        print(f"\n📋 시뮬레이션 정보:")
        print(f"  💰 초기 자본: ${metadata['initial_capital']:.2f}")
        print(f"  💰 최종 자본: ${metadata['final_capital']:.2f}")
        print(f"  📈 총 손익: ${metadata['total_pnl']:+.2f}")
        print(f"  📊 손익률: {metadata['pnl_percent']:+.2f}%")
        print(f"  💰 총 수수료: ${metadata['total_fees_paid']:.2f}")
        print(f"  📈 순 손익: ${metadata['net_pnl']:+.2f}")
        print(f"  📊 순 손익률: {metadata['net_pnl_percent']:+.2f}%")
        print(f"  ⏰ 시작 시간: {metadata['simulation_start_time']}")
        print(f"  ⏰ 종료 시간: {metadata['simulation_end_time']}")
        print(f"  🔢 총 라운드: {metadata['total_rounds']}")
        print(f"  🎯 투자 심볼: {metadata['invested_symbols']}/{metadata['max_symbols']}개")
        print(f"  🌊 최종 시장 상태: {metadata['final_market_regime']}")
        print(f"  📉 교체 기준: {metadata['replacement_threshold']}%")
        
        # 상위 심볼 성과
        print(f"\n🏆 최종 심볼 성과:")
        for i, perf in enumerate(result["individual_performance"], 1):
            emoji = "📈" if perf['pnl_percent'] > 5 else "📉" if perf['pnl_percent'] < -3 else "➡️"
            print(f"  {i}. {emoji} {perf['symbol']}: ${perf['pnl']:+.2f} ({perf['pnl_percent']:+.2f}%) - 순위: {perf['rank']}, 수익 가능성: {perf['profit_potential']:.1f}")
        
        # 결과 저장
        results_file = Path("modular_simulation_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과 저장: {results_file}")
        print(f"\n✅ 모듈화된 시뮬레이션 성공적으로 완료되었습니다!")
        
    else:
        print(f"❌ 시뮬레이션 실패: {result['error']}")


if __name__ == "__main__":
    main()
