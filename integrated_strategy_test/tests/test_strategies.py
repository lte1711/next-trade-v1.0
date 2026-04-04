"""
전략 테스트
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.strategies.all_strategies import create_strategy, STRATEGY_CLASSES
from src.strategies.strategy_manager import StrategyManager

class TestStrategies:
    """전략 테스트 클래스"""
    
    def test_strategy_creation(self):
        """전략 생성 테스트"""
        
        # 보수적 전략 생성
        config = {
            "symbol": "BTCUSDT",
            "type": "conservative",
            "initial_capital": 1000.0,
            "stop_loss": -0.05,
            "leverage": 2.0,
            "target_return": 0.15,
            "profit_target": 0.10
        }
        
        strategy = create_strategy("test_conservative", config)
        
        assert strategy.name == "test_conservative"
        assert strategy.symbol == "BTCUSDT"
        assert strategy.strategy_type == "conservative"
        assert strategy.initial_capital == 1000.0
        assert strategy.leverage == 2.0
    
    def test_strategy_validation(self):
        """전략 설정 검증 테스트"""
        
        # 유효한 설정
        valid_config = {
            "symbol": "ETHUSDT",
            "type": "growth",
            "initial_capital": 500.0,
            "stop_loss": -0.08,
            "leverage": 3.0,
            "target_return": 0.25,
            "profit_target": 0.20
        }
        
        strategy = create_strategy("test_growth", valid_config)
        assert strategy.validate_config() == True
        
        # 유효하지 않은 설정
        invalid_config = {
            "symbol": "SOLUSDT",
            "type": "growth",
            # initial_capital 누락
            "stop_loss": -0.08,
            "leverage": 3.0,
            "target_return": 0.25,
            "profit_target": 0.20
        }
        
        strategy = create_strategy("test_invalid", invalid_config)
        assert strategy.validate_config() == False
    
    def test_all_strategy_types(self):
        """모든 전략 타입 테스트"""
        
        base_config = {
            "symbol": "DOGEUSDT",
            "initial_capital": 200.0,
            "stop_loss": -0.10,
            "leverage": 2.0,
            "target_return": 0.20,
            "profit_target": 0.15
        }
        
        for strategy_type in STRATEGY_CLASSES.keys():
            config = base_config.copy()
            config["type"] = strategy_type
            
            try:
                strategy = create_strategy(f"test_{strategy_type}", config)
                assert strategy.strategy_type == strategy_type
                assert strategy.validate_config() == True
            except Exception as e:
                pytest.fail(f"Strategy type {strategy_type} failed: {e}")
    
    def test_strategy_manager(self):
        """전략 관리자 테스트"""
        
        manager = StrategyManager()
        strategies = manager.load_all_strategies()
        
        # 전략 수 확인
        assert len(strategies) > 0
        
        # 그룹별 분류 확인
        groups = manager.get_strategy_groups()
        assert len(groups) > 0
        
        # 총 투자금 확인
        total_investment = manager.get_total_investment()
        assert total_investment > 0
        
        # 전략 정보 확인
        strategy_info = manager.get_strategy_info()
        assert len(strategy_info) == len(strategies)
    
    def test_strategy_return_calculation(self):
        """전략 수익률 계산 테스트"""
        
        # 테스트 시장 데이터
        market_data = {
            "date": "2025-04-02",
            "market_phase": "bull_run",
            "symbols": {
                "BTCUSDT": {
                    "price": 65000,
                    "change": 2.5,
                    "volatility": 5.0,
                    "market_events": []
                }
            },
            "market_conditions": {
                "overall_sentiment": "bullish",
                "volatility_level": "high"
            }
        }
        
        config = {
            "symbol": "BTCUSDT",
            "type": "conservative",
            "initial_capital": 1000.0,
            "stop_loss": -0.05,
            "leverage": 2.0,
            "target_return": 0.15,
            "profit_target": 0.10
        }
        
        strategy = create_strategy("test_return", config)
        
        # 수익률 계산
        daily_return = strategy.calculate_return(market_data)
        
        # 결과 검증
        assert isinstance(daily_return, float)
        assert -1.0 <= daily_return <= 1.0  # 합리적인 범위
        
        # 레버리지 적용
        leveraged_return = strategy.get_leveraged_return(daily_return)
        assert isinstance(leveraged_return, float)
        
        # 리스크 관리 적용
        managed_return = strategy.apply_risk_management(leveraged_return)
        assert isinstance(managed_return, float)

if __name__ == "__main__":
    pytest.main([__file__])
