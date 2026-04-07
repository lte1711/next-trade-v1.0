#!/usr/bin/env python3
"""
Hybrid futures trading system.

This version leaves the v2 D-mode source untouched and routes entries by regime:
- TRENDING: use the existing v2 EMA + Heikin Ashi + fractal strategy.
- RANGING: use the SidewaysMarketStrategyV3 mean-reversion signal.
- NEUTRAL: do not open new positions.
"""

from __future__ import annotations

import time
from datetime import datetime

import pandas as pd

from completely_fixed_auto_strategy_trading_v2 import CompletelyFixedAutoStrategyFuturesTrading
from sideways_market_strategy_v3_existing_data import (
    RiskConfig,
    SidewaysMarketStrategyV3,
    StrategyConfig,
)


class HybridAutoStrategyFuturesTrading(CompletelyFixedAutoStrategyFuturesTrading):
    """Regime-routed v2 trend strategy plus sideways mean-reversion strategy."""

    sideways_strategy_name = "sideways_range_strategy"

    def __init__(self):
        self.sideways_engine = self.create_sideways_engine()
        self.sideways_min_confidence = 0.35
        self.sideways_signal_cache = {}
        super().__init__()

    @staticmethod
    def create_sideways_engine():
        """Create the tuned sideways-market engine."""
        return SidewaysMarketStrategyV3(
            strategy_config=StrategyConfig(
                ranging_adx_threshold=20.0,
                bandwidth_ranging_quantile=0.55,
                rsi_overbought=65.0,
                rsi_oversold=35.0,
                z_entry_threshold=1.20,
                low_volume_factor=0.50,
                tr_spike_atr_mult=2.30,
                realized_vol_spike_mult=2.00,
            ),
            risk_config=RiskConfig(
                risk_per_trade=0.004,
                atr_stop_mult=1.60,
                atr_take_mult=1.10,
                max_holding_bars=18,
            ),
        )

    def get_available_strategies(self):
        strategies = super().get_available_strategies()
        if self.sideways_strategy_name not in strategies:
            strategies.append(self.sideways_strategy_name)
        return strategies

    def get_strategy_profile(self, strategy_name):
        if strategy_name == self.sideways_strategy_name:
            return {
                "leverage": 8.0,
                "risk_per_trade": 0.004,
                "required_alignment_count": 0,
                "consensus_threshold": 0,
                "require_volume_expansion": False,
                "require_cross": False,
                "require_ha_alignment": False,
                "require_strong_5m_ha": False,
                "fractal_intervals": ["5m"],
                "candidate_limit": 6,
                "daily_entry_limit": 4,
                "exit_signal_threshold": 2,
                "symbol_mode": "balanced",
                "market_bias": "adaptive",
            }
        profile = dict(super().get_strategy_profile(strategy_name))
        if strategy_name == "pullback_confirmation_strategy":
            profile.update({
                "risk_per_trade": 0.009,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "exit_signal_threshold": 3,
                "daily_entry_limit": 4,
                "require_ha_alignment": True,
                "fractal_intervals": ["5m", "15m"],
                "candidate_limit": 6,
            })
        elif strategy_name == "balanced_rotation_strategy":
            profile.update({
                "risk_per_trade": 0.006,
                "required_alignment_count": 1,
                "consensus_threshold": 1,
                "daily_entry_limit": 3,
                "fractal_intervals": ["5m", "15m"],
                "candidate_limit": 6,
            })
        elif strategy_name == "volatility_strategy":
            profile.update({
                "risk_per_trade": 0.008,
                "consensus_threshold": 3,
                "daily_entry_limit": 4,
            })
        return profile

    def get_ma_trade_decision(self, strategy, market_regime):
        """Apply a 1h trend, 15m setup, and 5m execution MA filter."""
        signal = super().get_ma_trade_decision(strategy, market_regime)
        if not signal:
            return None

        timeframe_data = market_regime.get("timeframes", {})
        tf_5m = timeframe_data.get("5m", {})
        tf_15m = timeframe_data.get("15m", {})
        tf_1h = timeframe_data.get("1h", {})
        trend_consensus = self.safe_float_conversion(market_regime.get("trend_consensus"), 0.0)
        volume_expansion_count = sum(1 for tf in timeframe_data.values() if tf.get("volume_expansion"))
        current_price = self.safe_float_conversion(tf_15m.get("current_price"), 0.0)
        ema_mid_15m = self.safe_float_conversion(tf_15m.get("ema_mid"), 0.0)
        ema_fast_15m = self.safe_float_conversion(tf_15m.get("ema_fast"), 0.0)
        ema_slow_15m = self.safe_float_conversion(tf_15m.get("ema_slow"), 0.0)
        current_price_5m = self.safe_float_conversion(tf_5m.get("current_price"), current_price)
        ema_fast_5m = self.safe_float_conversion(tf_5m.get("ema_fast"), 0.0)
        ema_mid_5m = self.safe_float_conversion(tf_5m.get("ema_mid"), 0.0)
        ema_slow_5m = self.safe_float_conversion(tf_5m.get("ema_slow"), 0.0)
        ema_mid_1h = self.safe_float_conversion(tf_1h.get("ema_mid"), 0.0)
        ema_fast_1h = self.safe_float_conversion(tf_1h.get("ema_fast"), 0.0)
        ema_gap_15m = abs(ema_fast_15m - ema_mid_15m) / max(current_price, 1e-8)
        ema_gap_1h = abs(ema_fast_1h - ema_mid_1h) / max(current_price, 1e-8)
        ema_spread_15m = (
            max(ema_fast_15m, ema_mid_15m, ema_slow_15m) -
            min(ema_fast_15m, ema_mid_15m, ema_slow_15m)
        ) / max(current_price, 1e-8)
        ema_spread_5m = (
            max(ema_fast_5m, ema_mid_5m, ema_slow_5m) -
            min(ema_fast_5m, ema_mid_5m, ema_slow_5m)
        ) / max(current_price_5m, 1e-8)
        minimum_ema_gap = 0.0008
        minimum_1h_ema_gap = 0.0005
        has_15m_strength = ema_gap_15m >= minimum_ema_gap
        has_1h_strength = ema_gap_1h >= minimum_1h_ema_gap
        ema_tangled = ema_spread_15m < 0.0010 and ema_spread_5m < 0.0007
        long_setup = bool(tf_15m.get("recent_breakout_up") or tf_15m.get("fractal_breakout_up"))
        short_setup = bool(tf_15m.get("recent_breakout_down") or tf_15m.get("fractal_breakout_down"))
        fractal_break_buffer = 0.0005
        last_5m_fractal_high = self.safe_float_conversion(tf_5m.get("last_fractal_high"), 0.0)
        last_5m_fractal_low = self.safe_float_conversion(tf_5m.get("last_fractal_low"), 0.0)
        imported_fractal_break_up = (
            last_5m_fractal_high > 0 and
            current_price_5m > last_5m_fractal_high * (1 + fractal_break_buffer) and
            tf_5m.get("ha_trend") == "BULLISH" and
            (bool(tf_5m.get("ha_strong_bullish")) or self.safe_float_conversion(tf_5m.get("ha_bull_count"), 0.0) >= 2)
        )
        imported_fractal_break_down = (
            last_5m_fractal_low > 0 and
            current_price_5m < last_5m_fractal_low * (1 - fractal_break_buffer) and
            tf_5m.get("ha_trend") == "BEARISH" and
            (bool(tf_5m.get("ha_strong_bearish")) or self.safe_float_conversion(tf_5m.get("ha_bear_count"), 0.0) >= 2)
        )
        long_execution = bool(
            tf_5m.get("pullback_entry_up") or
            tf_5m.get("fractal_breakout_up") or
            imported_fractal_break_up
        )
        short_execution = bool(
            tf_5m.get("pullback_entry_down") or
            tf_5m.get("fractal_breakout_down") or
            imported_fractal_break_down
        )
        bullish_15m_direction = (
            tf_15m.get("alignment") == "BULLISH" and
            tf_15m.get("price_vs_ma") == "ABOVE" and
            tf_15m.get("ema_fast", 0) > tf_15m.get("ema_mid", 0)
        )
        bearish_15m_direction = (
            tf_15m.get("alignment") == "BEARISH" and
            tf_15m.get("price_vs_ma") == "BELOW" and
            tf_15m.get("ema_fast", 0) < tf_15m.get("ema_mid", 0)
        )
        bullish_1h_veto = tf_1h.get("alignment") == "BEARISH" and trend_consensus <= -1
        bearish_1h_veto = tf_1h.get("alignment") == "BULLISH" and trend_consensus >= 1

        if signal == "BUY":
            if ema_tangled:
                return None
            if trend_consensus < 2:
                return None
            if bullish_1h_veto or not bullish_15m_direction:
                return None
            if not has_15m_strength or not has_1h_strength:
                return None
            if not long_setup or not long_execution:
                return None
            if tf_5m.get("ema_fast", 0) <= tf_5m.get("ema_mid", 0):
                return None
            if tf_15m.get("ema_fast", 0) <= tf_15m.get("ema_mid", 0):
                return None
        elif signal == "SELL":
            if ema_tangled:
                return None
            if trend_consensus > -2:
                return None
            if bearish_1h_veto or not bearish_15m_direction:
                return None
            if not has_15m_strength or not has_1h_strength:
                return None
            if not short_setup or not short_execution:
                return None
            if tf_5m.get("ema_fast", 0) >= tf_5m.get("ema_mid", 0):
                return None
            if tf_15m.get("ema_fast", 0) >= tf_15m.get("ema_mid", 0):
                return None

        if strategy.get("strategy_type") in {"momentum_strategy", "volatility_strategy"} and volume_expansion_count < 1:
            return None
        return signal

    def get_sideways_frame(self, symbol, interval="5m", limit=160):
        """Build an OHLCV frame for the sideways strategy."""
        rows = self.get_klines(symbol, interval, limit)
        if len(rows) > 1:
            rows = rows[:-1]
        if len(rows) < self.sideways_engine.risk.min_data_bars:
            return None

        frame = pd.DataFrame(
            [
                {
                    "open": self.safe_float_conversion(row[1], 0.0),
                    "high": self.safe_float_conversion(row[2], 0.0),
                    "low": self.safe_float_conversion(row[3], 0.0),
                    "close": self.safe_float_conversion(row[4], 0.0),
                    "volume": self.safe_float_conversion(row[5], 0.0),
                }
                for row in rows
            ]
        )
        if frame.empty or (frame[["open", "high", "low", "close"]] <= 0).any().any():
            return None
        return frame

    def get_sideways_snapshot(self, symbol):
        """Return the latest prepared sideways-regime row for a symbol."""
        cache_key = (symbol, datetime.now().replace(second=0, microsecond=0).isoformat())
        if cache_key in self.sideways_signal_cache:
            return self.sideways_signal_cache[cache_key]

        frame = self.get_sideways_frame(symbol)
        if frame is None:
            return None

        try:
            prepared = self.sideways_engine.prepare_features(frame)
            snapshot = prepared.iloc[-1].to_dict()
            self.sideways_signal_cache = {cache_key: snapshot}
            return snapshot
        except Exception as exc:
            self.log_system_error("sideways_signal_error", f"{symbol}: {exc}")
            return None

    def get_routed_regime(self, symbol, market_regime):
        """Classify the active routing regime for the symbol."""
        sideways_snapshot = self.get_sideways_snapshot(symbol)
        if sideways_snapshot and sideways_snapshot.get("market_regime") == "RANGING":
            return "RANGING"

        trend_consensus = self.safe_float_conversion(market_regime.get("trend_consensus"), 0.0)
        if abs(trend_consensus) >= 2:
            return "TRENDING"
        return "NEUTRAL"

    def get_sideways_signal(self, symbol):
        """Return a sideways-market BUY/SELL signal when confidence is sufficient."""
        snapshot = self.get_sideways_snapshot(symbol)
        if not snapshot:
            return None
        if snapshot.get("market_regime") != "RANGING":
            return None
        if bool(snapshot.get("whipsaw_blocked", False)):
            return None
        signal = snapshot.get("signal")
        confidence = self.safe_float_conversion(snapshot.get("confidence"), 0.0)
        if signal in {"BUY", "SELL"} and confidence >= self.sideways_min_confidence:
            return signal
        return None

    def generate_strategy_signal(self, strategy_name, market_regime, symbol):
        """Route signals so trend and range engines do not conflict."""
        routed_regime = self.get_routed_regime(symbol, market_regime)

        if routed_regime == "RANGING":
            if strategy_name != self.sideways_strategy_name:
                return None
            return self.get_sideways_signal(symbol)

        if routed_regime == "TRENDING":
            if strategy_name == self.sideways_strategy_name:
                return None
            signal = super().generate_strategy_signal(strategy_name, market_regime, symbol)
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

        return None

    def get_managed_symbols(self):
        """Return the symbols this instance is allowed to manage."""
        configured = getattr(self, "managed_symbols", None)
        if configured:
            return {symbol for symbol in configured}
        return {symbol for symbol in getattr(self, "valid_symbols", [])}

    def owns_active_position(self, symbol):
        """Return whether this process has a local entry record for the symbol."""
        for trade in reversed(self.trading_results.get("real_orders", [])):
            if trade.get("symbol") != symbol:
                continue
            if trade.get("reduce_only"):
                return False
            return trade.get("status") in {"FILLED", "NEW", "PARTIALLY_FILLED"}
        return False

    def get_owned_active_positions(self):
        """Return active positions opened by this process only."""
        managed_symbols = self.get_managed_symbols()
        return {
            symbol: position
            for symbol, position in self.trading_results.get("active_positions", {}).items()
            if symbol in managed_symbols and self.owns_active_position(symbol)
        }

    def manage_open_positions(self):
        """Manage only positions that belong to this instance's symbol scope."""
        try:
            self.sync_positions()
            active_positions = self.get_owned_active_positions()
            if not active_positions:
                return

            for symbol, position in list(active_positions.items()):
                if not self.is_past_min_hold(symbol):
                    continue
                market_regime = self.analyze_market_regime(symbol)
                strategy = self.get_position_strategy(symbol)
                exit_reason = (
                    self.should_exit_position_ema21_trailing(position, market_regime) or
                    self.should_exit_position_ma(position, market_regime, strategy)
                )
                if exit_reason:
                    self.close_position(symbol, position, exit_reason)

            active_positions = self.get_owned_active_positions()
            if len(active_positions) > self.max_open_positions:
                excess = len(active_positions) - self.max_open_positions
                ranked = sorted(
                    active_positions.items(),
                    key=lambda item: self.safe_float_conversion(item[1].get("percentage"), 0.0),
                )
                for symbol, position in ranked[:excess]:
                    self.close_position(symbol, position, "position_limit")
        except Exception as exc:
            self.log_system_error("position_management_error", str(exc))

    def run_trading(self):
        """Run the main loop using only owned positions for entry limits."""
        print("[INFO] Auto futures trading started")

        try:
            while datetime.now() < self.end_time and self.running:
                try:
                    self.trading_results["market_session"] = self.get_market_session()
                    self.refresh_symbol_universe()
                    self.update_market_data()
                    self.refresh_pending_orders()
                    self.manage_open_positions()

                    if self.can_open_new_positions():
                        for strategy_name in self.strategies:
                            if len(self.get_owned_active_positions()) >= self.max_open_positions:
                                break
                            self.execute_strategy_trade(strategy_name)
                    else:
                        self.trading_results["sync_status"] = "ACCOUNT_DATA_UNAVAILABLE"

                    time.sleep(30)
                except Exception as exc:
                    self.log_system_error("trading_loop_error", str(exc))
                    time.sleep(30)
        except KeyboardInterrupt:
            print("\n[WARN] Auto trading interrupted")
        except Exception as exc:
            self.log_system_error("result_save_error", str(exc))
            print(f"\n[ERROR] Trading runtime error: {exc}")
        finally:
            self.running = False
            self.save_results()
            print("[INFO] Auto futures trading finished")

    def get_raw_structural_stop_price(self, entry_side, entry_price, market_regime):
        """Return the nearest confirmed fractal stop without applying the percentage cap."""
        if entry_price <= 0 or not market_regime:
            return None

        timeframe_data = market_regime.get("timeframes", {})
        if entry_side == "BUY":
            stop_candidates = []
            for interval in ("5m", "15m"):
                fractal_low = self.safe_float_conversion(
                    timeframe_data.get(interval, {}).get("last_fractal_low"),
                    0.0,
                )
                if 0 < fractal_low < entry_price:
                    stop_candidates.append(fractal_low)
            return max(stop_candidates) if stop_candidates else None

        stop_candidates = []
        for interval in ("5m", "15m"):
            fractal_high = self.safe_float_conversion(
                timeframe_data.get(interval, {}).get("last_fractal_high"),
                0.0,
            )
            if fractal_high > entry_price:
                stop_candidates.append(fractal_high)
        return min(stop_candidates) if stop_candidates else None

    def is_structural_stop_acceptable(self, entry_side, entry_price, market_regime):
        """Skip entries whose confirmed fractal stop is missing or wider than the cap."""
        raw_stop = self.get_raw_structural_stop_price(entry_side, entry_price, market_regime)
        if raw_stop is None or entry_price <= 0:
            return False
        stop_distance = abs(entry_price - raw_stop) / entry_price
        return stop_distance <= (self.default_stop_loss_pct / 100.0)

    def get_structural_stop_price(self, entry_side, entry_price, market_regime):
        """Return a capped fractal-based stop price for trend entries."""
        if entry_price <= 0 or not market_regime:
            return None

        raw_stop = self.get_raw_structural_stop_price(entry_side, entry_price, market_regime)
        if entry_side == "BUY":
            capped_stop = entry_price * (1 - self.default_stop_loss_pct / 100.0)
            if raw_stop is None:
                return capped_stop
            return max(raw_stop, capped_stop)

        capped_stop = entry_price * (1 + self.default_stop_loss_pct / 100.0)
        if raw_stop is None:
            return capped_stop
        return min(raw_stop, capped_stop)

    def place_protective_orders(self, strategy_name, symbol, entry_side, entry_price, market_regime=None):
        """Use ATR exits for sideways trades and v2 D-mode stop exits otherwise."""
        if strategy_name != self.sideways_strategy_name:
            exit_side = "SELL" if entry_side == "BUY" else "BUY"
            if market_regime is None:
                market_regime = self.analyze_market_regime(symbol)
            stop_price = self.get_structural_stop_price(entry_side, entry_price, market_regime)
            if stop_price is None:
                return super().place_protective_orders(strategy_name, symbol, entry_side, entry_price)
            self.cancel_symbol_protective_orders(symbol)
            return self.submit_protective_order(symbol, exit_side, "STOP_MARKET", stop_price)

        snapshot = self.get_sideways_snapshot(symbol)
        atr = self.safe_float_conversion(snapshot.get("atr") if snapshot else None, 0.0)
        bb_mid = self.safe_float_conversion(snapshot.get("bb_mid") if snapshot else None, entry_price)
        if entry_price <= 0 or atr <= 0:
            return super().place_protective_orders(strategy_name, symbol, entry_side, entry_price)

        risk = self.sideways_engine.risk
        exit_side = "SELL" if entry_side == "BUY" else "BUY"
        if entry_side == "BUY":
            stop_price = entry_price - atr * risk.atr_stop_mult
            take_price = min(bb_mid, entry_price + atr * risk.atr_take_mult) if bb_mid > entry_price else entry_price + atr * risk.atr_take_mult
        else:
            stop_price = entry_price + atr * risk.atr_stop_mult
            take_price = max(bb_mid, entry_price - atr * risk.atr_take_mult) if bb_mid < entry_price else entry_price - atr * risk.atr_take_mult

        self.cancel_symbol_protective_orders(symbol)
        self.submit_protective_order(symbol, exit_side, "STOP_MARKET", stop_price)
        self.submit_protective_order(symbol, exit_side, "TAKE_PROFIT_MARKET", take_price)


CompletelyFixedAutoStrategyFuturesTrading = HybridAutoStrategyFuturesTrading


if __name__ == "__main__":
    trading = HybridAutoStrategyFuturesTrading()
    trading.run_trading()
