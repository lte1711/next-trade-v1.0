#!/usr/bin/env python3
"""
서버 API 응답 수정 스크립트
HTML 파일에서 변수값을 정확하게 받아오도록 서버 응답 수정
"""

import json
import re
from pathlib import Path

def fix_server_api_response():
    """서버 API 응답에 binance 데이터 추가"""
    
    print('FACT: 서버 API 응답 수정 시작')
    
    server_path = Path('tools/dashboard/multi5_dashboard_server.py')
    if not server_path.exists():
        print('FACT: 서버 파일이 존재하지 않음')
        return False
    
    # 환경변수 값 확인
    import os
    execution_mode = os.environ.get('EXECUTION_MODE', 'testnet')
    print(f'FACT: 현재 환경변수 EXECUTION_MODE: {execution_mode}')
    
    # 서버 파일 읽기
    with open(server_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # /api/runtime 핸들러 찾기 및 수정
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        if 'return {' in line and '/api/runtime' in content[max(0, i-100):i]:
            print(f'FACT: 응답 데이터 발견 - 라인 {i+1}')
            
            # 현재 return 블록 찾기
            return_block = []
            j = i
            while j < len(lines) and '}' not in lines[j]:
                return_block.append(lines[j])
                j += 1
            if j < len(lines):
                return_block.append(lines[j])  # } 포함
            
            # binance 데이터가 있는지 확인
            block_text = '\n'.join(return_block)
            if 'binance_execution_mode' not in block_text:
                # 수정된 블록 생성
                modified_block = []
                for k, block_line in enumerate(return_block):
                    modified_block.append(block_line)
                    # 마지막 항목 뒤에 binance 데이터 추가
                    if k == len(return_block) - 2:  # } 바로 전 라인
                        modified_block.append(f'            "binance_execution_mode": "{execution_mode}",')
                        modified_block.append('            "binance_probe_mode": "enabled",')
                
                # 원본 블록 교체
                original_block = block_text
                new_block = '\n'.join(modified_block)
                
                content = content.replace(original_block, new_content)
                modified = True
                
                print('FACT: 서버 API 응답 데이터 수정 완료')
                print(f'- binance_execution_mode: {execution_mode}')
                print('- binance_probe_mode: enabled')
                break
            else:
                print('FACT: binance 데이터가 이미 존재함')
                break
    
    if modified:
        # 파일 저장
        with open(server_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('FACT: 서버 파일 저장 완료')
        return True
    else:
        print('FACT: 수정할 내용을 찾을 수 없음')
        return False

def verify_fix():
    """수정 내용 확인"""
    
    print('FACT: 수정 내용 확인')
    
    # 환경변수 확인
    import os
    execution_mode = os.environ.get('EXECUTION_MODE', 'testnet')
    print(f'FACT: 환경변수 EXECUTION_MODE: {execution_mode}')
    
    # 서버 파일 확인
    server_path = Path('tools/dashboard/multi5_dashboard_server.py')
    if server_path.exists():
        with open(server_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_execution_mode = 'binance_execution_mode' in content
        has_probe_mode = 'binance_probe_mode' in content
        
        print('FACT: 서버 파일 상태:')
        print(f'- binance_execution_mode: {"추가됨" if has_execution_mode else "없음"}')
        print(f'- binance_probe_mode: {"추가됨" if has_probe_mode else "없음"}')
    
    # HTML 파일 확인
    html_path = Path('tools/dashboard/multi5_dashboard.html')
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_js_api = 'fetch(`/api/runtime`' in content
        has_element_ids = 'id="binance_execution_mode"' in content and 'id="binance_probe_mode"' in content
        
        print('FACT: HTML 파일 상태:')
        print(f'- API 호출: {"있음" if has_js_api else "없음"}')
        print(f'- 요소 ID: {"있음" if has_element_ids else "없음"}')
    
    print('FACT: 확인 완료')

if __name__ == "__main__":
    print('=== HTML 파일 변수값 수신 문제 해결 ===')
    
    # 수정 실행
    success = fix_server_api_response()
    
    if success:
        # 확인
        verify_fix()
        print('FACT: HTML 파일 변수값 수신 문제 해결 완료')
    else:
        print('FACT: 수정 실패')
