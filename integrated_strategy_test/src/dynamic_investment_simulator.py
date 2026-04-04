"""
6시간 실제 투자 검증 시스템 (수정 버전)
5개 심볼만 투자 + 동적 교체 시스템
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any
import statistics

# 프로젝트 루트 설정
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

class DynamicInvestmentSimulator:
    """동적 투자 시뮬레이터 (5개 심볼 + 동적 교체)"""
    
    def __init__(self):
        self.total_capital = 500.0  # 총 자본 $500
        self.initial_capital = 500.0
        self.current_capital = 500.0
        self.max_symbols = 5  # 최대 5개 심볼만 투자
        self.investments = {}  # 심볼별 투자 정보
        self.performance_history = []  # 성과 기록
        self.replacement_history = []  # 교체 기록
        self.exchange_base_url = "https://demo-fapi.binance.com"
        self.supported_symbols = set()
        self.evaluated_symbols = []  # 평가된 모든 심볼 목록
        
        # 동적 교체 파라미터
        self.performance_threshold = -2.0  # -2% 이하면 교체
        self.min_replacement_interval = 10  # 최소 10분 간격 교체
        self.last_replacement_time = None
        
        print(f"FACT: 동적 투자 시뮬레이터 초기화")
        print(f"  💰 초기 자본: ${self.total_capital:.2f}")
        print(f"  🎯 투자 전략: 5개 심볼 + 동적 교체")
        print(f"  🔄 교체 기준: {self.performance_threshold}% 이하")
        print(f"  📊 대상 심볼: 거래량 기준 상위 80개")
        
        # 지원 심볼 로드
        self._load_supported_symbols()
    
    def _load_supported_symbols(self):
        """지원 심볼 목록 로드"""
        try:
            response = requests.get(f"{self.exchange_base_url}/fapi/v1/exchangeInfo", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 심볼 필터링: USDT 종목만, 상태가 TRADING인 것만
                filtered_symbols = []
                for s in data['symbols']:
                    if (s['symbol'].endswith('USDT') and 
                        s['status'] == 'TRADING' and 
                        s['contractType'] == 'PERPETUAL'):
                        filtered_symbols.append(s['symbol'])
                
                self.supported_symbols = set(filtered_symbols)
                print(f"  🔢 지원 심볼: {len(self.supported_symbols)}개 로드 완료")
                print(f"  📊 필터링: USDT + TRADING + PERPETUAL")
            else:
                print(f"  ⚠️ 심볼 목록 로드 실패: {response.status_code}")
                # fallback: 기본 심볼 목록
                fallback_symbols = [
                    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
                    'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT',
                    'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'FILUSDT'
                ]
                self.supported_symbols = set(fallback_symbols)
                print(f"  🔄 Fallback: {len(self.supported_symbols)}개 기본 심볼 사용")
        except Exception as e:
            print(f"  ❌ 심볼 목록 로드 오류: {e}")
            # fallback: 기본 심볼 목록
            fallback_symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
                'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT',
                'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'FILUSDT'
            ]
            self.supported_symbols = set(fallback_symbols)
            print(f"  🔄 Fallback: {len(self.supported_symbols)}개 기본 심볼 사용")
    
    def get_top_volume_symbols(self, limit: int = 80) -> List[Dict[str, Any]]:
        """거래량 기준 상위 심볼 조회"""
        print(f"FACT: 거래량 기준 상위 {limit}개 심볼 조회 시작")
        
        # USDT 종목만 필터링 (이미 필터링되어 있음)
        usdt_symbols = list(self.supported_symbols)
        print(f"  🔢 USDT 심볼: {len(usdt_symbols)}개")
        
        symbol_volumes = []
        failed_count = 0
        
        # 실제 거래량이 많은 주요 심볼 우선 조회
        priority_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
            'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT',
            'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'FILUSDT'
        ]
        
        # 우선 심볼 먼저 조회
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
                        usdt_symbols.remove(symbol)  # 중복 조회 방지
                    else:
                        failed_count += 1
                        print(f"  ⚠️ {symbol} 티커 조회 실패: {response.status_code}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"  ❌ {symbol} 조회 실패: {e}")
        
        # 나머지 심볼 조회
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
                    print(f"  ⚠️ {symbol} 티커 조회 실패: {response.status_code}")
                    
            except Exception as e:
                failed_count += 1
                print(f"  ❌ {symbol} 조회 실패: {e}")
        
        print(f"  📊 성공: {len(symbol_volumes)}개, 실패: {failed_count}개")
        
        # 거래량 기준 정렬
        symbol_volumes.sort(key=lambda x: x["quote_volume"], reverse=True)
        
        # 상위 N개 선택
        top_symbols = symbol_volumes[:limit]
        
        # 순위 매기기
        for i, symbol in enumerate(top_symbols, 1):
            symbol["rank"] = i
        
        print(f"  ✅ 상위 {len(top_symbols)}개 심볼 선택 완료")
        
        return top_symbols
    
    def evaluate_bullish_potential_advanced(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """고도화된 상승 가능성 평가"""
        print(f"FACT: 상위 {len(symbols)}개 심볼 상승 가능성 평가 시작")
        
        evaluated_symbols = []
        failed_count = 0
        
        for symbol_data in symbols:
            symbol = symbol_data["symbol"]
            
            try:
                # 기술적 지표 계산을 위한 과거 데이터 조회
                klines_url = f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=100"
                response = requests.get(klines_url, timeout=5)
                
                if response.status_code == 200:
                    klines_data = response.json()
                    
                    # 데이터 파싱
                    closes = [float(kline[4]) for kline in klines_data]
                    volumes = [float(kline[5]) for kline in klines_data]
                    highs = [float(kline[2]) for kline in klines_data]
                    lows = [float(kline[3]) for kline in klines_data]
                    
                    if len(closes) >= 20:
                        # 기술적 지표 계산
                        indicators = self._calculate_indicators(closes, volumes, highs, lows)
                        
                        # 상승 가능성 점수 계산
                        bullish_score = self._calculate_bullish_score(
                            symbol_data, indicators
                        )
                        
                        evaluated_symbol = {
                            **symbol_data,
                            **indicators,
                            **bullish_score
                        }
                        
                        evaluated_symbols.append(evaluated_symbol)
                    else:
                        print(f"  ⚠️ {symbol}: 데이터 부족 ({len(closes)}개 봉)")
                        failed_count += 1
                else:
                    print(f"  ⚠️ {symbol}: 과거 데이터 조회 실패 ({response.status_code})")
                    failed_count += 1
                
            except Exception as e:
                print(f"  ❌ {symbol} 평가 실패: {e}")
                failed_count += 1
        
        # 상승 가능성 점수순으로 정렬
        evaluated_symbols.sort(key=lambda x: x["bullish_score"], reverse=True)
        
        # 순위 재매기기
        for i, symbol in enumerate(evaluated_symbols, 1):
            symbol["bullish_rank"] = i
        
        print(f"  📊 평가 성공: {len(evaluated_symbols)}개, 실패: {failed_count}개")
        print(f"  ✅ {len(evaluated_symbols)}개 심볼 상승 가능성 평가 완료")
        
        return evaluated_symbols
    
    def _calculate_indicators(self, closes: List[float], volumes: List[float], highs: List[float], lows: List[float]) -> Dict[str, Any]:
        """기술적 지표 계산"""
        indicators = {}
        
        # RSI 계산
        indicators["rsi"] = self._calculate_rsi(closes, 14)
        
        # MACD 신호 계산 (단순화)
        indicators["macd_signal"] = self._calculate_macd_signal(closes)
        
        # 이동평균 계산
        indicators["sma_20"] = sum(closes[-20:]) / 20
        indicators["sma_50"] = sum(closes[-50:]) / 50 if len(closes) >= 50 else indicators["sma_20"]
        
        # 볼린저 밴드 계산
        bb_upper, bb_lower = self._calculate_bollinger_bands(closes, 20)
        indicators["bb_upper"] = bb_upper
        indicators["bb_lower"] = bb_lower
        
        # 변동성 계산
        indicators["volatility"] = self._calculate_volatility(closes)
        
        # 거래량 모멘텀
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
        """MACD 신호 계산 (단순화)"""
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
    
    def allocate_capital_equal(self, top_symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """5개 심볼에 균등 자본 분배"""
        print(f"FACT: 상위 {self.max_symbols}개 심볼에 균등 자본 분배")
        
        # 상위 5개 심볼 선택
        selected_symbols = top_symbols[:self.max_symbols]
        
        # 균등 분배
        equal_allocation = self.total_capital / self.max_symbols
        
        allocations = {}
        for symbol_data in selected_symbols:
            symbol = symbol_data["symbol"]
            allocations[symbol] = {
                "allocation": equal_allocation,
                "percentage": 100.0 / self.max_symbols,
                "symbol_data": symbol_data
            }
        
        print(f"  ✅ {len(allocations)}개 심볼에 ${self.total_capital:.2f} 균등 분배 완료")
        print(f"  💰 각 심볼: ${equal_allocation:.2f} ({100.0/self.max_symbols:.1f}%)")
        
        return allocations
    
    def initialize_investments(self, allocations: Dict[str, Any]):
        """투자 초기화"""
        print(f"FACT: 투자 포지션 초기화")
        
        self.investments = {}
        
        for symbol, allocation_data in allocations.items():
            symbol_data = allocation_data["symbol_data"]
            allocation = allocation_data["allocation"]
            
            # 주식 수 계산
            price = symbol_data["price"]
            shares = allocation / price
            
            self.investments[symbol] = {
                "initial_investment": allocation,
                "current_investment": allocation,
                "initial_price": price,
                "current_price": price,
                "shares": shares,
                "initial_time": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat(),
                "pnl": 0.0,
                "pnl_percent": 0.0,
                "rank": symbol_data["bullish_rank"],
                "bullish_score": symbol_data["bullish_score"]
            }
        
        print(f"  ✅ {len(self.investments)}개 심볼 투자 초기화 완료")
    
    def update_investment_performance(self):
        """투자 성과 업데이트"""
        total_value = 0
        total_pnl = 0
        
        for symbol, investment in self.investments.items():
            try:
                # 현재 가격 조회
                ticker_url = f"{self.exchange_base_url}/fapi/v1/ticker/24hr?symbol={symbol}"
                response = requests.get(ticker_url, timeout=5)
                
                if response.status_code == 200:
                    ticker_data = response.json()
                    current_price = float(ticker_data["lastPrice"])
                    
                    # 성과 계산
                    current_value = investment["shares"] * current_price
                    pnl = current_value - investment["initial_investment"]
                    pnl_percent = (pnl / investment["initial_investment"]) * 100
                    
                    # 투자 정보 업데이트
                    investment["current_price"] = current_price
                    investment["current_investment"] = current_value
                    investment["pnl"] = pnl
                    investment["pnl_percent"] = pnl_percent
                    investment["last_update"] = datetime.now().isoformat()
                    
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
            "individual_performance": {
                symbol: {
                    "pnl": investment["pnl"],
                    "pnl_percent": investment["pnl_percent"]
                }
                for symbol, investment in self.investments.items()
            }
        }
        
        self.performance_history.append(performance_record)
        
        return performance_record
    
    def should_replace_symbol(self, symbol: str) -> bool:
        """심볼 교체 필요 여부 판단"""
        if symbol not in self.investments:
            return False
        
        investment = self.investments[symbol]
        current_pnl_percent = investment["pnl_percent"]
        
        # 교체 기준 확인
        if current_pnl_percent <= self.performance_threshold:
            # 최소 교체 간격 확인
            if self.last_replacement_time is None:
                time_since_last = float('inf')
            else:
                time_since_last = (datetime.now() - self.last_replacement_time).total_seconds()
            
            if time_since_last >= self.min_replacement_interval * 60:
                return True
        
        return False
    
    def replace_underperforming_symbol(self):
        """부진 심볼 교체"""
        print(f"FACT: 부진 심볼 교체 프로세스 시작")
        
        # 교체 대상 심볼 찾기
        underperforming_symbols = []
        for symbol in self.investments.keys():
            if self.should_replace_symbol(symbol):
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
        
        # 교체할 심볼 선택 (현재 투자 중인 심볼 제외)
        available_symbols = [
            s for s in self.evaluated_symbols 
            if s["symbol"] not in self.investments
        ]
        
        if not available_symbols:
            print("  ⚠️ 교체 가능한 심볼 없음")
            return False
        
        # 가장 높은 상승 가능성 점수 심볼 선택
        best_replacement = available_symbols[0]
        
        print(f"  🎯 교체 심볼: {best_replacement['symbol']} (점수: {best_replacement['bullish_score']:.1f})")
        
        # 교체 실행
        old_investment = self.investments[worst_symbol]
        old_value = old_investment["current_investment"]
        
        # 기존 심볼 제거
        del self.investments[worst_symbol]
        
        # 새 심볼 추가
        new_price = best_replacement["price"]
        new_shares = old_value / new_price
        
        self.investments[best_replacement["symbol"]] = {
            "initial_investment": old_value,
            "current_investment": old_value,
            "initial_price": new_price,
            "current_price": new_price,
            "shares": new_shares,
            "initial_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "pnl": 0.0,
            "pnl_percent": 0.0,
            "rank": best_replacement["bullish_rank"],
            "bullish_score": best_replacement["bullish_score"]
        }
        
        # 교체 기록
        replacement_record = {
            "timestamp": datetime.now().isoformat(),
            "old_symbol": worst_symbol,
            "new_symbol": best_replacement["symbol"],
            "old_performance": worst_performance,
            "new_bullish_score": best_replacement["bullish_score"],
            "transferred_amount": old_value
        }
        
        self.replacement_history.append(replacement_record)
        self.last_replacement_time = datetime.now()
        
        print(f"  ✅ 교체 완료: {worst_symbol} → {best_replacement['symbol']}")
        print(f"  💰 이전 금액: ${old_value:.2f} → 새 심볼에 투자")
        
        return True
    
    def run_dynamic_investment_simulation(self, duration_minutes: int = 360, update_interval: int = 10):
        """동적 투자 시뮬레이션 실행"""
        print(f"FACT: 동적 투자 시뮬레이션 시작")
        print(f"  💰 초기 자본: ${self.total_capital:.2f}")
        print(f"  🎯 투자 전략: 5개 심볼 + 동적 교체")
        print(f"  ⏰ 시뮬레이션 기간: {duration_minutes}분")
        print(f"  🔄 업데이트 주기: {update_interval}분")
        print(f"  📉 교체 기준: {self.performance_threshold}% 이하")
        
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
        
        # 3. 자본 분배 (5개 심볼 균등 분배)
        allocations = self.allocate_capital_equal(self.evaluated_symbols)
        
        # 4. 투자 초기화
        self.initialize_investments(allocations)
        
        # 5. 시뮬레이션 실행
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        print(f"\n🚀 동적 투자 시뮬레이션 실행 시작")
        print("=" * 80)
        
        iteration = 0
        max_iterations = duration_minutes // update_interval  # 최대 반복 횟수 계산
        
        while datetime.now() < end_time and iteration < max_iterations:
            iteration += 1
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            print(f"\n🔄 라운드 {iteration}/{max_iterations} 시작 - {elapsed.total_seconds():.0f}초 경과")
            
            # 성과 업데이트
            performance = self.update_investment_performance()
            
            print(f"  💰 총 자산: ${performance['total_value']:.2f}")
            print(f"  📈 총 손익: ${performance['total_pnl']:+.2f} ({performance['pnl_percent']:+.2f}%)")
            
            # 현재 투자 심볼 성과
            current_performance = []
            for symbol, investment in self.investments.items():
                current_performance.append({
                    "symbol": symbol,
                    "pnl": investment["pnl"],
                    "pnl_percent": investment["pnl_percent"]
                })
            
            current_performance.sort(key=lambda x: x["pnl_percent"], reverse=True)
            
            print(f"  🏆 현재 투자 심볼 성과:")
            for i, perf in enumerate(current_performance, 1):
                emoji = "📈" if perf['pnl_percent'] > 0 else "📉" if perf['pnl_percent'] < 0 else "➡️"
                print(f"    {i}. {emoji} {perf['symbol']}: ${perf['pnl']:+.2f} ({perf['pnl_percent']:+.2f}%)")
            
            # 동적 교체 확인
            replacement_made = self.replace_underperforming_symbol()
            if replacement_made:
                print(f"  🔄 동적 교체 발생!")
            
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
        print(f"\n🎯 최종 동적 투자 시뮬레이션 보고서 생성")
        
        if not self.performance_history:
            return {"error": "성과 기록이 없습니다"}
        
        final_performance = self.performance_history[-1]
        
        # 개별 심볼 성과 정렬
        individual_performance = []
        for symbol, investment in self.investments.items():
            individual_performance.append({
                "symbol": symbol,
                "initial_investment": investment["initial_investment"],
                "final_investment": investment["current_investment"],
                "pnl": investment["pnl"],
                "pnl_percent": investment["pnl_percent"],
                "rank": investment["rank"],
                "bullish_score": investment["bullish_score"]
            })
        
        individual_performance.sort(key=lambda x: x["pnl_percent"], reverse=True)
        
        return {
            "simulation_metadata": {
                "initial_capital": self.initial_capital,
                "final_capital": self.current_capital,
                "total_pnl": final_performance["total_pnl"],
                "pnl_percent": final_performance["pnl_percent"],
                "start_time": self.performance_history[0]["timestamp"],
                "end_time": final_performance["timestamp"],
                "total_rounds": len(self.performance_history),
                "invested_symbols": len(self.investments),
                "max_symbols": self.max_symbols,
                "total_replacements": len(self.replacement_history)
            },
            "individual_performance": individual_performance,
            "replacement_history": self.replacement_history,
            "performance_history": self.performance_history
        }

def main():
    """메인 실행 함수"""
    print("🎯 6시간 동적 투자 검증 시뮬레이터")
    print("5개 심볼 + 동적 교체 시스템")
    print()
    
    # 시뮬레이터 생성
    simulator = DynamicInvestmentSimulator()
    
    # 6시간 시뮬레이션 실행
    result = simulator.run_dynamic_investment_simulation(duration_minutes=360, update_interval=10)
    
    if "error" not in result:
        # 최종 결과 출력
        print("\n" + "=" * 80)
        print("🎯 최종 동적 투자 시뮬레이션 결과")
        print("=" * 80)
        
        metadata = result["simulation_metadata"]
        print(f"\n📋 시뮬레이션 정보:")
        print(f"  💰 초기 자본: ${metadata['initial_capital']:.2f}")
        print(f"  💰 최종 자본: ${metadata['final_capital']:.2f}")
        print(f"  📈 총 손익: ${metadata['total_pnl']:+.2f}")
        print(f"  📊 손익률: {metadata['pnl_percent']:+.2f}%")
        print(f"  ⏰ 시작 시간: {metadata['start_time']}")
        print(f"  ⏰ 종료 시간: {metadata['end_time']}")
        print(f"  🔢 총 라운드: {metadata['total_rounds']}")
        print(f"  🎯 투자 심볼: {metadata['invested_symbols']}/{metadata['max_symbols']}개")
        print(f"  🔄 총 교체 횟수: {metadata['total_replacements']}")
        
        # 상위 5개 심볼 성과
        print(f"\n🏆 최종 심볼 성과:")
        for i, perf in enumerate(result["individual_performance"], 1):
            emoji = "📈" if perf['pnl_percent'] > 5 else "📉" if perf['pnl_percent'] < -5 else "➡️"
            print(f"  {i}. {emoji} {perf['symbol']}: ${perf['pnl']:+.2f} ({perf['pnl_percent']:+.2f}%) - 순위: {perf['rank']}")
        
        # 교체 기록
        if result["replacement_history"]:
            print(f"\n🔄 교체 기록:")
            for i, replacement in enumerate(result["replacement_history"], 1):
                print(f"  {i}. {replacement['old_symbol']} → {replacement['new_symbol']}")
                print(f"     기존 성과: {replacement['old_performance']:+.2f}%")
                print(f"     새 점수: {replacement['new_bullish_score']:.1f}")
                print(f"     이전 금액: ${replacement['transferred_amount']:.2f}")
        
        # 결과 저장
        results_file = Path("dynamic_investment_simulation_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과 저장: {results_file}")
    else:
        print(f"❌ 시뮬레이션 실패: {result['error']}")

if __name__ == "__main__":
    main()
