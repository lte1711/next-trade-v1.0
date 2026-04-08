#!/usr/bin/env python3
"""
Show Realtime Entry Symbols - Display current entry symbols in real-time
"""

import json
from datetime import datetime

def show_realtime_entry_symbols():
    """Show current entry symbols in real-time"""
    print('=' * 60)
    print('REALTIME ENTRY SYMBOLS')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Get current timestamp
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'Updated: {current_time}')
    
    # Check pending trades
    pending_trades = results.get('pending_trades', [])
    
    print(f'\n[PENDING TRADES] {len(pending_trades)} symbols waiting for entry:')
    
    if pending_trades:
        # Group by symbol to avoid duplicates
        symbol_trades = {}
        
        for trade in pending_trades:
            symbol = trade.get('symbol', 'Unknown')
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(trade)
        
        # Display unique symbols
        for i, (symbol, trades) in enumerate(symbol_trades.items(), 1):
            # Get the first trade for this symbol
            first_trade = trades[0]
            
            strategy = first_trade.get('strategy', 'Unknown')
            side = first_trade.get('side', 'Unknown')
            confidence = first_trade.get('signal_confidence', 0)
            reason = first_trade.get('signal_reason', 'No reason')
            
            # Get current price
            market_data = results.get('market_data', {})
            current_price = market_data.get(symbol, 'N/A')
            
            print(f'  {i}. {symbol}:')
            print(f'     - Side: {side}')
            print(f'     - Strategy: {strategy}')
            print(f'     - Confidence: {confidence:.2f}')
            print(f'     - Current Price: {current_price} USDT')
            print(f'     - Reason: {reason}')
            print(f'     - Duplicate entries: {len(trades)}')
            
            # Calculate position value
            if current_price != 'N/A' and trades:
                quantity = trades[0].get('quantity', 0)
                try:
                    price_float = float(current_price)
                    quantity_float = float(quantity)
                    position_value = price_float * quantity_float
                    print(f'     - Position Value: {position_value:.2f} USDT')
                except:
                    pass
            
            print()
    else:
        print('  No pending trades found')
    
    # Check active positions
    active_positions = results.get('active_positions', {})
    
    print(f'[ACTIVE POSITIONS] {len(active_positions)} symbols currently held:')
    
    if active_positions:
        for i, (symbol, position) in enumerate(active_positions.items(), 1):
            amount = position.get('amount', 0)
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            side = position.get('side', 'UNKNOWN')
            strategy = position.get('strategy', 'None')
            
            # Calculate PnL
            pnl = 0
            if entry_price and current_price and side == 'LONG':
                try:
                    entry_float = float(entry_price)
                    current_float = float(current_price)
                    pnl = (current_float - entry_float) * amount
                except:
                    pass
            
            print(f'  {i}. {symbol}:')
            print(f'     - Amount: {amount}')
            print(f'     - Side: {side}')
            print(f'     - Entry Price: {entry_price} USDT')
            print(f'     - Current Price: {current_price} USDT')
            print(f'     - PnL: {pnl:.2f} USDT')
            print(f'     - Strategy: {strategy}')
            print()
    else:
        print('  No active positions found')
    
    # Check strategy candidates
    print(f'[STRATEGY CANDIDATES] Potential entry symbols:')
    
    try:
        from core.strategy_registry import StrategyRegistry
        from core.market_data_service import MarketDataService
        
        sr = StrategyRegistry()
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        # Get available symbols
        symbols = mds.get_available_symbols()
        symbol_list = []
        for symbol_data in symbols:
            if isinstance(symbol_data, dict):
                symbol_list.append(symbol_data.get('symbol', ''))
            elif isinstance(symbol_data, str):
                symbol_list.append(symbol_data)
            else:
                symbol_list.append(str(symbol_data))
        
        # Get candidates for each strategy
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        for strategy_name in strategies:
            candidate_symbols = sr.select_preferred_symbols(strategy_name, symbol_list, 10)
            
            print(f'  {strategy_name.upper()} ({len(candidate_symbols)} candidates):')
            
            for i, symbol in enumerate(candidate_symbols[:5], 1):  # Show top 5
                # Get current price
                market_data = results.get('market_data', {})
                current_price = market_data.get(symbol, 'N/A')
                
                # Check if already in pending or active
                is_pending = symbol in [t.get('symbol') for t in pending_trades]
                is_active = symbol in active_positions
                
                status = []
                if is_pending:
                    status.append('PENDING')
                if is_active:
                    status.append('ACTIVE')
                
                status_str = f' ({", ".join(status)})' if status else ''
                
                print(f'    {i}. {symbol}: {current_price} USDT{status_str}')
            
            if len(candidate_symbols) > 5:
                print(f'    ... and {len(candidate_symbols) - 5} more')
            print()
    
    except Exception as e:
        print(f'  Error getting strategy candidates: {e}')
    
    # Summary
    print(f'[SUMMARY]')
    print(f'  - Pending Trades: {len(pending_trades)}')
    print(f'  - Active Positions: {len(active_positions)}')
    print(f'  - Max Positions: 5')
    print(f'  - Available Slots: {5 - len(active_positions)}')
    print(f'  - Can Accept New Entries: {len(active_positions) < 5}')
    
    # Check if there are any issues
    if len(pending_trades) > 0:
        print(f'\n[ISSUES]')
        print(f'  - Multiple pending trades for same symbol detected')
        print(f'  - This may indicate a duplicate entry issue')
    
    print('=' * 60)
    print('[RESULT] Realtime entry symbols display complete')
    print('=' * 60)

if __name__ == "__main__":
    show_realtime_entry_symbols()
