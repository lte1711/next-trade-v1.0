#!/usr/bin/env python3
"""
Signal Quality Gate Module - External Profit Strategy MVP
Author: CANDY (data_validation + execution)
Constitution: NEXT-TRADE v1.2.1
Purpose: Filter low-quality signals based on strategy performance metrics
"""

import json
import sys
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_RUNTIME = PROJECT_ROOT / "logs" / "runtime"
STRATEGY_SIGNALS = LOGS_RUNTIME / "strategy_signals"
OUTPUT_DIR = Path(__file__).parent / "output"
FILTERED_SIGNALS_DIR = OUTPUT_DIR / "strategy_signals_filtered"

# Quality thresholds (conservative defaults)
WIN_RATE_MIN_THRESHOLD = 0.3        # Minimum 30% win rate
SYMBOL_PNL_MIN_THRESHOLD = -5.0      # Minimum -5 PnL per symbol
MAX_HOLD_TIME_THRESHOLD = 1800.0     # Maximum 30 minutes hold time
MIN_TRADES_THRESHOLD = 5             # Minimum 5 trades to evaluate

def load_strategy_performance() -> Optional[Dict[str, Any]]:
    """Load strategy performance data"""
    try:
        perf_file = LOGS_RUNTIME / "strategy_performance.json"
        if not perf_file.exists():
            return None
        
        with open(perf_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading strategy performance: {e}")
        return None

def load_strategy_signals() -> Dict[str, Dict[str, Any]]:
    """Load all strategy signal files"""
    signals = {}
    
    try:
        signal_files = glob.glob(str(STRATEGY_SIGNALS / "*.json"))
        
        for signal_file in signal_files:
            file_path = Path(signal_file)
            symbol_strategy = file_path.stem
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    signals[symbol_strategy] = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load signal file {signal_file}: {e}")
                continue
    
    except Exception as e:
        print(f"Error scanning strategy signals: {e}")
    
    return signals

def evaluate_signal_quality(performance: Dict[str, Any], signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate signal quality for each symbol-strategy combination"""
    
    decisions = {}
    filtered_signals = {}
    
    for symbol_strategy, signal_data in signals.items():
        # Extract symbol from signal filename
        parts = symbol_strategy.split('_')
        symbol = parts[0] if parts else symbol_strategy
        
        # Get performance data for this symbol
        symbol_perf = performance.get(symbol, {})
        
        # Extract metrics
        trades = int(symbol_perf.get('trades', 0))
        pnl = float(symbol_perf.get('pnl', 0))
        wins = int(symbol_perf.get('wins', 0))
        losses = int(symbol_perf.get('losses', 0))
        avg_hold_time = float(symbol_perf.get('avg_hold_time_sec', 0))
        
        # Calculate win rate
        win_rate = wins / trades if trades > 0 else 0
        
        # Quality checks
        sufficient_trades = trades >= MIN_TRADES_THRESHOLD
        good_win_rate = win_rate >= WIN_RATE_MIN_THRESHOLD
        acceptable_pnl = pnl >= SYMBOL_PNL_MIN_THRESHOLD
        reasonable_hold_time = avg_hold_time <= MAX_HOLD_TIME_THRESHOLD
        
        # Overall quality decision
        if trades < MIN_TRADES_THRESHOLD:
            # Not enough data - allow by default
            quality_allow = True
            reason = "insufficient_data"
        else:
            # Enough data - apply quality filters
            quality_allow = good_win_rate and acceptable_pnl and reasonable_hold_time
            reasons = []
            if not good_win_rate:
                reasons.append(f"low_win_rate_{win_rate:.3f}")
            if not acceptable_pnl:
                reasons.append(f"poor_pnl_{pnl:.2f}")
            if not reasonable_hold_time:
                reasons.append(f"excessive_hold_time_{avg_hold_time:.0f}s")
            reason = "blocked:" + ",".join(reasons) if reasons else "good_quality"
        
        # Record decision
        decisions[symbol_strategy] = {
            "allow": quality_allow,
            "reason": reason,
            "metrics": {
                "trades": trades,
                "pnl": pnl,
                "win_rate": win_rate,
                "avg_hold_time_sec": avg_hold_time
            },
            "thresholds": {
                "min_trades": MIN_TRADES_THRESHOLD,
                "min_win_rate": WIN_RATE_MIN_THRESHOLD,
                "min_symbol_pnl": SYMBOL_PNL_MIN_THRESHOLD,
                "max_hold_time": MAX_HOLD_TIME_THRESHOLD
            }
        }
        
        # Keep signal if allowed
        if quality_allow:
            filtered_signals[symbol_strategy] = signal_data
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "decisions": decisions,
        "summary": {
            "total_signals": len(signals),
            "allowed_signals": len(filtered_signals),
            "blocked_signals": len(signals) - len(filtered_signals)
        }
    }, filtered_signals

def save_filtered_signals(filtered_signals: Dict[str, Dict[str, Any]]) -> bool:
    """Save filtered signal files"""
    try:
        # Ensure output directory exists
        FILTERED_SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
        
        saved_count = 0
        for symbol_strategy, signal_data in filtered_signals.items():
            output_file = FILTERED_SIGNALS_DIR / f"{symbol_strategy}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(signal_data, f, indent=2, ensure_ascii=False)
            
            saved_count += 1
        
        print(f"Saved {saved_count} filtered signal files to: {FILTERED_SIGNALS_DIR}")
        return True
    except Exception as e:
        print(f"Error saving filtered signals: {e}")
        return False

def save_gate_decisions(decisions: Dict[str, Any]) -> bool:
    """Save gate decisions to log file"""
    try:
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        log_file = OUTPUT_DIR / "external_gate_decisions.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            # Write as JSONL format
            f.write(json.dumps(decisions, ensure_ascii=False) + "\n")
        
        print(f"Gate decisions logged to: {log_file}")
        return True
    except Exception as e:
        print(f"Error saving gate decisions: {e}")
        return False

def main():
    """Main execution function"""
    print("=== Signal Quality Gate Module ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Signals directory: {STRATEGY_SIGNALS}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Load input data
    performance = load_strategy_performance()
    signals = load_strategy_signals()
    
    if performance is None:
        print("ERROR: Could not load strategy performance data")
        sys.exit(1)
    
    if not signals:
        print("ERROR: No strategy signals found")
        sys.exit(1)
    
    print(f"Loaded performance data for {len(performance)} symbols")
    print(f"Loaded {len(signals)} strategy signals")
    
    # Evaluate signal quality
    decisions, filtered_signals = evaluate_signal_quality(performance, signals)
    
    # Save results
    signals_saved = save_filtered_signals(filtered_signals)
    decisions_logged = save_gate_decisions(decisions)
    
    if signals_saved and decisions_logged:
        summary = decisions["summary"]
        print(f"Signal quality gate completed:")
        print(f"  Total signals: {summary['total_signals']}")
        print(f"  Allowed: {summary['allowed_signals']}")
        print(f"  Blocked: {summary['blocked_signals']}")
        print("Signal quality gate module completed successfully")
        sys.exit(0)
    else:
        print("ERROR: Failed to save gate results")
        sys.exit(1)

if __name__ == "__main__":
    main()
