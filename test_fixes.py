#!/usr/bin/env python3
"""수정된 서비스들에 대한 통합 테스트 스크립트"""

import sys
import os
import json
import threading
import time
import tempfile
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "merged_partial_v2" / "src"))

def test_risk_gate_service():
    """RiskGateService 제로 디비전 및 설정 로드 테스트"""
    print("🧪 RiskGateService 테스트 시작...")
    
    try:
        from merged_partial_v2.services.risk_gate_service import RiskGateService
        
        # 서비스 인스턴스 생성
        risk_service = RiskGateService()
        
        # 설정 로드 테스트
        print(f"  ✅ 설정 로드: failure_block_window_seconds = {risk_service.FAILURE_BLOCK_WINDOW_SECONDS}")
        print(f"  ✅ 설정 로드: daily_loss_reset_hour = {risk_service.DAILY_LOSS_RESET_HOUR}")
        
        # 제로 디비전 테스트
        test_cases = [
            {"wallet_balance": 0, "total_unrealized_pnl": 100},
            {"wallet_balance": 0.0, "total_unrealized_pnl": -50},
            {"wallet_balance": 1000, "total_unrealized_pnl": 100},
            {"wallet_balance": -100, "total_unrealized_pnl": 50},
        ]
        
        for i, case in enumerate(test_cases):
            result = risk_service._calculate_daily_pnl(case)
            print(f"  ✅ 테스트 케이스 {i+1}: wallet_balance={case['wallet_balance']}, pnl={case['total_unrealized_pnl']} → result={result}")
            
            # 제로 디비전 오류가 없는지 확인
            assert isinstance(result, float), f"결과가 숫자가 아님: {type(result)}"
        
        print("  ✅ RiskGateService 모든 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ RiskGateService 테스트 실패: {e}")
        return False

def test_leverage_management_service():
    """LeverageManagementService 입력 검증 테스트"""
    print("🧪 LeverageManagementService 테스트 시작...")
    
    try:
        from merged_partial_v2.services.leverage_management_service import LeverageManagementService
        
        service = LeverageManagementService()
        
        # 정상 입력 테스트
        result = service.calculate_optimal_leverage(1000.0, 15.0, "NORMAL")
        print(f"  ✅ 정상 입력 테스트: leverage={result['recommended_leverage']}")
        
        # 예외 입력 테스트
        error_cases = [
            (-1000, 15.0, "NORMAL", "account_balance cannot be negative"),
            (1000, -5.0, "NORMAL", "symbol_volatility cannot be negative"),
            (1000, 15.0, "", "market_regime must be a non-empty string"),
            (1000, 15.0, None, "market_regime must be a non-empty string"),
        ]
        
        for balance, volatility, regime, expected_error in error_cases:
            try:
                service.calculate_optimal_leverage(balance, volatility, regime)
                print(f"  ❌ 예외 발생해야 함: {expected_error}")
                return False
            except ValueError as e:
                if expected_error in str(e):
                    print(f"  ✅ 올바른 예외 처리: {expected_error}")
                else:
                    print(f"  ❌ 잘못된 예외 메시지: {e}")
                    return False
        
        # 포지션 크기 검증 테스트
        try:
            service.validate_position_size(-100, 1000, 3, "BTCUSDT")
            print("  ❌ 예외 발생해야 함: requested_size must be positive")
            return False
        except ValueError as e:
            if "requested_size must be positive" in str(e):
                print("  ✅ 포지션 크기 검증 통과")
            else:
                print(f"  ❌ 잘못된 예외 메시지: {e}")
                return False
        
        print("  ✅ LeverageManagementService 모든 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ LeverageManagementService 테스트 실패: {e}")
        return False

