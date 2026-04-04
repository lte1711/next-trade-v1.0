#!/usr/bin/env python3
"""
원본 프로젝트에 전략 통합 시 문제점 및 보완점 분석 (FACT ONLY)
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone

def analyze_integration_issues():
    """원본 프로젝트 통합 시 문제점 분석"""
    
    print("FACT: 원본 프로젝트에 전략 통합 시 문제점 분석")
    
    # 1. 현재 원본 프로젝트 상태 확인
    print("\nFACT: 현재 원본 프로젝트 상태 확인")
    
    # 실행중인 프로세스 확인
    try:
        result = subprocess.run([
            "Get-Process", "-Name", "python"
        ], capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            processes = result.stdout.strip().split('\n')
            python_processes = [p for p in processes if 'python' in p.lower()]
            print(f"  - 실행중인 Python 프로세스: {len(python_processes)}개")
            
            for process in python_processes[:5]:  # 상위 5개만 표시
                print(f"    * {process.strip()}")
        else:
            print("  - 프로세스 확인 실패")
            
    except Exception as e:
        print(f"  - 프로세스 확인 오류: {e}")
    
    # 2. 원본 전략 파일 구조 확인
    print("\nFACT: 원본 전략 파일 구조 확인")
    
    strategies_dir = Path("strategies")
    if strategies_dir.exists():
        strategy_files = list(strategies_dir.glob("*.py"))
        print(f"  - 전략 파일: {len(strategy_files)}개")
        
        for file in strategy_files:
            if file.name != "__init__.py":
                print(f"    * {file.name}")
                
                # 파일 내용 간단 확인
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 클래스 정의 확인
                    if 'class ' in content:
                        class_lines = [line for line in content.split('\n') if 'class ' in line]
                        for line in class_lines:
                            if 'Strategy' in line:
                                class_name = line.strip().split('class ')[1].split('(')[0].strip()
                                print(f"      - 클래스: {class_name}")
                
                except Exception as e:
                    print(f"      - 파일 읽기 오류: {e}")
    
    # 3. 멀티 전략 매니저 확인
    print("\nFACT: 멀티 전략 매니저 확인")
    
    manager_file = Path("strategies/multi_strategy_manager.py")
    if manager_file.exists():
        try:
            with open(manager_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 전략 등록 확인
            if 'register_strategy' in content:
                register_lines = [line for line in content.split('\n') if 'register_strategy' in line]
                print(f"  - 등록된 전략: {len(register_lines)}개")
                
                for line in register_lines:
                    if '#' not in line and 'register_strategy' in line:
                        strategy_name = line.strip().split('(')[1].split(')')[0].strip().strip('"\'')
                        print(f"    * {strategy_name}")
            
            # 전략 목록 확인
            if 'strategies' in content and '=' in content:
                strategies_line = [line for line in content.split('\n') if 'strategies' in line and '=' in line]
                for line in strategies_line:
                    if 'strategies' in line:
                        print(f"  - 전략 목록: {line.strip()}")
                        
        except Exception as e:
            print(f"  - 매니저 파일 읽기 오류: {e}")
    else:
        print("  - 멀티 전략 매니저 파일 없음")
    
    # 4. config.json 전략 설정 확인
    print("\nFACT: config.json 전략 설정 확인")
    
    config_file = Path("config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            strategies_config = config.get("strategies", {})
            print(f"  - 설정된 전략: {len(strategies_config)}개")
            
            for strategy_name, strategy_config in strategies_config.items():
                enabled = strategy_config.get("enabled", False)
                weight = strategy_config.get("weight", 0)
                symbols = strategy_config.get("symbols", [])
                
                print(f"    * {strategy_name}")
                print(f"      - 활성화: {enabled}")
                print(f"      - 가중치: {weight}")
                print(f"      - 심볼: {symbols}")
                
        except Exception as e:
            print(f"  - config.json 읽기 오류: {e}")
    else:
        print("  - config.json 파일 없음")
    
    return True

def identify_integration_problems():
    """통합 시 발생 가능한 문제점 식별"""
    
    print("\nFACT: 통합 시 발생 가능한 문제점 식별")
    
    problems = []
    
    # 문제 1: 전략 충돌
    problems.append({
        "category": "전략 충돌",
        "description": "동일 심볼에 대해 여러 전략 실행 시 충돌 가능성",
        "current_situation": "BCHUSDT, BTCUSDT 실행중",
        "potential_conflict": "QUICKUSDT, LRCUSDT 추가 시 심볼 중복 가능성",
        "severity": "높음"
    })
    
    # 문제 2: 리소스 경합
    problems.append({
        "category": "리소스 경합",
        "description": "동시 실행 시 메모리, CPU 사용량 증가",
        "current_situation": "2개 워커 실행중",
        "potential_impact": "4개 워커 실행 시 리소스 2배 증가",
        "severity": "중간"
    })
    
    # 문제 3: API 호출 제한
    problems.append({
        "category": "API 호출 제한",
        "description": "바이낸스 API 호출 빈도 증가로 제한 가능성",
        "current_situation": "2개 전략 API 호출",
        "potential_impact": "4개 전략 실행 시 API 호출 2배 증가",
        "severity": "높음"
    })
    
    # 문제 4: 데이터 일관성
    problems.append({
        "category": "데이터 일관성",
        "description": "여러 전략의 데이터 동기화 문제",
        "current_situation": "별도 데이터 소스 사용",
        "potential_impact": "데이터 불일치로 인한 잘못된 의사결정",
        "severity": "중간"
    })
    
    # 문제 5: 포지션 관리
    problems.append({
        "category": "포지션 관리",
        "description": "동일 심볼에 대한 여러 포지션 충돌",
        "current_situation": "각 전략별 독립 포지션",
        "potential_conflict": "동일 심볼 다중 진입 시 청산 충돌",
        "severity": "높음"
    })
    
    print(f"  - 식별된 문제점: {len(problems)}개")
    
    for i, problem in enumerate(problems):
        category = problem["category"]
        description = problem["description"]
        severity = problem["severity"]
        
        print(f"\n    {i+1}. {category} (심각도: {severity})")
        print(f"       - 설명: {description}")
        
        if "current_situation" in problem:
            current = problem["current_situation"]
            print(f"       - 현재 상황: {current}")
        
        if "potential_conflict" in problem:
            conflict = problem["potential_conflict"]
            print(f"       - 잠재적 충돌: {conflict}")
        
        if "potential_impact" in problem:
            impact = problem["potential_impact"]
            print(f"       - 잠재적 영향: {impact}")
    
    return problems

def suggest_improvements():
    """보완점 제안"""
    
    print("\nFACT: 보완점 제안")
    
    improvements = []
    
    # 보완 1: 전략 스케줄러
    improvements.append({
        "category": "전략 스케줄러",
        "description": "전략 실행 시간 및 우선순위 관리",
        "implementation": "실행 큐 및 우선순위 시스템 구축",
        "benefit": "리소스 효율화 및 충돌 방지",
        "complexity": "중간"
    })
    
    # 보완 2: 동적 리소스 관리
    improvements.append({
        "category": "동적 리소스 관리",
        "description": "시스템 리소스 상태에 따른 전략 실행 조절",
        "implementation": "CPU, 메모리 모니터링 및 자동 조절",
        "benefit": "시스템 안정성 확보",
        "complexity": "높음"
    })
    
    # 보완 3: 전략 성과 기반 필터링
    improvements.append({
        "category": "전략 성과 기반 필터링",
        "description": "성과 저조 전략 자동 중지 및 우수 전략 확장",
        "implementation": "성과 지표 기반 자동 필터링 시스템",
        "benefit": "수익률 자동 개선",
        "complexity": "중간"
    })
    
    # 보완 4: API 호출 최적화
    improvements.append({
        "category": "API 호출 최적화",
        "description": "API 호출 빈도 제한 및 캐싱 전략",
        "implementation": "API 호출 큐 및 Rate Limiting",
        "benefit": "API 제한 회피 및 안정성 확보",
        "complexity": "중간"
    })
    
    # 보완 5: 포지션 관리 통합
    improvements.append({
        "category": "포지션 관리 통합",
        "description": "중앙 포지션 관리 시스템 구축",
        "implementation": "통합 포지션 트래커 및 충돌 방지",
        "benefit": "포지션 충돌 방지 및 효율적 자산 관리",
        "complexity": "높음"
    })
    
    print(f"  - 제안된 보완점: {len(improvements)}개")
    
    for i, improvement in enumerate(improvements):
        category = improvement["category"]
        description = improvement["description"]
        implementation = improvement["implementation"]
        benefit = improvement["benefit"]
        complexity = improvement["complexity"]
        
        print(f"\n    {i+1}. {category} (복잡도: {complexity})")
        print(f"       - 설명: {description}")
        print(f"       - 구현: {implementation}")
        print(f"       - 효과: {benefit}")
    
    return improvements

def create_integration_plan():
    """통합 실행 계획 생성"""
    
    print("\nFACT: 통합 실행 계획 생성")
    
    # 1단계: 준비 단계
    preparation_steps = [
        {
            "step": 1,
            "action": "현재 실행중인 손실 전략 중지",
            "description": "BCHUSDT, BTCUSDT 워커 프로세스 안전 종료",
            "command": "kill -TERM 3824 5092",
            "risk": "중간",
            "timeline": "즉시"
        },
        {
            "step": 2,
            "action": "전략 설정 업데이트",
            "description": "config.json에 수익 전략 추가 및 활성화",
            "files": ["config.json"],
            "risk": "낮음",
            "timeline": "5분"
        },
        {
            "step": 3,
            "action": "리소스 사용량 확인",
            "description": "현재 시스템 리소스 상태 모니터링",
            "command": "top, htop",
            "risk": "낮음",
            "timeline": "2분"
        }
    ]
    
    print(f"  - 준비 단계: {len(preparation_steps)}단계")
    
    for step in preparation_steps:
        step_num = step["step"]
        action = step["action"]
        description = step["description"]
        risk = step["risk"]
        timeline = step["timeline"]
        
        print(f"    {step_num}. {action}")
        print(f"       - 설명: {description}")
        print(f"       - 위험: {risk}")
        print(f"       - 시간: {timeline}")
    
    # 2단계: 통합 단계
    integration_steps = [
        {
            "step": 4,
            "action": "수익 전략 워커 시작",
            "description": "QUICKUSDT, LRCUSDT 전략 워커 프로세스 시작",
            "command": "python worker.py --symbol QUICKUSDT",
            "risk": "중간",
            "timeline": "10분"
        },
        {
            "step": 5,
            "action": "멀티 전략 매니저 재시작",
            "description": "새로운 전략 설정 적용을 위해 매니저 재시작",
            "command": "kill -HUP $(pgrep -f multi_strategy_manager.py)",
            "risk": "중간",
            "timeline": "2분"
        },
        {
            "step": 6,
            "action": "성과 모니터링 시작",
            "description": "통합된 전략 성과 실시간 모니터링",
            "command": "curl http://127.0.0.1:8788/api/runtime",
            "risk": "낮음",
            "timeline": "1분"
        }
    ]
    
    print(f"\n  - 통합 단계: {len(integration_steps)}단계")
    
    for step in integration_steps:
        step_num = step["step"]
        action = step["action"]
        description = step["description"]
        risk = step["risk"]
        timeline = step["timeline"]
        
        print(f"    {step_num}. {action}")
        print(f"       - 설명: {description}")
        print(f"       - 위험: {risk}")
        print(f"       - 시간: {timeline}")
    
    # 3단계: 검증 단계
    verification_steps = [
        {
            "step": 7,
            "action": "전략 실행 상태 확인",
            "description": "모든 전략 워커 정상 실행 확인",
            "method": "프로세스 목록 및 API 응답 확인",
            "risk": "낮음",
            "timeline": "5분"
        },
        {
            "step": 8,
            "action": "성과 데이터 검증",
            "description": "각 전략별 성과 데이터 정확성 확인",
            "method": "대시보드 및 로그 파일 분석",
            "risk": "낮음",
            "timeline": "10분"
        },
        {
            "step": 9,
            "action": "리소스 사용량 모니터링",
            "description": "통합 후 시스템 리소스 사용량 추적",
            "method": "CPU, 메모리, 네트워크 사용량 모니터링",
            "risk": "낮음",
            "timeline": "지속"
        }
    ]
    
    print(f"\n  - 검증 단계: {len(verification_steps)}단계")
    
    for step in verification_steps:
        step_num = step["step"]
        action = step["action"]
        description = step["description"]
        method = step["method"]
        risk = step["risk"]
        timeline = step["timeline"]
        
        print(f"    {step_num}. {action}")
        print(f"       - 설명: {description}")
        print(f"       - 방법: {method}")
        print(f"       - 위험: {risk}")
        print(f"       - 시간: {timeline}")
    
    return {
        "preparation": preparation_steps,
        "integration": integration_steps,
        "verification": verification_steps
    }

def generate_integration_report():
    """통합 보고 생성"""
    
    print("\nFACT: 통합 보고 생성")
    
    # 문제점 및 보완점 요약
    problems = identify_integration_problems()
    improvements = suggest_improvements()
    plan = create_integration_plan()
    
    # 보고 생성
    report = {
        "integration_analysis": {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "원본 프로젝트 전략 통합",
            "current_status": "2개 손실 전략 실행중",
            "target_status": "4개 전략 통합 실행"
        },
        "identified_problems": {
            "total_count": len(problems),
            "high_severity": len([p for p in problems if p["severity"] == "높음"]),
            "medium_severity": len([p for p in problems if p["severity"] == "중간"]),
            "problems": problems
        },
        "suggested_improvements": {
            "total_count": len(improvements),
            "high_complexity": len([i for i in improvements if i["complexity"] == "높음"]),
            "medium_complexity": len([i for i in improvements if i["complexity"] == "중간"]),
            "improvements": improvements
        },
        "integration_plan": plan,
        "risk_assessment": {
            "overall_risk": "중간",
            "critical_points": [
                "API 호출 제한",
                "포지션 관리 충돌",
                "리소스 경합"
            ],
            "mitigation_strategies": [
                "API 호출 큐 관리",
                "중앙 포지션 관리",
                "동적 리소스 할당"
            ]
        },
        "expected_outcomes": [
            "손실 전략 중지로 추가 손실 방지",
            "수익 전략 추가로 수익 창출",
            "시스템 안정성 확보",
            "자동화된 전략 관리"
        ]
    }
    
    # 보고 저장
    report_file = Path("integration_analysis_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"FACT: 통합 분석 보고 저장 완료: {report_file}")
    
    return report

def main():
    """메인 실행"""
    
    print("=== 원본 프로젝트에 전략 통합 시 문제점 및 보완점 분석 (FACT ONLY) ===")
    
    # 1단계: 현재 상태 분석
    analyze_integration_issues()
    
    # 2단계: 문제점 식별
    problems = identify_integration_problems()
    
    # 3단계: 보완점 제안
    improvements = suggest_improvements()
    
    # 4단계: 통합 계획 생성
    plan = create_integration_plan()
    
    # 5단계: 보고 생성
    report = generate_integration_report()
    
    print("\nFACT: 최종 보고")
    print(f"  - 식별된 문제점: {len(problems)}개")
    print(f"  - 제안된 보완점: {len(improvements)}개")
    print(f"  - 통합 계획 단계: {sum(len(plan[k]) for k in plan.keys())}단계")
    print(f"  - 전체 위험도: 중간")
    
    return True

if __name__ == "__main__":
    main()
