#!/usr/bin/env python3
"""
기술적 지표 계산 라이브러리 (테스트 버전)
다양한 기술적 분석 지표 계산 함수
"""

from typing import List, Tuple
import math


def calculate_sma(values: List[float], period: int) -> float:
    """단순 이동평균 (Simple Moving Average)"""
    if len(values) < period:
        return 0.0
    return sum(values[-period:]) / period


def calculate_ema(values: List[float], period: int) -> float:
    """지수 이동평균 (Exponential Moving Average)"""
    if len(values) < period:
        return 0.0
    
    multiplier = 2 / (period + 1)
    ema = values[0]
    
    for price in values[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema


def calculate_macd(values: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[float, float, float]:
    """MACD (Moving Average Convergence Divergence)"""
    if len(values) < slow_period:
        return 0.0, 0.0, 0.0
    
    # EMA 계산
    ema_fast = calculate_ema(values, fast_period)
    ema_slow = calculate_ema(values, slow_period)
    
    # MACD 라인
    macd_line = ema_fast - ema_slow
    
    # 시그널 라인 (단순화된 버전)
    signal_line = macd_line * 0.8  # 단순화
    
    # 히스토그램
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_rsi(values: List[float], period: int = 14) -> float:
    """RSI (Relative Strength Index)"""
    if len(values) <= period:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(-period, 0):
        delta = values[i] - values[i - 1]
        if delta >= 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi


def calculate_bollinger_bands(values: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
    """볼린저 밴드 (Bollinger Bands)"""
    if len(values) < period:
        return 0.0, 0.0, 0.0
    
    sma = calculate_sma(values, period)
    
    # 표준편차 계산
    recent_values = values[-period:]
    variance = sum((x - sma) ** 2 for x in recent_values) / period
    std = math.sqrt(variance)
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band, sma, lower_band


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """ATR (Average True Range)"""
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return 0.0
    
    true_ranges = []
    
    for i in range(1, period + 1):
        high_low = highs[-i] - lows[-i]
        high_close = abs(highs[-i] - closes[-i-1])
        low_close = abs(lows[-i] - closes[-i-1])
        
        true_range = max(high_low, high_close, low_close)
        true_ranges.append(true_range)
    
    atr = sum(true_ranges) / period
    return atr


def calculate_adx(values: List[float], period: int = 14) -> float:
    """ADX (Average Directional Index) - 단순화된 버전"""
    if len(values) < period * 2:
        return 0.0
    
    # 단순화된 ADX 계산 (실제로는 더 복잡함)
    up_moves = []
    down_moves = []
    
    for i in range(-period, 0):
        change = values[i] - values[i - 1]
        if change > 0:
            up_moves.append(change)
            down_moves.append(0.0)
        else:
            up_moves.append(0.0)
            down_moves.append(abs(change))
    
    avg_up = sum(up_moves) / period
    avg_down = sum(down_moves) / period
    
    if avg_down == 0:
        return 100.0
    
    dx = abs(avg_up - avg_down) / (avg_up + avg_down) * 100
    adx = dx  # 단순화된 ADX
    
    return adx


def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
    """스토캐스틱 오실레이터"""
    if len(highs) < k_period or len(lows) < k_period or len(closes) < k_period:
        return 50.0, 50.0
    
    recent_highs = highs[-k_period:]
    recent_lows = lows[-k_period:]
    current_close = closes[-1]
    
    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)
    
    if highest_high == lowest_low:
        k_percent = 50.0
    else:
        k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
    
    # D 값은 K 값의 이동평균 (단순화)
    d_percent = k_percent  # 단순화
    
    return k_percent, d_percent


def calculate_roc(values: List[float], period: int = 10) -> float:
    """변화율 (Rate of Change)"""
    if len(values) <= period:
        return 0.0
    
    base = values[-period - 1]
    if base == 0:
        return 0.0
    
    current = values[-1]
    roc = ((current - base) / base) * 100.0
    
    return roc
