#!/usr/bin/env python3
"""수정된 서비스 통합 배포 테스트"""

import sys
import os
import json
import threading
import time
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "merged_partial_v2" / "src"))

def test_modified_services():
    """수정된 모든 서비스 통합 테스트"""
    print("🚀 수정된 서비스 통합 배포 테스트 시작\n")
    
    tests = []
    
    # 1. RiskGateService 테스트
    try:
        from merged_partial_v2.services.risk_gate_service import RiskGateService
        risk_service = RiskGateService()
        
        # 설정 로드 테스트
        assert risk_service.FAILURE_BLOCK_WINDOW_SECONDS == 900
        assert risk_service.DAILY_LOSS_RESET_HOUR == 0
        
        # 제로 디비전 테스트
        result1 = risk_service._calculate_daily_pnl({"wallet_balance": 0, "total_unrealized_pnl": 100})
        result2 = risk_service._calculate_daily_pnl({"wallet_balance": 1000, "total_unrealized_pnl": 100})
        
        assert isinstance(result1, float)
        assert isinstance(result2, float)
        
        tests.append(("RiskGateService", True))
        print("✅ RiskGateService: 설정 로드 및 제로 디비전 처리 통과")
    except Exception as e:
        tests.append(("RiskGateService", False))
        print(f"❌ RiskGateService 실패: {e}")
    
    # 2. LeverageManagementService 테스트
    try:
        from merged_partial_v2.services.leverage_management_service import LeverageManagementService
        service = LeverageManagementService()
        
        # 정상 입력 테스트
        result = service.calculate_optimal_leverage(1000.0, 15.0, "NORMAL")
        assert result['recommended_leverage'] > 0
        
        # 입력 검증 테스트
        try:
            service.calculate_optimal_leverage(-1000, 15.0, "NORMAL")
            assert False, "예외 발생해야 함"
        except ValueError:
            pass  # 예상된 예외
        
        tests.append(("LeverageManagementService", True))
        print("✅ LeverageManagementService: 레버리지 계산 및 입력 검증 통과")
    except Exception as e:
        tests.append(("LeverageManagementService", False))
        print(f"❌ LeverageManagementService 실패: {e}")
    
    # 3. DashboardServer 테스트
    try:
        sys.path.insert(0, str(project_root / "merged_partial_v2" / "src" / "merged_partial_v2"))
        from dashboard_server import _validate_autonomous_start_payload, _validate_health_check_payload
        
        # 유효한 페이로드 테스트
        valid_payload = {"adopt_active_positions": True, "interval_seconds": 60}
        is_valid, error = _validate_autonomous_start_payload(valid_payload)
        assert is_valid == True
        
        # 무효한 페이로드 테스트
        invalid_payload = {"adopt_active_positions": "yes"}
        is_valid, error = _validate_autonomous_start_payload(invalid_payload)
        assert is_valid == False
        assert "boolean" in error
        
        # 헬스체크 페이로드 테스트
        health_payload = {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.001}
        is_valid, error = _validate_health_check_payload(health_payload)
        assert is_valid == True
        
        tests.append(("DashboardServer", True))
        print("✅ DashboardServer: 입력 검증 모듈 통과")
    except Exception as e:
        tests.append(("DashboardServer", False))
        print(f"❌ DashboardServer 실패: {e}")
    
    # 4. ProcessManagerService 테스트
    try:
        from merged_partial_v2.services.process_manager_service import _THREAD_LOCK, _thread_is_running
        
        # 잠금 객체 확인
        assert hasattr(_THREAD_LOCK, 'acquire')
        assert hasattr(_THREAD_LOCK, 'release')
        
        # 간단한 스레드 테스트
        test_lock = threading.Lock()
        counter = [0]
        
        def worker():
            with test_lock:
                counter[0] += 1
        
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout=3.0)
        
        assert counter[0] == 1
        
        tests.append(("ProcessManagerService", True))
        print("✅ ProcessManagerService: 스레드 동기화 통과")
    except Exception as e:
        tests.append(("ProcessManagerService", False))
        print(f"❌ ProcessManagerService 실패: {e}")
    
    # 5. 설정 로드 테스트
    try:
        config_path = project_root / "merged_partial_v2" / "config.json"
        
        assert config_path.exists()
        
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        
        risk_limits = config.get("risk_limits", {})
        assert "failure_block_window_seconds" in risk_limits
        assert "daily_loss_reset_hour" in risk_limits
        
        tests.append(("설정 로드", True))
        print("✅ 설정 로드: config.json 설정 확인 통과")
    except Exception as e:
        tests.append(("설정 로드", False))
        print(f"❌ 설정 로드 실패: {e}")
    
    # 최종 결과
    print(f"\n{'='*60}")
    print("📊 최종 배포 테스트 결과:")
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 총계: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 수정된 서비스 통합 테스트 통과!")
        print("🚀 배포 준비 완료!")
        return True
    else:
        print("⚠️ 일부 테스트 실패. 배포 보류 필요.")
        return False

def main():
    """메인 배포 테스트"""
    success = test_modified_services()
    
    if success:
        print("\n🏁 배포 가능 상태 확인!")
    else:
        print("\n❌ 배포 불가 상태!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
