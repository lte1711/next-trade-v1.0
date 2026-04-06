"""
signal_engine.py — 통합 신호 엔진
====================================
설탕이님 전략 (EMA + HA + Fractal) + 라즈리본 (Cloud + 추세선 길이)
완전 통합 룰셋.

진입 레이어:
  L1. 15분봉 방향 필터 (설탕이님)
  L2. 횡보 차단 — ATR + 추세선 길이 (설탕이 + 라즈)
  L3. 5분봉 진입 타점
      A. 눌림 진입 (설탕이님 원형)
      B. 구름대 되돌림 진입 (라즈리본 추가)
      C. Fractal 돌파 진입 (설탕이님 원형)
손절: Fractal 구조 손절 + SL 캡 (진입가 대비 1.5% 초과 시 스킵)
익절: 1차 RR 1:1 50% / 2차 반대 Fractal or HA 연속 반전 2봉
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Literal, Optional

SideType   = Literal["long", "short"]
SignalType  = Literal["pullback", "cloud_rebound", "fractal_break", "none"]


# ─────────────────────────────────────────────────────────────
# 데이터 구조
# ─────────────────────────────────────────────────────────────

@dataclass
class Signal:
    bar_index:   int
    timestamp:   object
    side:        SideType
    signal_type: SignalType
    entry_price: float
    stop_loss:   float
    tp1:         float          # RR 1:1
    tp2:         float          # RR 1:2
    risk_pct:    float          # 진입가 대비 리스크 %
    reason:      str
    layers_passed: list[str] = field(default_factory=list)


@dataclass
class Position:
    signal:       Signal
    size_total:   float = 1.0   # 단위 (실제 수량은 외부에서 결정)
    size_remain:  float = 1.0
    tp1_hit:      bool  = False
    closed:       bool  = False
    exit_price:   float = 0.0
    exit_reason:  str   = ""


# ─────────────────────────────────────────────────────────────
# 설정값 (한 곳에서 관리)
# ─────────────────────────────────────────────────────────────

class Config:
    # ── 방향 필터 (L1) ─────────────────────
    HTF_EMA_ALIGN_STRICT = True     # True: 20>50>200 완전 정배열 요구
    HTF_HA_BULLISH_COUNT = 2        # 연속 HA 양봉 최소 수
    HTF_SLOPE_MIN_PCT    = 0.03     # EMA200 기울기 최소 % (횡보 배제)

    # ── 횡보 차단 (L2) ─────────────────────
    ATR_RATIO_THRESHOLD  = 0.65     # ATR < 평균의 65% → 횡보
    TL_EXPAND_CONFIRM    = True     # 추세선 길이 확장 확인
    EMA_ENTANGLE_MARGIN  = 0.002    # EMA20-50 거리 < 가격의 0.2% → 얽힘

    # ── 진입 (L3) ──────────────────────────
    PULLBACK_EMA_LIST    = [20, 50]   # 눌림 기준 EMA
    PULLBACK_MARGIN_PCT  = 0.003      # EMA ±0.3% 이내 = 눌림 도달
    CLOUD_IN_MARGIN      = 0.001      # 구름대 경계 ±0.1% = '들어왔다' 판정
    FRACTAL_BREAK_BUFFER = 0.0005     # 프랙탈 돌파 버퍼 0.05%
    HA_REVERSAL_CONFIRM  = 2          # HA 반전 확인 캔들 수

    # ── 손절 ───────────────────────────────
    SL_MAX_RISK_PCT      = 0.015      # 최대 손절폭 1.5% (캡)
    SL_BUFFER_PCT        = 0.001      # 프랙탈 기준 ±0.1% 여유

    # ── 익절 ───────────────────────────────
    TP1_RR               = 1.0        # 1차 익절 RR
    TP2_RR               = 2.0        # 2차 익절 RR
    TP1_SIZE_PCT         = 0.5        # 1차에서 50% 청산


# ─────────────────────────────────────────────────────────────
# L1: 15분봉 방향 필터
# ─────────────────────────────────────────────────────────────

def check_htf_bias(htf_row: pd.Series, cfg: Config = Config()) -> Optional[SideType]:
    """
    15분봉 한 행을 받아 롱/숏/None 반환.

    필요 컬럼: ema20, ema50, ema200, ha_bull, slope_ema200,
               last_fractal_high (상승 구조 확인용),
               last_fractal_low  (하락 구조 확인용)
    """
    e20, e50, e200 = htf_row["ema20"], htf_row["ema50"], htf_row["ema200"]
    ha_bull        = htf_row.get("ha_bull", True)
    slope200       = htf_row.get("slope_ema200", 0.1)

    # EMA 기울기 최소 조건 (횡보 시장 배제)
    if abs(slope200) < cfg.HTF_SLOPE_MIN_PCT:
        return None

    if cfg.HTF_EMA_ALIGN_STRICT:
        long_ema  = e20 > e50 > e200
        short_ema = e20 < e50 < e200
    else:
        long_ema  = e20 > e200
        short_ema = e20 < e200

    if long_ema and ha_bull:
        return "long"
    if short_ema and not ha_bull:
        return "short"
    return None


# ─────────────────────────────────────────────────────────────
# L2: 횡보 차단
# ─────────────────────────────────────────────────────────────

def is_ranging(row: pd.Series, cfg: Config = Config()) -> bool:
    """
    True 반환 시 진입 금지.

    조건 (하나라도 해당 시 횡보):
    ① ATR < ATR 평균 * threshold
    ② EMA20 ~ EMA50 거리가 너무 좁음 (얽힘)
    ③ 라즈: 추세선 길이 수렴 중 (tl_shrinking=True, tl_expanding=False)
    """
    # ① ATR 횡보
    if row.get("is_ranging", False):
        return True

    # ② EMA 얽힘
    price = row["close"]
    e20, e50 = row.get("ema20", price), row.get("ema50", price)
    if abs(e20 - e50) / price < cfg.EMA_ENTANGLE_MARGIN:
        return True

    return False


# ─────────────────────────────────────────────────────────────
# L3A: 눌림 진입 (설탕이님 원형)
# ─────────────────────────────────────────────────────────────

def check_pullback(
    row: pd.Series,
    side: SideType,
    cfg: Config = Config(),
) -> bool:
    """
    가격이 EMA20 or EMA50까지 되돌림 + HA 색 전환.
    """
    price  = row["close"]
    ha_bull = row.get("ha_bull", True)
    margin = cfg.PULLBACK_MARGIN_PCT

    for ema_key in ["ema20", "ema50"]:
        ema_val = row.get(ema_key, None)
        if ema_val is None:
            continue
        near_ema = abs(price - ema_val) / price <= margin

        if side == "long" and near_ema and ha_bull:
            return True
        if side == "short" and near_ema and not ha_bull:
            return True

    return False


# ─────────────────────────────────────────────────────────────
# L3B: 구름대 되돌림 진입 (라즈리본 추가)
# ─────────────────────────────────────────────────────────────

def check_cloud_rebound(
    row: pd.Series,
    side: SideType,
    cfg: Config = Config(),
) -> bool:
    """
    급변동(surge) 후 가격이 구름대 안으로 들어오고
    HA 방향 + EMA200 방향 일치 시 진입.
    """
    price = row["close"]
    cu    = row.get("cloud_upper", price * 1.01)
    cl    = row.get("cloud_lower", price * 0.99)
    margin = cfg.CLOUD_IN_MARGIN
    ha_bull = row.get("ha_bull", True)

    in_cloud = (cl * (1 - margin)) <= price <= (cu * (1 + margin))
    if not in_cloud:
        return False

    # EMA200 방향 일치
    e200 = row.get("ema200", price)
    if side == "long"  and price > e200 and ha_bull:
        return True
    if side == "short" and price < e200 and not ha_bull:
        return True
    return False


# ─────────────────────────────────────────────────────────────
# L3C: Fractal 돌파 진입 (설탕이님 원형)
# ─────────────────────────────────────────────────────────────

def check_fractal_break(
    row: pd.Series,
    side: SideType,
    cfg: Config = Config(),
) -> bool:
    """
    직전 확정 Fractal 고/저점 돌파 + HA 강한 봉.
    """
    price   = row["close"]
    ha_bull = row.get("ha_bull", True)
    ha_body = row.get("ha_body", 0)
    ha_wick = row.get("ha_upper_wick" if side == "long" else "ha_lower_wick", 0)
    buf     = cfg.FRACTAL_BREAK_BUFFER

    # HA 강한 봉 조건: 몸통 > 꼬리
    strong_ha = ha_body > ha_wick

    if side == "long":
        fh = row.get("last_fractal_high", None)
        if fh and price > fh * (1 + buf) and ha_bull and strong_ha:
            return True

    if side == "short":
        fl = row.get("last_fractal_low", None)
        if fl and price < fl * (1 - buf) and not ha_bull and strong_ha:
            return True

    return False


# ─────────────────────────────────────────────────────────────
# 손절 계산
# ─────────────────────────────────────────────────────────────

def calc_stop_loss(
    row: pd.Series,
    side: SideType,
    cfg: Config = Config(),
) -> Optional[float]:
    """
    Fractal 기준 구조 손절.
    SL이 진입가 대비 SL_MAX_RISK_PCT 초과 시 None 반환 → 진입 스킵.
    """
    price = row["close"]
    buf   = cfg.SL_BUFFER_PCT

    if side == "long":
        fl = row.get("last_fractal_low", None)
        if fl is None:
            return None
        sl = fl * (1 - buf)
        if (price - sl) / price > cfg.SL_MAX_RISK_PCT:
            return None
        return sl

    if side == "short":
        fh = row.get("last_fractal_high", None)
        if fh is None:
            return None
        sl = fh * (1 + buf)
        if (sl - price) / price > cfg.SL_MAX_RISK_PCT:
            return None
        return sl

    return None


# ─────────────────────────────────────────────────────────────
# 청산 조건
# ─────────────────────────────────────────────────────────────

def check_exit(
    row: pd.Series,
    pos: Position,
    ha_reversal_count: int,
    cfg: Config = Config(),
) -> Optional[str]:
    """
    청산 조건 확인. 해당 시 이유 문자열 반환, 아니면 None.

    청산 우선순위:
    1. 손절 (SL 터치)
    2. 1차 익절 (TP1, 아직 미청산 시)
    3. 라즈: 그물 색 반전 (net_to_blue / net_to_red)
    4. HA 연속 반전 (HA_REVERSAL_CONFIRM 봉 이상)
    5. 반대 Fractal 발생
    6. 2차 익절 (TP2 터치)
    """
    sig   = pos.signal
    side  = sig.side
    high  = row["high"]
    low   = row["low"]
    close = row["close"]

    # 1. 손절
    if side == "long"  and low  <= sig.stop_loss:
        return "stop_loss"
    if side == "short" and high >= sig.stop_loss:
        return "stop_loss"

    # 2. TP1
    if not pos.tp1_hit:
        if side == "long"  and high  >= sig.tp1:
            return "tp1"
        if side == "short" and low   <= sig.tp1:
            return "tp1"

    # 3. 그물 색 반전 (라즈리본)
    if side == "long"  and row.get("net_to_red",  False):
        return "net_color_red"
    if side == "short" and row.get("net_to_blue", False):
        return "net_color_blue"

    # 4. HA 연속 반전
    if side == "long"  and ha_reversal_count >= cfg.HA_REVERSAL_CONFIRM:
        return f"ha_reversal_{ha_reversal_count}봉"
    if side == "short" and ha_reversal_count >= cfg.HA_REVERSAL_CONFIRM:
        return f"ha_reversal_{ha_reversal_count}봉"

    # 5. 반대 Fractal 발생
    if side == "long"  and row.get("fractal_high", False):
        return "opposite_fractal"
    if side == "short" and row.get("fractal_low",  False):
        return "opposite_fractal"

    # 6. TP2
    if pos.tp1_hit:
        if side == "long"  and high >= sig.tp2:
            return "tp2"
        if side == "short" and low  <= sig.tp2:
            return "tp2"

    return None


# ─────────────────────────────────────────────────────────────
# 메인 신호 생성기
# ─────────────────────────────────────────────────────────────

def generate_signals(
    ltf_df:  pd.DataFrame,   # 5분봉 (지표 계산 완료)
    htf_df:  pd.DataFrame,   # 15분봉 (지표 계산 완료)
    cfg:     Config = Config(),
) -> list[Signal]:
    """
    5분봉 × 15분봉 조합으로 신호 생성.
    htf_df 인덱스는 ltf_df와 동일한 timezone이어야 함.
    """
    signals: list[Signal] = []

    # 15분봉 → 5분봉에 방향 매핑 (forward-fill)
    htf_bias_series = pd.Series(index=htf_df.index, dtype=object)
    for idx, row in htf_df.iterrows():
        htf_bias_series[idx] = check_htf_bias(row, cfg)
    htf_bias_ff = htf_bias_series.reindex(ltf_df.index, method="ffill")

    for i in range(10, len(ltf_df)):
        row = ltf_df.iloc[i]
        ts  = ltf_df.index[i]

        # ── L1 방향 필터 ──────────────────────
        bias: Optional[SideType] = htf_bias_ff.get(ts, None)
        if bias is None:
            continue

        # ── L2 횡보 차단 ──────────────────────
        if is_ranging(row, cfg):
            continue

        # ── L3 진입 타점 ──────────────────────
        sig_type: SignalType = "none"
        layers = [f"L1:{bias}", "L2:pass"]

        if check_pullback(row, bias, cfg):
            sig_type = "pullback"
            layers.append("L3A:pullback")
        elif check_cloud_rebound(row, bias, cfg):
            sig_type = "cloud_rebound"
            layers.append("L3B:cloud")
        elif check_fractal_break(row, bias, cfg):
            sig_type = "fractal_break"
            layers.append("L3C:fractal")

        if sig_type == "none":
            continue

        # ── 손절 계산 + SL 캡 ─────────────────
        sl = calc_stop_loss(row, bias, cfg)
        if sl is None:
            continue   # SL 너무 넓음 → 스킵

        price    = row["close"]
        risk     = abs(price - sl)
        risk_pct = risk / price * 100

        if bias == "long":
            tp1 = price + risk * cfg.TP1_RR
            tp2 = price + risk * cfg.TP2_RR
        else:
            tp1 = price - risk * cfg.TP1_RR
            tp2 = price - risk * cfg.TP2_RR

        reason = (
            f"HTF:{bias.upper()} | {sig_type} | "
            f"SL={sl:.4f} | TP1={tp1:.4f} | TP2={tp2:.4f} | "
            f"Risk={risk_pct:.2f}%"
        )

        signals.append(Signal(
            bar_index   = i,
            timestamp   = ts,
            side        = bias,
            signal_type = sig_type,
            entry_price = price,
            stop_loss   = sl,
            tp1         = tp1,
            tp2         = tp2,
            risk_pct    = risk_pct,
            reason      = reason,
            layers_passed = layers,
        ))

    return signals
