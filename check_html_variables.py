#!/usr/bin/env python3
"""
HTML 모든 변수 데이터 전달 확인 스크립트 (FACT ONLY)
"""

import re
from pathlib import Path

def check_html_variable_data_transfer():
    """HTML 모든 변수 데이터 전달 확인"""
    
    print("FACT: HTML 모든 변수 데이터 전달 확인 시작")
    
    # 1. HTML 변수 목록 확인
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if not html_path.exists():
        print("FACT: HTML 파일이 존재하지 않음")
        return False
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # JavaScript ids 배열 추출
    lines = html_content.split('\n')
    html_ids = []
    
    for i, line in enumerate(lines):
        if 'const ids' in line and '[' in line:
            array_content = line
            j = i + 1
            while j < len(lines) and ']' not in array_content:
                array_content += ' ' + lines[j]
                j += 1
            
            id_pattern = r'["\']([^"\']+)["\']'
            html_ids = re.findall(id_pattern, array_content)
            break
    
    print(f"FACT: HTML JavaScript ids 배열: {len(html_ids)}개")
    for id in html_ids:
        print(f"  - {id}")
    
    # 2. 서버 응답 데이터 확인
    server_path = Path("tools/dashboard/multi5_dashboard_server.py")
    if not server_path.exists():
        print("FACT: 서버 파일이 존재하지 않음")
        return False
    
    with open(server_path, 'r', encoding='utf-8') as f:
        server_content = f.read()
    
    # return 블록에서 키 추출
    lines = server_content.split('\n')
    server_keys = []
    
    for i, line in enumerate(lines):
        if 'return {' in line:
            return_block = []
            j = i
            while j < len(lines) and '}' not in lines[j]:
                return_block.append(lines[j])
                j += 1
            if j < len(lines):
                return_block.append(lines[j])
            
            block_text = '\n'.join(return_block)
            key_pattern = r'"([^"]+)"'
            server_keys = re.findall(key_pattern, block_text)
            break
    
    print(f"FACT: 서버 응답 키: {len(server_keys)}개")
    for key in server_keys:
        print(f"  - {key}")
    
    # 3. 데이터 전달 매핑 확인
    print("FACT: 데이터 전달 매핑 확인")
    
    matched = []
    unmatched_html = []
    missing_server = []
    
    for id in html_ids:
        if id in server_keys:
            matched.append(id)
        else:
            unmatched_html.append(id)
    
    for key in server_keys:
        if key not in html_ids:
            missing_server.append(key)
    
    print(f"FACT: 매핑 분석 결과:")
    print(f"  - 정상 매핑: {len(matched)}개")
    for id in matched:
        print(f"    ✓ {id}")
    
    print(f"  - HTML에만 있음: {len(unmatched_html)}개")
    for id in unmatched_html:
        print(f"    ❌ {id}")
    
    print(f"  - 서버에만 있음: {len(missing_server)}개")
    for key in missing_server:
        print(f"    ⚠️ {key}")
    
    # 4. 데이터 전달 상태 평가
    print("FACT: 데이터 전달 상태 평가")
    
    total_html = len(html_ids)
    total_server = len(server_keys)
    matched_count = len(matched)
    
    if matched_count == total_html:
        print("FACT: 모든 HTML 변수가 서버에서 데이터를 수신함 ✓")
        status = "완전"
    elif matched_count > total_html * 0.8:
        print("FACT: 대부분의 HTML 변수가 서버에서 데이터를 수신함 ⚠️")
        status = "부분"
    else:
        print("FACT: 대부분의 HTML 변수가 서버에서 데이터를 수신하지 못함 ❌")
        status = "미흡"
    
    print(f"FACT: 데이터 전달 상태: {status}")
    print(f"FACT: 전달율: {matched_count}/{total_html} ({matched_count/total_html*100:.1f}%)")
    
    # 5. 주요 변수 상세 확인
    print("FACT: 주요 변수 상세 확인")
    
    important_variables = [
        'binance_execution_mode',
        'binance_probe_mode',
        'account_equity',
        'engine_status',
        'runtime_alive'
    ]
    
    for var in important_variables:
        if var in matched:
            print(f"  ✓ {var}: 정상 전달")
        elif var in unmatched_html:
            print(f"  ❌ {var}: 서버 응답 없음")
        else:
            print(f"  ⚠️ {var}: HTML에 없음")
    
    return matched_count == total_html

def main():
    """메인 실행"""
    
    print("=== HTML 모든 변수 데이터 전달 확인 (FACT ONLY) ===")
    print()
    
    success = check_html_variable_data_transfer()
    
    print()
    print("FACT: 최종 보고")
    if success:
        print("FACT: 모든 HTML 변수가 정상적으로 데이터를 전달받음 ✓")
    else:
        print("FACT: 일부 HTML 변수가 데이터를 전달받지 못함 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
