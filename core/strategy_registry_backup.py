import json
import logging
from typing import Dict, List, Optional, Any

class StrategyRegistry:
    """V2 Merged: Strategy registry with dynamic symbol selection"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self._strategies = self._load_strategies()
    
    def _load_strategies(self) -> Dict[str, Any]:
        """Load strategy configurations"""
        return {
            'ma_trend_follow': {
                'name': 'MA Trend Following',
                'description': 'Moving average based trend following strategy',
                'type': 'trend_following',
                'timeframes': ['5m', '15m', '1h'],
                'signal_weights': {
                    'ma': 0.5,
                    'ha': 0.2,
                    'fractal': 0.2,
                    'rsi': 0.1
                },
                'ma_config': {
                    'fast_period': 20,
                    'slow_period': 50,
                    'signal_period': 10
                },
                'risk_config': {
                    'stop_loss_pct': 0.02,
                    'take_profit_pct': 0.04,
                    'max_position_size_usdt': 1000.0,
                    'max_open_positions': 3,
                    'leverage': 12.0,
                    'risk_per_trade': 0.015,
                    'partial_tp1_pct': 0.008,
                    'partial_tp2_pct': 0.015,
                    'fast_tp1_pct': 0.005,
                    'fast_tp2_pct': 0.012,
                    'fast_tight_stop_loss_pct': 0.003,
                    'fast_tp1_close_ratio': 0.5,
                    'session_multipliers': {
                        'US_PEAK': {'stop': 1.15, 'take': 1.2},
                        'EU_PEAK': {'stop': 1.0, 'take': 1.0},
                        'ASIA_PEAK': {'stop': 1.0, 'take': 1.0},
                        'DEAD_ZONE': {'stop': 0.95, 'take': 0.9},
                        'NORMAL': {'stop': 1.0, 'take': 1.0}
                    }
                },
                'entry_filters': {
                    'min_confidence': 0.5,
                    'min_trend_strength': 15.0,
                    'max_volatility': 0.08,
                    'required_alignment_count': 1,
                    'consensus_threshold': 1,
                    'fast_entry_min_quality_score': 2,
                    'fast_entry_consensus_relief': 1,
                    'fast_entry_min_trend_consensus_abs': 2
                },
                'symbol_selection': {
                    'candidate_limit': 6,
                    'symbol_mode': 'leaders',
                    'market_bias': 'adaptive'
                }
            },
            'ema_crossover': {
                'name': 'EMA Crossover',
                'description': 'Exponential moving average crossover strategy',
                'type': 'trend_following',
                'timeframes': ['5m', '15m', '1h'],
                'signal_weights': {
                    'ma': 0.6,
                    'ha': 0.2,
                    'fractal': 0.1,
                    'rsi': 0.1
                },
                'ma_config': {
                    'fast_period': 12,
                    'slow_period': 26,
                    'signal_period': 9
                },
                'risk_config': {
                    'stop_loss_pct': 0.015,
                    'take_profit_pct': 0.03,
                    'max_position_size_usdt': 800.0,
                    'max_open_positions': 3,
                    'leverage': 10.0,
                    'risk_per_trade': 0.010,
                    'partial_tp1_pct': 0.008,
                    'partial_tp2_pct': 0.015,
                    'fast_tp1_pct': 0.005,
                    'fast_tp2_pct': 0.012,
                    'fast_tight_stop_loss_pct': 0.003,
                    'fast_tp1_close_ratio': 0.5,
                    'session_multipliers': {
                        'US_PEAK': {'stop': 1.15, 'take': 1.2},
                        'EU_PEAK': {'stop': 1.0, 'take': 1.0},
                        'ASIA_PEAK': {'stop': 1.0, 'take': 1.0},
                        'DEAD_ZONE': {'stop': 0.95, 'take': 0.9},
                        'NORMAL': {'stop': 1.0, 'take': 1.0}
                    }
                },
                'entry_filters': {
                    'min_confidence': 0.55,
                    'min_trend_strength': 20.0,
                    'max_volatility': 0.08,
                    'required_alignment_count': 1,
                    'consensus_threshold': 1,
                    'fast_entry_min_quality_score': 2,
                    'fast_entry_consensus_relief': 1,
                    'fast_entry_min_trend_consensus_abs': 2
                },
                'symbol_selection': {
                    'candidate_limit': 8,
                    'symbol_mode': 'volatile',
                    'market_bias': 'adaptive'
                }
            }
        }
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy names"""
        return list(self._strategies.keys())
    
    def get_strategy_profile(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """Get strategy configuration by name"""
        return self._strategies.get(strategy_name)
    
    def select_preferred_symbols(self, strategy_name: str, 
                                available_symbols: List[Dict[str, Any]],
                                max_symbols: int = 10) -> List[str]:
        """V2 Merged: Select preferred symbols for a strategy"""
        try:
            # Get strategy configuration dynamically
            strategy_config = self.get_strategy_profile(strategy_name)
            if not strategy_config:
                return []
            
            # Get symbol selection configuration with robust error handling
            symbol_selection = strategy_config.get('symbol_selection', {})
            
            # Handle the case where symbol_selection might be malformed
            if not symbol_selection or not isinstance(symbol_selection, dict):
                symbol_selection = {}
            
            # Ensure symbol_selection is a dict
            if isinstance(symbol_selection, str):
                # If it's a string, use default values
                symbol_selection = {}
            elif not isinstance(symbol_selection, dict):
                # If it's neither dict nor string, convert to empty dict
                symbol_selection = {}
            
            # Get values with defaults from configuration
            symbol_mode = symbol_selection.get('symbol_mode', 'leaders')
            candidate_limit = symbol_selection.get('candidate_limit', 6)
            
            # Convert available symbols to list if needed
            if not available_symbols:
                return []
            
            symbols = []
            for s in available_symbols:
                if isinstance(s, dict):
                    symbols.append(s.get('symbol', str(s)))
                elif isinstance(s, str):
                    symbols.append(s)
                else:
                    symbols.append(str(s))
            
            candidates = symbols[:50]  # Use top 50 candidates
            
            # V2 Merged symbol selection modes
            if symbol_mode == 'leaders':
                return candidates[:min(candidate_limit, len(candidates))]
            elif symbol_mode == 'volatile':
                # Select volatile symbols (every other from top)
                volatile_symbols = candidates[:min(candidate_limit * 2, len(candidates)):2]
                if not volatile_symbols:
                    volatile_symbols = candidates[:min(candidate_limit // 2, len(candidates))]
                return volatile_symbols
            elif symbol_mode == 'pullback':
                # Select symbols from middle range
                start_idx = min(3, len(candidates))
                end_idx = min(candidate_limit + 5, len(candidates))
                pullback_symbols = candidates[start_idx:end_idx]
                if not pullback_symbols:
                    pullback_symbols = candidates[:min(candidate_limit, len(candidates))]
                return pullback_symbols
            elif symbol_mode == 'balanced':
                # Mix of top and bottom symbols
                top_symbols = candidates[:min(candidate_limit // 2, len(candidates))]
                bottom_symbols = candidates[-min(candidate_limit // 2, len(candidates)):]
                balanced_symbols = []
                
                # Remove duplicates
                all_symbols = top_symbols + bottom_symbols
                seen = set()
                for symbol in all_symbols:
                    if symbol not in seen:
                        balanced_symbols.append(symbol)
                        seen.add(symbol)
                
                return balanced_symbols[:candidate_limit]
            else:
                return candidates[:min(candidate_limit, len(candidates))]
            
        except Exception as e:
            self.log_error("symbol_selection", str(e))
            # Return fallback symbols
            return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    def select_candidate_symbols(self, available_symbols: List[str], 
                               candidate_limit: int) -> List[str]:
        """V2 Merged: Select candidate symbols evenly across the available universe"""
        try:
            symbols = list(available_symbols)
            if candidate_limit >= len(symbols):
                return symbols
            
            selected = []
            max_index = len(symbols) - 1
            
            for idx in range(candidate_limit):
                position = round((idx * max_index) / max(1, candidate_limit - 1))
                symbol = symbols[position]
                if symbol not in selected:
                    selected.append(symbol)
            
            # Fill remaining slots if needed
            if len(selected) < candidate_limit:
                for symbol in symbols:
                    if symbol not in selected:
                        selected.append(symbol)
                    if len(selected) >= candidate_limit:
                        break
            
            return selected
            
        except Exception as e:
            self.log_error("candidate_selection", str(e))
            return available_symbols[:candidate_limit]
    
    def register_strategy(self, strategy_name: str, strategy_config: Dict[str, Any]):
        """Register a new strategy"""
        try:
            # Validate required fields
            required_fields = ['name', 'type', 'signal_weights', 'risk_config']
            for field in required_fields:
                if field not in strategy_config:
                    raise ValueError(f"Missing required field: {field}")
            
            self._strategies[strategy_name] = strategy_config
            self.logger.info(f"Strategy {strategy_name} registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register strategy {strategy_name}: {e}")
            raise
    
    def log_error(self, error_type: str, message: str):
        """Log error message"""
        self.logger.error(f"[{error_type}] {message}")
