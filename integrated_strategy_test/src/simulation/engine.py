"""
시뮬레이션 엔진
"""

from typing import Dict, List, Any
from collections import defaultdict

from ..strategies.base_strategy import BaseStrategy

class SimulationEngine:
    """시뮬레이션 엔진"""
    
    def __init__(self):
        self.simulation_results = []
        self.total_pnl_history = []
    
    def run_simulation(self, historical_data: List[Dict[str, Any]], strategies: Dict[str, BaseStrategy]) -> Dict[str, Any]:
        """시뮬레이션 실행"""
        
        print(f"FACT: 시뮬레이션 엔진 실행")
        print(f"  - 시뮬레이션 기간: {len(historical_data)}일")
        print(f"  - 실행 전략: {len(strategies)}개")
        
        # 시뮬레이션 초기화
        self.simulation_results = []
        self.total_pnl_history = []
        
        for day_data in historical_data:
            date = day_data["date"]
            market_phase = day_data["market_phase"]
            market_conditions = day_data["market_conditions"]
            symbols = day_data["symbols"]
            
            daily_result = {
                "date": date,
                "market_phase": market_phase,
                "market_conditions": market_conditions,
                "strategies": {},
                "total_pnl": 0,
                "total_capital": 0,
                "stop_loss_triggered": [],
                "profit_taken": []
            }
            
            # 각 전략 실행
            for strategy_name, strategy in strategies.items():
                try:
                    # 전략 실행
                    strategy_result = self._execute_strategy(strategy, day_data)
                    
                    # 결과 저장
                    daily_result["strategies"][strategy_name] = strategy_result
                    
                    # 집계
                    daily_result["total_pnl"] += strategy_result["cumulative_pnl"]
                    daily_result["total_capital"] += strategy_result["final_amount"]
                    
                    # 리스크 이벤트 기록
                    if strategy_result.get("stop_loss_triggered"):
                        daily_result["stop_loss_triggered"].append(strategy_name)
                    
                    if strategy_result.get("profit_taken"):
                        daily_result["profit_taken"].append(strategy_name)
                
                except Exception as e:
                    print(f"ERROR: 전략 {strategy_name} 실행 실패: {e}")
                    continue
            
            # 누적 손익 기록
            self.total_pnl_history.append(daily_result["total_pnl"])
            self.simulation_results.append(daily_result)
        
        print(f"FACT: 시뮬레이션 완료")
        print(f"  - 총 실행 일수: {len(self.simulation_results)}일")
        print(f"  - 최종 손익: {self.total_pnl_history[-1]:.2f} USDT")
        
        return {
            "simulation_results": self.simulation_results,
            "total_pnl_history": self.total_pnl_history
        }
    
    def _execute_strategy(self, strategy: BaseStrategy, day_data: Dict[str, Any]) -> Dict[str, Any]:
        """개별 전략 실행"""
        
        # 시장 데이터 추출
        symbol_data = day_data["symbols"].get(strategy.symbol, {})
        market_conditions = day_data["market_conditions"]
        
        # 수익률 계산
        daily_return = strategy.calculate_return(day_data)
        
        # 레버리지 적용
        leveraged_return = strategy.get_leveraged_return(daily_return)
        
        # 리스크 관리 적용
        managed_return = strategy.apply_risk_management(leveraged_return)
        
        # 일일 손익 계산
        daily_pnl = strategy.initial_capital * managed_return
        
        # 누적 손익 계산
        if len(self.simulation_results) == 0:
            cumulative_pnl = daily_pnl
        else:
            prev_result = self.simulation_results[-1]["strategies"].get(strategy.name, {})
            prev_pnl = prev_result.get("cumulative_pnl", 0)
            cumulative_pnl = prev_pnl + daily_pnl
        
        # 최종 금액 계산
        final_amount = strategy.initial_capital + cumulative_pnl
        
        # 수익률 계산
        return_rate = (cumulative_pnl / strategy.initial_capital) * 100
        
        # 리스크 이벤트 확인
        stop_loss_triggered = managed_return <= strategy.stop_loss / 365
        profit_taken = managed_return >= strategy.profit_target / 365
        
        return {
            "symbol": strategy.symbol,
            "type": strategy.strategy_type,
            "algorithm": strategy.algorithm,
            "daily_pnl": round(daily_pnl, 2),
            "cumulative_pnl": round(cumulative_pnl, 2),
            "return_rate": round(return_rate, 2),
            "daily_return": round(managed_return * 100, 4),
            "price": symbol_data.get("price", 0),
            "price_change": symbol_data.get("change", 0),
            "volatility": symbol_data.get("volatility", 0),
            "market_phase": day_data["market_phase"],
            "market_conditions": market_conditions,
            "market_events": symbol_data.get("market_events", []),
            "stop_loss_triggered": stop_loss_triggered,
            "profit_taken": profit_taken,
            "final_amount": final_amount
        }
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """시뮬레이션 요약"""
        if not self.simulation_results:
            return {}
        
        # 기본 통계
        total_pnl = self.total_pnl_history[-1] if self.total_pnl_history else 0
        max_pnl = max(self.total_pnl_history) if self.total_pnl_history else 0
        min_pnl = min(self.total_pnl_history) if self.total_pnl_history else 0
        avg_pnl = sum(self.total_pnl_history) / len(self.total_pnl_history) if self.total_pnl_history else 0
        
        # 변동성 계산
        returns = []
        for i in range(1, len(self.total_pnl_history)):
            if self.total_pnl_history[i-1] != 0:
                daily_return = (self.total_pnl_history[i] - self.total_pnl_history[i-1]) / abs(self.total_pnl_history[i-1])
                returns.append(daily_return)
        
        volatility = sum(abs(r) for r in returns) / len(returns) * 100 if returns else 0
        
        return {
            "total_days": len(self.simulation_results),
            "final_pnl": total_pnl,
            "max_pnl": max_pnl,
            "min_pnl": min_pnl,
            "avg_pnl": avg_pnl,
            "volatility": volatility
        }
