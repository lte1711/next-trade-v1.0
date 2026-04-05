#!/usr/bin/env python3
"""최소한의 테스트 - 문제의 근본 원인 확인"""

import sys
from pathlib import Path

def test_basic_imports():
    """기본 임포트 테스트"""
    print("🔍 기본 임포트 테스트 시작...")
    
    try:
        print("  📦 1. sys 모듈...")
        print(f"    ✅ sys.version: {sys.version}")
        
        print("  📦 2. pathlib 모듈...")
        from pathlib import Path
        test_path = Path(__file__)
        print(f"    ✅ Path(__file__): {test_path}")
        
        print("  📦 3. threading 모듈...")
        import threading
        test_lock = threading.Lock()
        print(f"    ✅ threading.Lock(): {type(test_lock)}")
        
        print("  📦 4. time 모듈...")
        import time
        print(f"    ✅ time.sleep: {time.sleep}")
        
        print("  ✅ 모든 기본 임포트 통과")
        return True
        
    except Exception as e:
        print(f"  ❌ 기본 임포트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_structure():
    """프로젝트 구조 테스트"""
    print("🔍 프로젝트 구조 테스트...")
    
    try:
        project_root = Path(__file__).parent
        print(f"  📁 프로젝트 루트: {project_root}")
        
        # 디렉토리 존재 확인
        dirs_to_check = [
            "merged_partial_v2",
            "merged_partial_v2/src",
            "merged_partial_v2/src/merged_partial_v2",
            "merged_partial_v2/src/merged_partial_v2/services",
        ]
        
        for dir_path in dirs_to_check:
            full_path = project_root / dir_path
            exists = full_path.exists()
            print(f"    📁 {dir_path}: {'✅ 존재' if exists else '❌ 없음'}")
        
        print("  ✅ 프로젝트 구조 확인 완료")
        return True
        
    except Exception as e:
        print(f"  ❌ 프로젝트 구조 확인 실패: {e}")
        return False

def test_simple_thread():
    """가장 간단한 스레드 테스트"""
    print("🔍 가장 간단한 스레드 테스트...")
    
    try:
        import threading
        import time
        
        print("  🔄 스레드 생성...")
        
        def simple_worker():
            print("    🚀 워커 시작")
            time.sleep(0.1)
            print("    ✅ 워커 완료")
        
        thread = threading.Thread(target=simple_worker)
        print("  ▶️ 스레드 시작...")
        thread.start()
        
        print("  ⏳ 스레드 대기...")
        thread.join(timeout=2.0)
        
        if thread.is_alive():
            print("  ❌ 스레드 타임아웃")
            return False
        else:
            print("  ✅ 스레드 정상 완료")
            return True
        
    except Exception as e:
        print(f"  ❌ 스레드 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 - 단계별 문제 확인"""
    print("🚀 최소한의 문제 확인 테스트 시작\n")
    
    tests = [
        ("기본 임포트", test_basic_imports),
        ("프로젝트 구조", test_project_structure),
        ("간단한 스레드", test_simple_thread),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🔄 {test_name} 테스트...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} 통과")
            else:
                print(f"❌ {test_name} 실패")
        except Exception as e:
            print(f"❌ {test_name} 예외: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 최종 결과
    print(f"\n{'='*50}")
    print("📊 최종 결과:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 총계: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 기본 테스트 통과!")
    else:
        print("⚠️ 기본적인 문제 발견!")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 프로그램 종료: success={success}")
    sys.exit(0 if success else 1)
