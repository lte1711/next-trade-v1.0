#!/usr/bin/env python3
"""
평균 회귀 전략 (Mean Reversion Strategy)
가격이 평균에서 크게 벗어났을 때 평균으로 회귀할 것이라는 가정에 기반한 전략
"""

from typing import Dict, Any, List
from strategies.base_strategy import BaseStrategy
from utils.indicators import calculate_bollinger_bands, calculate_rsi, calculate_stochastic


class MeanReversionV1(BaseStrategy):
    """평균 회귀 전략 v1.0"""
    
    def __init__(self):
        super().__init__()
        self.name = "mean_reversion_v1"
        self.description = "평균 회귀 기반 매매 전략"
        self.params = {
            "take_profit_pct": 0.010,
            "stop_loss_pct": 0.005,
            "rsi_overbought": 70.0,
            "rsi_oversold": 30.0,
            "stoch_overbought": 80.0,
            "stoch_oversold": 20.0,
            "bb_period": 20,
            "bb_std_dev": 2.0
        }
    
    def calculate_indicators(self, closes: List[float], highs: List[float], lows: List[float]) -> Dict[str, float]:
        """평균 회귀 관련 지표 계산"""
        try:
            # 볼린저 밴드 계산
            upper_band, middle_band, lower_band = calculate_bollinger_bands(
                closes, self.params["bb_period"], self.params["bb_std_dev"]
            )
            
            # RSI 계산
            rsi = calculate_rsi(closes, 14)
            
            # 스토캐스틱 오실레이터 계산
            if len(highs) >= 14 and len(lows) >= 14:
                k_percent, d_percent = calculate_stochastic(highs, lows, closes, 14, 3)
            else:
                k_percent, d_percent = 50.0, 50.0
            
            # 밴드 위치 비율 계산
            band_position = (closes[-1] - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
            
            return {
                "upper_band": upper_band,
                "middle_band": middle_band,
                "lower_band": lower_band,
                "rsi": rsi,
                "k_percent": k_percent,
                "d_percent": d_percent,
                "band_position": band_position
            }
        except Exception as e:
            return {
                "upper_band": 0,
                "middle_band": 0,
                "lower_band": 0,
                "rsi": 50.0,
                "k_percent": 50.0,
                "d_percent": 50.0,
                "band_position": 0.5
            }
    
    def generate_signal(self, symbol: str, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Dict[str, Any]:
        """평균 회귀 신호 생성"""
        try:
            if len(closes) < 20:
                return self._create_hold_signal(symbol)
            
            indicators = self.calculate_indicators(closes, highs, lows)
            current_price = closes[-1]
            
            # 과매도 조건 확인 (LONG 신호)
            oversold_signals = 0
            
            # RSI 과매도
            if indicators["rsi"] < self.params["rsi_oversold"]:
                oversold_signals += 1
            
            # 스토캐스틱 과매도
            if indicators["k_percent"] < self.params["stoch_oversold"]:
                oversold_signals += 1
            
            # 볼린저 하단 밴드 근접
            if indicators["band_position"] < 0.1:  # 하단 10% 이내
                oversold_signals += 1
            
            # 과매도 조건 충족 시 LONG 신호
            if oversold_signals >= 2:
                signal_score = self._calculate_mean_reversion_score(
                    indicators["rsi"], indicators["k_percent"], indicators["band_position"], "oversold"
                )
                return {
                    "symbol": symbol,
                    "strategy_id": self.name,
                    "signal": "LONG",
                    "signal_score": signal_score,
                    "entry_price": current_price,
                    "take_profit": indicators["middle_band"],  # 평균으로 회귀
                    "stop_loss": current_price * (1 - self.params["stop_loss_pct"]),
                    "confidence": min(signal_score / 10, 1.0),
                    "reason": f"과매도 조건 충족 (RSI: {indicators['rsi']:.1f}, K: {indicators['k_percent']:.1f}, 밴드 위치: {indicators['band_position']:.2f})"
                }
            
            # 과매수 조건 확인 (SHORT 신호)
            overbought_signals = 0
            
            # RSI 과매수
            if indicators["rsi"] > self.params["rsi_overbought"]:
                overbought_signals += 1
            
            # 스토캐스틱 과매수
            if indicators["k_percent"] > self.params["stoch_overbought"]:
                overbought_signals += 1
            
            # 볼린저 상단 밴드 근접
            if indicators["band_position"] > 0.9:  # 상단 10% 이내
                overbought_signals += 1
            
            # 과매수 조건 충족 시 SHORT 신호
            if overbought_signals >= 2:
                signal_score = self._calculate_mean_reversion_score(
                    indicators["rsi"], indicators["k_percent"], indicators["band_position"], "overbought"
                )
                return {
                    "symbol": symbol,
                    "strategy_id": self.name,
                    "signal": "SHORT",
                    "signal_score": signal_score,
                    "entry_price": current_price,
                    "take_profit": indicators["middle_band"],  # 평균으로 회귀
                    "stop_loss": current_price * (1 + self.params["stop_loss_pct"]),
                    "confidence": min(signal_score / 10, 1.0),
                    "reason": f"과매수 조건 충족 (RSI: {indicators['rsi']:.1f}, K: {indicators['k_percent']:.1f}, 밴드 위치: {indicators['band_position']:.2f})"
                }
            
            # 중립 구간 (HOLD 신호)
            else:
                return self._create_hold_signal(symbol)
                
        except Exception as e:
            return self._create_hold_signal(symbol)
    
    def _calculate_mean_reversion_score(self, rsi: float, k_percent: float, band_position: float, condition: str) -> float:
        """평균 회귀 강도 계산"""
        if condition == "oversold":
            # 과매도 강도 계산 (낮을수록 강한 과매도)
            rsi_strength = (self.params["rsi_oversold"] - rsi) / self.params["rsi_oversold"]
            k_strength = (self.params["stoch_oversold"] - k_percent) / self.params["stoch_oversold"]
            band_strength = (0.1 - band_position) / 0.1 if band_position < 0.1 else 0
        else:  # overbought
            # 과매수 강도 계산 (높을수록 강한 과매수)
            rsi_strength = (rsi - self.params["rsi_overbought"]) / (100 - self.params["rsi_overbought"])
            k_strength = (k_percent - self.params["stoch_overbought"]) / (100 - self.params["stoch_overbought"])
            band_strength = (band_position - 0.9) / 0.1 if band_position > 0.9 else 0
        
        # 음수값 방지
        rsi_strength = max(0, rsi_strength)
        k_strength = max(0, k_strength)
        band_strength = max(0, band_strength)
        
        # 종합 점수 계산
        total_score = (rsi_strength + k_strength + band_strength) * 10 / 3
        return min(total_score, 10)
    
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
            "reason": "평균 회귀 조건 미충족"
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
