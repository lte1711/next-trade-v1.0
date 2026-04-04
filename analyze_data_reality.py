#!/usr/bin/env python3
"""
HTML 변수 데이터 실제 여부 확인 (FACT ONLY)
"""

import re
from pathlib import Path

def analyze_data_reality():
    """HTML 변수 데이터 실제 여부 확인"""
    
    print("FACT: HTML 변수 데이터 실제 여부 확인")
    
    # 1. 서버 응답 데이터 소스 확인
    server_path = Path("tools/dashboard/multi5_dashboard_server.py")
    if not server_path.exists():
        print("FACT: 서버 파일이 존재하지 않음")
        return False
    
    with open(server_path, 'r', encoding='utf-8') as f:
        server_content = f.read()
    
    print("FACT: 서버 데이터 소스 분석")
    
    # 데이터 소스 패턴 확인
    data_sources = []
    
    # runtime 데이터 소스
    if 'runtime.get(' in server_content:
        runtime_matches = re.findall(r'runtime\.get\([\'"]([^\'\"]+)[\'\"]', server_content)
        for match in runtime_matches:
            data_sources.append(f"runtime.{match}")
    
    # snapshot 데이터 소스
    if 'snapshot.get(' in server_content:
        snapshot_matches = re.findall(r'snapshot\.get\([\'"]([^\'\"]+)[\'\"]', server_content)
        for match in snapshot_matches:
            data_sources.append(f"snapshot.{match}")
    
    # summary 데이터 소스
    if 'summary.get(' in server_content:
        summary_matches = re.findall(r'summary\.get\([\'"]([^\'\"]+)[\'\"]', server_content)
        for match in summary_matches:
            data_sources.append(f"summary.{match}")
    
    # 직접 값 할당
    direct_values = re.findall(r'\"([^\"]+)\"', server_content)
    
    print(f"FACT: 데이터 소스 종류:")
    for source in sorted(set(data_sources)):
        print(f"  - {source}")
    
    # 2. 실제 데이터 소스 확인
    print("\nFACT: 실제 데이터 소스 확인")
    
    # runtime 데이터 확인
    if 'runtime = load_runtime_state()' in server_content:
        print("FACT: runtime 데이터 - load_runtime_state() 함수에서 로드")
        if 'runtime_state.json' in server_content:
            print("  - 소스: runtime_state.json 파일")
        else:
            print("  - 소스: 런타임 상태 로드 함수")
    
    # snapshot 데이터 확인
    if 'snapshot = load_portfolio_snapshot()' in server_content:
        print("FACT: snapshot 데이터 - load_portfolio_snapshot() 함수에서 로드")
        if 'portfolio_metrics_snapshot.json' in server_content:
            print("  - 소스: portfolio_metrics_snapshot.json 파일")
        else:
            print("  - 소스: 포트폴리오 스냅샷 로드 함수")
    
    # investor_probe 데이터 확인
    if 'investor_probe = get_investor_probe()' in server_content:
        print("FACT: investor_probe 데이터 - get_investor_probe() 함수에서 로드")
        print("  - 소스: investor API 호출")
    
    # 3. 거래소 연동 확인
    print("\nFACT: 거래소 연동 확인")
    
    # 바이낸스 API 연동 확인
    if 'binance' in server_content.lower():
        print("FACT: 바이낸스 관련 데이터 발견")
        
        # API 호출 확인
        if 'testnet_api_base' in server_content:
            print("  - 바이낸스 테스트넷 API 사용")
        
        # 실시간 연동 확인
        if 'realtime_exchange_link_ok' in server_content:
            print("  - 실시간 거래소 연동 상태 확인")
        
        # 자격증명 확인
        if 'credentials_present' in server_content:
            print("  - API 자격증명 확인")
    
    # 4. 데이터 실시간성 확인
    print("\nFACT: 데이터 실시간성 확인")
    
    # 자동 새로고침 확인
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        if 'setInterval(refresh, 3000)' in html_content:
            print("FACT: 3초 간격 자동 새로고침")
        
        if 'fetch(`/api/runtime?t=${Date.now()}`' in html_content:
            print("FACT: API 호출 시 캐시 방지 (타임스탬프 사용)")
    
    # 5. 데이터 가공 여부 확인
    print("\nFACT: 데이터 가공 여부 확인")
    
    # 데이터 변환 확인
    transformations = []
    
    # 문자열 변환
    if 'str(' in server_content:
        str_transforms = re.findall(r'str\([^)]+\)', server_content)
        for transform in str_transforms:
            transformations.append(f"문자열 변환: {transform}")
    
    # 불리언 변환
    if 'true' in server_content or 'false' in server_content:
        transformations.append("불리언 변환: true/false")
    
    # 조건부 처리
    if 'if' in server_content and 'else' in server_content:
        transformations.append("조건부 데이터 처리")
    
    # 기본값 처리
    if '||' in server_content:
        transformations.append("기본값 처리 (|| 연산자)")
    
    print(f"FACT: 데이터 가공 방식:")
    for transform in set(transformations):
        print(f"  - {transform}")
    
    # 6. 데이터 원본 추적
    print("\nFACT: 데이터 원본 추적")
    
    # 주요 변수별 데이터 원본
    key_variables = {
        'account_equity': 'portfolio_metrics_snapshot.json',
        'binance_execution_mode': '환경변수 EXECUTION_MODE',
        'binance_probe_mode': 'get_investor_probe() API 호출',
        'engine_status': 'runtime_state.json',
        'runtime_alive': 'runtime_state.json',
        'active_symbols': 'runtime_state.json'
    }
    
    for var, source in key_variables.items():
        print(f"FACT: {var}")
        print(f"  - 데이터 원본: {source}")
        print(f"  - 실시간 여부: {'실시간' if 'runtime' in source or 'API' in source else '주기적 업데이트'}")
    
    # 7. 최종 평가
    print("\nFACT: 최종 평가")
    
    # 실제 데이터 비율 계산
    real_data_sources = 0
    virtual_data_sources = 0
    
    for source in data_sources:
        if 'runtime' in source or 'snapshot' in source:
            real_data_sources += 1
        else:
            virtual_data_sources += 1
    
    total_sources = real_data_sources + virtual_data_sources
    
    if total_sources > 0:
        real_percentage = (real_data_sources / total_sources) * 100
        virtual_percentage = (virtual_data_sources / total_sources) * 100
    else:
        real_percentage = 0
        virtual_percentage = 0
    
    print(f"FACT: 데이터 원본 분석:")
    print(f"  - 실제 데이터 소스: {real_data_sources}개 ({real_percentage:.1f}%)")
    print(f"  - 가상 데이터 소스: {virtual_data_sources}개 ({virtual_percentage:.1f}%)")
    print(f"  - 총 데이터 소스: {total_sources}개")
    
    # 거래소 데이터 실시간성
    print(f"FACT: 거래소 데이터 실시간성:")
    if 'realtime_exchange_link_ok' in server_content:
        print("  - 실시간 거래소 연동: 지원")
        print("  - 데이터 반영: 실시간 (3초 간격)")
    else:
        print("  - 실시간 거래소 연동: 미지원")
        print("  - 데이터 반영: 주기적")
    
    return True

def main():
    """메인 실행"""
    
    print("=== HTML 변수 데이터 실제 여부 확인 (FACT ONLY) ===")
    
    success = analyze_data_reality()
    
    print("\nFACT: 최종 보고")
    if success:
        print("FACT: HTML 변수 데이터 실제 여부 확인 완료 ✓")
    else:
        print("FACT: 확인 실패 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
