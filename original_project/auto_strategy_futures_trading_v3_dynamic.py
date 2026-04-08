#!/usr/bin/env python3
"""
v3.2 Automated Futures Trading System - Clean Start
==================================================
Clean restart of v3.2 system with verified components.
"""

import sys
import os
import time
import json
import math
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import requests

# Add project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Mock API credentials for testing
os.environ['BINANCE_TESTNET_KEY'] = 'test_key'
os.environ['BINANCE_TESTNET_SECRET'] = 'test_secret'

# ==================== ENUMS & DATA STRUCTURES ====================

class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class MarketRegime(Enum):
    BULL = "BULL_MARKET"
    BEAR = "BEAR_MARKET"
    SIDEWAYS = "SIDEWAYS_MARKET"
    NEUTRAL = "NEUTRAL"

@dataclass
class MarketState:
    regime: MarketRegime
    volatility: float
    strength: float
    spread_pct: float
    trend_strength: float = 0.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class TradeSignal:
    strategy: str
    signal: Signal
    strength: float
    leverage: float
    stop_loss_pct: float
    take_profit_pct: float
    risk_per_trade: float
    reason: str
    timestamp: float = field(default_factory=time.time)

# ==================== CONFIGURATION SYSTEM ====================

class DynamicConfig:
    """Dynamic configuration system for v3.2"""
    
    def __init__(self):
        # v3.2: Balanced thresholds for trade generation
        self.SIGNAL_THRESHOLD = 0.58  # Standard threshold
        
        # Dynamic market thresholds
        self._market_thresholds = {}
        self._strategy_params = {}
        self._performance_history = []
        self._symbol_rankings = {}
        
        # Cache settings (enabled for real API)
        self.PRICE_CACHE_TTL = 30
        self.TICKER24_CACHE_TTL = 60
        self.KLINES_CACHE_TTL = 300
        self.REGIME_CACHE_TTL = 300
        
        # Risk management
        self.MAX_POSITION_EQUITY = 0.1  # 10% max per position
        
        # Initialize thresholds
        self._initialize_thresholds()
    
    def _initialize_thresholds(self):
        """Initialize market thresholds with responsive design"""
        # Base volatility (will be updated dynamically)
        volatility = 0.02
        
        # Dynamic thresholds based on volatility - v3.2 ultra-relaxed for signal generation
        self._market_thresholds = {
            'bull_threshold': max(0.0001, volatility * 0.05),  # Ultra-responsive
            'bear_threshold': min(-0.0001, -volatility * 0.05),  # Ultra-responsive
            'momentum_strong': max(0.0001, volatility * 0.01),  # Ultra-sensitive
            'mean_rev_max': max(0.0005, volatility * 0.05),  # Ultra-sensitive
            'vol_high_threshold': max(0.001, volatility * 0.1),  # Very sensitive
            'trend_strong': max(0.0001, volatility * 0.01),  # Ultra-sensitive
            'arb_spread_min': max(0.005, volatility * 1.0),  # Very low
        }
        
        # Store volatility for trend analysis
        self._volatility_history = [volatility]
    
    def get_threshold(self, name: str) -> float:
        """Get threshold value"""
        return self._market_thresholds.get(name, 0.0)
    
    def update_market_thresholds(self, volatility: float) -> None:
        """Update thresholds based on market volatility"""
        self._volatility_history.append(volatility)
        if len(self._volatility_history) > 100:
            self._volatility_history.pop(0)
        
        # Update thresholds with new volatility - ultra-relaxed
        self._market_thresholds['bull_threshold'] = max(0.0001, volatility * 0.05)
        self._market_thresholds['bear_threshold'] = min(-0.0001, -volatility * 0.05)
        self._market_thresholds['momentum_strong'] = max(0.0001, volatility * 0.01)
        self._market_thresholds['mean_rev_max'] = max(0.0005, volatility * 0.05)
        self._market_thresholds['vol_high_threshold'] = max(0.001, statistics.mean(self._volatility_history) * 0.1) if self._volatility_history else 0.001
        self._market_thresholds['trend_strong'] = max(0.0001, volatility * 0.01)
        self._market_thresholds['arb_spread_min'] = max(0.005, volatility * 1.0)
    
    def get_dynamic_strategy_params(self, strategy: str, market: MarketState) -> Dict:
        """Get strategy parameters based on market conditions"""
        base_params = {
            "risk_per_trade": self._calculate_dynamic_risk(),
            "stop_loss": self._calculate_stop_loss(market.volatility),
            "take_profit": self._calculate_take_profit(market.volatility),
        }
        return base_params
    
    def _calculate_dynamic_risk(self) -> float:
        """Calculate dynamic risk based on recent performance"""
        if not self._performance_history:
            return 0.02  # 2% base risk
        
        recent_performance = self._performance_history[-10:]  # Last 10 trades
        win_rate = sum(1 for p in recent_performance if p > 0) / len(recent_performance)
        
        base_risk = 0.02
        if win_rate > 0.6:  # Good performance - increase risk
            base_risk *= 1.2
        elif win_rate < 0.4:  # Poor performance - reduce risk
            base_risk *= 0.8
        
        return min(max(base_risk, 0.005), 0.02)  # Keep between 0.5% and 2%
    
    def update_symbol_rankings(self, ticker_data: Dict) -> None:
        """Update symbol rankings based on multiple factors"""
        rankings = {}
        
        for symbol, data in ticker_data.items():
            if isinstance(data, dict):
                volume = float(data.get('quoteVolume', 0))
                count = float(data.get('count', 0))
                price_change = abs(float(data.get('priceChangePercent', 0)))
                
                # Composite ranking score
                score = (volume * 0.4 + count * 0.3 + price_change * 0.3)
                rankings[symbol] = score
        
        # Normalize rankings
        if rankings:
            max_score = max(rankings.values())
            self._symbol_rankings = {s: score/max_score for s, score in rankings.items()}
    
    def get_symbol_ranking(self, symbol: str) -> float:
        """Get symbol ranking score"""
        return self._symbol_rankings.get(symbol, 0.5)
    
    def record_performance(self, pnl_pct: float) -> None:
        """Record trade performance"""
        self._performance_history.append(pnl_pct)
        if len(self._performance_history) > 100:
            self._performance_history.pop(0)
    
    def _calculate_stop_loss(self, volatility: float) -> float:
        """Calculate dynamic stop loss based on volatility"""
        return min(max(volatility * 2.0, 0.01), 0.05)  # 1% to 5%
    
    def _calculate_take_profit(self, volatility: float) -> float:
        """Calculate dynamic take profit based on volatility"""
        return min(max(volatility * 3.0, 0.02), 0.08)  # 2% to 8%

