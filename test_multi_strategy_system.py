#!/usr/bin/env python3
"""
멀티 전략 시스템 통합 테스트
모든 멀티 전략 컴포넌트가 정상적으로 작동하는지 확인
"""

import sys
import traceback
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

def test_module_imports():
    """모듈 임포트 테스트"""
    print("=== 모듈 임포트 테스트 ===")
    try:
        from strategies.base_strategy import BaseStrategy
        print("FACT: BaseStrategy 임포트 성공 ✓")
        
        from strategies.momentum_intraday_v1 import MomentumIntradayV1
        print("FACT: MomentumIntradayV1 임포트 성공 ✓")
        
        from strategies.trend_following_v1 import TrendFollowingV1
        print("FACT: TrendFollowingV1 임포트 성공 ✓")
        
        from strategies.multi_strategy_manager import MultiStrategyManager
        print("FACT: MultiStrategyManager 임포트 성공 ✓")
        
        from utils.indicators import calculate_sma, calculate_rsi, calculate_macd
        print("FACT: 기술적 지표 모듈 임포트 성공 ✓")
        
        return True
    except Exception as e:
        print(f"FACT: 모듈 임포트 실패: {e}")
        traceback.print_exc()
        return False

def test_indicators():
    """기술적 지표 테스트"""
    print("\n=== 기술적 지표 테스트 ===")
    try:
        from utils.indicators import calculate_sma, calculate_rsi, calculate_macd
        
        test_prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
        
        sma = calculate_sma(test_prices, 10)
        print(f"FACT: SMA 계산 성공: {sma:.2f} ✓")
        
        rsi = calculate_rsi(test_prices, 14)
        print(f"FACT: RSI 계산 성공: {rsi:.2f} ✓")
        
        macd_line, signal_line, histogram = calculate_macd(test_prices)
        print(f"FACT: MACD 계산 성공: {macd_line:.6f} ✓")
        
        return True
    except Exception as e:
        print(f"FACT: 기술적 지표 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_multi_strategy_manager():
    """멀티 전략 관리자 테스트"""
    print("\n=== 멀티 전략 관리자 테스트 ===")
    try:
        from strategies.multi_strategy_manager import MultiStrategyManager
        
        manager = MultiStrategyManager()
        performance = manager.get_strategy_performance()
        
        print(f"FACT: 멀티 전략 관리자 초기화 성공 ✓")
        print(f"FACT: 활성 전략 수: {performance['total_strategies']}")
        print(f"FACT: 활성 전략 목록: {performance['active_strategies']}")
        print(f"FACT: 현재 시장 레짐: {performance['current_market_regime']}")
        
        return True
    except Exception as e:
        print(f"FACT: 멀티 전략 관리자 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_strategy_evaluation():
    """전략 평가 테스트"""
    print("\n=== 전략 평가 테스트 ===")
    try:
        from strategies.multi_strategy_manager import MultiStrategyManager
        
        manager = MultiStrategyManager()
        
        # 테스트 데이터
        test_closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
        test_volumes = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000]
        
        result = manager.evaluate_strategies('BTCUSDT', test_closes, test_volumes)
        
        print(f"FACT: 전략 평가 성공 ✓")
        print(f"FACT: 심볼: {result['symbol']}")
        print(f"FACT: 시장 레짐: {result['market_regime']}")
        print(f"FACT: 통합 신호: {result['aggregated_signal']['signal']}")
        print(f"FACT: 신호 확신도: {result['aggregated_signal']['confidence']}")
        print(f"FACT: 기여 전략: {result['aggregated_signal']['contributing_strategies']}")
        
        return True
    except Exception as e:
        print(f"FACT: 전략 평가 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_individual_strategies():
    """개별 전략 테스트"""
    print("\n=== 개별 전략 테스트 ===")
    try:
        from strategies.momentum_intraday_v1 import MomentumIntradayV1
        from strategies.trend_following_v1 import TrendFollowingV1
        
        # 테스트 데이터
        test_closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
        test_volumes = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000]
        
        # 모멘텀 전략 테스트
        momentum_strategy = MomentumIntradayV1()
        momentum_result = momentum_strategy.evaluate('BTCUSDT', test_closes, test_volumes)
        print(f"FACT: 모멘텀 전략 신호: {momentum_result['signal']} ✓")
        
        # 추세 추종 전략 테스트
        trend_strategy = TrendFollowingV1()
        trend_result = trend_strategy.evaluate('BTCUSDT', test_closes, test_volumes)
        print(f"FACT: 추세 추종 전략 신호: {trend_result['signal']} ✓")
        
        return True
    except Exception as e:
        print(f"FACT: 개별 전략 테스트 실패: {e}")
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("=== 멀티 전략 시스템 통합 테스트 시작 ===")
    print(f"테스트 시작 시간: {datetime.datetime.now()}")
    
    tests = [
        ("모듈 임포트", test_module_imports),
        ("기술적 지표", test_indicators),
        ("멀티 전략 관리자", test_multi_strategy_manager),
        ("개별 전략", test_individual_strategies),
        ("전략 평가", test_strategy_evaluation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FACT: {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "통과" if result else "실패"
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nFACT: 전체 테스트 {total}개 중 {passed}개 통과")
    print(f"FACT: 성공률: {passed/total*100:.1f}%")
    
    if passed == total:
        print("FACT: 멀티 전략 시스템이 완벽하게 작동합니다 ✓")
        return True
    else:
        print("FACT: 일부 테스트가 실패했습니다. 확인이 필요합니다.")
        return False

if __name__ == "__main__":
    import datetime
    main()
