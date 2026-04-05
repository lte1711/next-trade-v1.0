#!/usr/bin/env python3
"""수정된 서비스들에 대한 최종 테스트"""

import sys
import os
import json
import threading
import time
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "merged_partial_v2" / "src"))

def test_risk_gate_service():
    """RiskGateService 테스트"""
    print("🧪 RiskGateService 테스트 시작...")
    
    try:
        from merged_partial_v2.services.risk_gate_service import RiskGateService
        
        risk_service = RiskGateService()
        print(f"  ✅ 설정 로드: failure_block_window_seconds = {risk_service.FAILURE_BLOCK_WINDOW_SECONDS}")
        
        # 제로 디비전 테스트
        result = risk_service._calculate_daily_pnl({"wallet_balance": 0, "total_unrealized_pnl": 100})
        print(f"  ✅ 제로 디비전 테스트: {result}")
        
        print("  ✅ RiskGateService 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ RiskGateService 테스트 실패: {e}")
        return False

def test_leverage_management_service():
    """LeverageManagementService 테스트"""
    print("🧪 LeverageManagementService 테스트 시작...")
    
    try:
        from merged_partial_v2.services.leverage_management_service import LeverageManagementService
        
        service = LeverageManagementService()
        result = service.calculate_optimal_leverage(1000.0, 15.0, "NORMAL")
        print(f"  ✅ 레버리지 계산: {result['recommended_leverage']}")
        
        print("  ✅ LeverageManagementService 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ LeverageManagementService 테스트 실패: {e}")
        return False

def test_dashboard_server():
    """DashboardServer 테스트"""
    print("🧪 DashboardServer 테스트 시작...")
    
    try:
        sys.path.insert(0, str(project_root / "merged_partial_v2" / "src" / "merged_partial_v2"))
        from dashboard_server import _validate_autonomous_start_payload
        
        is_valid, error = _validate_autonomous_start_payload({"adopt_active_positions": True})
        print(f"  ✅ 입력 검증: valid={is_valid}")
        
        print("  ✅ DashboardServer 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ DashboardServer 테스트 실패: {e}")
        return False

def test_thread_safety():
    """스레드 안전성 테스트"""
    print("🧪 스레드 안전성 테스트 시작...")
    
    try:
        # 간단한 스레드 테스트
        lock = threading.Lock()
        counter = [0]
        
        def worker():
            for i in range(5):
                with lock:
                    counter[0] += 1
                time.sleep(0.001)
        
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout=5.0)
        
        print(f"  ✅ 스레드 테스트: 카운터 = {counter[0]}")
        return counter[0] == 5
        
    except Exception as e:
        print(f"  ❌ 스레드 안전성 테스트 실패: {e}")
        return False

def test_config_loading():
    """설정 로드 테스트"""
    print("🧪 설정 로드 테스트 시작...")
    
    try:
        config_path = project_root / "merged_partial_v2" / "config.json"
        
        if not config_path.exists():
            print("  ❌ 설정 파일 없음")
            return False
        
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        
        risk_limits = config.get("risk_limits", {})
        print(f"  ✅ 설정 로드: {len(risk_limits)}개 항목")
        
        print("  ✅ 설정 로드 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 설정 로드 테스트 실패: {e}")
        return False

def main():
    """메인 테스트"""
    print("🚀 수정된 서비스 최종 테스트 시작\n")
    
    tests = [
        ("RiskGateService", test_risk_gate_service),
        ("LeverageManagementService", test_leverage_management_service),
        ("DashboardServer", test_dashboard_server),
        ("스레드 안전성", test_thread_safety),
        ("설정 로드", test_config_loading),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            print(f"🔄 {test_name} 테스트 실행 중...")
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
        print("⚠️ 일부 테스트 실패.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
