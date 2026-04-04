"""
실전 테스트용 최종 동적 투자 시뮬레이터 v4.0
- 실제 시장 데이터만 사용
- 12시간 테스트
- 거래 수수료 포함
- 익절/손절 동적 자동 평가
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

class RealMarketDynamicInvestmentSimulator:
    """실전 테스트용 최종 동적 투자 시뮬레이터 v4.0"""
    
    def __init__(self, symbol_count: int = 10, replacement_threshold: float = -0.8):
        self.total_capital = 500.0  # 총 자본 $500
        self.initial_capital = 500.0
        self.current_capital = 500.0
        self.max_symbols = symbol_count  # 10개 심볼
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
        
        # 교체 파라미터
        self.performance_threshold = replacement_threshold  # -0.8%
        self.min_replacement_interval = 5  # 5분
        self.max_replacements_per_hour = 5  # 시간당 최대 5회
        self.last_replacement_time = None
        self.replacements_this_hour = 0
        self.last_hour_reset = datetime.now().hour
        
        # 시장 상태 분석
        self.market_regime = "NORMAL"
        self.volatility_threshold = 2.5
        self.extreme_volatility_threshold = 5.0
        
        print(f"FACT: 실전 테스트용 최종 동적 투자 시뮬레이터 v4.0 초기화")
        print(f"  💰 초기 자본: ${self.total_capital:.2f}")
        print(f"  🎯 투자 전략: {self.max_symbols}개 심볼 + 실전 동적 교체")
        print(f"  🔄 교체 기준: {self.performance_threshold}% 이하")
        print(f"  📊 거래 수수료: {self.trading_fee*100:.2f}% 포함")
        print(f"  🎯 익절/손절: 동적 자동 평가")
        print(f"  ⏰ 테스트 시간: 12시간")
        
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
    
    def analyze_market_volatility(self) -> str:
        """실제 시장 변동성 분석"""
        if not self.investments:
            return "NORMAL"
        
        volatilities = []
        for symbol in self.investments.keys():
            try:
                klines_url = f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=24"
                response = requests.get(klines_url, timeout=5)
                
                if response.status_code == 200:
                    klines_data = response.json()
                    closes = [float(kline[4]) for kline in klines_data]
                    
                    if len(closes) >= 20:
                        volatility = self._calculate_volatility(closes)
                        volatilities.append(volatility)
            except:
                continue
        
        if not volatilities:
            return "NORMAL"
        
        avg_volatility = sum(volatilities) / len(volatilities)
        
        if avg_volatility >= self.extreme_volatility_threshold:
            self.market_regime = "EXTREME"
            return "EXTREME"
        elif avg_volatility >= self.volatility_threshold:
            self.market_regime = "HIGH_VOLATILITY"
            return "HIGH_VOLATILITY"
        else:
            self.market_regime = "NORMAL"
            return "NORMAL"
    
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
    
    def allocate_capital_equal(self, top_symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """균등 자본 분배"""
        print(f"FACT: 상위 {self.max_symbols}개 심볼에 균등 자본 분배")
        
        selected_symbols = top_symbols[:self.max_symbols]
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
                "rank": symbol_data["bullish_rank"],
                "bullish_score": symbol_data["bullish_score"],
                "fees_paid": fee,
                "take_profit": self.take_profit_threshold,
                "stop_loss": self.stop_loss_threshold
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
    
    def should_replace_symbol(self, symbol: str) -> bool:
        """심볼 교체 필요 여부 판단"""
        if symbol not in self.investments:
            return False
        
        investment = self.investments[symbol]
        current_pnl_percent = investment["pnl_percent"]
        
        # 익절/손절 우선 처리
        if investment.get("should_close", False):
            return True
        
        # 시장 상태에 따른 동적 교체 기준 조정
        threshold = self.performance_threshold
        
        if self.market_regime == "EXTREME":
            threshold = threshold * 0.5
        elif self.market_regime == "HIGH_VOLATILITY":
            threshold = threshold * 0.75
        
        # 교체 기준 확인
        if current_pnl_percent <= threshold:
            if self.last_replacement_time is None:
                time_since_last = float('inf')
            else:
                time_since_last = (datetime.now() - self.last_replacement_time).total_seconds()
            
            if time_since_last >= self.min_replacement_interval * 60:
                current_hour = datetime.now().hour
                if current_hour != self.last_hour_reset:
                    self.replacements_this_hour = 0
                    self.last_hour_reset = current_hour
                
                if self.replacements_this_hour < self.max_replacements_per_hour:
                    return True
        
        return False
    
    def replace_underperforming_symbol(self):
        """부진 심볼 교체"""
        print(f"FACT: 실전 부진 심볼 교체 프로세스 시작")
        print(f"  🌊 현재 시장 상태: {self.market_regime}")
        
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
        
        # 익절/손절 사유 확인
        investment = self.investments[worst_symbol]
        close_reason = investment.get("close_reason", "PERFORMANCE_THRESHOLD")
        print(f"  📋 교체 사유: {close_reason}")
        
        # 교체할 심볼 선택
        available_symbols = [
            s for s in self.evaluated_symbols 
            if s["symbol"] not in self.investments
        ]
        
        if not available_symbols:
            print("  ⚠️ 교체 가능한 심볼 없음")
            return False
        
        best_replacement = available_symbols[0]
        print(f"  🎯 교체 심볼: {best_replacement['symbol']} (점수: {best_replacement['bullish_score']:.1f})")
        
        # 교체 실행
        old_investment = self.investments[worst_symbol]
        old_value = old_investment["current_investment"]
        
        # 매도 수수료
        sell_fee = old_value * self.trading_fee
        net_proceeds = old_value - sell_fee
        
        # 기존 심볼 제거
        del self.investments[worst_symbol]
        
        # 새 심볼 매수
        new_price = best_replacement["price"]
        buy_fee = net_proceeds * self.trading_fee
        net_investment = net_proceeds - buy_fee
        new_shares = net_investment / new_price
        
        self.investments[best_replacement["symbol"]] = {
            "initial_investment": net_proceeds,
            "net_investment": net_investment,
            "current_investment": net_investment,
            "initial_price": new_price,
            "current_price": new_price,
            "shares": new_shares,
            "initial_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "pnl": 0.0,
            "pnl_percent": 0.0,
            "rank": best_replacement["bullish_rank"],
            "bullish_score": best_replacement["bullish_score"],
            "fees_paid": buy_fee,
            "take_profit": self.take_profit_threshold,
            "stop_loss": self.stop_loss_threshold
        }
        
        # 수수료 누적
        total_fee = sell_fee + buy_fee
        self.total_fees_paid += total_fee
        
        # 교체 기록
        replacement_record = {
            "timestamp": datetime.now().isoformat(),
            "old_symbol": worst_symbol,
            "new_symbol": best_replacement["symbol"],
            "old_performance": worst_performance,
            "old_close_reason": close_reason,
            "new_bullish_score": best_replacement["bullish_score"],
            "transferred_amount": net_proceeds,
            "sell_fee": sell_fee,
            "buy_fee": buy_fee,
            "total_fee": total_fee,
            "market_regime": self.market_regime,
            "replacement_threshold": self.performance_threshold
        }
        
        self.replacement_history.append(replacement_record)
        self.last_replacement_time = datetime.now()
        self.replacements_this_hour += 1
        
        print(f"  ✅ 교체 완료: {worst_symbol} → {best_replacement['symbol']}")
        print(f"  💰 이전 금액: ${net_proceeds:.2f} → 새 심볼에 투자")
        print(f"  💰 거래 수수료: ${total_fee:.2f}")
        print(f"  🌊 시장 상태: {self.market_regime}")
        
        return True
    
    def run_real_market_simulation(self, duration_minutes: int = 720, update_interval: int = 5):
        """실전 시장 시뮬레이션 실행"""
        print(f"FACT: 실전 시장 시뮬레이션 v4.0 시작")
        print(f"  💰 초기 자본: ${self.total_capital:.2f}")
        print(f"  🎯 투자 전략: {self.max_symbols}개 심볼 + 실전 동적 교체")
        print(f"  ⏰ 시뮬레이션 기간: {duration_minutes}분")
        print(f"  🔄 업데이트 주기: {update_interval}분")
        print(f"  📉 교체 기준: {self.performance_threshold}% 이하")
        print(f"  🎯 익절/손절: 동적 자동 평가")
        print(f"  💰 거래 수수료: {self.trading_fee*100:.2f}% 포함")
        
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
        
        # 3. 자본 분배
        allocations = self.allocate_capital_equal(self.evaluated_symbols)
        
        # 4. 투자 초기화
        self.initialize_investments(allocations)
        
        # 5. 시뮬레이션 실행
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        print(f"\n🚀 실전 시장 시뮬레이션 실행 시작")
        print("=" * 80)
        
        iteration = 0
        max_iterations = duration_minutes // update_interval
        
        while datetime.now() < end_time and iteration < max_iterations:
            iteration += 1
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            print(f"\n🔄 라운드 {iteration}/{max_iterations} 시작 - {elapsed.total_seconds():.0f}초 경과")
            
            # 시장 변동성 분석
            market_regime = self.analyze_market_volatility()
            print(f"  🌊 시장 상태: {market_regime}")
            
            # 성과 업데이트
            performance = self.update_investment_performance()
            
            print(f"  💰 총 자산: ${performance['total_value']:.2f}")
            print(f"  📈 총 손익: ${performance['total_pnl']:+.2f} ({performance['pnl_percent']:+.2f}%)")
            print(f"  💰 총 수수료: ${performance['total_fees_paid']:.2f}")
            print(f"  📈 순 손익: ${performance['net_pnl']:+.2f} ({performance['net_pnl_percent']:+.2f}%)")
            
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
                    "close_reason": investment.get("close_reason", "")
                })
            
            current_performance.sort(key=lambda x: x["pnl_percent"], reverse=True)
            
            print(f"  🏆 현재 투자 심볼 성과:")
            for i, perf in enumerate(current_performance, 1):
                emoji = "📈" if perf['pnl_percent'] > 0 else "📉" if perf['pnl_percent'] < 0 else "➡️"
                close_info = ""
                if perf['should_close']:
                    close_info = f" [{perf['close_reason']}]"
                print(f"    {i}. {emoji} {perf['symbol']}: ${perf['pnl']:+.2f} ({perf['pnl_percent']:+.2f}%){close_info}")
            
            # 동적 교체 확인
            replacement_made = self.replace_underperforming_symbol()
            if replacement_made:
                print(f"  🔄 실전 동적 교체 발생!")
            
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
        print(f"\n🎯 최종 실전 시장 투자 시뮬레이션 보고서 생성")
        
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
                "stop_loss": investment["stop_loss"]
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
                "final_market_regime": self.market_regime
            },
            "individual_performance": individual_performance,
            "replacement_history": self.replacement_history,
            "performance_history": self.performance_history,
            "market_regime_history": [p.get("market_regime", "NORMAL") for p in self.performance_history]
        }

def main():
    """메인 실행 함수"""
    print("🎯 실전 테스트용 최종 동적 투자 검증 시뮬레이터 v4.0")
    print("실전 테스트 특징:")
    print("  📊 실제 시장 데이터만 사용")
    print("  ⏰ 12시간 테스트")
    print("  💰 거래 수수료 포함")
    print("  🎯 익절/손절 동적 자동 평가")
    print("  🔄 실전 동적 교체")
    print()
    
    # 실전 테스트 시뮬레이터 생성
    simulator = RealMarketDynamicInvestmentSimulator(
        symbol_count=10,  # 10개 심볼
        replacement_threshold=-0.8  # -0.8% 교체 기준
    )
    
    # 12시간 시뮬레이션 실행
    result = simulator.run_real_market_simulation(duration_minutes=720, update_interval=5)
    
    if "error" not in result:
        # 최종 결과 출력
        print("\n" + "=" * 80)
        print("🎯 최종 실전 시장 투자 시뮬레이션 결과")
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
        
        # 상위 심볼 성과
        print(f"\n🏆 최종 심볼 성과:")
        for i, perf in enumerate(result["individual_performance"], 1):
            emoji = "📈" if perf['pnl_percent'] > 5 else "📉" if perf['pnl_percent'] < -3 else "➡️"
            print(f"  {i}. {emoji} {perf['symbol']}: ${perf['pnl']:+.2f} ({perf['pnl_percent']:+.2f}%) - 순위: {perf['rank']}")
        
        # 교체 기록
        if result["replacement_history"]:
            print(f"\n🔄 교체 기록:")
            for i, replacement in enumerate(result["replacement_history"], 1):
                print(f"  {i}. {replacement['old_symbol']} → {replacement['new_symbol']}")
                print(f"     기존 성과: {replacement['old_performance']:+.2f}%")
                print(f"     교체 사유: {replacement['old_close_reason']}")
                print(f"     새 점수: {replacement['new_bullish_score']:.1f}")
                print(f"     이전 금액: ${replacement['transferred_amount']:.2f}")
                print(f"     거래 수수료: ${replacement['total_fee']:.2f}")
                print(f"     시장 상태: {replacement['market_regime']}")
        
        # 시장 상태 변화
        market_regimes = result["market_regime_history"]
        regime_changes = {}
        for regime in market_regimes:
            regime_changes[regime] = regime_changes.get(regime, 0) + 1
        
        print(f"\n🌊 시장 상태 분석:")
        for regime, count in regime_changes.items():
            percentage = (count / len(market_regimes)) * 100
            print(f"  {regime}: {count}회 ({percentage:.1f}%)")
        
        # 결과 저장
        results_file = Path("real_market_simulation_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과 저장: {results_file}")
    else:
        print(f"❌ 시뮬레이션 실패: {result['error']}")

if __name__ == "__main__":
    main()
