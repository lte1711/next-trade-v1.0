#!/usr/bin/env python3
"""
Dynamic Symbol Manager - Manage dynamic symbol loading and filtering
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime

class DynamicSymbolManager:
    """Dynamic symbol manager with filtering and ranking"""
    
    def __init__(self, market_data_service=None):
        self.logger = logging.getLogger(__name__)
        self.mds = market_data_service
        self.available_symbols = []
        self.filtered_symbols = []
        self.ranked_symbols = []
        self.last_update = None
        
    def load_available_symbols(self) -> List[str]:
        """Load all available symbols from market data service"""
        try:
            if not self.mds:
                from core.market_data_service import MarketDataService
                self.mds = MarketDataService('https://demo-fapi.binance.com')
            
            # Get available symbols
            symbols_data = self.mds.get_available_symbols()
            
            # Extract symbol names
            self.available_symbols = []
            for symbol_info in symbols_data:
                if isinstance(symbol_info, dict):
                    symbol = symbol_info.get('symbol', '')
                else:
                    symbol = str(symbol_info)
                
                # Only include USDT perpetual contracts
                if symbol.endswith('USDT') and symbol not in self.available_symbols:
                    self.available_symbols.append(symbol)
            
            self.last_update = datetime.now()
            
            self.logger.info(f"Loaded {len(self.available_symbols)} available symbols")
            return self.available_symbols
            
        except Exception as e:
            self.logger.error(f"Error loading available symbols: {e}")
            return []
    
    def filter_symbols(self, filters: Dict[str, Any] = None) -> List[str]:
        """Filter symbols based on criteria"""
        try:
            if not self.available_symbols:
                self.load_available_symbols()
            
            if not filters:
                filters = self._get_default_filters()
            
            filtered = []
            
            for symbol in self.available_symbols:
                if self._passes_filters(symbol, filters):
                    filtered.append(symbol)
            
            self.filtered_symbols = filtered
            self.logger.info(f"Filtered to {len(filtered)} symbols")
            return filtered
            
        except Exception as e:
            self.logger.error(f"Error filtering symbols: {e}")
            return self.available_symbols
    
    def rank_symbols(self, ranking_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Rank symbols by volume and other criteria"""
        try:
            if not self.filtered_symbols:
                self.filter_symbols()
            
            if not ranking_criteria:
                ranking_criteria = self._get_default_ranking_criteria()
            
            ranked = []
            
            for symbol in self.filtered_symbols:
                # Get symbol data for ranking
                symbol_data = self._get_symbol_data(symbol)
                
                # Calculate ranking score
                score = self._calculate_ranking_score(symbol_data, ranking_criteria)
                
                ranked.append({
                    'symbol': symbol,
                    'score': score,
                    'data': symbol_data
                })
            
            # Sort by score (descending)
            ranked.sort(key=lambda x: x['score'], reverse=True)
            
            self.ranked_symbols = ranked
            self.logger.info(f"Ranked {len(ranked)} symbols")
            return ranked
            
        except Exception as e:
            self.logger.error(f"Error ranking symbols: {e}")
            return []
    
    def get_top_symbols(self, limit: int = 20) -> List[str]:
        """Get top N symbols by ranking"""
        try:
            if not self.ranked_symbols:
                self.rank_symbols()
            
            top_symbols = [item['symbol'] for item in self.ranked_symbols[:limit]]
            return top_symbols
            
        except Exception as e:
            self.logger.error(f"Error getting top symbols: {e}")
            return self.available_symbols[:limit]
    
    def get_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """Get detailed data for a specific symbol"""
        try:
            return self._get_symbol_data(symbol)
        except Exception as e:
            self.logger.error(f"Error getting symbol data for {symbol}: {e}")
            return {}
    
    def refresh_symbols(self, force: bool = False) -> bool:
        """Refresh symbol list"""
        try:
            now = datetime.now()
            
            # Check if refresh is needed (every hour)
            if not force and self.last_update:
                time_diff = (now - self.last_update).total_seconds()
                if time_diff < 3600:  # 1 hour
                    return True
            
            # Reload symbols
            self.load_available_symbols()
            self.filter_symbols()
            self.rank_symbols()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error refreshing symbols: {e}")
            return False
    
    def get_symbol_statistics(self) -> Dict[str, Any]:
        """Get statistics about symbols"""
        try:
            stats = {
                'total_available': len(self.available_symbols),
                'total_filtered': len(self.filtered_symbols),
                'total_ranked': len(self.ranked_symbols),
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'top_symbols': self.get_top_symbols(10),
                'filter_criteria': self._get_default_filters(),
                'ranking_criteria': self._get_default_ranking_criteria()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting symbol statistics: {e}")
            return {}
    
    def _get_default_filters(self) -> Dict[str, Any]:
        """Get default filtering criteria"""
        return {
            'min_volume': 1000000,  # Minimum 24h volume
            'min_price': 0.00001,    # Minimum price
            'max_price': 100000,      # Maximum price
            'status': 'TRADING',       # Trading status
            'contract_type': 'PERPETUAL',  # Contract type
            'exclude_symbols': [],      # Symbols to exclude
            'include_only': []          # Only include these symbols (empty = all)
        }
    
    def _get_default_ranking_criteria(self) -> Dict[str, Any]:
        """Get default ranking criteria"""
        return {
            'volume_weight': 0.4,      # 40% weight to volume
            'volatility_weight': 0.3,   # 30% weight to volatility
            'price_weight': 0.2,        # 20% weight to price (mid-range preferred)
            'change_weight': 0.1         # 10% weight to 24h change
        }
    
    def _passes_filters(self, symbol: str, filters: Dict[str, Any]) -> bool:
        """Check if symbol passes filters"""
        try:
            symbol_data = self._get_symbol_data(symbol)
            
            # Check include only filter
            include_only = filters.get('include_only', [])
            if include_only and symbol not in include_only:
                return False
            
            # Check exclude filter
            exclude_symbols = filters.get('exclude_symbols', [])
            if symbol in exclude_symbols:
                return False
            
            # Check trading status
            if 'status' in filters:
                if symbol_data.get('status') != filters['status']:
                    return False
            
            # Check contract type
            if 'contract_type' in filters:
                if symbol_data.get('contract_type') != filters['contract_type']:
                    return False
            
            # Check minimum volume
            if 'min_volume' in filters:
                volume = symbol_data.get('volume', 0)
                if volume < filters['min_volume']:
                    return False
            
            # Check price range
            price = symbol_data.get('price', 0)
            if 'min_price' in filters and price < filters['min_price']:
                return False
            if 'max_price' in filters and price > filters['max_price']:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking filters for {symbol}: {e}")
            return False
    
    def _get_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """Get symbol data from market data service"""
        try:
            if not self.mds:
                return {}
            
            # Get symbol data from available symbols
            for symbol_info in self.available_symbols:
                if isinstance(symbol_info, dict):
                    if symbol_info.get('symbol') == symbol:
                        return symbol_info
                elif str(symbol_info) == symbol:
                    return {'symbol': symbol}
            
            # If not found, try to get from market data
            try:
                market_data = self.mds.update_market_data([symbol])
                if symbol in market_data:
                    data = market_data[symbol]
                    prices = data.get('prices', {})
                    klines = data.get('klines', {})
                    
                    # Calculate 24h change from klines
                    change_24h = 0
                    if '1h' in klines and len(klines['1h']) >= 24:
                        current_price = klines['1h'][-1]['close']
                        old_price = klines['1h'][0]['close']
                        change_24h = ((current_price - old_price) / old_price) * 100
                    
                    return {
                        'symbol': symbol,
                        'price': prices.get('current', 0),
                        'volume': klines.get('1h', [])[-1].get('volume', 0) if klines.get('1h') else 0,
                        'change_24h': change_24h,
                        'status': 'TRADING',
                        'contract_type': 'PERPETUAL'
                    }
            except:
                pass
            
            return {'symbol': symbol, 'status': 'UNKNOWN'}
            
        except Exception as e:
            self.logger.error(f"Error getting symbol data for {symbol}: {e}")
            return {}
    
    def _calculate_ranking_score(self, symbol_data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate ranking score for symbol"""
        try:
            score = 0.0
            
            # Volume score (normalized)
            volume = symbol_data.get('volume', 0)
            volume_score = min(volume / 100000000, 1.0)  # Normalize to 0-1
            score += volume_score * criteria.get('volume_weight', 0.4)
            
            # Volatility score (moderate volatility preferred)
            volatility = symbol_data.get('volatility', 0)
            volatility_score = min(volatility / 0.1, 1.0)  # Normalize to 0-1
            score += volatility_score * criteria.get('volatility_weight', 0.3)
            
            # Price score (mid-range preferred)
            price = symbol_data.get('price', 0)
            if price > 0:
                # Log scale for price
                log_price = max(0, min(10, (abs(price).bit_length() - 10) / 2))
                price_score = 1.0 - abs(log_price - 5) / 5  # Prefer mid-range
                score += price_score * criteria.get('price_weight', 0.2)
            
            # 24h change score (moderate change preferred)
            change_24h = symbol_data.get('change_24h', 0)
            change_score = max(0, 1.0 - abs(change_24h) / 10)  # Prefer stable
            score += change_score * criteria.get('change_weight', 0.1)
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating ranking score: {e}")
            return 0.0
    
    def save_configuration(self, config_file: str = 'symbol_config.json') -> bool:
        """Save current configuration to file"""
        try:
            config = {
                'filters': self._get_default_filters(),
                'ranking_criteria': self._get_default_ranking_criteria(),
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'statistics': self.get_symbol_statistics()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def load_configuration(self, config_file: str = 'symbol_config.json') -> bool:
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Update filters and criteria
            if 'filters' in config:
                self._default_filters = config['filters']
            if 'ranking_criteria' in config:
                self._default_ranking_criteria = config['ranking_criteria']
            
            self.logger.info(f"Configuration loaded from {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
