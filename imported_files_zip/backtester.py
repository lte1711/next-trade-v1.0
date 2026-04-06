"""
backtester.py — 포지션 관리 + KPI 백테스트
============================================
분할 청산(1차 50%), 연속 손절 추적, 드로우다운 계산 포함.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from signal_engine import Signal, Position, check_exit, Config


# ─────────────────────────────────────────────────────────────
# 거래 기록
# ─────────────────────────────────────────────────────────────

@dataclass
class Trade:
    signal:        Signal
    exit_bar:      int
    exit_ts:       object
    exit_price:    float
    exit_reason:   str
    pnl_pct:       float      # 전체 포지션 기준 손익 %
    partial_exit:  bool       # TP1 분할 청산 여부


# ─────────────────────────────────────────────────────────────
# 백테스터
# ─────────────────────────────────────────────────────────────

def run_backtest(
    ltf_df:   pd.DataFrame,
    signals:  list[Signal],
    cfg:      Config = Config(),
) -> list[Trade]:
    """
    신호 리스트를 받아 포지션 관리 + 청산 시뮬레이션.
    한 번에 하나의 포지션만 허용.
    """
    trades: list[Trade] = []
    pos: Optional[Position] = None
    ha_reversal_count = 0
    last_ha_bull: Optional[bool] = None

    for i in range(len(ltf_df)):
        row = ltf_df.iloc[i]
        ts  = ltf_df.index[i]
        ha_bull = bool(row.get("ha_bull", True))

        # HA 연속 반전 카운터
        if last_ha_bull is not None and ha_bull != last_ha_bull:
            ha_reversal_count = 1
        elif last_ha_bull is not None:
            ha_reversal_count += 1
        last_ha_bull = ha_bull

        # ── 열린 포지션 청산 확인 ─────────────
        if pos and not pos.closed:
            reason = check_exit(row, pos, ha_reversal_count, cfg)

            if reason == "tp1" and not pos.tp1_hit:
                # 1차 50% 청산 후 포지션 유지
                pos.tp1_hit    = True
                pos.size_remain = 1.0 - cfg.TP1_SIZE_PCT
                pnl = cfg.TP1_SIZE_PCT * cfg.TP1_RR  # 절반 × RR1 수익
                trades.append(Trade(
                    signal       = pos.signal,
                    exit_bar     = i,
                    exit_ts      = ts,
                    exit_price   = pos.signal.tp1,
                    exit_reason  = "tp1_partial",
                    pnl_pct      = round(pnl * pos.signal.risk_pct, 4),
                    partial_exit = True,
                ))

            elif reason and reason != "tp1":
                # 전량 청산
                sig   = pos.signal
                ep    = sig.entry_price
                sl    = sig.stop_loss
                risk  = abs(ep - sl) / ep

                if "stop_loss" in reason:
                    exit_p  = sl
                    pnl_r   = -1.0
                elif "tp2" in reason:
                    exit_p  = sig.tp2
                    pnl_r   = cfg.TP2_RR
                else:
                    exit_p  = float(row["close"])
                    pnl_r   = (exit_p - ep) / ep / risk if sig.side == "long" else (ep - exit_p) / ep / risk

                remain_size = pos.size_remain
                pnl_pct = round(remain_size * pnl_r * sig.risk_pct, 4)

                trades.append(Trade(
                    signal       = sig,
                    exit_bar     = i,
                    exit_ts      = ts,
                    exit_price   = exit_p,
                    exit_reason  = reason,
                    pnl_pct      = pnl_pct,
                    partial_exit = False,
                ))
                pos = None
                ha_reversal_count = 0

        # ── 신규 진입 ─────────────────────────
        if pos is None:
            for sig in signals:
                if sig.bar_index == i:
                    pos = Position(signal=sig)
                    break

    return trades


# ─────────────────────────────────────────────────────────────
# KPI 계산
# ─────────────────────────────────────────────────────────────

def calc_kpi(trades: list[Trade]) -> dict:
    if not trades:
        return {}

    # 분할 청산 제외한 최종 청산만 집계
    final = [t for t in trades if not t.partial_exit]
    partial = [t for t in trades if t.partial_exit]

    total     = len(final)
    wins      = sum(1 for t in final if t.pnl_pct > 0)
    losses    = total - wins
    win_rate  = wins / total * 100 if total else 0

    gross_win  = sum(t.pnl_pct for t in final if t.pnl_pct > 0)
    gross_loss = abs(sum(t.pnl_pct for t in final if t.pnl_pct < 0))
    pf         = gross_win / gross_loss if gross_loss else float("inf")

    tp1_gains  = sum(t.pnl_pct for t in partial)
    net_pnl    = sum(t.pnl_pct for t in trades)

    # 누적 수익 곡선 & 최대 드로우다운
    equity = np.cumsum([t.pnl_pct for t in trades])
    peak   = np.maximum.accumulate(equity)
    dd     = equity - peak
    max_dd = float(dd.min())

    # 신호 타입별
    by_type: dict[str, list] = {}
    for t in final:
        k = t.signal.signal_type
        by_type.setdefault(k, []).append(t.pnl_pct)

    type_stats = {
        k: {
            "count":    len(v),
            "win_rate": round(sum(1 for x in v if x > 0) / len(v) * 100, 1),
            "avg_pnl":  round(np.mean(v), 4),
        }
        for k, v in by_type.items()
    }

    # 연속 손절 최대
    streak = max_streak = 0
    for t in final:
        if t.pnl_pct < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    return {
        "total_trades":   total,
        "wins":           wins,
        "losses":         losses,
        "win_rate_pct":   round(win_rate, 1),
        "profit_factor":  round(pf, 2),
        "net_pnl_pct":    round(net_pnl, 2),
        "tp1_gains_pct":  round(tp1_gains, 2),
        "max_drawdown":   round(max_dd, 2),
        "max_loss_streak": max_streak,
        "by_signal_type": type_stats,
        "equity_curve":   equity.tolist(),
    }


# ─────────────────────────────────────────────────────────────
# 결과 출력
# ─────────────────────────────────────────────────────────────

def print_report(trades: list[Trade], kpi: dict) -> None:
    bar = "═" * 70

    print(f"\n{bar}")
    print("  통합 전략 백테스트 결과")
    print(bar)

    if not kpi:
        print("  거래 없음")
        return

    print(f"  총 거래        : {kpi['total_trades']}건")
    print(f"  승 / 패        : {kpi['wins']}승 / {kpi['losses']}패")
    print(f"  승률           : {kpi['win_rate_pct']}%")
    print(f"  Profit Factor  : {kpi['profit_factor']}")
    print(f"  누적 손익      : {kpi['net_pnl_pct']:+.2f}%")
    print(f"  1차 분할 수익  : {kpi['tp1_gains_pct']:+.2f}%")
    print(f"  최대 드로우다운: {kpi['max_drawdown']:.2f}%")
    print(f"  최대 연속 손절 : {kpi['max_loss_streak']}회")

    print(f"\n  ── 신호 타입별 ──")
    for stype, stat in kpi["by_signal_type"].items():
        print(f"  {stype:<16} : {stat['count']}건 | "
              f"승률 {stat['win_rate']}% | "
              f"평균 손익 {stat['avg_pnl']:+.3f}%")

    print(f"\n  ── 거래 상세 (최근 10건) ──")
    header = f"  {'시각':<22} {'방향':<6} {'타입':<15} {'진입':>10} {'손절':>10} {'청산':>10} {'손익':>7} {'이유'}"
    print(header)
    print("  " + "─" * 100)

    show = trades[-10:] if len(trades) > 10 else trades
    for t in show:
        sig = t.signal
        print(
            f"  {str(t.exit_ts):<22} "
            f"{sig.side:<6} "
            f"{sig.signal_type:<15} "
            f"{sig.entry_price:>10.2f} "
            f"{sig.stop_loss:>10.2f} "
            f"{t.exit_price:>10.2f} "
            f"{t.pnl_pct:>+7.3f}% "
            f"{t.exit_reason}"
        )

    print(bar)
