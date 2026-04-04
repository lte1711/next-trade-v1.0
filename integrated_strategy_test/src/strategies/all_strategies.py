"""
모든 전략 통합 모듈
"""

import random
from typing import Dict, Any, List

from .base_strategy import BaseStrategy

class ConservativeStrategy(BaseStrategy):
    """보수적 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 상황에 따른 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.2
        elif sentiment == "bearish":
            trend_multiplier = 0.8
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * trend_multiplier + random.gauss(0, 0.001)
        return self.apply_risk_management(daily_return)

class GrowthStrategy(BaseStrategy):
    """성장 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 상황에 따른 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.5
        elif sentiment == "bearish":
            trend_multiplier = 0.6
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * trend_multiplier + random.gauss(0, 0.002)
        return self.apply_risk_management(daily_return)

class VolatilityStrategy(BaseStrategy):
    """변동성 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 변동성 기반 조정
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        volatility = symbol_data.get("volatility", 5.0) / 100
        vol_factor = volatility
        
        daily_return = base_return * (1 + vol_factor) + random.gauss(0, 0.003)
        return self.apply_risk_management(daily_return)

class MomentumStrategy(BaseStrategy):
    """모멘텀 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 가격 변동 기반 모멘텀
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        price_change = symbol_data.get("change", 0.0)
        
        momentum_factor = 1.2 if price_change > 0 else 0.8
        
        # 시장 상황 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.3
        elif sentiment == "bearish":
            trend_multiplier = 0.7
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * momentum_factor * trend_multiplier + random.gauss(0, 0.003)
        return self.apply_risk_management(daily_return)

class UltraAggressiveStrategy(BaseStrategy):
    """초공격적 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 상황에 따른 공격적 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.8
        elif sentiment == "bearish":
            trend_multiplier = 0.4
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * trend_multiplier * 1.5 + random.gauss(0, 0.004)
        return self.apply_risk_management(daily_return)

class HighGrowthStrategy(BaseStrategy):
    """고성장 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 상황에 따른 고성장 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 2.0
        elif sentiment == "bearish":
            trend_multiplier = 0.5
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * trend_multiplier * 1.8 + random.gauss(0, 0.005)
        return self.apply_risk_management(daily_return)

class MLMomentumStrategy(BaseStrategy):
    """머신러닝 모멘텀 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 가격 변동 기반 머신러닝 모멘텀
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        price_change = symbol_data.get("change", 0.0)
        
        momentum_factor = 1.3 if price_change > 2 else 0.7
        
        # 시장 상황 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.4
        elif sentiment == "bearish":
            trend_multiplier = 0.6
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * momentum_factor * trend_multiplier + random.gauss(0, 0.002)
        return self.apply_risk_management(daily_return)

class StatisticalArbitrageStrategy(BaseStrategy):
    """통계적 차익거래 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 통계적 차익거래는 시장 상황에 덜 민감
        daily_return = base_return * 0.7 + random.gauss(0, 0.001)
        return self.apply_risk_management(daily_return)

class VolatilityArbitrageStrategy(BaseStrategy):
    """변동성 차익 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 변동성 기반 차익
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        volatility = symbol_data.get("volatility", 5.0) / 100
        vol_factor = volatility
        
        # 변동성 수준 조정
        volatility_level = market_data.get("market_conditions", {}).get("volatility_level", "low")
        volatility_multiplier = 1.3 if volatility_level == "high" else 1.0
        
        daily_return = base_return * (1 + vol_factor * volatility_multiplier * 1.5) + random.gauss(0, 0.004)
        return self.apply_risk_management(daily_return)

class MeanReversionStrategy(BaseStrategy):
    """평균 회귀 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 가격 변동 기반 평균 회귀
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        price_change = symbol_data.get("change", 0.0)
        
        reversion_factor = -0.6 if price_change > 3 else 0.4
        
        daily_return = base_return * (1 + reversion_factor * 0.4) + random.gauss(0, 0.002)
        return self.apply_risk_management(daily_return)

class MarketMakingStrategy(BaseStrategy):
    """시장 메이킹 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 메이킹은 안정적 수익
        daily_return = base_return * 0.6 + random.gauss(0, 0.001)
        return self.apply_risk_management(daily_return)

class TriangularArbitrageStrategy(BaseStrategy):
    """삼각 차익거래 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 삼각 차익거래는 안정적 수익
        daily_return = base_return * 0.5 + random.gauss(0, 0.001)
        return self.apply_risk_management(daily_return)

