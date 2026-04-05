"""Operational risk-gate checks for recommendation-only and guarded execution flows."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from merged_partial_v2.pathing import merged_root
import json


def _load_risk_config() -> Dict[str, Any]:
    """위험 관리 설정 로드"""
    try:
        config_path = merged_root() / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                config = json.load(handle)
                return config.get("risk_limits", {})
    except Exception:
        pass
    return {}


class RiskGateService:
    """Centralize high-level gate checks before creating new entry recommendations."""

    NON_BLOCKING_FAILURE_CATEGORIES = {
        "price_lookup_failed",
        "missing_symbol",
        "invalid_side",
        "invalid_quantity",
    }
    
    def __init__(self):
        self.risk_config = _load_risk_config()
        self.FAILURE_BLOCK_WINDOW_SECONDS = int(self.risk_config.get("failure_block_window_seconds", 900))
        self.DAILY_LOSS_RESET_HOUR = int(self.risk_config.get("daily_loss_reset_hour", 0))

    def evaluate(
        self,
        *,
        market_snapshot: Dict[str, Any],
        account_context: Dict[str, Any],
        recent_health_check: Dict[str, Any] | None = None,
        recent_order_failures: Dict[str, Any] | None = None,
        config: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        account = dict(account_context.get("account", {}))
        positions = dict(account_context.get("positions", {}))
        health = dict(recent_health_check or {})
        order_failures = dict(recent_order_failures or {})
        risk_limits = dict(config.get("risk_limits", {}) if config else {})

        reasons: List[Dict[str, str]] = []

        if not account.get("ok", False):
            reasons.append(
                {
                    "reason": "account_snapshot_unavailable",
                    "detail": "Private account snapshot is unavailable, so new entry recommendations are blocked.",
                }
            )

        if not positions.get("ok", False):
            reasons.append(
                {
                    "reason": "position_snapshot_unavailable",
                    "detail": "Private position snapshot is unavailable, so new entry recommendations are blocked.",
                }
            )

        # 일일 손실 제한 체크
        daily_loss_limit = float(risk_limits.get("daily_loss_limit_percent", 5.0))
        if daily_loss_limit > 0:
            daily_pnl = self._calculate_daily_pnl(account)
            if daily_pnl < -daily_loss_limit:
                reasons.append(
                    {
                        "reason": "daily_loss_limit_exceeded",
                        "detail": f"Daily PnL {daily_pnl:.2f}% exceeds limit of -{daily_loss_limit:.2f}%",
                    }
                )

        # 연속 실패 차단 체크
        max_consecutive_failures = int(risk_limits.get("max_consecutive_failures", 3))
        if max_consecutive_failures > 0:
            consecutive_failures = self._count_consecutive_failures(order_failures)
            if consecutive_failures >= max_consecutive_failures:
                reasons.append(
                    {
                        "reason": "max_consecutive_failures_exceeded",
                        "detail": f"Consecutive failures {consecutive_failures} exceeds limit of {max_consecutive_failures}",
                    }
                )

        # 총 익스포저 제한 체크
        max_exposure_percent = float(risk_limits.get("max_total_exposure_percent", 95.0))
        if max_exposure_percent > 0:
            current_exposure = self._calculate_total_exposure(account, positions)
            if current_exposure > max_exposure_percent:
                reasons.append(
                    {
                        "reason": "max_exposure_limit_exceeded",
                        "detail": f"Current exposure {current_exposure:.2f}% exceeds limit of {max_exposure_percent:.2f}%",
                    }
                )

        # 개별 포지션 크기 제한 체크
        max_position_size = float(risk_limits.get("max_position_size_percent", 20.0))
        if max_position_size > 0:
            large_positions = self._check_large_positions(positions, account, max_position_size)
            if large_positions:
                reasons.append(
                    {
                        "reason": "max_position_size_exceeded",
                        "detail": f"Positions {large_positions} exceed size limit of {max_position_size:.2f}%",
                    }
                )

        if health.get("ok") is True:
            latest_open = dict(health.get("latest_open") or {})
            latest_close = dict(health.get("latest_close") or {})
            open_status = latest_open.get("final_status")
            close_status = latest_close.get("final_status")
            if latest_open and open_status not in {"FILLED", None}:
                reasons.append(
                    {
                        "reason": "recent_health_check_open_not_filled",
                        "detail": f"Recent health-check open order ended with status {open_status}.",
                    }
                )
            if latest_close and close_status not in {"FILLED", None}:
                reasons.append(
                    {
                        "reason": "recent_health_check_close_not_filled",
                        "detail": f"Recent health-check close order ended with status {close_status}.",
                    }
                )

        wallet_balance = float(account.get("wallet_balance", 0.0) or 0.0)
        if wallet_balance <= 0:
            reasons.append(
                {
                    "reason": "wallet_balance_not_positive",
                    "detail": "Wallet balance must be positive before new entries are considered.",
                }
            )

        if order_failures.get("ok") is True and int(order_failures.get("critical_failure_count", 0) or 0) > 0:
            latest_failure = dict(order_failures.get("latest_failure") or {})
            failure_category = str(latest_failure.get("category") or "unknown")
            failure_age_seconds = self._failure_age_seconds(latest_failure.get("ts"))
            should_block = (
                failure_category not in self.NON_BLOCKING_FAILURE_CATEGORIES
                and failure_age_seconds is not None
                and failure_age_seconds <= self.FAILURE_BLOCK_WINDOW_SECONDS
            )
            if should_block:
                reasons.append(
                    {
                        "reason": "recent_critical_order_failure",
                        "detail": (
                            f"Recent critical order failure detected: "
                            f"{failure_category} / {latest_failure.get('symbol', '-')}"
                        ),
                    }
                )

        return {
            "ok": not reasons,
            "block_new_entries": bool(reasons),
            "market_regime": market_snapshot.get("market_regime"),
            "reason_count": len(reasons),
            "reasons": reasons,
            "recent_order_failures": order_failures,
            "risk_metrics": {
                "daily_pnl_percent": self._calculate_daily_pnl(account),
                "consecutive_failures": self._count_consecutive_failures(order_failures),
                "total_exposure_percent": self._calculate_total_exposure(account, positions),
                "max_position_size_percent": max_position_size,
            },
            "decision_line": (
                "risk gate passed"
                if not reasons
                else f"risk gate blocked {len(reasons)} condition(s)"
            ),
        }

    def _calculate_daily_pnl(self, account: Dict[str, Any]) -> float:
        """일일 손익 계산 (간단화된 버전)"""
        try:
            total_pnl = float(account.get("total_unrealized_pnl", 0.0) or 0.0)
            wallet_balance = float(account.get("wallet_balance", 0.0) or 0.0)
            if wallet_balance > 0:
                return (total_pnl / wallet_balance) * 100
        except Exception:
            pass
        return 0.0

    def _count_consecutive_failures(self, order_failures: Dict[str, Any]) -> int:
        """연속 실패 횟수 계산"""
        if not order_failures.get("ok"):
            return 0
        failures = list(order_failures.get("recent_failures", []))
        if not failures:
            return 0
        consecutive = 0
        for failure in failures:
            if failure.get("retryable", True):
                consecutive += 1
            else:
                break
        return consecutive

    def _calculate_total_exposure(self, account: Dict[str, Any], positions: Dict[str, Any]) -> float:
        """총 익스포저 퍼센트 계산"""
        try:
            wallet_balance = float(account.get("wallet_balance", 0.0) or 0.0)
            if wallet_balance <= 0:
                return 0.0
            
            active_positions = list(positions.get("active_positions", []))
            total_exposure = 0.0
            for pos in active_positions:
                try:
                    amount = abs(float(pos.get("positionAmt", 0.0) or 0.0))
                    price = float(pos.get("markPrice", 0.0) or 0.0)
                    total_exposure += amount * price
                except Exception:
                    continue
            
            return (total_exposure / wallet_balance) * 100 if wallet_balance > 0 else 0.0
        except Exception:
            return 0.0

    def _check_large_positions(self, positions: Dict[str, Any], account: Dict[str, Any], limit_percent: float) -> List[str]:
        """크기 제한을 초과하는 포지션 확인"""
        try:
            wallet_balance = float(account.get("wallet_balance", 0.0) or 0.0)
            if wallet_balance <= 0:
                return []
            
            active_positions = list(positions.get("active_positions", []))
            large_positions = []
            for pos in active_positions:
                try:
                    amount = abs(float(pos.get("positionAmt", 0.0) or 0.0))
                    price = float(pos.get("markPrice", 0.0) or 0.0)
                    position_value = amount * price
                    position_percent = (position_value / wallet_balance) * 100 if wallet_balance > 0 else 0.0
                    if position_percent > limit_percent:
                        large_positions.append(pos.get("symbol", "UNKNOWN"))
                except Exception:
                    continue
            
            return large_positions
        except Exception:
            return []

    def _failure_age_seconds(self, ts: str | None) -> float | None:
        if not ts:
            return None
        try:
            failure_ts = datetime.fromisoformat(ts)
        except Exception:
            return None
        return max((datetime.now(timezone.utc) - failure_ts).total_seconds(), 0.0)