# Global configuration instance
CONFIG = DynamicConfig()

# ==================== PERFORMANCE TRACKING ====================

@dataclass
class PerformanceTracker:
    """Track strategy performance with accurate PnL calculation"""
    pnl_list: list = field(default_factory=list)
    wins: int = 0
    losses: int = 0

    def record(self, pnl_pct: float) -> None:
        """Record trade PnL"""
        self.pnl_list.append(pnl_pct)
        CONFIG.record_performance(pnl_pct)
        if pnl_pct > 0.0:
            self.wins += 1
        else:
            self.losses += 1

    def record_realized_pnl(self, pnl_pct: float) -> None:
        """Record realized PnL from position exit"""
        self.pnl_list.append(pnl_pct)
        CONFIG.record_performance(pnl_pct)
        if pnl_pct > 0.0:
            self.wins += 1
        else:
            self.losses += 1

    def summary(self) -> Dict:
        """Get performance summary"""
        total_trades = len(self.pnl_list)
        win_rate = self.wins / max(total_trades, 1)
        avg_pnl = statistics.mean(self.pnl_list) if self.pnl_list else 0.0
        total_pnl = sum(self.pnl_list)
        
        return {
            "total_trades": total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": win_rate,
            "avg_pnl": avg_pnl,
            "total_pnl": total_pnl
        }

# ==================== POSITION MANAGEMENT ====================