class EnhancedStrategy(BaseStrategy):
    """향상된 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 상황에 따른 향상된 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.4
        elif sentiment == "bearish":
            trend_multiplier = 0.6
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * trend_multiplier * 1.2 + random.gauss(0, 0.003)
        return self.apply_risk_management(daily_return)

class ExtremeLeverageStrategy(BaseStrategy):
    """초극단 레버리지 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 상황에 따른 초극단 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 2.5
        elif sentiment == "bearish":
            trend_multiplier = 0.3
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * trend_multiplier * 2.0 + random.gauss(0, 0.006)
        return self.apply_risk_management(daily_return)

class PumpScalpingStrategy(BaseStrategy):
    """펌핑 스캘핑 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 시장 이벤트 기반 펌핑
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        market_events = symbol_data.get("market_events", [])
        
        pump_factor = 2.5 if market_events else 1.0
        
        # 시장 상황 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.5
        elif sentiment == "bearish":
            trend_multiplier = 0.5
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * pump_factor * trend_multiplier + random.gauss(0, 0.008)
        return self.apply_risk_management(daily_return)

class MemeExplosionStrategy(BaseStrategy):
    """펨코인 폭발 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 펨코인 이벤트 기반 폭발
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        market_events = symbol_data.get("market_events", [])
        
        explosion_factor = 3.0 if market_events and "Meme" in str(market_events) else 1.0
        
        # 시장 상황 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 1.8
        elif sentiment == "bearish":
            trend_multiplier = 0.4
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * explosion_factor * trend_multiplier + random.gauss(0, 0.010)
        return self.apply_risk_management(daily_return)

class UltraScalpingStrategy(BaseStrategy):
    """초단기 스캘핑 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 초단기 스캘핑
        daily_return = base_return * 1.8 + random.gauss(0, 0.007)
        return self.apply_risk_management(daily_return)

class ExtremeMomentumStrategy(BaseStrategy):
    """극단적 모멘텀 전략"""
    
    def calculate_return(self, market_data: Dict[str, Any]) -> float:
        base_return = self.target_return / 365
        
        # 가격 변동 기반 극단적 모멘텀
        symbol_data = market_data.get("symbols", {}).get(self.symbol, {})
        price_change = symbol_data.get("change", 0.0)
        
        momentum_factor = 4.0 if price_change > 5 else 2.0
        
        # 시장 상황 조정
        sentiment = market_data.get("market_conditions", {}).get("overall_sentiment", "neutral")
        if sentiment == "bullish":
            trend_multiplier = 2.0
        elif sentiment == "bearish":
            trend_multiplier = 0.3
        else:
            trend_multiplier = 1.0
        
        daily_return = base_return * momentum_factor * trend_multiplier + random.gauss(0, 0.012)
        return self.apply_risk_management(daily_return)

# 전략 클래스 매핑
STRATEGY_CLASSES = {
    "conservative": ConservativeStrategy,
    "growth": GrowthStrategy,
    "volatility": VolatilityStrategy,
    "momentum": MomentumStrategy,
    "ultra_aggressive": UltraAggressiveStrategy,
    "high_growth": HighGrowthStrategy,
    "ml_momentum": MLMomentumStrategy,
    "statistical_arbitrage": StatisticalArbitrageStrategy,
    "volatility_arbitrage": VolatilityArbitrageStrategy,
    "mean_reversion": MeanReversionStrategy,
    "market_making": MarketMakingStrategy,
    "triangular_arbitrage": TriangularArbitrageStrategy,
    "enhanced": EnhancedStrategy,
    "extreme_leverage": ExtremeLeverageStrategy,
    "pump_scalping": PumpScalpingStrategy,
    "meme_explosion": MemeExplosionStrategy,
    "ultra_scalping": UltraScalpingStrategy,
    "extreme_momentum": ExtremeMomentumStrategy
}

def create_strategy(name: str, config: Dict[str, Any]) -> BaseStrategy:
    """전략 인스턴스 생성"""
    strategy_type = config.get("type", "conservative")
    
    if strategy_type not in STRATEGY_CLASSES:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    strategy_class = STRATEGY_CLASSES[strategy_type]
    return strategy_class(name, config)
