#!/usr/bin/env python3
"""
CANDY write_json() Performance Test
PHASE C: 테스트 파일 생성 - 확인된 시그니처와 Python 경로 기반
"""

import sys
import os
import time
import threading
import json
import psutil
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 확인된 실제 함수 시그니처와 import 방식 사용
from tools.multi5.multi5_engine_runtime import write_json

def get_memory_usage() -> int:
    """메모리 사용량(bytes) 반환"""
    process = psutil.Process()
    return process.memory_info().rss

def concurrent_write_test(thread_id: int, results: List[Dict[str, Any]], test_count: int = 5):
    """동시성 쓰기 테스트"""
    try:
        for i in range(test_count):
            test_path = Path(f"concurrent_test_{thread_id}_{i}.json")
            test_payload = {
                "thread_id": thread_id,
                "iteration": i,
                "timestamp": time.time(),
                "data": "x" * 100  # 100 bytes 데이터
            }
            
            start_time = time.time()
            write_json(test_path, test_payload)
            end_time = time.time()
            
            # 파일 읽기 검증
            content = test_path.read_text()
            parsed = json.loads(content)
            
            # 데이터 무결성 확인
            if (parsed["thread_id"] == thread_id and 
                parsed["iteration"] == i and 
                parsed["data"] == "x" * 100):
                
                results.append({
                    "thread_id": thread_id,
                    "iteration": i,
                    "write_time_ms": (end_time - start_time) * 1000,
                    "file_size": test_path.stat().st_size,
                    "success": True,
                    "json_parse_success": True,
                    "payload_match": True
                })
            else:
                results.append({
                    "thread_id": thread_id,
                    "iteration": i,
                    "success": False,
                    "json_parse_success": False,
                    "payload_match": False,
                    "error": "Data corruption"
                })
            
            test_path.unlink()  # 테스트 파일 정리
            
    except Exception as e:
        results.append({
            "thread_id": thread_id,
            "success": False,
            "error": str(e)
        })

def main():
    """메인 테스트 실행"""
    print("=== CANDY write_json() Performance Test ===")
    print(f"Python path: {sys.executable}")
    print(f"Project root: {project_root}")
    
    # 초기 메모리 측정
    initial_memory = get_memory_usage()
    
    # 동시성 테스트 설정
    thread_count = 10
    test_count_per_thread = 5
    total_requests = thread_count * test_count_per_thread
    
    print(f"Concurrency test: {thread_count} threads, {test_count_per_thread} writes per thread")
    print(f"Total requests: {total_requests}")
    
    # 결과 수집
    all_results: List[Dict[str, Any]] = []
    threads = []
    
    # 동시 실행
    start_time = time.time()
    
    for i in range(thread_count):
        thread = threading.Thread(target=concurrent_write_test, args=(i, all_results, test_count_per_thread))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    # 최종 메모리 측정
    final_memory = get_memory_usage()
    
    # 결과 분석
    successful_writes = [r for r in all_results if r.get("success", False) == True]
    failed_writes = [r for r in all_results if r.get("success", False) == False]
    
    # 성공 결과에서 시간 통계 계산
    if successful_writes:
        write_times = [r["write_time_ms"] for r in successful_writes]
        avg_time = sum(write_times) / len(write_times)
        min_time = min(write_times)
        max_time = max(write_times)
        median_time = sorted(write_times)[len(write_times) // 2]
    else:
        avg_time = min_time = max_time = median_time = 0
    
    # JSON 파싱 및 페이로드 일치 통계
    json_parse_success = sum(1 for r in all_results if r.get("json_parse_success", False) == True)
    payload_match_success = sum(1 for r in all_results if r.get("payload_match", False) == True)
    
    # 결과 저장
    results = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "python_path": sys.executable,
            "project_root": str(project_root),
            "total_requested_writes": total_requests,
            "thread_count": thread_count,
            "test_count_per_thread": test_count_per_thread,
            "total_execution_time_ms": (end_time - start_time) * 1000
        },
        "performance_metrics": {
            "success_count": len(successful_writes),
            "fail_count": len(failed_writes),
            "success_rate_percent": (len(successful_writes) / total_requests) * 100,
            "avg_ms": avg_time,
            "min_ms": min_time,
            "max_ms": max_time,
            "median_ms": median_time
        },
        "memory_metrics": {
            "rss_before_bytes": initial_memory,
            "rss_after_bytes": final_memory,
            "rss_delta_bytes": final_memory - initial_memory
        },
        "integrity_metrics": {
            "json_parse_success_count": json_parse_success,
            "json_parse_error_count": total_requests - json_parse_success,
            "payload_match_count": payload_match_success,
            "payload_mismatch_count": total_requests - payload_match_success
        },
        "detailed_results": all_results
    }
    
    # 개별 결과 파일들 저장
    Path("tools/validation").mkdir(exist_ok=True)
    
    with open("tools/validation/concurrency_test_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_requested_writes": total_requests,
            "success_count": len(successful_writes),
            "fail_count": len(failed_writes),
            "success_rate_percent": (len(successful_writes) / total_requests) * 100
        }, f, indent=2)
    
    with open("tools/validation/write_latency_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "avg_ms": avg_time,
            "min_ms": min_time,
            "max_ms": max_time,
            "median_ms": median_time,
            "total_execution_time_ms": (end_time - start_time) * 1000
        }, f, indent=2)
    
    with open("tools/validation/memory_usage_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "rss_before_bytes": initial_memory,
            "rss_after_bytes": final_memory,
            "rss_delta_bytes": final_memory - initial_memory
        }, f, indent=2)
    
    with open("tools/validation/integrity_check_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "json_parse_success_count": json_parse_success,
            "json_parse_error_count": total_requests - json_parse_success,
            "payload_match_count": payload_match_success,
            "payload_mismatch_count": total_requests - payload_match_success
        }, f, indent=2)
    
    # 전체 결과 저장
    with open("tools/validation/performance_test_complete_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"=== Test Complete ===")
    print(f"Success: {len(successful_writes)}/{total_requests} ({(len(successful_writes)/total_requests)*100:.1f}%)")
    print(f"Avg time: {avg_time:.2f}ms")
    print(f"Memory delta: {final_memory - initial_memory} bytes")
    print(f"JSON parse success: {json_parse_success}/{total_requests}")
    print(f"Payload match: {payload_match_success}/{total_requests}")

if __name__ == "__main__":
    main()
