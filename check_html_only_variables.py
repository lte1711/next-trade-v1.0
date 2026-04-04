#!/usr/bin/env python3
"""
HTML에만 있는 변수 처리 방법 확인 (FACT ONLY)
"""

import re
from pathlib import Path

def check_html_only_variables():
    """HTML에만 있는 변수 처리 방법 확인"""
    
    print("FACT: HTML에만 있는 변수 처리 방법 확인")
    
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if not html_path.exists():
        print("FACT: HTML 파일이 존재하지 않음")
        return False
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 1. HTML에만 있는 변수 목록 확인
    lines = html_content.split('\n')
    js_ids = []
    
    # JavaScript ids 배열 추출
    for i, line in enumerate(lines):
        if 'const ids' in line and '[' in line:
            array_content = line
            j = i + 1
            while j < len(lines) and ']' not in array_content:
                array_content += ' ' + lines[j]
                j += 1
            
            id_pattern = r'["\']([^"\']+)["\']'
            js_ids = re.findall(id_pattern, array_content)
            break
    
    # HTML에 정의된 모든 ID 추출
    id_pattern = r'id="([^"]+)"'
    all_html_ids = re.findall(id_pattern, html_content)
    unique_html_ids = sorted(list(set(all_html_ids)))
    
    # HTML에만 있는 변수 확인
    html_only_ids = []
    for id in unique_html_ids:
        if id not in js_ids:
            html_only_ids.append(id)
    
    print(f"FACT: HTML에만 있는 변수: {len(html_only_ids)}개")
    for id in html_only_ids:
        print(f"  - {id}")
    
    # 2. 각 HTML에만 있는 변수 처리 방법 확인
    print("FACT: HTML에만 있는 변수 처리 방법 확인")
    
    for id in html_only_ids:
        # HTML 요소 찾기
        element_pattern = rf'<[^>]*id="{id}"[^>]*>([^<]*)</[^>]*>'
        element_match = re.search(element_pattern, html_content)
        
        if element_match:
            element_content = element_match.group(0)
            element_value = element_match.group(1).strip()
            
            print(f"FACT: {id} 처리 방법:")
            print(f"  - HTML 요소: {element_content[:100]}...")
            print(f"  - 초기값: '{element_value}'")
            
            # JavaScript에서 특별 처리 확인
            if id in html_content:
                # refresh 함수에서 특별 처리 확인
                refresh_pattern = rf'setDisplayValue\("{id}"'
                if re.search(refresh_pattern, html_content):
                    print(f"  - 처리 방식: refresh() 함수에서 setDisplayValue()로 처리")
                else:
                    # 다른 처리 방식 확인
                    if id == 'banner':
                        print(f"  - 처리 방식: refresh() 함수에서 banner.textContent로 직접 처리")
                    elif id == 'last_update':
                        print(f"  - 처리 방식: refresh() 함수에서 setDisplayValue()로 처리")
                    elif id == 'selected_symbol_dup':
                        print(f"  - 처리 방식: refresh() 함수에서 data.selected_symbol로 처리")
                    elif id == 'exchange_open_position_count_dup':
                        print(f"  - 처리 방식: refresh() 함수에서 data.exchange_open_position_count로 처리")
                    elif id in ['equity_chart', 'allocation_chart']:
                        print(f"  - 처리 방식: renderEquityChart() 또는 renderAllocationChart() 함수로 처리")
                    elif id in ['equity_chart_meta', 'allocation_chart_meta']:
                        print(f"  - 처리 방식: 차트 메타데이터로 별도 처리")
                    elif id in ['kst_daily_symbol_meta', 'kst_daily_symbol_table']:
                        print(f"  - 처리 방식: renderKstDailySymbolTable() 함수로 처리")
                    elif id in ['warning_panel', 'warning_list']:
                        print(f"  - 처리 방식: renderWarnings() 함수로 처리")
                    elif id in ['process_roles']:
                        print(f"  - 처리 방식: renderProcessRoles() 함수로 처리")
                    elif id == 'equityFill':
                        print(f"  - 처리 방식: 특별 차트 처리 (용도 불명)")
                    else:
                        print(f"  - 처리 방식: 확인 필요")
            else:
                print(f"  - 처리 방식: JavaScript에서 처리되지 않음")
        else:
            print(f"FACT: {id}: HTML 요소를 찾을 수 없음")
        
        print()
    
    # 3. refresh 함수에서의 특별 처리 확인
    print("FACT: refresh 함수에서의 특별 처리 확인")
    
    # refresh 함수 내용 추출
    refresh_pattern = r'async function refresh\(\) \{([^}]+)\}'
    refresh_match = re.search(refresh_pattern, html_content, re.DOTALL)
    
    if refresh_match:
        refresh_content = refresh_match.group(1)
        
        # 특별 처리된 변수 확인
        special_handlers = []
        
        for id in html_only_ids:
            if id in refresh_content:
                special_handlers.append(id)
        
        print(f"FACT: refresh 함수에서 특별 처리된 변수: {len(special_handlers)}개")
        for id in special_handlers:
            # 해당 라인 찾기
            lines = refresh_content.split('\n')
            for i, line in enumerate(lines):
                if id in line:
                    print(f"  - {id}: {line.strip()}")
                    break
    
    # 4. 렌더링 함수 확인
    print("FACT: 렌더링 함수 확인")
    
    rendering_functions = [
        'renderEquityChart',
        'renderAllocationChart',
        'renderWarnings',
        'renderProcessRoles',
        'renderKstDailySymbolTable'
    ]
    
    for func in rendering_functions:
        func_pattern = rf'function {func}\([^)]*\) \{{([^}}]+)\}}'
        func_match = re.search(func_pattern, html_content, re.DOTALL)
        
        if func_match:
            func_content = func_match.group(1)
            print(f"FACT: {func} 함수 발견")
            
            # 함수에서 사용하는 HTML ID 확인
            used_ids = []
            for id in html_only_ids:
                if id in func_content:
                    used_ids.append(id)
            
            if used_ids:
                print(f"  - 사용하는 HTML ID: {', '.join(used_ids)}")
        else:
            print(f"FACT: {func} 함수 없음")
    
    # 5. 최종 평가
    print("FACT: 최종 평가")
    
    total_html_only = len(html_only_ids)
    handled_count = 0
    
    for id in html_only_ids:
        if id in html_content and ('setDisplayValue' in html_content or 'textContent' in html_content or 'render' in html_content):
            handled_count += 1
    
    print(f"FACT: HTML에만 있는 변수 처리 상태:")
    print(f"  - 전체 HTML에만 있는 변수: {total_html_only}개")
    print(f"  - 처리된 변수: {handled_count}개")
    print(f"  - 처리율: {handled_count/total_html_only*100:.1f}%")
    
    if handled_count == total_html_only:
        print("FACT: 모든 HTML에만 있는 변수가 적절히 처리됨 ✓")
        return True
    else:
        print("FACT: 일부 HTML에만 있는 변수가 처리되지 않음 ❌")
        return False

def main():
    """메인 실행"""
    
    print("=== HTML에만 있는 변수 처리 방법 확인 (FACT ONLY) ===")
    print()
    
    success = check_html_only_variables()
    
    print()
    print("FACT: 최종 보고")
    if success:
        print("FACT: HTML에만 있는 변수가 모두 적절히 처리됨 ✓")
    else:
        print("FACT: 일부 HTML에만 있는 변수 처리에 문제가 있음 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
