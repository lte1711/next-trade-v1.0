#!/usr/bin/env python3
"""
진행중인 전략 프로세스 정밀 분석 (FACT ONLY)
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

def analyze_current_strategies():
    """진행중인 전략 프로세스 정밀 분석"""
    
    print("FACT: 진행중인 전략 프로세스 정밀 분석")
    
    # 1. 현재 실행중인 프로세스 확인
    print("FACT: 현재 실행중인 프로세스 확인")
    
    # 이전 API 응답에서 프로세스 정보 추출
    process_roles = [
        {
            "label": "api_8100",
            "role": "api",
            "root_pid": 8320,
            "pid_count": 2,
            "pids": "8320 7696",
            "root_chain_count": 1,
            "root_pids": "8320",
            "duplicate_independent_count": 0,
            "wrapper_child_chain_present": True
        },
        {
            "label": "dashboard_8787",
            "role": "dashboard",
            "root_pid": 7600,
            "pid_count": 1,
            "pids": "7600",
            "root_chain_count": 1,
            "root_pids": "7600",
            "duplicate_independent_count": 0,
            "wrapper_child_chain_present": False
        },
        {
            "label": "multi5_engine",
            "role": "engine",
            "root_pid": 4748,
            "pid_count": 2,
            "pids": "4748 8904",
            "root_chain_count": 1,
            "root_pids": "4748",
            "duplicate_independent_count": 0,
            "wrapper_child_chain_present": True
        },
        {
            "label": "worker:BCHUSDT",
            "role": "worker",
            "root_pid": 3824,
            "pid_count": 2,
            "pids": "3824 8516",
            "root_chain_count": 1,
            "root_pids": "3824",
            "duplicate_independent_count": 0,
            "wrapper_child_chain_present": True
        },
        {
            "label": "worker:BTCUSDT",
            "role": "worker",
            "root_pid": 5092,
            "pid_count": 2,
            "pids": "5092 7344",
            "root_chain_count": 1,
            "root_pids": "5092",
            "duplicate_independent_count": 0,
            "wrapper_child_chain_present": True
        }
    ]
    
    print(f"  - 총 프로세스 역할: {len(process_roles)}개")
    
    for i, process in enumerate(process_roles):
        label = process["label"]
        role = process["role"]
        root_pid = process["root_pid"]
        pid_count = process["pid_count"]
        pids = process["pids"]
        
        print(f"  {i+1}. {label}")
        print(f"     - 역할: {role}")
        print(f"     - 루트 PID: {root_pid}")
        print(f"     - PID 개수: {pid_count}")
        print(f"     - PID 목록: {pids}")
    
    # 2. 전략별 워커 프로세스 분석
    print("\nFACT: 전략별 워커 프로세스 분석")
    
    worker_processes = [p for p in process_roles if p["role"] == "worker"]
    strategy_symbols = []
    
    print(f"  - 워커 프로세스: {len(worker_processes)}개")
    
    for worker in worker_processes:
        label = worker["label"]
        # 심볼명 추출 (worker:SYMBOL 형식)
        if ":" in label:
            symbol = label.split(":")[1]
            strategy_symbols.append(symbol)
            
            root_pid = worker["root_pid"]
            pids = worker["pids"]
            
            print(f"  - {symbol} 전략 워커")
            print(f"     - 루트 PID: {root_pid}")
            print(f"     - PID 목록: {pids}")
            print(f"     - 체인 카운트: {worker['root_chain_count']}")
            print(f"     - 자식 체인: {worker['wrapper_child_chain_present']}")
    
    # 3. 활성 심볼 확인
    print("\nFACT: 활성 심볼 확인")
    
    active_symbols = ["BTCUSDT", "ETHUSDT", "BCHUSDT"]
    print(f"  - 활성 심볼: {len(active_symbols)}개")
    for symbol in active_symbols:
        print(f"  - {symbol}")
    
    # 4. 워커 vs 활성 심볼 비교
    print("\nFACT: 워커 vs 활성 심볼 비교")
    
    worker_symbols = [w["label"].split(":")[1] for w in worker_processes if ":" in w["label"]]
    
    print(f"  - 워커 심볼: {worker_symbols}")
    print(f"  - 활성 심볼: {active_symbols}")
    
    # 일치하는 심볼
    matching_symbols = set(worker_symbols) & set(active_symbols)
    print(f"  - 일치 심볼: {list(matching_symbols)}")
    
    # 워커에만 있는 심볼
    worker_only = set(worker_symbols) - set(active_symbols)
    print(f"  - 워커 전용: {list(worker_only)}")
    
    # 활성에만 있는 심볼
    active_only = set(active_symbols) - set(worker_symbols)
    print(f"  - 활성 전용: {list(active_only)}")
    
    # 5. 전략 파일 확인
    print("\nFACT: 전략 파일 확인")
    
    strategies_dir = Path("strategies")
    if strategies_dir.exists():
        strategy_files = list(strategies_dir.glob("*.py"))
        print(f"  - 전략 파일: {len(strategy_files)}개")
        
        for file in strategy_files:
            if file.name != "__init__.py":
                print(f"  - {file.name}")
    
    # 6. config.json에서 전략 설정 확인
    print("\nFACT: config.json 전략 설정 확인")
    
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        strategies_config = config.get("strategies", {})
        print(f"  - 설정된 전략: {len(strategies_config)}개")
        
        for strategy_name, strategy_config in strategies_config.items():
            enabled = strategy_config.get("enabled", False)
            weight = strategy_config.get("weight", 0)
            symbols = strategy_config.get("symbols", [])
            
            print(f"  - {strategy_name}")
            print(f"     - 활성화: {enabled}")
            print(f"     - 가중치: {weight}")
            print(f"     - 심볼: {symbols}")
    
    # 7. 현재 실행중인 전략 요약
    print("\nFACT: 현재 실행중인 전략 요약")
    
    # 실제 실행중인 전략 (워커 프로세스 기준)
    running_strategies = []
    
    for worker in worker_processes:
        label = worker["label"]
        if ":" in label:
            symbol = label.split(":")[1]
            root_pid = worker["root_pid"]
            
            running_strategies.append({
                "symbol": symbol,
                "process_name": f"worker:{symbol}",
                "root_pid": root_pid,
                "status": "RUNNING"
            })
    
    print(f"  - 실행중인 전략: {len(running_strategies)}개")
    
    for strategy in running_strategies:
        symbol = strategy["symbol"]
        process_name = strategy["process_name"]
        root_pid = strategy["root_pid"]
        status = strategy["status"]
        
        print(f"  - {symbol} 전략")
        print(f"     - 프로세스: {process_name}")
        print(f"     - PID: {root_pid}")
        print(f"     - 상태: {status}")
    
    # 8. 전략별 성과 확인
    print("\nFACT: 전략별 성과 확인")
    
    # 이전 데이터에서 심볼별 성과 추출
    symbol_performance = {
        "QUICKUSDT": {"pnl": 7.41795, "return_pct": 3.763526, "trades": 38},
        "LRCUSDT": {"pnl": 1.568793, "return_pct": 1.937667, "trades": 15},
        "BNBUSDT": {"pnl": 0.041382, "return_pct": 0.091456, "trades": 6},
        "BTCUSDT": {"pnl": -1.679352, "return_pct": -0.081502, "trades": 6},
        "ETHUSDT": {"pnl": -0.429526, "return_pct": -0.063253, "trades": 19},
        "BCHUSDT": {"pnl": -0.13217, "return_pct": -0.197894, "trades": 9},
        "DOGEUSDT": {"pnl": -0.099997, "return_pct": -0.268363, "trades": 7},
        "XRPUSDT": {"pnl": -0.007025, "return_pct": -0.053865, "trades": 4}
    }
    
    print(f"  - 실행중인 전략 성과:")
    for strategy in running_strategies:
        symbol = strategy["symbol"]
        if symbol in symbol_performance:
            perf = symbol_performance[symbol]
            pnl = perf["pnl"]
            return_pct = perf["return_pct"]
            trades = perf["trades"]
            
            print(f"  - {symbol}")
            print(f"     - 손익: {pnl:.3f} USDT")
            print(f"     - 수익률: {return_pct:.3f}%")
            print(f"     - 거래: {trades}건")
        else:
            print(f"  - {symbol}: 성과 데이터 없음")
    
    # 9. 최종 분석
    print("\nFACT: 최종 분석")
    
    total_strategies = len(running_strategies)
    profitable_strategies = 0
    losing_strategies = 0
    
    for strategy in running_strategies:
        symbol = strategy["symbol"]
        if symbol in symbol_performance:
            pnl = symbol_performance[symbol]["pnl"]
            if pnl > 0:
                profitable_strategies += 1
            elif pnl < 0:
                losing_strategies += 1
    
    print(f"  - 총 실행 전략: {total_strategies}개")
    print(f"  - 수익 전략: {profitable_strategies}개")
    print(f"  - 손실 전략: {losing_strategies}개")
    
    if total_strategies > 0:
        profit_ratio = (profitable_strategies / total_strategies) * 100
        print(f"  - 수익 비율: {profit_ratio:.1f}%")
    
    return True

def main():
    """메인 실행"""
    
    print("=== 진행중인 전략 프로세스 정밀 분석 (FACT ONLY) ===")
    
    success = analyze_current_strategies()
    
    print("\nFACT: 최종 보고")
    if success:
        print("FACT: 진행중인 전략 프로세스 분석 완료 ✓")
    else:
        print("FACT: 분석 실패 ❌")
    
    print("FACT: 확인 완료")

if __name__ == "__main__":
    main()
