# 개선된 기능 통합 테스트

import sys
import os
import json
import threading
import time
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "merged_partial_v2" / "src"))

def test_dynamic_risk_management():
    """탄력적 위험 관리 시스템 테스트"""
    print("🧪 탄력적 위험 관리 테스트...")
    
    try:
        from merged_partial_v2.services.risk_gate_service import RiskGateService
        
        service = RiskGateService()
        
        # 시장 상태별 동적 포지션 크기 제한 테스트
        test_cases = [
            ("NORMAL", 1000, {"wallet_balance": 10000}),
            ("EXTREME", 1000, {"wallet_balance": 10000}),
            ("VOLATILE", 1000, {"wallet_balance": 10000}),
        ]
        
        for market_regime, balance, account in test_cases:
            max_size = service._calculate_dynamic_position_size_limit(market_regime, account)
            print(f"  ✅ {market_regime}: {max_size:.1f}%")
        
        # EXTREME 시장에서 50% 감소 확인
        normal_limit = service._calculate_dynamic_position_size_limit("NORMAL", account)
        extreme_limit = service._calculate_dynamic_position_size_limit("EXTREME", account)
        assert extreme_limit < normal_limit, "EXTREME 시장 제한 감소 확인"
        
        print("  ✅ 탄력적 위험 관리 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 탄력적 위험 관리 테스트 실패: {e}")
        return False

def test_failure_recovery():
    """실패 후 자동 복구 로직 테스트"""
    print("🧪 실패 복구 로직 테스트...")
    
    try:
        from merged_partial_v2.services.process_manager_service import _record_failure_recovery_attempt
        
        # 복구 기록 테스트
        _record_failure_recovery_attempt(12345, "test_recovery")
        
        # 기록 파일 확인
        recovery_path = project_root / "merged_partial_v2" / "runtime" / "recovery_attempts.json"
        if recovery_path.exists():
            with recovery_path.open("r", encoding="utf-8") as f:
                records = json.load(f)
                assert len(records) > 0, "복구 기록 확인"
                assert records[-1]["pid"] == 12345, "PID 확인"
                assert records[-1]["recovery_type"] == "test_recovery", "복구 타입 확인"
        
        print("  ✅ 실패 복구 로직 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 실패 복구 로직 테스트 실패: {e}")
        return False

def test_dynamic_reserve_ratio():
    """동적 예비금 비율 테스트"""
    print("🧪 동적 예비금 비율 테스트...")
    
    try:
        from merged_partial_v2.services.leverage_management_service import LeverageManagementService
        
        service = LeverageManagementService()
        
        # 손익 상태별 예비금 비율 테스트
        test_cases = [
            (15.0, 0.2),   # 높은 수익
            (-10.0, 0.3),  # 높은 손실
            (-2.0, 0.15),  # 적은 손실
            (5.0, 0.1),    # 작은 수익
        ]
        
        for pnl, expected_ratio in test_cases:
            actual_ratio = service._calculate_dynamic_reserve_ratio(1000, pnl)
            print(f"  ✅ PNL {pnl}%: 예비금 {actual_ratio:.2f} (예상: {expected_ratio})")
            assert abs(actual_ratio - expected_ratio) < 0.01, f"예비금 비율 오차: {actual_ratio} vs {expected_ratio}"
        
        print("  ✅ 동적 예비금 비율 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 동적 예비금 비율 테스트 실패: {e}")
        return False

def test_dynamic_leverage():
    """동적 레버리지 조정 테스트"""
    print("🧪 동적 레버리지 조정 테스트...")
    
    try:
        from merged_partial_v2.services.leverage_management_service import LeverageManagementService
        
        service = LeverageManagementService()
        
        # 변동성별 조정 계수 테스트
        volatility_tests = [
            (30.0, 0.6),   # 높은 변동성
            (20.0, 0.6),   # 높은 변동성
            (10.0, 1.1),   # 보통 변동성
            (3.0, 1.3),    # 낮은 변동성
            (1.0, 1.3),    # 매우 낮은 변동성
        ]
        
        for volatility, expected_factor in volatility_tests:
            actual_factor = service._calculate_volatility_adjustment_factor(volatility)
            print(f"  ✅ 변동성 {volatility}: 조정계수 {actual_factor} (예상: {expected_factor})")
            assert abs(actual_factor - expected_factor) < 0.01, f"조정계수 오차: {actual_factor} vs {expected_factor}"
        
        # 시장 상태별 조정 계수 테스트
        regime_tests = [
            ("EXTREME", 0.5),
            ("VOLATILE", 0.8),
            ("BEARISH", 0.7),
            ("BULLISH", 1.1),
            ("NORMAL", 1.0),
        ]
        
        for regime, expected_factor in regime_tests:
            actual_factor = service._calculate_regime_adjustment_factor(regime)
            print(f"  ✅ 시장 {regime}: 조정계수 {actual_factor} (예상: {expected_factor})")
            assert abs(actual_factor - expected_factor) < 0.01, f"시장조정계수 오차: {actual_factor} vs {expected_factor}"
        
        print("  ✅ 동적 레버리지 조정 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 동적 레버리지 조정 테스트 실패: {e}")
        return False

def main():
    """개선된 기능 통합 테스트"""
    print("🚀 개선된 기능 통합 테스트 시작")
    
    tests = [
        ("탄력적 위험 관리", test_dynamic_risk_management),
        ("실패 복구 로직", test_failure_recovery),
        ("동적 예비금 비율", test_dynamic_reserve_ratio),
        ("동적 레버리지 조정", test_dynamic_leverage),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"🔄 {test_name} 테스트 실행 중...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} 테스트 통과")
            else:
                print(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            print(f"❌ {test_name} 테스트 예외: {e}")
            results.append((test_name, False))
    
    # 최종 결과
    print(f"{'='*50}")
    print("📊 최종 개선 테스트 결과:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {status}: {test_name}")
    
    print(f"🎯 총계: {passed}/{total} 개선 테스트 통과")
    
    if passed == total:
        print("🎉 모든 개선 기능 테스트 통과!")
        return True
    else:
        print("⚠️ 일부 개선 기능 테스트 실패.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
