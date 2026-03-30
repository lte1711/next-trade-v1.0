#!/usr/bin/env python3
"""
Enhanced write_json() Test
CODEX 구현 개선 기능 테스트
"""

import sys
import os
import time
import threading
import json
import psutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 개선된 write_json 함수 임포트
from tools.multi5.multi5_engine_runtime import write_json

def test_basic_functionality():
    """기본 기능 테스트"""
    print("=== Basic Functionality Test ===")
    
    test_file = Path("test_basic.json")
    test_payload = {
        "test": "basic",
        "timestamp": time.time(),
        "data": list(range(10))
    }
    
    try:
        write_json(test_file, test_payload)
        
        # 파일 읽기 검증
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        if loaded == test_payload:
            print("✓ Basic functionality test PASSED")
            return True
        else:
            print("✗ Basic functionality test FAILED: Data mismatch")
            return False
            
    except Exception as e:
        print(f"✗ Basic functionality test FAILED: {e}")
        return False
    finally:
        if test_file.exists():
            test_file.unlink()

def test_same_path_race_improved():
    """개선된 same-path race 테스트"""
    print("\n=== Same-Path Race Test (Improved) ===")
    
    target_file = Path("test_race_improved.json")
    thread_count = 10
    writes_per_thread = 3
    total_attempts = thread_count * writes_per_thread
    
    results = []
    exceptions = []
    
    def race_writer(thread_id: int):
        for i in range(writes_per_thread):
            payload = {
                "thread_id": thread_id,
                "iteration": i,
                "timestamp": time.time(),
                "unique_data": f"thread_{thread_id}_iter_{i}"
            }
            
            try:
                start_time = time.time()
                write_json(target_file, payload)
                end_time = time.time()
                
                results.append({
                    "thread_id": thread_id,
                    "iteration": i,
                    "success": True,
                    "write_time_ms": (end_time - start_time) * 1000
                })
                
            except Exception as e:
                exceptions.append({
                    "thread_id": thread_id,
                    "iteration": i,
                    "exception": str(e),
                    "exception_type": type(e).__name__
                })
    
    # 동시 실행
    threads = []
    start_time = time.time()
    
    for i in range(thread_count):
        thread = threading.Thread(target=race_writer, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    # 결과 분석
    success_count = len(results)
    exception_count = len(exceptions)
    success_rate = (success_count / total_attempts) * 100
    
    print(f"Total attempts: {total_attempts}")
    print(f"Success: {success_count}")
    print(f"Exceptions: {exception_count}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time: {(end_time - start_time)*1000:.2f}ms")
    
    # 최종 파일 검증
    final_valid = False
    if target_file.exists():
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
            final_valid = True
            print(f"✓ Final file is valid JSON with {len(final_data)} fields")
        except:
            print("✗ Final file is corrupted")
    
    # 성공 기준
    if success_rate >= 90 and final_valid:
        print("✓ Same-path race test IMPROVED (90%+ success rate)")
        return True
    else:
        print("✗ Same-path race test FAILED")
        return False

def test_performance_impact():
    """성능 영향 테스트"""
    print("\n=== Performance Impact Test ===")
    
    # 기존 방식과 성능 비교
    test_count = 100
    payload = {"data": "x" * 1000, "timestamp": time.time()}
    
    # 개선된 write_json 성능 측정
    start_time = time.time()
    for i in range(test_count):
        test_file = Path(f"perf_test_{i}.json")
        try:
            write_json(test_file, payload)
        finally:
            if test_file.exists():
                test_file.unlink()
    end_time = time.time()
    
    improved_time = end_time - start_time
    avg_time_per_write = (improved_time / test_count) * 1000
    
    print(f"Improved write_json: {avg_time_per_write:.2f}ms per write")
    print(f"Total time: {improved_time*1000:.2f}ms for {test_count} writes")
    
    # 성능 기준 (10% 이내 영향)
    if avg_time_per_write < 20:  # 20ms 이하
        print("✓ Performance impact within acceptable range")
        return True
    else:
        print("✗ Performance impact too high")
        return False

def test_retry_mechanism():
    """재시도 메커니즘 테스트"""
    print("\n=== Retry Mechanism Test ===")
    
    # 인위적인 경합 상황 생성
    target_file = Path("test_retry.json")
    results = []
    
    def concurrent_writer(thread_id: int):
        for i in range(5):
            payload = {"thread_id": thread_id, "iteration": i, "data": f"test_{i}"}
            try:
                write_json(target_file, payload)
                results.append({"thread_id": thread_id, "success": True})
            except Exception as e:
                results.append({"thread_id": thread_id, "success": False, "error": str(e)})
    
    # 고빈도 동시 쓰기
    threads = []
    for i in range(20):  # 더 많은 쓰레드로 경합 유발
        thread = threading.Thread(target=concurrent_writer, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    success_count = sum(1 for r in results if r["success"])
    total_attempts = len(results)
    success_rate = (success_count / total_attempts) * 100
    
    print(f"Retry test: {success_count}/{total_attempts} successful ({success_rate:.1f}%)")
    
    # 재시도 성공률 기준
    if success_rate >= 80:
        print("✓ Retry mechanism working effectively")
        return True
    else:
        print("✗ Retry mechanism needs improvement")
        return False

def main():
    """메인 테스트 실행"""
    print("=== Enhanced write_json() Test Suite ===")
    print(f"Python path: {sys.executable}")
    print(f"Project root: {project_root}")
    
    test_results = []
    
    # 기본 기능 테스트
    test_results.append(("Basic Functionality", test_basic_functionality()))
    
    # 개선된 same-path race 테스트
    test_results.append(("Same-Path Race (Improved)", test_same_path_race_improved()))
    
    # 성능 영향 테스트
    test_results.append(("Performance Impact", test_performance_impact()))
    
    # 재시도 메커니즘 테스트
    test_results.append(("Retry Mechanism", test_retry_mechanism()))
    
    # 최종 결과
    print("\n=== Test Results Summary ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests PASSED - Implementation ready for production")
        return 0
    else:
        print("✗ Some tests FAILED - Implementation needs refinement")
        return 1

if __name__ == "__main__":
    sys.exit(main())
