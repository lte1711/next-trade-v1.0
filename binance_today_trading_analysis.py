#!/usr/bin/env python3
"""
Binance Testnet Today's Trading Analysis - Complete trading evaluation
"""

import time
import json
import sys
import os
import subprocess
import requests
import hmac
import hashlib
from datetime import datetime, timedelta

def get_binance_account_info():
    """Get real-time account information from Binance Testnet"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        base_url = config['binance_testnet']['base_url']
        
        # Get server time
        server_time_url = f"{base_url}/fapi/v1/time"
        server_time_response = requests.get(server_time_url, timeout=5)
        server_time = server_time_response.json()['serverTime']
        
        # Create account request
        timestamp = server_time
        params = {
            "timestamp": timestamp,
            "recvWindow": 5000
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}/fapi/v2/account?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Error getting account info: {e}")
        return None

def get_today_orders():
    """Get all orders from today"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        base_url = config['binance_testnet']['base_url']
        
        # Get server time
        server_time_url = f"{base_url}/fapi/v1/time"
        server_time_response = requests.get(server_time_url, timeout=5)
        server_time = server_time_response.json()['serverTime']
        
        # Calculate today's start time (UTC midnight)
        now_utc = datetime.utcnow()
        today_start = datetime(now_utc.year, now_utc.month, now_utc.day)
        start_timestamp = int(today_start.timestamp() * 1000)
        
        # Create orders request
        timestamp = server_time
        params = {
            "timestamp": timestamp,
            "recvWindow": 5000,
            "startTime": start_timestamp,
            "limit": 1000  # Maximum limit
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}/fapi/v1/allOrders?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Orders API Error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Error getting today's orders: {e}")
        return None

