"""
Account Service - Account information and synchronization
"""

import requests
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any
from decimal import Decimal

class AccountService:
    """Binance Futures account information and synchronization"""
    
    def __init__(self, base_url: str, api_key: str, api_secret: str,
                 log_error_callback=None):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.log_error = log_error_callback or self._default_log_error
        self._last_balance_sync_time = 0
        self._last_position_sync_time = 0
        self._sync_interval = 30  # 30 seconds between syncs
    
    def _default_log_error(self, error_type, message):
        """Default error logging"""
        print(f"[ERROR] {error_type}: {message}")
    
    def _create_signature(self, query_string: str) -> str:
        """Create API signature"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def safe_float_conversion(self, value, default=0.0):
        """Safely convert to float"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                'timestamp': timestamp,
                'recvWindow': 5000
            }
            query_string = '&'.join([f'{k}={v}' for k, v in sorted(params.items())])
            signature = self._create_signature(query_string)
            
            url = f"{self.base_url}/fapi/v2/account?{query_string}&signature={signature}"
            headers = {'X-MBX-APIKEY': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log_error("account_info", f"Failed to get account info: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_error("account_info_exception", str(e))
            return None
    
    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance information"""
        try:
            account_info = self.get_account_info()
            if not account_info:
                return {}
            
            assets = account_info.get('assets', [])
            balances = {}
            
            for asset in assets:
                symbol = asset.get('asset')
                wallet_balance = self.safe_float_conversion(asset.get('walletBalance', 0))
                available_balance = self.safe_float_conversion(asset.get('availableBalance', 0))
                
                if wallet_balance > 0:
                    balances[symbol] = {
                        'wallet_balance': wallet_balance,
                        'available_balance': available_balance,
                        'unrealized_pnl': self.safe_float_conversion(asset.get('unrealizedPnl', 0))
                    }
            
            return balances
            
        except Exception as e:
            self.log_error("account_balance", str(e))
            return {}
    
    def get_total_balance(self) -> float:
        """Get total USDT balance"""
        try:
            balances = self.get_account_balance()
            usdt_balance = balances.get('USDT', {})
            return usdt_balance.get('wallet_balance', 0.0)
        except Exception as e:
            self.log_error("total_balance", str(e))
            return 0.0
    
    def get_available_balance(self) -> float:
        """Get available USDT balance"""
        try:
            balances = self.get_account_balance()
            usdt_balance = balances.get('USDT', {})
            return usdt_balance.get('available_balance', 0.0)
        except Exception as e:
            self.log_error("available_balance", str(e))
            return 0.0
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions"""
        try:
            account_info = self.get_account_info()
            if not account_info:
                return []
            
            positions = account_info.get('positions', [])
            active_positions = []
            
            for position in positions:
                amount = self.safe_float_conversion(position.get('positionAmt', 0))
                if amount != 0:  # Only include positions with non-zero amount
                    active_positions.append({
                        'symbol': position.get('symbol'),
                        'amount': amount,
                        'entry_price': self.safe_float_conversion(position.get('entryPrice', 0)),
                        'mark_price': self.safe_float_conversion(position.get('markPrice', 0)),
                        'unrealized_pnl': self.safe_float_conversion(position.get('unrealizedPnl', 0)),
                        'percentage': self.safe_float_conversion(position.get('percentage', 0)),
                        'side': 'LONG' if amount > 0 else 'SHORT'
                    })
            
            return active_positions
            
        except Exception as e:
            self.log_error("positions_get", str(e))
            return []
    
    def sync_account_balance(self, trading_results: Dict[str, Any]) -> bool:
        """Synchronize account balance with trading results"""
        try:
            current_time = time.time()
            if current_time - self._last_balance_sync_time < self._sync_interval:
                return True  # Skip sync if too recent
            
            balances = self.get_account_balance()
            if not balances:
                return False
            
            # Update trading results
            trading_results["account_balance"] = balances
            trading_results["total_balance"] = self.get_total_balance()
            trading_results["available_balance"] = self.get_available_balance()
            
            self._last_balance_sync_time = current_time
            return True
            
        except Exception as e:
            self.log_error("account_balance_sync", str(e))
            return False
    
    def sync_positions(self, trading_results: Dict[str, Any]) -> bool:
        """Synchronize positions with exchange while preserving local position metadata"""
        try:
            current_time = time.time()
            if current_time - self._last_position_sync_time < self._sync_interval:
                return True
            
            positions = self.get_positions()
            if positions is None:
                return False
            
            existing_positions = trading_results.get("active_positions", {})
            active_positions = {}
            
            for position in positions:
                symbol = position['symbol']
                existing = existing_positions.get(symbol, {})
                
                active_positions[symbol] = {
                    'symbol': symbol,
                    'amount': position['amount'],
                    'entry_price': position['entry_price'],
                    'mark_price': position['mark_price'],
                    'current_price': existing.get('current_price', position['mark_price']),
                    'unrealized_pnl': position['unrealized_pnl'],
                    'percentage': position['percentage'],
                    'side': position['side'],
                    'strategy': existing.get('strategy'),
                    'entry_time': existing.get('entry_time'),
                    'signal_confidence': existing.get('signal_confidence'),
                    'stop_loss_pct': existing.get('stop_loss_pct'),
                    'take_profit_pct': existing.get('take_profit_pct'),
                    'last_sync': int(current_time * 1000)
                }
            
            trading_results["active_positions"] = active_positions
            
            self._last_position_sync_time = current_time
            return True
            
        except Exception as e:
            self.log_error("positions_sync", str(e))
            return False
    
    def can_open_new_positions(self, trading_results: Dict[str, Any], 
                            max_positions: int = 1) -> bool:
        """Check if new positions can be opened"""
        try:
            # Check position limit
            active_positions = trading_results.get("active_positions", {})
            if len(active_positions) >= max_positions:
                return False
            
            # Check available balance
            available_balance = trading_results.get("available_balance", 0.0)
            min_balance_threshold = 50.0  # Minimum USDT required
            
            if available_balance < min_balance_threshold:
                return False
            
            return True
            
        except Exception as e:
            self.log_error("can_open_positions", str(e))
            return False
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        try:
            balances = self.get_account_balance()
            positions = self.get_positions()
            
            total_balance = self.get_total_balance()
            available_balance = self.get_available_balance()
            
            # Calculate total unrealized PnL
            total_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
            
            # Position summary
            long_positions = [pos for pos in positions if pos.get('side') == 'LONG']
            short_positions = [pos for pos in positions if pos.get('side') == 'SHORT']
            
            return {
                'total_balance': total_balance,
                'available_balance': available_balance,
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_positions': len(positions),
                'long_positions': len(long_positions),
                'short_positions': len(short_positions),
                'balances': balances,
                'positions': positions,
                'last_sync': int(time.time() * 1000)
            }
            
        except Exception as e:
            self.log_error("account_summary", str(e))
            return {}
    
    def periodic_sync(self, trading_results: Dict[str, Any]) -> bool:
        """Perform periodic synchronization of account and positions"""
        try:
            success = True
            
            # Sync account balance
            if not self.sync_account_balance(trading_results):
                success = False
            
            # Sync positions
            if not self.sync_positions(trading_results):
                success = False
            
            return success
            
        except Exception as e:
            self.log_error("periodic_sync", str(e))
            return False
