#!/usr/bin/env python3
"""
Fractal-break scalping futures trading system.

This file leaves the original, v2, and hybrid sources untouched. It focuses on
one fast setup only: confirmed fractal breakouts with Heikin Ashi confirmation.
"""

from __future__ import annotations

from completely_fixed_auto_strategy_trading_hybrid import HybridAutoStrategyFuturesTrading


class ScalpingAutoStrategyFuturesTrading(HybridAutoStrategyFuturesTrading):
    """Fast fractal-break strategy using 1m execution, 5m setup, and 1h veto."""

    scalping_interval_map = {
        "5m": "1m",
        "15m": "5m",
        "1h": "1h",
    }

    def __init__(self):
        super().__init__()
        self.min_hold_seconds = 60
        self.reentry_cooldown_seconds = 300
        self.default_stop_loss_pct = 0.8
        self.default_take_profit_pct = 0.0
        self.max_open_positions = 6
        self.pullback_lookback_bars = 2
        self.pullback_proximity_pct = 0.20 / 100.0

    def get_klines(self, symbol, interval, limit=100):
        """Remap inherited strategy labels to fast live intervals."""
        return super().get_klines(symbol, self.scalping_interval_map.get(interval, interval), limit)

    def get_available_strategies(self):
        """Use one strategy slot so capital and limits remain easy to reason about."""
        return ["fractal_break_scalping_strategy"]

    def get_strategy_profile(self, strategy_name):
        """Define the dedicated fractal-break scalping profile."""
        if strategy_name == "fractal_break_scalping_strategy":
            return {
                "leverage": 4.0,
                "risk_per_trade": 0.0025,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": True,
                "require_strong_5m_ha": True,
                "fractal_intervals": ["5m"],
                "candidate_limit": 5,
                "daily_entry_limit": 12,
                "exit_signal_threshold": 2,
                "symbol_mode": "balanced",
                "market_bias": "adaptive",
            }
        return super().get_strategy_profile(strategy_name)

    def get_session_policy(self, session=None):
        """Allow the fee-adjusted stronger sessions for the imported breakout idea."""
        policy = dict(super().get_session_policy(session))
        session_name = session or self.get_market_session()
        if session_name == "NORMAL":
            policy["position_size_multiplier"] = 0.55
        elif session_name in {"EU_PEAK", "ASIA_PEAK"}:
            policy["position_size_multiplier"] = 0.45
        elif session_name == "US_PEAK":
            policy["allow_new_entries"] = False
            policy["position_size_multiplier"] = 0.0
        elif session_name == "DEAD_ZONE":
            policy["allow_new_entries"] = False
            policy["position_size_multiplier"] = 0.0
        return policy

    def generate_strategy_signal(self, strategy_name, market_regime, symbol):
        """Route only the dedicated fast breakout strategy."""
        if strategy_name != "fractal_break_scalping_strategy":
            return None
        signal = self.get_fractal_break_signal(market_regime)
        if not signal:
            return None
        entry_price = self.safe_float_conversion(
            getattr(self, "current_prices", {}).get(symbol),
            self.safe_float_conversion(
                market_regime.get("timeframes", {}).get("5m", {}).get("current_price"),
                0.0,
            ),
        )
        if not self.is_structural_stop_acceptable(signal, entry_price, market_regime):
            return None
        return signal

    def get_fractal_break_signal(self, market_regime):
        """Return BUY or SELL only on confirmed fractal breakouts."""
        timeframe_data = market_regime.get("timeframes", {})
        tf_exec = timeframe_data.get("5m", {})
        tf_setup = timeframe_data.get("15m", {})
        trend_consensus = self.safe_float_conversion(market_regime.get("trend_consensus"), 0.0)

        current_price = self.safe_float_conversion(tf_exec.get("current_price"), 0.0)
        last_fractal_high = self.safe_float_conversion(tf_exec.get("last_fractal_high"), 0.0)
        last_fractal_low = self.safe_float_conversion(tf_exec.get("last_fractal_low"), 0.0)
        if current_price <= 0:
            return None

        ema_fast = self.safe_float_conversion(tf_exec.get("ema_fast"), 0.0)
        ema_mid = self.safe_float_conversion(tf_exec.get("ema_mid"), 0.0)
        ema_slow = self.safe_float_conversion(tf_exec.get("ema_slow"), 0.0)
        ema_spread = (max(ema_fast, ema_mid, ema_slow) - min(ema_fast, ema_mid, ema_slow)) / max(current_price, 1e-8)
        if ema_spread < 0.0006:
            return None

        buffer_pct = 0.0005
        strong_bull = bool(tf_exec.get("ha_strong_bullish")) or self.safe_float_conversion(tf_exec.get("ha_bull_count"), 0.0) >= 2
        strong_bear = bool(tf_exec.get("ha_strong_bearish")) or self.safe_float_conversion(tf_exec.get("ha_bear_count"), 0.0) >= 2

        setup_bullish = tf_setup.get("ema_fast", 0) > tf_setup.get("ema_mid", 0)
        setup_bearish = tf_setup.get("ema_fast", 0) < tf_setup.get("ema_mid", 0)

        if (
            setup_bullish and
            trend_consensus >= 0 and
            last_fractal_high > 0 and
            current_price > last_fractal_high * (1 + buffer_pct) and
            tf_exec.get("ha_trend") == "BULLISH" and
            strong_bull and
            ema_fast > ema_mid
        ):
            return "BUY"

        if (
            setup_bearish and
            trend_consensus <= 0 and
            last_fractal_low > 0 and
            current_price < last_fractal_low * (1 - buffer_pct) and
            tf_exec.get("ha_trend") == "BEARISH" and
            strong_bear and
            ema_fast < ema_mid
        ):
            return "SELL"

        return None

    def is_structural_stop_acceptable(self, entry_side, entry_price, market_regime):
        """Require a nearby confirmed fractal stop."""
        raw_stop = self.get_raw_structural_stop_price(entry_side, entry_price, market_regime)
        if raw_stop is None or entry_price <= 0:
            return False
        stop_distance = abs(entry_price - raw_stop) / entry_price
        return stop_distance <= 0.008

    def get_structural_stop_price(self, entry_side, entry_price, market_regime):
        """Return a capped fractal stop for fast breakout entries."""
        if entry_price <= 0 or not market_regime:
            return None
        raw_stop = self.get_raw_structural_stop_price(entry_side, entry_price, market_regime)
        if entry_side == "BUY":
            capped_stop = entry_price * 0.992
            if raw_stop is None:
                return capped_stop
            return max(raw_stop, capped_stop)

        capped_stop = entry_price * 1.008
        if raw_stop is None:
            return capped_stop
        return min(raw_stop, capped_stop)


CompletelyFixedAutoStrategyFuturesTrading = ScalpingAutoStrategyFuturesTrading


if __name__ == "__main__":
    trading = ScalpingAutoStrategyFuturesTrading()
    trading.run_trading()
