#!/usr/bin/env python3
"""
추세 추종 전략 v1
MACD, 이동평균, ADX를 사용한 추세 추종 전략
"""

from typing import Any, Dict, List
from .base_strategy import BaseStrategy
from utils.indicators import calculate_macd, calculate_ema, calculate_adx


class TrendFollowingV1(BaseStrategy):
    """추세 추종 전략 v1"""
    
    def __init__(self):
        super().__init__("trend_following_v1", "추세 추종 전략 v1")
        self.strategy_unit = "TREND_FOLLOWING"
        self.take_profit_pct = 0.015
        self.stop_loss_pct = 0.008
    
    def calculate_indicators(self, closes: List[float], volumes: List[float]) -> Dict[str, float]:
        """기술적 지표 계산"""
        if not self.validate_data(closes, volumes):
            return {}
        
        # MACD 계산
        macd_line, signal_line, histogram = calculate_macd(closes, 12, 26, 9)
        
        # 이동평균 계산
        ema_20 = calculate_ema(closes, 20)
        ema_50 = calculate_ema(closes, 50)
        
        # ADX 계산
        adx = calculate_adx(closes, 14)
        
        # 현재 가격
        current_price = closes[-1]
        
        return {
            "close": current_price,
            "macd_line": macd_line,
            "signal_line": signal_line,
            "macd_histogram": histogram,
            "ema_20": ema_20,
            "ema_50": ema_50,
            "adx": adx,
            "volume": volumes[-1] if volumes else 0.0
        }
    
    def generate_signal(self, data: Dict[str, Any]) -> str:
        """신호 생성"""
        if not data:
            return "HOLD"
        
        macd_line = float(data.get("macd_line", 0))
        signal_line = float(data.get("signal_line", 0))
        macd_histogram = float(data.get("macd_histogram", 0))
        ema_20 = float(data.get("ema_20", 0))
        ema_50 = float(data.get("ema_50", 0))
        adx = float(data.get("adx", 0))
        current_price = float(data.get("close", 0))
        
        # 강한 추세 조건 (ADX > 25)
        if adx > 25:
            # 상승 추세
            if (macd_line > signal_line and 
                macd_histogram > 0 and 
                current_price > ema_20 and 
                ema_20 > ema_50):
                return "LONG"
            
            # 하락 추세
            elif (macd_line < signal_line and 
                  macd_histogram < 0 and 
                  current_price < ema_20 and 
                  ema_20 < ema_50):
                return "SHORT"
        
        return "HOLD"
    
    def evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """전략 평가 및 신호 생성"""
        market_data = self.calculate_indicators(closes, volumes)
        signal = self.generate_signal(market_data)
        
        # 신호 강도 계산
        signal_strength = 0.0
        if signal != "HOLD":
            adx = float(market_data.get("adx", 0))
            macd_hist = float(market_data.get("macd_histogram", 0))
            signal_strength = min(abs(adx) / 50.0 + abs(macd_hist) * 1000, 1.0)
        
        return {
            "symbol": symbol,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_unit": self.strategy_unit,
            "signal": signal,
            "signal_score": round(signal_strength, 6),
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
            **{k: round(float(v), 6) for k, v in market_data.items()}
        }
