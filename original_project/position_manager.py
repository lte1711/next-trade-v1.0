# Position Manager Module
import time

class PositionManager:
    """
    Enhanced position manager with cooldown and advanced tracking.
    """
    
    def __init__(self):
        self.positions = {}  # symbol -> {side, size, entry_price, strategy, entry_ts}
        self.cooldowns = {}  # symbol -> last_exit_ts
    
    def has_open_position(self, symbol: str) -> bool:
        """Check if we have an active position in symbol."""
        pos = self.positions.get(symbol)
        return bool(pos and pos.get("qty", 0) > 0)
    
    def in_cooldown(self, symbol: str, now_ts: float, seconds: int = 1800) -> bool:
        """Check if symbol is in cooldown period."""
        last_ts = self.cooldowns.get(symbol, 0)
        return now_ts - last_ts < seconds
    
    def can_enter(self, symbol: str, now_ts: float) -> bool:
        """Check if we can enter a new position."""
        return (not self.has_open_position(symbol)) and (not self.in_cooldown(symbol, now_ts))
    
    def register_entry(self, symbol: str, side: str, qty: float, entry_price: float, strategy: str):
        """Register a new position entry."""
        self.positions[symbol] = {
            "side": side,
            "qty": qty,
            "entry_price": entry_price,
            "strategy": strategy,
            "entry_ts": time.time(),
        }
    
    def register_exit(self, symbol: str):
        """Register position exit and start cooldown."""
        if symbol in self.positions:
            del self.positions[symbol]
        self.cooldowns[symbol] = time.time()
    
    def update(self, symbol: str, side: str, size: float):
        """Legacy method - use register_entry instead."""
        self.register_entry(symbol, side, size, 0.0, "unknown")
    
    def close(self, symbol: str):
        """Legacy method - use register_exit instead."""
        self.register_exit(symbol)
    
    def get_position(self, symbol: str) -> dict:
        """Get position information."""
        return self.positions.get(symbol, {})
    
    def cleanup_old_positions(self, max_age_hours: int = 24):
        """Clean up old positions."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        expired = []
        for symbol, pos in self.positions.items():
            if current_time - pos.get("entry_ts", 0) > max_age_seconds:
                expired.append(symbol)
        
        for symbol in expired:
            del self.positions[symbol]
    
    def get_all_positions(self) -> dict:
        """Get all active positions."""
        return {k: v for k, v in self.positions.items() if v.get("qty", 0) > 0}
