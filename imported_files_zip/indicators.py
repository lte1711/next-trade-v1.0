"""
indicators.py — 지표 계산 모듈
================================
설탕이님 전략 + 라즈리본 통합에 필요한 모든 지표.
"""

import pandas as pd
import numpy as np


# ── EMA ────────────────────────────────────────────────────
def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


# ── ATR ────────────────────────────────────────────────────
def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([
        h - l,
        (h - c.shift(1)).abs(),
        (l - c.shift(1)).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


# ── Heikin-Ashi ────────────────────────────────────────────
def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    ha = pd.DataFrame(index=df.index)
    ha["ha_close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    ha_open = [(df["open"].iloc[0] + df["close"].iloc[0]) / 2]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i - 1] + ha["ha_close"].iloc[i - 1]) / 2)
    ha["ha_open"]  = ha_open
    ha["ha_high"]  = pd.concat([df["high"], ha["ha_open"], ha["ha_close"]], axis=1).max(axis=1)
    ha["ha_low"]   = pd.concat([df["low"],  ha["ha_open"], ha["ha_close"]], axis=1).min(axis=1)
    ha["ha_bull"]  = ha["ha_close"] > ha["ha_open"]
    ha["ha_body"]  = (ha["ha_close"] - ha["ha_open"]).abs()
    ha["ha_upper_wick"] = ha["ha_high"] - ha[["ha_open", "ha_close"]].max(axis=1)
    ha["ha_lower_wick"] = ha[["ha_open", "ha_close"]].min(axis=1) - ha["ha_low"]
    return ha


# ── Williams Fractal (5캔들) ────────────────────────────────
def fractals(df: pd.DataFrame) -> pd.DataFrame:
    high, low = df["high"], df["low"]
    frac_high = pd.Series(False, index=df.index)
    frac_low  = pd.Series(False, index=df.index)

    for i in range(2, len(df) - 2):
        h = high.iloc[i]
        if h > high.iloc[i-2] and h > high.iloc[i-1] and h > high.iloc[i+1] and h > high.iloc[i+2]:
            frac_high.iloc[i] = True
        l = low.iloc[i]
        if l < low.iloc[i-2] and l < low.iloc[i-1] and l < low.iloc[i+1] and l < low.iloc[i+2]:
            frac_low.iloc[i] = True

    # 확정된 프랙탈 고/저점 값 (2캔들 후 확정)
    df["fractal_high"] = frac_high
    df["fractal_low"]  = frac_low

    # 가장 최근 확정 프랙탈 고/저점 가격 (rolling forward-fill)
    fh_val = high.where(frac_high)
    fl_val = low.where(frac_low)
    df["last_fractal_high"] = fh_val.ffill()
    df["last_fractal_low"]  = fl_val.ffill()
    return df


# ── 라즈리본 그물 + 구름대 ─────────────────────────────────
def raz_cloud(df: pd.DataFrame) -> pd.DataFrame:
    """EMA 20~30 밴드 → 구름대 upper/lower/mid."""
    close = df["close"]
    nets  = pd.DataFrame({f"n{p}": ema(close, p) for p in range(20, 31)}, index=df.index)
    df["cloud_upper"] = nets.max(axis=1)
    df["cloud_lower"] = nets.min(axis=1)
    df["cloud_mid"]   = nets.mean(axis=1)

    # 그물 색상 비율 (0=빨강, 1=파랑)
    ratio = (close - df["cloud_lower"]) / (df["cloud_upper"] - df["cloud_lower"] + 1e-10)
    df["net_ratio"] = ratio.clip(0, 1)
    prev = df["net_ratio"].shift(1)
    df["net_to_blue"] = (df["net_ratio"] >= 0.8) & (prev < 0.8)
    df["net_to_red"]  = (df["net_ratio"] <= 0.2) & (prev > 0.2)
    return df


# ── 추세선 길이 변화 (라즈 독창 기법) ──────────────────────
def trendline_length(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """
    라즈가 말한 '추세선 꼭짓점 길이 짧아졌다 길어지면 전환' 개념.
    근사값: 이동창 내 고점/저점 간 거리 변화율로 수치화.

    tl_shrinking = True  → 길이 짧아지는 중 (추세 지속)
    tl_expanding = True  → 길이 갑자기 길어짐 (전환 가능성↑)
    """
    close = df["close"]
    roll_high = close.rolling(window).max()
    roll_low  = close.rolling(window).min()
    span      = (roll_high - roll_low).abs()

    span_change = span.diff()
    df["tl_span"]      = span
    df["tl_shrinking"] = span_change < 0
    df["tl_expanding"] = (span_change > 0) & (span_change.shift(1) <= 0)
    return df


# ── ATR 기반 횡보 감지 ────────────────────────────────────
def range_filter(df: pd.DataFrame, atr_period: int = 14,
                 atr_ratio: float = 0.6, lookback: int = 20) -> pd.DataFrame:
    """
    현재 ATR < 최근 lookback 평균 ATR * atr_ratio → 횡보 판정.
    진입 금지 조건.
    """
    df["atr"] = atr(df, atr_period)
    df["atr_ma"] = df["atr"].rolling(lookback).mean()
    df["is_ranging"] = df["atr"] < df["atr_ma"] * atr_ratio
    return df


# ── EMA 기울기 (횡보 보조 판단) ──────────────────────────
def ema_slope(series: pd.Series, lookback: int = 5) -> pd.Series:
    """EMA 기울기 (lookback 캔들 전 대비 변화율 %)."""
    return (series - series.shift(lookback)) / series.shift(lookback) * 100


# ── 전체 지표 한 번에 ────────────────────────────────────
def build_all(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 라즈리본 4선
    close = df["close"]
    df["ema30"]  = ema(close, 30)
    df["ema60"]  = ema(close, 60)
    df["ema100"] = ema(close, 100)
    df["ema200"] = ema(close, 200)

    # 설탕이님 전략 EMA
    df["ema20"] = ema(close, 20)
    df["ema50"] = ema(close, 50)

    # EMA 기울기
    df["slope_ema20"]  = ema_slope(df["ema20"])
    df["slope_ema200"] = ema_slope(df["ema200"])

    # Heikin-Ashi
    ha = heikin_ashi(df)
    df = pd.concat([df, ha], axis=1)

    # Fractal
    df = fractals(df)

    # 라즈 구름대
    df = raz_cloud(df)

    # 추세선 길이 변화
    df = trendline_length(df)

    # ATR 횡보 필터
    df = range_filter(df)

    return df
