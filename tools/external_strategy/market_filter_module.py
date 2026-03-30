#!/usr/bin/env python3
"""
Market Filter Module - External Profit Strategy MVP
Author: CANDY (data_validation + execution)
Constitution: NEXT-TRADE v1.2.1
Purpose: Global market state filtering based on portfolio metrics
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_RUNTIME = PROJECT_ROOT / "logs" / "runtime"
OUTPUT_DIR = Path(__file__).parent / "output"

# Filter thresholds (conservative defaults)
REALIZED_PNL_STOP_THRESHOLD = -50.0  # Stop if realized PnL < -50
DRAWDOWN_STOP_THRESHOLD = 25.0       # Stop if drawdown > 25%
EQUITY_MIN_THRESHOLD = 9900.0        # Stop if equity < 9900

def load_portfolio_metrics() -> Optional[Dict[str, Any]]:
    """Load portfolio metrics snapshot"""
    try:
        metrics_file = LOGS_RUNTIME / "portfolio_metrics_snapshot.json"
        if not metrics_file.exists():
            return None
        
        with open(metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading portfolio metrics: {e}")
        return None

def load_runtime_health() -> Optional[Dict[str, Any]]:
    """Load runtime health summary"""
    try:
        health_file = LOGS_RUNTIME / "runtime_health_summary.json"
        if not health_file.exists():
            return None
        
        with open(health_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading runtime health: {e}")
        return None

def evaluate_market_conditions(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate market conditions based on portfolio metrics"""
    
    realized_pnl = float(metrics.get('realized_pnl', 0))
    drawdown = float(metrics.get('drawdown', 0))
    equity = float(metrics.get('equity', 10000))
    
    # Filter decisions
    pnl_stop = realized_pnl < REALIZED_PNL_STOP_THRESHOLD
    drawdown_stop = drawdown > DRAWDOWN_STOP_THRESHOLD
    equity_stop = equity < EQUITY_MIN_THRESHOLD
    
    # Global decision
    global_allow = not (pnl_stop or drawdown_stop or equity_stop)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "global_allow": global_allow,
        "metrics": {
            "realized_pnl": realized_pnl,
            "drawdown": drawdown,
            "equity": equity
        },
        "filters": {
            "pnl_stop_triggered": pnl_stop,
            "drawdown_stop_triggered": drawdown_stop,
            "equity_stop_triggered": equity_stop
        },
        "thresholds": {
            "realized_pnl_stop": REALIZED_PNL_STOP_THRESHOLD,
            "drawdown_stop": DRAWDOWN_STOP_THRESHOLD,
            "equity_min": EQUITY_MIN_THRESHOLD
        }
    }

def save_market_filter_status(status: Dict[str, Any]) -> bool:
    """Save market filter status to output file"""
    try:
        output_file = OUTPUT_DIR / "market_filter_status.json"
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        
        print(f"Market filter status saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving market filter status: {e}")
        return False

def main():
    """Main execution function"""
    print("=== Market Filter Module ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Log directory: {LOGS_RUNTIME}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Load input data
    metrics = load_portfolio_metrics()
    health = load_runtime_health()
    
    if metrics is None:
        print("ERROR: Could not load portfolio metrics")
        sys.exit(1)
    
    print(f"Loaded portfolio metrics: equity={metrics.get('equity')}, pnl={metrics.get('realized_pnl')}")
    
    # Evaluate market conditions
    status = evaluate_market_conditions(metrics)
    
    # Add health data if available
    if health:
        status["runtime_health"] = health
    
    # Save results
    success = save_market_filter_status(status)
    
    if success:
        print(f"Market filter decision: {'ALLOW' if status['global_allow'] else 'BLOCK'}")
        print("Market filter module completed successfully")
        sys.exit(0)
    else:
        print("ERROR: Failed to save market filter status")
        sys.exit(1)

if __name__ == "__main__":
    main()
