"""Paper decision service for recommendation-only trade planning."""

from __future__ import annotations

from typing import Any, Dict, List


class PaperDecisionService:
    """Turn market candidates and account context into recommendation-only trade decisions."""

    def __init__(self, profile: Dict[str, Any]) -> None:
        self.profile = profile

    def build_decision(
        self,
        market_snapshot: Dict[str, Any],
        account_context: Dict[str, Any],
        risk_gate: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        selected_symbols = list(market_snapshot.get("selected_symbols", []))
        account = dict(account_context.get("account", {}))
        positions_snapshot = dict(account_context.get("positions", {}))
        active_positions = list(positions_snapshot.get("active_positions", []))
        risk_gate = dict(risk_gate or {})

        active_symbols = {
            str(position.get("symbol", "")).upper()
            for position in active_positions
            if str(position.get("symbol", "")).strip()
        }

        wallet_balance = float(account.get("wallet_balance", 0.0) or 0.0)
        allocation = float(self.profile.get("fixed_allocation", 0.0) or 0.0)
        max_symbols = int(
            self.profile.get("max_symbols_by_regime", {}).get(
                market_snapshot.get("market_regime", "NORMAL"),
                len(selected_symbols),
            )
        )

        available_slots = max(max_symbols - len(active_symbols), 0)
        affordable_slots = int(wallet_balance // allocation) if allocation > 0 else 0

        recommendations: List[Dict[str, Any]] = []
        blocked: List[Dict[str, Any]] = []

        remaining_slots = min(available_slots, affordable_slots)
        for item in selected_symbols:
            symbol = str(item.get("symbol", "")).upper()
            if not symbol:
                continue

            if risk_gate.get("block_new_entries"):
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "risk_gate_blocked",
                        "detail": risk_gate.get("decision_line", "Risk gate blocked new entries."),
                    }
                )
                continue

            if symbol in active_symbols:
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "already_active_position",
                        "detail": "The account already has an active position for this symbol.",
                    }
                )
                continue

            if allocation <= 0 or wallet_balance < allocation:
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "insufficient_wallet_balance",
                        "detail": "Wallet balance is below the profile allocation required for a new entry.",
                    }
                )
                continue

            if remaining_slots <= 0:
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "regime_slot_limit_reached",
                        "detail": "The current profile and regime do not allow more concurrent recommendation slots.",
                    }
                )
                continue

            price = float(item.get("price", 0.0) or 0.0)
            estimated_quantity = allocation / price if price > 0 else 0.0
            recommendations.append(
                {
                    "symbol": symbol,
                    "side": "BUY",
                    "profile_name": self.profile.get("name"),
                    "market_regime": market_snapshot.get("market_regime"),
                    "entry_price_reference": price,
                    "allocation": allocation,
                    "estimated_quantity": round(estimated_quantity, 8),
                    "bullish_score": item.get("bullish_score"),
                    "profit_potential": item.get("profit_potential"),
                    "why": (
                        f"Selected by {self.profile.get('name')} under "
                        f"{market_snapshot.get('market_regime')} regime."
                    ),
                }
            )
            remaining_slots -= 1

        decision_line = (
            f"paper-decision recommends {len(recommendations)} order(s) | "
            f"wallet ${wallet_balance:.2f} | active positions {len(active_symbols)} | "
            f"blocked {len(blocked)}"
        )
        return {
            "profile_name": self.profile.get("name"),
            "market_regime": market_snapshot.get("market_regime"),
            "wallet_balance": wallet_balance,
            "active_position_count": len(active_symbols),
            "available_slots": available_slots,
            "affordable_slots": affordable_slots,
            "risk_gate": risk_gate,
            "recommendations": recommendations,
            "blocked": blocked,
            "decision_line": decision_line,
        }
