#!/usr/bin/env python3
"""
HTML 파일 직접 확인하여 변수 데이터 전달 상태 확인 (FACT ONLY)
"""

import re
from pathlib import Path

def check_html_file_variables():
    """HTML 파일 직접 확인하여 변수 데이터 전달 상태 확인"""
    
    print("FACT: HTML 파일 직접 확인하여 변수 데이터 전달 상태 확인")
    
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if not html_path.exists():
        print("FACT: HTML 파일이 존재하지 않음")
        return False
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"FACT: HTML 파일 크기: {len(html_content)} 문자")
    
    # 1. HTML에 정의된 모든 ID 확인
    id_pattern = r'id="([^"]+)"'
    all_html_ids = re.findall(id_pattern, html_content)
    unique_html_ids = sorted(list(set(all_html_ids)))
    
    print(f"FACT: HTML에 정의된 모든 ID: {len(unique_html_ids)}개")
    for id in unique_html_ids:
        print(f"  - {id}")
    
    # 2. JavaScript ids 배열 확인
    lines = html_content.split('\n')
    js_ids = []
    
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
    
    print(f"FACT: JavaScript ids 배열: {len(js_ids)}개")
    for id in js_ids:
        print(f"  - {id}")
    
    # 3. HTML 요소와 JavaScript 배열 매핑 확인
    print("FACT: HTML 요소와 JavaScript 배열 매핑 확인")
    
    matched_elements = []
    unmatched_elements = []
    missing_in_js = []
    
    for id in unique_html_ids:
        if id in js_ids:
            matched_elements.append(id)
        else:
            missing_in_js.append(id)
    
    for id in js_ids:
        if id in unique_html_ids:
            matched_elements.append(id)
        else:
            unmatched_elements.append(id)
    
    matched_elements = list(set(matched_elements))
    
    print(f"FACT: 매핑 분석 결과:")
    print(f"  - 정상 매핑: {len(matched_elements)}개")
    for id in matched_elements:
        print(f"    ✓ {id}")
    
    print(f"  - HTML에만 있음: {len(missing_in_js)}개")
    for id in missing_in_js:
        print(f"    ⚠️ {id}")
    
    print(f"  - JavaScript에만 있음: {len(unmatched_elements)}개")
    for id in unmatched_elements:
        print(f"    ❌ {id}")
    
    # 4. 데이터 전달 로직 확인
    print("FACT: 데이터 전달 로직 확인")
    
    # refresh 함수 확인
    if 'async function refresh()' in html_content:
        print("FACT: refresh() 함수 발견 ✓")
        
        # API 호출 확인
        if 'fetch(`/api/runtime`' in html_content:
            print("FACT: /api/runtime API 호출 발견 ✓")
        else:
            print("FACT: /api/runtime API 호출 없음 ❌")
        
        # 데이터 처리 확인
        if 'for (const id of ids) setDisplayValue(id, data[id])' in html_content:
            print("FACT: 데이터 처리 로직 발견 ✓")
        else:
            print("FACT: 데이터 처리 로직 없음 ❌")
        
        # 자동 새로고침 확인
        if 'setInterval(refresh, 3000)' in html_content:
            print("FACT: 3초 자동 새로고침 발견 ✓")
        else:
            print("FACT: 자동 새로고침 없음 ❌")
    else:
        print("FACT: refresh() 함수 없음 ❌")
    
    # 5. 특정 변수 상태 확인
    print("FACT: 특정 변수 상태 확인")
    
    important_variables = [
        'binance_execution_mode',
        'binance_probe_mode',
        'account_equity',
        'engine_status',
        'runtime_alive'
    ]
    
    for var in important_variables:
        # HTML 요소 확인
        html_element = f'id="{var}"' in html_content
        
        # JavaScript 배열 확인
        js_array = var in js_ids
        
        if html_element and js_array:
            print(f"  ✓ {var}: HTML 요소 및 JS 배열 모두 있음")
        elif html_element:
            print(f"  ⚠️ {var}: HTML 요소만 있음 (JS 배열 없음)")
        elif js_array:
            print(f"  ⚠️ {var}: JS 배열만 있음 (HTML 요소 없음)")
        else:
            print(f"  ❌ {var}: HTML 요소 및 JS 배열 모두 없음")
    
    # 6. 초기값 확인
    print("FACT: 초기값 확인")
    
    # 모든 data 클래스 요소의 초기값 확인
    data_pattern = r'<div[^>]*class="data"[^>]*id="([^"]+)"[^>]*>([^<]*)</div>'
    data_elements = re.findall(data_pattern, html_content)
    
    print(f"FACT: data 클래스 요소 초기값: {len(data_elements)}개")
    for id, value in data_elements:
        print(f"  - {id}: '{value.strip()}'")
    
    # 7. 최종 평가
    print("FACT: 최종 평가")
    
    total_html_elements = len(unique_html_ids)
    total_js_ids = len(js_ids)
    matched_count = len(matched_elements)
    
    if matched_count == total_js_ids:
        print("FACT: 모든 JavaScript ID가 HTML 요소에 매핑됨 ✓")
        status = "완전"
    elif matched_count > total_js_ids * 0.8:
        print("FACT: 대부분의 JavaScript ID가 HTML 요소에 매핑됨 ⚠️")
        status = "부분"
    else:
        print("FACT: 대부분의 JavaScript ID가 HTML 요소에 매핑되지 않음 ❌")
        status = "미흡"
    
    print(f"FACT: HTML 변수 데이터 전달 상태: {status}")
    print(f"FACT: 매핑율: {matched_count}/{total_js_ids} ({matched_count/total_js_ids*100:.1f}%)")
    
    return matched_count == total_js_ids

def main():
    """메인 실행"""
    
    print("=== HTML 파일 직접 확인하여 변수 데이터 전달 상태 확인 (FACT ONLY) ===")
    print()
    
    success = check_html_file_variables()
    
    print()
    print("FACT: 최종 보고")
    if success:
        print("FACT: HTML 파일의 모든 변수가 정상적으로 구성됨 ✓")
    else:
        print("FACT: HTML 파일의 일부 변수에 문제가 있음 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
