#!/usr/bin/env python3
"""
멀티전략 시스템 성과 확인 (FACT ONLY)
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

def analyze_multi_strategy_performance():
    """멀티전략 시스템 성과 확인"""
    
    print("FACT: 멀티전략 시스템 성과 확인")
    
    # 1. 현재 API 데이터 가져오기
    try:
        import requests
        api_response = requests.get("http://127.0.0.1:8788/api/runtime", timeout=5)
        if api_response.status_code != 200:
            print("FACT: API 응답 실패")
            return False
        
        data = api_response.json()
        print("FACT: API 데이터 수신 성공")
        
    except Exception as e:
        print(f"FACT: API 호출 실패: {e}")
        return False
    
    # 2. 핵심 성과 지표 확인
    print("\nFACT: 핵심 성과 지표")
    
    # 손익 관련
    account_equity = data.get("account_equity", "0")
    realized_pnl = data.get("kpi_realized_pnl", "0")
    unrealized_pnl = data.get("unrealized_pnl_live", "0")
    total_exposure = data.get("total_exposure", "0")
    
    print(f"  - 계좌 자산: {account_equity} USDT")
    print(f"  - 실현 손익: {realized_pnl} USDT")
    print(f"  - 미실현 손익: {unrealized_pnl} USDT")
    print(f"  - 총 노출: {total_exposure} USDT")
    
    # 거래 관련
    total_trades = data.get("kpi_total_trades", 0)
    win_rate = data.get("kpi_win_rate", "0")
    drawdown = data.get("kpi_drawdown", "0")
    profit_factor = data.get("profit_factor", "0")
    
    print(f"  - 총 거래: {total_trades}건")
    print(f"  - 승률: {win_rate}%")
    print(f"  - 최대 낙폭: {drawdown}%")
    print(f"  - 수익 비율: {profit_factor}")
    
    # 3. 시스템 상태 확인
    print("\nFACT: 시스템 상태")
    
    engine_status = data.get("engine_status", "UNKNOWN")
    runtime_alive = data.get("runtime_alive", "false")
    active_symbols = data.get("active_symbols", [])
    exchange_open_position_count = data.get("exchange_open_position_count", 0)
    
    print(f"  - 엔진 상태: {engine_status}")
    print(f"  - 런타임: {runtime_alive}")
    print(f"  - 활성 심볼: {len(active_symbols)}개")
    print(f"  - 오픈 포지션: {exchange_open_position_count}개")
    
    # 4. 전략별 성과 확인
    print("\nFACT: 전략별 성과")
    
    # allocation_top에서 전략별 성과 확인
    allocation_top = data.get("allocation_top", [])
    if allocation_top:
        print(f"  - 상위 {len(allocation_top)}개 심볼 배분:")
        for i, allocation in enumerate(allocation_top[:5]):  # 상위 5개만
            symbol = allocation.get("symbol", "UNKNOWN")
            weight = allocation.get("weight", 0)
            score = allocation.get("score", 0)
            print(f"    {i+1}. {symbol}: 배분 {weight:.3f}, 점수 {score:.3f}")
    
    # 5. 일일 성과 확인
    print("\nFACT: 일일 성과")
    
    kst_daily_symbol_summary = data.get("kst_daily_symbol_summary", {})
    if kst_daily_symbol_summary:
        daily_invested = kst_daily_symbol_summary.get("total_invested_amount", 0)
        daily_realized_pnl = kst_daily_symbol_summary.get("total_realized_pnl", 0)
        daily_trade_count = kst_daily_symbol_summary.get("total_trade_count", 0)
        symbol_count = kst_daily_symbol_summary.get("symbol_count", 0)
        
        print(f"  - 일일 투자금: {daily_invested:.2f} USDT")
        print(f"  - 일일 실현 손익: {daily_realized_pnl:.2f} USDT")
        print(f"  - 일일 거래: {daily_trade_count}건")
        print(f"  - 거래 심볼: {symbol_count}개")
        
        # 일일 수익률 계산
        if daily_invested > 0:
            daily_return_pct = (daily_realized_pnl / daily_invested) * 100
            print(f"  - 일일 수익률: {daily_return_pct:.3f}%")
    
    # 6. KST 심볼별 상세 성과
    print("\nFACT: KST 심볼별 상세 성과")
    
    kst_daily_symbol_stats = data.get("kst_daily_symbol_stats", [])
    if kst_daily_symbol_stats:
        profitable_symbols = 0
        losing_symbols = 0
        
        for symbol_stat in kst_daily_symbol_stats:
            symbol = symbol_stat.get("symbol", "UNKNOWN")
            realized_pnl = symbol_stat.get("realized_pnl", 0)
            trade_count = symbol_stat.get("trade_count", 0)
            return_pct = symbol_stat.get("return_pct", 0)
            
            if realized_pnl > 0:
                profitable_symbols += 1
            elif realized_pnl < 0:
                losing_symbols += 1
        
        print(f"  - 수익 심볼: {profitable_symbols}개")
        print(f"  - 손실 심볼: {losing_symbols}개")
        print(f"  - 총 심볼: {len(kst_daily_symbol_stats)}개")
        
        # 상위 수익 심볼
        profitable_stats = [s for s in kst_daily_symbol_stats if s.get("realized_pnl", 0) > 0]
        if profitable_stats:
            profitable_stats.sort(key=lambda x: x.get("realized_pnl", 0), reverse=True)
            print(f"  - 상위 수익 심볼:")
            for i, stat in enumerate(profitable_stats[:3]):
                symbol = stat.get("symbol", "UNKNOWN")
                pnl = stat.get("realized_pnl", 0)
                return_pct = stat.get("return_pct", 0)
                print(f"    {i+1}. {symbol}: {pnl:.3f} USDT ({return_pct:.3f}%)")
    
    # 7. 시간 기준 성과 분석
    print("\nFACT: 시간 기준 성과 분석")
    
    # equity_history에서 성과 분석
    equity_history = data.get("equity_history", [])
    if equity_history:
        # 최근 1시간 데이터 분석
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        recent_equity = [e for e in equity_history if datetime.fromisoformat(e["ts"].replace('Z', '+00:00')) >= one_hour_ago]
        
        if len(recent_equity) >= 2:
            start_equity = recent_equity[0]["equity"]
            end_equity = recent_equity[-1]["equity"]
            
            try:
                start_val = float(start_equity)
                end_val = float(end_equity)
                hourly_return = ((end_val - start_val) / start_val) * 100
                
                print(f"  - 최근 1시간 수익률: {hourly_return:.3f}%")
                print(f"  - 시작 자산: {start_val:.2f} USDT")
                print(f"  - 종료 자산: {end_val:.2f} USDT")
            except (ValueError, ZeroDivisionError):
                print("  - 최근 1시간 수익률: 계산 불가")
    
    # 8. 위험 관리 상태
    print("\nFACT: 위험 관리 상태")
    
    global_kill_switch = data.get("global_kill_switch_state", "false")
    global_api_failures = data.get("global_api_failures", 0)
    global_engine_errors = data.get("global_engine_errors", 0)
    
    print(f"  - 글로벌 킬 스위치: {global_kill_switch}")
    print(f"  - API 실패: {global_api_failures}회")
    print(f"  - 엔진 오류: {global_engine_errors}회")
    
    # 9. 최종 성과 평가
    print("\nFACT: 최종 성과 평가")
    
    # 성과 지표 계산
    try:
        account_equity_val = float(account_equity)
        realized_pnl_val = float(realized_pnl)
        win_rate_val = float(win_rate)
        drawdown_val = float(drawdown)
        
        # 성과 등급 평가
        performance_score = 0
        
        # 손익 평가
        if realized_pnl_val > 0:
            performance_score += 1
            print("  - 손익 평가: 양수 (+1점)")
        else:
            print("  - 손익 평가: 음수 (0점)")
        
        # 승률 평가
        if win_rate_val > 50:
            performance_score += 1
            print("  - 승률 평가: 50% 초과 (+1점)")
        else:
            print("  - 승률 평가: 50% 이하 (0점)")
        
        # 낙폭 평가
        if drawdown_val < 5:
            performance_score += 1
            print("  - 낙폭 평가: 5% 미만 (+1점)")
        else:
            print("  - 낙폭 평가: 5% 이상 (0점)")
        
        # 시스템 안정성 평가
        if engine_status == "RUNNING" and runtime_alive == "true":
            performance_score += 1
            print("  - 시스템 안정성: 정상 (+1점)")
        else:
            print("  - 시스템 안정성: 비정상 (0점)")
        
        print(f"\n  - 총 성과 점수: {performance_score}/4")
        
        # 최종 평가
        if performance_score >= 3:
            print("  - 최종 평가: 우수")
            return True
        elif performance_score >= 2:
            print("  - 최종 평가: 양호")
            return True
        else:
            print("  - 최종 평가: 개선 필요")
            return False
            
    except (ValueError, TypeError):
        print("  - 성과 평가: 데이터 오류")
        return False

def main():
    """메인 실행"""
    
    print("=== 멀티전략 시스템 성과 확인 (FACT ONLY) ===")
    
    success = analyze_multi_strategy_performance()
    
    print("\nFACT: 최종 보고")
    if success:
        print("FACT: 멀티전략 시스템이 성과를 내고 있음 ✓")
    else:
        print("FACT: 멀티전략 시스템 성과 개선 필요 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
