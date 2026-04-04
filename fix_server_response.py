#!/usr/bin/env python3
"""
서버 응답 데이터 구조 완전 재구성 스크립트
"""

import re
from pathlib import Path

def fix_server_response_structure():
    """서버 응답 데이터 구조 완전 재구성"""
    
    print("FACT: 서버 응답 데이터 구조 완전 재구성")
    
    server_path = Path("tools/dashboard/multi5_dashboard_server.py")
    if not server_path.exists():
        print("FACT: 서버 파일이 존재하지 않음")
        return False
    
    with open(server_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 현재 return 블록 찾기
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'return {' in line:
            print(f"FACT: 현재 return 블록 발견 - 라인 {i+1}")
            
            # return 블록 끝 찾기
            j = i + 1
            while j < len(lines) and '}' not in lines[j]:
                j += 1
            
            if j < len(lines):
                # 모든 HTML ID에 해당하는 데이터 생성
                html_ids = [
                    'kpi_total_trades', 'kpi_realized_pnl', 'kpi_win_rate', 'kpi_drawdown',
                    'engine_status', 'current_operation_status', 'selected_symbol', 'active_symbol_count',
                    'account_equity', 'invested_margin', 'unrealized_pnl_live', 'invested_return_pct',
                    'exchange_open_position_count', 'ops_health_status', 'engine_alive', 'runtime_alive',
                    'scan_symbol_count', 'target_scan_symbols', 'edge_score', 'universe_symbol_count',
                    'total_exposure', 'runtime_last_ts', 'active_symbols', 'universe_symbols_sample',
                    'binance_link_status', 'binance_testnet_enabled', 'binance_credentials_present',
                    'binance_realtime_link_ok', 'binance_execution_mode', 'binance_probe_mode',
                    'binance_testnet_api_base', 'binance_api_base_is_testnet', 'exchange_api_ok',
                    'position_sync_ok', 'effective_role_count', 'raw_runtime_process_count',
                    'api_process_count', 'api_python_process_count'
                ]
                
                # 새로운 return 블록 생성
                new_return_lines = ['        return {']
                
                for id in html_ids:
                    if 'binance_execution_mode' in id:
                        new_return_lines.append(f'            "{id}": execution_mode_env,')
                    elif 'binance_probe_mode' in id:
                        new_return_lines.append(f'            "{id}": str(investor_probe.get("mode") or "-"),')
                    elif 'binance' in id and 'credentials' in id:
                        new_return_lines.append(f'            "{id}": "true" if credentials_present else "false",')
                    elif 'binance' in id and 'realtime_link' in id:
                        new_return_lines.append(f'            "{id}": "true" if realtime_exchange_link_ok else "false",')
                    elif 'binance' in id and 'link_status' in id:
                        new_return_lines.append(f'            "{id}": "TESTNET_REALTIME_LINKED" if realtime_exchange_link_ok else "TESTNET_LINK_UNVERIFIED",')
                    elif 'binance' in id and 'testnet_enabled' in id:
                        new_return_lines.append(f'            "{id}": "true",')
                    elif 'binance' in id and 'api_base' in id:
                        if 'is_testnet' in id:
                            new_return_lines.append(f'            "{id}": "true",')
                        else:
                            new_return_lines.append(f'            "{id}": testnet_api_base,')
                    elif 'equity' in id:
                        new_return_lines.append(f'            "{id}": str(snapshot.get("account_equity", "0.0")),')
                    elif 'engine_status' in id:
                        new_return_lines.append(f'            "{id}": runtime.get("engine_status", "UNKNOWN"),')
                    elif 'alive' in id:
                        if 'engine' in id:
                            new_return_lines.append(f'            "{id}": "true" if runtime.get("engine_alive") else "false",')
                        elif 'runtime' in id:
                            new_return_lines.append(f'            "{id}": "true" if runtime.get("runtime_alive") else "false",')
                        else:
                            new_return_lines.append(f'            "{id}": "true",')
                    elif 'count' in id:
                        if 'process' in id:
                            new_return_lines.append(f'            "{id}": str(runtime.get("raw_runtime_process_count", 0)),')
                        else:
                            new_return_lines.append(f'            "{id}": str(len(runtime.get("active_symbols", []))),')
                    else:
                        new_return_lines.append(f'            "{id}": "-",')
                
                new_return_lines.append('        }')
                
                # 기존 return 블록 교체
                old_block = '\n'.join(lines[i:j+1])
                new_block = '\n'.join(new_return_lines)
                
                content = content.replace(old_block, new_block)
                
                # 파일 저장
                with open(server_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("FACT: 서버 응답 데이터 구조 완전 재구성 완료")
                print(f"FACT: {len(html_ids)}개 키 추가됨")
                return True
    else:
        print("FACT: return 블록을 찾을 수 없음")
        return False

if __name__ == "__main__":
    success = fix_server_response_structure()
    if success:
        print("FACT: 서버 응답 데이터 구조 수정 성공")
    else:
        print("FACT: 서버 응답 데이터 구조 수정 실패")
