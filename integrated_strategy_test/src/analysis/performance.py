"""
성과 분석 모듈
"""

from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime

class PerformanceAnalyzer:
    """성과 분석기"""
    
    def __init__(self):
        self.analysis_results = {}
    
    def analyze(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """성과 분석"""
        
        print(f"FACT: 성과 분석 시작")
        
        simulation_results = simulation_data["simulation_results"]
        total_pnl_history = simulation_data["total_pnl_history"]
        
        # 전체 성과 분석
        total_performance = self._analyze_total_performance(total_pnl_history)
        
        # 전략별 성과 분석
        strategy_summary = self._analyze_strategy_performance(simulation_results)
        
        # 전략 그룹별 분석
        group_performance = self._analyze_group_performance(strategy_summary)
        
        # 시장 페이즈별 분석
        phase_performance = self._analyze_phase_performance(simulation_results)
        
        # 리스크/보상 분석
        risk_reward_analysis = self._analyze_risk_reward(simulation_results)
        
        # 투자 분석
        investment_analysis = self._analyze_investment(strategy_summary)
        
        self.analysis_results = {
            "total_performance": total_performance,
            "strategy_summary": strategy_summary,
            "group_performance": group_performance,
            "phase_performance": phase_performance,
            "risk_reward_analysis": risk_reward_analysis,
            "investment_analysis": investment_analysis,
            "daily_results": simulation_results,
            "pnl_history": total_pnl_history
        }
        
        print(f"FACT: 성과 분석 완료")
        print(f"  - 최종 손익: {total_performance['final_pnl']:.2f} USDT")
        print(f"  - 실제 수익률: {investment_analysis['actual_return_rate']:.2f}%")
        
        return self.analysis_results
    
    def _analyze_total_performance(self, total_pnl_history: List[float]) -> Dict[str, Any]:
        """전체 성과 분석"""
        
        if not total_pnl_history:
            return {}
        
        initial_total_pnl = total_pnl_history[0]
        final_total_pnl = total_pnl_history[-1]
        total_change = final_total_pnl - initial_total_pnl
        
        # 통계 계산
        max_pnl = max(total_pnl_history)
        min_pnl = min(total_pnl_history)
        avg_pnl = sum(total_pnl_history) / len(total_pnl_history)
        
        # 변동성 계산
        returns = []
        for i in range(1, len(total_pnl_history)):
            if total_pnl_history[i-1] != 0:
                daily_return = (total_pnl_history[i] - total_pnl_history[i-1]) / abs(total_pnl_history[i-1])
                returns.append(daily_return)
        
        volatility = sum(abs(r) for r in returns) / len(returns) * 100 if returns else 0
        
        return {
            "initial_pnl": initial_total_pnl,
            "final_pnl": final_total_pnl,
            "total_change": total_change,
            "max_pnl": max_pnl,
            "min_pnl": min_pnl,
            "avg_pnl": avg_pnl,
            "volatility": volatility
        }
    
    def _analyze_strategy_performance(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전략별 성과 분석"""
        
        strategy_summary = defaultdict(lambda: {
            "total_pnl": 0,
            "days_active": 0,
            "stop_loss_count": 0,
            "profit_taken_count": 0,
            "symbol": "",
            "type": "",
            "algorithm": "",
            "initial_capital": 0
        })
        
        for day_result in simulation_results:
            for strategy_name, strategy_data in day_result["strategies"].items():
                # 기본 정보 설정 (첫 날에만)
                if strategy_summary[strategy_name]["days_active"] == 0:
                    strategy_summary[strategy_name]["symbol"] = strategy_data.get("symbol", "")
                    strategy_summary[strategy_name]["type"] = strategy_data.get("type", "")
                    strategy_summary[strategy_name]["algorithm"] = strategy_data.get("algorithm", "")
                
                # 성과 집계
                strategy_summary[strategy_name]["total_pnl"] += strategy_data.get("daily_pnl", 0)
                strategy_summary[strategy_name]["days_active"] += 1
            
            # 리스크 이벤트 집계
            for triggered_strategy in day_result["stop_loss_triggered"]:
                strategy_summary[triggered_strategy]["stop_loss_count"] += 1
            
            for profit_strategy in day_result["profit_taken"]:
                strategy_summary[profit_strategy]["profit_taken_count"] += 1
        
        return dict(strategy_summary)
    
    def _analyze_group_performance(self, strategy_summary: Dict[str, Any]) -> Dict[str, Any]:
        """전략 그룹별 성과 분석"""
        
        group_performance = defaultdict(lambda: {"count": 0, "total_pnl": 0})
        
        for strategy_name, summary in strategy_summary.items():
            strategy_type = summary["type"]
            total_pnl = summary["total_pnl"]
            
            group_performance[strategy_type]["count"] += 1
            group_performance[strategy_type]["total_pnl"] += total_pnl
        
        return dict(group_performance)
    
    def _analyze_phase_performance(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """시장 페이즈별 성과 분석"""
        
        phase_performance = defaultdict(lambda: {"count": 0, "total_pnl": 0})
        
        for day_result in simulation_results:
            phase = day_result["market_phase"]
            phase_performance[phase]["count"] += 1
            phase_performance[phase]["total_pnl"] += day_result["total_pnl"]
        
        return dict(phase_performance)
    
    def _analyze_risk_reward(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """리스크/보상 분석"""
        
        total_stop_loss_events = 0
        total_profit_taken_events = 0
        
        for day_result in simulation_results:
            total_stop_loss_events += len(day_result["stop_loss_triggered"])
            total_profit_taken_events += len(day_result["profit_taken"])
        
        return {
            "total_stop_loss_events": total_stop_loss_events,
            "total_profit_taken_events": total_profit_taken_events,
            "risk_reward_ratio": f"{total_profit_taken_events}/{total_stop_loss_events}"
        }
    
    def _analyze_investment(self, strategy_summary: Dict[str, Any]) -> Dict[str, Any]:
        """투자 분석"""
        
        # 전략별 초기 자본금 합계
        total_investment = 0
        
        for strategy_name, summary in strategy_summary.items():
            # 전략 관리자에서 초기 자본금 가져오기 (여기서는 추정)
            estimated_capital = self._estimate_strategy_capital(strategy_name)
            total_investment += estimated_capital
            summary["initial_capital"] = estimated_capital
        
        # 수익률 계산
        total_change = sum(summary["total_pnl"] for summary in strategy_summary.values())
        actual_return_rate = (total_change / total_investment) * 100 if total_investment > 0 else 0
        
        return {
            "total_investment": total_investment,
            "actual_return_rate": actual_return_rate,
            "annual_return_rate": actual_return_rate
        }
    
    def _estimate_strategy_capital(self, strategy_name: str) -> float:
        """전략별 초기 자본금 추정"""
        
        # 전략 이름별 초기 자본금 매핑 (실제 전략 관리자에서 가져와야 함)
        capital_mapping = {
            "conservative_btc": 2000.0,
            "conservative_eth": 1500.0,
            "growth_sol": 1000.0,
            "volatility_doge": 300.0,
            "momentum_shib": 200.0,
            "ultra_aggressive_1": 1590.0,
            "ultra_aggressive_2": 1060.0,
            "high_growth_1": 530.0,
            "high_growth_2": 265.0,
            "high_growth_3": 212.0,
            "ml_momentum_1": 318.0,
            "statistical_arb_1": 265.0,
            "volatility_arb_1": 212.0,
            "mean_reversion_1": 159.0,
            "market_making_1": 212.0,
            "triangular_arb_1": 159.0,
            "enhanced_1": 150.0,
            "enhanced_2": 120.0,
            "enhanced_3": 100.0,
            "extreme_leverage_1": 1000.0,
            "extreme_leverage_2": 800.0,
            "pump_scalp_1": 600.0,
            "pump_scalp_2": 500.0,
            "meme_explosion_1": 400.0,
            "meme_explosion_2": 300.0,
            "ultra_scalp_1": 250.0,
            "ultra_scalp_2": 200.0,
            "extreme_momentum_1": 150.0,
            "extreme_momentum_2": 100.0
        }
        
        return capital_mapping.get(strategy_name, 100.0)
    
    def get_top_performers(self, metric: str = "total_pnl", limit: int = 5) -> List[Dict[str, Any]]:
        """최고 성과 전략 반환"""
        
        if "strategy_summary" not in self.analysis_results:
            return []
        
        strategy_summary = self.analysis_results["strategy_summary"]
        
        # 성과 정렬
        sorted_strategies = sorted(
            strategy_summary.items(),
            key=lambda x: x[1].get(metric, 0),
            reverse=True
        )
        
        return [
            {
                "name": name,
                **summary,
                "return_rate": (summary["total_pnl"] / summary["initial_capital"] * 100) if summary["initial_capital"] > 0 else 0
            }
            for name, summary in sorted_strategies[:limit]
        ]
    
    def get_worst_performers(self, metric: str = "total_pnl", limit: int = 5) -> List[Dict[str, Any]]:
        """최저 성과 전략 반환"""
        
        if "strategy_summary" not in self.analysis_results:
            return []
        
        strategy_summary = self.analysis_results["strategy_summary"]
        
        # 성과 정렬 (오름차순)
        sorted_strategies = sorted(
            strategy_summary.items(),
            key=lambda x: x[1].get(metric, 0)
        )
        
        return [
            {
                "name": name,
                **summary,
                "return_rate": (summary["total_pnl"] / summary["initial_capital"] * 100) if summary["initial_capital"] > 0 else 0
            }
            for name, summary in sorted_strategies[:limit]
        ]