class PositionManager:
    """Manage position limits and cooldowns"""
    
    def __init__(self):
        self.max_open_positions = 3
        self.symbol_cooldown_sec = 1800  # 30 minutes
        self.loss_streak_pause = 3
        
        # Track recent performance
        self.recent_losses = {name: 0 for name in ["momentum", "mean_reversion", "volatility", "trend_following"]}
        
        # Track open positions
        self.open_positions = {}  # symbol -> position info
        
        # Track cooldowns
        self.symbol_cooldowns = {}  # symbol -> timestamp
    
    def can_enter(self, symbol: str, current_time: float) -> bool:
        """Check if we can enter a position"""
        # Check max positions
        if len(self.open_positions) >= self.max_open_positions:
            return False
        
        # Check symbol cooldown
        if symbol in self.symbol_cooldowns:
            if current_time - self.symbol_cooldowns[symbol] < self.symbol_cooldown_sec:
                return False
        
        # Check if already have position
        if symbol in self.open_positions:
            return False
        
        return True
    
    def register_entry(self, symbol: str, side: str, qty: float, price: float, strategy: str) -> None:
        """Register position entry"""
        self.open_positions[symbol] = {
            "side": side,
            "qty": qty,
            "entry_price": price,
            "strategy": strategy,
            "entry_time": time.time()
        }
        
        # Set cooldown
        self.symbol_cooldowns[symbol] = time.time()
    
    def register_exit(self, symbol: str) -> None:
        """Register position exit"""
        if symbol in self.open_positions:
            strategy = self.open_positions[symbol]["strategy"]
            
            # Update loss tracking
            # This would be updated based on actual PnL result
            # For now, just remove the position
            del self.open_positions[symbol]
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position info"""
        return self.open_positions.get(symbol)
    
    def has_open_position(self, symbol: str) -> bool:
        """Check if we have open position"""
        return symbol in self.open_positions

# ==================== MARKET ANALYSIS ====================

class MarketAnalyzer:
    """Analyze market conditions and generate signals"""
    
    def __init__(self, client):
        self.client = client
        self.REGIME_SYMBOL = "BTCUSDT"
        self._regime_cache: Optional[Tuple[float, MarketState]] = None
    
    def get_market_state(self) -> MarketState:
        """Get overall market state"""
        now = time.time()
        if self._regime_cache and now - self._regime_cache[0] < CONFIG.REGIME_CACHE_TTL:
            return self._regime_cache[1]
        
        state = self._analyze(self.REGIME_SYMBOL)
        self._regime_cache = (now, state)
        return state
    
    def _analyze(self, symbol: str) -> MarketState:
        """Analyze market for a symbol"""
        klines = self.client.get_klines(symbol, "1h", 24)
        if not klines:
            return MarketState(MarketRegime.SIDEWAYS, 0.020, 0.0, 0.001, timestamp=time.time())
        
        returns = [
            (float(k[4]) - float(k[1])) / float(k[1])
            for k in klines
            if float(k[1]) > 0
        ]
        
        if not returns:
            return MarketState(MarketRegime.SIDEWAYS, 0.020, 0.0, 0.001, timestamp=time.time())
        
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance)
        
        # Update CONFIG with new volatility
        CONFIG.update_market_thresholds(volatility)
        
        # Determine regime
        bull_threshold = CONFIG.get_threshold('bull_threshold')
        bear_threshold = CONFIG.get_threshold('bear_threshold')
        
        if avg_return > bull_threshold:
            regime = MarketRegime.BULL
        elif avg_return < bear_threshold:
            regime = MarketRegime.BEAR
        else:
            regime = MarketRegime.SIDEWAYS
        
        # Log regime calculation details for main market
        print(f"[REGIME_DEBUG] {symbol}: avg_return={avg_return:.6f}, bull_thr={bull_threshold:.6f}, bear_thr={bear_threshold:.6f}, regime={regime.value}")
        
        # Calculate spread
        spread_pct = self._calc_spread(symbol)
        
        return MarketState(
            regime=regime,
            volatility=round(volatility, 6),
            strength=round(avg_return, 6),
            spread_pct=spread_pct,
            timestamp=time.time(),
        )
    
    def get_symbol_market_state(self, symbol: str) -> MarketState:
        """Get market state for specific symbol"""
        klines = self.client.get_klines(symbol, "1h", 24)
        if not klines:
            return MarketState(MarketRegime.SIDEWAYS, 0.020, 0.0, 0.001, timestamp=time.time())
        
        returns = [
            (float(k[4]) - float(k[1])) / float(k[1])
            for k in klines
            if float(k[1]) > 0
        ]
        
        if not returns:
            return MarketState(MarketRegime.SIDEWAYS, 0.020, 0.0, 0.001, timestamp=time.time())
        
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance)
        
        # Determine regime
        bull_threshold = CONFIG.get_threshold('bull_threshold')
        bear_threshold = CONFIG.get_threshold('bear_threshold')
        
        if avg_return > bull_threshold:
            regime = MarketRegime.BULL
        elif avg_return < bear_threshold:
            regime = MarketRegime.BEAR
        else:
            regime = MarketRegime.SIDEWAYS
        
        # Calculate spread
        try:
            ticker = self.client.get_ticker_24h()
            if symbol in ticker:
                spread_pct = abs(float(ticker[symbol].get('priceChangePercent', 0))) / 100
            else:
                spread_pct = 0.001
        except Exception:
            spread_pct = 0.001
        
        return MarketState(
            regime=regime,
            volatility=round(volatility, 6),
            strength=round(avg_return, 6),
            spread_pct=spread_pct,
            timestamp=time.time(),
        )
    
    def _calc_spread(self, symbol: str) -> float:
        """Calculate spread percentage"""
        try:
            ticker = self.client.get_ticker_24h()
            if symbol in ticker:
                return abs(float(ticker[symbol].get('priceChangePercent', 0))) / 100
        except Exception:
            pass
        return 0.001

# ==================== STRATEGY ENGINE ====================

class StrategyEngine:
    """Generate trading signals"""
    
    MAX_LEVERAGE = 20.0
    MIN_LEVERAGE = 1.0
    
    def __init__(self):
        self._regime_cache: Optional[Tuple[float, MarketState]] = None
    
    def _calc_leverage(self, volatility: float) -> float:
        """Calculate leverage based on volatility"""
        raw = self.MAX_LEVERAGE * (0.01 / max(volatility, 0.001))
        return round(min(max(raw, self.MIN_LEVERAGE), self.MAX_LEVERAGE), 1)
    
    def _build(self, name: str, signal: Signal, strength: float,
               market: MarketState, reason: str) -> TradeSignal:
        """Build trade signal"""
        params = CONFIG.get_dynamic_strategy_params(name, market)
        
        return TradeSignal(
            strategy=name,
            signal=signal,
            strength=strength,
            leverage=self._calc_leverage(market.volatility),
            stop_loss_pct=params["stop_loss"],
            take_profit_pct=params["take_profit"],
            risk_per_trade=params["risk_per_trade"],
            reason=reason,
            timestamp=time.time(),
        )
    
    def momentum(self, market: MarketState) -> TradeSignal:
        """Momentum strategy"""
        if market.regime == MarketRegime.BULL and market.strength > CONFIG.get_threshold('momentum_strong'):
            return self._build("momentum", Signal.BUY, market.strength, market,
                              f"Bull momentum detected (strength={market.strength:.4f})")
        elif market.regime == MarketRegime.BEAR and market.strength < -CONFIG.get_threshold('momentum_strong'):
            return self._build("momentum", Signal.SELL, abs(market.strength), market,
                              f"Bear momentum detected (strength={market.strength:.4f})")
        
        return self._build("momentum", Signal.HOLD, 0.0, market,
                          f"No clear momentum (strength={market.strength:.4f})")
    
    def mean_reversion(self, market: MarketState) -> TradeSignal:
        """Mean reversion strategy - enhanced for sideways markets"""
        mean_rev_max = CONFIG.get_threshold('mean_rev_max')
        
        # Enhanced sideways market detection
        if (market.regime == MarketRegime.SIDEWAYS and 
            abs(market.strength) < mean_rev_max and 
            market.volatility < CONFIG.get_threshold('vol_high_threshold')):
            
            # Check for mean reversion opportunity
            if market.strength < -mean_rev_max * 0.5:  # Oversold
                return self._build("mean_reversion", Signal.BUY, abs(market.strength), market,
                                  f"Mean reversion buy opportunity (strength={market.strength:.4f})")
            elif market.strength > mean_rev_max * 0.5:  # Overbought
                return self._build("mean_reversion", Signal.SELL, market.strength, market,
                                  f"Mean reversion sell opportunity (strength={market.strength:.4f})")
        
        return self._build("mean_reversion", Signal.HOLD, 0.0, market,
                          f"No mean reversion signal (strength={market.strength:.4f})")
    
    def volatility(self, market: MarketState) -> TradeSignal:
        """Volatility breakout strategy"""
        vol_high = CONFIG.get_threshold('vol_high_threshold')
        
        if market.volatility > vol_high:
            if market.strength > 0:
                return self._build("volatility", Signal.BUY, market.volatility, market,
                                  f"Volatility breakout buy (vol={market.volatility:.4f})")
            else:
                return self._build("volatility", Signal.SELL, market.volatility, market,
                                  f"Volatility breakout sell (vol={market.volatility:.4f})")
        
        return self._build("volatility", Signal.HOLD, 0.0, market,
                          f"Low volatility (vol={market.volatility:.4f})")
    
    def trend_following(self, market: MarketState) -> TradeSignal:
        """Trend following strategy"""
        trend_strong = CONFIG.get_threshold('trend_strong')
        
        if market.regime == MarketRegime.BULL and market.strength > trend_strong:
            return self._build("trend_following", Signal.BUY, market.strength, market,
                              f"Bull trend following (strength={market.strength:.4f})")
        elif market.regime == MarketRegime.BEAR and market.strength < -trend_strong:
            return self._build("trend_following", Signal.SELL, abs(market.strength), market,
                              f"Bear trend following (strength={market.strength:.4f})")
        
        return self._build("trend_following", Signal.HOLD, 0.0, market,
                          f"No clear trend (strength={market.strength:.4f})")
    
    def run_all(self, market: MarketState) -> Dict[str, TradeSignal]:
        """Run all strategies"""
        signals = {
            "momentum": self.momentum(market),
            "mean_reversion": self.mean_reversion(market),
            "volatility": self.volatility(market),
            "trend_following": self.trend_following(market)
        }
        
        # Find best signal
        active_signals = [s for s in signals.values() if s.signal != Signal.HOLD]
        
        if not active_signals:
            return signals
        
        # Vote for best signal
        buy_signals = [s for s in active_signals if s.signal == Signal.BUY]
        sell_signals = [s for s in active_signals if s.signal == Signal.SELL]
        
        buy_score = sum(s.strength for s in buy_signals)
        sell_score = sum(s.strength for s in sell_signals)
        total = buy_score + sell_score
        
        if buy_score > sell_score and buy_score / total >= CONFIG.SIGNAL_THRESHOLD:
            best = max(buy_signals, key=lambda s: s.strength)
            return {name: best for name, sig in signals.items()}
        elif sell_score > buy_score and sell_score / total >= CONFIG.SIGNAL_THRESHOLD:
            best = max(sell_signals, key=lambda s: s.strength)
            return {name: best for name, sig in signals.items()}
        
        # No consensus
        best = max(active_signals, key=lambda s: s.strength)
        return {name: best for name, sig in signals.items()}

# ==================== SYMBOL SELECTION ====================

class SymbolSelector:
    """Select best symbols for trading"""
    
    def __init__(self, client):
        self.client = client
    
    def select_best_symbol_for_strategy(self, strategy: str, candidates: List[str], 
                                     analyzer: MarketAnalyzer, engine: StrategyEngine) -> Tuple[str, TradeSignal, float]:
        """Select best symbol for a strategy"""
        best_symbol = None
        best_signal = None
        best_score = 0.0
        
        for symbol in candidates:
            # Get market state for this symbol
            market = analyzer.get_symbol_market_state(symbol)
            
            # Get strategy signal for this symbol
            if strategy == "momentum":
                signal = engine.momentum(market)
            elif strategy == "mean_reversion":
                signal = engine.mean_reversion(market)
            elif strategy == "volatility":
                signal = engine.volatility(market)
            elif strategy == "trend_following":
                signal = engine.trend_following(market)
            else:
                continue
            
            # Log signal generation details
            print(f"[SIGNAL] {strategy} {symbol}: {signal.signal.value} | strength={signal.strength:.3f} | regime={market.regime.value} | strength={market.strength:.6f}")
            
            # Skip HOLD signals
            if signal.signal == Signal.HOLD:
                continue
            
            # Calculate score
            score = self._calculate_symbol_score(symbol, signal, market)
            
            # Log score calculation details
            print(f"[SCORE] {strategy} {symbol}: score={score:.3f} | signal={signal.signal.value} | ENTRY_SCORE_MIN=0.100")
            
            # Update best
            if score > best_score and score >= 0.10:  # Ultra-relaxed for testing
                best_symbol = symbol
                best_signal = signal
                best_score = score
        
        return best_symbol, best_signal, best_score
    
    def _calculate_symbol_score(self, symbol: str, signal: TradeSignal, market: MarketState) -> float:
        """Calculate symbol score"""
        # Base score from signal strength
        score = signal.strength * 0.4
        
        # Add trend alignment bonus
        if (signal.signal == Signal.BUY and market.regime == MarketRegime.BULL) or \
           (signal.signal == Signal.SELL and market.regime == MarketRegime.BEAR):
            score += 0.2
        
        # Add spread quality
        if market.spread_pct < 0.002:  # Good spread
            score += 0.1
        elif market.spread_pct > 0.01:  # Bad spread
            score -= 0.1
        
        # Add liquidity bonus
        liquidity_bonus = CONFIG.get_symbol_ranking(symbol) * 0.2
        score += liquidity_bonus
        
        # Add volatility quality
        if 0.01 < market.volatility < 0.05:  # Good volatility
            score += 0.1
        elif market.volatility > 0.1:  # Too volatile
            score -= 0.1
        
        return min(max(score, 0.0), 1.0)

# ==================== ORDER EXECUTION ====================

class OrderExecutor:
    """Execute trading orders"""
    
    def __init__(self, client):
        self.client = client
    
    def execute(self, symbol: str, signal: TradeSignal, total_capital: float) -> Optional[Dict]:
        """Execute trading signal"""
        try:
            # Get current price
            current_price = self.client.get_price(symbol)
            
            # Calculate position size
            dollar_position = min(
                total_capital * signal.risk_per_trade * signal.leverage,
                total_capital * CONFIG.MAX_POSITION_EQUITY,
            )
            raw_qty = dollar_position / current_price
            
            # Get symbol info for precision
            info = self.client.get_symbol_info(symbol)
            if not info:
                return None
            
            # Apply quantity precision
            qty_precision = info.get('quantityPrecision', 4)
            qty = round(raw_qty, qty_precision)
            
            # Submit order
            result = self.client.submit_order(symbol, signal.signal.value, qty)
            
            if result:
                # Submit protective orders
                entry_price = float(result.get('avgPrice', current_price))
                
                # Validate entry price
                if entry_price <= 0:
                    print(f"[ERROR] Invalid entry price: {entry_price} for {symbol}")
                    return
                
                # Stop loss
                if signal.signal == Signal.BUY:
                    stop_price = entry_price * (1 - signal.stop_loss_pct)
                else:
                    stop_price = entry_price * (1 + signal.stop_loss_pct)
                
                # Validate stop price
                if stop_price <= 0:
                    print(f"[ERROR] Invalid stop price: {stop_price} for {symbol}")
                    return
                
                self.client.submit_stop_market(symbol, signal.signal.value, qty, stop_price)
                
                # Take profit
                if signal.signal == Signal.BUY:
                    tp_price = entry_price * (1 + signal.take_profit_pct)
                else:
                    tp_price = entry_price * (1 - signal.take_profit_pct)
                
                # Validate take profit price
                if tp_price <= 0:
                    print(f"[ERROR] Invalid take profit price: {tp_price} for {symbol}")
                    return
                
                self.client.submit_take_profit_limit(symbol, signal.signal.value, qty, tp_price)
                
                return result
            
        except Exception as e:
            print(f"[ERROR] Order execution failed: {e}")
        
        return None

# ==================== MAIN TRADING SYSTEM ====================

class AutoStrategyFuturesTrading:
    """Main automated trading system"""
    
    def __init__(self, testnet: bool = True, duration_hours: int = 24):
        self.testnet = testnet
        self.duration_hours = duration_hours
        
        # Initialize components
        self.client = BinanceClient(testnet=testnet)
        self.analyzer = MarketAnalyzer(self.client)
        self.engine = StrategyEngine()
        self.selector = SymbolSelector(self.client)
        self.executor = OrderExecutor(self.client)
        self.position_manager = PositionManager()
        
        # Performance tracking
        self.trackers: Dict[str, PerformanceTracker] = {
            name: PerformanceTracker() for name in ["momentum", "mean_reversion", "volatility", "trend_following"]
        }
        
        # Results tracking
        self.results: Dict = {
            "meta": {
                "start_time": datetime.now().isoformat(),
                "end_time": "N/A",
                "duration_hours": duration_hours,
                "testnet": testnet
            },
            "trades": [],
            "performance": {},
            "summary": {}
        }
        
        # v3.2: Minimum trade guarantee to prevent paralysis
        self.last_trade_time = time.time()  # Initialize to current time to avoid massive time calculation
        self.no_trade_timeout = 1200  # 20 minutes without trades
        
        # Track open positions for realized PnL calculation
        self.open_positions = {}  # symbol -> {entry_price, entry_time, strategy, side}
    
    def run(self):
        """Main trading loop"""
        print(f"[START] Automated Strategy Futures Trading v3.2 (Clean Restart)")
        print("=" * 70)
        
        # Initialize
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=self.duration_hours)
        
        print(f"[INIT] Starting system initialization...")
        
        # Get valid symbols
        self.valid_symbols = self.client.get_valid_symbols()
        print(f"[INIT] Tradable symbols: {len(self.valid_symbols)}")
        
        # Get initial prices
        self.current_prices = self.client.get_all_prices()
        print(f"[INIT] Prices loaded: {len(self.current_prices)} symbols")
        
        # Get account balance
        self.total_capital = self.client.get_balance()
        print(f"[INIT] Account equity: ${self.total_capital:,.2f}")
        
        print(f"[INIT] Complete | equity=${self.total_capital:,.2f} | end={self.end_time}")
        
        # Main trading loop
        trade_count = 0
        error_count = 0
        
        while datetime.now() < self.end_time:
            try:
                # Update prices
                self.current_prices = self.client.get_all_prices()
                
                # Update symbol rankings
                tickers = self.client.get_ticker_24h()
                CONFIG.update_symbol_rankings(tickers)
                
                # Get market state
                market = self.analyzer.get_market_state()
                signals = self.engine.run_all(market)
                
                # Try to execute trades
                new_trades_this_loop = 0
                
                for name, sig in signals.items():
                    if sig.signal == Signal.HOLD:
                        continue
                    
                    # Get candidates for this strategy
                    batch_size = 4
                    start_idx = (list(signals.keys()).index(name) * batch_size) % len(self.valid_symbols)
                    batch = self.valid_symbols[start_idx:start_idx + batch_size]
                    
                    # Select best symbol for strategy
                    symbol, best_signal, score = self.selector.select_best_symbol_for_strategy(
                        name, batch, self.analyzer, self.engine
                    )
                    
                    # v3.2: Adaptive threshold relaxation for minimum trade guarantee
                    current_time = time.time()
                    time_since_last_trade = current_time - self.last_trade_time
                    
                    # Apply relaxed thresholds if no trades for too long
                    if time_since_last_trade > self.no_trade_timeout:
                        relaxed_score_min = 0.10  # Ultra-relaxed
                        relaxed_strength_min = 0.001  # Ultra-relaxed
                        print(f"[ADAPTIVE] Ultra-relaxed thresholds - no trades for {time_since_last_trade/60:.1f}min")
                    else:
                        relaxed_score_min = 0.10  # Ultra-relaxed
                        relaxed_strength_min = 0.001  # Ultra-relaxed
                    
                    # Check if individual symbol signal is valid
                    if not symbol or score < relaxed_score_min:
                        print(f"[BLOCK] {name} {symbol} | reason=entry_score_low | value={score:.3f} | min={relaxed_score_min:.3f}")
                        continue
                    
                    # Check individual signal strength
                    if best_signal.strength < relaxed_strength_min:
                        print(f"[BLOCK] {name} {symbol} | reason=signal_strength_low | value={best_signal.strength:.3f} | min={relaxed_strength_min:.3f}")
                        continue
                    
                    # Execute trade
                    result = self.executor.execute(symbol, best_signal, self.total_capital)
                    
                    if result:
                        new_trades_this_loop += 1
                        trade_count += 1
                        self.last_trade_time = time.time()  # v3.2: Update last trade time
                        
                        # Register position
                        entry_price = float(result.get('avgPrice', 0))
                        self.position_manager.register_entry(
                            symbol, best_signal.signal.value, 
                            float(result.get('executedQty', 0)),
                            entry_price,
                            name
                        )
                        
                        # Track position for realized PnL calculation with side field
                        self.open_positions[symbol] = {
                            "side": best_signal.signal.value,  # "BUY" or "SELL"
                            "qty": float(result.get('executedQty', 0)),
                            "entry_price": entry_price,
                            "strategy": name,
                            "entry_ts": time.time(),
                            "stop_loss_pct": best_signal.stop_loss_pct,
                            "take_profit_pct": best_signal.take_profit_pct,
                        }
                        
                        self.results["trades"].append({
                            "time": datetime.now().isoformat(),
                            "strategy": name,
                            "symbol": symbol,
                            "signal": best_signal.signal.value,
                            "leverage": best_signal.leverage,
                            "stop_loss": best_signal.stop_loss_pct,
                            "take_profit": best_signal.take_profit_pct,
                            "entry_price": entry_price,
                            "qty": result.get('executedQty', 0),
                            "pnl_pct": 0.0  # Will be updated on exit
                        })
                        
                        print(f"[TRADE] {name} | {symbol} | {best_signal.signal.value} | "
                              f"score={score:.3f} | strength={best_signal.strength:.3f}")
                
                # Monitor position exits
                self._monitor_position_exits()
                
                # Print progress
                progress = (datetime.now() - self.start_time).total_seconds() / 3600 / self.duration_hours * 100
                remaining = self.end_time - datetime.now()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Progress={progress:.1f}%  "
                      f"Remaining={remaining}  Equity=${self.total_capital:,.2f}")
                print(f"  Regime={market.regime.value}  Vol={market.volatility:.3%}  "
                      f"Strength={market.strength:+.4f}  Spread={market.spread_pct:+.3%}")
                print(f"  Dynamic thresholds: Bull={CONFIG.get_threshold('bull_threshold'):.3f} "
                      f"Bear={CONFIG.get_threshold('bear_threshold'):.3f} "
                      f"Arb={CONFIG.get_threshold('arb_spread_min'):.1%}")
                print(f"  Trades={trade_count}  Errors={error_count}")
                print("=" * 70)
                
                # Sleep
                time.sleep(10)
                
            except KeyboardInterrupt:
                print(f"\n[STOP] User interrupt at {datetime.now()}")
                break
            except Exception as e:
                print(f"[ERROR] Main loop error: {e}")
                error_count += 1
                time.sleep(10)
        
        self._save_results(trade_count, error_count)
    
    def _monitor_position_exits(self):
        """Monitor open positions and track unrealized PnL (no realized recording without actual exit)"""
        try:
            current_prices = self.client.get_all_prices()
            
            for symbol, pos in list(self.open_positions.items()):
                if symbol not in current_prices:
                    continue
                    
                current_price = current_prices[symbol]
                entry_price = pos["entry_price"]
                strategy_name = pos["strategy"]
                side = pos["side"]
                
                if strategy_name not in self.trackers:
                    continue
                
                # Calculate unrealized PnL (for monitoring only)
                unrealized_pnl_pct = self._calculate_pnl_pct(side, entry_price, current_price)
                
                # Update position with unrealized PnL data (no tracker recording)
                pos["unrealized_pnl_pct"] = unrealized_pnl_pct
                pos["last_mark_price"] = current_price
                pos["last_check_ts"] = time.time()
                
                # Print unrealized PnL for monitoring
                hold_duration = time.time() - pos["entry_ts"]
                print(f"[MONITOR] {strategy_name} | {symbol} | Unrealized PnL: {unrealized_pnl_pct:+.4f} | Duration: {hold_duration:.0f}s")
                
        except Exception as e:
            print(f"[ERROR] Position monitoring error: {e}")
    
    def _finalize_closed_position(self, symbol: str, exit_price: float, exit_reason: str):
        """Finalize a closed position and record realized PnL (only called on actual exit)"""
        position = self.open_positions.get(symbol)
        if not position:
            return

        side = position["side"]
        entry_price = position["entry_price"]
        strategy = position["strategy"]

        # Calculate realized PnL using side-based calculation
        pnl_pct = self._calculate_pnl_pct(side, entry_price, exit_price)
        
        # Record realized PnL in tracker
        self.trackers[strategy].record_realized_pnl(pnl_pct)

        # Update trade results with realized PnL
        for trade in self.results["trades"]:
            if trade["symbol"] == symbol and trade["pnl_pct"] == 0.0:
                trade["pnl_pct"] = pnl_pct
                trade["exit_time"] = datetime.now().isoformat()
                trade["exit_reason"] = exit_reason
                break
        
        # Add to closed trades record
        if "closed_trades" not in self.results:
            self.results["closed_trades"] = []
            
        self.results["closed_trades"].append({
            "symbol": symbol,
            "strategy": strategy,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pct": pnl_pct,
            "exit_reason": exit_reason,
            "entry_ts": position.get("entry_ts"),
            "exit_ts": time.time(),
        })

        # Remove from open positions and register exit
        self.open_positions.pop(symbol, None)
        self.position_manager.register_exit(symbol)
        
        print(f"[REALIZED] {strategy} | {symbol} | Realized PnL: {pnl_pct:+.4f} | Reason: {exit_reason}")
    
    def _calculate_pnl_pct(self, side: str, entry_price: float, current_price: float) -> float:
        """Calculate PnL percentage based on position side"""
        if entry_price == 0:
            return 0.0
        if side == "BUY":
            return (current_price - entry_price) / entry_price
        elif side == "SELL":
            return (entry_price - current_price) / entry_price
        return 0.0
    
    def _save_results(self, trade_count: int, error_count: int) -> None:
        """Save trading results"""
        total = trade_count + error_count
        success = round(trade_count / max(total, 1) * 100, 1)

        self.results["summary"] = {
            "end_time": datetime.now().isoformat(),
            "total_trades": trade_count,
            "total_errors": error_count,
            "success_rate": success,
            "duration_hours": self.duration_hours
        }
        
        # Performance summaries
        self.results["performance"] = {
            name: tracker.summary() for name, tracker in self.trackers.items()
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"v3_2_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n[RESULTS] Saved to {filename}")
        self._print_summary()
    
    def _print_summary(self):
        """Print trading summary"""
        print("\n" + "=" * 70)
        print("[RESULTS] Trading Summary")
        print("=" * 70)
        
        summary = self.results["summary"]
        print(f"Duration: {summary['duration_hours']} hours")
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Success Rate: {summary['success_rate']}%")
        
        print("\n[PERFORMANCE] Strategy Performance:")
        for name, perf in self.results["performance"].items():
            print(f"  {name}:")
            print(f"    Trades: {perf['total_trades']}")
            print(f"    Win Rate: {perf['win_rate']:.2%}")
            print(f"    Total PnL: {perf['total_pnl']:+.4f}")
        
        print("=" * 70)

# ==================== BINANCE CLIENT ====================

class BinanceClient:
    """Binance futures client with caching"""
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        # API credentials - read from config.json
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.api_key = config['binance']['testnet']['api_key']
                self.api_secret = config['binance']['testnet']['api_secret']
        except Exception as e:
            print(f"[ERROR] Failed to load config.json: {e}")
            self.api_key = ''
            self.api_secret = ''
        
        # Caching
        self._price_cache = {}
        self._ticker24_cache = None
        self._klines_cache = {}
        self._symbol_cache = {}
        
        # Test mode - use real API if credentials available
        if not self.api_key or not self.api_secret:
            self._mock_mode = True
            print("[MODE] Using MOCK mode - no API credentials")
        else:
            self._mock_mode = False
            print("[MODE] Using REAL testnet API")
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get all symbol prices"""
        if self._mock_mode:
            return self._mock_get_all_prices()
        
        try:
            now = time.time()
            cached = self._price_cache.get('all')
            if cached and now - cached[0] < CONFIG.PRICE_CACHE_TTL:
                return cached[1]
            
            r = requests.get(f"{self.base_url}/fapi/v1/ticker/price", timeout=10)
            r.raise_for_status()
            
            now = time.time()
            prices = {}
            for item in r.json():
                sym = item["symbol"]
                prices[sym] = float(item["price"])
            
            self._price_cache['all'] = (now, prices)
            return prices
            
        except Exception as e:
            print(f"[ERROR] Failed to get prices: {e}")
            return self._mock_get_all_prices()
    
    def _mock_get_all_prices(self) -> Dict[str, float]:
        """Mock price data for testing"""
        return {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "BNBUSDT": 600.0,
            "SOLUSDT": 150.0,
            "XRPUSDT": 0.5,
            "ADAUSDT": 0.4,
            "DOGEUSDT": 0.08,
            "AVAXUSDT": 35.0,
            "LINKUSDT": 15.0,
            "DOTUSDT": 7.0,
            "LTCUSDT": 70.0,
            "BCHUSDT": 250.0,
            "MATICUSDT": 0.9,
            "ATOMUSDT": 10.0,
            "UNIUSDT": 8.0,
            "ETCUSDT": 3.0
        }
    
    def get_price(self, symbol: str) -> float:
        """Get price for a symbol"""
        prices = self.get_all_prices()
        return prices.get(symbol, 0.0)
    
    def get_ticker_24h(self) -> Dict[str, Dict]:
        """Get 24h ticker data"""
        if self._mock_mode:
            return self._mock_get_ticker_24h()
        
        try:
            now = time.time()
            if self._ticker24_cache and now - self._ticker24_cache[0] < CONFIG.TICKER24_CACHE_TTL:
                return self._ticker24_cache[1]
            
            r = requests.get(f"{self.base_url}/fapi/v1/ticker/24hr", timeout=10)
            r.raise_for_status()
            
            now = time.time()
            tickers = {}
            for item in r.json():
                sym = item["symbol"]
                tickers[sym] = item
            
            self._ticker24_cache = (now, tickers)
            return tickers
            
        except Exception as e:
            print(f"[ERROR] Failed to get tickers: {e}")
            return self._mock_get_ticker_24h()
    
    def _mock_get_ticker_24h(self) -> Dict[str, Dict]:
        """Mock 24h ticker data with realistic variations"""
        import random
        random.seed(42)  # Consistent randomness
        
        ticker_data = {}
        for symbol in self._mock_get_all_prices().keys():
            # Create varied price changes
            price_change = random.uniform(-5.0, 5.0)  # -5% to +5%
            volume = random.uniform(500000, 5000000)  # Varied volumes
            count = random.uniform(5000, 50000)  # Varied trade counts
            
            ticker_data[symbol] = {
                "priceChangePercent": f"{price_change:.2f}",
                "quoteVolume": f"{volume:.0f}",
                "count": f"{count:.0f}"
            }
        
        return ticker_data
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> List:
        """Get kline data"""
        if self._mock_mode:
            return self._mock_get_klines(symbol, limit)
        
        try:
            key = f"{symbol}_{interval}_{limit}"
            now = time.time()
            cached = self._klines_cache.get(key)
            if cached and now - cached[0] < CONFIG.KLINES_CACHE_TTL:
                return cached[1]
            
            params = {"symbol": symbol, "interval": interval, "limit": limit}
            r = requests.get(f"{self.base_url}/fapi/v1/klines", params=params, timeout=10)
            r.raise_for_status()
            
            now = time.time()
            self._klines_cache[key] = (now, r.json())
            return r.json()
            
        except Exception as e:
            print(f"[ERROR] Failed to get klines: {e}")
            return self._mock_get_klines(symbol, limit)
    
    def _mock_get_klines(self, symbol: str, limit: int) -> List:
        """Mock kline data with enhanced volatility"""
        base_price = self._mock_get_all_prices().get(symbol, 100.0)
        klines = []
        
        # Create trending or volatile patterns
        import random
        random.seed(hash(symbol) % 1000)  # Consistent per symbol
        
        trend_direction = random.choice([-1, 1])  # -1 for bear, 1 for bull
        volatility_level = random.uniform(0.01, 0.05)  # 1% to 5% volatility
        
        current_price = base_price
        
        for i in range(limit):
            # Add trend and volatility
            trend_change = trend_direction * volatility_level * 0.3
            random_change = random.uniform(-volatility_level, volatility_level)
            
            price_change_pct = trend_change + random_change
            current_price = current_price * (1 + price_change_pct)
            
            # Create OHLC
            open_price = current_price
            high_price = open_price * (1 + abs(random_change) * 0.5)
            low_price = open_price * (1 - abs(random_change) * 0.5)
            close_price = open_price * (1 + random_change * 0.3)
            
            klines.append([
                f"{open_price:.6f}",  # Open
                f"{high_price:.6f}",  # High
                f"{low_price:.6f}",  # Low
                f"{close_price:.6f}",  # Close
                "1000000",  # Volume
                str(int(time.time() - (limit - i) * 3600) * 1000)  # Close time
            ])
        
        return klines
    
    def get_valid_symbols(self) -> List[str]:
        """Get valid trading symbols"""
        if self._mock_mode:
            return list(self._mock_get_all_prices().keys())
        
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            r.raise_for_status()
            
            symbols = []
            for item in r.json()["symbols"]:
                if item["status"] == "TRADING":
                    symbols.append(item["symbol"])
            
            return symbols
            
        except Exception as e:
            print(f"[ERROR] Failed to get symbols: {e}")
            return list(self._mock_get_all_prices().keys())
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information"""
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]
        
        if self._mock_mode:
            info = {
                'symbol': symbol,
                'pricePrecision': 4,
                'quantityPrecision': 4,
                'minQty': '0.001',
                'maxQty': '1000',
                'stepSize': '0.001',
                'minNotional': '5.0',
                'filters': [
                    {'filterType': 'PRICE_FILTER', 'minPrice': '0.0001', 'maxPrice': '1000000', 'tickSize': '0.0001'},
                    {'filterType': 'LOT_SIZE', 'minQty': '0.001', 'maxQty': '1000000', 'stepSize': '0.001'},
                    {'filterType': 'MIN_NOTIONAL', 'notional': '5.0'},
                ]
            }
        else:
            try:
                r = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
                r.raise_for_status()
                
                for item in r.json()["symbols"]:
                    if item["symbol"] == symbol:
                        info = item
                        break
                else:
                    info = None
                    
            except Exception as e:
                print(f"[ERROR] Failed to get symbol info: {e}")
                info = None
        
        self._symbol_cache[symbol] = info
        return info
    
    def get_balance(self) -> float:
        """Get account balance"""
        if self._mock_mode:
            return 10000.0
        
        try:
            params = self._signed_params({})
            headers = {"X-MBX-APIKEY": self.api_key}
            r = requests.get(f"{self.base_url}/fapi/v2/account", params=params, headers=headers, timeout=10)
            r.raise_for_status()
            
            for asset in r.json()["assets"]:
                if asset["asset"] == "USDT":
                    return float(asset["availableBalance"])
            
            return 0.0
            
        except Exception as e:
            print(f"[ERROR] Failed to get balance: {e}")
            return 10000.0
    
    def submit_order(self, symbol: str, side: str, qty: float) -> Optional[Dict]:
        """Submit order"""
        if self._mock_mode:
            return self._mock_submit_order(symbol, side, qty)
        
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": qty
            }
            
            signed_params = self._signed_params(params)
            headers = {"X-MBX-APIKEY": self.api_key}
            r = requests.post(f"{self.base_url}/fapi/v1/order", params=signed_params, headers=headers, timeout=10)
            r.raise_for_status()
            
            return r.json()
            
        except Exception as e:
            print(f"[ERROR] Failed to submit order: {e}")
            return None
    
    def _mock_submit_order(self, symbol: str, side: str, qty: float) -> Dict:
        """Mock order submission"""
        price = self.get_price(symbol)
        return {
            "avgPrice": str(price),
            "executedQty": str(qty),
            "symbol": symbol,
            "side": side
        }
    
    def submit_stop_market(self, symbol: str, side: str, qty: float, price: float) -> Optional[Dict]:
        """Submit stop market order"""
        if self._mock_mode:
            print(f"[MOCK] Stop market: {symbol} {side} {qty} @ {price}")
            return {"orderId": int(time.time())}
        
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": "STOP_MARKET",
                "quantity": qty,
                "stopPrice": price
            }
            
            signed_params = self._signed_params(params)
            headers = {"X-MBX-APIKEY": self.api_key}
            r = requests.post(f"{self.base_url}/fapi/v1/order", params=signed_params, headers=headers, timeout=10)
            r.raise_for_status()
            
            return r.json()
            
        except Exception as e:
            print(f"[ERROR] Failed to submit stop market: {e}")
            return None
    
    def submit_take_profit_limit(self, symbol: str, side: str, qty: float, price: float) -> Optional[Dict]:
        """Submit take profit limit order"""
        if self._mock_mode:
            print(f"[MOCK] Take profit: {symbol} {side} {qty} @ {price}")
            return {"orderId": int(time.time())}
        
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": "TAKE_PROFIT_LIMIT",
                "quantity": qty,
                "price": price,
                "timeInForce": "GTC"
            }
            
            signed_params = self._signed_params(params)
            headers = {"X-MBX-APIKEY": self.api_key}
            r = requests.post(f"{self.base_url}/fapi/v1/order", params=signed_params, headers=headers, timeout=10)
            r.raise_for_status()
            
            return r.json()
            
        except Exception as e:
            print(f"[ERROR] Failed to submit take profit: {e}")
            return None
    
    def _signed_params(self, extra: dict) -> dict:
        """Create signed parameters"""
        params = {**extra, "timestamp": self.server_time(), "recvWindow": 5000}
        params["signature"] = self._sign(params)
        return params
    
    def server_time(self) -> int:
        """Get server time"""
        if self._mock_mode:
            return int(time.time() * 1000)
        
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            r.raise_for_status()
            return r.json()["serverTime"]
        except Exception:
            return int(time.time() * 1000)
    
    def _sign(self, params: dict) -> str:
        """Sign parameters"""
        import hmac
        import hashlib
        import urllib.parse
        
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    print("[CONFIG] Dynamic configuration system initialized")
    
    # Create and run trading system
    trading_system = AutoStrategyFuturesTrading(testnet=True, duration_hours=1)
    trading_system.run()