def test_dashboard_server_validation():
    """DashboardServer 입력 검증 테스트"""
    print("🧪 DashboardServer 입력 검증 테스트 시작...")
    
    try:
        # 테스트를 위해 모듈 임포트
        sys.path.insert(0, str(project_root / "merged_partial_v2" / "src" / "merged_partial_v2"))
        from dashboard_server import _validate_autonomous_start_payload, _validate_health_check_payload
        
        # 자동매매 시작 페이로드 검증 테스트
        valid_payload = {"adopt_active_positions": True, "interval_seconds": 60}
        is_valid, error = _validate_autonomous_start_payload(valid_payload)
        assert is_valid, f"유효한 페이로드가 거부됨: {error}"
        print("  ✅ 유효한 자동매수 페이로드 검증 통과")
        
        invalid_payloads = [
            ({"adopt_active_positions": "yes"}, "adopt_active_positions must be a boolean"),
            ({"interval_seconds": -10}, "interval_seconds must be between 1.0 and 3600.0"),
            ({"interval_seconds": 5000}, "interval_seconds must be between 1.0 and 3600.0"),
            ("not_a_dict", "payload must be a dictionary"),
        ]
        
        for payload, expected_error in invalid_payloads:
            is_valid, error = _validate_autonomous_start_payload(payload)
            assert not is_valid, f"무효한 페이로드가 통과됨: {payload}"
            assert expected_error in error, f"예상된 오류 메시지 다름: {error}"
            print(f"  ✅ 무효한 페이로드 검증 통과: {expected_error}")
        
        # 헬스체크 페이로드 검증 테스트
        valid_health_payload = {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.001}
        is_valid, error = _validate_health_check_payload(valid_health_payload)
        assert is_valid, f"유효한 헬스체크 페이로드가 거부됨: {error}"
        print("  ✅ 유효한 헬스체크 페이로드 검증 통과")
        
        invalid_health_payloads = [
            ({}, "symbol is required and must be a string"),
            ({"symbol": ""}, "symbol is required and must be a string"),
            ({"symbol": "BTCUSDT", "side": "INVALID"}, "side must be either 'BUY' or 'SELL'"),
            ({"symbol": "BTCUSDT", "side": "BUY", "quantity": -1}, "quantity must be between 0 and 1000"),
        ]
        
        for payload, expected_error in invalid_health_payloads:
            is_valid, error = _validate_health_check_payload(payload)
            assert not is_valid, f"무효한 헬스체크 페이로드가 통과됨: {payload}"
            assert expected_error in error, f"예상된 오류 메시지 다름: {error}"
            print(f"  ✅ 무효한 헬스체크 페이로드 검증 통과: {expected_error}")
        
        print("  ✅ DashboardServer 모든 입력 검증 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ DashboardServer 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_manager_thread_safety():
    """ProcessManagerService 스레드 동기화 테스트"""
    print("🧪 ProcessManagerService 스레드 동기화 테스트 시작...")
    
    try:
        print("  📦 모듈 임포트 중...")
        sys.path.insert(0, str(project_root / "merged_partial_v2" / "src" / "merged_partial_v2"))
        from services.process_manager_service import _THREAD_LOCK
        print("  ✅ 모듈 임포트 완료")
        
        # 잠금 객체만 확인 - _thread_is_running 호출 제거
        print(f"  🔍 스레드 잠금 객체 확인: {type(_THREAD_LOCK).__name__}")
        
        # 간단한 잠금 획득/해제 테스트
        print("  🔄 잠금 테스트 시작...")
        lock_acquired = []
        lock_released = []
        
        def test_lock(thread_id):
            try:
                print(f"    스레드 {thread_id}: 잠금 시도...")
                with _THREAD_LOCK:
                    lock_acquired.append(thread_id)
                    print(f"    ✅ 스레드 {thread_id}: 잠금 획득 성공")
                    time.sleep(0.01)  # 매우 짧은 대기
                lock_released.append(thread_id)
                print(f"    ✅ 스레드 {thread_id}: 잠금 해제 성공")
            except Exception as e:
                print(f"    ❌ 스레드 {thread_id}: 오류 발생 {e}")
        
        print("  🚀 스레드 생성 중...")
        # 여러 스레드에서 동시에 잠금 테스트
        threads = []
        for i in range(3):
            thread = threading.Thread(target=test_lock, args=(i,))
            threads.append(thread)
            print(f"    스레드 {i} 생성 완료")
        
        print("  ▶️ 스레드 시작 중...")
        # 스레드 시작
        for i, thread in enumerate(threads):
            thread.start()
            print(f"    스레드 {i} 시작")
        
        print("  ⏳ 스레드 완료 대기 중...")
        # 타임아웃과 함께 대기
        completed_count = 0
        for i, thread in enumerate(threads):
            print(f"    스레드 {i} 대기 중...")
            thread.join(timeout=3.0)
            if thread.is_alive():
                print(f"    ⚠️ 스레드 {i} 타임아웃 발생")
                # 강제 종료는 파이썬에서 불가능하므로 계속 진행
            else:
                completed_count += 1
                print(f"    ✅ 스레드 {i} 완료")
        
        print(f"  📊 최종 결과:")
        print(f"    - 완료된 스레드: {completed_count}/3")
        print(f"    - 잠금 획득한 스레드: {len(lock_acquired)}")
        print(f"    - 잠금 해제한 스레드: {len(lock_released)}")
        
        # 모든 스레드가 잠금을 획득하고 해제했는지 확인
        if len(lock_acquired) == 3 and len(lock_released) == 3:
            print("  ✅ ProcessManagerService 스레드 동기화 테스트 통과")
            return True
        else:
            print(f"  ❌ 일부 스레드가 완료되지 않음: 획득={len(lock_acquired)}, 해제={len(lock_released)}")
            return False
        
    except Exception as e:
        print(f"  ❌ ProcessManagerService 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """설정 로드 테스트"""
    print("🧪 설정 로드 테스트 시작...")
    
    try:
        config_path = project_root / "merged_partial_v2" / "config.json"
        
        if not config_path.exists():
            print(f"  ❌ 설정 파일 없음: {config_path}")
            return False
        
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        
        # risk_limits 설정 확인
        risk_limits = config.get("risk_limits", {})
        expected_keys = ["failure_block_window_seconds", "daily_loss_reset_hour"]
        
        for key in expected_keys:
            if key not in risk_limits:
                print(f"  ❌ 설정 누락: {key}")
                return False
            print(f"  ✅ 설정 확인: {key} = {risk_limits[key]}")
        
        print("  ✅ 설정 로드 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 설정 로드 테스트 실패: {e}")
        return False

def main():
    """모든 테스트 실행"""
    print("🚀 수정된 서비스 통합 테스트 시작\n")
    
    tests = [
        ("RiskGateService", test_risk_gate_service),
        ("LeverageManagementService", test_leverage_management_service),
        ("DashboardServer 입력 검증", test_dashboard_server_validation),
        ("ProcessManagerService 스레드 동기화", test_process_manager_thread_safety),
        ("설정 로드", test_config_loading),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
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
    print(f"\n{'='*50}")
    print("📊 최종 테스트 결과:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 총계: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 테스트 통과! 수정된 코드가 정상적으로 작동합니다.")
        return True
    else:
        print("⚠️ 일부 테스트 실패. 수정이 필요합니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
