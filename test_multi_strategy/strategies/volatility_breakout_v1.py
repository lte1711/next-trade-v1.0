#!/usr/bin/env python3
"""
변동성 돌파 전략 (Volatility Breakout Strategy)
변동성이 낮은 시장에서 가격이 특정 범위를 돌파할 때 매매 신호 생성
"""

from typing import Dict, Any, List
from strategies.base_strategy import BaseStrategy
from utils.indicators import calculate_bollinger_bands, calculate_atr


class VolatilityBreakoutV1(BaseStrategy):
    """변동성 돌파 전략 v1.0"""
    
    def __init__(self):
        super().__init__()
        self.name = "volatility_breakout_v1"
        self.description = "변동성 돌파 기반 매매 전략"
        self.params = {
            "take_profit_pct": 0.018,
            "stop_loss_pct": 0.009,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "atr_period": 14,
            "atr_multiplier": 1.5
        }
    
    def calculate_indicators(self, closes: List[float], highs: List[float], lows: List[float]) -> Dict[str, float]:
        """변동성 관련 지표 계산"""
        try:
            # 볼린저 밴드 계산
            upper_band, middle_band, lower_band = calculate_bollinger_bands(
                closes, self.params["bb_period"], self.params["bb_std_dev"]
            )
            
            # ATR 계산
            atr = calculate_atr(highs, lows, closes, self.params["atr_period"])
            
            # 변동성 비율 계산
            volatility_ratio = atr / closes[-1] if closes[-1] > 0 else 0
            
            # 밴드 폭 비율
            band_width = (upper_band - lower_band) / middle_band if middle_band > 0 else 0
            
            return {
                "upper_band": upper_band,
                "middle_band": middle_band,
                "lower_band": lower_band,
                "atr": atr,
                "volatility_ratio": volatility_ratio,
                "band_width": band_width
            }
        except Exception as e:
            return {
                "upper_band": 0,
                "middle_band": 0,
                "lower_band": 0,
                "atr": 0,
                "volatility_ratio": 0,
                "band_width": 0
            }
    
    def generate_signal(self, symbol: str, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Dict[str, Any]:
        """변동성 돌파 신호 생성"""
        try:
            if len(closes) < 20:
                return self._create_hold_signal(symbol)
            
            indicators = self.calculate_indicators(closes, highs, lows)
            current_price = closes[-1]
            
            # 변동성이 너무 낮은 경우 (신호 생성하지 않음)
            if indicators["volatility_ratio"] < 0.01:
                return self._create_hold_signal(symbol)
            
            # 상단 밴드 돌파 (LONG 신호)
            if current_price > indicators["upper_band"]:
                signal_score = self._calculate_breakout_score(
                    current_price, indicators["upper_band"], indicators["atr"]
                )
                return {
                    "symbol": symbol,
                    "strategy_id": self.name,
                    "signal": "LONG",
                    "signal_score": signal_score,
                    "entry_price": current_price,
                    "take_profit": current_price * (1 + self.params["take_profit_pct"]),
                    "stop_loss": current_price * (1 - self.params["stop_loss_pct"]),
                    "confidence": min(signal_score / 10, 1.0),
                    "reason": f"볼린저 상단 밴드 돌파 (가격: {current_price:.2f}, 밴드: {indicators['upper_band']:.2f})"
                }
            
            # 하단 밴드 돌파 (SHORT 신호)
            elif current_price < indicators["lower_band"]:
                signal_score = self._calculate_breakout_score(
                    indicators["lower_band"], current_price, indicators["atr"]
                )
                return {
                    "symbol": symbol,
                    "strategy_id": self.name,
                    "signal": "SHORT",
                    "signal_score": signal_score,
                    "entry_price": current_price,
                    "take_profit": current_price * (1 - self.params["take_profit_pct"]),
                    "stop_loss": current_price * (1 + self.params["stop_loss_pct"]),
                    "confidence": min(signal_score / 10, 1.0),
                    "reason": f"볼린저 하단 밴드 돌파 (가격: {current_price:.2f}, 밴드: {indicators['lower_band']:.2f})"
                }
            
            # 밴드 내부 (HOLD 신호)
            else:
                return self._create_hold_signal(symbol)
                
        except Exception as e:
            return self._create_hold_signal(symbol)
    
    def _calculate_breakout_score(self, breakout_level: float, current_price: float, atr: float) -> float:
        """돌파 강도 계산"""
        breakout_strength = abs(current_price - breakout_level) / atr if atr > 0 else 0
        return min(breakout_strength * 5, 10)
    
    def _create_hold_signal(self, symbol: str) -> Dict[str, Any]:
        """HOLD 신호 생성"""
        return {
            "symbol": symbol,
            "strategy_id": self.name,
            "signal": "HOLD",
            "signal_score": 0.0,
            "entry_price": 0,
            "take_profit": 0,
            "stop_loss": 0,
            "confidence": 0.0,
            "reason": "변동성 돌파 조건 미충족"
        }
    
    def evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """전략 평가 (BaseStrategy 인터페이스 구현)"""
        try:
            # highs와 lows가 없는 경우를 대비하여 closes에서 생성
            highs = closes.copy()
            lows = closes.copy()
            
            return self.generate_signal(symbol, closes, highs, lows, volumes)
        except Exception as e:
            return self._create_hold_signal(symbol)
