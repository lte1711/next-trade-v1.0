"""Paper decision service for recommendation-only trade planning."""

from __future__ import annotations

from typing import Any, Dict, List
from merged_partial_v2.services.leverage_management_service import LeverageManagementService
from merged_partial_v2.services.capital_allocation_service import CapitalAllocationService


class PaperDecisionService:
    """Turn market candidates and account context into recommendation-only trade decisions."""

    def __init__(self, profile: Dict[str, Any]) -> None:
        self.profile = profile
        self.leverage_service = LeverageManagementService()
        self.allocation_service = CapitalAllocationService()

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
        account_equity = float(account.get("account_equity", 0.0) or 0.0)
        current_invested_notional = self._calculate_active_notional(active_positions)
        total_capital = account_equity if account_equity > 0 else (wallet_balance + current_invested_notional)
        capital_utilization_percent = float(self.profile.get("capital_utilization_percent", 100.0) or 100.0)
        reserve_cash_percent = float(self.profile.get("reserve_cash_percent", 0.0) or 0.0)
        min_allocation = float(self.profile.get("min_allocation", 0.0) or 0.0)
        max_symbols = int(
            self.profile.get("max_symbols_by_regime", {}).get(
                market_snapshot.get("market_regime", "NORMAL"),
                len(selected_symbols),
            )
        )
        target_symbols = selected_symbols[:max_symbols]
        target_symbol_names = [
            str(item.get("symbol", "")).upper()
            for item in target_symbols
            if str(item.get("symbol", "")).strip()
        ]
        target_symbol_count = len(target_symbol_names)
        reserve_cash = total_capital * (reserve_cash_percent / 100.0)
        target_invested_capital = max((total_capital * (capital_utilization_percent / 100.0)) - reserve_cash, 0.0)
        target_allocation = (
            target_invested_capital / target_symbol_count
            if target_symbol_count > 0
            else 0.0
        )
        active_target_count = sum(1 for symbol in active_symbols if symbol in target_symbol_names)
        available_slots = max(target_symbol_count - active_target_count, 0)

        recommendations: List[Dict[str, Any]] = []
        blocked: List[Dict[str, Any]] = []

        for item in target_symbols:
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

            current_symbol_notional = self._position_notional_for_symbol(active_positions, symbol)
            allocation_gap = max(target_allocation - current_symbol_notional, 0.0)
            action = "scale_in" if symbol in active_symbols else "new_entry"

            if target_allocation <= 0 or allocation_gap <= 0:
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "allocation_target_reached",
                        "detail": "The symbol is already at or above the current target allocation.",
                    }
                )
                continue

            if action == "new_entry" and available_slots <= 0:
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "regime_slot_limit_reached",
                        "detail": "The current profile and regime do not allow more concurrent recommendation slots.",
                    }
                )
                continue

            if allocation_gap < min_allocation:
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "allocation_below_minimum",
                        "detail": "The remaining allocation gap is below the minimum order allocation.",
                    }
                )
                continue

            if wallet_balance < allocation_gap:
                blocked.append(
                    {
                        "symbol": symbol,
                        "reason": "insufficient_wallet_balance",
                        "detail": "Wallet balance is below the required allocation gap for this symbol.",
                    }
                )
                continue

            # Apply leverage management
            market_regime = market_snapshot.get("market_regime", "NORMAL")
            symbol_volatility = item.get("volatility", 15.0)  # Default volatility
            
            # Calculate optimal leverage
            leverage_info = self.leverage_service.calculate_optimal_leverage(
                account_balance=wallet_balance,
                symbol_volatility=symbol_volatility,
                market_regime=market_regime
            )
            
            # Validate position size with leverage consideration
            position_validation = self.leverage_service.validate_position_size(
                requested_size=allocation_gap,
                account_balance=wallet_balance,
                leverage=leverage_info["recommended_leverage"],
                symbol=symbol
            )
            
            if not position_validation["valid"]:
                # Adjust allocation based on validation
                allocation_gap = position_validation["recommended_size"]
                if allocation_gap < min_allocation:
                    blocked.append(
                        {
                            "symbol": symbol,
                            "reason": "adjusted_allocation_below_minimum",
                            "detail": f"Leverage-adjusted allocation {allocation_gap:.2f} is below minimum {min_allocation:.2f}.",
                        }
                    )
                    continue

            # Apply capital allocation optimization
            allocation_info = self.allocation_service.calculate_position_allocation(
                total_capital=total_capital,
                active_positions=active_positions,
                new_symbol=symbol,
                target_symbol_count=target_symbol_count
            )
            
            # Use the more conservative allocation
            final_allocation = min(allocation_gap, allocation_info["recommended_allocation"])

            price = float(item.get("price", 0.0) or 0.0)
            estimated_quantity = final_allocation / price if price > 0 else 0.0
            
            recommendations.append(
                {
                    "symbol": symbol,
                    "side": "BUY",
                    "action": action,
                    "profile_name": self.profile.get("name"),
                    "market_regime": market_regime,
                    "entry_price_reference": price,
                    "allocation": final_allocation,
                    "estimated_quantity": round(estimated_quantity, 8),
                    "current_notional": current_symbol_notional,
                    "target_allocation": target_allocation,
                    "target_invested_capital": target_invested_capital,
                    "leverage": leverage_info["recommended_leverage"],
                    "leverage_info": leverage_info,
                    "allocation_info": allocation_info,
                    "position_validation": position_validation,
                    "bullish_score": item.get("bullish_score"),
                    "profit_potential": item.get("profit_potential"),
                    "reason": (
                        f"Selected by {self.profile.get('name')} under "
                        f"{market_regime} regime with leverage {leverage_info['recommended_leverage']}x."
                    ),
                }
            )
            if action == "new_entry":
                available_slots -= 1

        decision_line = (
            f"paper-decision recommends {len(recommendations)} order(s) | "
            f"wallet ${wallet_balance:.2f} | invested ${current_invested_notional:.2f} | "
            f"target invest ${target_invested_capital:.2f} | active positions {len(active_symbols)} | "
            f"blocked {len(blocked)}"
        )
        return {
            "profile_name": self.profile.get("name"),
            "market_regime": market_snapshot.get("market_regime"),
            "wallet_balance": wallet_balance,
            "account_equity": account_equity,
            "current_invested_notional": current_invested_notional,
            "target_invested_capital": target_invested_capital,
            "target_allocation_per_symbol": target_allocation,
            "target_symbol_count": target_symbol_count,
            "capital_utilization_percent": capital_utilization_percent,
            "reserve_cash_percent": reserve_cash_percent,
            "active_position_count": len(active_symbols),
            "available_slots": available_slots,
            "risk_gate": risk_gate,
            "recommendations": recommendations,
            "blocked": blocked,
            "decision_line": decision_line,
        }

    def _calculate_active_notional(self, active_positions: List[Dict[str, Any]]) -> float:
        total = 0.0
        for position in active_positions:
            total += self._position_notional(position)
        return total

    def _position_notional_for_symbol(
        self,
        active_positions: List[Dict[str, Any]],
        symbol: str,
    ) -> float:
        target = str(symbol).upper()
        for position in active_positions:
            if str(position.get("symbol", "")).upper() == target:
                return self._position_notional(position)
        return 0.0

    def _position_notional(self, position: Dict[str, Any]) -> float:
        amount = abs(float(position.get("positionAmt", 0.0) or 0.0))
        mark_price = float(position.get("markPrice", 0.0) or 0.0)
        return amount * mark_price
