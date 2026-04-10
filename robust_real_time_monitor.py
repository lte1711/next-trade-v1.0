#!/usr/bin/env python3
"""
Robust Real-Time Binance Monitor - Robust version for continuous real-time monitoring
"""

import time
import json
import sys
import os
import subprocess
import requests
import hmac
import hashlib
from datetime import datetime

def get_binance_account_info():
    """Get real-time account information from Binance Testnet"""
    try:
        # Load configuration
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

def get_open_positions():
    """Get open positions from Binance Testnet"""
    try:
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        base_url = config['binance_testnet']['base_url']
        
        # Get server time
        server_time_url = f"{base_url}/fapi/v1/time"
        server_time_response = requests.get(server_time_url, timeout=5)
        server_time = server_time_response.json()['serverTime']
        
        # Create positions request
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
        
        url = f"{base_url}/fapi/v2/positionRisk?{query_string}&signature={signature}"
        headers = {"X-MBX-APIKEY": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            positions = response.json()
            # Filter only positions with non-zero size
            active_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
            return active_positions
        else:
            print(f"Positions API Error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Error getting positions: {e}")
        return None

def get_recent_orders():
    """Get recent orders from Binance Testnet"""
    try:
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        base_url = config['binance_testnet']['base_url']
        
        # Get server time
        server_time_url = f"{base_url}/fapi/v1/time"
        server_time_response = requests.get(server_time_url, timeout=5)
        server_time = server_time_response.json()['serverTime']
        
        # Create orders request
        timestamp = server_time
        params = {
            "timestamp": timestamp,
            "recvWindow": 5000,
            "limit": 10
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
        print(f"Error getting recent orders: {e}")
        return None

def robust_real_time_monitor():
    """Robust real-time Binance Testnet monitoring"""
    print('=' * 80)
    print('ROBUST REAL-TIME BINANCE TESTNET MONITOR')
    print('=' * 80)
    
    print(f'Monitor Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('Press Ctrl+C to stop monitoring')
    print('=' * 80)
    
    try:
        while True:
            current_time = datetime.now()
            
            print(f"\n{'='*60}")
            print(f"BINANCE TESTNET REAL-TIME MONITORING REPORT")
            print(f"{'='*60}")
            print(f"Report Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Exchange: Binance Testnet")
            print(f"API Status: Checking...")
            
            # 1. Account Information
            print(f"\n[1] ACCOUNT INFORMATION")
            account_info = get_binance_account_info()
            
            if account_info:
                # Handle account info with robust field access
                try:
                    total_wallet_balance = float(account_info.get('totalWalletBalance', 0))
                    available_balance = float(account_info.get('availableBalance', 0))
                    total_unrealized_pnl = float(account_info.get('totalUnrealizedPnl', 0))
                    total_margin_balance = float(account_info.get('totalMarginBalance', 0))
                    total_position_initial_margin = float(account_info.get('totalPositionInitialMargin', 0))
                    
                    print(f"  - Total Wallet Balance: ${total_wallet_balance:.2f}")
                    print(f"  - Available Balance: ${available_balance:.2f}")
                    print(f"  - Total Unrealized PnL: ${total_unrealized_pnl:+.4f}")
                    print(f"  - Total Margin Balance: ${total_margin_balance:.2f}")
                    print(f"  - Total Position Initial Margin: ${total_position_initial_margin:.2f}")
                    print(f"  - API Status: CONNECTED")
                    
                except (KeyError, ValueError, TypeError) as e:
                    print(f"  - API Status: CONNECTED (data parsing error)")
                    print(f"  - Available Fields: {list(account_info.keys())}")
                    print(f"  - Error: {e}")
            else:
                print(f"  - API Status: FAILED TO CONNECT")
                print(f"  - Error: Unable to fetch account information")
            
            # 2. Open Positions
            print(f"\n[2] OPEN POSITIONS")
            positions = get_open_positions()
            
            if positions:
                print(f"  - Total Active Positions: {len(positions)}")
                
                for pos in positions:
                    try:
                        symbol = pos['symbol']
                        side = 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT'
                        amount = abs(float(pos['positionAmt']))
                        entry_price = float(pos['entryPrice'])
                        mark_price = float(pos['markPrice'])
                        unrealized_pnl = float(pos['unRealizedProfit'])
                        
                        # Handle percentage field robustly
                        percentage = pos.get('percentage', '0.00')
                        if percentage != '0.00':
                            try:
                                percentage = float(percentage)
                                percentage_str = f"({percentage:+.2f}%)"
                            except (ValueError, TypeError):
                                percentage_str = "(N/A)"
                        else:
                            percentage_str = "(0.00%)"
                        
                        print(f"    - {symbol}: {side} {amount:.6f} @ {entry_price:.6f}")
                        print(f"      Mark Price: {mark_price:.6f}")
                        print(f"      Unrealized PnL: ${unrealized_pnl:+.4f} {percentage_str}")
                        
                    except (KeyError, ValueError, TypeError) as e:
                        print(f"    - Error parsing position: {e}")
                        print(f"    - Position data: {pos}")
            else:
                print(f"  - Total Active Positions: 0")
                print(f"  - Status: No open positions")
            
            # 3. Recent Orders
            print(f"\n[3] RECENT ORDERS")
            orders = get_recent_orders()
            
            if orders:
                print(f"  - Recent Orders: {len(orders)}")
                
                for order in orders[:5]:  # Show last 5 orders
                    try:
                        symbol = order['symbol']
                        side = order['side']
                        order_type = order['type']
                        quantity = float(order['origQty'])
                        filled_qty = float(order['executedQty'])
                        order_status = order['status']
                        order_time = datetime.fromtimestamp(int(order['time']) / 1000)
                        
                        print(f"    - {symbol}: {side} {order_type}")
                        print(f"      Quantity: {quantity:.6f}")
                        print(f"      Filled: {filled_qty:.6f}")
                        print(f"      Status: {order_status}")
                        print(f"      Time: {order_time.strftime('%H:%M:%S')}")
                        
                    except (KeyError, ValueError, TypeError) as e:
                        print(f"    - Error parsing order: {e}")
            else:
                print(f"  - Recent Orders: None")
                print(f"  - Status: No recent orders found")
            
            # 4. Local Trading Results
            print(f"\n[4] LOCAL TRADING RESULTS")
            try:
                with open('trading_results.json', 'r') as f:
                    local_results = json.load(f)
                
                local_active_positions = local_results.get('active_positions', {})
                local_closed_trades = local_results.get('closed_trades', [])
                local_pending_trades = local_results.get('pending_trades', [])
                
                print(f"  - Local Active Positions: {len(local_active_positions)}")
                print(f"  - Local Closed Trades: {len(local_closed_trades)}")
                print(f"  - Local Pending Trades: {len(local_pending_trades)}")
                
                # Show local active positions
                if local_active_positions:
                    print(f"  - Local Active Positions Detail:")
                    for symbol, position in local_active_positions.items():
                        side = position.get('side', 'UNKNOWN')
                        amount = position.get('amount', 0)
                        entry_price = position.get('entry_price', 0)
                        unrealized_pnl = position.get('unrealized_pnl', 0)
                        
                        print(f"    - {symbol}: {side} {amount:.6f} @ {entry_price:.6f} (PnL: {unrealized_pnl:+.4f})")
                
            except Exception as e:
                print(f"  - Error reading local results: {e}")
            
            # 5. System Status
            print(f"\n[5] SYSTEM STATUS")
            
            # Check if main runtime is running
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                      capture_output=True, text=True)
                
                if 'python.exe' in result.stdout:
                    python_lines = [line for line in result.stdout.split('\n') if 'python.exe' in line]
                    print(f"  - Python Processes: {len(python_lines)}")
                    
                    # Check for main runtime
                    main_runtime_found = False
                    for line in python_lines:
                        if 'main_runtime' in line.lower():
                            main_runtime_found = True
                            break
                    
                    if main_runtime_found:
                        print(f"  - Main Runtime: RUNNING")
                    else:
                        print(f"  - Main Runtime: NOT FOUND")
                else:
                    print(f"  - Python Processes: 0")
                    print(f"  - Main Runtime: NOT RUNNING")
            
            except Exception as e:
                print(f"  - Error checking system status: {e}")
            
            # 6. Market Status
            print(f"\n[6] MARKET STATUS")
            
            # Get server time
            try:
                server_time_url = "https://demo-fapi.binance.com/fapi/v1/time"
                server_time_response = requests.get(server_time_url, timeout=5)
                server_time = server_time_response.json()['serverTime']
                server_datetime = datetime.fromtimestamp(server_time / 1000)
                
                print(f"  - Server Time: {server_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  - Local Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  - Time Difference: {(current_time - server_datetime).total_seconds():.2f} seconds")
                print(f"  - Market Status: OPEN")
                
            except Exception as e:
                print(f"  - Error checking market status: {e}")
            
            # 7. Configuration Status
            print(f"\n[7] CONFIGURATION STATUS")
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                
                real_time_mode = config.get('real_time_mode', False)
                virtual_tests_disabled = config.get('all_virtual_tests_disabled', False)
                force_real_exchange = config.get('force_real_exchange', False)
                max_positions = config.get('trading_config', {}).get('max_open_positions', 0)
                
                print(f"  - Real-Time Mode: {real_time_mode}")
                print(f"  - Virtual Tests Disabled: {virtual_tests_disabled}")
                print(f"  - Force Real Exchange: {force_real_exchange}")
                print(f"  - Max Open Positions: {max_positions}")
                
            except Exception as e:
                print(f"  - Error reading configuration: {e}")
            
            # 8. Trading Summary
            print(f"\n[8] TRADING SUMMARY")
            try:
                if account_info and positions:
                    total_balance = float(account_info.get('totalWalletBalance', 0))
                    total_pnl = float(account_info.get('totalUnrealizedPnl', 0))
                    
                    print(f"  - Account Balance: ${total_balance:.2f}")
                    print(f"  - Total PnL: ${total_pnl:+.4f}")
                    print(f"  - Active Positions: {len(positions)}")
                    
                    if positions:
                        total_position_value = sum([abs(float(pos['positionAmt']) * float(pos['markPrice'])) for pos in positions])
                        print(f"  - Total Position Value: ${total_position_value:.2f}")
                        
                        # Calculate PnL percentage
                        if total_position_value > 0:
                            pnl_percentage = (total_pnl / total_position_value) * 100
                            print(f"  - PnL Percentage: {pnl_percentage:+.2f}%")
                    
                    # Performance indicator
                    if total_pnl > 0:
                        print(f"  - Performance: PROFITABLE")
                    elif total_pnl < 0:
                        print(f"  - Performance: LOSS")
                    else:
                        print(f"  - Performance: BREAKEVEN")
                
            except Exception as e:
                print(f"  - Error calculating trading summary: {e}")
            
            print(f"\n{'='*60}")
            print(f"NEXT UPDATE IN 30 SECONDS...")
            print(f"{'='*60}")
            
            # Wait for next update
            time.sleep(30)
    
    except KeyboardInterrupt:
        print(f"\n\nReal-time monitoring stopped by user")
        print(f"Stop Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"\nCritical error in monitoring: {e}")

if __name__ == "__main__":
    robust_real_time_monitor()
