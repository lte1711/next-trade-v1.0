"""
Strategy Registry - Strategy profiles and dynamic strategy management
"""

from typing import List, Dict, Optional, Any
from decimal import Decimal
import json

class StrategyRegistry:
    """Strategy registration and configuration management"""
    
    def __init__(self, log_error_callback=None):
        self.log_error = log_error_callback or self._default_log_error
        self._strategies = {}
        self._initialize_default_strategies()
    
    def _default_log_error(self, error_type, message):
        """Default error logging"""
        print(f"[ERROR] {error_type}: {message}")
    
    def _initialize_default_strategies(self):
        """Initialize default strategy configurations"""
        self._strategies = {
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
                    # V2 Merged partial take profit
                    'partial_tp1_pct': 0.008,  # 0.8%
                    'partial_tp2_pct': 0.015,  # 1.5%
                    'fast_tp1_pct': 0.005,     # 0.5%
                    'fast_tp2_pct': 0.012,     # 1.2%
                    'fast_tight_stop_loss_pct': 0.003,  # 0.3%
                    'fast_tp1_close_ratio': 0.50,
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
                'type': 'crossover',
                'timeframes': ['5m', '15m'],
                'signal_weights': {
                    'ma': 0.7,
                    'ha': 0.2,
                    'fractal': 0.1,
                    'rsi': 0.0
                },
                'ma_config': {
                    'fast_period': 12,
                    'slow_period': 26,
                    'signal_period': 9
                },
                'risk_config': {
                    'stop_loss_pct': 0.02 * 0.75,  # 75% of base stop loss
                    'take_profit_pct': 0.04 * 0.75,  # 75% of base take profit
                    'max_position_size_usdt': 1000.0 * 0.8,  # 80% of base size
                    'max_open_positions': 3,
                    'leverage': 8.0,
                    'risk_per_trade': 0.012,
                    # V2 Merged partial take profit
                    'partial_tp1_pct': 0.006,  # 0.6% (0.8% * 0.75)
                    'partial_tp2_pct': 0.011,  # 1.1% (1.5% * 0.75)
                    'fast_tp1_pct': 0.004,     # 0.4% (0.5% * 0.8)
                    'fast_tp2_pct': 0.009,     # 0.9% (1.2% * 0.75)
                    'fast_tight_stop_loss_pct': 0.002,  # 0.2% (0.3% * 0.75)
                    'fast_tp1_close_ratio': 0.50,
                    'session_multipliers': {
                        'US_PEAK': {'stop': 1.15, 'take': 1.2},
                        'EU_PEAK': {'stop': 1.0, 'take': 1.0},
                        'ASIA_PEAK': {'stop': 1.0, 'take': 1.0},
                        'DEAD_ZONE': {'stop': 0.95, 'take': 0.9},
                        'NORMAL': {'stop': 1.0, 'take': 1.0}
                    }
                },
                'entry_filters': {
                    'min_confidence': 0.6,
                    'min_trend_strength': 10.0,
                    'max_volatility': 0.06,
                    'required_alignment_count': 1,
                    'consensus_threshold': 1,
                    'fast_entry_min_quality_score': 2,
                    'fast_entry_consensus_relief': 1,
                    'fast_entry_min_trend_consensus_abs': 2
                },
                'symbol_selection': {
                    'candidate_limit': 8,
                    'symbol_mode': 'leaders',
                    'market_bias': 'adaptive'
                }
            },
            'fractal_breakout': {
                'name': 'Fractal Breakout',
                'description': 'Fractal pattern based breakout strategy',
                'type': 'breakout',
                'timeframes': ['15m', '1h'],
                'signal_weights': {
                    'ma': 0.2,
                    'ha': 0.3,
                    'fractal': 0.4,
                    'rsi': 0.1
                },
                'ma_config': {
                    'fast_period': 10,
                    'slow_period': 30,
                    'signal_period': 5
                },
                'risk_config': {
                    'stop_loss_pct': 0.025,
                    'take_profit_pct': 0.05,
                    'max_position_size_usdt': 1200.0,
                    'max_open_positions': 3,
                    'leverage': 10.0,
                    'risk_per_trade': 0.010,
                    # V2 Merged partial take profit
                    'partial_tp1_pct': 0.008,  # 0.8%
                    'partial_tp2_pct': 0.015,  # 1.5%
                    'fast_tp1_pct': 0.005,     # 0.5%
                    'fast_tp2_pct': 0.012,     # 1.2%
                    'fast_tight_stop_loss_pct': 0.003,  # 0.3%
                    'fast_tp1_close_ratio': 0.50,
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
            strategy_config = self.get_strategy_profile(strategy_name)
            if not strategy_config:
                return []
            
            # Get symbol selection configuration
            symbol_selection = strategy_config.get('symbol_selection', {})
            symbol_mode = symbol_selection.get('symbol_mode', 'leaders')
            candidate_limit = symbol_selection.get('candidate_limit', 6)
            
            # Convert available symbols to list if needed
            if available_symbols and isinstance(available_symbols[0], dict):
                symbols = [s.get('symbol', s) for s in available_symbols]
            else:
                symbols = list(available_symbols)
            
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
            return True
            
        except Exception as e:
            self.log_error("strategy_registration", str(e))
            return False
    
    def generate_dynamic_strategies(self, market_conditions: Dict[str, Any]) -> List[str]:
        """Generate strategy recommendations based on market conditions"""
        try:
            regime = market_conditions.get('regime', 'UNKNOWN')
            volatility = market_conditions.get('volatility_level', 0.0)
            trend_strength = market_conditions.get('trend_strength', 0.0)
            
            recommended_strategies = []
            
            if regime == 'BULL_TREND' and trend_strength > 30:
                recommended_strategies.extend(['ma_trend_follow', 'ema_crossover'])
            elif regime == 'BEAR_TREND' and trend_strength > 30:
                recommended_strategies.extend(['ma_trend_follow'])
            elif regime == 'RANGING':
                recommended_strategies.extend(['fractal_breakout'])
            elif regime == 'HIGH_VOLATILITY':
                # In high volatility, prefer strategies with tighter risk management
                recommended_strategies.extend(['ema_crossover'])
            else:
                # Default recommendations
                recommended_strategies.extend(['ma_trend_follow', 'ema_crossover'])
            
            return list(set(recommended_strategies))  # Remove duplicates
            
        except Exception as e:
            self.log_error("dynamic_strategy_generation", str(e))
            return ['ma_trend_follow']  # Default fallback
    
    def select_preferred_symbols(self, strategy_name: str, 
                                available_symbols: List[Dict[str, Any]],
                                max_symbols: int = 10) -> List[str]:
        """Select preferred symbols for a strategy"""
        try:
            strategy_config = self.get_strategy_profile(strategy_name)
            if not strategy_config:
                return []
            
            # Filter symbols based on strategy preferences
            preferred_symbols = []
            
            for symbol_info in available_symbols:
                symbol = symbol_info.get('symbol')
                
                # Basic filters
                if not symbol:
                    continue
                
                # Prefer high volume symbols
                volume = symbol_info.get('volume', 0)
                if volume < getattr(self, 'min_volume_threshold', 1000000):  # Minimum volume threshold
                    continue
                
                # Prefer major pairs for trend following
                if strategy_config.get('type') == 'trend_following':
                    if any(major in symbol for major in ['BTC', 'ETH', 'BNB']):
                        preferred_symbols.append(symbol)
                # Prefer more volatile symbols for breakout
                elif strategy_config.get('type') == 'breakout':
                    preferred_symbols.append(symbol)
                else:
                    preferred_symbols.append(symbol)
            
            return preferred_symbols[:max_symbols]
            
        except Exception as e:
            self.log_error("symbol_selection", str(e))
            return []
    
    def generate_strategy_config(self, strategy_name: str, 
                                market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dynamic strategy configuration based on market conditions"""
        try:
            base_config = self.get_strategy_profile(strategy_name)
            if not base_config:
                return {}
            
            volatility = market_conditions.get('volatility_level', 0.0)
            trend_strength = market_conditions.get('trend_strength', 0.0)
            
            # Create dynamic config
            dynamic_config = base_config.copy()
            
            # Adjust risk parameters based on volatility
            risk_config = dynamic_config.get('risk_config', {}).copy()
            if volatility > 0.04:  # High volatility
                risk_config['stop_loss_pct'] *= 1.5  # Wider stops
                risk_config['take_profit_pct'] *= 1.2  # Wider targets
                risk_config['max_position_size_usdt'] *= 0.8  # Smaller positions
            elif volatility < 0.02:  # Low volatility
                risk_config['stop_loss_pct'] *= 0.8  # Tighter stops
                risk_config['take_profit_pct'] *= 0.9  # Tighter targets
                risk_config['max_position_size_usdt'] *= 1.2  # Larger positions
            
            # Adjust confidence threshold based on trend strength
            entry_filters = dynamic_config.get('entry_filters', {}).copy()
            if trend_strength > 40:  # Strong trend
                entry_filters['min_confidence'] *= 0.9  # Lower threshold
            elif trend_strength < 20:  # Weak trend
                entry_filters['min_confidence'] *= 1.1  # Higher threshold
            
            dynamic_config['risk_config'] = risk_config
            dynamic_config['entry_filters'] = entry_filters
            
            return dynamic_config
            
        except Exception as e:
            self.log_error("config_generation", str(e))
            return self.get_strategy_profile(strategy_name) or {}
    
    def validate_strategy_config(self, strategy_config: Dict[str, Any]) -> bool:
        """Validate strategy configuration"""
        try:
            # Check required sections
            required_sections = ['signal_weights', 'risk_config', 'entry_filters']
            for section in required_sections:
                if section not in strategy_config:
                    return False
            
            # Check signal weights sum to 1.0 (approximately)
            signal_weights = strategy_config.get('signal_weights', {})
            total_weight = sum(signal_weights.values())
            if abs(total_weight - 1.0) > 0.1:  # Allow 10% tolerance
                return False
            
            # Check risk parameters are reasonable
            risk_config = strategy_config.get('risk_config', {})
            stop_loss = risk_config.get('stop_loss_pct', 0.0)
            take_profit = risk_config.get('take_profit_pct', 0.0)
            
            if stop_loss <= 0 or stop_loss > 0.1:  # Max 10% stop loss
                return False
            if take_profit <= 0 or take_profit > 0.2:  # Max 20% take profit
                return False
            if take_profit <= stop_loss:  # Take profit must be greater than stop loss
                return False
            
            return True
            
        except Exception as e:
            self.log_error("config_validation", str(e))
            return False
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of all registered strategies"""
        try:
            summary = {
                'total_strategies': len(self._strategies),
                'strategy_types': {},
                'strategy_list': []
            }
            
            for name, config in self._strategies.items():
                strategy_type = config.get('type', 'unknown')
                summary['strategy_types'][strategy_type] = summary['strategy_types'].get(strategy_type, 0) + 1
                
                summary['strategy_list'].append({
                    'name': name,
                    'display_name': config.get('name', name),
                    'type': strategy_type,
                    'description': config.get('description', ''),
                    'timeframes': config.get('timeframes', [])
                })
            
            return summary
            
        except Exception as e:
            self.log_error("strategy_summary", str(e))
            return {}
