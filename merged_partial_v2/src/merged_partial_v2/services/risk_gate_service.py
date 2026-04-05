"""Operational risk-gate checks for recommendation-only and guarded execution flows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


class RiskGateService:
    """Centralize high-level gate checks before creating new entry recommendations."""

    NON_BLOCKING_FAILURE_CATEGORIES = {
        "price_lookup_failed",
        "missing_symbol",
        "invalid_side",
        "invalid_quantity",
    }
    FAILURE_BLOCK_WINDOW_SECONDS = 900

    def evaluate(
        self,
        *,
        market_snapshot: Dict[str, Any],
        account_context: Dict[str, Any],
        recent_health_check: Dict[str, Any] | None = None,
        recent_order_failures: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        account = dict(account_context.get("account", {}))
        positions = dict(account_context.get("positions", {}))
        health = dict(recent_health_check or {})
        order_failures = dict(recent_order_failures or {})

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
            "decision_line": (
                "risk gate passed"
                if not reasons
                else f"risk gate blocked {len(reasons)} condition(s)"
            ),
        }

    def _failure_age_seconds(self, ts: str | None) -> float | None:
        if not ts:
            return None
        try:
            failure_ts = datetime.fromisoformat(ts)
        except Exception:
            return None
        return max((datetime.now(timezone.utc) - failure_ts).total_seconds(), 0.0)
