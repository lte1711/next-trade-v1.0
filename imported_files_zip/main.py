"""
main.py — 통합 전략 실행 진입점
=================================
사용법:
    python main.py                  # 더미 데이터 백테스트
    python main.py --csv data.csv   # CSV 파일 백테스트
    python main.py --live           # 실시간 신호 (ccxt 필요)

파일 구조:
    unified_strategy/
    ├── indicators.py     지표 계산 (EMA/HA/Fractal/Cloud/ATR)
    ├── signal_engine.py  신호 생성 (L1/L2/L3 레이어)
    ├── backtester.py     포지션 관리 + KPI
    └── main.py           ← 이 파일
"""

import sys
import argparse
import pandas as pd
import numpy as np

from indicators   import build_all
from signal_engine import generate_signals, Config
from backtester   import run_backtest, calc_kpi, print_report


# ─────────────────────────────────────────────────────────────
# 더미 OHLCV 생성 (테스트용)
# ─────────────────────────────────────────────────────────────

def make_dummy(n: int = 1200, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    현실적인 추세 + 횡보 + 급변동 구간이 포함된 더미 데이터.
    Returns (ltf_5m, htf_15m)
    """
    np.random.seed(seed)
    price = 50000.0
    rows  = []

    for i in range(n):
        # 구간별 드리프트
        if   100 < i < 400:  drift =  0.0005  # 상승 추세
        elif 450 < i < 500:  drift =  0.0000  # 횡보
        elif 500 < i < 750:  drift = -0.0004  # 하락 추세
        elif 800 < i < 850:  drift =  0.0000  # 횡보
        else:                drift =  0.0001  # 약한 상승

        o  = price
        c  = o + np.random.normal(drift, 0.0022) * o
        h  = max(o, c) + abs(np.random.normal(0, 0.0008)) * o
        l  = min(o, c) - abs(np.random.normal(0, 0.0008)) * o

        # 급변동 삽입
        if i in [120, 280, 510, 680, 820]:
            direction = 1 if drift >= 0 else -1
            c += direction * o * 0.028
            h  = max(o, c) + o * 0.004
            l  = min(o, c) - o * 0.002

        rows.append({"open": o, "high": h, "low": l, "close": c})
        price = c

    idx5m  = pd.date_range("2024-01-01", periods=n,     freq="5min")
    idx15m = pd.date_range("2024-01-01", periods=n // 3, freq="15min")

    ltf = pd.DataFrame(rows,          index=idx5m)
    # 15분봉: 5분봉 3개 묶어 OHLCV 생성
    htf_rows = []
    for j in range(0, n - 2, 3):
        chunk = rows[j:j+3]
        htf_rows.append({
            "open":  chunk[0]["open"],
            "high":  max(r["high"] for r in chunk),
            "low":   min(r["low"]  for r in chunk),
            "close": chunk[-1]["close"],
        })
    htf = pd.DataFrame(htf_rows[:len(idx15m)], index=idx15m)

    return ltf, htf


# ─────────────────────────────────────────────────────────────
# CSV 로드
# ─────────────────────────────────────────────────────────────

def load_csv(path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    CSV → 5분봉 로드 후 15분봉 리샘플.
    필수 컬럼: timestamp, open, high, low, close
    """
    df = pd.read_csv(path, parse_dates=["timestamp"], index_col="timestamp")
    df.columns = df.columns.str.lower()
    df = df[["open", "high", "low", "close"]].dropna()

    htf = df.resample("15min").agg({
        "open":  "first",
        "high":  "max",
        "low":   "min",
        "close": "last",
    }).dropna()

    return df, htf


# ─────────────────────────────────────────────────────────────
# 실시간 단일 신호 조회
# ─────────────────────────────────────────────────────────────

def live_signal(symbol: str = "BTC/USDT") -> None:
    try:
        import ccxt
    except ImportError:
        print("pip install ccxt 필요")
        return

    ex = ccxt.binance({"options": {"defaultType": "future"}})

    def fetch(tf, lim):
        raw = ex.fetch_ohlcv(symbol, tf, limit=lim)
        df  = pd.DataFrame(raw, columns=["ts","open","high","low","close","vol"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        return df.set_index("ts")[["open","high","low","close"]]

    print(f"[라이브] {symbol} 데이터 수신 중...")
    ltf = fetch("5m",  600)
    htf = fetch("15m", 200)

    ltf_ind = build_all(ltf)
    htf_ind = build_all(htf)

    cfg     = Config()
    signals = generate_signals(ltf_ind, htf_ind, cfg)

    if not signals:
        print("현재 신호 없음")
        return

    last = signals[-1]
    print(f"\n최신 신호:")
    print(f"  방향   : {last.side.upper()}")
    print(f"  타입   : {last.signal_type}")
    print(f"  진입가 : {last.entry_price:.2f}")
    print(f"  손절   : {last.stop_loss:.2f}  (리스크 {last.risk_pct:.2f}%)")
    print(f"  TP1    : {last.tp1:.2f}")
    print(f"  TP2    : {last.tp2:.2f}")
    print(f"  근거   : {last.reason}")


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="통합 전략 실행기")
    parser.add_argument("--csv",  type=str, help="CSV 파일 경로")
    parser.add_argument("--live", action="store_true", help="실시간 신호")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--seed",   type=int, default=42)
    args = parser.parse_args()

    cfg = Config()

    if args.live:
        live_signal(args.symbol)
        return

    # ── 데이터 준비 ───────────────────────────
    if args.csv:
        print(f"[CSV] {args.csv} 로드 중...")
        ltf, htf = load_csv(args.csv)
    else:
        print("[더미] 테스트 데이터 생성 중...")
        ltf, htf = make_dummy(seed=args.seed)

    print(f"  5분봉:  {len(ltf)}행  {ltf.index[0]} ~ {ltf.index[-1]}")
    print(f"  15분봉: {len(htf)}행\n")

    # ── 지표 계산 ─────────────────────────────
    print("[1/3] 지표 계산...")
    ltf_ind = build_all(ltf)
    htf_ind = build_all(htf)

    # ── 신호 생성 ─────────────────────────────
    print("[2/3] 신호 생성...")
    signals = generate_signals(ltf_ind, htf_ind, cfg)
    print(f"  생성된 신호: {len(signals)}건")

    if not signals:
        print("  신호 없음 — 파라미터를 완화해 보세요 (Config 값 조정)")
        return

    # 신호 요약
    from collections import Counter
    type_cnt = Counter(s.signal_type for s in signals)
    side_cnt = Counter(s.side        for s in signals)
    print(f"  타입별: {dict(type_cnt)}")
    print(f"  방향별: {dict(side_cnt)}")

    # ── 백테스트 ──────────────────────────────
    print("[3/3] 백테스트 실행...")
    trades = run_backtest(ltf_ind, signals, cfg)
    kpi    = calc_kpi(trades)
    print_report(trades, kpi)


if __name__ == "__main__":
    main()
