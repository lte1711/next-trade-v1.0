"""Capital allocation service for efficient position sizing and risk management."""

from __future__ import annotations

from typing import Any, Dict, List
from merged_partial_v2.pathing import merged_root
from pathlib import Path
import json


class CapitalAllocationService:
    """Manage capital allocation across positions and optimize sizing."""

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or self._load_config()
        self.allocation_config = self.config.get("capital_allocation", {})
        self.risk_limits = self.config.get("risk_limits", {})

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json."""
        config_path = merged_root() / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return {}

    def calculate_position_allocation(self,
                                   total_capital: float,
                                   active_positions: List[Dict[str, Any]],
                                   new_symbol: str,
                                   target_symbol_count: int) -> Dict[str, Any]:
        """Calculate optimal allocation for a new position."""
        max_position_size = float(self.allocation_config.get("max_allocation_per_position", 5000.0))
        min_position_size = float(self.allocation_config.get("min_allocation_per_position", 100.0))
        max_total_exposure = float(self.risk_limits.get("max_total_exposure_percent", 95.0)) / 100
        
        # Calculate current exposure
        current_exposure = sum(
            abs(float(pos.get("positionAmt", 0)) * float(pos.get("markPrice", 0)))
            for pos in active_positions
        )
        
        # Available capital for new positions
        available_exposure = total_capital * max_total_exposure - current_exposure
        available_for_new = min(available_exposure, max_position_size)
        
        # Calculate allocation based on target symbol count
        if target_symbol_count > 0:
            equal_allocation = total_capital / target_symbol_count
            optimal_allocation = min(equal_allocation, available_for_new, max_position_size)
        else:
            optimal_allocation = min(available_for_new, max_position_size)
        
        # Ensure minimum allocation
        optimal_allocation = max(optimal_allocation, min_position_size)
        
        return {
            "recommended_allocation": optimal_allocation,
            "available_exposure": available_exposure,
            "current_exposure": current_exposure,
            "total_exposure_percent": (current_exposure / total_capital) * 100,
            "max_position_size": max_position_size,
            "target_symbol_count": target_symbol_count,
            "new_symbol": new_symbol,
        }

    def should_rebalance_portfolio(self,
                                 active_positions: List[Dict[str, Any]],
                                 target_allocation: Dict[str, float]) -> Dict[str, Any]:
        """Determine if portfolio rebalancing is needed."""
        rebalance_threshold = float(self.allocation_config.get("rebalance_threshold_percent", 10.0)) / 100
        
        rebalance_needed = []
        current_allocations = {}
        
        for position in active_positions:
            symbol = position.get("symbol")
            current_value = abs(float(position.get("positionAmt", 0)) * float(position.get("markPrice", 0)))
            current_allocations[symbol] = current_value
            
            if symbol in target_allocation:
                target_value = target_allocation[symbol]
                deviation = abs(current_value - target_value) / target_value
                
                if deviation > rebalance_threshold:
                    rebalance_needed.append({
                        "symbol": symbol,
                        "current_value": current_value,
                        "target_value": target_value,
                        "deviation_percent": deviation * 100,
                        "action": "reduce" if current_value > target_value else "increase",
                    })
        
        return {
            "should_rebalance": len(rebalance_needed) > 0,
            "rebalance_positions": rebalance_needed,
            "rebalance_threshold": rebalance_threshold * 100,
            "current_allocations": current_allocations,
            "target_allocations": target_allocation,
        }

    def calculate_profit_taking_levels(self,
                                     position: Dict[str, Any],
                                     entry_price: float) -> Dict[str, Any]:
        """Calculate profit taking levels for a position."""
        profit_taking_threshold = float(self.allocation_config.get("profit_taking_threshold_percent", 50.0)) / 100
        stop_loss_threshold = float(self.allocation_config.get("stop_loss_threshold_percent", 20.0)) / 100
        
        position_value = abs(float(position.get("positionAmt", 0)) * float(position.get("markPrice", 0)))
        unrealized_pnl = float(position.get("unRealizedProfit", 0))
        pnl_percent = (unrealized_pnl / position_value) * 100 if position_value > 0 else 0
        
        # Calculate levels
        profit_target = entry_price * (1 + profit_taking_threshold)
        stop_loss = entry_price * (1 - stop_loss_threshold)
        
        # Current status
        current_price = float(position.get("markPrice", entry_price))
        is_profit_target = current_price >= profit_target
        is_stop_loss = current_price <= stop_loss
        
        return {
            "symbol": position.get("symbol"),
            "entry_price": entry_price,
            "current_price": current_price,
            "profit_target": profit_target,
            "stop_loss": stop_loss,
            "profit_taking_threshold": profit_taking_threshold * 100,
            "stop_loss_threshold": stop_loss_threshold * 100,
            "current_pnl_percent": pnl_percent,
            "should_take_profit": is_profit_target,
            "should_stop_loss": is_stop_loss,
            "position_value": position_value,
        }

    def optimize_capital_distribution(self,
                                    total_capital: float,
                                    market_regime: str,
                                    volatility_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Optimize capital distribution based on market conditions."""
        max_positions = int(self.allocation_config.get("max_positions_per_symbol", 1))
        max_exposure = float(self.risk_limits.get("max_total_exposure_percent", 95.0)) / 100
        
        # Adjust allocation based on market regime
        regime_adjustments = {
            "NORMAL": 1.0,
            "HIGH_VOLATILITY": 0.7,
            "EXTREME": 0.4,
        }
        
        adjustment_factor = regime_adjustments.get(market_regime, 1.0)
        adjusted_max_exposure = max_exposure * adjustment_factor
        
        # Calculate optimal position count
        avg_volatility = sum(volatility_metrics.values()) / len(volatility_metrics) if volatility_metrics else 15.0
        
        if avg_volatility > 20:
            # High volatility - fewer positions, smaller size
            recommended_positions = min(3, max_positions)
            position_size_factor = 0.6
        elif avg_volatility < 10:
            # Low volatility - more positions, larger size
            recommended_positions = min(5, max_positions)
            position_size_factor = 1.2
        else:
            # Normal volatility
            recommended_positions = min(4, max_positions)
            position_size_factor = 1.0
        
        # Calculate per-position allocation
        available_capital = total_capital * adjusted_max_exposure
        per_position_allocation = (available_capital / recommended_positions) * position_size_factor
        
        return {
            "recommended_position_count": recommended_positions,
            "per_position_allocation": per_position_allocation,
            "total_available_capital": available_capital,
            "max_exposure_percent": adjusted_max_exposure * 100,
            "market_regime": market_regime,
            "adjustment_factor": adjustment_factor,
            "avg_volatility": avg_volatility,
            "position_size_factor": position_size_factor,
            "volatility_metrics": volatility_metrics,
        }

    def validate_risk_limits(self,
                           proposed_positions: List[Dict[str, Any]],
                           total_capital: float) -> Dict[str, Any]:
        """Validate if proposed positions exceed risk limits."""
        max_total_exposure = float(self.risk_limits.get("max_total_exposure_percent", 95.0)) / 100
        max_position_size = float(self.risk_limits.get("max_position_size_percent", 20.0)) / 100
        
        # Calculate total proposed exposure
        total_proposed_exposure = sum(pos.get("allocation", 0) for pos in proposed_positions)
        
        # Check individual position limits
        oversized_positions = []
        for pos in proposed_positions:
            allocation = pos.get("allocation", 0)
            position_percent = (allocation / total_capital) * 100 if total_capital > 0 else 0
            
            if position_percent > max_position_size * 100:
                oversized_positions.append({
                    "symbol": pos.get("symbol"),
                    "allocation": allocation,
                    "position_percent": position_percent,
                    "max_allowed_percent": max_position_size * 100,
                })
        
        # Check total exposure
        total_exposure_percent = (total_proposed_exposure / total_capital) * 100 if total_capital > 0 else 0
        exceeds_total_limit = total_exposure_percent > max_total_exposure * 100
        
        return {
            "valid": len(oversized_positions) == 0 and not exceeds_total_limit,
            "total_proposed_exposure": total_proposed_exposure,
            "total_exposure_percent": total_exposure_percent,
            "max_total_exposure_percent": max_total_exposure * 100,
            "oversized_positions": oversized_positions,
            "max_position_size_percent": max_position_size * 100,
            "exceeds_total_limit": exceeds_total_limit,
        }
