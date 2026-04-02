#!/usr/bin/env python3
"""
테스트 멀티 전략 관리자
새로운 전략들을 테스트하고 기존 프로젝트와 비교 분석
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime, timezone

# 테스트 폴더 경로 추가
test_dir = Path(__file__).parent
sys.path.append(str(test_dir))
sys.path.append(str(test_dir.parent))

# 원본 프로젝트 경로 추가
project_dir = test_dir.parent
sys.path.append(str(project_dir))

from strategies.volatility_breakout_v1 import VolatilityBreakoutV1
from strategies.mean_reversion_v1 import MeanReversionV1


class TestMultiStrategyManager:
    """테스트 멀티 전략 관리자"""
    
    def __init__(self):
        self.strategies = {}
        self.test_results = {}
        self.comparison_results = {}
        self.initialize_strategies()
    
    def initialize_strategies(self):
        """새로운 전략 초기화"""
        self.strategies = {
            "volatility_breakout_v1": VolatilityBreakoutV1(),
            "mean_reversion_v1": MeanReversionV1()
        }
    
    def test_new_strategies(self, test_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """새로운 전략 테스트"""
        results = {}
        
        for strategy_id, strategy in self.strategies.items():
            try:
                # 테스트 데이터 생성
                closes = test_data.get("closes", [])
                highs = test_data.get("highs", closes.copy())
                lows = test_data.get("lows", closes.copy())
                volumes = test_data.get("volumes", [1000] * len(closes))
                
                # 전략 평가
                result = strategy.evaluate("BTCUSDT", closes, volumes)
                results[strategy_id] = {
                    "success": True,
                    "signal": result.get("signal", "HOLD"),
                    "signal_score": result.get("signal_score", 0.0),
                    "confidence": result.get("confidence", 0.0),
                    "reason": result.get("reason", ""),
                    "error": None
                }
            except Exception as e:
                results[strategy_id] = {
                    "success": False,
                    "signal": "HOLD",
                    "signal_score": 0.0,
                    "confidence": 0.0,
                    "reason": "",
                    "error": str(e)
                }
        
        self.test_results = results
        return results
    
    def compare_with_original(self) -> Dict[str, Any]:
        """원본 프로젝트와 비교 분석"""
        comparison = {
            "new_strategies": {
                "volatility_breakout_v1": {
                    "status": "미포함",
                    "file_exists": False,
                    "location": "test_multi_strategy/strategies/volatility_breakout_v1.py"
                },
                "mean_reversion_v1": {
                    "status": "미포함",
                    "file_exists": False,
                    "location": "test_multi_strategy/strategies/mean_reversion_v1.py"
                }
            },
            "existing_strategies": {
                "momentum_intraday_v1": {
                    "status": "포함됨",
                    "file_exists": True,
                    "location": "strategies/momentum_intraday_v1.py"
                },
                "trend_following_v1": {
                    "status": "포함됨",
                    "file_exists": True,
                    "location": "strategies/trend_following_v1.py"
                }
            },
            "integration_issues": [],
            "recommendations": []
        }
        
        # 원본 프로젝트 파일 존재 여부 확인
        original_strategies_dir = project_dir / "strategies"
        
        for strategy_name in comparison["existing_strategies"]:
            file_path = original_strategies_dir / f"{strategy_name}.py"
            comparison["existing_strategies"][strategy_name]["file_exists"] = file_path.exists()
        
        for strategy_name in comparison["new_strategies"]:
            file_path = original_strategies_dir / f"{strategy_name}.py"
            if file_path.exists():
                comparison["new_strategies"][strategy_name]["status"] = "포함됨"
                comparison["new_strategies"][strategy_name]["file_exists"] = True
                comparison["new_strategies"][strategy_name]["location"] = f"strategies/{strategy_name}.py"
            else:
                comparison["integration_issues"].append(f"{strategy_name} 전략이 원본 프로젝트에 없음")
        
        # 권장 사항 생성
        missing_count = len([s for s in comparison["new_strategies"].values() if s["status"] == "미포함"])
        if missing_count > 0:
            comparison["recommendations"].append(f"{missing_count}개 전략을 원본 프로젝트에 합체 필요")
        
        self.comparison_results = comparison
        return comparison
    
    def generate_test_report(self) -> str:
        """테스트 보고서 생성"""
        report = []
        report.append("# 테스트 멀티 전략 보고서")
        report.append(f"생성 시간: {datetime.now(timezone.utc).isoformat()}")
        report.append("")
        
        # 테스트 결과
        report.append("## 테스트 결과")
        for strategy_id, result in self.test_results.items():
            report.append(f"### {strategy_id}")
            report.append(f"- 성공 여부: {result['success']}")
            report.append(f"- 신호: {result['signal']}")
            report.append(f"- 신호 점수: {result['signal_score']}")
            report.append(f"- 확신도: {result['confidence']}")
            if result['error']:
                report.append(f"- 오류: {result['error']}")
            report.append("")
        
        # 비교 분석 결과
        report.append("## 원본 프로젝트와의 비교")
        comparison = self.comparison_results
        
        report.append("### 새로운 전략 상태")
        for strategy_name, info in comparison["new_strategies"].items():
            report.append(f"- {strategy_name}: {info['status']}")
        
        report.append("### 기존 전략 상태")
        for strategy_name, info in comparison["existing_strategies"].items():
            report.append(f"- {strategy_name}: {info['status']}")
        
        if comparison["integration_issues"]:
            report.append("### 통합 이슈")
            for issue in comparison["integration_issues"]:
                report.append(f"- {issue}")
        
        if comparison["recommendations"]:
            report.append("### 권장 사항")
            for rec in comparison["recommendations"]:
                report.append(f"- {rec}")
        
        return "\n".join(report)
    
    def save_report(self, output_path: str):
        """보고서 저장"""
        report = self.generate_test_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"보고서가 저장되었습니다: {output_path}")


def create_test_data() -> Dict[str, List[float]]:
    """테스트 데이터 생성"""
    # 다양한 시나리오를 위한 테스트 데이터
    base_price = 100
    
    # 추세 상승 데이터
    trend_up = [base_price + i * 0.5 for i in range(50)]
    
    # 횡보 데이터
    ranging = [base_price + (i % 10 - 5) * 0.2 for i in range(50)]
    
    # 변동성 높은 데이터
    volatile = [base_price + (i % 20 - 10) * 0.8 for i in range(50)]
    
    # 과매수/과매도 데이터
    overbought_oversold = [base_price + (i % 30 - 15) * 0.5 for i in range(50)]
    
    return {
        "trend_up": {
            "closes": trend_up,
            "highs": [p + 0.1 for p in trend_up],
            "lows": [p - 0.1 for p in trend_up],
            "volumes": [1000 + i * 10 for i in range(50)]
        },
        "ranging": {
            "closes": ranging,
            "highs": [p + 0.05 for p in ranging],
            "lows": [p - 0.05 for p in ranging],
            "volumes": [800 + i * 5 for i in range(50)]
        },
        "volatile": {
            "closes": volatile,
            "highs": [p + 0.2 for p in volatile],
            "lows": [p - 0.2 for p in volatile],
            "volumes": [1200 + i * 20 for i in range(50)]
        },
        "overbought_oversold": {
            "closes": overbought_oversold,
            "highs": [p + 0.15 for p in overbought_oversold],
            "lows": [p - 0.15 for p in overbought_oversold],
            "volumes": [900 + i * 8 for i in range(50)]
        }
    }


def main():
    """메인 테스트 실행"""
    print("=== 테스트 멀티 전략 실행 시작 ===")
    
    # 테스트 관리자 초기화
    manager = TestMultiStrategyManager()
    
    # 테스트 데이터 생성
    test_data_sets = create_test_data()
    
    # 각 시나리오별 테스트 실행
    all_results = {}
    for scenario, data in test_data_sets.items():
        print(f"\n--- {scenario} 시나리오 테스트 ---")
        results = manager.test_new_strategies(data)
        all_results[scenario] = results
        
        for strategy_id, result in results.items():
            status = "성공" if result["success"] else "실패"
            print(f"{strategy_id}: {status} - 신호: {result['signal']}")
    
    # 원본 프로젝트와 비교
    print("\n--- 원본 프로젝트와 비교 분석 ---")
    comparison = manager.compare_with_original()
    
    print("새로운 전략 상태:")
    for strategy_name, info in comparison["new_strategies"].items():
        print(f"- {strategy_name}: {info['status']}")
    
    print("\n기존 전략 상태:")
    for strategy_name, info in comparison["existing_strategies"].items():
        print(f"- {strategy_name}: {info['status']}")
    
    if comparison["integration_issues"]:
        print("\n통합 이슈:")
        for issue in comparison["integration_issues"]:
            print(f"- {issue}")
    
    # 보고서 생성 및 저장
    report_path = test_dir / "test_multi_strategy_report.md"
    manager.save_report(str(report_path))
    
    print(f"\n=== 테스트 완료 ===")
    print(f"보고서: {report_path}")


if __name__ == "__main__":
    main()
