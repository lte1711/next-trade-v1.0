"""
Remote candidate profiles and a lightweight profile switcher for merged_partial_v2.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


REMOTE_RISK_REFERENCE_PROFILE: Dict[str, Any] = {
    "name": "remote_risk_reference",
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


REMOTE_DEFAULT_PROFILE: Dict[str, Any] = {
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


class ProfileSwitcherService:
    """Select the aggressive or balanced profile from simple risk and monthly-return inputs."""

    def __init__(
        self,
        selection_config: Dict[str, Any] | None = None,
        benchmark_metrics: Dict[str, Dict[str, Any]] | None = None,
    ) -> None:
        self.reference_profile = deepcopy(REMOTE_RISK_REFERENCE_PROFILE)
        self.default_profile = deepcopy(REMOTE_DEFAULT_PROFILE)
        self.selection_config = selection_config or {}
        self.benchmark_metrics = deepcopy(benchmark_metrics or {})

    def get_profile(self, profile_name: str | None = None) -> Dict[str, Any]:
        default_name = self.selection_config.get("default_profile_name", self.default_profile["name"])
        aggressive_name = self.selection_config.get("aggressive_profile_name", self.reference_profile["name"])
        normalized = (profile_name or default_name).lower()
        if normalized in {
            "remote_risk_reference",
            "reference",
            "aggressive",
            aggressive_name.lower(),
            self.reference_profile["name"].lower(),
        }:
            return deepcopy(self.reference_profile)
        return deepcopy(self.default_profile)

    def choose_profile_from_metrics(
        self,
        *,
        max_drawdown_percent: float | None = None,
        positive_months: int | None = None,
        negative_months: int | None = None,
        prefer_aggressive: bool = False,
    ) -> Dict[str, Any]:
        if prefer_aggressive or self.selection_config.get("prefer_aggressive", False):
            return deepcopy(self.reference_profile)

        drawdown = abs(max_drawdown_percent or 0.0)
        pos_months = positive_months if positive_months is not None else 0
        neg_months = negative_months if negative_months is not None else 0
        max_drawdown_threshold = float(self.selection_config.get("max_drawdown_threshold", 12.0))
        require_month_rule = bool(
            self.selection_config.get("require_positive_months_not_less_than_negative", True)
        )
        max_drawdown_gap = float(self.selection_config.get("max_drawdown_gap_for_aggressive", 6.0))
        require_pnl_outperformance = bool(
            self.selection_config.get("require_aggressive_pnl_outperformance", True)
        )

        # Keep the balanced candidate as the default unless the risk signal is clearly acceptable.
        month_rule_ok = pos_months >= max(neg_months, 1) if require_month_rule else True
        aggressive_benchmark = self.get_benchmark_metrics(self.reference_profile["name"])
        default_benchmark = self.get_benchmark_metrics(self.default_profile["name"])
        aggressive_drawdown = abs(float(aggressive_benchmark.get("max_drawdown_percent", 0.0) or 0.0))
        default_drawdown = abs(float(default_benchmark.get("max_drawdown_percent", 0.0) or 0.0))
        aggressive_pnl = float(aggressive_benchmark.get("final_pnl_percent", 0.0) or 0.0)
        default_pnl = float(default_benchmark.get("final_pnl_percent", 0.0) or 0.0)
        drawdown_gap_ok = aggressive_drawdown <= (default_drawdown + max_drawdown_gap)
        pnl_rule_ok = aggressive_pnl > default_pnl if require_pnl_outperformance else True

        if drawdown <= max_drawdown_threshold and month_rule_ok and drawdown_gap_ok and pnl_rule_ok:
            return deepcopy(self.reference_profile)
        return deepcopy(self.default_profile)

    def get_benchmark_metrics(self, profile_name: str) -> Dict[str, Any]:
        return deepcopy(self.benchmark_metrics.get(profile_name, {}))

    def build_selection_summary(
        self,
        *,
        selected_profile: Dict[str, Any],
        max_drawdown_percent: float | None = None,
        positive_months: int | None = None,
        negative_months: int | None = None,
    ) -> Dict[str, Any]:
        return {
            "selected_profile": selected_profile["name"],
            "max_drawdown_percent": max_drawdown_percent,
            "positive_months": positive_months,
            "negative_months": negative_months,
            "metrics_source_resolved": self.selection_config.get("metrics_source_resolved"),
            "selected_profile_benchmark": self.get_benchmark_metrics(selected_profile["name"]),
            "available_profile_benchmarks": deepcopy(self.benchmark_metrics),
            "selection_rule": (
                "Use aggressive reference only when drawdown stays at or below "
                f"{self.selection_config.get('max_drawdown_threshold', 12.0)}%, "
                "positive months are not fewer than negative months, "
                "and the aggressive benchmark still outperforms the default without an excessive drawdown gap."
            ),
        }
