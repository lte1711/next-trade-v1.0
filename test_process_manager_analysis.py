#!/usr/bin/env python3
"""ProcessManagerService 정밀 분석 및 해결 테스트"""

import sys
import os
import threading
import time
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent

def test_path_resolution():
    """경로 해결 문제 테스트"""
    print("🔍 경로 해결 테스트...")
    
    try:
        # pathing 모듈 테스트
        sys.path.insert(0, str(project_root / "merged_partial_v2" / "src"))
        
        print(f"  📁 프로젝트 루트: {project_root}")
        print(f"  📁 추가된 경로: {sys.path[0]}")
        
        # pathing 모듈 직접 테스트
        import merged_partial_v2.pathing
        install_root_path = merged_partial_v2.pathing.install_root()
        print(f"  📁 install_root(): {install_root_path}")
        
        # 경로가 존재하는지 확인
        if install_root_path.exists():
            print("  ✅ install_root 경로 존재")
        else:
            print("  ❌ install_root 경로 없음")
            
        return True
        
    except Exception as e:
        print(f"  ❌ 경로 해결 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_thread_lock_mechanism():
    """스레드 잠금 메커니즘 테스트"""
    print("🔍 스레드 잠금 메커니즘 테스트...")
    
    try:
        # 간단한 잠금 테스트
        test_lock = threading.Lock()
        test_var = [0]
        
        def worker(thread_id):
            for i in range(5):
                with test_lock:
                    test_var[0] += 1
                    print(f"    스레드 {thread_id}: 카운터 {test_var[0]} (반복 {i+1})")
                time.sleep(0.001)
        
        threads = []
        for i in range(2):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
        
        print("  🚀 스레드 시작...")
        for thread in threads:
            thread.start()
        
        print("  ⏳ 스레드 대기...")
        for thread in threads:
            thread.join(timeout=5.0)
        
        print(f"  📊 최종 카운터: {test_var[0]} (예상: 10)")
        
        return test_var[0] == 10
        
    except Exception as e:
        print(f"  ❌ 스레드 잠금 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_manager_import():
    """ProcessManagerService 임포트 테스트 - 단계별"""
    print("🔍 ProcessManagerService 단계별 임포트 테스트...")
    
    try:
        print("  📦 1단계: 기본 모듈 임포트...")
        import merged_partial_v2.pathing
        print("  ✅ pathing 임포트 성공")
        
        print("  📦 2단계: 서비스 모듈 임포트...")
        from merged_partial_v2.services import process_manager_service
        print("  ✅ process_manager_service 임포트 성공")
        
        print("  📦 3단계: 전역 변수 확인...")
        print(f"    _THREAD_LOCK: {type(process_manager_service._THREAD_LOCK)}")
        print(f"    _AUTONOMOUS_THREAD: {process_manager_service._AUTONOMOUS_THREAD}")
        print(f"    _AUTONOMOUS_STOP_EVENT: {process_manager_service._AUTONOMOUS_STOP_EVENT}")
        
        print("  📦 4단계: 함수 호출 테스트...")
        result = process_manager_service._thread_is_running()
        print(f"    _thread_is_running(): {result}")
        
        print("  ✅ ProcessManagerService 임포트 테스트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ ProcessManagerService 임포트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 분석 테스트"""
    print("🚀 ProcessManagerService 정밀 분석 시작\n")
    
    tests = [
        ("경로 해결", test_path_resolution),
        ("스레드 잠금 메커니즘", test_thread_lock_mechanism),
        ("ProcessManagerService 임포트", test_process_manager_import),
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
    print("📊 최종 분석 결과:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 총계: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 분석 테스트 통과!")
    else:
        print("⚠️ 문제가 발견되었습니다.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
