#!/usr/bin/env python3
"""
횡보장 전략 계산식 모듈
인터넷 자료 기반 실전 전략 구현
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class SidewaysMarketStrategy:
    """횡보장 전략 계산식 클래스"""
    
    def __init__(self):
        self.name = "횡보장 전략"
        self.description = "ADX 기반 시장 판별 + 다중 횡보장 전략"
        
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        ADX (Average Directional Index) 계산
        ADX < 20: 횡보장
        ADX > 25: 추세장
        """
        # True Range 계산
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        
        # +DM, -DM 계산
        up_move = df['high'] - df['high'].shift(1)
        down_move = df['low'].shift(1) - df['low']
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed 계산
        atr = pd.Series(tr).rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)
        
        # ADX 계산
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = pd.Series(dx).rolling(window=period).mean()
        
        return adx
    
    def detect_market_condition(self, df: pd.DataFrame, adx_period: int = 14) -> str:
        """
        시장 상태 판별
        """
        adx = self.calculate_adx(df, adx_period)
        current_adx = adx.iloc[-1] if not adx.empty else 0
        
        if current_adx < 20:
            return "RANGING"
        elif current_adx > 25:
            return "TRENDING"
        else:
            return "NEUTRAL"
    
    def bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        볼린저 밴드 계산
        """
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'middle': sma,
            'upper': upper_band,
            'lower': lower_band,
            'bandwidth': (upper_band - lower_band) / sma
        }
    
    def rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) 계산
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def range_trading_strategy(self, df: pd.DataFrame, 
                              bb_period: int = 20, 
                              bb_std: float = 2,
                              rsi_period: int = 14,
                              rsi_overbought: float = 70,
                              rsi_oversold: float = 30) -> Dict:
        """
        레인지 트레이딩 전략 계산
        """
        if len(df) < bb_period:
            return {"signal": "NEUTRAL", "reason": "데이터 부족"}
        
        # 볼린저 밴드 계산
        bb = self.bollinger_bands(df, bb_period, bb_std)
        
        # RSI 계산
        rsi = self.rsi(df, rsi_period)
        
        current_price = df['close'].iloc[-1]
        current_bb_upper = bb['upper'].iloc[-1]
        current_bb_lower = bb['lower'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        # 시그널 생성 로직
        if current_price >= current_bb_upper and current_rsi >= rsi_overbought:
            return {
                "signal": "SELL",
                "price": current_price,
                "bb_upper": current_bb_upper,
                "bb_lower": current_bb_lower,
                "rsi": current_rsi,
                "reason": "과매수 + 저항선 도달",
                "confidence": 0.8
            }
        elif current_price <= current_bb_lower and current_rsi <= rsi_oversold:
            return {
                "signal": "BUY",
                "price": current_price,
                "bb_upper": current_bb_upper,
                "bb_lower": current_bb_lower,
                "rsi": current_rsi,
                "reason": "과매도 + 지지선 도달",
                "confidence": 0.8
            }
        else:
            return {
                "signal": "NEUTRAL",
                "price": current_price,
                "bb_upper": current_bb_upper,
                "bb_lower": current_bb_lower,
                "rsi": current_rsi,
                "reason": "횡보장 중간 구간",
                "confidence": 0.5
            }
    
    def grid_trading_strategy(self, df: pd.DataFrame,
                             grid_count: int = 10,
                             grid_range_pct: float = 0.05,
                             current_position: Optional[str] = None) -> Dict:
        """
        그리드 트레이딩 전략 계산
        """
        if len(df) < 20:
            return {"signal": "NEUTRAL", "reason": "데이터 부족"}
        
        current_price = df['close'].iloc[-1]
        
        # 최근 고가/저가 기반 그리드 범위 설정
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        
        # 동적 그리드 범위
        grid_upper = max(recent_high, current_price * (1 + grid_range_pct))
        grid_lower = min(recent_low, current_price * (1 - grid_range_pct))
        
        # 그리드 레벨 계산
        grid_levels = np.linspace(grid_lower, grid_upper, grid_count + 1)
        
        # 현재 가격 위치 확인
        current_grid_level = None
        for i in range(len(grid_levels) - 1):
            if grid_levels[i] <= current_price <= grid_levels[i + 1]:
                current_grid_level = i
                break
        
        if current_grid_level is None:
            return {"signal": "NEUTRAL", "reason": "그리드 범위 밖"}
        
        # 그리드 시그널 생성
        if current_position is None:
            # 초기 포지션 설정
            if current_grid_level < len(grid_levels) // 2:
                return {
                    "signal": "BUY",
                    "price": current_price,
                    "grid_level": current_grid_level,
                    "grid_upper": grid_upper,
                    "grid_lower": grid_lower,
                    "reason": f"그리드 하단 ({current_grid_level}/{grid_count})",
                    "confidence": 0.7
                }
            else:
                return {
                    "signal": "SELL",
                    "price": current_price,
                    "grid_level": current_grid_level,
                    "grid_upper": grid_upper,
                    "grid_lower": grid_lower,
                    "reason": f"그리드 상단 ({current_grid_level}/{grid_count})",
                    "confidence": 0.7
                }
        else:
            # 그리드 이동 시 신호
            if current_position == "LONG" and current_grid_level >= len(grid_levels) - 2:
                return {
                    "signal": "SELL",
                    "price": current_price,
                    "grid_level": current_grid_level,
                    "grid_upper": grid_upper,
                    "grid_lower": grid_lower,
                    "reason": "그리드 상단 도달 - 청산",
                    "confidence": 0.9
                }
            elif current_position == "SHORT" and current_grid_level <= 1:
                return {
                    "signal": "BUY",
                    "price": current_price,
                    "grid_level": current_grid_level,
                    "grid_upper": grid_upper,
                    "grid_lower": grid_lower,
                    "reason": "그리드 하단 도달 - 청산",
                    "confidence": 0.9
                }
            else:
                return {
                    "signal": "HOLD",
                    "price": current_price,
                    "grid_level": current_grid_level,
                    "grid_upper": grid_upper,
                    "grid_lower": grid_lower,
                    "reason": f"그리드 유지 ({current_grid_level}/{grid_count})",
                    "confidence": 0.6
                }
    
    def mean_reversion_strategy(self, df: pd.DataFrame,
                               lookback_period: int = 20,
                               z_threshold: float = 2.0) -> Dict:
        """
        평균 회귀 전략 계산 (Z-Score 기반)
        """
        if len(df) < lookback_period:
            return {"signal": "NEUTRAL", "reason": "데이터 부족"}
        
        # 이동평균 및 표준편차 계산
        mean_price = df['close'].rolling(window=lookback_period).mean()
        std_price = df['close'].rolling(window=lookback_period).std()
        
        current_price = df['close'].iloc[-1]
        current_mean = mean_price.iloc[-1]
        current_std = std_price.iloc[-1]
        
        # Z-Score 계산
        if current_std > 0:
            z_score = (current_price - current_mean) / current_std
        else:
            z_score = 0
        
        # 평균 회귀 시그널
        if z_score > z_threshold:
            return {
                "signal": "SELL",
                "price": current_price,
                "mean_price": current_mean,
                "std_price": current_std,
                "z_score": z_score,
                "reason": f"평균 대비 {z_threshold:.1f}σ 이상 상승",
                "confidence": min(0.9, abs(z_score) / z_threshold * 0.8)
            }
        elif z_score < -z_threshold:
            return {
                "signal": "BUY",
                "price": current_price,
                "mean_price": current_mean,
                "std_price": current_std,
                "z_score": z_score,
                "reason": f"평균 대비 {z_threshold:.1f}σ 이상 하락",
                "confidence": min(0.9, abs(z_score) / z_threshold * 0.8)
            }
        else:
            return {
                "signal": "NEUTRAL",
                "price": current_price,
                "mean_price": current_mean,
                "std_price": current_std,
                "z_score": z_score,
                "reason": f"평균 근접 (Z-Score: {z_score:.2f})",
                "confidence": 0.5
            }
    
    def whipsaw_filter(self, df: pd.DataFrame,
                       volume_threshold: float = 1.5,
                       price_change_threshold: float = 0.02) -> bool:
        """
        휩쏘 필터링
        """
        if len(df) < 5:
            return False
        
        # 거래량 확인
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].tail(20).mean()
        
        # 가격 변화율 확인
        price_change = abs(df['close'].pct_change().iloc[-1])
        
        # 휩쏘 위험 신호
        low_volume = current_volume < avg_volume * volume_threshold
        high_volatility = price_change > price_change_threshold
        
        # 휩쏘 가능성이 높으면 True 반환
        return low_volume and high_volatility
    
    def adaptive_sideways_strategy(self, df: pd.DataFrame,
                                  strategy_preference: str = "RANGE") -> Dict:
        """
        적응형 횡보장 전략
        """
        # 시장 상태 판별
        market_condition = self.detect_market_condition(df)
        
        if market_condition != "RANGING":
            return {
                "signal": "NEUTRAL",
                "market_condition": market_condition,
                "reason": f"시장 상태: {market_condition} (횡보장 아님)",
                "confidence": 0.3
            }
        
        # 휩쏘 필터링
        if self.whipsaw_filter(df):
            return {
                "signal": "NEUTRAL",
                "market_condition": market_condition,
                "reason": "휩쏘 위험 감지",
                "confidence": 0.2
            }
        
        # 전략 선택 및 실행
        if strategy_preference == "RANGE":
            result = self.range_trading_strategy(df)
        elif strategy_preference == "GRID":
            result = self.grid_trading_strategy(df)
        elif strategy_preference == "MEAN_REVERSION":
            result = self.mean_reversion_strategy(df)
        else:
            # 자동 전략 선택
            range_result = self.range_trading_strategy(df)
            grid_result = self.grid_trading_strategy(df)
            mean_result = self.mean_reversion_strategy(df)
            
            # 가장 신뢰도 높은 전략 선택
            results = [range_result, grid_result, mean_result]
            result = max(results, key=lambda x: x.get('confidence', 0))
        
        result["market_condition"] = market_condition
        return result
    
    def calculate_position_size(self, df: pd.DataFrame,
                               risk_per_trade: float = 0.02,
                               account_balance: float = 10000) -> float:
        """
        포지션 사이징 계산
        """
        if len(df) < 20:
            return 0
        
        # ATR 기반 변동성 계산
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = tr.rolling(window=14).mean().iloc[-1]
        
        current_price = df['close'].iloc[-1]
        
        # 리스크 기반 포지션 사이즈
        if atr > 0:
            stop_loss_distance = atr * 2  # 2x ATR 손절
            position_size = (account_balance * risk_per_trade) / stop_loss_distance
            position_value = position_size * current_price
            
            # 최대 포지션 제한 (계정의 20%)
            max_position = account_balance * 0.2
            position_value = min(position_value, max_position)
            
            return position_value / current_price
        
        return 0

# 사용 예시
def example_usage():
    """사용 예시"""
    strategy = SidewaysMarketStrategy()
    
    # 샘플 데이터 생성
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    prices = np.random.normal(100, 2, 100).cumsum()
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.normal(0, 0.5, 100),
        'high': prices + np.random.normal(0, 1, 100),
        'low': prices - np.random.normal(0, 1, 100),
        'close': prices,
        'volume': np.random.normal(1000, 200, 100)
    })
    
    # 시장 상태 판별
    market_condition = strategy.detect_market_condition(df)
    print(f"시장 상태: {market_condition}")
    
    # 적응형 전략 실행
    result = strategy.adaptive_sideways_strategy(df)
    print(f"전략 결과: {result}")
    
    # 포지션 사이징
    position_size = strategy.calculate_position_size(df)
    print(f"포지션 사이즈: {position_size:.2f}")

if __name__ == "__main__":
    example_usage()
