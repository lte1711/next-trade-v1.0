"""
기본 전략 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseStrategy(ABC):
    """기본 전략 클래스"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.symbol = config.get("symbol", "")
        self.strategy_type = config.get("type", "unknown")
        self.initial_capital = config.get("initial_capital", 0.0)
        self.stop_loss = config.get("stop_loss", -0.1)
        self.leverage = config.get("leverage", 1.0)
        self.target_return = config.get("target_return", 0.1)
        self.profit_target = config.get("profit_target", 0.05)
        self.algorithm = config.get("algorithm", "Basic")
    
    @abstractmethod
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        """수익률 계산 (추상 메서드)"""
        pass
    
    def apply_risk_management(self, daily_return: float) -> float:
        """리스크 관리 적용"""
        # 손절 체크
        if daily_return <= self.stop_loss / 365:
            return self.stop_loss / 365
        
        # 익절 체크
        if daily_return >= self.profit_target / 365:
            return self.profit_target / 365
        
        return daily_return
    
    def get_leveraged_return(self, daily_return: float) -> float:
        """레버리지 적용 수익률"""
        return daily_return * self.leverage
    
    def validate_config(self) -> bool:
        """설정 유효성 검증"""
        required_fields = ["symbol", "type", "initial_capital", "stop_loss", "leverage", "target_return", "profit_target"]
        
        for field in required_fields:
            if field not in self.config:
                return False
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            "name": self.name,
            "symbol": self.symbol,
            "type": self.strategy_type,
            "algorithm": self.algorithm,
            "initial_capital": self.initial_capital,
            "leverage": self.leverage,
            "stop_loss": self.stop_loss,
            "profit_target": self.profit_target,
            "target_return": self.target_return
        }
