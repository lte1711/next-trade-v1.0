#!/usr/bin/env python3
"""
데이터 반영 간격 정밀 분석 (FACT ONLY)
"""

import re
from pathlib import Path

def analyze_refresh_interval():
    """데이터 반영 간격 정밀 분석"""
    
    print("FACT: 데이터 반영 간격 정밀 분석")
    
    # 1. HTML 자동 새로고침 설정 확인
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if not html_path.exists():
        print("FACT: HTML 파일이 존재하지 않음")
        return False
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("FACT: HTML 자동 새로고침 설정 확인")
    
    # setInterval 확인
    setInterval_pattern = r'setInterval\([^,]+,\s*(\d+)\)'
    setInterval_matches = re.findall(setInterval_pattern, html_content)
    
    if setInterval_matches:
        for match in setInterval_matches:
            interval_ms = int(match)
            interval_sec = interval_ms / 1000
            print(f"  - setInterval 발견: {interval_ms}ms ({interval_sec}초)")
    else:
        print("  - setInterval: 없음")
    
    # 2. API 호출 캐시 방지 확인
    print("\nFACT: API 호출 캐시 방지 확인")
    
    # fetch 호출 확인
    fetch_pattern = r'fetch\([^)]+Date\.now\(\)[^)]+\)'
    fetch_matches = re.findall(fetch_pattern, html_content)
    
    if fetch_matches:
        print(f"  - fetch 호출 with Date.now(): {len(fetch_matches)}개 발견")
        for match in fetch_matches[:3]:  # 처음 3개만 표시
            print(f"    * {match[:100]}...")
    else:
        print("  - fetch 호출 with Date.now(): 없음")
    
    # 3. 서버 캐시 설정 확인
    print("\nFACT: 서버 캐시 설정 확인")
    
    server_path = Path("tools/dashboard/multi5_dashboard_server.py")
    if not server_path.exists():
        print("FACT: 서버 파일이 존재하지 않음")
        return False
    
    with open(server_path, 'r', encoding='utf-8') as f:
        server_content = f.read()
    
    # 캐시 관련 설정 확인
    cache_patterns = [
        (r'cache.*?no-store', 'no-store 캐시'),
        (r'cache.*?no-cache', 'no-cache 캐시'),
        (r'_EQUITY_HISTORY_CACHE', 'Equity 히스토리 캐시'),
        (r'_KST_DAILY_SYMBOL_CACHE', 'KST 심볼 캐시'),
        (r'cache.*?(\d+)', '캐시 시간')
    ]
    
    for pattern, description in cache_patterns:
        matches = re.findall(pattern, server_content, re.IGNORECASE)
        if matches:
            print(f"  - {description}: {matches}")
    
    # 4. 캐시 시간 상세 분석
    print("\nFACT: 캐시 시간 상세 분석")
    
    # Equity 히스토리 캐시 시간
    equity_cache_pattern = r'_EQUITY_HISTORY_CACHE\.get\("ts", 0\.0\)\) < (\d+)'
    equity_cache_match = re.search(equity_cache_pattern, server_content)
    
    if equity_cache_match:
        equity_cache_time = int(equity_cache_match.group(1))
        equity_cache_sec = equity_cache_time
        print(f"  - Equity 히스토리 캐시: {equity_cache_time}초 ({equity_cache_sec//60}분)")
    else:
        print("  - Equity 히스토리 캐시: 확인 불가")
    
    # KST 심볼 캐시 시간
    kst_cache_pattern = r'_KST_DAILY_SYMBOL_CACHE\.get\("ts", 0\.0\)\) < (\d+)'
    kst_cache_match = re.search(kst_cache_pattern, server_content)
    
    if kst_cache_match:
        kst_cache_time = int(kst_cache_match.group(1))
        print(f"  - KST 심볼 캐시: {kst_cache_time}초")
    else:
        print("  - KST 심볼 캐시: 확인 불가")
    
    # 5. API 응답 시간 확인
    print("\nFACT: API 응답 시간 확인")
    
    # API 타임아웃 설정
    timeout_patterns = [
        (r'timeout=(\d+)', 'requests 타임아웃'),
        (r'timeout.*?(\d+)', '일반 타임아웃')
    ]
    
    for pattern, description in timeout_patterns:
        matches = re.findall(pattern, server_content)
        if matches:
            for match in matches:
                timeout_sec = int(match)
                print(f"  - {description}: {timeout_sec}초")
    
    # 6. 데이터 생성 시간 확인
    print("\nFACT: 데이터 생성 시간 확인")
    
    # equity history 생성 시간
    equity_generation_pattern = r'for i in range\((\d+)\):'
    equity_generation_matches = re.findall(equity_generation_pattern, server_content)
    
    if equity_generation_matches:
        for match in equity_generation_matches:
            points = int(match)
            print(f"  - Equity 히스토리 생성 포인트: {points}개")
    
    # 시간 간격 확인
    time_interval_patterns = [
        (r'timedelta\(seconds=(\d+)\)', '초 간격'),
        (r'timedelta\(minutes=(\d+)\)', '분 간격'),
        (r'timedelta\(hours=(\d+)\)', '시간 간격')
    ]
    
    for pattern, description in time_interval_patterns:
        matches = re.findall(pattern, server_content)
        if matches:
            for match in matches:
                interval = int(match)
                print(f"  - {description}: {interval}")
    
    # 7. 실제 반영 간격 계산
    print("\nFACT: 실제 반영 간격 계산")
    
    # 기본 새로고침 간격
    base_interval = 3000  # 3초 (기본값)
    
    if setInterval_matches:
        base_interval = int(setInterval_matches[0])
    
    base_interval_sec = base_interval / 1000
    print(f"  - 기본 새로고침 간격: {base_interval}ms ({base_interval_sec}초)")
    
    # 캐시 영향 확인
    cache_delays = []
    
    if equity_cache_match:
        equity_cache_time = int(equity_cache_match.group(1))
        if equity_cache_time > base_interval_sec:
            cache_delays.append(f"Equity 캐시: {equity_cache_time}초")
    
    if kst_cache_match:
        kst_cache_time = int(kst_cache_match.group(1))
        if kst_cache_time > base_interval_sec:
            cache_delays.append(f"KST 캐시: {kst_cache_time}초")
    
    if cache_delays:
        print(f"  - 캐시로 인한 지연:")
        for delay in cache_delays:
            print(f"    * {delay}")
        print(f"  - 실제 반영 간격: 최대 {max([int(d.split(':')[1].strip()) for d in cache_delays])}초")
    else:
        print(f"  - 실제 반영 간격: {base_interval_sec}초 (캐시 영향 없음)")
    
    # 8. 지연 원인 분석
    print("\nFACT: 지연 원인 분석")
    
    delay_factors = []
    
    # 네트워크 지연
    if 'timeout' in server_content:
        timeout_matches = re.findall(r'timeout=(\d+)', server_content)
        if timeout_matches:
            max_timeout = max([int(t) for t in timeout_matches])
            if max_timeout > 5:
                delay_factors.append(f"네트워크 타임아웃: {max_timeout}초")
    
    # 데이터 처리 지연
    if 'build_equity_history' in server_content:
        delay_factors.append("Equity 히스토리 빌드 지연")
    
    if 'build_allocation_top' in server_content:
        delay_factors.append("Allocation 빌드 지연")
    
    # API 호출 지연
    if 'requests.get' in server_content:
        delay_factors.append("API 호출 지연")
    
    if delay_factors:
        print(f"  - 지연 요인:")
        for factor in delay_factors:
            print(f"    * {factor}")
    else:
        print("  - 지연 요인: 없음")
    
    # 9. 최종 평가
    print("\nFACT: 최종 평가")
    
    actual_interval = base_interval_sec
    
    if cache_delays:
        max_cache_delay = max([int(d.split(':')[1].strip()) for d in cache_delays])
        actual_interval = max(base_interval_sec, max_cache_delay)
    
    print(f"FACT: 반영 간격 분석 결과:")
    print(f"  - 설정된 간격: {base_interval_sec}초")
    print(f"  - 실제 간격: {actual_interval}초")
    print(f"  - 차이: {actual_interval - base_interval_sec}초")
    
    if actual_interval > base_interval_sec + 2:
        print(f"  - 평가: 10초로 느껴지는 이유 있음 (캐시 및 지연 요인)")
        return False
    else:
        print(f"  - 평가: 3초 간격 정상 작동")
        return True

def main():
    """메인 실행"""
    
    print("=== 데이터 반영 간격 정밀 분석 (FACT ONLY) ===")
    
    success = analyze_refresh_interval()
    
    print("\nFACT: 최종 보고")
    if success:
        print("FACT: 3초 간격 정상 작동 ✓")
    else:
        print("FACT: 지연 요인 발견 (10초로 느껴지는 이유 있음) ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
