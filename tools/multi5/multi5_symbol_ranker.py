from __future__ import annotations

from typing import Any


def sort_by_edge(symbol_states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        symbol_states,
        key=lambda row: (
            1 if str(row.get("strategy_signal", "HOLD")) in {"LONG", "SHORT"} else 0,
            float(row.get("strategy_signal_score", 0.0)),
            float(row.get("edge_score", 0.0)),
        ),
        reverse=True,
    )


def select_top_one(symbol_states: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = sort_by_edge(symbol_states)
    if not ranked:
        return None
    top = ranked[0]
    payload = {
        "SELECTED_SYMBOL": top.get("symbol"),
        "EDGE_SCORE": float(top.get("edge_score", 0.0)),
        "REGIME": top.get("regime", "unknown"),
        "VOLATILITY": float(top.get("volatility", 0.0)),
        "STRATEGY_SIGNAL": top.get("strategy_signal", "HOLD"),
        "STRATEGY_ID": top.get("strategy_id", ""),
    }
    if "diversification_penalty" in top:
        payload["diversification_penalty"] = float(top.get("diversification_penalty", 0.0) or 0.0)
    if "blocked_symbol_penalty" in top:
        payload["blocked_symbol_penalty"] = float(top.get("blocked_symbol_penalty", 0.0) or 0.0)
    return payload


def select_top_n(symbol_states: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    ranked = sort_by_edge(symbol_states)
    if limit <= 0:
        return []
    return ranked[:limit]
