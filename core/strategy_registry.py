"""
Enhanced Strategy Registry - With minimal thresholds
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

class StrategyRegistry:
    """Enhanced strategy registry with minimal thresholds"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.strategies = self._load_minimal_strategies()
    
    def _load_minimal_strategies(self) -> Dict[str, Any]:
        """Load strategies with minimal thresholds"""
        return {
            'ma_trend_follow': {
                'name': 'ma_trend_follow',
                'type': 'trend_following',
                'entry_filters': {
                    'min_confidence': 0.1,  # Very low
                    'min_trend_strength': 1.0,  # Very low
                    'max_volatility': 1.0,  # Very high
                    'required_alignment_count': 0,  # None required
                    'consensus_threshold': 0  # None required
                },
                'exit_filters': {
                    'min_confidence': 0.1,
                    'min_trend_strength': 1.0,
                    'max_volatility': 1.0
                },
                'risk_config': {
                    'max_position_size': 0.02,
                    'stop_loss_pct': 0.02,
                    'take_profit_pct': 0.04,
                    'max_open_positions': 10
                },
                'symbols': []  # Will be populated dynamically
            },
            'ema_crossover': {
                'name': 'ema_crossover',
                'type': 'trend_following',
                'entry_filters': {
                    'min_confidence': 0.1,  # Very low
                    'min_trend_strength': 1.0,  # Very low
                    'max_volatility': 1.0,  # Very high
                    'required_alignment_count': 0,  # None required
                    'consensus_threshold': 0  # None required
                },
                'exit_filters': {
                    'min_confidence': 0.1,
                    'min_trend_strength': 1.0,
                    'max_volatility': 1.0
                },
                'risk_config': {
                    'max_position_size': 0.02,
                    'stop_loss_pct': 0.02,
                    'take_profit_pct': 0.04,
                    'max_open_positions': 10
                },
                'symbols': []  # Will be populated dynamically
            }
        }
    
    def get_strategy_profile(self, strategy_name: str) -> Dict[str, Any]:
        """Get strategy profile with minimal thresholds"""
        return self.strategies.get(strategy_name, {})
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies"""
        return list(self.strategies.keys())
    
    def update_strategy(self, strategy_name: str, config: Dict[str, Any]) -> bool:
        """Update strategy configuration"""
        try:
            self.strategies[strategy_name] = config
            return True
        except Exception as e:
            self.logger.error(f"Error updating strategy {strategy_name}: {e}")
            return False

    def select_preferred_symbols(
        self,
        strategy_name: str,
        available_symbols: List[Any],
        max_symbols: int = 10,
    ) -> List[str]:
        """Select a bounded symbol list for a strategy."""
        try:
            strategy_config = self.get_strategy_profile(strategy_name)
            if not strategy_config or not available_symbols:
                return []

            symbol_selection = strategy_config.get("symbol_selection", {})
            if not isinstance(symbol_selection, dict):
                symbol_selection = {}

            symbol_mode = symbol_selection.get("symbol_mode", "leaders")
            candidate_limit = min(
                max_symbols,
                int(symbol_selection.get("candidate_limit", max_symbols)),
            )

            symbols: List[str] = []
            for item in available_symbols:
                if isinstance(item, dict):
                    symbol = item.get("symbol")
                else:
                    symbol = str(item)
                if symbol:
                    symbols.append(symbol)

            if not symbols:
                return []

            if symbol_mode == "volatile":
                selected = symbols[: min(len(symbols), candidate_limit * 2) : 2]
                if not selected:
                    selected = symbols[:candidate_limit]
                return selected[:candidate_limit]

            if symbol_mode == "pullback":
                selected = symbols[3 : 3 + candidate_limit]
                if not selected:
                    selected = symbols[:candidate_limit]
                return selected[:candidate_limit]

            if symbol_mode == "balanced":
                head = symbols[: max(1, candidate_limit // 2)]
                tail = symbols[-max(1, candidate_limit // 2) :]
                deduped: List[str] = []
                seen = set()
                for symbol in head + tail:
                    if symbol not in seen:
                        deduped.append(symbol)
                        seen.add(symbol)
                return deduped[:candidate_limit]

            return symbols[:candidate_limit]

        except Exception as e:
            self.log_error("symbol_selection", str(e))
            return []

    def log_error(self, error_type: str, message: str) -> None:
        """Log registry-related errors in a consistent format."""
        self.logger.error(f"[{error_type}] {message}")

    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status"""
        return {
            'total_strategies': len(self.strategies),
            'available_strategies': list(self.strategies.keys()),
            'threshold_type': 'MINIMAL_HARDCODED',
            'timestamp': datetime.now().isoformat()
        }
