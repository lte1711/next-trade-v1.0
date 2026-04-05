#!/usr/bin/env python3
"""
거래소 데이터 불일치 수정 - 실제 포지션과 시스템 데이터 동기화
"""

import requests
import hmac
import hashlib
import urllib.parse
from datetime import datetime
import json

class ExchangeDataSync:
    def __init__(self):
        self.api_key = "tyc0Nz8Trhl8zRG74u1i3gNLFFAzqVQK6mcOtviDD47Z9TpYBPE7qAILBtGCdlCg"
        self.api_secret = "jTuqPonQabOq6Xx19sEWiYsl07Te9L4YsY4j7gJQZ2Lcom0vDxttBuqgK4YME7NI"
        self.base_url = "https://testnet.binancefuture.com"
        
        print("🔧 거래소 데이터 불일치 수정 시작")
        print("=" * 80)
    
    def get_server_time(self):
        """서버 시간 가져오기"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            if response.status_code == 200:
                return response.json()["serverTime"]
            else:
                return int(time.time() * 1000)
        except:
            return int(time.time() * 1000)
    
    def get_account_info(self):
        """계정 정보 가져오기"""
        try:
            server_time = self.get_server_time()
            params = {
                "timestamp": server_time,
                "recvWindow": 5000
            }
            
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v2/account?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 계정 정보 실패: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 계정 정보 오류: {e}")
            return None
    
    def get_current_positions(self):
        """현재 포지션 정보 가져오기"""
        account_info = self.get_account_info()
        if not account_info:
            return {}
        
        positions = {}
        for position in account_info['positions']:
            if float(position['positionAmt']) != 0:
                positions[position['symbol']] = {
                    'amount': float(position['positionAmt']),
                    'entry_price': float(position['entryPrice']),
                    'mark_price': float(position['markPrice']),
                    'unrealized_pnl': float(position['unrealizedPnl']),
                    'percentage': float(position['percentage'])
                }
        
        return positions
    
    def get_recent_trades(self, limit=50):
        """최근 거래 내역 가져오기"""
        try:
            server_time = self.get_server_time()
            params = {
                "timestamp": server_time,
                "recvWindow": 5000,
                "limit": limit
            }
            
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v1/userTrades?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 거래 내역 실패: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 거래 내역 오류: {e}")
            return []
    
    def analyze_discrepancies(self):
        """불일치 분석"""
        print("📊 거래소 데이터 불일치 분석...")
        
        # 1. 현재 포지션 확인
        current_positions = self.get_current_positions()
        print(f"\n📈 현재 포지션 ({len(current_positions)}개):")
        for symbol, pos in current_positions.items():
            side = "LONG" if pos['amount'] > 0 else "SHORT"
            pnl_status = "📈" if pos['unrealized_pnl'] > 0 else "📉" if pos['unrealized_pnl'] < 0 else "➡️"
            print(f"  {symbol}: {side} {abs(pos['amount'])} | 진입: ${pos['entry_price']:.4f} | 현재: ${pos['mark_price']:.4f} | PnL: {pnl_status} {pos['unrealized_pnl']:+.4f}")
        
        # 2. 최근 거래 내역 확인
        recent_trades = self.get_recent_trades()
        print(f"\n📋 최근 거래 내역 ({len(recent_trades)}개):")
        
        # 심볼별 거래 집계
        trade_summary = {}
        for trade in recent_trades:
            symbol = trade['symbol']
            if symbol not in trade_summary:
                trade_summary[symbol] = {
                    'buy_qty': 0,
                    'sell_qty': 0,
                    'buy_amount': 0,
                    'sell_amount': 0,
                    'trades': []
                }
            
            qty = float(trade['qty'])
            price = float(trade['price'])
            amount = qty * price
            
            if trade['side'] == 'BUY':
                trade_summary[symbol]['buy_qty'] += qty
                trade_summary[symbol]['buy_amount'] += amount
            else:
                trade_summary[symbol]['sell_qty'] += qty
                trade_summary[symbol]['sell_amount'] += amount
            
            trade_summary[symbol]['trades'].append({
                'side': trade['side'],
                'qty': qty,
                'price': price,
                'time': datetime.fromtimestamp(int(trade['time']) / 1000)
            })
        
        # 심볼별 거래 요약
        for symbol, summary in trade_summary.items():
            net_qty = summary['buy_qty'] - summary['sell_qty']
            net_side = "BUY" if net_qty > 0 else "SELL" if net_qty < 0 else "BALANCED"
            print(f"  {symbol}: {net_side} | 매수: {summary['buy_qty']:.2f} | 매도: {summary['sell_qty']:.2f} | 순수량: {abs(net_qty):.2f}")
        
        # 3. 포지션과 거래 내역 비교
        print(f"\n🔍 포지션 vs 거래 내역 비교:")
        discrepancies = []
        
        for symbol, position in current_positions.items():
            if symbol in trade_summary:
                summary = trade_summary[symbol]
                expected_qty = summary['buy_qty'] - summary['sell_qty']
                actual_qty = position['amount']
                
                if abs(expected_qty - actual_qty) > 0.001:  # 0.001 이상 차이
                    discrepancies.append({
                        'symbol': symbol,
                        'expected_qty': expected_qty,
                        'actual_qty': actual_qty,
                        'difference': expected_qty - actual_qty
                    })
                    print(f"  ❌ {symbol}: 예상 {expected_qty:.4f} vs 실제 {actual_qty:.4f} (차이: {expected_qty - actual_qty:.4f})")
                else:
                    print(f"  ✅ {symbol}: 예상 {expected_qty:.4f} vs 실제 {actual_qty:.4f} (일치)")
            else:
                print(f"  ⚠️ {symbol}: 포지션만 있고 거래 내역 없음")
        
        # 4. 총 자산 비교
        account_info = self.get_account_info()
        if account_info:
            total_balance = float(account_info['totalWalletBalance'])
            available_balance = float(account_info['availableBalance'])
            
            print(f"\n💰 자산 상태:")
            print(f"  총 자산: {total_balance:.8f} USDT")
            print(f"  사용 가능: {available_balance:.8f} USDT")
            print(f"  사용 중: {total_balance - available_balance:.8f} USDT")
            
            # 포지션별 마진 사용 계산
            total_position_margin = 0
            for symbol, position in current_positions.items():
                position_margin = abs(position['amount']) * position['entry_price'] / 10  # 10x 레버리지 가정
                total_position_margin += position_margin
            
            print(f"  계산된 마진: {total_position_margin:.8f} USDT")
            print(f"  실제 사용 중: {total_balance - available_balance:.8f} USDT")
            
            margin_diff = (total_balance - available_balance) - total_position_margin
            if abs(margin_diff) > 0.01:
                print(f"  ❌ 마진 차이: {margin_diff:.8f} USDT")
                discrepancies.append({
                    'type': 'margin',
                    'expected': total_position_margin,
                    'actual': total_balance - available_balance,
                    'difference': margin_diff
                })
            else:
                print(f"  ✅ 마진 일치")
        
        return {
            'positions': current_positions,
            'trades': trade_summary,
            'discrepancies': discrepancies
        }
    
    def clean_data_for_json(self, data):
        """JSON 직렬화를 위한 데이터 정리"""
        if isinstance(data, dict):
            return {k: self.clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_data_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    def generate_sync_report(self, analysis_result):
        """동기화 보고서 생성"""
        print(f"\n📋 동기화 보고서 생성...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exchange_sync_report_{timestamp}.json"
        
        sync_data = {
            'timestamp': datetime.now().isoformat(),
            'positions': analysis_result['positions'],
            'trades': analysis_result['trades'],
            'discrepancies': analysis_result['discrepancies'],
            'sync_status': 'NEEDS_SYNC' if analysis_result['discrepancies'] else 'SYNCED'
        }
        
        # 데이터 정리
        cleaned_data = self.clean_data_for_json(sync_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 동기화 보고서 저장: {filename}")
        return filename
    
    def suggest_fixes(self, analysis_result):
        """수정 제안"""
        print(f"\n🔧 수정 제안:")
        
        if not analysis_result['discrepancies']:
            print("✅ 모든 데이터가 일치합니다. 수정 필요 없음.")
            return
        
        for discrepancy in analysis_result['discrepancies']:
            if discrepancy['type'] == 'margin':
                print(f"💰 마진 불일치: 예상 {discrepancy['expected']:.8f} vs 실제 {discrepancy['actual']:.8f}")
                print(f"   제안: 레버리지 계산 로직 수정 또는 포지션 마진 재계산")
            else:
                symbol = discrepancy['symbol']
                print(f"📊 {symbol} 수량 불일치: 예상 {discrepancy['expected_qty']:.4f} vs 실제 {discrepancy['actual_qty']:.4f}")
                print(f"   제안: 거래 내역 재조회 또는 포지션 계산 로직 수정")
    
    def run_sync_analysis(self):
        """동기화 분석 실행"""
        print("🔍 거래소 데이터 동기화 분석 시작")
        print("=" * 80)
        
        # 1. 불일치 분석
        analysis_result = self.analyze_discrepancies()
        
        # 2. 동기화 보고서 생성
        report_file = self.generate_sync_report(analysis_result)
        
        # 3. 수정 제안
        self.suggest_fixes(analysis_result)
        
        # 4. 요약
        print(f"\n🎯 분석 요약:")
        print("=" * 50)
        print(f"포지션 수: {len(analysis_result['positions'])}개")
        print(f"거래 내역: {len(analysis_result['trades'])}개 심볼")
        print(f"불일치 항목: {len(analysis_result['discrepancies'])}개")
        print(f"동기화 상태: {'❌ 필요' if analysis_result['discrepancies'] else '✅ 완료'}")
        
        return analysis_result

if __name__ == "__main__":
    sync = ExchangeDataSync()
    result = sync.run_sync_analysis()
