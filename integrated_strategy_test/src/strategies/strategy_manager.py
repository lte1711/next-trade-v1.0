"""
전략 관리자
"""

from typing import Dict, List, Any
from collections import defaultdict

from .all_strategies import create_strategy

class StrategyManager:
    """전략 관리자"""
    
    def __init__(self):
        self.strategies = {}
        self.strategy_groups = defaultdict(list)
    
    def load_all_strategies(self) -> Dict[str, Any]:
        """모든 전략 로드"""
        
        print(f"FACT: 모든 전략 로드 시작")
        
        # 모든 전략 통합 (총 29개 전략)
        strategy_configs = {
            # 1. 기본 전략 (5개)
            "conservative_btc": {
                "symbol": "BTCUSDT", "type": "conservative", "initial_capital": 2000.0,
                "stop_loss": -0.08, "leverage": 2.0, "target_return": 0.15, "profit_target": 0.12
            },
            "conservative_eth": {
                "symbol": "ETHUSDT", "type": "conservative", "initial_capital": 1500.0,
                "stop_loss": -0.08, "leverage": 2.0, "target_return": 0.18, "profit_target": 0.15
            },
            "growth_sol": {
                "symbol": "SOLUSDT", "type": "growth", "initial_capital": 1000.0,
                "stop_loss": -0.10, "leverage": 3.0, "target_return": 0.35, "profit_target": 0.25
            },
            "volatility_doge": {
                "symbol": "DOGEUSDT", "type": "volatility", "initial_capital": 300.0,
                "stop_loss": -0.15, "leverage": 4.0, "target_return": 0.60, "profit_target": 0.40
            },
            "momentum_shib": {
                "symbol": "SHIBUSDT", "type": "momentum", "initial_capital": 200.0,
                "stop_loss": -0.20, "leverage": 5.0, "target_return": 1.0, "profit_target": 0.60
            },
            
            # 2. 극대화 전략 (5개)
            "ultra_aggressive_1": {
                "symbol": "BTCUSDT", "type": "ultra_aggressive", "initial_capital": 1590.0,
                "stop_loss": -0.12, "leverage": 5.0, "target_return": 0.50, "profit_target": 0.35
            },
            "ultra_aggressive_2": {
                "symbol": "ETHUSDT", "type": "ultra_aggressive", "initial_capital": 1060.0,
                "stop_loss": -0.12, "leverage": 6.0, "target_return": 0.60, "profit_target": 0.40
            },
            "high_growth_1": {
                "symbol": "SOLUSDT", "type": "high_growth", "initial_capital": 530.0,
                "stop_loss": -0.15, "leverage": 7.0, "target_return": 0.80, "profit_target": 0.50
            },
            "high_growth_2": {
                "symbol": "QUICKUSDT", "type": "high_growth", "initial_capital": 265.0,
                "stop_loss": -0.15, "leverage": 8.0, "target_return": 1.0, "profit_target": 0.60
            },
            "high_growth_3": {
                "symbol": "LRCUSDT", "type": "high_growth", "initial_capital": 212.0,
                "stop_loss": -0.15, "leverage": 9.0, "target_return": 1.2, "profit_target": 0.70
            },
            
            # 3. 확장 전략 (9개)
            "ml_momentum_1": {
                "symbol": "DOGEUSDT", "type": "ml_momentum", "initial_capital": 318.0,
                "stop_loss": -0.10, "leverage": 3.5, "target_return": 0.45, "profit_target": 0.35,
                "algorithm": "LSTM_Momentum"
            },
            "statistical_arb_1": {
                "symbol": "SHIBUSDT", "type": "statistical_arbitrage", "initial_capital": 265.0,
                "stop_loss": -0.08, "leverage": 2.5, "target_return": 0.25, "profit_target": 0.20,
                "algorithm": "Pairs_Trading"
            },
            "volatility_arb_1": {
                "symbol": "PEPEUSDT", "type": "volatility_arbitrage", "initial_capital": 212.0,
                "stop_loss": -0.12, "leverage": 4.5, "target_return": 0.50, "profit_target": 0.40,
                "algorithm": "Volatility_Scaling"
            },
            "mean_reversion_1": {
                "symbol": "WIFUSDT", "type": "mean_reversion", "initial_capital": 159.0,
                "stop_loss": -0.10, "leverage": 3.0, "target_return": 0.30, "profit_target": 0.25,
                "algorithm": "Ornstein_Uhlenbeck"
            },
            "market_making_1": {
                "symbol": "BONKUSDT", "type": "market_making", "initial_capital": 212.0,
                "stop_loss": -0.06, "leverage": 2.0, "target_return": 0.20, "profit_target": 0.15,
                "algorithm": "Bid_Ask_Spread"
            },
            "triangular_arb_1": {
                "symbol": "FLOKIUSDT", "type": "triangular_arbitrage", "initial_capital": 159.0,
                "stop_loss": -0.08, "leverage": 2.5, "target_return": 0.35, "profit_target": 0.25,
                "algorithm": "Triangular_Loop"
            },
            "enhanced_1": {
                "symbol": "ADAUSDT", "type": "enhanced", "initial_capital": 150.0,
                "stop_loss": -0.10, "leverage": 3.5, "target_return": 0.40, "profit_target": 0.30
            },
            "enhanced_2": {
                "symbol": "MATICUSDT", "type": "enhanced", "initial_capital": 120.0,
                "stop_loss": -0.10, "leverage": 4.0, "target_return": 0.45, "profit_target": 0.35
            },
            "enhanced_3": {
                "symbol": "AVAXUSDT", "type": "enhanced", "initial_capital": 100.0,
                "stop_loss": -0.10, "leverage": 4.5, "target_return": 0.50, "profit_target": 0.40
            },
            
            # 4. 초극단 전략 (10개)
            "extreme_leverage_1": {
                "symbol": "BTCUSDT", "type": "extreme_leverage", "initial_capital": 1000.0,
                "stop_loss": -0.15, "leverage": 10.0, "target_return": 1.2, "profit_target": 0.80
            },
            "extreme_leverage_2": {
                "symbol": "ETHUSDT", "type": "extreme_leverage", "initial_capital": 800.0,
                "stop_loss": -0.15, "leverage": 12.0, "target_return": 1.5, "profit_target": 1.0
            },
            "pump_scalp_1": {
                "symbol": "SOLUSDT", "type": "pump_scalping", "initial_capital": 600.0,
                "stop_loss": -0.20, "leverage": 15.0, "target_return": 2.0, "profit_target": 1.5
            },
            "pump_scalp_2": {
                "symbol": "DOGEUSDT", "type": "pump_scalping", "initial_capital": 500.0,
                "stop_loss": -0.25, "leverage": 20.0, "target_return": 3.0, "profit_target": 2.0
            },
            "meme_explosion_1": {
                "symbol": "SHIBUSDT", "type": "meme_explosion", "initial_capital": 400.0,
                "stop_loss": -0.30, "leverage": 25.0, "target_return": 5.0, "profit_target": 3.0
            },
            "meme_explosion_2": {
                "symbol": "PEPEUSDT", "type": "meme_explosion", "initial_capital": 300.0,
                "stop_loss": -0.35, "leverage": 30.0, "target_return": 8.0, "profit_target": 4.0
            },
            "ultra_scalp_1": {
                "symbol": "WIFUSDT", "type": "ultra_scalping", "initial_capital": 250.0,
                "stop_loss": -0.25, "leverage": 20.0, "target_return": 4.0, "profit_target": 2.5
            },
            "ultra_scalp_2": {
                "symbol": "BONKUSDT", "type": "ultra_scalping", "initial_capital": 200.0,
                "stop_loss": -0.30, "leverage": 25.0, "target_return": 6.0, "profit_target": 3.0
            },
            "extreme_momentum_1": {
                "symbol": "FLOKIUSDT", "type": "extreme_momentum", "initial_capital": 150.0,
                "stop_loss": -0.40, "leverage": 35.0, "target_return": 10.0, "profit_target": 5.0
            },
            "extreme_momentum_2": {
                "symbol": "1000PEPEUSDT", "type": "extreme_momentum", "initial_capital": 100.0,
                "stop_loss": -0.40, "leverage": 40.0, "target_return": 12.0, "profit_target": 6.0
            }
        }
        
        # 전략 인스턴스 생성
        for strategy_name, config in strategy_configs.items():
            try:
                strategy = create_strategy(strategy_name, config)
                self.strategies[strategy_name] = strategy
                
                # 그룹별 분류
                strategy_type = config.get("type", "unknown")
                self.strategy_groups[strategy_type].append(strategy_name)
                
            except Exception as e:
                print(f"ERROR: 전략 {strategy_name} 생성 실패: {e}")
                continue
        
        print(f"FACT: {len(self.strategies)}개 전략 로드 완료")
        print(f"  - 전략 그룹: {len(self.strategy_groups)}개")
        
        for group_name, strategies in self.strategy_groups.items():
            print(f"  - {group_name}: {len(strategies)}개")
        
        return self.strategies
    
    def get_strategy(self, name: str):
        """특정 전략 가져오기"""
        return self.strategies.get(name)
    
    def get_strategies_by_group(self, group_type: str) -> List[Any]:
        """그룹별 전략 가져오기"""
        return [self.strategies[name] for name in self.strategy_groups.get(group_type, [])]
    
    def get_all_strategies(self) -> Dict[str, Any]:
        """모든 전략 가져오기"""
        return self.strategies
    
    def get_strategy_groups(self) -> Dict[str, List[str]]:
        """전략 그룹 가져오기"""
        return dict(self.strategy_groups)
    
    def validate_strategies(self) -> Dict[str, bool]:
        """전략 유효성 검증"""
        results = {}
        
        for name, strategy in self.strategies.items():
            results[name] = strategy.validate_config()
        
        return results
    
    def get_total_investment(self) -> float:
        """총 투자금 계산"""
        return sum(strategy.initial_capital for strategy in self.strategies.values())
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            name: strategy.get_info()
            for name, strategy in self.strategies.items()
        }
