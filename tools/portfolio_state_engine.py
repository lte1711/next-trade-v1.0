# Portfolio state engine module

from __future__ import annotations

from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def evaluate_portfolio_state(metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate current portfolio state and return a normalized decision payload."""
    metrics = metrics if isinstance(metrics, dict) else {}
    total_trades = _to_int(metrics.get("total_trades", metrics.get("total", 0)))
    win_rate = _to_float(metrics.get("win_rate", 0.0))
    total_pnl = _to_float(metrics.get("total_pnl", metrics.get("pnl", 0.0)))
    max_drawdown = _to_float(metrics.get("max_drawdown", 0.0))

    reasons: list[str] = []
    decision = "ALLOW"
    status = "ok"
    state = "stable"

    if total_trades < 5:
        return {
            "status": "warmup",
            "state": "insufficient_history",
            "decision": "ALLOW",
            "reasons": ["insufficient_history"],
            "metrics": {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "max_drawdown": max_drawdown,
            },
        }

    if total_trades >= 10 and win_rate < 0.25 and total_pnl < 0.0:
        decision = "BLOCK"
        status = "risk"
        state = "weak_edge"
        reasons.append("win_rate_critical")

    if max_drawdown >= 10.0 and total_pnl < 0.0:
        decision = "BLOCK"
        status = "risk"
        state = "drawdown_stressed"
        reasons.append("drawdown_critical")

    if decision != "BLOCK":
        if total_trades >= 20 and win_rate < 0.35 and total_pnl < -1.0:
            decision = "BLOCK"
            status = "risk"
            state = "persistent_loss"
            reasons.append("persistent_negative_expectancy")
        elif win_rate < 0.40:
            decision = "CAUTION"
            status = "soft_warning"
            state = "win_rate_soft_limit"
            reasons.append("win_rate_soft_limit")
        elif total_pnl < 0.0:
            decision = "CAUTION"
            status = "soft_warning"
            state = "negative_pnl"
            reasons.append("negative_pnl")

    if not reasons:
        reasons.append("portfolio_ok")

    return {
        "status": status,
        "state": state,
        "decision": decision,
        "reasons": reasons,
        "metrics": {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 6),
            "total_pnl": round(total_pnl, 6),
            "max_drawdown": round(max_drawdown, 6),
        },
    }


def should_enter_trade(metrics: dict[str, Any] | None = None, *args, **kwargs) -> bool:
    """Return True only when the portfolio state allows new entries."""
    result = evaluate_portfolio_state(metrics)
    return str(result.get("decision", "ALLOW")).upper() != "BLOCK"
