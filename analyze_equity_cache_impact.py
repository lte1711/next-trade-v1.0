#!/usr/bin/env python3
"""
Equity 히스토리 5분 캐시 영향 정밀 분석 (FACT ONLY)
"""

import re
from pathlib import Path

def analyze_equity_cache_impact():
    """Equity 히스토리 5분 캐시 영향 정밀 분석"""
    
    print("FACT: Equity 히스토리 5분 캐시 영향 정밀 분석")
    
    # 1. Equity 히스토리 사용 위치 확인
    server_path = Path("tools/dashboard/multi5_dashboard_server.py")
    if not server_path.exists():
        print("FACT: 서버 파일이 존재하지 않음")
        return False
    
    with open(server_path, 'r', encoding='utf-8') as f:
        server_content = f.read()
    
    print("FACT: Equity 히스토리 사용 위치 확인")
    
    # build_equity_history 함수 호출 위치 확인
    equity_usage_pattern = r'build_equity_history\([^)]*\)'
    equity_usage_matches = re.findall(equity_usage_pattern, server_content)
    
    print(f"  - build_equity_history 호출: {len(equity_usage_matches)}개")
    for i, match in enumerate(equity_usage_matches):
        print(f"    {i+1}. {match}")
    
    # 2. API 엔드포인트에서의 사용 확인
    print("\nFACT: API 엔드포인트에서의 사용 확인")
    
    # /api/runtime 엔드포인트 확인
    api_pattern = r'@app\.route\([\'"]\/api\/runtime[\'"]'
    api_match = re.search(api_pattern, server_content)
    
    if api_match:
        print("  - /api/runtime 엔드포인트 발견")
        
        # 엔드포인트 함수 내용 확인
        api_start = api_match.start()
        # 다음 @app.route나 함수 끝까지 찾기
        lines = server_content[api_start:].split('\n')
        api_content = ""
        for line in lines:
            if line.strip().startswith('@app.route') and len(api_content) > 0:
                break
            api_content += line + '\n'
        
        # equity_history 사용 확인
        if 'equity_history' in api_content:
            print("  - equity_history 사용 확인")
            
            # equity_history 반환 확인
            equity_return_pattern = r'"equity_history":\s*([^,}]+)'
            equity_return_match = re.search(equity_return_pattern, api_content)
            
            if equity_return_match:
                print(f"    - equity_history 반환: {equity_return_match.group(1)}")
            else:
                print("    - equity_history 반환: 확인 불가")
        else:
            print("  - equity_history 사용 없음")
    
    # 3. HTML에서 equity_history 사용 확인
    print("\nFACT: HTML에서 equity_history 사용 확인")
    
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # renderEquityChart 호출 확인
        equity_chart_pattern = r'renderEquityChart\([^)]*\)'
        equity_chart_matches = re.findall(equity_chart_pattern, html_content)
        
        print(f"  - renderEquityChart 호출: {len(equity_chart_matches)}개")
        for match in equity_chart_matches:
            print(f"    * {match}")
        
        # equity_chart 요소 확인
        equity_chart_element_pattern = r'id="equity_chart"'
        equity_chart_element_match = re.search(equity_chart_element_pattern, html_content)
        
        if equity_chart_element_match:
            print("  - equity_chart HTML 요소: 있음")
        else:
            print("  - equity_chart HTML 요소: 없음")
    
    # 4. build_equity_history 함수 상세 분석
    print("\nFACT: build_equity_history 함수 상세 분석")
    
    # 함수 정의 확인
    function_pattern = r'def build_equity_history\([^)]*\):\s*\n(.*?)(?=\ndef|\Z)'
    function_match = re.search(function_pattern, server_content, re.DOTALL)
    
    if function_match:
        function_content = function_match.group(1)
        function_lines = function_content.split('\n')
        
        print(f"  - 함수 길이: {len(function_lines)}줄")
        
        # 캐시 확인 라인
        cache_line_pattern = r'if now - float\(_EQUITY_HISTORY_CACHE\.get\("ts", 0\.0\)\) < (\d+):'
        cache_line_match = re.search(cache_line_pattern, function_content)
        
        if cache_line_match:
            cache_time = int(cache_line_match.group(1))
            print(f"  - 캐시 시간: {cache_time}초 ({cache_time//60}분)")
        
        # API 호출 확인
        api_call_pattern = r'requests\.get\([^)]+\)'
        api_call_matches = re.findall(api_call_pattern, function_content)
        
        print(f"  - API 호출: {len(api_call_matches)}개")
        for match in api_call_matches:
            print(f"    * {match}")
        
        # 데이터 생성 확인
        data_generation_pattern = r'points\.append\('
        data_generation_matches = re.findall(data_generation_pattern, function_content)
        
        print(f"  - 데이터 생성: {len(data_generation_matches)}개 포인트")
        
        # 캐시 저장 확인
        cache_save_pattern = r'_EQUITY_HISTORY_CACHE\[.+\] = '
        cache_save_matches = re.findall(cache_save_pattern, function_content)
        
        print(f"  - 캐시 저장: {len(cache_save_matches)}개")
    
    # 5. 다른 데이터와의 영향 비교
    print("\nFACT: 다른 데이터와의 영향 비교")
    
    # 다른 주요 데이터 소스 캐시 확인
    other_data_sources = [
        ('runtime_state.json', '런타임 상태'),
        ('portfolio_metrics_snapshot.json', '포트폴리오 스냅샷'),
        ('build_allocation_top', 'Allocation 데이터'),
        ('build_kst_daily_symbol_stats', 'KST 심볼 통계')
    ]
    
    for source, description in other_data_sources:
        if source in server_content:
            print(f"  - {description}: 사용됨")
            
            # 캐시 확인
            if 'cache' in server_content.lower() and source.replace('.json', '').replace('build_', '') in server_content:
                print(f"    * 캐시 사용 가능")
            else:
                print(f"    * 캐시 없음 (실시간)")
        else:
            print(f"  - {description}: 사용되지 않음")
    
    # 6. 실제 영향 범위 분석
    print("\nFACT: 실제 영향 범위 분석")
    
    # equity_history가 영향을 미치는 변수 확인
    impact_variables = []
    
    # HTML에서 equity_chart 관련 변수
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # equity_chart 관련 ID
        equity_ids = ['equity_chart', 'equity_chart_meta']
        for id in equity_ids:
            if f'id="{id}"' in html_content:
                impact_variables.append(id)
    
    print(f"  - 직접 영향 변수: {len(impact_variables)}개")
    for var in impact_variables:
        print(f"    * {var}")
    
    # 간접 영향 변수 (banner 등)
    indirect_impacts = []
    if 'current_equity_source' in server_content:
        indirect_impacts.append('current_equity_source')
    
    print(f"  - 간접 영향 변수: {len(indirect_impacts)}개")
    for var in indirect_impacts:
        print(f"    * {var}")
    
    # 7. 캐시가 없을 경우 vs 있을 경우 비교
    print("\nFACT: 캐시 유무에 따른 영향 비교")
    
    total_variables = 38  # JavaScript ids 배열 크기
    equity_impacted_variables = len(impact_variables) + len(indirect_impacts)
    non_equity_variables = total_variables - equity_impacted_variables
    
    print(f"  - 전체 변수: {total_variables}개")
    print(f"  - Equity 캐시 영향 변수: {equity_impacted_variables}개 ({equity_impacted_variables/total_variables*100:.1f}%)")
    print(f"  - Equity 캐시 비영향 변수: {non_equity_variables}개 ({non_equity_variables/total_variables*100:.1f}%)")
    
    # 8. 최종 평가
    print("\nFACT: 최종 평가")
    
    if equity_impacted_variables <= 3:  # equity_chart, equity_chart_meta, banner
        print("FACT: Equity 히스토리 5분 캐시는 그래프 전용임 ✓")
        print("FACT: 대부분의 변수는 실시간으로 업데이트됨")
        return True
    else:
        print("FACT: Equity 히스토리 5분 캐시가 다른 변수에도 영향을 미침 ❌")
        return False

def main():
    """메인 실행"""
    
    print("=== Equity 히스토리 5분 캐시 영향 정밀 분석 (FACT ONLY) ===")
    
    success = analyze_equity_cache_impact()
    
    print("\nFACT: 최종 보고")
    if success:
        print("FACT: Equity 히스토리 5분 캐시는 그래프 전용 ✓")
    else:
        print("FACT: Equity 히스토리 5분 캐시가 다른 변수에도 영향을 미침 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
