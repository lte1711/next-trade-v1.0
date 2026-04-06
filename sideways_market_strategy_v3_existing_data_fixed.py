#!/usr/bin/env python3
"""
횡보장 전략 v3 백테스트 실행기 - 기존 데이터 사용 (수정 버전)
가지고 있는 실제 데이터로 백테스트 실행
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import os
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.005     # 0.5% of equity
    atr_stop_mult: float = 1.5
    atr_take_mult: float = 1.0
    fee_rate: float = 0.0004          # 0.04% per side
    slippage_rate: float = 0.0002     # 0.02% per side
    max_holding_bars: int = 24
    min_data_bars: int = 120


@dataclass
class StrategyConfig:
    adx_period: int = 14
    atr_period: int = 14
    rsi_period: int = 14
    bb_period: int = 20
    bb_std: float = 2.0
    z_period: int = 20
    ranging_adx_threshold: float = 20.0
    trending_adx_threshold: float = 25.0
    bandwidth_quantile_window: int = 100
    bandwidth_ranging_quantile: float = 0.35
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    z_entry_threshold: float = 2.0
    volume_lookback: int = 20
    low_volume_factor: float = 0.80
    tr_spike_atr_mult: float = 1.80
    realized_vol_window: int = 20
    realized_vol_spike_mult: float = 1.50
    confidence_floor: float = 0.0
    confidence_cap: float = 1.0


@dataclass
class Trade:
    entry_index: int
    exit_index: int
    side: str
    entry_time: object
    exit_time: object
    entry_price: float
    exit_price: float
    qty: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    bars_held: int
    exit_reason: str
    entry_confidence: float
    market_regime: str


class SidewaysMarketStrategyV3:
    def __init__(
        self,
        strategy_config: Optional[StrategyConfig] = None,
        risk_config: Optional[RiskConfig] = None,
    ) -> None:
        self.cfg = strategy_config or StrategyConfig()
        self.risk = risk_config or RiskConfig()

    # -----------------------------
    # validation
    # -----------------------------
    def validate_dataframe(self, df: pd.DataFrame) -> None:
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        if len(df) < self.risk.min_data_bars:
            raise ValueError(
                f"Not enough rows: got {len(df)}, "
                f"need at least {self.risk.min_data_bars}"
            )

    @staticmethod
    def _to_series(x, index=None) -> pd.Series:
        if isinstance(x, pd.Series):
            return x
        return pd.Series(x, index=index)

    @staticmethod
    def _rma(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    # -----------------------------
    # indicators
    # -----------------------------
    def atr(self, df: pd.DataFrame, period: Optional[int] = None) -> pd.Series:
        p = period or self.cfg.atr_period
        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                (df["high"] - df["low"]).abs(),
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return self._rma(tr, p)

    def adx(self, df: pd.DataFrame, period: Optional[int] = None) -> Tuple[pd.Series, pd.Series, pd.Series]:
        p = period or self.cfg.adx_period

        up_move = df["high"].diff()
        down_move = -df["low"].diff()

        plus_dm = pd.Series(
            np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
            index=df.index,
        )
        minus_dm = pd.Series(
            np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
            index=df.index,
        )

        atr = self.atr(df, p).replace(0, np.nan)
        plus_di = 100.0 * self._rma(plus_dm, p) / atr
        minus_di = 100.0 * self._rma(minus_dm, p) / atr

        dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = self._rma(dx, p)
        return adx, plus_di, minus_di

    def rsi(self, df: pd.DataFrame, period: Optional[int] = None) -> pd.Series:
        p = period or self.cfg.rsi_period
        delta = df["close"].diff()
        gain = delta.clip(lower=0.0)
        loss = (-delta).clip(lower=0.0)

        avg_gain = self._rma(gain, p)
        avg_loss = self._rma(loss, p).replace(0, np.nan)

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)

    def bollinger_bands(
        self,
        df: pd.DataFrame,
        period: Optional[int] = None,
        std_mult: Optional[float] = None,
    ) -> pd.DataFrame:
        p = period or self.cfg.bb_period
        k = std_mult or self.cfg.bb_std
        mid = df["close"].rolling(p, min_periods=p).mean()
        std = df["close"].rolling(p, min_periods=p).std(ddof=0)

        upper = mid + k * std
        lower = mid - k * std
        bandwidth = (upper - lower) / mid.replace(0, np.nan)
        percent_b = (df["close"] - lower) / (upper - lower).replace(0, np.nan)

        return pd.DataFrame(
            {
                "bb_mid": mid,
                "bb_upper": upper,
                "bb_lower": lower,
                "bb_bandwidth": bandwidth,
                "bb_percent_b": percent_b,
            },
            index=df.index,
        )

    def zscore(self, df: pd.DataFrame, period: Optional[int] = None) -> pd.Series:
        p = period or self.cfg.z_period
        mean = df["close"].rolling(p, min_periods=p).mean()
        std = df["close"].rolling(p, min_periods=p).std(ddof=0).replace(0, np.nan)
        return (df["close"] - mean) / std

    def realized_vol(self, df: pd.DataFrame, window: Optional[int] = None) -> pd.Series:
        w = window or self.cfg.realized_vol_window
        log_ret = np.log(df["close"] / df["close"].shift(1))
        return log_ret.rolling(w, min_periods=w).std()

    # -----------------------------
    # features / regime
    # -----------------------------
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validate_dataframe(df)
        out = df.copy()

        out["atr"] = self.atr(out, self.cfg.atr_period)
        out["adx"], out["plus_di"], out["minus_di"] = self.adx(out, self.cfg.adx_period)
        out["rsi"] = self.rsi(out, self.cfg.rsi_period)

        bb = self.bollinger_bands(out, self.cfg.bb_period, self.cfg.bb_std)
        out = pd.concat([out, bb], axis=1)

        out["zscore"] = self.zscore(out, self.cfg.z_period)
        out["realized_vol"] = self.realized_vol(out, self.cfg.realized_vol_window)

        prev_close = out["close"].shift(1)
        out["true_range"] = pd.concat(
            [
                (out["high"] - out["low"]).abs(),
                (out["high"] - prev_close).abs(),
                (out["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        out["avg_volume"] = out["volume"].rolling(
            self.cfg.volume_lookback,
            min_periods=self.cfg.volume_lookback,
        ).mean()

        bw_roll = out["bb_bandwidth"].rolling(
            self.cfg.bandwidth_quantile_window,
            min_periods=self.cfg.bandwidth_quantile_window,
        )
        out["bw_q"] = bw_roll.quantile(self.cfg.bandwidth_ranging_quantile)
        out["rv_median"] = out["realized_vol"].rolling(
            self.cfg.realized_vol_window,
            min_periods=self.cfg.realized_vol_window,
        ).median()

        out["market_regime"] = out.apply(self._detect_market_condition_row, axis=1)
        out["whipsaw_blocked"] = out.apply(self._whipsaw_filter_row, axis=1)

        signal_df = out.apply(self._signal_row, axis=1, result_type="expand")
        out = pd.concat([out, signal_df], axis=1)

        return out

    def _detect_market_condition_row(self, row: pd.Series) -> str:
        adx = row.get("adx", np.nan)
        bw = row.get("bb_bandwidth", np.nan)
        bw_q = row.get("bw_q", np.nan)

        if pd.notna(adx) and pd.notna(bw) and pd.notna(bw_q):
            if adx < self.cfg.ranging_adx_threshold and bw <= bw_q:
                return "RANGING"
            if adx > self.cfg.trending_adx_threshold:
                return "TRENDING"
        return "NEUTRAL"

    def _whipsaw_filter_row(self, row: pd.Series) -> bool:
        current_volume = row.get("volume", np.nan)
        avg_volume = row.get("avg_volume", np.nan)
        tr = row.get("true_range", np.nan)
        atr = row.get("atr", np.nan)
        rv = row.get("realized_vol", np.nan)
        rv_median = row.get("rv_median", np.nan)

        low_volume = (
            pd.notna(current_volume)
            and pd.notna(avg_volume)
            and current_volume < avg_volume * self.cfg.low_volume_factor
        )
        tr_spike = (
            pd.notna(tr)
            and pd.notna(atr)
            and atr > 0
            and tr > atr * self.cfg.tr_spike_atr_mult
        )
        rv_spike = (
            pd.notna(rv)
            and pd.notna(rv_median)
            and rv_median > 0
            and rv > rv_median * self.cfg.realized_vol_spike_mult
        )
        return bool(low_volume or tr_spike or rv_spike)

    def _confidence_clip(self, value: float) -> float:
        return float(np.clip(value, self.cfg.confidence_floor, self.cfg.confidence_cap))

    def _signal_row(self, row: pd.Series) -> pd.Series:
        regime = row.get("market_regime", "NEUTRAL")
        blocked = bool(row.get("whipsaw_blocked", False))

        result = {
            "signal": "NEUTRAL",
            "signal_source": "NONE",
            "reason": "No signal",
            "confidence": 0.0,
        }

        if regime != "RANGING":
            result["reason"] = f"Regime={regime}"
            return pd.Series(result)

        if blocked:
            result["reason"] = "Whipsaw filter blocked"
            return pd.Series(result)

        close = row.get("close", np.nan)
        lower = row.get("bb_lower", np.nan)
        upper = row.get("bb_upper", np.nan)
        mid = row.get("bb_mid", np.nan)
        rsi = row.get("rsi", np.nan)
        z = row.get("zscore", np.nan)
        adx = row.get("adx", np.nan)
        pb = row.get("bb_percent_b", np.nan)

        # Range setup
        if pd.notna(close) and pd.notna(lower) and pd.notna(rsi):
            if close <= lower and rsi <= self.cfg.rsi_oversold:
                distance_score = 0.0 if pd.isna(mid) or mid == 0 else abs((mid - close) / mid)
                rsi_score = min(1.0, max(0.0, (self.cfg.rsi_oversold - rsi) / 20.0))
                adx_score = 0.0 if pd.isna(adx) else min(1.0, max(0.0, (self.cfg.ranging_adx_threshold - adx) / 20.0))
                conf = self._confidence_clip(0.35 + 0.30 * rsi_score + 0.20 * distance_score + 0.15 * adx_score)
                return pd.Series(
                    {
                        "signal": "BUY",
                        "signal_source": "RANGE",
                        "reason": "Price at lower band and RSI oversold",
                        "confidence": conf,
                    }
                )

        if pd.notna(close) and pd.notna(upper) and pd.notna(rsi):
            if close >= upper and rsi >= self.cfg.rsi_overbought:
                distance_score = 0.0 if pd.isna(mid) or mid == 0 else abs((close - mid) / mid)
                rsi_score = min(1.0, max(0.0, (rsi - self.cfg.rsi_overbought) / 20.0))
                adx_score = 0.0 if pd.isna(adx) else min(1.0, max(0.0, (self.cfg.ranging_adx_threshold - adx) / 20.0))
                conf = self._confidence_clip(0.35 + 0.30 * rsi_score + 0.20 * distance_score + 0.15 * adx_score)
                return pd.Series(
                    {
                        "signal": "SELL",
                        "signal_source": "RANGE",
                        "reason": "Price at upper band and RSI overbought",
                        "confidence": conf,
                    }
                )

        # Mean reversion fallback
        if pd.notna(z):
            if z <= -self.cfg.z_entry_threshold:
                z_score = min(1.0, abs(z) / (self.cfg.z_entry_threshold + 1.5))
                pb_score = 0.0 if pd.isna(pb) else min(1.0, max(0.0, (0.2 - pb) / 0.2))
                conf = self._confidence_clip(0.30 + 0.45 * z_score + 0.25 * pb_score)
                return pd.Series(
                    {
                        "signal": "BUY",
                        "signal_source": "MEAN_REVERSION",
                        "reason": f"Z-score {z:.2f} below threshold",
                        "confidence": conf,
                    }
                )
            if z >= self.cfg.z_entry_threshold:
                z_score = min(1.0, abs(z) / (self.cfg.z_entry_threshold + 1.5))
                pb_score = 0.0 if pd.isna(pb) else min(1.0, max(0.0, (pb - 0.8) / 0.2))
                conf = self._confidence_clip(0.30 + 0.45 * z_score + 0.25 * pb_score)
                return pd.Series(
                    {
                        "signal": "SELL",
                        "signal_source": "MEAN_REVERSION",
                        "reason": f"Z-score {z:.2f} above threshold",
                        "confidence": conf,
                    }
                )

        return pd.Series(result)

    # -----------------------------
    # execution helpers
    # -----------------------------
    def _entry_exit_levels(self, row: pd.Series, side: str) -> Dict[str, float]:
        entry = float(row["close"])
        atr = float(row["atr"])
        mid = float(row["bb_mid"]) if pd.notna(row["bb_mid"]) else entry

        if side == "LONG":
            stop = entry - atr * self.risk.atr_stop_mult
            tp = min(mid, entry + atr * self.risk.atr_take_mult) if mid > entry else entry + atr * self.risk.atr_take_mult
        else:
            stop = entry + atr * self.risk.atr_stop_mult
            tp = max(mid, entry - atr * self.risk.atr_take_mult) if mid < entry else entry - atr * self.risk.atr_take_mult

        return {"entry": entry, "stop": stop, "take_profit": tp}

    def _position_size(self, equity: float, entry: float, stop: float) -> float:
        risk_amount = equity * self.risk.risk_per_trade
        per_unit_risk = abs(entry - stop)
        if per_unit_risk <= 0:
            return 0.0
        qty = risk_amount / per_unit_risk
        return max(0.0, float(qty))

    def _apply_entry_slippage(self, price: float, side: str) -> float:
        if side == "LONG":
            return price * (1.0 + self.risk.slippage_rate)
        return price * (1.0 - self.risk.slippage_rate)

    def _apply_exit_slippage(self, price: float, side: str) -> float:
        if side == "LONG":
            return price * (1.0 - self.risk.slippage_rate)
        return price * (1.0 + self.risk.slippage_rate)

    # -----------------------------
    # backtest
    # -----------------------------
    def backtest(
        self,
        features: pd.DataFrame,
        initial_capital: float = 10_000.0,
        min_confidence: float = 0.55,
        allow_signal_sources: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        if not isinstance(features, pd.DataFrame):
            raise TypeError("features must be a pandas DataFrame from prepare_features()")

        df = features.copy()
        self.validate_dataframe(df)

        allow_sources = set(allow_signal_sources or ["RANGE", "MEAN_REVERSION"])

        equity = float(initial_capital)
        peak_equity = float(initial_capital)
        position: Optional[Dict[str, object]] = None

        equity_curve: List[Dict[str, object]] = []
        trades: List[Trade] = []

        for i in range(len(df)):
            row = df.iloc[i]
            timestamp = df.index[i]

            # mark-to-market equity
            if position is None:
                marked_equity = equity
            else:
                close_price = float(row["close"])
                if position["side"] == "LONG":
                    unrealized = (close_price - position["entry_price"]) * position["qty"]
                else:
                    unrealized = (position["entry_price"] - close_price) * position["qty"]
                marked_equity = equity + unrealized

            peak_equity = max(peak_equity, marked_equity)
            drawdown = 0.0 if peak_equity == 0 else (peak_equity - marked_equity) / peak_equity

            equity_curve.append(
                {
                    "time": timestamp,
                    "equity": marked_equity,
                    "peak_equity": peak_equity,
                    "drawdown": drawdown,
                    "position": "FLAT" if position is None else position["side"],
                }
            )

            # need one more bar for forward exit logic
            if i == len(df) - 1:
                continue

            next_row = df.iloc[i + 1]
            next_ts = df.index[i + 1]

            # manage open position using next bar OHLC
            if position is not None:
                exit_hit, exit_price, exit_reason = self._evaluate_exit(position, next_row)

                bars_held = i + 1 - int(position["entry_index"])
                timed_out = bars_held >= self.risk.max_holding_bars

                if not exit_hit and timed_out:
                    exit_hit = True
                    exit_price = self._apply_exit_slippage(float(next_row["close"]), position["side"])
                    exit_reason = "TIME_EXIT"

                # regime break exit
                if not exit_hit and str(next_row.get("market_regime", "NEUTRAL")) != "RANGING":
                    exit_hit = True
                    exit_price = self._apply_exit_slippage(float(next_row["close"]), position["side"])
                    exit_reason = "REGIME_EXIT"

                if exit_hit:
                    gross_pnl, net_pnl, return_pct = self._calculate_trade_pnl(
                        side=position["side"],
                        entry_price=float(position["entry_price"]),
                        exit_price=float(exit_price),
                        qty=float(position["qty"]),
                    )

                    equity += net_pnl
                    trades.append(
                        Trade(
                            entry_index=int(position["entry_index"]),
                            exit_index=i + 1,
                            side=str(position["side"]),
                            entry_time=position["entry_time"],
                            exit_time=next_ts,
                            entry_price=float(position["entry_price"]),
                            exit_price=float(exit_price),
                            qty=float(position["qty"]),
                            gross_pnl=gross_pnl,
                            net_pnl=net_pnl,
                            return_pct=return_pct,
                            bars_held=bars_held,
                            exit_reason=str(exit_reason),
                            entry_confidence=float(position["confidence"]),
                            market_regime=str(position["market_regime"]),
                        )
                    )
                    position = None
                    continue

            # open new position
            if position is None:
                signal = str(row.get("signal", "NEUTRAL"))
                source = str(row.get("signal_source", "NONE"))
                confidence = float(row.get("confidence", 0.0))

                if signal in {"BUY", "SELL"} and source in allow_sources and confidence >= min_confidence:
                    side = "LONG" if signal == "BUY" else "SHORT"
                    levels = self._entry_exit_levels(row, side)

                    raw_entry = levels["entry"]
                    entry_price = self._apply_entry_slippage(raw_entry, side)
                    stop = levels["stop"]
                    take_profit = levels["take_profit"]

                    qty = self._position_size(equity, entry_price, stop)
                    if qty > 0:
                        position = {
                            "side": side,
                            "entry_index": i + 1,
                            "entry_time": next_ts,
                            "entry_price": self._apply_entry_slippage(float(next_row["open"]), side),
                            "stop": stop,
                            "take_profit": take_profit,
                            "qty": qty,
                            "confidence": confidence,
                            "market_regime": str(row.get("market_regime", "UNKNOWN")),
                        }

        equity_df = pd.DataFrame(equity_curve)
        trades_df = pd.DataFrame([asdict(t) for t in trades])

        summary = self._build_summary(
            trades_df=trades_df,
            equity_df=equity_df,
            initial_capital=initial_capital,
            final_equity=float(equity_df["equity"].iloc[-1]) if not equity_df.empty else initial_capital,
        )

        return {
            "summary": summary,
            "trades": trades_df,
            "equity_curve": equity_df,
            "config": {
                "strategy_config": asdict(self.cfg),
                "risk_config": asdict(self.risk),
                "min_confidence": min_confidence,
                "allow_signal_sources": sorted(list(allow_sources)),
            },
        }

    def _evaluate_exit(self, position: Dict[str, object], bar: pd.Series) -> Tuple[bool, float, str]:
        side = str(position["side"])
        stop = float(position["stop"])
        tp = float(position["take_profit"])

        high = float(bar["high"])
        low = float(bar["low"])

        if side == "LONG":
            stop_hit = low <= stop
            tp_hit = high >= tp
            if stop_hit and tp_hit:
                return True, self._apply_exit_slippage(stop, side), "STOP_AND_TP_SAME_BAR_STOP_PRIORITY"
            if stop_hit:
                return True, self._apply_exit_slippage(stop, side), "STOP_LOSS"
            if tp_hit:
                return True, self._apply_exit_slippage(tp, side), "TAKE_PROFIT"
        else:
            stop_hit = high >= stop
            tp_hit = low <= tp
            if stop_hit and tp_hit:
                return True, self._apply_exit_slippage(stop, side), "STOP_AND_TP_SAME_BAR_STOP_PRIORITY"
            if stop_hit:
                return True, self._apply_exit_slippage(stop, side), "STOP_LOSS"
            if tp_hit:
                return True, self._apply_exit_slippage(tp, side), "TAKE_PROFIT"

        return False, 0.0, ""

    def _calculate_trade_pnl(self, side: str, entry_price: float, exit_price: float, qty: float) -> Tuple[float, float, float]:
        if side == "LONG":
            gross = (exit_price - entry_price) * qty
            notional = (entry_price + exit_price) * qty
            net = gross - notional * self.risk.fee_rate
            ret = 0.0 if entry_price == 0 else (exit_price - entry_price) / entry_price
        else:
            gross = (entry_price - exit_price) * qty
            notional = (entry_price + exit_price) * qty
            net = gross - notional * self.risk.fee_rate
            ret = 0.0 if entry_price == 0 else (entry_price - exit_price) / entry_price

        return float(gross), float(net), float(ret)

    def _build_summary(
        self,
        trades_df: pd.DataFrame,
        equity_df: pd.DataFrame,
        initial_capital: float,
        final_equity: float,
    ) -> Dict[str, float]:
        if equity_df.empty:
            return {
                "initial_capital": float(initial_capital),
                "final_equity": float(final_equity),
                "net_profit": 0.0,
                "total_return_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "avg_bars_held": 0.0,
            }

        max_drawdown_pct = float(equity_df["drawdown"].max() * 100.0)

        if trades_df.empty:
            return {
                "initial_capital": float(initial_capital),
                "final_equity": float(final_equity),
                "net_profit": float(final_equity - initial_capital),
                "total_return_pct": float((final_equity / initial_capital - 1.0) * 100.0),
                "max_drawdown_pct": max_drawdown_pct,
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "avg_bars_held": 0.0,
            }

        wins = trades_df[trades_df["net_pnl"] > 0]
        losses = trades_df[trades_df["net_pnl"] < 0]

        gross_profit = float(wins["net_pnl"].sum()) if not wins.empty else 0.0
        gross_loss = float(losses["net_pnl"].sum()) if not losses.empty else 0.0
        profit_factor = 0.0 if gross_loss == 0 else abs(gross_profit / gross_loss)

        summary = {
            "initial_capital": float(initial_capital),
            "final_equity": float(final_equity),
            "net_profit": float(final_equity - initial_capital),
            "total_return_pct": float((final_equity / initial_capital - 1.0) * 100.0),
            "max_drawdown_pct": max_drawdown_pct,
            "total_trades": int(len(trades_df)),
            "win_rate": float((len(wins) / len(trades_df)) * 100.0),
            "profit_factor": float(profit_factor),
            "expectancy": float(trades_df["net_pnl"].mean()),
            "avg_bars_held": float(trades_df["bars_held"].mean()),
            "avg_trade_return_pct": float(trades_df["return_pct"].mean() * 100.0),
            "median_trade_return_pct": float(trades_df["return_pct"].median() * 100.0),
            "best_trade_pct": float(trades_df["return_pct"].max() * 100.0),
            "worst_trade_pct": float(trades_df["return_pct"].min() * 100.0),
        }
        return summary

    # -----------------------------
    # convenience
    # -----------------------------
    def run_full_pipeline(
        self,
        df: pd.DataFrame,
        initial_capital: float = 10_000.0,
        min_confidence: float = 0.55,
        allow_signal_sources: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        features = self.prepare_features(df)
        return self.backtest(
            features=features,
            initial_capital=initial_capital,
            min_confidence=min_confidence,
            allow_signal_sources=allow_signal_sources,
        )

    @staticmethod
    def save_results(result: Dict[str, object], output_dir: str) -> None:
        import os
        os.makedirs(output_dir, exist_ok=True)

        summary = result.get("summary", {})
        trades = result.get("trades", pd.DataFrame())
        equity_curve = result.get("equity_curve", pd.DataFrame())

        pd.DataFrame([summary]).to_csv(f"{output_dir}/summary.csv", index=False)

        if isinstance(trades, pd.DataFrame):
            trades.to_csv(f"{output_dir}/trades.csv", index=False)

        if isinstance(equity_curve, pd.DataFrame):
            equity_curve.to_csv(f"{output_dir}/equity_curve.csv", index=False)

    def load_existing_data(self, data_path: str) -> pd.DataFrame:
        """기존 데이터 로드"""
        print(f"📊 기존 데이터 로드: {data_path}")
        
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        # 데이터를 리스트로 변환하고 필요한 컬럼만 선택
        if isinstance(data, list) and len(data) > 0:
            # 각 행에서 앞 5개 요소만 선택
            filtered_data = []
            for row in data:
                if len(row) >= 5:
                    filtered_data.append([row[0], row[1], row[2], row[3], row[4]])
            
            df = pd.DataFrame(filtered_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        else:
            raise ValueError("Invalid data format")
        
        # timestamp를 datetime으로 변환
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 데이터 타입 변환
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 결측치 제거
        df.dropna(inplace=True)
        
        print(f"📈 데이터 기간: {df.index[0]} ~ {df.index[-1]}")
        print(f"📊 총 데이터 수: {len(df)}")
        print(f"💰 가격 범위: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
        
        return df


__all__ = [
    "RiskConfig",
    "StrategyConfig",
    "Trade",
    "SidewaysMarketStrategyV3",
]


# 메인 실행 함수
def main():
    """메인 실행 함수 - 기존 데이터로 백테스트"""
    print("🎯 횡보장 전략 v3 백테스트 시작 (기존 데이터)")
    print("=" * 60)
    
    # 전략 인스턴스 생성
    strategy = SidewaysMarketStrategyV3()
    
    # 기존 데이터 찾기
    data_dir = "data/backtest_cache_v2"
    available_files = []
    
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith('.json'):
                available_files.append(file)
    
    if not available_files:
        print("❌ 기존 데이터 파일을 찾을 수 없습니다.")
        print("📁 data/backtest_cache_v2/ 디렉토리에 JSON 파일이 있는지 확인하세요.")
        return
    
    # 사용 가능한 데이터 파일 목록
    print("📋 사용 가능한 데이터 파일:")
    for i, file in enumerate(available_files, 1):
        print(f"  {i}. {file}")
    
    # BTCUSDT 5분 5년 데이터 사용 (가장 긴 기간)
    target_file = None
    for file in available_files:
        if 'BTCUSDT_5m_5.0y' in file:
            target_file = file
            break
    
    if not target_file:
        # BTC 데이터가 없으면 첫 번째 파일 사용
        target_file = available_files[0]
    
    data_path = os.path.join(data_dir, target_file)
    print(f"\n🎯 선택된 데이터: {target_file}")
    
    # 데이터 로드
    try:
        df = strategy.load_existing_data(data_path)
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return
    
    # 데이터 일부만 사용 (최근 6개월)
    if len(df) > 50000:  # 약 6개월 분량 (5분데이터)
        df = df.tail(50000)
        print(f"📊 최근 6개월 데이터만 사용: {len(df)} 행")
    
    print()
    
    # 백테스트 실행
    print("🔄 백테스트 실행 중...")
    result = strategy.run_full_pipeline(
        df,
        initial_capital=10_000,
        min_confidence=0.55
    )
    
    # 결과 출력
    summary = result["summary"]
    trades = result["trades"]
    
    print("📊 백테스트 결과")
    print("-" * 40)
    print(f"초기 자본: ${summary['initial_capital']:,.2f}")
    print(f"최종 자본: ${summary['final_equity']:,.2f}")
    print(f"순수익: ${summary['net_profit']:,.2f}")
    print(f"총수익률: {summary['total_return_pct']:.2f}%")
    print(f"최대낙폭: {summary['max_drawdown_pct']:.2f}%")
    print(f"총거래횟수: {summary['total_trades']}")
    print(f"승률: {summary['win_rate']:.2f}%")
    print(f"수익인자: {summary['profit_factor']:.2f}")
    print(f"기대값: ${summary['expectancy']:.2f}")
    print(f"평균보유봉: {summary['avg_bars_held']:.1f}")
    print()
    
    # 거래 상세
    if not trades.empty:
        print("📋 최근 10개 거래")
        print("-" * 40)
        display_cols = ['entry_time', 'side', 'entry_price', 'exit_price', 'net_pnl', 'return_pct', 'exit_reason']
        available_display_cols = [col for col in display_cols if col in trades.columns]
        print(trades[available_display_cols].head(10).to_string(index=False))
        print()
    
    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"backtest_results_{timestamp}"
    
    print(f"💾 결과 저장: {output_dir}/")
    strategy.save_results(result, output_dir)
    
    # 설정 정보 출력
    config = result["config"]
    print("⚙️ 사용된 설정")
    print("-" * 40)
    print(f"최소 신뢰도: {config['min_confidence']}")
    print(f"허용 신호 소스: {', '.join(config['allow_signal_sources'])}")
    print(f"데이터 파일: {target_file}")
    print()
    
    # 시장 상태 분석
    if 'market_regime' in df.columns:
        regime_counts = df['market_regime'].value_counts()
        print("📈 시장 상태 분포")
        print("-" * 40)
        for regime, count in regime_counts.items():
            pct = (count / len(df)) * 100
            print(f"{regime}: {count} ({pct:.1f}%)")
        print()
    
    print("✅ 백테스트 완료!")
    return result


if __name__ == "__main__":
    main()