def get_today_fills():
    """Get all fills from today"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        base_url = config['binance_testnet']['base_url']
        
        # Get server time
        server_time_url = f"{base_url}/fapi/v1/time"
        server_time_response = requests.get(server_time_url, timeout=5)
        server_time = server_time_response.json()['serverTime']
        
        # Calculate today's start time (UTC midnight)
        now_utc = datetime.utcnow()
        today_start = datetime(now_utc.year, now_utc.month, now_utc.day)
        start_timestamp = int(today_start.timestamp() * 1000)
        
        # Create fills request
        timestamp = server_time
        params = {
            "timestamp": timestamp,
            "recvWindow": 5000,
            "startTime": start_timestamp,
            "limit": 1000  # Maximum limit
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}/fapi/v1/userTrades?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Fills API Error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Error getting today's fills: {e}")
        return None

def analyze_today_trading():
    """Complete analysis of today's trading activity"""
    print('=' * 80)
    print('BINANCE TESTNET TODAY\'S TRADING ANALYSIS')
    print('=' * 80)
    
    current_time = datetime.now()
    print(f'Analysis Time: {current_time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Trading Date: {current_time.strftime("%Y-%m-%d")}')
    print('=' * 80)
    
    # 1. Get account information
    print('\n[1] ACCOUNT INFORMATION')
    account_info = get_binance_account_info()
    
    if account_info:
        try:
            total_wallet_balance = float(account_info.get('totalWalletBalance', 0))
            available_balance = float(account_info.get('availableBalance', 0))
            total_unrealized_pnl = float(account_info.get('totalUnrealizedPnl', 0))
            total_margin_balance = float(account_info.get('totalMarginBalance', 0))
            total_position_initial_margin = float(account_info.get('totalPositionInitialMargin', 0))
            
            print(f'  - Total Wallet Balance: ${total_wallet_balance:.2f}')
            print(f'  - Available Balance: ${available_balance:.2f}')
            print(f'  - Total Unrealized PnL: ${total_unrealized_pnl:+.4f}')
            print(f'  - Total Margin Balance: ${total_margin_balance:.2f}')
            print(f'  - Total Position Initial Margin: ${total_position_initial_margin:.2f}')
            
        except (KeyError, ValueError, TypeError) as e:
            print(f'  - Error parsing account info: {e}')
    else:
        print('  - Failed to get account information')
    
    # 2. Get today's orders
    print('\n[2] TODAY\'S ORDERS')
    today_orders = get_today_orders()
    
    if today_orders:
        print(f'  - Total Orders Today: {len(today_orders)}')
        
        # Analyze orders by symbol
        symbol_orders = {}
        order_types = {}
        order_sides = {}
        order_status = {}
        
        for order in today_orders:
            symbol = order['symbol']
            side = order['side']
            order_type = order['type']
            status = order['status']
            
            # Count by symbol
            if symbol not in symbol_orders:
                symbol_orders[symbol] = 0
            symbol_orders[symbol] += 1
            
            # Count by type
            if order_type not in order_types:
                order_types[order_type] = 0
            order_types[order_type] += 1
            
            # Count by side
            if side not in order_sides:
                order_sides[side] = 0
            order_sides[side] += 1
            
            # Count by status
            if status not in order_status:
                order_status[status] = 0
            order_status[status] += 1
        
        print(f'  - Orders by Symbol:')
        for symbol, count in sorted(symbol_orders.items()):
            print(f'    {symbol}: {count} orders')
        
        print(f'  - Orders by Type:')
        for order_type, count in order_types.items():
            print(f'    {order_type}: {count} orders')
        
        print(f'  - Orders by Side:')
        for side, count in order_sides.items():
            print(f'    {side}: {count} orders')
        
        print(f'  - Orders by Status:')
        for status, count in order_status.items():
            print(f'    {status}: {count} orders')
        
        # Show detailed orders
        print(f'\n  - Detailed Orders:')
        for i, order in enumerate(today_orders, 1):
            symbol = order['symbol']
            side = order['side']
            order_type = order['type']
            quantity = float(order['origQty'])
            filled_qty = float(order['executedQty'])
            price = float(order['price']) if order['price'] else 0
            status = order['status']
            order_time = datetime.fromtimestamp(int(order['time']) / 1000)
            
            print(f'    {i}. {symbol} {side} {order_type}')
            print(f'       Quantity: {quantity:.6f}')
            print(f'       Filled: {filled_qty:.6f}')
            print(f'       Price: ${price:.6f}' if price > 0 else '       Price: MARKET')
            print(f'       Status: {status}')
            print(f'       Time: {order_time.strftime("%H:%M:%S")}')
            print()
    else:
        print('  - No orders found for today')
    
    # 3. Get today's fills
    print('\n[3] TODAY\'S FILLS (EXECUTED TRADES)')
    today_fills = get_today_fills()
    
    if today_fills:
        print(f'  - Total Fills Today: {len(today_fills)}')
        
        # Analyze fills
        symbol_fills = {}
        side_fills = {}
        total_volume = 0
        total_commission = 0
        
        for fill in today_fills:
            symbol = fill['symbol']
            side = fill['side']
            quantity = float(fill['qty'])
            price = float(fill['price'])
            commission = float(fill['commission'])
            
            # Count by symbol
            if symbol not in symbol_fills:
                symbol_fills[symbol] = {'count': 0, 'volume': 0, 'commission': 0}
            symbol_fills[symbol]['count'] += 1
            symbol_fills[symbol]['volume'] += quantity * price
            symbol_fills[symbol]['commission'] += commission
            
            # Count by side
            if side not in side_fills:
                side_fills[side] = {'count': 0, 'volume': 0}
            side_fills[side]['count'] += 1
            side_fills[side]['volume'] += quantity * price
            
            # Totals
            total_volume += quantity * price
            total_commission += commission
        
        print(f'  - Fills by Symbol:')
        for symbol, data in sorted(symbol_fills.items()):
            print(f'    {symbol}: {data["count"]} fills, ${data["volume"]:.2f} volume, ${data["commission"]:.4f} commission')
        
        print(f'  - Fills by Side:')
        for side, data in side_fills.items():
            print(f'    {side}: {data["count"]} fills, ${data["volume"]:.2f} volume')
        
        print(f'  - Total Trading Volume: ${total_volume:.2f}')
        print(f'  - Total Commission: ${total_commission:.4f}')
        
        # Show detailed fills
        print(f'\n  - Detailed Fills:')
        for i, fill in enumerate(today_fills, 1):
            symbol = fill['symbol']
            side = fill['side']
            quantity = float(fill['qty'])
            price = float(fill['price'])
            commission = float(fill['commission'])
            commission_asset = fill['commissionAsset']
            fill_time = datetime.fromtimestamp(int(fill['time']) / 1000)
            
            print(f'    {i}. {symbol} {side}')
            print(f'       Quantity: {quantity:.6f}')
            print(f'       Price: ${price:.6f}')
            print(f'       Value: ${quantity * price:.4f}')
            print(f'       Commission: {commission:.6f} {commission_asset}')
            print(f'       Time: {fill_time.strftime("%H:%M:%S")}')
            print()
    else:
        print('  - No fills found for today')
    
    # 4. Local trading results comparison
    print('\n[4] LOCAL TRADING RESULTS COMPARISON')
    try:
        with open('trading_results.json', 'r') as f:
            local_results = json.load(f)
        
        local_active_positions = local_results.get('active_positions', {})
        local_closed_trades = local_results.get('closed_trades', [])
        local_pending_trades = local_results.get('pending_trades', [])
        
        print(f'  - Local Active Positions: {len(local_active_positions)}')
        print(f'  - Local Closed Trades: {len(local_closed_trades)}')
        print(f'  - Local Pending Trades: {len(local_pending_trades)}')
        
        # Show today's closed trades from local data
        today_local_trades = []
        today_start_local = datetime(current_time.year, current_time.month, current_time.day)
        today_timestamp = int(today_start_local.timestamp() * 1000)
        
        for trade in local_closed_trades:
            trade_time = trade.get('close_time', trade.get('time', 0))
            if trade_time and trade_time >= today_timestamp:
                today_local_trades.append(trade)
        
        print(f'  - Today\'s Local Closed Trades: {len(today_local_trades)}')
        
        if today_local_trades:
            print(f'  - Today\'s Local Trades Detail:')
            for i, trade in enumerate(today_local_trades, 1):
                symbol = trade.get('symbol', 'Unknown')
                side = trade.get('side', 'Unknown')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                pnl = trade.get('realized_pnl', 0)
                trade_time = datetime.fromtimestamp(int(trade.get('close_time', 0)) / 1000)
                
                print(f'    {i}. {symbol} {side}')
                print(f'       Quantity: {quantity:.6f}')
                print(f'       Price: ${price:.6f}')
                print(f'       PnL: ${pnl:+.4f}')
                print(f'       Time: {trade_time.strftime("%H:%M:%S")}')
                print()
        
    except Exception as e:
        print(f'  - Error reading local results: {e}')
    
    # 5. Performance analysis
    print('\n[5] PERFORMANCE ANALYSIS')
    
    if today_orders and today_fills:
        filled_orders = [order for order in today_orders if order['status'] == 'FILLED']
        fill_rate = len(filled_orders) / len(today_orders) * 100 if today_orders else 0
        
        print(f'  - Order Fill Rate: {fill_rate:.1f}%')
        print(f'  - Total Orders: {len(today_orders)}')
        print(f'  - Filled Orders: {len(filled_orders)}')
        print(f'  - Cancelled Orders: {len([o for o in today_orders if o["status"] == "CANCELLED"])}')
        
        if account_info:
            start_balance = 10000.0  # Assuming starting balance
            current_balance = float(account_info.get('totalWalletBalance', 0))
            daily_pnl = current_balance - start_balance
            daily_return = (daily_pnl / start_balance) * 100 if start_balance > 0 else 0
            
            print(f'  - Daily PnL: ${daily_pnl:+.2f}')
            print(f'  - Daily Return: {daily_return:+.2f}%')
    
    # 6. Trading summary
    print('\n[6] TRADING SUMMARY')
    
    summary = {
        'date': current_time.strftime('%Y-%m-%d'),
        'total_orders': len(today_orders) if today_orders else 0,
        'total_fills': len(today_fills) if today_fills else 0,
        'total_volume': sum([float(f['qty']) * float(f['price']) for f in today_fills]) if today_fills else 0,
        'total_commission': sum([float(f['commission']) for f in today_fills]) if today_fills else 0,
        'unique_symbols': len(set([o['symbol'] for o in today_orders])) if today_orders else 0,
        'buy_orders': len([o for o in today_orders if o['side'] == 'BUY']) if today_orders else 0,
        'sell_orders': len([o for o in today_orders if o['side'] == 'SELL']) if today_orders else 0,
    }
    
    print(f'  - Trading Date: {summary["date"]}')
    print(f'  - Total Orders: {summary["total_orders"]}')
    print(f'  - Total Fills: {summary["total_fills"]}')
    print(f'  - Total Volume: ${summary["total_volume"]:.2f}')
    print(f'  - Total Commission: ${summary["total_commission"]:.4f}')
    print(f'  - Unique Symbols: {summary["unique_symbols"]}')
    print(f'  - Buy Orders: {summary["buy_orders"]}')
    print(f'  - Sell Orders: {summary["sell_orders"]}')
    
    if account_info:
        current_balance = float(account_info.get('totalWalletBalance', 0))
        print(f'  - Current Balance: ${current_balance:.2f}')
    
    print('\n' + '=' * 80)
    print('TODAY\'S TRADING ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_today_trading()
