#!/usr/bin/env python3
"""
HTML 모든 변수 데이터 전달 정밀 분석 스크립트
"""

import re
from pathlib import Path

def analyze_html_variables():
    """HTML 모든 변수 분석"""
    
    print("FACT: HTML 모든 변수 데이터 전달 정밀 분석")
    
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if not html_path.exists():
        print("FACT: HTML 파일이 존재하지 않음")
        return
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 모든 id 속성 찾기
    id_pattern = r'id="([^"]+)"'
    all_ids = re.findall(id_pattern, content)
    unique_ids = sorted(list(set(all_ids)))
    
    print(f"FACT: HTML에서 발견된 모든 ID: {len(unique_ids)}개")
    
    # 카테고리별 분류
    binance_ids = [id for id in unique_ids if 'binance' in id.lower()]
    runtime_ids = [id for id in unique_ids if any(x in id.lower() for x in ['runtime', 'engine', 'status'])]
    symbol_ids = [id for id in unique_ids if 'symbol' in id.lower()]
    portfolio_ids = [id for id in unique_ids if any(x in id.lower() for x in ['equity', 'balance', 'profit'])]
    
    print(f"FACT: 바이낸스 관련: {len(binance_ids)}개")
    for id in binance_ids:
        print(f"  - {id}")
    
    print(f"FACT: 런타임 관련: {len(runtime_ids)}개")
    for id in runtime_ids[:5]:
        print(f"  - {id}")
    if len(runtime_ids) > 5:
        print(f"  - ... 외 {len(runtime_ids)-5}개")
    
    print(f"FACT: 심볼 관련: {len(symbol_ids)}개")
    for id in symbol_ids[:5]:
        print(f"  - {id}")
    if len(symbol_ids) > 5:
        print(f"  - ... 외 {len(symbol_ids)-5}개")
    
    print(f"FACT: 포트폴리오 관련: {len(portfolio_ids)}개")
    for id in portfolio_ids:
        print(f"  - {id}")
    
    return unique_ids

def analyze_javascript_ids():
    """JavaScript ids 배열 분석"""
    
    print("FACT: JavaScript ids 배열 확인")
    
    html_path = Path("tools/dashboard/multi5_dashboard.html")
    if not html_path.exists():
        print("FACT: HTML 파일이 존재하지 않음")
        return []
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # JavaScript ids 배열 찾기
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'const ids' in line and '[' in line:
            print(f"FACT: JavaScript ids 배열 발견 - 라인 {i+1}")
            
            # 배열 내용 추출
            array_content = line
            j = i + 1
            while j < len(lines) and ']' not in array_content:
                array_content += ' ' + lines[j]
                j += 1
            
            # 따옴표 안의 ID 추출
            id_pattern = r'["\']([^"\']+)["\']'
            id_list = re.findall(id_pattern, array_content)
            
            print(f"FACT: JavaScript ids 배열 항목: {len(id_list)}개")
            for id in id_list:
                print(f"  - {id}")
            
            return id_list
    
    print("FACT: JavaScript ids 배열을 찾을 수 없음")
    return []

def analyze_server_response():
    """서버 응답 데이터 분석"""
    
    print("FACT: 서버 응답 데이터 확인")
    
    server_path = Path("tools/dashboard/multi5_dashboard_server.py")
    if not server_path.exists():
        print("FACT: 서버 파일이 존재하지 않음")
        return []
    
    with open(server_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # return 문에서 데이터 키 찾기
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'return {' in line:
            print(f"FACT: 서버 응답 데이터 발견 - 라인 {i+1}")
            
            # return 블록 내용 추출
            return_block = []
            j = i
            while j < len(lines) and '}' not in lines[j]:
                return_block.append(lines[j])
                j += 1
            if j < len(lines):
                return_block.append(lines[j])  # } 포함
            
            block_text = '\n'.join(return_block)
            
            # 키-값 쌍 추출
            key_pattern = r'"([^"]+)"'
            keys = re.findall(key_pattern, block_text)
            
            print(f"FACT: 서버 응답 키: {len(keys)}개")
            for key in keys:
                print(f"  - {key}")
            
            return keys
    
    print("FACT: 서버 응답 데이터를 찾을 수 없음")
    return []

def analyze_mapping():
    """데이터 매핑 분석"""
    
    print("FACT: 데이터 매핑 분석")
    
    # HTML ids 배열
    html_ids = analyze_javascript_ids()
    
    # 서버 응답 키
    server_keys = analyze_server_response()
    
    # 매핑 분석
    print(f"FACT: HTML ids 배열: {len(html_ids)}개")
    print(f"FACT: 서버 응답 키: {len(server_keys)}개")
    
    matched = []
    unmatched_html = []
    unmatched_server = []
    
    for id in html_ids:
        if id in server_keys:
            matched.append(id)
        else:
            unmatched_html.append(id)
    
    for key in server_keys:
        if key not in html_ids:
            unmatched_server.append(key)
    
    print(f"FACT: 매핑 분석 결과:")
    print(f"  - 정상 매핑: {len(matched)}개")
    for id in matched[:10]:
        print(f"    ✓ {id}")
    if len(matched) > 10:
        print(f"    ... 외 {len(matched)-10}개")
    
    print(f"  - HTML에만 있음: {len(unmatched_html)}개")
    for id in unmatched_html:
        print(f"    ❌ {id}")
    
    print(f"  - 서버에만 있음: {len(unmatched_server)}개")
    for key in unmatched_server:
        print(f"    ⚠️ {key}")
    
    return matched, unmatched_html, unmatched_server

def main():
    """메인 분석 실행"""
    
    print("=== HTML 모든 변수 데이터 전달 정밀 분석 (FACT ONLY) ===")
    print()
    
    # 1. HTML 모든 변수 확인
    all_ids = analyze_html_variables()
    print()
    
    # 2. JavaScript ids 배열 확인
    js_ids = analyze_javascript_ids()
    print()
    
    # 3. 서버 응답 데이터 확인
    server_keys = analyze_server_response()
    print()
    
    # 4. 매핑 분석
    matched, unmatched_html, unmatched_server = analyze_mapping()
    print()
    
    # 5. 문제 식별
    print("FACT: 데이터 전달 문제 식별")
    print(f"  - 총 HTML ID: {len(all_ids)}개")
    print(f"  - JavaScript 배열: {len(js_ids)}개")
    print(f"  - 서버 응답: {len(server_keys)}개")
    print(f"  - 정상 매핑: {len(matched)}개")
    print(f"  - 문제 ID: {len(unmatched_html)}개")
    print(f"  - 미사용 키: {len(unmatched_server)}개")
    
    if unmatched_html:
        print()
        print("FACT: 해결 필요한 문제:")
        print("  - HTML에 있지만 서버 응답에 없는 ID가 있음")
        print("  - 서버 응답에 해당 키를 추가해야 함")
    
    print()
    print("FACT: 분석 완료")

if __name__ == "__main__":
    main()
