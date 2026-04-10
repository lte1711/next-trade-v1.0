#!/usr/bin/env python3
"""
Position Cross Analysis - Check if SHORT positions can be crossed to LONG
"""

import json
import requests
import hmac
import hashlib
from datetime import datetime
import time

def get_binance_account_info():
    """Get account information from Binance"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        base_url = config['binance_testnet']['base_url']
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        
        # Get account info
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        
        url = f"{base_url}/fapi/v2/account"
        headers = {
            'X-MBX-APIKEY': api_key
        }
        params = {
            'timestamp': timestamp,
            'signature': signature
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting account info: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error getting account info: {e}")
        return None

def get_binance_positions():
    """Get current positions from Binance"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        base_url = config['binance_testnet']['base_url']
        api_key = config['binance_testnet']['api_key']
        api_secret = config['binance_testnet']['api_secret']
        
        # Get positions
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        
        url = f"{base_url}/fapi/v2/positionRisk"
        headers = {
            'X-MBX-APIKEY': api_key
        }
        params = {
            'timestamp': timestamp,
            'signature': signature
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            positions = response.json()
            # Filter only positions with non-zero size
            active_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
            return active_positions
        else:
            print(f"Error getting positions: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error getting positions: {e}")
        return None

def analyze_position_cross_feasibility():
    """Analyze feasibility of crossing SHORT positions to LONG"""
    print('=' * 80)
    print('POSITION CROSS ANALYSIS: SHORT → LONG')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # Get current account info
    print('\n[1] CURRENT ACCOUNT STATUS')
    
    account_info = get_binance_account_info()
    if not account_info:
        print('  - Error: Could not get account information')
        return
    
    total_wallet_balance = float(account_info.get('totalWalletBalance', 0))
    available_balance = float(account_info.get('availableBalance', 0))
    total_unrealized_pnl = float(account_info.get('totalUnrealizedPnl', 0))
    total_margin_balance = float(account_info.get('totalMarginBalance', 0))
    
    print(f'  - Total Wallet Balance: ${total_wallet_balance:.2f}')
    print(f'  - Available Balance: ${available_balance:.2f}')
    print(f'  - Total Unrealized PnL: ${total_unrealized_pnl:+.2f}')
    print(f'  - Total Margin Balance: ${total_margin_balance:.2f}')
    
    # Get current positions
    print('\n[2] CURRENT POSITIONS ANALYSIS')
    
    positions = get_binance_positions()
    if not positions:
        print('  - No active positions found')
        return
    
    print(f'  - Total Active Positions: {len(positions)}')
    
    short_positions = []
    long_positions = []
    
    for pos in positions:
        symbol = pos['symbol']
        position_amt = float(pos['positionAmt'])
        entry_price = float(pos['entryPrice'])
        mark_price = float(pos['markPrice'])
        unrealized_pnl = float(pos['unrealizedPnl'])
        
        position_info = {
            'symbol': symbol,
            'position_amt': position_amt,
            'entry_price': entry_price,
            'mark_price': mark_price,
            'unrealized_pnl': unrealized_pnl,
            'side': 'SHORT' if position_amt < 0 else 'LONG'
        }
        
        if position_amt < 0:
            short_positions.append(position_info)
        else:
            long_positions.append(position_info)
    
    print(f'  - SHORT Positions: {len(short_positions)}')
    print(f'  - LONG Positions: {len(long_positions)}')
    
    # Analyze each SHORT position for crossing possibility
    print('\n[3] SHORT POSITION CROSS ANALYSIS')
    
    crossing_analysis = []
    
    for pos in short_positions:
        symbol = pos['symbol']
        position_amt = abs(pos['position_amt'])
        entry_price = pos['entry_price']
        mark_price = pos['mark_price']
        unrealized_pnl = pos['unrealized_pnl']
        
        print(f'\n  [{symbol}] SHORT Position Analysis:')
        print(f'    - Position Size: {position_amt:,.0f}')
        print(f'    - Entry Price: ${entry_price:.6f}')
        print(f'    - Mark Price: ${mark_price:.6f}')
        print(f'    - Unrealized PnL: ${unrealized_pnl:+.4f}')
        
        # Calculate crossing requirements
        # To cross from SHORT to LONG:
        # 1. Close SHORT position (buy back)
        # 2. Open LONG position (buy)
        
        # Cost to close SHORT
        close_cost = position_amt * mark_price
        print(f'    - Cost to Close SHORT: ${close_cost:.2f}')
        
        # Cost to open LONG (same size)
        open_cost = position_amt * mark_price
        print(f'    - Cost to Open LONG: ${open_cost:.2f}')
        
        # Total cost for crossing
        total_cross_cost = close_cost + open_cost
        print(f'    - Total Cross Cost: ${total_cross_cost:.2f}')
        
        # Check if available balance is sufficient
        can_cross = available_balance >= total_cross_cost
        print(f'    - Available Balance: ${available_balance:.2f}')
        print(f'    - Can Cross: {"✅ YES" if can_cross else "❌ NO"}')
        
        # Calculate position margin requirements
        position_margin = total_cross_cost * 0.1  # Assuming 10% margin
        print(f'    - Required Margin: ${position_margin:.2f}')
        
        # Risk assessment
        price_change_pct = ((mark_price - entry_price) / entry_price) * 100
        risk_level = "HIGH" if abs(price_change_pct) > 5 else "MEDIUM" if abs(price_change_pct) > 2 else "LOW"
        print(f'    - Price Change: {price_change_pct:+.2f}%')
        print(f'    - Risk Level: {risk_level}')
        
        crossing_analysis.append({
            'symbol': symbol,
            'position_amt': position_amt,
            'entry_price': entry_price,
            'mark_price': mark_price,
            'unrealized_pnl': unrealized_pnl,
            'close_cost': close_cost,
            'open_cost': open_cost,
            'total_cross_cost': total_cross_cost,
            'available_balance': available_balance,
            'can_cross': can_cross,
            'required_margin': position_margin,
            'price_change_pct': price_change_pct,
            'risk_level': risk_level
        })
    
    # Overall crossing feasibility
    print('\n[4] OVERALL CROSSING FEASIBILITY')
    
    can_cross_positions = [pos for pos in crossing_analysis if pos['can_cross']]
    cannot_cross_positions = [pos for pos in crossing_analysis if not pos['can_cross']]
    
    print(f'  - Positions that CAN be crossed: {len(can_cross_positions)}')
    print(f'  - Positions that CANNOT be crossed: {len(cannot_cross_positions)}')
    
    if can_cross_positions:
        print(f'\n  ✅ POSITIONS THAT CAN BE CROSSED:')
        for pos in can_cross_positions:
            print(f'    - {pos["symbol"]}: ${pos["total_cross_cost"]:.2f} required, ${pos["available_balance"]:.2f} available')
    
    if cannot_cross_positions:
        print(f'\n  ❌ POSITIONS THAT CANNOT BE CROSSED:')
        for pos in cannot_cross_positions:
            deficit = pos['total_cross_cost'] - pos['available_balance']
            print(f'    - {pos["symbol"]}: ${deficit:.2f} shortage (${pos["total_cross_cost"]:.2f} needed, ${pos["available_balance"]:.2f} available)')
    
    # Calculate total crossing requirements
    total_cross_cost_all = sum(pos['total_cross_cost'] for pos in crossing_analysis)
    print(f'\n  - Total Cost to Cross All Positions: ${total_cross_cost_all:.2f}')
    print(f'  - Available Balance: ${available_balance:.2f}')
    print(f'  - Can Cross All: {"✅ YES" if available_balance >= total_cross_cost_all else "❌ NO"}')
    
    # Risk analysis
    print('\n[5] RISK ANALYSIS')
    
    total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in crossing_analysis)
    print(f'  - Total Unrealized PnL: ${total_unrealized_pnl:+.2f}')
    
    if total_unrealized_pnl < 0:
        print(f'  ⚠️  WARNING: Currently in loss position')
        print(f'  - Recommendation: Consider waiting for better entry point')
    else:
        print(f'  ✅ Currently in profit position')
        print(f'  - Recommendation: Crossing may be considered')
    
    # Market impact analysis
    print('\n[6] MARKET IMPACT ANALYSIS')
    
    for pos in crossing_analysis:
        symbol = pos['symbol']
        price_change_pct = pos['price_change_pct']
        
        if price_change_pct > 2:
            print(f'  - {symbol}: Price moved UP {price_change_pct:+.2f}% (unfavorable for SHORT→LONG)')
        elif price_change_pct < -2:
            print(f'  - {symbol}: Price moved DOWN {price_change_pct:+.2f}% (favorable for SHORT→LONG)')
        else:
            print(f'  - {symbol}: Price stable ({price_change_pct:+.2f}% change)')
    
    # Strategy recommendations
    print('\n[7] STRATEGY RECOMMENDATIONS')
    
    print(f'  📋 CROSSING STRATEGY OPTIONS:')
    
    if can_cross_positions:
        print(f'    1. Partial Crossing: Cross {len(can_cross_positions)} profitable positions')
        print(f'    2. Full Crossing: Cross all positions if sufficient balance')
        print(f'    3. Wait and Watch: Wait for better market conditions')
    else:
        print(f'    1. Wait for Balance: Need more available balance')
        print(f'    2. Close Positions: Close SHORT positions without reopening')
        print(f'    3. Reduce Size: Cross smaller positions first')
    
    print(f'\n  🎯 RISK MANAGEMENT:')
    print(f'    - Stop Loss: Set appropriate stop loss for new LONG positions')
    print(f'    - Position Sizing: Consider smaller position sizes')
    print(f'    - Market Timing: Choose optimal entry points')
    print(f'    - Diversification: Don\'t cross all positions at once')
    
    # Technical feasibility
    print('\n[8] TECHNICAL FEASIBILITY')
    
    print(f'  🔧 TECHNICAL REQUIREMENTS:')
    print(f'    - API Access: ✅ Available')
    print(f'    - Account Balance: {"✅ Sufficient" if available_balance > 100 else "⚠️ Low"}')
    print(f'    - Position Limits: Check max positions per symbol')
    print(f'    - Margin Requirements: Verify margin levels')
    print(f'    - Trading Fees: Consider transaction costs')
    
    print(f'\n  📊 EXECUTION STEPS:')
    print(f'    1. Close SHORT position (BUY order)')
    print(f'    2. Wait for position closure confirmation')
    print(f'    3. Open LONG position (BUY order)')
    print(f'    4. Set stop loss and take profit')
    print(f'    5. Monitor new position')
    
    # Final recommendation
    print('\n[9] FINAL RECOMMENDATION')
    
    if len(can_cross_positions) == len(crossing_analysis):
        print(f'  ✅ RECOMMENDATION: CROSSING FEASIBLE')
        print(f'  - All {len(crossing_analysis)} positions can be crossed')
        print(f'  - Total cost: ${total_cross_cost_all:.2f}')
        print(f'  - Available balance: ${available_balance:.2f}')
        print(f'  - Proceed with caution and proper risk management')
    elif len(can_cross_positions) > 0:
        print(f'  ⚡ RECOMMENDATION: PARTIAL CROSSING POSSIBLE')
        print(f'  - {len(can_cross_positions)} of {len(crossing_analysis)} positions can be crossed')
        print(f'  - Consider crossing profitable positions first')
        print(f'  - Wait for better conditions for remaining positions')
    else:
        print(f'  ❌ RECOMMENDATION: CROSSING NOT FEASIBLE')
        print(f'  - Insufficient balance for crossing')
        print(f'  - Consider closing positions or waiting for balance increase')
    
    print('\n' + '=' * 80)
    print('POSITION CROSS ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_position_cross_feasibility()
