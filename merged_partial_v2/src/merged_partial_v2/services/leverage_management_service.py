"""Leverage and margin management service for optimal position sizing."""

from __future__ import annotations

from typing import Any, Dict
from merged_partial_v2.pathing import merged_root
from pathlib import Path
import json


class LeverageManagementService:
    """Manage leverage settings and position size limits."""

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or self._load_config()
        self.leverage_config = self.config.get("leverage_management", {})
        self.margin_config = self.config.get("margin_management", {})
        self.allocation_config = self.config.get("capital_allocation", {})

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json."""
        config_path = merged_root() / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return {}

    def calculate_optimal_leverage(self, 
                                account_balance: float,
                                symbol_volatility: float,
                                market_regime: str) -> Dict[str, Any]:
        """Calculate optimal leverage based on market conditions."""
        default_leverage = float(self.leverage_config.get("default_leverage", 3))
        max_leverage = float(self.leverage_config.get("max_leverage", 10))
        adjustment_threshold = float(self.leverage_config.get("leverage_adjustment_threshold", 15.0))
        
        # Adjust leverage based on volatility
        if symbol_volatility > adjustment_threshold:
            # High volatility - reduce leverage
            optimal_leverage = max(default_leverage * 0.5, 1)
        elif symbol_volatility < 5.0:
            # Low volatility - can use higher leverage
            optimal_leverage = min(default_leverage * 1.5, max_leverage)
        else:
            # Normal volatility - use default
            optimal_leverage = default_leverage

        # Additional adjustment for market regime
        if market_regime == "EXTREME":
            optimal_leverage = max(optimal_leverage * 0.7, 1)

        return {
            "recommended_leverage": int(optimal_leverage),
            "max_leverage": max_leverage,
            "default_leverage": default_leverage,
            "adjustment_factor": optimal_leverage / default_leverage,
            "volatility": symbol_volatility,
            "market_regime": market_regime,
        }

    def calculate_position_size_limit(self,
                                   account_balance: float,
                                   leverage: int,
                                   symbol: str) -> Dict[str, Any]:
        """Calculate maximum position size based on margin and leverage."""
        position_size_factor = float(self.leverage_config.get("position_size_limit_factor", 0.8))
        max_margin_utilization = float(self.margin_config.get("max_margin_utilization_percent", 80.0)) / 100
        
        # Available margin for this position
        available_margin = account_balance * max_margin_utilization * position_size_factor
        
        # Maximum position size based on leverage
        max_position_value = available_margin * leverage
        
        # Apply allocation limits
        max_allocation = float(self.allocation_config.get("max_allocation_per_position", 5000.0))
        min_allocation = float(self.allocation_config.get("min_allocation_per_position", 100.0))
        
        max_position_value = min(max_position_value, max_allocation)
        
        return {
            "max_position_value": max(max_position_value, min_allocation),
            "available_margin": available_margin,
            "leverage": leverage,
            "position_size_factor": position_size_factor,
            "max_margin_utilization": max_margin_utilization * 100,
            "symbol": symbol,
        }

    def should_reduce_position(self,
                            current_position_value: float,
                            account_balance: float,
                            unrealized_pnl_percent: float) -> Dict[str, Any]:
        """Determine if position should be reduced due to margin pressure."""
        auto_reduce = bool(self.leverage_config.get("auto_reduce_on_margin_pressure", True))
        emergency_buffer = float(self.margin_config.get("emergency_liquidation_buffer", 10.0))
        
        if not auto_reduce:
            return {"should_reduce": False, "reason": "auto_reduce_disabled"}

        # Check if position is losing money and using too much margin
        margin_utilization = (current_position_value / account_balance) * 100
        is_under_pressure = (
            unrealized_pnl_percent < -emergency_buffer and 
            margin_utilization > 70
        )

        if is_under_pressure:
            reduction_factor = min(abs(unrealized_pnl_percent) / emergency_buffer, 0.5)
            return {
                "should_reduce": True,
                "reduction_factor": reduction_factor,
                "reason": f"margin_pressure_{margin_utilization:.1f}%_pnl_{unrealized_pnl_percent:.1f}%",
                "current_utilization": margin_utilization,
                "pnl_percent": unrealized_pnl_percent,
            }

        return {"should_reduce": False, "reason": "normal_conditions"}

    def get_margin_requirement(self,
                             position_value: float,
                             leverage: int,
                             symbol: str) -> Dict[str, Any]:
        """Calculate margin requirements for a position."""
        initial_margin_ratio = float(self.margin_config.get("initial_margin_ratio", 0.1))
        maintenance_margin_ratio = float(self.margin_config.get("maintenance_margin_ratio", 0.05))
        margin_buffer = float(self.margin_config.get("margin_buffer_percent", 20.0)) / 100
        
        # Base margin requirements
        initial_margin = position_value / leverage * initial_margin_ratio
        maintenance_margin = position_value / leverage * maintenance_margin_ratio
        
        # Add safety buffer
        buffered_initial_margin = initial_margin * (1 + margin_buffer)
        buffered_maintenance_margin = maintenance_margin * (1 + margin_buffer)
        
        return {
            "position_value": position_value,
            "leverage": leverage,
            "initial_margin": initial_margin,
            "maintenance_margin": maintenance_margin,
            "buffered_initial_margin": buffered_initial_margin,
            "buffered_maintenance_margin": buffered_maintenance_margin,
            "margin_buffer_percent": margin_buffer * 100,
            "initial_margin_ratio": initial_margin_ratio,
            "maintenance_margin_ratio": maintenance_margin_ratio,
        }

    def validate_position_size(self,
                              requested_size: float,
                              account_balance: float,
                              leverage: int,
                              symbol: str) -> Dict[str, Any]:
        """Validate if requested position size is within limits."""
        limits = self.calculate_position_size_limit(account_balance, leverage, symbol)
        max_size = limits["max_position_value"]
        
        # Check allocation limits
        max_allocation = float(self.allocation_config.get("max_allocation_per_position", 5000.0))
        
        is_valid = requested_size <= max_size and requested_size <= max_allocation
        
        if not is_valid:
            recommended_size = min(requested_size * 0.8, max_size, max_allocation)
            return {
                "valid": False,
                "requested_size": requested_size,
                "recommended_size": recommended_size,
                "max_allowed": min(max_size, max_allocation),
                "reason": "position_size_exceeds_limits",
                "limits": limits,
            }

        return {
            "valid": True,
            "requested_size": requested_size,
            "max_allowed": min(max_size, max_allocation),
            "limits": limits,
        }
