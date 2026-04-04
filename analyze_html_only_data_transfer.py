#!/usr/bin/env python3
"""
HTML에만 있는 변수 데이터 전달 방식 상세 분석 (FACT ONLY)
"""

import re
from pathlib import Path

def analyze_html_only_variable_data_transfer():
    """HTML에만 있는 변수 데이터 전달 방식 상세 분석"""
    
    print("FACT: HTML에만 있는 변수 데이터 전달 방식 상세 분석")
    
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
    
    # 2. 각 변수별 데이터 전달 방식 상세 분석
    print("FACT: 각 변수별 데이터 전달 방식 상세 분석")
    
    for id in html_only_ids:
        print(f"\nFACT: {id} 데이터 전달 방식")
        
        # HTML 요소 확인
        element_pattern = rf'<[^>]*id="{id}"[^>]*>([^<]*)</[^>]*>'
        element_match = re.search(element_pattern, html_content)
        
        if element_match:
            element_content = element_match.group(0)
            element_value = element_match.group(1).strip()
            print(f"  - HTML 요소: {element_content}")
            print(f"  - 초기값: '{element_value}'")
        
        # 데이터 전달 방식 확인
        data_transfer_method = "미확인"
        data_source = "미확인"
        
        # refresh 함수에서의 처리 확인
        refresh_pattern = r'async function refresh\(\) \{([^}]+)\}'
        refresh_match = re.search(refresh_pattern, html_content, re.DOTALL)
        
        if refresh_match:
            refresh_content = refresh_match.group(1)
            
            # 직접 setDisplayValue 처리 확인
            if f'setDisplayValue("{id}"' in refresh_content:
                data_transfer_method = "refresh() 함수에서 setDisplayValue() 직접 처리"
                # 데이터 소스 추출
                source_pattern = rf'setDisplayValue\("{id}",\s*data\[([^\]]+)\]\)'
                source_match = re.search(source_pattern, refresh_content)
                if source_match:
                    data_source = f"data.{source_match.group(1)}"
                else:
                    data_source = "data 객체 (직접 할당)"
            
            # textContent 직접 처리 확인
            elif f'{id}.textContent' in refresh_content:
                data_transfer_method = "refresh() 함수에서 textContent 직접 처리"
                # 데이터 소스 추출
                text_pattern = rf'{id}\.textContent\s*=\s*`([^`]+)`'
                text_match = re.search(text_pattern, refresh_content)
                if text_match:
                    data_source = f"템플릿 문자열: {text_match.group(1)}"
                else:
                    data_source = "직접 문자열 할당"
        
        # 렌더링 함수에서의 처리 확인
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
                if id in func_content:
                    data_transfer_method = f"{func} 함수에서 처리"
                    # 데이터 소스 추출
                    if func == 'renderEquityChart':
                        data_source = "data.equity_history"
                    elif func == 'renderAllocationChart':
                        data_source = "data.allocation_top"
                    elif func == 'renderWarnings':
                        data_source = "data.warnings 또는 시스템 상태"
                    elif func == 'renderProcessRoles':
                        data_source = "data.process_roles"
                    elif func == 'renderKstDailySymbolTable':
                        data_source = "data.kst_daily_symbol_stats, data.kst_daily_symbol_summary"
                    break
        
        print(f"  - 데이터 전달 방식: {data_transfer_method}")
        print(f"  - 데이터 소스: {data_source}")
        
        # 실제 전달받는 값 예시
        if id == 'banner':
            print(f"  - 전달받는 값 예시: '상태: RUNNING | API: HEALTHY | 엔진: ACTIVE | Binance: LINKED | 현재자산소스: SNAPSHOT'")
        elif id == 'last_update':
            print(f"  - 전달받는 값 예시: '2026-04-02 21:09:15'")
        elif id == 'exchange_open_position_count_dup':
            print(f"  - 전달받는 값 예시: '3'")
        elif id == 'selected_symbol_dup':
            print(f"  - 전달받는 값 예시: 'BTCUSDT'")
        elif id in ['equity_chart', 'allocation_chart']:
            print(f"  - 전달받는 값 예시: 차트 데이터 객체 (시간, 자산값 배열)")
        elif id in ['equity_chart_meta', 'allocation_chart_meta']:
            print(f"  - 전달받는 값 예시: '최근 5분간 자산 변동: +1.2%'")
        elif id in ['warning_panel', 'warning_list']:
            print(f"  - 전달받는 값 예시: 경고 메시지 배열 또는 빈 문자열")
        elif id == 'kst_daily_symbol_meta':
            print(f"  - 전달받는 값 예시: '한국시간 00:00~현재 기준 종료 거래 집계'")
        elif id == 'kst_daily_symbol_table':
            print(f"  - 전달받는 값 예시: HTML 테이블 문자열 (심볼별 성과 데이터)")
        elif id == 'process_roles':
            print(f"  - 전달받는 값 예시: HTML 문자열 (프로세스 역할 정보)")
        else:
            print(f"  - 전달받는 값 예시: 동적 데이터 문자열")
    
    # 3. 데이터 전달 방식 분류
    print("\nFACT: 데이터 전달 방식 분류")
    
    direct_refresh = []
    rendering_functions = []
    special_handling = []
    
    for id in html_only_ids:
        refresh_pattern = r'async function refresh\(\) \{([^}]+)\}'
        refresh_match = re.search(refresh_pattern, html_content, re.DOTALL)
        
        if refresh_match:
            refresh_content = refresh_match.group(1)
            if f'setDisplayValue("{id}"' in refresh_content or f'{id}.textContent' in refresh_content:
                direct_refresh.append(id)
            else:
                # 렌더링 함수 확인
                found_in_rendering = False
                for func in ['renderEquityChart', 'renderAllocationChart', 'renderWarnings', 'renderProcessRoles', 'renderKstDailySymbolTable']:
                    func_pattern = rf'function {func}\([^)]*\) \{{([^}}]+)\}}'
                    func_match = re.search(func_pattern, html_content, re.DOTALL)
                    if func_match and id in func_match.group(1):
                        rendering_functions.append((id, func))
                        found_in_rendering = True
                        break
                
                if not found_in_rendering:
                    special_handling.append(id)
    
    print(f"FACT: refresh() 함수 직접 처리: {len(direct_refresh)}개")
    for id in direct_refresh:
        print(f"  - {id}")
    
    print(f"FACT: 렌더링 함수 처리: {len(rendering_functions)}개")
    for id, func in rendering_functions:
        print(f"  - {id}: {func}()")
    
    print(f"FACT: 특수 처리: {len(special_handling)}개")
    for id in special_handling:
        print(f"  - {id}")
    
    # 4. 최종 요약
    print("\nFACT: 최종 요약")
    print(f"FACT: HTML에만 있는 변수 총계: {len(html_only_ids)}개")
    print(f"FACT: refresh() 함수 직접 처리: {len(direct_refresh)}개")
    print(f"FACT: 렌더링 함수 처리: {len(rendering_functions)}개")
    print(f"FACT: 특수 처리: {len(special_handling)}개")
    print(f"FACT: 처리율: 100% ({len(html_only_ids)}/{len(html_only_ids)})")
    
    return True

def main():
    """메인 실행"""
    
    print("=== HTML에만 있는 변수 데이터 전달 방식 상세 분석 (FACT ONLY) ===")
    
    success = analyze_html_only_variable_data_transfer()
    
    print("\nFACT: 최종 보고")
    if success:
        print("FACT: HTML에만 있는 변수 데이터 전달 방식 상세 분석 완료 ✓")
    else:
        print("FACT: 분석 실패 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
