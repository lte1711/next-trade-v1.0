#!/usr/bin/env python3
"""
멀티 전략 관리자
여러 전략을 관리하고 신호를 통합하는 중앙 관리자
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone
from strategies.base_strategy import BaseStrategy
from strategies.momentum_intraday_v1 import MomentumIntradayV1
from strategies.trend_following_v1 import TrendFollowingV1
from strategies.volatility_breakout_v1 import VolatilityBreakoutV1
from strategies.mean_reversion_v1 import MeanReversionV1


class MultiStrategyManager:
    """멀티 전략 관리자"""
    
    def __init__(self, config_path: str = "config/strategies.json"):
        self.config_path = Path(config_path)
        self.strategies: Dict[str, BaseStrategy] = {}
        self.config: Dict[str, Any] = {}
        self.market_regime = "default"
        self.performance_cache = {}
        self.load_config()
        self.initialize_strategies()
    
    def load_config(self) -> None:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "strategies": {
                "momentum_intraday_v1": {"enabled": True, "weight": 0.25},
                "trend_following_v1": {"enabled": True, "weight": 0.75}
            },
            "market_regimes": {
                "default": {
                    "momentum_intraday_v1": 0.25,
                    "trend_following_v1": 0.75
                }
            }
        }
    
    def initialize_strategies(self) -> None:
        """전략 초기화"""
        strategy_classes = {
            "momentum_intraday_v1": MomentumIntradayV1,
            "trend_following_v1": TrendFollowingV1,
            "volatility_breakout_v1": VolatilityBreakoutV1,
            "mean_reversion_v1": MeanReversionV1
        }
        
        for strategy_id, strategy_config in self.config.get("strategies", {}).items():
            if strategy_config.get("enabled", False):
                if strategy_id in strategy_classes:
                    strategy = strategy_classes[strategy_id]()
                    self.strategies[strategy_id] = strategy
    
    def detect_market_regime(self, market_data: Dict[str, Any]) -> str:
        """시장 레짐 감지 (단순화된 버전)"""
        volatility = float(market_data.get("volatility", 0.02))
        trend_strength = float(market_data.get("trend_strength", 0.5))
        
        if volatility > 0.03:
            return "volatile"
        elif trend_strength > 0.7:
            return "trending"
        elif trend_strength < 0.3:
            return "ranging"
        else:
            return "default"
    
    def get_strategy_weights(self, market_regime: str = None) -> Dict[str, float]:
        """전략 가중치 가져오기"""
        if market_regime is None:
            market_regime = self.market_regime
        
        regime_weights = self.config.get("market_regimes", {}).get(market_regime, {})
        default_weights = self.config.get("market_regimes", {}).get("default", {})
        
        # 레짐 가중치와 기본 가중치 병합
        weights = {**default_weights, **regime_weights}
        
        # 활성화된 전략만 필터링
        active_weights = {}
        for strategy_id, weight in weights.items():
            if strategy_id in self.strategies:
                active_weights[strategy_id] = weight
        
        return active_weights
    
    def generate_individual_signals(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Dict[str, Any]]:
        """개별 전략 신호 생성"""
        signals = {}
        
        for strategy_id, strategy in self.strategies.items():
            try:
                signal_data = strategy.evaluate(symbol, closes, volumes)
                signals[strategy_id] = signal_data
            except Exception as e:
                # 오류 발생 시 HOLD 신호
                signals[strategy_id] = {
                    "symbol": symbol,
                    "strategy_id": strategy_id,
                    "signal": "HOLD",
                    "signal_score": 0.0,
                    "error": str(e)
                }
        
        return signals
    
    def aggregate_signals(self, individual_signals: Dict[str, Dict[str, Any]], market_regime: str = None) -> Dict[str, Any]:
        """신호 통합"""
        if not individual_signals:
            return {"signal": "HOLD", "confidence": 0.0, "contributing_strategies": []}
        
        weights = self.get_strategy_weights(market_regime)
        
        # 신호 가중치 계산
        long_weight = 0.0
        short_weight = 0.0
        hold_weight = 0.0
        contributing_strategies = []
        
        for strategy_id, signal_data in individual_signals.items():
            signal = signal_data.get("signal", "HOLD")
            score = signal_data.get("signal_score", 0.0)
            weight = weights.get(strategy_id, 0.0)
            
            if signal == "LONG":
                long_weight += weight * score
                contributing_strategies.append(strategy_id)
            elif signal == "SHORT":
                short_weight += weight * score
                contributing_strategies.append(strategy_id)
            else:
                hold_weight += weight
        
        # 최종 신호 결정
        if long_weight > short_weight and long_weight > hold_weight:
            final_signal = "LONG"
            confidence = long_weight
        elif short_weight > long_weight and short_weight > hold_weight:
            final_signal = "SHORT"
            confidence = short_weight
        else:
            final_signal = "HOLD"
            confidence = hold_weight
        
        return {
            "signal": final_signal,
            "confidence": round(confidence, 6),
            "contributing_strategies": contributing_strategies,
            "individual_signals": individual_signals,
            "weights_used": weights
        }
    
    def evaluate_strategies(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """전체 전략 평가"""
        # 시장 데이터 생성 (단순화)
        market_data = {
            "volatility": 0.02,  # 단순화된 값
            "trend_strength": 0.5  # 단순화된 값
        }
        
        # 시장 레짐 감지
        self.market_regime = self.detect_market_regime(market_data)
        
        # 개별 신호 생성
        individual_signals = self.generate_individual_signals(symbol, closes, volumes)
        
        # 신호 통합
        aggregated_signal = self.aggregate_signals(individual_signals, self.market_regime)
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_regime": self.market_regime,
            "aggregated_signal": aggregated_signal,
            "individual_signals": individual_signals,
            "active_strategies": list(self.strategies.keys())
        }
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """전략 성과 정보"""
        return {
            "total_strategies": len(self.strategies),
            "active_strategies": list(self.strategies.keys()),
            "current_market_regime": self.market_regime,
            "strategy_weights": self.get_strategy_weights(),
            "config_path": str(self.config_path)
        }
    
    def update_strategy_performance(self, strategy_id: str, performance_metrics: Dict[str, float]) -> None:
        """전략 성과 업데이트"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].update_performance(performance_metrics)
            self.performance_cache[strategy_id] = performance_metrics
