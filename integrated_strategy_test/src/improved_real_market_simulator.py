"""
개선된 실전 테스트용 최종 동적 투자 시뮬레이터 v5.0
- 교체 빈도 제어 개선
- 수수료 효율성 최적화
- 시장 상태 감지 강화
- 반복적 교체 방지
- 수익 가능성 평가 후 선택적 투자
- 동적 전략 로드 시스템
"""

import sys
import os
import json
import time
import requests
import random
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any
import statistics

class ImprovedRealMarketDynamicInvestmentSimulator:
    """개선된 실전 테스트용 최종 동적 투자 시뮬레이터 v5.0"""
    
    def __init__(self, symbol_count: int = 10, replacement_threshold: float = -0.8):
        self.total_capital = 1000.0  # 총 자본 $1000
        self.initial_capital = 1000.0
        self.current_capital = 1000.0
        self.max_symbols = symbol_count  # 최대 10개 심볼
        self.investments = {}  # 심볼별 투자 정보
        self.performance_history = []  # 성과 기록
        self.replacement_history = []  # 교체 기록
        self.exchange_base_url = "https://demo-fapi.binance.com"
        self.supported_symbols = set()
        self.evaluated_symbols = []  # 평가된 모든 심볼 목록
        
        # 거래 수수료 설정
        self.trading_fee = 0.0004  # 0.04% (바이낸스 선물 기본 수수료)
        self.total_fees_paid = 0.0  # 총 지불 수수료
        
        # 익절/손절 동적 설정
        self.take_profit_threshold = 5.0  # 5% 익절
        self.stop_loss_threshold = -3.0  # -3% 손절
        self.dynamic_take_profit = True  # 동적 익절
        self.dynamic_stop_loss = True  # 동적 손절
        
        # 개선된 교체 파라미터
        self.performance_threshold = replacement_threshold  # -0.8%
        self.min_replacement_interval = 15  # 15분으로 증가
        self.max_replacements_per_hour = 2  # 시간당 최대 2회로 감소
        self.max_replacements_per_day = 20  # 일일 최대 20회
        self.last_replacement_time = None
        self.replacements_this_hour = 0
        self.replacements_today = 0
        self.last_hour_reset = datetime.now().hour
        self.last_day_reset = datetime.now().date()
        
        # 반복적 교체 방지
        self.replacement_cooldown = {}  # 심볼별 교체 쿨다운
        self.replacement_blacklist = {}  # 심볼별 교체 블랙리스트
        self.recent_replacements = []  # 최근 교체 기록
        
        # 시장 상태 분석 강화
        self.market_regime = "NORMAL"
        self.volatility_threshold = 2.5
        self.extreme_volatility_threshold = 5.0
        self.market_state_history = []  # 시장 상태 기록
        
        # 수익 가능성 평가
        self.profitability_threshold = 80.0  # 기본 수익 가능성 점수 기준 (동적 조정)
        self.min_profit_symbols = 1  # 최소 투자 심볼 수 (1개 보장)
        self.max_profit_symbols = 10  # 최대 투자 심볼 수 ($1000 ÷ $100)
        
        # 시장 상태별 동적 기준
        self.market_regime_thresholds = {
            "EXTREME": 70.0,      # 극단적 시장: 70% 이상
            "HIGH_VOLATILITY": 75.0,  # 고변동성: 75% 이상
            "NORMAL": 80.0        # 정상 시장: 80% 이상
        }
        
        # 동적 전략 로드
        self.available_strategies = {
            "conservative": {
                "take_profit": 3.0,
                "stop_loss": -2.0,
                "replacement_threshold": -1.0,
                "max_symbols": 5,
                "replacement_interval": 30
            },
            "balanced": {
                "take_profit": 5.0,
                "stop_loss": -3.0,
                "replacement_threshold": -0.8,
                "max_symbols": 8,
                "replacement_interval": 15
            },
            "aggressive": {
                "take_profit": 8.0,
                "stop_loss": -4.0,
                "replacement_threshold": -0.5,
                "max_symbols": 10,
                "replacement_interval": 10
            }
        }
        self.current_strategy = "balanced"
        
        print(f"FACT: 개선된 실전 테스트용 최종 동적 투자 시뮬레이터 v5.0 초기화")
        print(f"  💰 초기 자본: $1000.00")
        print(f"  🎯 투자 전략: 선택적 심볼 + 개선된 동적 교체 + $100 고정 투자")
        print(f"  🔄 교체 기준: -0.8% 이하")
        print(f"  📊 거래 수수료: 0.04% 포함")
        print(f"  🎯 익절/손절: 동적 자동 평가")
        print(f"  ⏰ 테스트 시간: 12시간")
        print(f"  🔧 개선 사항: 교체 빈도 제어, 수수료 효율성, 반복 방지, $100 고정 투자")
        print(f"  🔢 지원 심볼: {len(self.supported_symbols)}개 로드 완료")  
        
        self._load_supported_symbols()
    
    def _load_supported_symbols(self):
        """지원 심볼 목록 로드"""
        try:
            response = requests.get(f"{self.exchange_base_url}/fapi/v1/exchangeInfo", timeout=10)
            if response.status_code == 200:
                data = response.json()
                filtered_symbols = []
                for s in data['symbols']:
                    if (s['symbol'].endswith('USDT') and 
                        s['status'] == 'TRADING' and 
                        s['contractType'] == 'PERPETUAL'):
                        filtered_symbols.append(s['symbol'])
                self.supported_symbols = set(filtered_symbols)
                print(f"  🔢 지원 심볼: {len(self.supported_symbols)}개 로드 완료")
            else:
                fallback_symbols = [
                    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
                    'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT'
                ]
                self.supported_symbols = set(fallback_symbols)
                print(f"  🔄 Fallback: {len(self.supported_symbols)}개 기본 심볼 사용")
        except Exception as e:
            print(f"  ❌ 심볼 목록 로드 오류: {e}")
            fallback_symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
                'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT'
            ]
            self.supported_symbols = set(fallback_symbols)
            print(f"  🔄 Fallback: {len(self.supported_symbols)}개 기본 심볼 사용")
    
    def analyze_market_volatility_enhanced(self) -> str:
        """강화된 시장 변동성 분석"""
        if not self.investments:
            return "NORMAL"
        
        volatilities = []
        price_changes = []
        volume_changes = []
        
        for symbol in self.investments.keys():
            try:
                # 24시간 데이터 분석
                klines_url = f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=24"
                response = requests.get(klines_url, timeout=5)
                
                if response.status_code == 200:
                    klines_data = response.json()
                    closes = [float(kline[4]) for kline in klines_data]
                    volumes = [float(kline[5]) for kline in klines_data]
                    
                    if len(closes) >= 20:
                        # 변동성 계산
                        volatility = self._calculate_volatility(closes)
                        volatilities.append(volatility)
                        
                        # 가격 변화율
                        price_change = (closes[-1] - closes[0]) / closes[0] * 100
                        price_changes.append(price_change)
                        
                        # 거래량 변화
                        volume_change = (volumes[-1] - volumes[0]) / volumes[0] * 100
                        volume_changes.append(volume_change)
            except:
                continue
        
        if not volatilities:
            return "NORMAL"
        
        avg_volatility = sum(volatilities) / len(volatilities)
        avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
        avg_volume_change = sum(volume_changes) / len(volume_changes) if volume_changes else 0
        
        # 시장 상태 결정 로직 강화
        if avg_volatility >= self.extreme_volatility_threshold:
            self.market_regime = "EXTREME"
        elif avg_volatility >= self.volatility_threshold:
            self.market_regime = "HIGH_VOLATILITY"
        elif abs(avg_price_change) > 2.0 or abs(avg_volume_change) > 30:
            self.market_regime = "HIGH_VOLATILITY"
        else:
            self.market_regime = "NORMAL"
        
        # 시장 상태 기록
        self.market_state_history.append({
            "timestamp": datetime.now().isoformat(),
            "regime": self.market_regime,
            "volatility": avg_volatility,
            "price_change": avg_price_change,
            "volume_change": avg_volume_change
        })
        
        return self.market_regime
    
    def evaluate_profitability_potential(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """수익 가능성 평가 (동적 기준 적용)"""
        # 현재 시장 상태에 따른 기준 동적 조정
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
        
        print(f"FACT: 상승장 정밀평가 시작 (시장 상태: {self.market_regime}, 기준: {current_threshold}%)")
        
        profitable_symbols = []
        
        for symbol_data in symbols:
            # 기본 상승 가능성 점수 확인
            bullish_score = symbol_data.get("bullish_score", 0)
            
            # 상승장 정밀평가 (동적 기준 적용)
            if bullish_score >= current_threshold:
                # 추가 상승 가능성 평가
                profit_potential = self._calculate_profit_potential(symbol_data)
                
                # 동적 기준 적용
                if profit_potential >= current_threshold:
                    symbol_data["profit_potential"] = profit_potential
                    profitable_symbols.append(symbol_data)
                    print(f"  ✅ {symbol_data['symbol']}: 상승 가능성 {profit_potential:.1f}%")
                else:
                    print(f"  ❌ {symbol_data['symbol']}: 상승 가능성 {profit_potential:.1f}% (미달)")
            else:
                print(f"  ❌ {symbol_data['symbol']}: 상승 가능성 {bullish_score:.1f}% (미달)")
        
        # 상승 가능성 순으로 정렬
        profitable_symbols.sort(key=lambda x: x["profit_potential"], reverse=True)
        
        print(f"  📊 상승 가능성 {current_threshold}% 이상 심볼: {len(profitable_symbols)}개")
        
        # 최소 1개 심볼 보장
        if len(profitable_symbols) == 0:
            print(f"  ⚠️ {current_threshold}% 이상 심볼 없음 - 최소 1개 심볼 보장 적용")
            # 가장 높은 상승 가능성 심볼 1개 선택
            all_symbols_sorted = sorted(symbols, key=lambda x: x.get("bullish_score", 0), reverse=True)
            if all_symbols_sorted:
                best_symbol = all_symbols_sorted[0]
                profit_potential = self._calculate_profit_potential(best_symbol)
                best_symbol["profit_potential"] = profit_potential
                profitable_symbols = [best_symbol]
                print(f"  🛡️ 최소 보장: {best_symbol['symbol']} (상승 가능성 {profit_potential:.1f}%)")
        
        # 모든 심볼에 profit_potential 설정 보장 (데이터 일치성)
        for symbol_data in symbols:
            if "profit_potential" not in symbol_data:
                symbol_data["profit_potential"] = self._calculate_profit_potential(symbol_data)
        
        return profitable_symbols
    
    def get_real_time_symbol_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """실시간 심볼 데이터 조회"""
        real_time_data = []
        
        print(f"FACT: 실시간 심볼 데이터 조회 시작 ({len(symbols)}개 심볼)")
        
        for symbol in symbols:
            try:
                # 실시간 가격 데이터 조회
                ticker_response = requests.get(f"{self.exchange_base_url}/fapi/v1/ticker/24hr?symbol={symbol}", timeout=10)
                if ticker_response.status_code == 200:
                    ticker_data = ticker_response.json()
                    
                    # 실시간 기술적 지표 계산
                    symbol_data = {
                        "symbol": symbol,
                        "price": float(ticker_data["lastPrice"]),
                        "change_percent": float(ticker_data["priceChangePercent"]),
                        "volume": float(ticker_data["volume"]),
                        # 실시간 RSI, MACD 계산 (시뮬레이션에서는 간단한 근사치 사용)
                        "rsi": self.calculate_real_time_rsi(symbol),
                        "macd_signal": self.calculate_real_time_macd(symbol),
                        "bullish_score": self.calculate_real_time_bullish_score(symbol)
                    }
                    
                    real_time_data.append(symbol_data)
                    print(f"  ✅ {symbol}: 가격 ${symbol_data['price']:.4f}, 변동 {symbol_data['change_percent']:+.2f}%")
                    
                else:
                    print(f"  ❌ {symbol}: API 응답 오류 ({ticker_response.status_code})")
                    
            except Exception as e:
                print(f"  ❌ {symbol}: 실시간 데이터 조회 실패 - {e}")
        
        print(f"  📊 실시간 데이터 조회 성공: {len(real_time_data)}개")
        return real_time_data
    
    def calculate_real_time_rsi(self, symbol: str) -> float:
        """실시간 RSI 계산 (간단한 근사치)"""
        try:
            # Klines 데이터 조회
            klines_response = requests.get(f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=14", timeout=10)
            if klines_response.status_code == 200:
                klines = klines_response.json()
                
                # 종가 데이터 추출
                closes = [float(k[4]) for k in klines]
                
                # RSI 계산
                if len(closes) < 2:
                    return 50.0
                
                gains = []
                losses = []
                
                for i in range(1, len(closes)):
                    change = closes[i] - closes[i-1]
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))
                
                avg_gain = sum(gains) / len(gains) if gains else 0
                avg_loss = sum(losses) / len(losses) if losses else 0
                
                if avg_loss == 0:
                    return 100.0
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                
                return min(max(rsi, 0), 100)
                
        except Exception as e:
            print(f"  ❌ {symbol} RSI 계산 실패: {e}")
            return 50.0
    
    def calculate_real_time_macd(self, symbol: str) -> str:
        """실시간 MACD 신호 계산 (간단한 근사치)"""
        try:
            # Klines 데이터 조회
            klines_response = requests.get(f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=26", timeout=10)
            if klines_response.status_code == 200:
                klines = klines_response.json()
                
                # 종가 데이터 추출
                closes = [float(k[4]) for k in klines]
                
                if len(closes) < 26:
                    return "NEUTRAL"
                
                # 간단한 MACD 근사치 계산
                # 12일 EMA
                ema_12 = closes[0]
                for price in closes[1:12]:
                    ema_12 = (price * 2/13) + (ema_12 * 11/13)
                
                # 26일 EMA
                ema_26 = closes[0]
                for price in closes[1:26]:
                    ema_26 = (price * 2/27) + (ema_26 * 25/27)
                
                # MACD 라인
                macd_line = ema_12 - ema_26
                
                # 신호 라인 (간단한 9일 SMA)
                if macd_line > 0:
                    return "BULLISH"
                elif macd_line < 0:
                    return "BEARISH"
                else:
                    return "NEUTRAL"
                    
        except Exception as e:
            print(f"  ❌ {symbol} MACD 계산 실패: {e}")
            return "NEUTRAL"
    
    def calculate_real_time_bullish_score(self, symbol: str) -> float:
        """실시간 상승 점수 계산"""
        try:
            # Klines 데이터 조회
            klines_response = requests.get(f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=24", timeout=10)
            if klines_response.status_code == 200:
                klines = klines_response.json()
                
                # 종가 데이터 추출
                closes = [float(k[4]) for k in klines]
                
                if len(closes) < 2:
                    return 50.0
                
                # 상승 점수 계산
                recent_change = (closes[-1] - closes[0]) / closes[0] * 100
                volume_trend = sum(float(k[5]) for k in klines[-5:]) / sum(float(k[5]) for k in klines[-10:-5]) if len(klines) >= 10 else 1.0
                
                # 종합 상승 점수
                bullish_score = 50.0
                
                # 가격 상승 점수 (30%)
                if recent_change > 0:
                    bullish_score += min(recent_change * 2, 30)
                else:
                    bullish_score += max(recent_change * 2, -30)
                
                # 거래량 점수 (20%)
                if volume_trend > 1.2:
                    bullish_score += 20
                elif volume_trend > 1.0:
                    bullish_score += 10
                elif volume_trend < 0.8:
                    bullish_score -= 10
                
                return min(max(bullish_score, 0), 100)
                
        except Exception as e:
            print(f"  ❌ {symbol} 상승 점수 계산 실패: {e}")
            return 50.0
    
    def update_real_time_profit_potential(self):
        """매 라운드 실시간 상승 가능성 평가"""
        print(f"FACT: 실시간 상승 가능성 평가 시작")
        
        # 현재 투자 심볼 목록
        current_symbols = list(self.investments.keys())
        
        if not current_symbols:
            print(f"  ℹ️ 현재 투자 심볼 없음")
            return
        
        # 실시간 데이터 조회
        real_time_data = self.get_real_time_symbol_data(current_symbols)
        
        # 상승 가능성 재계산
        for symbol_data in real_time_data:
            symbol = symbol_data["symbol"]
            current_potential = self._calculate_profit_potential(symbol_data)
            
            # evaluated_symbols 업데이트
            for evaluated in self.evaluated_symbols:
                if evaluated["symbol"] == symbol:
                    evaluated.update(symbol_data)
                    evaluated["profit_potential"] = current_potential
                    print(f"  🔄 {symbol}: 상승 가능성 {current_potential:.1f}% (실시간 업데이트)")
                    break
    
    def find_new_high_potential_symbols(self) -> List[Dict[str, Any]]:
        """실시간으로 높은 상승 가능성 심볼 찾기"""
        print(f"FACT: 실시간 높은 상승 가능성 심볼 탐색 시작")
        
        # 현재 시장 상태에 따른 기준
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
        
        # 상위 거래량 심볼 다시 조회 (실시간)
        top_volume_symbols = self.get_top_volume_symbols(80)
        
        if not top_volume_symbols:
            print(f"  ❌ 상위 심볼 조회 실패")
            return []
        
        # 실시간 데이터 조회
        symbol_names = [s["symbol"] for s in top_volume_symbols]
        real_time_data = self.get_real_time_symbol_data(symbol_names)
        
        # 상승 가능성 평가
        high_potential_symbols = []
        
        for symbol_data in real_time_data:
            # 현재 투자 중인 심볼은 제외
            if symbol_data["symbol"] in self.investments:
                continue
            
            # 상승 가능성 계산
            current_potential = self._calculate_profit_potential(symbol_data)
            symbol_data["profit_potential"] = current_potential
            
            # 기준 이상 심볼 선택
            if current_potential >= current_threshold:
                high_potential_symbols.append(symbol_data)
                print(f"  ✅ {symbol_data['symbol']}: 상승 가능성 {current_potential:.1f}% (기준 {current_threshold}% 이상)")
            else:
                print(f"  ❌ {symbol_data['symbol']}: 상승 가능성 {current_potential:.1f}% (기준 미달)")
        
        # 상승 가능성 순으로 정렬
        high_potential_symbols.sort(key=lambda x: x["profit_potential"], reverse=True)
        
        print(f"  📊 기준 이상 심볼: {len(high_potential_symbols)}개")
        
        return high_potential_symbols
    
    def _calculate_profit_potential(self, symbol_data: Dict[str, Any]) -> float:
        """상승 가능성 정밀 계산"""
        potential = 0
        
        # 상승 가능성 점수 (40%)
        bullish_score = symbol_data.get("bullish_score", 0)
        potential += bullish_score * 0.4
        
        # 현재 가격 상승률 (25%)
        change_percent = symbol_data.get("change_percent", 0)
        if change_percent > 0:
            # 상승률이 높을수록 더 높은 점수
            momentum_score = min(change_percent * 3, 25)
        else:
            momentum_score = 0  # 하락은 0점
        potential += momentum_score
        
        # 거래량 증가 (15%)
        volume = symbol_data.get("volume", 0)
        volume_score = min(volume / 800000, 15)  # 거래량 기준 상향 조정
        potential += volume_score
        
        # 기술적 지표 강화 (15%)
        rsi = symbol_data.get("rsi", 50)
        if 40 <= rsi <= 60:  # 정상 범위
            rsi_score = 10
        elif 30 <= rsi < 40:  # 과매도 근접
            rsi_score = 15
        elif 60 < rsi <= 70:  # 과매수 근접
            rsi_score = 8
        else:
            rsi_score = 0
        potential += rsi_score
        
        # MACD 상승 신호 (5%)
        macd_signal = symbol_data.get("macd_signal", "NEUTRAL")
        if macd_signal == "BULLISH":
            macd_score = 5
        else:
            macd_score = 0
        potential += macd_score
        
        return potential
    
    def select_optimal_symbols(self, profitable_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """최적 심볼 선택 (동적 기준 적용)"""
        # 현재 시장 상태에 따른 기준 확인
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
        
        print(f"FACT: 상승장 최적 심볼 선택 시작 (기준: {current_threshold}%)")
        print(f"  📊 입력 심볼 수: {len(profitable_symbols)}개")
        
        # 현재 시장 상태에 따른 최대 심볼 수 조정
        if self.market_regime == "EXTREME":
            max_symbols = min(self.max_profit_symbols, 5)  # 극단적 시장: 최대 5개
        elif self.market_regime == "HIGH_VOLATILITY":
            max_symbols = min(self.max_profit_symbols, 7)  # 고변동성: 최대 7개
        else:
            max_symbols = self.max_profit_symbols  # 정상 시장: 최대 10개
        
        print(f"  🌊 시장 상태: {self.market_regime}")
        print(f"  📊 최대 심볼 수: {max_symbols}")
        print(f"  📊 최소 심볼 수: {self.min_profit_symbols}")
        print(f"  📊 최대 심볼 상수: {self.max_profit_symbols}")
        
        # 상승 가능성이 높은 심볼 선택
        selected_symbols = profitable_symbols[:max_symbols]
        
        print(f"  📊 선택된 심볼 수: {len(selected_symbols)}개")
        
        # 선택된 심볼 상세 정보 출력
        for i, symbol in enumerate(selected_symbols, 1):
            print(f"    {i}. {symbol['symbol']}: 상승 가능성 {symbol['profit_potential']:.1f}%")
        
        # 최소 심볼 수 확인 (1개 보장)
        if len(selected_symbols) == 0:
            print(f"  ⚠️ 선택된 심볼 없음 - 최소 1개 심볼 보장 적용")
            print(f"  🔄 교체주기마다 재평가하여 추가/교체/배재 진행")
            return selected_symbols  # 빈 리스트 반환
        
        print(f"  ✅ {len(selected_symbols)}개 상승 가능성 높은 심볼 선택 완료 (최대 {max_symbols}개)")
        
        return selected_symbols
    
    def load_dynamic_strategy(self, market_regime: str) -> Dict[str, Any]:
        """동적 전략 로드"""
        print(f"FACT: 동적 전략 로드 (시장 상태: {market_regime})")
        
        if market_regime == "EXTREME":
            strategy = self.available_strategies["conservative"]
            self.current_strategy = "conservative"
        elif market_regime == "HIGH_VOLATILITY":
            strategy = self.available_strategies["balanced"]
            self.current_strategy = "balanced"
        else:
            strategy = self.available_strategies["aggressive"]
            self.current_strategy = "aggressive"
        
        # 전략 파라미터 적용
        self.take_profit_threshold = strategy["take_profit"]
        self.stop_loss_threshold = strategy["stop_loss"]
        self.performance_threshold = strategy["replacement_threshold"]
        self.max_symbols = strategy["max_symbols"]
        self.min_replacement_interval = strategy["replacement_interval"]
        
        print(f"  ✅ 전략 로드 완료: {self.current_strategy}")
        print(f"    익절: {self.take_profit_threshold}%, 손절: {self.stop_loss_threshold}%")
        print(f"    교체 기준: {self.performance_threshold}%, 최대 심볼: {self.max_symbols}개")
        
        return strategy
    
    def check_replacement_cooldown(self, symbol: str) -> bool:
        """교체 쿨다운 확인"""
        current_time = datetime.now()
        
        # 심볼별 쿨다운 확인
        if symbol in self.replacement_cooldown:
            last_replacement = self.replacement_cooldown[symbol]
            cooldown_period = timedelta(hours=2)  # 2시간 쿨다운
            
            if current_time - last_replacement < cooldown_period:
                return False
        
        # 반복적 교체 확인
        recent_count = 0
        for replacement in self.recent_replacements[-10:]:  # 최근 10개 교체 확인
            if isinstance(replacement, dict) and (
                replacement.get("old_symbol") == symbol or 
                replacement.get("new_symbol") == symbol
            ):
                recent_count += 1
        
        if recent_count >= 3:  # 최근 10개 중 3회 이상 교체된 심볼은 제외
            return False
        
        return True
    
    def dynamic_portfolio_rebalancing(self):
        """교체주기마다 동적 포트폴리오 리밸런싱 (동적 기준 적용)"""
        # 현재 시장 상태에 따른 기준 동적 조정
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
        
        print(f"FACT: 동적 포트폴리오 리밸런싱 시작 (기준: {current_threshold}%)")
        
        # 1. 현재 투자 심볼 상승 가능성 재평가
        current_symbols = list(self.investments.keys())
        symbols_to_remove = []
        
        for symbol in current_symbols:
            # 현재 투자 심볼의 상승 가능성 재평가
            symbol_data = None
            for evaluated in self.evaluated_symbols:
                if evaluated["symbol"] == symbol:
                    symbol_data = evaluated
                    break
            
            if symbol_data:
                current_potential = self._calculate_profit_potential(symbol_data)
                if current_potential < current_threshold:  # 동적 기준 적용
                    symbols_to_remove.append(symbol)
                    print(f"  📉 {symbol}: 상승 가능성 {current_potential:.1f}% (배재 대상)")
        
        # 2. 상승 가능성 기준 이상 새로운 심볼 찾기 (실시간)
        available_symbols = []
        
        # 실시간으로 높은 상승 가능성 심볼 찾기
        high_potential_symbols = self.find_new_high_potential_symbols()
        
        for symbol_data in high_potential_symbols:
            if symbol_data["symbol"] not in self.investments:
                available_symbols.append(symbol_data)
        
        print(f"  📊 평가된 심볼 수: {len(self.evaluated_symbols)}개")
        print(f"  📊 profit_potential 설정된 심볼: {sum(1 for s in self.evaluated_symbols if 'profit_potential' in s)}개")
        print(f"  📊 실시간 기준 이상 심볼: {len(available_symbols)}개")
        
        # 3. 배재 및 추가 결정
        if symbols_to_remove:
            print(f"  🗑️ 배재 심볼: {len(symbols_to_remove)}개")
            for symbol in symbols_to_remove:
                investment = self.investments[symbol]
                current_value = investment["current_investment"]
                
                # 매도 수수료
                sell_fee = current_value * self.trading_fee
                net_proceeds = current_value - sell_fee
                
                # 투자 제거
                del self.investments[symbol]
                self.total_fees_paid += sell_fee
                
                print(f"    ❌ {symbol}: ${net_proceeds:.2f} 회수 (수수료: ${sell_fee:.2f})")
        
        if available_symbols:
            print(f"  ➕ 추가 가능 심볼: {len(available_symbols)}개")
            
            # 배재된 자본으로 새로운 심볼 추가
            total_available_capital = self.current_capital
            
            if symbols_to_remove:
                # 배재된 자본 계산
                for symbol in symbols_to_remove:
                    if symbol in current_symbols:
                        total_available_capital += self.investments.get(symbol, {}).get("current_investment", 0)
            
            # 새로운 심볼에 자본 분배
            max_new_symbols = min(len(available_symbols), self.max_profit_symbols - len(self.investments))
            new_symbols = available_symbols[:max_new_symbols]
            
            if new_symbols and total_available_capital > 0:
                # 각 새로운 심볼에 $100 투자
                fixed_amount = 100.0
                
                for symbol_data in new_symbols:
                    symbol = symbol_data["symbol"]
                    price = symbol_data["price"]
                    
                    # $100 고정 투자
                    allocation = fixed_amount
                    
                    # 자본 확인
                    if len(self.investments) * fixed_amount + fixed_amount > self.total_capital:
                        print(f"    ⚠️ 자본 초과: {len(self.investments)}개 + 1개 x ${fixed_amount} > ${self.total_capital}")
                        break
                    
                    # 매수 수수료
                    buy_fee = allocation * self.trading_fee
                    net_investment = allocation - buy_fee
                    shares = net_investment / price
                    
                    self.investments[symbol] = {
                        "initial_investment": allocation,
                        "net_investment": net_investment,
                        "current_investment": net_investment,
                        "initial_price": price,
                        "current_price": price,
                        "shares": shares,
                        "initial_time": datetime.now().isoformat(),
                        "last_update": datetime.now().isoformat(),
                        "pnl": 0.0,
                        "pnl_percent": 0.0,
                        "rank": symbol_data.get("bullish_rank", 1),  # 기본값 1
                        "bullish_score": symbol_data["bullish_score"],
                        "fees_paid": buy_fee,
                        "take_profit": self.take_profit_threshold,
                        "stop_loss": self.stop_loss_threshold,
                        "profit_potential": symbol_data.get("profit_potential", 0)
                    }
                    
                    self.total_fees_paid += buy_fee
                    print(f"    ✅ {symbol}: ${net_investment:.2f} 투자 (수수료: ${buy_fee:.2f})")
        
        # 4. 최종 포트폴리오 상태
        print(f"  📊 최종 포트폴리오: {len(self.investments)}개 심볼")
        for symbol, investment in self.investments.items():
            print(f"    • {symbol}: 상승 가능성 {investment.get('profit_potential', 0):.1f}%")
        
        return len(self.investments) > 0
    
    def update_replacement_cooldown(self, symbol: str):
        """교체 쿨다운 업데이트"""
        self.replacement_cooldown[symbol] = datetime.now()
        
        # 최근 교체 기록에 추가
        self.recent_replacements.append({
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol
        })
        
        # 최근 교체 기록 유지 (최근 20개)
        if len(self.recent_replacements) > 20:
            self.recent_replacements = self.recent_replacements[-20:]
    
    def should_replace_symbol_improved(self, symbol: str) -> bool:
        """개선된 심볼 교체 필요 여부 판단"""
        if symbol not in self.investments:
            return False
        
        investment = self.investments[symbol]
        current_pnl_percent = investment["pnl_percent"]
        
        # 익절/손절 우선 처리
        if investment.get("should_close", False):
            return True
        
        # 교체 쿨다운 확인
        if not self.check_replacement_cooldown(symbol):
            return False
        
        # 시간당 교체 횟수 확인
        current_time = datetime.now()
        current_hour = current_time.hour
        current_date = current_time.date()
        
        if current_hour != self.last_hour_reset:
            self.replacements_this_hour = 0
            self.last_hour_reset = current_hour
        
        if current_date != self.last_day_reset:
            self.replacements_today = 0
            self.last_day_reset = current_date
        
        if self.replacements_this_hour >= self.max_replacements_per_hour:
            return False
        
        if self.replacements_today >= self.max_replacements_per_day:
            return False
        
        # 최소 교체 간격 확인
        if self.last_replacement_time is not None:
            time_since_last = (current_time - self.last_replacement_time).total_seconds()
            if time_since_last < self.min_replacement_interval * 60:
                return False
        
        # 시장 상태에 따른 동적 교체 기준 조정
        threshold = self.performance_threshold
        
        if self.market_regime == "EXTREME":
            threshold = threshold * 0.5
        elif self.market_regime == "HIGH_VOLATILITY":
            threshold = threshold * 0.75
        
        # 교체 기준 확인
        if current_pnl_percent <= threshold:
            return True
        
        return False
    
    def replace_underperforming_symbol_improved(self):
        """개선된 부진 심볼 교체"""
        print(f"FACT: 개선된 부진 심볼 교체 프로세스 시작")
        print(f"  🌊 현재 시장 상태: {self.market_regime}")
        print(f"  📋 현재 전략: {self.current_strategy}")
        
        # 교체 대상 심볼 찾기
        underperforming_symbols = []
        for symbol in self.investments.keys():
            if self.should_replace_symbol_improved(symbol):
                underperforming_symbols.append(symbol)
        
        if not underperforming_symbols:
            print("  ✅ 교체 대상 심볼 없음")
            return False
        
        # 가장 부진한 심볼 선택
        worst_symbol = None
        worst_performance = float('inf')
        
        for symbol in underperforming_symbols:
            investment = self.investments[symbol]
            if investment["pnl_percent"] < worst_performance:
                worst_performance = investment["pnl_percent"]
                worst_symbol = symbol
        
        if worst_symbol is None:
            return False
        
        print(f"  🔄 교체 대상: {worst_symbol} (성과: {worst_performance:.2f}%)")
        
        # 익절/손절 사유 확인
        investment = self.investments[worst_symbol]
        close_reason = investment.get("close_reason", "PERFORMANCE_THRESHOLD")
        print(f"  📋 교체 사유: {close_reason}")
        
        # 현재 시장 상태에 따른 기준 동적 조정
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
        
        # 현재 심볼의 상승 가능성 재평가
        current_symbol_data = None
        for evaluated in self.evaluated_symbols:
            if evaluated["symbol"] == worst_symbol:
                current_symbol_data = evaluated
                break
        
        if current_symbol_data:
            current_potential = self._calculate_profit_potential(current_symbol_data)
            print(f"  📊 {worst_symbol} 현재 상승 가능성: {current_potential:.1f}%")
            
            # 상승 가능성이 기준 이상이면 익절/손절하지 않고 유지
            if current_potential >= current_threshold:
                print(f"  ✅ {worst_symbol} 상승 가능성 {current_potential:.1f}% >= {current_threshold}% 기준 - 익절/손절하지 않고 유지")
                
                # 익절/손절 상태와 상관없이 계속 보유
                investment["should_close"] = False
                investment["close_reason"] = "HIGH_POTENTIAL_CONTINUE"
                print(f"  🔄 {worst_symbol} 계속 보유 (상승 가능성 {current_potential:.1f}%)")
                
                return False
        
        # 교체할 심볼 선택 (수익 가능성 평가)
        available_symbols = [
            s for s in self.evaluated_symbols 
            if s["symbol"] not in self.investments and s.get("profit_potential", 0) >= current_threshold
        ]
        
        if not available_symbols:
            print("  ⚠️ 교체 가능한 심볼 없음")
            return False
        
        best_replacement = available_symbols[0]
        print(f"  🎯 교체 심볼: {best_replacement['symbol']} (점수: {best_replacement['bullish_score']:.1f}, 수익 가능성: {best_replacement.get('profit_potential', 0):.1f})")
        
        # 교체 실행
        old_investment = self.investments[worst_symbol]
        old_value = old_investment["current_investment"]
        
        # 매도 수수료
        sell_fee = old_value * self.trading_fee
        net_proceeds = old_value - sell_fee
        
        # 기존 심볼 제거
        del self.investments[worst_symbol]
        
        # 새 심볼 매수 ($100 고정 투자)
        new_price = best_replacement["price"]
        fixed_amount = 100.0  # $100 고정
        
        # 자본 확인
        if len(self.investments) * fixed_amount + fixed_amount > self.total_capital:
            print(f"  ⚠️ 자본 초과: {len(self.investments)}개 + 1개 x ${fixed_amount} > ${self.total_capital}")
            return False
        
        buy_fee = fixed_amount * self.trading_fee
        net_investment = fixed_amount - buy_fee
        new_shares = net_investment / new_price
        
        self.investments[best_replacement["symbol"]] = {
            "initial_investment": fixed_amount,
            "net_investment": net_investment,
            "current_investment": net_investment,
            "initial_price": new_price,
            "current_price": new_price,
            "shares": new_shares,
            "initial_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "pnl": 0.0,
            "pnl_percent": 0.0,
            "rank": best_replacement.get("bullish_rank", 1),  # 기본값 1
            "bullish_score": best_replacement["bullish_score"],
            "fees_paid": buy_fee,
            "take_profit": self.take_profit_threshold,
            "stop_loss": self.stop_loss_threshold,
            "profit_potential": best_replacement.get("profit_potential", 0)
        }
        
        # 수수료 누적
        total_fee = sell_fee + buy_fee
        self.total_fees_paid += total_fee
        
        # 교체 쿨다운 업데이트
        self.update_replacement_cooldown(worst_symbol)
        
        # 교체 기록
        replacement_record = {
            "timestamp": datetime.now().isoformat(),
            "old_symbol": worst_symbol,
            "new_symbol": best_replacement["symbol"],
            "old_performance": worst_performance,
            "new_potential": best_replacement.get("profit_potential", 0),
            "reason": close_reason,
            "market_regime": self.market_regime,
            "strategy": self.current_strategy,
            "replacement_threshold": self.performance_threshold
        }
        
        self.replacement_history.append(replacement_record)
        self.last_replacement_time = datetime.now()
        self.replacements_this_hour += 1
        self.replacements_today += 1
        
        print(f"  ✅ 교체 완료: {worst_symbol} → {best_replacement['symbol']}")
        print(f"  💰 이전 금액: ${old_value:.2f} 회수 → 새 심볼에 ${fixed_amount:.2f} 투자")
        print(f"  💰 거래 수수료: ${total_fee:.2f}")
        print(f"  🌊 시장 상태: {self.market_regime}")
        print(f"  📋 현재 전략: {self.current_strategy}")
        
        return True
    
    def get_top_volume_symbols(self, limit: int = 80) -> List[Dict[str, Any]]:
        """거래량 기준 상위 심볼 조회"""
        print(f"FACT: 거래량 기준 상위 {limit}개 심볼 조회 시작")
        
        usdt_symbols = list(self.supported_symbols)
        symbol_volumes = []
        failed_count = 0
        
        priority_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
            'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT'
        ]
        
        for symbol in priority_symbols:
            if symbol in usdt_symbols:
                try:
                    ticker_url = f"{self.exchange_base_url}/fapi/v1/ticker/24hr?symbol={symbol}"
                    response = requests.get(ticker_url, timeout=5)
                    
                    if response.status_code == 200:
                        ticker_data = response.json()
                        symbol_volume = {
                            "symbol": ticker_data["symbol"],
                            "volume": float(ticker_data["volume"]),
                            "quote_volume": float(ticker_data["quoteVolume"]),
                            "price": float(ticker_data["lastPrice"]),
                            "change_percent": float(ticker_data["priceChangePercent"]),
                            "high": float(ticker_data["highPrice"]),
                            "low": float(ticker_data["lowPrice"])
                        }
                        symbol_volumes.append(symbol_volume)
                        usdt_symbols.remove(symbol)
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
        
        remaining_symbols = usdt_symbols[:limit - len(symbol_volumes)]
        
        for symbol in remaining_symbols:
            try:
                ticker_url = f"{self.exchange_base_url}/fapi/v1/ticker/24hr?symbol={symbol}"
                response = requests.get(ticker_url, timeout=5)
                
                if response.status_code == 200:
                    ticker_data = response.json()
                    symbol_volume = {
                        "symbol": ticker_data["symbol"],
                        "volume": float(ticker_data["volume"]),
                        "quote_volume": float(ticker_data["quoteVolume"]),
                        "price": float(ticker_data["lastPrice"]),
                        "change_percent": float(ticker_data["priceChangePercent"]),
                        "high": float(ticker_data["highPrice"]),
                        "low": float(ticker_data["lowPrice"])
                    }
                    symbol_volumes.append(symbol_volume)
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
        
        symbol_volumes.sort(key=lambda x: x["quote_volume"], reverse=True)
        top_symbols = symbol_volumes[:limit]
        
        for i, symbol in enumerate(top_symbols, 1):
            symbol["rank"] = i
        
        print(f"  📊 성공: {len(top_symbols)}개, 실패: {failed_count}개")
        return top_symbols
    
    def evaluate_bullish_potential_advanced(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """고도화된 상승 가능성 평가"""
        print(f"FACT: 상위 {len(symbols)}개 심볼 상승 가능성 평가 시작")
        
        evaluated_symbols = []
        failed_count = 0
        
        for symbol_data in symbols:
            symbol = symbol_data["symbol"]
            
            try:
                klines_url = f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=100"
                response = requests.get(klines_url, timeout=5)
                
                if response.status_code == 200:
                    klines_data = response.json()
                    closes = [float(kline[4]) for kline in klines_data]
                    volumes = [float(kline[5]) for kline in klines_data]
                    highs = [float(kline[2]) for kline in klines_data]
                    lows = [float(kline[3]) for kline in klines_data]
                    
                    if len(closes) >= 20:
                        indicators = self._calculate_indicators(closes, volumes, highs, lows)
                        bullish_score = self._calculate_bullish_score(symbol_data, indicators)
                        
                        evaluated_symbol = {
                            **symbol_data,
                            **indicators,
                            **bullish_score
                        }
                        evaluated_symbols.append(evaluated_symbol)
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                
            except Exception as e:
                failed_count += 1
        
        evaluated_symbols.sort(key=lambda x: x["bullish_score"], reverse=True)
        
        for i, symbol in enumerate(evaluated_symbols, 1):
            symbol["bullish_rank"] = i
        
        print(f"  📊 평가 성공: {len(evaluated_symbols)}개, 실패: {failed_count}개")
        return evaluated_symbols
    
    def _calculate_indicators(self, closes: List[float], volumes: List[float], highs: List[float], lows: List[float]) -> Dict[str, Any]:
        """기술적 지표 계산"""
        indicators = {}
        indicators["rsi"] = self._calculate_rsi(closes, 14)
        indicators["macd_signal"] = self._calculate_macd_signal(closes)
        indicators["sma_20"] = sum(closes[-20:]) / 20
        indicators["sma_50"] = sum(closes[-50:]) / 50 if len(closes) >= 50 else indicators["sma_20"]
        bb_upper, bb_lower = self._calculate_bollinger_bands(closes, 20)
        indicators["bb_upper"] = bb_upper
        indicators["bb_lower"] = bb_lower
        indicators["volatility"] = self._calculate_volatility(closes)
        indicators["volume_momentum"] = self._calculate_volume_momentum(volumes)
        return indicators
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """RSI 계산"""
        if len(closes) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(-period, 0):
            delta = closes[i] - closes[i-1]
            if delta >= 0:
                gains.append(delta)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(delta))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))
    
    def _calculate_macd_signal(self, closes: List[float]) -> str:
        """MACD 신호 계산"""
        if len(closes) < 26:
            return "NEUTRAL"
        
        ema_12 = sum(closes[-12:]) / 12
        ema_26 = sum(closes[-26:]) / 26
        
        if ema_12 > ema_26:
            return "BULLISH"
        elif ema_12 < ema_26:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _calculate_bollinger_bands(self, closes: List[float], period: int = 20, std_dev: float = 2) -> tuple:
        """볼린저 밴드 계산"""
        if len(closes) < period:
            return closes[-1] * 1.02, closes[-1] * 0.98
        
        sma = sum(closes[-period:]) / period
        variance = sum((price - sma) ** 2 for price in closes[-period:]) / period
        std = variance ** 0.5
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, lower
    
    def _calculate_volatility(self, closes: List[float]) -> float:
        """변동성 계산"""
        if len(closes) < 20:
            return 0.0
        
        returns = []
        for i in range(-20, 0):
            ret = (closes[i] - closes[i-1]) / closes[i-1] * 100
            returns.append(ret)
        
        return statistics.stdev(returns) if len(returns) > 1 else 0.0
    
    def _calculate_volume_momentum(self, volumes: List[float]) -> float:
        """거래량 모멘텀 계산"""
        if len(volumes) < 10:
            return 0.0
        
        recent_avg = sum(volumes[-5:]) / 5
        previous_avg = sum(volumes[-10:-5]) / 5
        
        if previous_avg == 0:
            return 0.0
        
        return ((recent_avg - previous_avg) / previous_avg) * 100
    
    def _calculate_bullish_score(self, symbol_data: Dict, indicators: Dict) -> Dict[str, Any]:
        """상승 가능성 점수 계산"""
        score = 0
        score_breakdown = {}
        
        # 1. 현재 상승률 (25%)
        change_percent = symbol_data["change_percent"]
        if change_percent > 0:
            momentum_score = min(change_percent * 2.5, 25)
        else:
            momentum_score = max(change_percent * 2.5, -10)
        score += momentum_score
        score_breakdown["momentum"] = momentum_score
        
        # 2. RSI 신호 (20%)
        rsi = indicators["rsi"]
        if 30 <= rsi <= 70:
            rsi_score = 20
        elif 20 <= rsi < 30:
            rsi_score = 25
        elif 70 < rsi <= 80:
            rsi_score = 10
        else:
            rsi_score = 0
        score += rsi_score
        score_breakdown["rsi"] = rsi_score
        
        # 3. MACD 신호 (15%)
        macd_signal = indicators["macd_signal"]
        if macd_signal == "BULLISH":
            macd_score = 15
        elif macd_signal == "BEARISH":
            macd_score = -5
        else:
            macd_score = 5
        score += macd_score
        score_breakdown["macd"] = macd_score
        
        # 4. 이동평균 추세 (15%)
        current_price = symbol_data["price"]
        sma_20 = indicators["sma_20"]
        if current_price > sma_20:
            trend_score = 15
        else:
            trend_score = -5
        score += trend_score
        score_breakdown["trend"] = trend_score
        
        # 5. 볼린저 밴드 위치 (10%)
        bb_upper = indicators["bb_upper"]
        bb_lower = indicators["bb_lower"]
        if bb_upper != bb_lower:
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            bb_score = bb_position * 10
        else:
            bb_score = 5
        score += bb_score
        score_breakdown["bollinger"] = bb_score
        
        # 6. 변동성 보너스 (10%)
        volatility = indicators["volatility"]
        volatility_bonus = min(volatility * 2, 10)
        score += volatility_bonus
        score_breakdown["volatility"] = volatility_bonus
        
        # 7. 거래량 모멘텀 (5%)
        volume_momentum = indicators["volume_momentum"]
        volume_score = min(max(volume_momentum / 10, -5), 5)
        score += volume_score
        score_breakdown["volume_momentum"] = volume_score
        
        return {
            "bullish_score": score,
            "score_breakdown": score_breakdown
        }
    
    def calculate_dynamic_take_profit_stop_loss(self, symbol: str, investment: Dict) -> tuple:
        """동적 익절/손절 계산"""
        current_pnl_percent = investment["pnl_percent"]
        
        # 동적 익절 계산
        if self.dynamic_take_profit:
            if self.market_regime == "EXTREME":
                take_profit = self.take_profit_threshold * 0.5  # 극단적 시장: 2.5%
            elif self.market_regime == "HIGH_VOLATILITY":
                take_profit = self.take_profit_threshold * 0.75  # 고변동성: 3.75%
            else:
                take_profit = self.take_profit_threshold  # 정상: 5%
        else:
            take_profit = self.take_profit_threshold
        
        # 동적 손절 계산
        if self.dynamic_stop_loss:
            if self.market_regime == "EXTREME":
                stop_loss = self.stop_loss_threshold * 1.5  # 극단적 시장: -4.5%
            elif self.market_regime == "HIGH_VOLATILITY":
                stop_loss = self.stop_loss_threshold * 1.25  # 고변동성: -3.75%
            else:
                stop_loss = self.stop_loss_threshold  # 정상: -3%
        else:
            stop_loss = self.stop_loss_threshold
        
        return take_profit, stop_loss
    
    def allocate_capital_fixed_amount(self, selected_symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """고정 금액 자본 분배 ($100 per symbol)"""
        print(f"FACT: 고정 금액 자본 분배 시작 ($100 per symbol)")
        
        # 각 심볼당 $100 투자
        fixed_amount = 100.0
        allocations = {}
        
        for symbol_data in selected_symbols:
            symbol = symbol_data["symbol"]
            
            # $100 고정 할당
            allocation = fixed_amount
            
            # 총 자본 확인
            if len(allocations) * fixed_amount > self.total_capital:
                print(f"  ⚠️ 총 자본 초과: {len(allocations)}개 심볼 x ${fixed_amount} = ${len(allocations) * fixed_amount}")
                print(f"  ⚠️ 현재 자본: ${self.total_capital}")
                break
            
            allocations[symbol] = {
                "allocation": allocation,
                "percentage": (allocation / self.total_capital) * 100,
                "symbol_data": symbol_data,
                "profit_potential": symbol_data.get("profit_potential", 0),
                "fixed_amount": True
            }
        
        print(f"  ✅ {len(allocations)}개 심볼에 ${len(allocations) * fixed_amount:.2f} 분배 완료")
        print(f"  📊 심볼당 고정 금액: ${fixed_amount:.2f}")
        print(f"  💰 남은 자본: ${self.total_capital - (len(allocations) * fixed_amount):.2f}")
        
        return allocations
    
    def initialize_investments(self, allocations: Dict[str, Any]):
        """투자 초기화"""
        print(f"FACT: 투자 포지션 초기화")
        
        self.investments = {}
        
        for symbol, allocation_data in allocations.items():
            symbol_data = allocation_data["symbol_data"]
            allocation = allocation_data["allocation"]
            
            # 거래 수수료 계산
            fee = allocation * self.trading_fee
            net_investment = allocation - fee
            
            price = symbol_data["price"]
            shares = net_investment / price
            
            self.investments[symbol] = {
                "initial_investment": allocation,
                "net_investment": net_investment,
                "current_investment": net_investment,
                "initial_price": price,
                "current_price": price,
                "shares": shares,
                "initial_time": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat(),
                "pnl": 0.0,
                "pnl_percent": 0.0,
                "rank": symbol_data.get("bullish_rank", 1),  # 기본값 1
                "bullish_score": symbol_data["bullish_score"],
                "fees_paid": fee,
                "take_profit": self.take_profit_threshold,
                "stop_loss": self.stop_loss_threshold,
                "profit_potential": symbol_data.get("profit_potential", 50)
            }
        
        self.total_fees_paid = len(allocations) * allocation * self.trading_fee
        print(f"  ✅ {len(self.investments)}개 심볼 투자 초기화 완료")
        print(f"  💰 초기 수수료: ${self.total_fees_paid:.2f}")
    
    def update_investment_performance(self):
        """투자 성과 업데이트"""
        total_value = 0
        total_pnl = 0
        total_fees = 0
        
        for symbol, investment in self.investments.items():
            try:
                ticker_url = f"{self.exchange_base_url}/fapi/v1/ticker/24hr?symbol={symbol}"
                response = requests.get(ticker_url, timeout=5)
                
                if response.status_code == 200:
                    ticker_data = response.json()
                    current_price = float(ticker_data["lastPrice"])
                else:
                    current_price = investment["current_price"]
                
                # 동적 익절/손절 계산
                take_profit, stop_loss = self.calculate_dynamic_take_profit_stop_loss(symbol, investment)
                investment["take_profit"] = take_profit
                investment["stop_loss"] = stop_loss
                
                # 성과 계산
                current_value = investment["shares"] * current_price
                pnl = current_value - investment["net_investment"]
                pnl_percent = (pnl / investment["net_investment"]) * 100
                
                # 익절/손절 확인
                should_close = False
                close_reason = ""
                
                # 상승 가능성 재평가 (익절/손절 전에 확인)
                symbol_data = None
                for evaluated in self.evaluated_symbols:
                    if evaluated["symbol"] == symbol:
                        symbol_data = evaluated
                        break
                
                if symbol_data:
                    current_potential = self._calculate_profit_potential(symbol_data)
                    current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
                    
                    # 상승 가능성이 기준 이상이면 익절/손절하지 않음
                    if current_potential >= current_threshold:
                        should_close = False
                        close_reason = "HIGH_POTENTIAL_CONTINUE"
                        print(f"  🛡️ {symbol}: 상승 가능성 {current_potential:.1f}% >= {current_threshold}% - 익절/손절하지 않고 계속 진행")
                    else:
                        # 상승 가능성이 기준 미만이면 기존 익절/손절 로직 적용
                        if pnl_percent >= take_profit:
                            should_close = True
                            close_reason = "TAKE_PROFIT"
                        elif pnl_percent <= stop_loss:
                            should_close = True
                            close_reason = "STOP_LOSS"
                else:
                    # 상승 가능성 데이터 없으면 기존 로직 적용
                    if pnl_percent >= take_profit:
                        should_close = True
                        close_reason = "TAKE_PROFIT"
                    elif pnl_percent <= stop_loss:
                        should_close = True
                        close_reason = "STOP_LOSS"
                
                # 투자 정보 업데이트
                investment["current_price"] = current_price
                investment["current_investment"] = current_value
                investment["pnl"] = pnl
                investment["pnl_percent"] = pnl_percent
                investment["last_update"] = datetime.now().isoformat()
                investment["should_close"] = should_close
                investment["close_reason"] = close_reason
                
                total_value += current_value
                total_pnl += pnl
                
            except Exception as e:
                print(f"  ❌ {symbol} 성과 업데이트 실패: {e}")
        
        self.current_capital = total_value
        
        # 성과 기록
        performance_record = {
            "timestamp": datetime.now().isoformat(),
            "total_value": total_value,
            "total_pnl": total_pnl,
            "pnl_percent": (total_pnl / self.initial_capital) * 100,
            "market_regime": self.market_regime,
            "strategy": self.current_strategy,
            "total_fees_paid": self.total_fees_paid,
            "net_pnl": total_pnl - self.total_fees_paid,
            "net_pnl_percent": ((total_pnl - self.total_fees_paid) / self.initial_capital) * 100,
            "individual_performance": {
                symbol: {
                    "pnl": investment["pnl"],
                    "pnl_percent": investment["pnl_percent"],
                    "take_profit": investment["take_profit"],
                    "stop_loss": investment["stop_loss"],
                    "should_close": investment.get("should_close", False),
                    "close_reason": investment.get("close_reason", "")
                }
                for symbol, investment in self.investments.items()
            }
        }
        
        self.performance_history.append(performance_record)
        
        return performance_record
    
    def run_improved_real_market_simulation(self, duration_minutes: int = 720, update_interval: int = 5):
        """개선된 실전 시장 시뮬레이션 실행"""
        print(f"FACT: 개선된 실전 시장 시뮬레이션 v5.0 시작")
        print(f"  💰 초기 자본: ${self.total_capital:.2f}")
        print(f"  🎯 투자 전략: 선택적 심볼 + 개선된 동적 교체")
        print(f"  ⏰ 시뮬레이션 기간: {duration_minutes}분")
        print(f"  🔄 업데이트 주기: {update_interval}분")
        print(f"  📉 교체 기준: {self.performance_threshold}% 이하")
        print(f"  🎯 익절/손절: 동적 자동 평가")
        print(f"  💰 거래 수수료: {self.trading_fee*100:.2f}% 포함")
        print(f"  🔧 개선 사항: 교체 빈도 제어, 수수료 효율성, 반복 방지")
        
        # 1. 거래량 기준 상위 심볼 조회
        top_volume_symbols = self.get_top_volume_symbols(80)
        
        if not top_volume_symbols:
            print("❌ 상위 심볼 조회 실패")
            return
        
        # 2. 상승 가능성 평가
        self.evaluated_symbols = self.evaluate_bullish_potential_advanced(top_volume_symbols)
        
        if not self.evaluated_symbols:
            print("❌ 상승 가능성 평가 실패")
            return
        
        # 3. 수익 가능성 평가
        profitable_symbols = self.evaluate_profitability_potential(self.evaluated_symbols)
        
        if not profitable_symbols:
            print("❌ 수익 가능성 있는 심볼 없음")
            return
        
        # 4. 최적 심볼 선택
        print(f"  📋 최적 심볼 선택 전 상태:")
        print(f"    - profitable_symbols 개수: {len(profitable_symbols)}")
        if profitable_symbols:
            for i, symbol in enumerate(profitable_symbols[:5], 1):
                print(f"    {i}. {symbol['symbol']}: {symbol['profit_potential']:.1f}%")
        
        selected_symbols = self.select_optimal_symbols(profitable_symbols)
        
        print(f"  📋 최적 심볼 선택 후 상태:")
        print(f"    - selected_symbols 개수: {len(selected_symbols)}")
        
        if not selected_symbols:
            print("  ❌ 선택된 심볼 없음")
            print("  🔄 교체주기마다 재평가하여 추가/교체/배재 진행")
            return None
        else:
            print(f"  ✅ {len(selected_symbols)}개 심볼 선택됨 - 초기화 진행")
        
        # 5. 자본 분배
        allocations = self.allocate_capital_fixed_amount(selected_symbols)
        
        # 6. 투자 초기화
        self.initialize_investments(allocations)
        
        # 7. 시뮬레이션 실행
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        print(f"\n🚀 개선된 실전 시장 시뮬레이션 실행 시작")
        print("=" * 80)
        
        iteration = 0
        max_iterations = duration_minutes // update_interval
        
        while datetime.now() < end_time and iteration < max_iterations:
            iteration += 1
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            print(f"\n🔄 라운드 {iteration}/{max_iterations} 시작 - {elapsed.total_seconds():.0f}초 경과")
            
            # 시장 변동성 분석
            market_regime = self.analyze_market_volatility_enhanced()
            print(f"  🌊 시장 상태: {market_regime}")
            
            # 동적 전략 로드
            strategy = self.load_dynamic_strategy(market_regime)
            
            # 성과 업데이트
            performance = self.update_investment_performance()
            
            print(f"  💰 총 자산: ${performance['total_value']:.2f}")
            print(f"  📈 총 손익: ${performance['total_pnl']:+.2f} ({performance['pnl_percent']:+.2f}%)")
            print(f"  💰 총 수수료: ${performance['total_fees_paid']:.2f}")
            print(f"  📈 순 손익: ${performance['net_pnl']:+.2f} ({performance['net_pnl_percent']:+.2f}%)")
            print(f"  📋 현재 전략: {self.current_strategy}")
            
            # 현재 투자 심볼 성과
            current_performance = []
            for symbol, investment in self.investments.items():
                current_performance.append({
                    "symbol": symbol,
                    "pnl": investment["pnl"],
                    "pnl_percent": investment["pnl_percent"],
                    "take_profit": investment["take_profit"],
                    "stop_loss": investment["stop_loss"],
                    "should_close": investment.get("should_close", False),
                    "close_reason": investment.get("close_reason", ""),
                    "profit_potential": investment.get("profit_potential", 50)
                })
            
            current_performance.sort(key=lambda x: x["pnl_percent"], reverse=True)
            
            print(f"  🏆 현재 투자 심볼 성과:")
            for i, perf in enumerate(current_performance, 1):
                emoji = "📈" if perf['pnl_percent'] > 0 else "📉" if perf['pnl_percent'] < 0 else "➡️"
                close_info = ""
                if perf['should_close']:
                    close_info = f" [{perf['close_reason']}]"
                print(f"    {i}. {emoji} {perf['symbol']}: ${perf['pnl']:+.2f} ({perf['pnl_percent']:+.2f}%){close_info}")
            
            # 개선된 동적 교체 확인
            replacement_made = self.replace_underperforming_symbol_improved()
            if replacement_made:
                print(f"  🔄 개선된 동적 교체 발생!")
            
            # 동적 포트폴리오 리밸런싱 (매 라운드마다)
            rebalancing_made = self.dynamic_portfolio_rebalancing()
            if rebalancing_made:
                print(f"  🔄 동적 포트폴리오 리밸런싱 발생!")
            elif len(self.investments) == 0:
                print(f"  ⚠️ 현재 투자 심볼 없음 - 다음 라운드에 재평가")
            
            # 실시간 상승 가능성 평가
            self.update_real_time_profit_potential()
            
            # 다음 라운드까지 남은 시간 계산
            time_until_next = update_interval * 60
            print(f"  ⏱️ 다음 라운드까지 {update_interval}분 대기...")
            
            # 대기
            time.sleep(time_until_next)
        
        # 최종 결과
        final_result = self._generate_final_report()
        
        return final_result
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """최종 보고서 생성"""
        print(f"\n🎯 최종 개선된 실전 시장 투자 시뮬레이션 보고서 생성")
        
        if not self.performance_history:
            return {"error": "성과 기록이 없습니다"}
        
        final_performance = self.performance_history[-1]
        
        # 개별 심볼 성과 정렬
        individual_performance = []
        for symbol, investment in self.investments.items():
            individual_performance.append({
                "symbol": symbol,
                "initial_investment": investment["initial_investment"],
                "net_investment": investment["net_investment"],
                "final_investment": investment["current_investment"],
                "pnl": investment["pnl"],
                "pnl_percent": investment["pnl_percent"],
                "rank": investment["rank"],
                "bullish_score": investment["bullish_score"],
                "fees_paid": investment["fees_paid"],
                "take_profit": investment["take_profit"],
                "stop_loss": investment["stop_loss"],
                "profit_potential": investment.get("profit_potential", 50)
            })
        
        individual_performance.sort(key=lambda x: x["pnl_percent"], reverse=True)
        
        return {
            "simulation_metadata": {
                "initial_capital": self.initial_capital,
                "final_capital": self.current_capital,
                "total_pnl": final_performance["total_pnl"],
                "pnl_percent": final_performance["pnl_percent"],
                "total_fees_paid": self.total_fees_paid,
                "net_pnl": final_performance["net_pnl"],
                "net_pnl_percent": final_performance["net_pnl_percent"],
                "start_time": self.performance_history[0]["timestamp"],
                "end_time": final_performance["timestamp"],
                "total_rounds": len(self.performance_history),
                "invested_symbols": len(self.investments),
                "max_symbols": self.max_symbols,
                "total_replacements": len(self.replacement_history),
                "replacement_threshold": self.performance_threshold,
                "trading_fee": self.trading_fee,
                "take_profit_threshold": self.take_profit_threshold,
                "stop_loss_threshold": self.stop_loss_threshold,
                "dynamic_take_profit": self.dynamic_take_profit,
                "dynamic_stop_loss": self.dynamic_stop_loss,
                "final_market_regime": self.market_regime,
                "final_strategy": self.current_strategy,
                "min_replacement_interval": self.min_replacement_interval,
                "max_replacements_per_hour": self.max_replacements_per_hour,
                "max_replacements_per_day": self.max_replacements_per_day,
                "profitability_threshold": self.profitability_threshold,
                "market_state_changes": len(set(h["regime"] for h in self.market_state_history))
            },
            "individual_performance": individual_performance,
            "replacement_history": self.replacement_history,
            "performance_history": self.performance_history,
            "market_regime_history": [p.get("market_regime", "NORMAL") for p in self.performance_history],
            "strategy_history": [p.get("strategy", "balanced") for p in self.performance_history],
            "market_state_history": self.market_state_history
        }

def main():
    """메인 실행 함수"""
    print("🎯 개선된 실전 테스트용 최종 동적 투자 검증 시뮬레이터 v5.0")
    print("개선된 특징:")
    print("  📊 실제 시장 데이터만 사용")
    print("  ⏰ 12시간 테스트")
    print("  💰 거래 수수료 포함")
    print("  🎯 익절/손절 동적 자동 평가")
    print("  🔄 개선된 실전 동적 교체")
    print("  🔧 교체 빈도 제어")
    print("  💰 수수료 효율성 최적화")
    print("  🌊 시장 상태 감지 강화")
    print("  🚫 반복적 교체 방지")
    print("  📊 수익 가능성 평가 후 선택적 투자")
    print("  🔄 동적 전략 로드 시스템")
    print()
    
    # 개선된 실전 테스트 시뮬레이터 생성
    simulator = ImprovedRealMarketDynamicInvestmentSimulator(
        symbol_count=10,  # 최대 10개 심볼
        replacement_threshold=-0.8  # -0.8% 교체 기준
    )
    
    # 30분 시뮬레이션 실행
    result = simulator.run_improved_real_market_simulation(duration_minutes=30, update_interval=5)
    
    if "error" not in result:
        # 최종 결과 출력
        print("\n" + "=" * 80)
        print("🎯 최종 개선된 실전 시장 투자 시뮬레이션 결과")
        print("=" * 80)
        
        metadata = result["simulation_metadata"]
        print(f"\n📋 시뮬레이션 정보:")
        print(f"  💰 초기 자본: ${metadata['initial_capital']:.2f}")
        print(f"  💰 최종 자본: ${metadata['final_capital']:.2f}")
        print(f"  📈 총 손익: ${metadata['total_pnl']:+.2f}")
        print(f"  📊 손익률: {metadata['pnl_percent']:+.2f}%")
        print(f"  💰 총 수수료: ${metadata['total_fees_paid']:.2f}")
        print(f"  📈 순 손익: ${metadata['net_pnl']:+.2f}")
        print(f"  📊 순 손익률: {metadata['net_pnl_percent']:+.2f}%")
        print(f"  ⏰ 시작 시간: {metadata['start_time']}")
        print(f"  ⏰ 종료 시간: {metadata['end_time']}")
        print(f"  🔢 총 라운드: {metadata['total_rounds']}")
        print(f"  🎯 투자 심볼: {metadata['invested_symbols']}/{metadata['max_symbols']}개")
        print(f"  🔄 총 교체 횟수: {metadata['total_replacements']}")
        print(f"  📉 교체 기준: {metadata['replacement_threshold']}%")
        print(f"  💰 거래 수수료: {metadata['trading_fee']*100:.2f}%")
        print(f"  🎯 익절 기준: {metadata['take_profit_threshold']}%")
        print(f"  📉 손절 기준: {metadata['stop_loss_threshold']}%")
        print(f"  🌊 최종 시장 상태: {metadata['final_market_regime']}")
        print(f"  📋 최종 전략: {metadata['final_strategy']}")
        print(f"  ⏰ 최소 교체 간격: {metadata['min_replacement_interval']}분")
        print(f"  📊 시간당 최대 교체: {metadata['max_replacements_per_hour']}회")
        print(f"  📊 일일 최대 교체: {metadata['max_replacements_per_day']}회")
        print(f"  📊 수익 가능성 기준: {metadata['profitability_threshold']}점")
        print(f"  🌊 시장 상태 변화: {metadata['market_state_changes']}개")
        
        # 상위 심볼 성과
        print(f"\n🏆 최종 심볼 성과:")
        for i, perf in enumerate(result["individual_performance"], 1):
            emoji = "📈" if perf['pnl_percent'] > 5 else "📉" if perf['pnl_percent'] < -3 else "➡️"
            print(f"  {i}. {emoji} {perf['symbol']}: ${perf['pnl']:+.2f} ({perf['pnl_percent']:+.2f}%) - 순위: {perf['rank']}, 수익 가능성: {perf['profit_potential']:.1f}")
        
        # 교체 기록
        if result["replacement_history"]:
            print(f"\n🔄 교체 기록:")
            for i, replacement in enumerate(result["replacement_history"][-10:], 1):  # 최근 10개만 표시
                print(f"  {i}. {replacement['old_symbol']} → {replacement['new_symbol']}")
                print(f"     기존 성과: {replacement['old_performance']:+.2f}%")
                print(f"     교체 사유: {replacement['old_close_reason']}")
                print(f"     새 점수: {replacement['new_bullish_score']:.1f}")
                print(f"     수익 가능성: {replacement.get('new_profit_potential', 0):.1f}")
                print(f"     이전 금액: ${replacement['transferred_amount']:.2f}")
                print(f"     거래 수수료: ${replacement['total_fee']:.2f}")
                print(f"     시장 상태: {replacement['market_regime']}")
                print(f"     전략: {replacement['strategy']}")
        
        # 시장 상태 변화
        market_regimes = result["market_regime_history"]
        regime_changes = {}
        for regime in market_regimes:
            regime_changes[regime] = regime_changes.get(regime, 0) + 1
        
        print(f"\n🌊 시장 상태 분석:")
        for regime, count in regime_changes.items():
            percentage = (count / len(market_regimes)) * 100
            print(f"  {regime}: {count}회 ({percentage:.1f}%)")
        
        # 전략 사용 분석
        strategies = result["strategy_history"]
        strategy_usage = {}
        for strategy in strategies:
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        print(f"\n📋 전략 사용 분석:")
        for strategy, count in strategy_usage.items():
            percentage = (count / len(strategies)) * 100
            print(f"  {strategy}: {count}회 ({percentage:.1f}%)")
        
        # 결과 저장
        results_file = Path("improved_real_market_simulation_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과 저장: {results_file}")
    else:
        print(f"❌ 시뮬레이션 실패: {result['error']}")

if __name__ == "__main__":
    main()
