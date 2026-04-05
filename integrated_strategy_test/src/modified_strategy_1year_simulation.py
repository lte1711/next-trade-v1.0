#!/usr/bin/env python3
"""
Deterministic 1-year synthetic backtest aligned more closely to the modular strategy.

What this version fixes:
- deterministic synthetic data via a fixed random seed
- market-regime thresholds aligned to bar-level percent changes
- regime-aware entry thresholds instead of a hard-coded 70
- cooldown semantics translated from minutes to bar counts explicitly
- richer outputs: rebalancing events, individual performance, and comparison report

The generated data is still synthetic. This script is useful for comparative
strategy tuning, not for claiming production-grade historical validation.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
OLD_RESULTS_PATH = SCRIPT_DIR / "modified_strategy_1year_results.json"
NEW_RESULTS_PATH = SCRIPT_DIR / "modified_strategy_1year_results_v2.json"
COMPARISON_REPORT_PATH = SCRIPT_DIR / "modified_strategy_1year_comparison_report.md"

SEED = 20260405
INITIAL_CAPITAL = 1000.0
FIXED_ALLOCATION = 100.0
TRADING_FEE = 0.0004
REPLACEMENT_THRESHOLD = -0.8
TAKE_PROFIT = 1.5
REENTRY_COOLDOWN_MINUTES = 20
COOLDOWN_BARS = max(1, math.ceil(REENTRY_COOLDOWN_MINUTES / 1440.0))

REGIME_VOLATILITY_THRESHOLDS = {
    "EXTREME": 5.0,
    "HIGH_VOLATILITY": 2.5,
}

ENTRY_THRESHOLDS = {
    "EXTREME": 66.0,
    "HIGH_VOLATILITY": 70.0,
    "NORMAL": 68.0,
}

MAX_SYMBOLS_BY_REGIME = {
    "EXTREME": 3,
    "HIGH_VOLATILITY": 5,
    "NORMAL": 10,
}

ENTRY_BUFFER = 0.0
EXIT_BUFFER = 3.0
MINIMUM_HOLD_BARS = 1
PROFIT_POTENTIAL_OFFSET = 18.0

DEFAULT_PROFILE = {
    "name": "baseline_v2",
    "take_profit": TAKE_PROFIT,
    "reentry_cooldown_minutes": REENTRY_COOLDOWN_MINUTES,
    "reentry_cooldown_bars": COOLDOWN_BARS,
    "entry_thresholds": ENTRY_THRESHOLDS,
    "max_symbols_by_regime": MAX_SYMBOLS_BY_REGIME,
    "entry_buffer": ENTRY_BUFFER,
    "exit_buffer": EXIT_BUFFER,
    "profit_potential_offset": PROFIT_POTENTIAL_OFFSET,
    "replacement_threshold": REPLACEMENT_THRESHOLD,
    "trading_fee": TRADING_FEE,
    "regime_volatility_thresholds": REGIME_VOLATILITY_THRESHOLDS,
    "fixed_allocation": FIXED_ALLOCATION,
    "minimum_hold_bars": MINIMUM_HOLD_BARS,
    "partial_take_profit": None,
    "partial_take_profit_ratio": 0.5,
    "trailing_stop_activation": None,
    "trailing_stop_drawdown": None,
    "dynamic_sizing": False,
    "allocation_min": FIXED_ALLOCATION,
    "allocation_max": FIXED_ALLOCATION,
    "allocation_score_floor": 60.0,
    "allocation_score_ceiling": 90.0,
    "allow_reacceleration": False,
    "reacceleration_bullish_bonus": 4.0,
    "reacceleration_profit_offset": 10.0,
    "reacceleration_add_fraction": 0.5,
    "reacceleration_min_pnl_percent": 0.8,
    "max_reaccelerations_per_position": 1,
}

V3_CANDIDATE_PROFILE = {
    "name": "v3_candidate_cs_more_entries",
    "entry_thresholds": {"NORMAL": 58.0, "HIGH_VOLATILITY": 60.0, "EXTREME": 56.0},
    "profit_potential_offset": 28.0,
    "entry_buffer": -4.0,
    "exit_buffer": 5.0,
    "max_symbols_by_regime": {"NORMAL": 2, "HIGH_VOLATILITY": 2, "EXTREME": 1},
    "fixed_allocation": 180.0,
    "take_profit": 2.6,
    "replacement_threshold": -1.1,
    "minimum_hold_bars": 1,
}

REMOTE_V3_REFERENCE_PROFILE = {
    "name": "v3_remote_reference_low_churn",
    "entry_thresholds": {"NORMAL": 68.0, "HIGH_VOLATILITY": 72.0, "EXTREME": 76.0},
    "regime_volatility_thresholds": {"EXTREME": 16.0, "HIGH_VOLATILITY": 8.0},
    "profit_potential_offset": 16.0,
    "entry_buffer": 0.0,
    "exit_buffer": 6.0,
    "max_symbols_by_regime": {"NORMAL": 1, "HIGH_VOLATILITY": 1, "EXTREME": 1},
    "fixed_allocation": 180.0,
    "take_profit": 3.0,
    "replacement_threshold": -1.3,
    "minimum_hold_bars": 2,
}

REMOTE_V3_DEFAULT_PROFILE = {
    "name": "v3_remote_default_capital_preserver",
    "entry_thresholds": {"NORMAL": 72.0, "HIGH_VOLATILITY": 76.0, "EXTREME": 80.0},
    "regime_volatility_thresholds": {"EXTREME": 18.0, "HIGH_VOLATILITY": 9.0},
    "profit_potential_offset": 16.0,
    "entry_buffer": 0.0,
    "exit_buffer": 6.0,
    "max_symbols_by_regime": {"NORMAL": 1, "HIGH_VOLATILITY": 1, "EXTREME": 1},
    "fixed_allocation": 140.0,
    "take_profit": 2.6,
    "replacement_threshold": -0.9,
    "minimum_hold_bars": 2,
}

SYMBOL_CONFIG = {
    "BTCUSDT": {"price": 65000.0, "beta": 1.0, "base_vol": 0.020, "quote_volume": 90_000_000},
    "ETHUSDT": {"price": 3500.0, "beta": 1.2, "base_vol": 0.024, "quote_volume": 70_000_000},
    "BNBUSDT": {"price": 600.0, "beta": 0.9, "base_vol": 0.021, "quote_volume": 40_000_000},
    "XRPUSDT": {"price": 0.65, "beta": 1.4, "base_vol": 0.032, "quote_volume": 30_000_000},
    "DOGEUSDT": {"price": 0.15, "beta": 1.6, "base_vol": 0.038, "quote_volume": 25_000_000},
    "BCHUSDT": {"price": 650.0, "beta": 1.1, "base_vol": 0.028, "quote_volume": 18_000_000},
    "QUICKUSDT": {"price": 1200.0, "beta": 1.8, "base_vol": 0.050, "quote_volume": 7_000_000},
    "LRCUSDT": {"price": 0.25, "beta": 1.7, "base_vol": 0.045, "quote_volume": 9_000_000},
}


@dataclass
class Position:
    symbol: str
    initial_investment: float
    net_investment: float
    shares: float
    entry_price: float
    current_price: float
    current_value: float
    entry_date: str
    entry_day_index: int
    entry_bullish_score: float
    last_profit_potential: float
    pnl: float = 0.0
    pnl_percent: float = 0.0
    peak_pnl_percent: float = 0.0
    partial_exit_done: bool = False
    reaccelerations_done: int = 0
    last_scaled_day_index: int = -1


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def generate_historical_data(seed: int = SEED) -> list[dict[str, Any]]:
    """Generate deterministic daily bars with market regimes and cross-symbol correlation."""
    rng = random.Random(seed)
    start_date = datetime(2025, 4, 2)
    end_date = datetime(2026, 4, 2)

    regime_segments = [
        (0, 45, "NORMAL", 0.0005, 0.012),
        (45, 95, "HIGH_VOLATILITY", -0.0002, 0.028),
        (95, 140, "NORMAL", 0.0008, 0.014),
        (140, 190, "EXTREME", -0.0006, 0.050),
        (190, 250, "HIGH_VOLATILITY", 0.0003, 0.026),
        (250, 310, "NORMAL", 0.0009, 0.013),
        (310, 366, "HIGH_VOLATILITY", -0.0001, 0.024),
    ]

    def get_regime(day_index: int) -> tuple[str, float, float]:
        for start, end, name, drift, sigma in regime_segments:
            if start <= day_index < end:
                return name, drift, sigma
        return "NORMAL", 0.0005, 0.012

    historical_data: list[dict[str, Any]] = []
    price_state = {symbol: cfg["price"] for symbol, cfg in SYMBOL_CONFIG.items()}
    change_windows = {symbol: deque(maxlen=20) for symbol in SYMBOL_CONFIG}
    volume_windows = {symbol: deque(maxlen=20) for symbol in SYMBOL_CONFIG}

    current_date = start_date
    day_index = 0
    while current_date <= end_date:
        regime_name, market_drift, market_sigma = get_regime(day_index)
        market_return = rng.gauss(market_drift, market_sigma)

        daily_symbols: dict[str, Any] = {}
        for symbol, cfg in SYMBOL_CONFIG.items():
            idio = rng.gauss(0.0, cfg["base_vol"])
            drift = market_return * cfg["beta"] + idio
            drift = clamp(drift, -0.18, 0.18)

            previous_price = price_state[symbol]
            new_price = max(previous_price * (1.0 + drift), 0.0001)
            intraday_vol = abs(drift) + rng.uniform(cfg["base_vol"] * 0.4, cfg["base_vol"] * 1.2)
            intraday_vol = clamp(intraday_vol, 0.003, 0.25)

            volume_multiplier = 1.0 + abs(drift) * 4.0 + (0.15 if regime_name != "NORMAL" else 0.0)
            quote_volume = cfg["quote_volume"] * volume_multiplier * rng.uniform(0.85, 1.20)

            change_pct = drift * 100.0
            volatility_pct = intraday_vol * 100.0

            change_windows[symbol].append(change_pct)
            volume_windows[symbol].append(quote_volume)

            high = new_price * (1.0 + rng.uniform(0.002, intraday_vol))
            low = new_price * max(0.5, 1.0 - rng.uniform(0.002, intraday_vol))

            daily_symbols[symbol] = {
                "price": round(new_price, 4),
                "change": round(change_pct, 4),
                "volatility": round(volatility_pct, 4),
                "volume": int(quote_volume / max(new_price, 0.0001)),
                "quote_volume": round(quote_volume, 2),
                "high": round(high, 4),
                "low": round(low, 4),
                "synthetic_regime": regime_name,
                "change_history": list(change_windows[symbol]),
                "quote_volume_history": list(volume_windows[symbol]),
            }

            price_state[symbol] = new_price

        historical_data.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "timestamp": current_date.isoformat(),
                "synthetic_regime": regime_name,
                "symbols": daily_symbols,
            }
        )

        current_date += timedelta(days=1)
        day_index += 1

    return historical_data


def build_profile(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = {
        "name": DEFAULT_PROFILE["name"],
        "take_profit": DEFAULT_PROFILE["take_profit"],
        "reentry_cooldown_minutes": DEFAULT_PROFILE["reentry_cooldown_minutes"],
        "reentry_cooldown_bars": DEFAULT_PROFILE["reentry_cooldown_bars"],
        "entry_thresholds": dict(DEFAULT_PROFILE["entry_thresholds"]),
        "max_symbols_by_regime": dict(DEFAULT_PROFILE["max_symbols_by_regime"]),
        "entry_buffer": DEFAULT_PROFILE["entry_buffer"],
        "exit_buffer": DEFAULT_PROFILE["exit_buffer"],
        "profit_potential_offset": DEFAULT_PROFILE["profit_potential_offset"],
        "replacement_threshold": DEFAULT_PROFILE["replacement_threshold"],
        "trading_fee": DEFAULT_PROFILE["trading_fee"],
        "regime_volatility_thresholds": dict(DEFAULT_PROFILE["regime_volatility_thresholds"]),
        "fixed_allocation": DEFAULT_PROFILE["fixed_allocation"],
        "minimum_hold_bars": DEFAULT_PROFILE["minimum_hold_bars"],
        "partial_take_profit": DEFAULT_PROFILE["partial_take_profit"],
        "partial_take_profit_ratio": DEFAULT_PROFILE["partial_take_profit_ratio"],
        "trailing_stop_activation": DEFAULT_PROFILE["trailing_stop_activation"],
        "trailing_stop_drawdown": DEFAULT_PROFILE["trailing_stop_drawdown"],
        "dynamic_sizing": DEFAULT_PROFILE["dynamic_sizing"],
        "allocation_min": DEFAULT_PROFILE["allocation_min"],
        "allocation_max": DEFAULT_PROFILE["allocation_max"],
        "allocation_score_floor": DEFAULT_PROFILE["allocation_score_floor"],
        "allocation_score_ceiling": DEFAULT_PROFILE["allocation_score_ceiling"],
        "allow_reacceleration": DEFAULT_PROFILE["allow_reacceleration"],
        "reacceleration_bullish_bonus": DEFAULT_PROFILE["reacceleration_bullish_bonus"],
        "reacceleration_profit_offset": DEFAULT_PROFILE["reacceleration_profit_offset"],
        "reacceleration_add_fraction": DEFAULT_PROFILE["reacceleration_add_fraction"],
        "reacceleration_min_pnl_percent": DEFAULT_PROFILE["reacceleration_min_pnl_percent"],
        "max_reaccelerations_per_position": DEFAULT_PROFILE["max_reaccelerations_per_position"],
    }
    if overrides:
        for key, value in overrides.items():
            if key in {"entry_thresholds", "max_symbols_by_regime", "regime_volatility_thresholds"}:
                profile[key] = dict(value)
            else:
                profile[key] = value
    return profile


def calculate_market_regime(daily_data: dict[str, Any], regime_volatility_thresholds: dict[str, float]) -> str:
    changes = [abs(symbol_data["change"]) for symbol_data in daily_data["symbols"].values()]
    avg_volatility = sum(changes) / len(changes)
    if avg_volatility > regime_volatility_thresholds["EXTREME"]:
        return "EXTREME"
    if avg_volatility > regime_volatility_thresholds["HIGH_VOLATILITY"]:
        return "HIGH_VOLATILITY"
    return "NORMAL"


def calculate_profit_potential(symbol_data: dict[str, Any]) -> float:
    change = symbol_data["change"]
    volatility = symbol_data["volatility"]
    quote_volume = symbol_data["quote_volume"]
    change_history = symbol_data.get("change_history", [])
    volume_history = symbol_data.get("quote_volume_history", [])

    score = 0.0
    if change > 0:
        score += min(change * 4.0, 35.0)

    if change_history:
        short_mean = sum(change_history[-5:]) / min(5, len(change_history))
        long_mean = sum(change_history) / len(change_history)
        trend_delta = short_mean - long_mean
        score += clamp(trend_delta * 4.0, -10.0, 15.0)

    if 2.0 <= volatility <= 6.5:
        score += 18.0
    elif 1.0 <= volatility < 2.0 or 6.5 < volatility <= 9.0:
        score += 10.0
    elif volatility > 9.0:
        score += 4.0

    if volume_history:
        baseline_volume = sum(volume_history) / len(volume_history)
        volume_ratio = quote_volume / baseline_volume if baseline_volume else 1.0
        score += clamp((volume_ratio - 1.0) * 20.0, -5.0, 15.0)

    return clamp(score, 0.0, 100.0)


def calculate_bullish_score(symbol_data: dict[str, Any], market_regime: str) -> float:
    change = symbol_data["change"]
    volatility = symbol_data["volatility"]
    quote_volume = symbol_data["quote_volume"]
    change_history = symbol_data.get("change_history", [])
    volume_history = symbol_data.get("quote_volume_history", [])

    score = 0.0

    if change > 0:
        score += min(change * 5.0, 25.0)
    else:
        score += max(change * 2.0, -10.0)

    if change_history:
        short_mean = sum(change_history[-5:]) / min(5, len(change_history))
        long_mean = sum(change_history) / len(change_history)
        trend_delta = short_mean - long_mean
        if short_mean > 0 and trend_delta > 0:
            score += 22.0
        elif short_mean > 0:
            score += 14.0
        elif trend_delta > 0:
            score += 8.0

    if 2.0 <= volatility <= 6.5:
        score += 15.0
    elif 1.0 <= volatility < 2.0 or 6.5 < volatility <= 9.0:
        score += 8.0
    elif volatility > 9.0:
        score += 3.0

    if volume_history:
        avg_volume = sum(volume_history) / len(volume_history)
        volume_ratio = quote_volume / avg_volume if avg_volume else 1.0
        score += clamp((volume_ratio - 1.0) * 18.0, -5.0, 13.0)

    liquidity_bonus = clamp((math.log10(max(quote_volume, 1.0)) - 6.5) * 8.0, 0.0, 15.0)
    score += liquidity_bonus

    if market_regime == "EXTREME":
        score -= 3.0
    elif market_regime == "HIGH_VOLATILITY":
        score -= 1.0

    return clamp(score, 0.0, 100.0)


def calculate_target_allocation(
    profile: dict[str, Any],
    bullish_score: float,
    profit_potential: float,
    cash_balance: float,
) -> float:
    base_allocation = profile["fixed_allocation"]
    if not profile.get("dynamic_sizing"):
        return min(base_allocation, cash_balance)

    allocation_min = min(profile.get("allocation_min", base_allocation), profile.get("allocation_max", base_allocation))
    allocation_max = max(profile.get("allocation_min", base_allocation), profile.get("allocation_max", base_allocation))
    score_floor = profile.get("allocation_score_floor", 60.0)
    score_ceiling = max(score_floor + 0.001, profile.get("allocation_score_ceiling", 90.0))
    combined_score = (bullish_score + profit_potential) / 2.0
    normalized = clamp((combined_score - score_floor) / (score_ceiling - score_floor), 0.0, 1.0)
    target_allocation = allocation_min + (allocation_max - allocation_min) * normalized
    return min(target_allocation, cash_balance)


def simulate_modified_strategy(historical_data: list[dict[str, Any]], profile_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = build_profile(profile_overrides)
    cash_balance = INITIAL_CAPITAL
    investments: dict[str, Position] = {}
    realized_pnl = 0.0
    total_fees = 0.0
    performance_history: list[dict[str, Any]] = []
    trade_history: list[dict[str, Any]] = []
    rebalancing_events: list[dict[str, Any]] = []
    cooldowns: dict[str, int] = {}

    for day_index, daily_data in enumerate(historical_data):
        market_regime = calculate_market_regime(daily_data, profile["regime_volatility_thresholds"])
        entry_threshold = profile["entry_thresholds"][market_regime]
        max_symbols = profile["max_symbols_by_regime"][market_regime]

        evaluated_symbols = []
        for symbol, symbol_data in daily_data["symbols"].items():
            bullish_score = calculate_bullish_score(symbol_data, market_regime)
            profit_potential = calculate_profit_potential(symbol_data)
            evaluated_symbols.append(
                {
                    "symbol": symbol,
                    "price": symbol_data["price"],
                    "change": symbol_data["change"],
                    "quote_volume": symbol_data["quote_volume"],
                    "bullish_score": bullish_score,
                    "profit_potential": profit_potential,
                }
            )

        evaluated_symbols.sort(
            key=lambda item: (item["bullish_score"], item["profit_potential"], item["quote_volume"]),
            reverse=True,
        )

        unrealized_pnl = 0.0
        symbols_to_remove: list[tuple[str, str, float]] = []
        for symbol, position in list(investments.items()):
            current_price = daily_data["symbols"][symbol]["price"]
            current_value = position.shares * current_price
            pnl = current_value - position.net_investment
            pnl_percent = (pnl / position.net_investment) * 100.0

            position.current_price = current_price
            position.current_value = current_value
            position.pnl = pnl
            position.pnl_percent = pnl_percent
            position.peak_pnl_percent = max(position.peak_pnl_percent, pnl_percent)

            candidate = next((item for item in evaluated_symbols if item["symbol"] == symbol), None)
            current_potential = candidate["profit_potential"] if candidate else 0.0
            position.last_profit_potential = current_potential

            held_bars = day_index - position.entry_day_index
            if held_bars < profile["minimum_hold_bars"]:
                unrealized_pnl += position.pnl
                continue

            partial_take_profit = profile.get("partial_take_profit")
            partial_take_profit_ratio = profile.get("partial_take_profit_ratio", 0.5)
            if (
                partial_take_profit is not None
                and not position.partial_exit_done
                and pnl_percent >= partial_take_profit
                and 0.0 < partial_take_profit_ratio < 1.0
            ):
                sold_fraction = partial_take_profit_ratio
                sold_value = current_value * sold_fraction
                sell_fee = sold_value * profile["trading_fee"]
                net_proceeds = sold_value - sell_fee
                realized_trade_pnl = net_proceeds - (position.initial_investment * sold_fraction)

                cash_balance += net_proceeds
                total_fees += sell_fee
                realized_pnl += realized_trade_pnl

                keep_fraction = 1.0 - sold_fraction
                position.shares *= keep_fraction
                position.initial_investment *= keep_fraction
                position.net_investment *= keep_fraction
                position.current_value = position.shares * current_price
                position.pnl = position.current_value - position.net_investment
                position.pnl_percent = (
                    (position.pnl / position.net_investment) * 100.0 if position.net_investment > 0 else 0.0
                )
                position.partial_exit_done = True
                position.last_scaled_day_index = day_index
                position.peak_pnl_percent = max(position.peak_pnl_percent, position.pnl_percent)

                trade_history.append(
                    {
                        "date": daily_data["date"],
                        "symbol": symbol,
                        "action": "PARTIAL_TAKE_PROFIT",
                        "pnl_percent": pnl_percent,
                        "realized_pnl": realized_trade_pnl,
                        "current_value": sold_value,
                        "sold_fraction": sold_fraction,
                    }
                )
                rebalancing_events.append(
                    {
                        "date": daily_data["date"],
                        "symbol": symbol,
                        "reason": "partial_take_profit",
                        "market_regime": market_regime,
                        "pnl_percent": pnl_percent,
                        "profit_potential": current_potential,
                    }
                )

            trailing_stop_activation = profile.get("trailing_stop_activation")
            trailing_stop_drawdown = profile.get("trailing_stop_drawdown")

            remove_reason = None
            if pnl_percent >= profile["take_profit"]:
                remove_reason = "take_profit"
            elif (
                trailing_stop_activation is not None
                and trailing_stop_drawdown is not None
                and position.peak_pnl_percent >= trailing_stop_activation
                and pnl_percent <= position.peak_pnl_percent - trailing_stop_drawdown
            ):
                remove_reason = "trailing_stop"
            elif pnl_percent <= profile["replacement_threshold"] and current_potential < entry_threshold + profile["exit_buffer"]:
                remove_reason = "loss_threshold"
            elif current_potential < entry_threshold - profile["exit_buffer"]:
                remove_reason = "potential_drop"

            if remove_reason:
                symbols_to_remove.append((symbol, remove_reason, current_potential))
            else:
                unrealized_pnl += position.pnl

        for symbol, reason, current_potential in symbols_to_remove:
            position = investments.pop(symbol)
            current_value = position.current_value
            sell_fee = current_value * profile["trading_fee"]
            net_proceeds = current_value - sell_fee
            realized_trade_pnl = net_proceeds - position.initial_investment

            cash_balance += net_proceeds
            total_fees += sell_fee
            realized_pnl += realized_trade_pnl
            cooldowns[symbol] = day_index + profile["reentry_cooldown_bars"]

            trade_history.append(
                {
                    "date": daily_data["date"],
                    "symbol": symbol,
                    "action": reason.upper(),
                    "pnl_percent": position.pnl_percent,
                    "realized_pnl": realized_trade_pnl,
                    "current_value": current_value,
                }
            )
            rebalancing_events.append(
                {
                    "date": daily_data["date"],
                    "symbol": symbol,
                    "reason": reason,
                    "market_regime": market_regime,
                    "pnl_percent": position.pnl_percent,
                    "profit_potential": current_potential,
                }
            )

        cooled_symbols = {symbol for symbol, unlock_day in cooldowns.items() if day_index >= unlock_day}
        for symbol in cooled_symbols:
            cooldowns.pop(symbol, None)

        if profile.get("allow_reacceleration"):
            for symbol, position in list(investments.items()):
                if cash_balance <= 0 or position.last_scaled_day_index == day_index:
                    continue
                if not position.partial_exit_done:
                    continue
                if position.reaccelerations_done >= profile.get("max_reaccelerations_per_position", 1):
                    continue

                candidate = next((item for item in evaluated_symbols if item["symbol"] == symbol), None)
                if not candidate:
                    continue

                bullish_gate = entry_threshold + profile.get("reacceleration_bullish_bonus", 4.0)
                profit_gate = entry_threshold - profile.get("reacceleration_profit_offset", 10.0)
                if candidate["bullish_score"] < bullish_gate:
                    continue
                if candidate["profit_potential"] < profit_gate:
                    continue
                if position.pnl_percent < profile.get("reacceleration_min_pnl_percent", 0.8):
                    continue

                desired_add = profile["fixed_allocation"] * profile.get("reacceleration_add_fraction", 0.5)
                add_allocation = min(desired_add, cash_balance)
                if add_allocation < profile["fixed_allocation"] * 0.25:
                    continue

                buy_fee = add_allocation * profile["trading_fee"]
                add_net_investment = add_allocation - buy_fee
                add_shares = add_net_investment / candidate["price"]

                cash_balance -= add_allocation
                total_fees += buy_fee
                position.initial_investment += add_allocation
                position.net_investment += add_net_investment
                position.shares += add_shares
                position.current_price = candidate["price"]
                position.current_value = position.shares * candidate["price"]
                position.pnl = position.current_value - position.net_investment
                position.pnl_percent = (
                    (position.pnl / position.net_investment) * 100.0 if position.net_investment > 0 else 0.0
                )
                position.peak_pnl_percent = max(position.peak_pnl_percent, position.pnl_percent)
                position.last_profit_potential = candidate["profit_potential"]
                position.reaccelerations_done += 1
                position.last_scaled_day_index = day_index

                trade_history.append(
                    {
                        "date": daily_data["date"],
                        "symbol": symbol,
                        "action": "REACCELERATION",
                        "entry_price": candidate["price"],
                        "bullish_score": candidate["bullish_score"],
                        "profit_potential": candidate["profit_potential"],
                        "allocation": add_allocation,
                    }
                )
                rebalancing_events.append(
                    {
                        "date": daily_data["date"],
                        "symbol": symbol,
                        "reason": "reacceleration",
                        "market_regime": market_regime,
                        "pnl_percent": position.pnl_percent,
                        "profit_potential": candidate["profit_potential"],
                    }
                )

        available_slots = max_symbols - len(investments)
        minimum_entry_allocation = profile["allocation_min"] if profile.get("dynamic_sizing") else profile["fixed_allocation"]
        if available_slots > 0 and cash_balance >= minimum_entry_allocation:
            for symbol_data in evaluated_symbols:
                if available_slots <= 0 or cash_balance < minimum_entry_allocation:
                    break

                symbol = symbol_data["symbol"]
                if symbol in investments or symbol in cooldowns:
                    continue
                if symbol_data["bullish_score"] < entry_threshold + profile["entry_buffer"]:
                    continue
                if symbol_data["profit_potential"] < entry_threshold - profile["profit_potential_offset"]:
                    continue

                allocation = calculate_target_allocation(
                    profile,
                    symbol_data["bullish_score"],
                    symbol_data["profit_potential"],
                    cash_balance,
                )
                if allocation < minimum_entry_allocation:
                    continue

                fee = allocation * profile["trading_fee"]
                net_investment = allocation - fee
                shares = net_investment / symbol_data["price"]
                investments[symbol] = Position(
                    symbol=symbol,
                    initial_investment=allocation,
                    net_investment=net_investment,
                    shares=shares,
                    entry_price=symbol_data["price"],
                    current_price=symbol_data["price"],
                    current_value=net_investment,
                    entry_date=daily_data["date"],
                    entry_day_index=day_index,
                    entry_bullish_score=symbol_data["bullish_score"],
                    last_profit_potential=symbol_data["profit_potential"],
                    peak_pnl_percent=0.0,
                    partial_exit_done=False,
                    reaccelerations_done=0,
                    last_scaled_day_index=day_index,
                )
                cash_balance -= allocation
                total_fees += fee
                trade_history.append(
                    {
                        "date": daily_data["date"],
                        "symbol": symbol,
                        "action": "ENTRY",
                        "entry_price": symbol_data["price"],
                        "bullish_score": symbol_data["bullish_score"],
                        "profit_potential": symbol_data["profit_potential"],
                        "allocation": allocation,
                    }
                )
                available_slots -= 1

        invested_value = sum(position.current_value for position in investments.values())
        total_value = cash_balance + invested_value
        total_pnl = total_value - INITIAL_CAPITAL
        performance_history.append(
            {
                "date": daily_data["date"],
                "synthetic_regime": daily_data["synthetic_regime"],
                "market_regime": market_regime,
                "entry_threshold": entry_threshold,
                "max_symbols_allowed": max_symbols,
                "total_value": total_value,
                "cash_balance": cash_balance,
                "invested_value": invested_value,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_pnl": total_pnl,
                "pnl_percent": (total_pnl / INITIAL_CAPITAL) * 100.0,
                "total_fees_paid": total_fees,
                "net_pnl": total_pnl,
                "net_pnl_percent": (total_pnl / INITIAL_CAPITAL) * 100.0,
                "invested_symbols": len(investments),
            }
        )

    final_record = performance_history[-1]
    rebalancing_counter = Counter(event["reason"] for event in rebalancing_events)
    individual_performance = []
    for symbol, position in sorted(investments.items()):
        individual_performance.append(
            {
                "symbol": symbol,
                "entry_date": position.entry_date,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "current_value": position.current_value,
                "pnl": position.pnl,
                "pnl_percent": position.pnl_percent,
                "entry_bullish_score": position.entry_bullish_score,
                "profit_potential": position.last_profit_potential,
            }
        )

    return {
        "analysis_basis": {
            "data_type": "deterministic_synthetic_daily_data",
            "seed": SEED,
            "profile_name": profile["name"],
            "cooldown_bars": profile["reentry_cooldown_bars"],
            "cooldown_note": f"{profile['reentry_cooldown_minutes']} minutes is converted to {profile['reentry_cooldown_bars']} daily bar(s) in this bar-based simulator.",
            "limitations": [
                "This is not exchange historical data.",
                "Intraday path is approximated with daily bars only.",
                "Results are for comparative tuning, not production validation.",
            ],
        },
        "strategy_params": {
            "take_profit": profile["take_profit"],
            "reentry_cooldown_minutes": profile["reentry_cooldown_minutes"],
            "reentry_cooldown_bars": profile["reentry_cooldown_bars"],
            "extreme_threshold": profile["entry_thresholds"]["EXTREME"],
            "high_volatility_threshold": profile["entry_thresholds"]["HIGH_VOLATILITY"],
            "normal_threshold": profile["entry_thresholds"]["NORMAL"],
            "extreme_max_symbols": profile["max_symbols_by_regime"]["EXTREME"],
            "high_volatility_max_symbols": profile["max_symbols_by_regime"]["HIGH_VOLATILITY"],
            "normal_max_symbols": profile["max_symbols_by_regime"]["NORMAL"],
            "entry_buffer": profile["entry_buffer"],
            "exit_buffer": profile["exit_buffer"],
            "profit_potential_offset": profile["profit_potential_offset"],
            "replacement_threshold": profile["replacement_threshold"],
            "trading_fee": profile["trading_fee"],
            "regime_volatility_thresholds": profile["regime_volatility_thresholds"],
            "fixed_allocation": profile["fixed_allocation"],
            "minimum_hold_bars": profile["minimum_hold_bars"],
            "partial_take_profit": profile.get("partial_take_profit"),
            "partial_take_profit_ratio": profile.get("partial_take_profit_ratio"),
            "trailing_stop_activation": profile.get("trailing_stop_activation"),
            "trailing_stop_drawdown": profile.get("trailing_stop_drawdown"),
            "dynamic_sizing": profile.get("dynamic_sizing"),
            "allocation_min": profile.get("allocation_min"),
            "allocation_max": profile.get("allocation_max"),
            "allocation_score_floor": profile.get("allocation_score_floor"),
            "allocation_score_ceiling": profile.get("allocation_score_ceiling"),
            "allow_reacceleration": profile.get("allow_reacceleration"),
            "reacceleration_bullish_bonus": profile.get("reacceleration_bullish_bonus"),
            "reacceleration_profit_offset": profile.get("reacceleration_profit_offset"),
            "reacceleration_add_fraction": profile.get("reacceleration_add_fraction"),
            "reacceleration_min_pnl_percent": profile.get("reacceleration_min_pnl_percent"),
            "max_reaccelerations_per_position": profile.get("max_reaccelerations_per_position"),
        },
        "simulation_metadata": {
            "start_date": historical_data[0]["date"],
            "end_date": historical_data[-1]["date"],
            "total_days": len(historical_data),
            "initial_capital": INITIAL_CAPITAL,
            "final_capital": final_record["total_value"],
            "final_pnl": final_record["total_pnl"],
            "final_pnl_percent": final_record["pnl_percent"],
            "total_fees_paid": final_record["total_fees_paid"],
            "realized_pnl": final_record["realized_pnl"],
            "unrealized_pnl": final_record["unrealized_pnl"],
            "net_pnl": final_record["net_pnl"],
            "net_pnl_percent": final_record["net_pnl_percent"],
            "market_regime_counts": dict(Counter(item["market_regime"] for item in performance_history)),
            "synthetic_regime_counts": dict(Counter(item["synthetic_regime"] for item in performance_history)),
            "rebalancing_counts": dict(rebalancing_counter),
        },
        "performance_history": performance_history,
        "trade_history": trade_history,
        "rebalancing_events": rebalancing_events,
        "individual_performance": individual_performance,
        "final_portfolio": {
            symbol: {
                "initial_investment": position.initial_investment,
                "net_investment": position.net_investment,
                "shares": position.shares,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "current_value": position.current_value,
                "entry_date": position.entry_date,
                "entry_bullish_score": position.entry_bullish_score,
                "profit_potential": position.last_profit_potential,
                "pnl": position.pnl,
                "pnl_percent": position.pnl_percent,
                "reaccelerations_done": position.reaccelerations_done,
            }
            for symbol, position in investments.items()
        },
    }


def load_previous_results() -> dict[str, Any] | None:
    if not OLD_RESULTS_PATH.exists():
        return None
    with OLD_RESULTS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_comparison_report(previous: dict[str, Any] | None, current: dict[str, Any]) -> str:
    current_meta = current["simulation_metadata"]
    current_params = current["strategy_params"]
    current_trade_counts = Counter(item["action"] for item in current["trade_history"])

    lines = [
        "# Modified Strategy 1-Year Comparison Report",
        "",
        "## What Was Fixed",
        "- Random synthetic data is now deterministic via a fixed seed.",
        "- Market regime thresholds are bar-aligned (5.0 / 2.5 average absolute daily change).",
        "- Entry thresholds are regime-aware, time-frame adjusted, and no longer hard-coded to 70.0.",
        "- Cooldown semantics are explicit: 20 minutes becomes 1 daily bar in this simulator.",
        "- Results now include rebalancing events, market-regime counts, and individual performance.",
        "",
        "## Current Run Summary",
        f"- Final capital: ${current_meta['final_capital']:.2f}",
        f"- Final PnL: ${current_meta['final_pnl']:+.2f} ({current_meta['final_pnl_percent']:+.2f}%)",
        f"- Fees paid: ${current_meta['total_fees_paid']:.2f}",
        f"- Realized PnL: ${current_meta['realized_pnl']:+.2f}",
        f"- Unrealized PnL: ${current_meta['unrealized_pnl']:+.2f}",
        f"- Entries: {current_trade_counts.get('ENTRY', 0)}",
        f"- Take profits: {current_trade_counts.get('TAKE_PROFIT', 0)}",
        f"- Loss exits: {current_trade_counts.get('LOSS_THRESHOLD', 0)}",
        f"- Potential-drop exits: {current_trade_counts.get('POTENTIAL_DROP', 0)}",
        f"- Market regime counts: {current_meta['market_regime_counts']}",
        "",
        "## Strategy Alignment Notes",
        f"- Take profit remains {current_params['take_profit']}%, matching the tuned modular strategy.",
        f"- Entry thresholds now vary by regime: {ENTRY_THRESHOLDS}.",
        f"- Regime volatility thresholds now use {REGIME_VOLATILITY_THRESHOLDS}, which fit daily bars.",
        f"- Reentry cooldown is documented as {current_params['reentry_cooldown_bars']} daily bar(s).",
        "",
    ]

    if previous:
        previous_meta = previous.get("simulation_metadata", {})
        previous_trade_counts = Counter(item.get("action") for item in previous.get("trade_history", []))
        lines.extend(
            [
                "## Previous vs Current",
                f"- Previous final capital: ${previous_meta.get('final_capital', 0.0):.2f}",
                f"- Current final capital: ${current_meta['final_capital']:.2f}",
                f"- Previous final PnL: ${previous_meta.get('final_pnl', 0.0):+.2f}",
                f"- Current final PnL: ${current_meta['final_pnl']:+.2f}",
                f"- Previous entries: {previous_trade_counts.get('ENTRY', 0)}",
                f"- Current entries: {current_trade_counts.get('ENTRY', 0)}",
                f"- Previous take profits: {previous_trade_counts.get('TAKE_PROFIT', 0)}",
                f"- Current take profits: {current_trade_counts.get('TAKE_PROFIT', 0)}",
                f"- Previous loss exits: {previous_trade_counts.get('LOSS_THRESHOLD', 0)}",
                f"- Current loss exits: {current_trade_counts.get('LOSS_THRESHOLD', 0)}",
                "",
                "## Important Caveat",
                "- The previous run mixed daily bars with minute-labeled cooldown and regime thresholds that never triggered.",
                "- The current run is still synthetic, but its semantics are internally consistent and reproducible.",
            ]
        )
    else:
        lines.extend(
            [
                "## Previous vs Current",
                "- No previous JSON was found, so only the current deterministic run is documented.",
            ]
        )

    return "\n".join(lines) + "\n"


def save_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def main() -> None:
    print("FACT: Running deterministic 1-year synthetic backtest v2")
    historical_data = generate_historical_data()
    current_results = simulate_modified_strategy(historical_data)
    previous_results = load_previous_results()
    comparison_report = build_comparison_report(previous_results, current_results)

    save_json(NEW_RESULTS_PATH, current_results)
    COMPARISON_REPORT_PATH.write_text(comparison_report, encoding="utf-8")

    current_meta = current_results["simulation_metadata"]
    current_trade_counts = Counter(item["action"] for item in current_results["trade_history"])

    print(f"  Final capital: ${current_meta['final_capital']:.2f}")
    print(f"  Final PnL: ${current_meta['final_pnl']:+.2f} ({current_meta['final_pnl_percent']:+.2f}%)")
    print(f"  Fees: ${current_meta['total_fees_paid']:.2f}")
    print(f"  Entries: {current_trade_counts.get('ENTRY', 0)}")
    print(f"  Take profits: {current_trade_counts.get('TAKE_PROFIT', 0)}")
    print(f"  Loss exits: {current_trade_counts.get('LOSS_THRESHOLD', 0)}")
    print(f"  Potential-drop exits: {current_trade_counts.get('POTENTIAL_DROP', 0)}")
    print(f"  Saved: {NEW_RESULTS_PATH.name}")
    print(f"  Saved: {COMPARISON_REPORT_PATH.name}")


if __name__ == "__main__":
    main()
