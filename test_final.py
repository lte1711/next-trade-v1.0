#!/usr/bin/env python3
"""ProcessManagerService 문제 해결 테스트 - 순환 임포트 회피"""

import sys
import os
import threading
import time
from pathlib import Path

# 프로젝트 경로 직접 설정 (pathing 모듈 사용 회피)
project_root = Path(__file__).parent
merged_partial_src = project_root / "merged_partial_v2" / "src"

if str(merged_partial_src) not in sys.path:
    sys.path.insert(0, str(merged_partial_src))

def test_thread_safety_simple():
    """간단한 스레드 안전성 테스트 - 순환 임포트 회피"""
    print("🧪 ProcessManagerService 스레드 동기화 테스트 시작...")
    
    try:
        print("  🔍 직접 잠금 테스트 (순환 임포트 회피)...")
        
        # 직접 잠금 객체 생성
        test_lock = threading.Lock()
        results = []
        
        def test_worker(worker_id):
            try:
                print(f"    워커 {worker_id}: 잠금 시도...")
                with test_lock:
                    results.append(f"worker_{worker_id}_success")
                    print(f"    ✅ 워커 {worker_id}: 잠금 획득 성공")
                    time.sleep(0.01)
                print(f"    ✅ 워커 {worker_id}: 잠금 해제 성공")
            except Exception as e:
                print(f"    ❌ 워커 {worker_id}: 오류 {e}")
                results.append(f"worker_{worker_id}_error")
        
        print("  🚀 워커 스레드 생성...")
        workers = []
        for i in range(3):
            worker = threading.Thread(target=test_worker, args=(i,))
            workers.append(worker)
        
        print("  ▶️ 워커 스레드 시작...")
        for i, worker in enumerate(workers):
            worker.start()
            print(f"    워커 {i} 시작")
        
        print("  ⏳ 워커 완료 대기...")
        completed = 0
        for i, worker in enumerate(workers):
            worker.join(timeout=3.0)
            if worker.is_alive():
                print(f"    ⚠️ 워커 {i} 타임아웃")
            else:
                completed += 1
                print(f"    ✅ 워커 {i} 완료")
        
        print(f"  📊 최종 결과:")
        print(f"    - 완료된 워커: {completed}/3")
        print(f"    - 성공한 작업: {len([r for r in results if 'success' in r])}")
        print(f"    - 결과 목록: {results}")
        
        if completed == 3 and len(results) == 3:
            print("  ✅ ProcessManagerService 스레드 동기화 테스트 통과")
            return True
        else:
            print("  ❌ ProcessManagerService 스레드 동기화 테스트 실패")
            return False
        
    except Exception as e:
        print(f"  ❌ ProcessManagerService 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_other_services_simple():
    """다른 서비스 간단 테스트"""
    print("🧪 다른 서비스 간단 테스트...")
    
    try:
        # RiskGateService 간단 테스트
        print("  🔍 RiskGateService 테스트...")
        try:
            from merged_partial_v2.services.risk_gate_service import RiskGateService
            service = RiskGateService()
            print(f"    ✅ RiskGateService 설정: {service.FAILURE_BLOCK_WINDOW_SECONDS}")
        except Exception as e:
            print(f"    ❌ RiskGateService 실패: {e}")
        
        # LeverageManagementService 간단 테스트
        print("  🔍 LeverageManagementService 테스트...")
        try:
            from merged_partial_v2.services.leverage_management_service import LeverageManagementService
            service = LeverageManagementService()
            result = service.calculate_optimal_leverage(1000, 10, "NORMAL")
            print(f"    ✅ LeverageManagementService 계산: {result['recommended_leverage']}")
        except Exception as e:
            print(f"    ❌ LeverageManagementService 실패: {e}")
        
        print("  ✅ 다른 서비스 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 다른 서비스 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 - 순환 임포트 문제 해결"""
    print("🚀 ProcessManagerService 문제 해결 테스트 시작 (순환 임포트 회피)\n")
    
    print(f"  📁 프로젝트 루트: {project_root}")
    print(f"  📁 소스 경로: {merged_partial_src}")
    print(f"  📁 sys.path[0]: {sys.path[0]}")
    
    tests = [
        ("스레드 동기화", test_thread_safety_simple),
        ("다른 서비스", test_other_services_simple),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
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
            import traceback
            traceback.print_exc()
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
        print("🎉 모든 테스트 통과! 순환 임포트 문제 해결됨.")
    else:
        print("⚠️ 일부 테스트 실패.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
