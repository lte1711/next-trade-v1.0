#!/usr/bin/env python3
"""
CANDY write_json() Same-Path Race Test
STEP-CANDY-SAME-PATH-RACE-VERIFY-1: 동일 파일 경로 동시 접근 원자성 검증
"""

import sys
import os
import time
import threading
import json
import psutil
import traceback
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 확인된 실제 함수 시그니처와 import 방식 사용
from tools.multi5.multi5_engine_runtime import write_json

def same_path_race_test(thread_id: int, results: List[Dict[str, Any]], test_count: int = 5, target_file: str = "race_test_target.json"):
    """동일 경로 경합 테스트"""
    try:
        for i in range(test_count):
            # 각 쓰레드마다 고유 payload 생성
            test_payload = {
                "thread_id": thread_id,
                "iteration": i,
                "timestamp": time.time(),
                "unique_data": f"thread_{thread_id}_iter_{i}_unique_string_" + "x" * 50
            }
            
            start_time = time.time()
            
            # 동일 파일 경로에 동시 쓰기 시도
            write_json(Path(target_file), test_payload)
            
            end_time = time.time()
            
            # 성공 기록
            results.append({
                "thread_id": thread_id,
                "iteration": i,
                "write_time_ms": (end_time - start_time) * 1000,
                "success": True,
                "exception": None,
                "payload_hash": hash(str(test_payload))
            })
            
    except Exception as e:
        # 예외 발생 기록
        results.append({
            "thread_id": thread_id,
            "success": False,
            "exception": str(e),
            "exception_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })

def analyze_final_file(target_file: str, all_payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """최종 파일 분석"""
    analysis = {
        "file_exists": False,
        "file_size": 0,
        "json_parse_success": False,
        "json_parse_error": None,
        "payload_is_whole_object": False,
        "partial_write_detected": False,
        "corrupted_json_detected": False,
        "payload_match_found": False,
        "matching_payload": None
    }
    
    try:
        target_path = Path(target_file)
        if target_path.exists():
            analysis["file_exists"] = True
            analysis["file_size"] = target_path.stat().st_size
            
            # 파일 내용 읽기
            content = target_path.read_text()
            
            # JSON 파싱 시도
            try:
                parsed = json.loads(content)
                analysis["json_parse_success"] = True
                
                # payload가 전체 객체인지 확인 (부분 문자열 아닌지)
                if isinstance(parsed, dict) and all(key in parsed for key in ["thread_id", "iteration", "timestamp", "unique_data"]):
                    analysis["payload_is_whole_object"] = True
                    
                    # 테스트된 payload 중 일치하는 것이 있는지 확인
                    for payload in all_payloads:
                        if (parsed.get("thread_id") == payload["thread_id"] and 
                            parsed.get("iteration") == payload["iteration"] and
                            parsed.get("unique_data") == payload["unique_data"]):
                            analysis["payload_match_found"] = True
                            analysis["matching_payload"] = payload
                            break
                else:
                    analysis["partial_write_detected"] = True
                    
            except json.JSONDecodeError as e:
                analysis["json_parse_error"] = str(e)
                analysis["corrupted_json_detected"] = True
                
    except Exception as e:
        analysis["file_read_error"] = str(e)
    
    return analysis

def main():
    """메인 테스트 실행"""
    print("=== CANDY write_json() Same-Path Race Test ===")
    print(f"Python path: {sys.executable}")
    print(f"Project root: {project_root}")
    
    # 테스트 설정
    thread_count = 10
    test_count_per_thread = 5
    target_file = "tools/validation/same_path_race_target.json"
    total_attempts = thread_count * test_count_per_thread
    
    print(f"Same-path race test: {thread_count} threads, {test_count_per_thread} writes per thread")
    print(f"Total attempts: {total_attempts}")
    print(f"Target file: {target_file}")
    
    # 테스트 전 파일 정리
    if Path(target_file).exists():
        Path(target_file).unlink()
        print("Pre-existing target file cleaned")
    
    # 모든 테스트 payload 생성 (나중에 비교용)
    all_test_payloads = []
    for thread_id in range(thread_count):
        for i in range(test_count_per_thread):
            payload = {
                "thread_id": thread_id,
                "iteration": i,
                "timestamp": time.time(),  # 실제 실행 시에는 다른 값이 들어감
                "unique_data": f"thread_{thread_id}_iter_{i}_unique_string_" + "x" * 50
            }
            all_test_payloads.append(payload)
    
    # 결과 수집
    all_results: List[Dict[str, Any]] = []
    threads = []
    
    # 동시 실행
    start_time = time.time()
    
    for i in range(thread_count):
        thread = threading.Thread(target=same_path_race_test, args=(i, all_results, test_count_per_thread, target_file))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    # 최종 파일 분석
    final_analysis = analyze_final_file(target_file, all_test_payloads)
    
    # 결과 통계
    successful_calls = [r for r in all_results if r.get("success", False) == True]
    exception_calls = [r for r in all_results if r.get("success", False) == False]
    
    # 결과 저장
    results = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "python_path": sys.executable,
            "project_root": str(project_root),
            "target_file": target_file,
            "total_attempts": total_attempts,
            "thread_count": thread_count,
            "test_count_per_thread": test_count_per_thread,
            "total_execution_time_ms": (end_time - start_time) * 1000
        },
        "race_test_metrics": {
            "total_attempts": total_attempts,
            "success_call_count": len(successful_calls),
            "exception_count": len(exception_calls),
            "success_rate_percent": (len(successful_calls) / total_attempts) * 100 if total_attempts > 0 else 0
        },
        "final_file_analysis": final_analysis,
        "detailed_results": all_results
    }
    
    # 결과 파일 저장
    Path("tools/validation").mkdir(exist_ok=True)
    
    with open("tools/validation/same_path_race_test_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_attempts": total_attempts,
            "success_call_count": len(successful_calls),
            "exception_count": len(exception_calls),
            "success_rate_percent": (len(successful_calls) / total_attempts) * 100 if total_attempts > 0 else 0,
            "final_json_parse_success": final_analysis["json_parse_success"],
            "final_json_parse_error": final_analysis.get("json_parse_error"),
            "final_payload_is_whole_object": final_analysis["payload_is_whole_object"],
            "partial_write_detected": final_analysis["partial_write_detected"],
            "corrupted_json_detected": final_analysis["corrupted_json_detected"],
            "payload_match_found": final_analysis["payload_match_found"]
        }, f, indent=2)
    
    with open("tools/validation/same_path_race_test_complete_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    # 로그 기록
    log_entry = f"""
=== Same-Path Race Test Log ===
Timestamp: {datetime.now().isoformat()}
Target File: {target_file}
Total Attempts: {total_attempts}
Success Calls: {len(successful_calls)}
Exceptions: {len(exception_calls)}
Final File Exists: {final_analysis['file_exists']}
JSON Parse Success: {final_analysis['json_parse_success']}
Payload Is Whole Object: {final_analysis['payload_is_whole_object']}
Partial Write Detected: {final_analysis['partial_write_detected']}
Corrupted JSON Detected: {final_analysis['corrupted_json_detected']}
Payload Match Found: {final_analysis['payload_match_found']}
"""
    
    with open("tools/validation/same_path_race_test.log", "w", encoding="utf-8") as f:
        f.write(log_entry)
    
    # 결과 출력
    print(f"\n=== Test Results ===")
    print(f"Total attempts: {total_attempts}")
    print(f"Success calls: {len(successful_calls)}")
    print(f"Exceptions: {len(exception_calls)}")
    print(f"Success rate: {(len(successful_calls)/total_attempts)*100:.1f}%")
    print(f"\n=== Final File Analysis ===")
    print(f"File exists: {final_analysis['file_exists']}")
    print(f"JSON parse success: {final_analysis['json_parse_success']}")
    print(f"Payload is whole object: {final_analysis['payload_is_whole_object']}")
    print(f"Partial write detected: {final_analysis['partial_write_detected']}")
    print(f"Corrupted JSON detected: {final_analysis['corrupted_json_detected']}")
    print(f"Payload match found: {final_analysis['payload_match_found']}")
    
    # PASS/FAIL 판정
    pass_conditions = [
        len(exception_calls) == 0,  # 예외 0
        final_analysis["json_parse_success"],  # JSON 파싱 성공
        not final_analysis["partial_write_detected"],  # partial write 없음
        not final_analysis["corrupted_json_detected"],  # 깨진 JSON 없음
        final_analysis["payload_match_found"]  # payload 일치
    ]
    
    if all(pass_conditions):
        print(f"\n=== RESULT: PASS ===")
        print("All race condition tests passed")
    else:
        print(f"\n=== RESULT: FAIL ===")
        print("Race condition test failed")
        for i, condition in enumerate(pass_conditions):
            if not condition:
                condition_names = ["No exceptions", "JSON parse success", "No partial write", "No corrupted JSON", "Payload match found"]
                print(f"Failed condition: {condition_names[i]}")

if __name__ == "__main__":
    main()
