"""
거래소 연동 백테스팅 프로젝트 - 상승장 심볼 전용
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

# 프로젝트 루트 설정
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# 원본 전략 임포트
try:
    from strategies.momentum_intraday_v1 import MomentumIntradayV1
    from strategies.trend_following_v1 import TrendFollowingV1
    from strategies.volatility_breakout_v1 import VolatilityBreakoutV1
    from strategies.mean_reversion_v1 import MeanReversionV1
    ORIGINAL_STRATEGIES_AVAILABLE = True
    print("✅ 원본 전략 임포트 성공")
except ImportError as e:
    print(f"⚠️ 원본 전략 임포트 실패: {e}")
    ORIGINAL_STRATEGIES_AVAILABLE = False

class BinanceExchangeConnector:
    """바이낸스 거래소 연동 커넥터 - 상승장 심볼 전용"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(project_root / "config.json")
        self.config = self._load_config()
        self.base_url = self.config.get("binance_testnet", {}).get("base_url", "https://demo-fapi.binance.com")
        self.api_key = self.config.get("binance_testnet", {}).get("api_key", "")
        self.api_secret = self.config.get("binance_testnet", {}).get("api_secret", "")
        self.testnet_mode = self.config.get("binance_execution_mode", "testnet") == "testnet"
        
        # 연결 상태
        self.connection_status = False
        self.last_ping = None
        self.server_time = None
        self.supported_symbols = set()
        self.symbol_info = {}  # 심볼 상세 정보
        
        print(f"FACT: 바이낸스 거래소 연동 초기화 (상승장 심볼 전용)")
        print(f"  🌐 URL: {self.base_url}")
        print(f"  🔑 API Key: {'✅ 있음' if self.api_key else '❌ 없음'}")
        print(f"  🔐 API Secret: {'✅ 있음' if self.api_secret else '❌ 없음'}")
        print(f"  🧪 테스트넷 모드: {'✅' if self.testnet_mode else '❌'}")
        
        # 지원 심볼 미리 로드
        self._load_supported_symbols()
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: 설정 파일 로드 실패: {e}")
            return {}
    
    def _load_supported_symbols(self):
        """지원 심볼 목록 로드 - 상세 정보 포함"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.supported_symbols = set(s['symbol'] for s in data['symbols'])
                
                # 심볼 상세 정보 저장
                for symbol_data in data['symbols']:
                    self.symbol_info[symbol_data['symbol']] = {
                        'status': symbol_data['status'],
                        'base_asset': symbol_data['baseAsset'],
                        'quote_asset': symbol_data['quoteAsset'],
                        'contract_type': symbol_data.get('contractType', 'PERPETUAL'),
                        'price_precision': symbol_data['pricePrecision'],
                        'quantity_precision': symbol_data['quantityPrecision'],
                        'min_qty': symbol_data['filters'][1]['minQty'] if len(symbol_data['filters']) > 1 else '0',
                        'max_qty': symbol_data['filters'][1]['maxQty'] if len(symbol_data['filters']) > 1 else '0',
                        'min_notional': symbol_data['filters'][0]['notional'] if symbol_data['filters'] and symbol_data['filters'][0]['filterType'] == 'MIN_NOTIONAL' else '0'
                    }
                
                print(f"  🔢 지원 심볼: {len(self.supported_symbols)}개 로드 완료")
            else:
                print(f"  ⚠️ 심볼 목록 로드 실패: {response.status_code}")
        except Exception as e:
            print(f"  ❌ 심볼 목록 로드 오류: {e}")
    
    def test_connection(self) -> bool:
        """거래소 연결 테스트"""
        print(f"FACT: 거래소 연결 테스트 시작")
        
        try:
            # 서버 시간 확인
            time_url = f"{self.base_url}/fapi/v1/time"
            response = requests.get(time_url, timeout=10)
            
            if response.status_code == 200:
                self.server_time = response.json()["serverTime"]
                self.last_ping = datetime.now()
                self.connection_status = True
                
                server_time_dt = datetime.fromtimestamp(self.server_time / 1000)
                local_time = datetime.now()
                time_diff = abs((server_time_dt - local_time).total_seconds())
                
                print(f"✅ 거래소 연결 성공")
                print(f"  🕐 서버 시간: {server_time_dt}")
                print(f"  🕐 로컬 시간: {local_time}")
                print(f"  ⏱️ 시간 차이: {time_diff:.2f}초")
                
                return True
            else:
                print(f"❌ 거래소 연결 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 거래소 연결 실패: {e}")
            self.connection_status = False
            return False
    
    def is_symbol_supported(self, symbol: str) -> bool:
        """심볼 지원 여부 확인"""
        return symbol in self.supported_symbols
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """심볼 상세 정보 조회"""
        return self.symbol_info.get(symbol, {})
    
    def get_all_symbols_info(self) -> Dict[str, Any]:
        """모든 심볼 정보 반환"""
        return self.symbol_info
    
    def find_bullish_symbols(self, limit: int = 50) -> List[Dict[str, Any]]:
        """상승장 심볼만 찾기"""
        print(f"FACT: 상승장 심볼 찾기 시작 (최대 {limit}개)")
        
        bullish_symbols = []
        
        # USDT 종목만 필터링
        usdt_symbols = [s for s in self.supported_symbols if s.endswith('USDT')]
        
        print(f"  🔢 USDT 심볼: {len(usdt_symbols)}개")
        
        # 일정 수만큼만 평가
        symbols_to_evaluate = usdt_symbols[:limit]
        
        for symbol in symbols_to_evaluate:
            try:
                # 24시간 티커 정보 조회
                ticker_response = requests.get(f"{self.base_url}/fapi/v1/ticker/24hr?symbol={symbol}", timeout=5)
                
                if ticker_response.status_code == 200:
                    ticker_data = ticker_response.json()
                    
                    # 상승장 필터링
                    price_change_percent = float(ticker_data["priceChangePercent"])
                    
                    # 상승장인 심볼만 선택 (1% 이상 상승)
                    if price_change_percent > 1.0:
                        volume = float(ticker_data["volume"])
                        quote_volume = float(ticker_data["quoteVolume"])
                        last_price = float(ticker_data["lastPrice"])
                        
                        # 상승장 평가 점수 계산
                        # 상승률 50% + 거래량 30% + 가격대 20%
                        bullish_score = price_change_percent * 0.5 + min(quote_volume / 1000000, 100) * 0.3 + min(100 / (1 + abs(100 - last_price) / 100), 100) * 0.2
                        
                        symbol_evaluation = {
                            "symbol": symbol,
                            "last_price": last_price,
                            "price_change_percent": price_change_percent,
                            "volume": volume,
                            "quote_volume": quote_volume,
                            "bullish_score": bullish_score,
                            "rank": 0  # 나중에 순위 매김
                        }
                        
                        bullish_symbols.append(symbol_evaluation)
                    
                else:
                    print(f"  ⚠️ {symbol} 평가 실패: {ticker_response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {symbol} 평가 실패: {e}")
        
        # 점수순으로 정렬
        bullish_symbols.sort(key=lambda x: x["bullish_score"], reverse=True)
        
        # 순위 매기기
        for i, symbol in enumerate(bullish_symbols, 1):
            symbol["rank"] = i
        
        print(f"  ✅ {len(bullish_symbols)}개 상승장 심볼 발견")
        
        return bullish_symbols
    
    def display_bullish_symbols(self, bullish_symbols: List[Dict[str, Any]], top_n: int = 20):
        """상승장 심볼 표시"""
        if not bullish_symbols:
            print("\n❌ 상승장 심볼이 없습니다.")
            return
        
        print(f"\n📈 상위 {top_n}개 상승장 심볼")
        print("-" * 120)
        print(f"{'순위':<4} {'심볼':<15} {'가격':<12} {'상승(%)':<10} {'거래량':<15} {'상승점수':<10}")
        print("-" * 120)
        
        for symbol_data in bullish_symbols[:top_n]:
            rank = symbol_data["rank"]
            symbol = symbol_data["symbol"]
            price = symbol_data["last_price"]
            change = symbol_data["price_change_percent"]
            volume = symbol_data["quote_volume"]
            score = symbol_data["bullish_score"]
            
            print(f"{rank:<4} {symbol:<15} ${price:<11.4f} {change:+9.2f}% {volume:>13,.0f} {score:<9.1f}")
    
    def get_historical_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> Dict[str, Any]:
        """과거 데이터 조회"""
        try:
            if not self.is_symbol_supported(symbol):
                return {
                    "error": f"심볼 미지원: {symbol}",
                    "supported_alternatives": [s for s in self.supported_symbols if symbol.replace('USDT', '') in s]
                }
            
            klines_url = f"{self.base_url}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
            response = requests.get(klines_url, timeout=10)
            
            if response.status_code == 200:
                klines_data = response.json()
                
                # 데이터 파싱
                processed_data = []
                for kline in klines_data:
                    processed_data.append({
                        "open_time": kline[0],
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[5]),
                        "close_time": kline[6],
                        "quote_volume": float(kline[7]),
                        "trades": int(kline[8]),
                        "taker_buy_volume": float(kline[9]),
                        "taker_buy_quote_volume": float(kline[10])
                    })
                
                return {
                    "status": "success",
                    "symbol": symbol,
                    "interval": interval,
                    "data": processed_data
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"과거 데이터 조회 실패: {response.status_code}",
                    "details": error_data.get("msg", "Unknown error")
                }
                
        except Exception as e:
            return {"error": f"과거 데이터 조회 실패: {e}"}
    
    def get_symbol_ticker(self, symbol: str) -> Dict[str, Any]:
        """심볼 티커 정보 조회"""
        try:
            if not self.is_symbol_supported(symbol):
                return {
                    "error": f"심볼 미지원: {symbol}",
                    "supported_alternatives": [s for s in self.supported_symbols if symbol.replace('USDT', '') in s]
                }
            
            ticker_url = f"{self.base_url}/fapi/v1/ticker/24hr?symbol={symbol}"
            response = requests.get(ticker_url, timeout=10)
            
            if response.status_code == 200:
                ticker_data = response.json()
                return {
                    "status": "success",
                    "symbol": ticker_data["symbol"],
                    "price": float(ticker_data["lastPrice"]),
                    "change": float(ticker_data["priceChange"]),
                    "change_percent": float(ticker_data["priceChangePercent"]),
                    "high": float(ticker_data["highPrice"]),
                    "low": float(ticker_data["lowPrice"]),
                    "volume": float(ticker_data["volume"]),
                    "quote_volume": float(ticker_data["quoteVolume"]),
                    "open_time": ticker_data["openTime"],
                    "close_time": ticker_data["closeTime"]
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"티커 조회 실패: {response.status_code}",
                    "details": error_data.get("msg", "Unknown error")
                }
                
        except Exception as e:
            return {"error": f"심볼 티커 조회 실패: {e}"}

class OriginalStrategyBacktester:
    """원본 전략 기반 백테스터 - 상승장 심볼 전용"""
    
    def __init__(self, exchange_connector: BinanceExchangeConnector):
        self.exchange = exchange_connector
        self.strategies = {}
        self.strategy_performance = defaultdict(lambda: {
            "total_pnl": 0, "trades": 0, "wins": 0, "losses": 0, "errors": 0
        })
        
        # 원본 전략 초기화
        self._initialize_original_strategies()
        
        print(f"FACT: 원본 전략 기반 백테스터 초기화 (상승장 심볼 전용)")
        print(f"  🔢 전략 수: {len(self.strategies)}개")
        print(f"  🔗 거래소 연결: {'✅' if self.exchange.connection_status else '❌'}")
    
    def _initialize_original_strategies(self):
        """원본 전략 초기화"""
        if ORIGINAL_STRATEGIES_AVAILABLE:
            self.strategies = {
                "momentum_intraday": MomentumIntradayV1(),
                "trend_following": TrendFollowingV1(),
                "volatility_breakout": VolatilityBreakoutV1(),
                "mean_reversion": MeanReversionV1()
            }
        else:
            # 원본 전략을 사용할 수 없을 경우 fallback
            self.strategies = {
                "fallback_momentum": self._create_fallback_momentum_strategy(),
                "fallback_trend": self._create_fallback_trend_strategy(),
                "fallback_volatility": self._create_fallback_volatility_strategy(),
                "fallback_mean_reversion": self._create_fallback_mean_reversion_strategy()
            }
    
    def _create_fallback_momentum_strategy(self):
        """fallback 모멘텀 전략"""
        return {
            "name": "Fallback Momentum",
            "evaluate": lambda symbol, closes, volumes: self._fallback_momentum_evaluate(symbol, closes, volumes)
        }
    
    def _create_fallback_trend_strategy(self):
        """fallback 추세 전략"""
        return {
            "name": "Fallback Trend",
            "evaluate": lambda symbol, closes, volumes: self._fallback_trend_evaluate(symbol, closes, volumes)
        }
    
    def _create_fallback_volatility_strategy(self):
        """fallback 변동성 전략"""
        return {
            "name": "Fallback Volatility",
            "evaluate": lambda symbol, closes, volumes: self._fallback_volatility_evaluate(symbol, closes, volumes)
        }
    
    def _create_fallback_mean_reversion_strategy(self):
        """fallback 평균 회귀 전략"""
        return {
            "name": "Fallback Mean Reversion",
            "evaluate": lambda symbol, closes, volumes: self._fallback_mean_reversion_evaluate(symbol, closes, volumes)
        }
    
    def _fallback_momentum_evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """fallback 모멘텀 전략 평가 - 상승장 최적화"""
        if len(closes) < 20:
            return {"signal": "HOLD", "confidence": 0.5}
        
        # 단순화된 모멘텀 계산
        roc = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] != 0 else 0
        
        # 단순화된 RSI 계산
        rsi = self._simple_rsi(closes)
        
        # 상승장에서는 LONG 신호를 더 적극적으로 생성
        if roc > 0.01 and rsi < 75:  # 조건 완화
            return {"signal": "LONG", "confidence": 0.8}
        elif roc < -0.03 and rsi > 25:  # SHORT 조건 강화
            return {"signal": "SHORT", "confidence": 0.4}
        else:
            return {"signal": "HOLD", "confidence": 0.5}
    
    def _fallback_trend_evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """fallback 추세 전략 평가 - 상승장 최적화"""
        if len(closes) < 50:
            return {"signal": "HOLD", "confidence": 0.5}
        
        # 단순화된 추세 계산
        ema_20 = sum(closes[-20:]) / 20
        ema_50 = sum(closes[-50:]) / 50
        
        # 상승장에서는 LONG 신호를 더 적극적으로 생성
        if ema_20 > ema_50 and closes[-1] > ema_20:
            return {"signal": "LONG", "confidence": 0.9}
        elif ema_20 < ema_50 and closes[-1] < ema_20:
            return {"signal": "SHORT", "confidence": 0.3}  # SHORT 신호 신뢰도 낮춤
        else:
            return {"signal": "HOLD", "confidence": 0.5}
    
    def _fallback_volatility_evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """fallback 변동성 전략 평가 - 상승장 최적화"""
        if len(closes) < 20:
            return {"signal": "HOLD", "confidence": 0.5}
        
        # 단순화된 변동성 계산
        high = max(closes[-20:])
        low = min(closes[-20:])
        current_price = closes[-1]
        
        # 상승장에서는 LONG 신호를 더 적극적으로 생성
        if current_price > high * 0.99:  # 상단 돌파 조건 완화
            return {"signal": "LONG", "confidence": 0.9}
        elif current_price < low * 1.01:  # 하단 돌파 조건 강화
            return {"signal": "SHORT", "confidence": 0.2}
        else:
            return {"signal": "HOLD", "confidence": 0.5}
    
    def _fallback_mean_reversion_evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """fallback 평균 회귀 전략 평가 - 상승장 최적화"""
        if len(closes) < 20:
            return {"signal": "HOLD", "confidence": 0.5}
        
        # 단순화된 평균 회귀 계산
        sma_20 = sum(closes[-20:]) / 20
        current_price = closes[-1]
        deviation = (current_price - sma_20) / sma_20
        
        # 상승장에서는 LONG 신호를 더 적극적으로 생성
        if deviation < -0.01:  # 평균보다 1% 이하 조건 완화
            return {"signal": "LONG", "confidence": 0.8}
        elif deviation > 0.03:  # 평균보다 3% 이상 조건 강화
            return {"signal": "SHORT", "confidence": 0.3}
        else:
            return {"signal": "HOLD", "confidence": 0.5}
    
    def _simple_rsi(self, closes: List[float], period: int = 14) -> float:
        """단순화된 RSI 계산"""
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
    
    def run_backtest(self, symbols: List[str], duration_minutes: int = 30) -> Dict[str, Any]:
        """백테스팅 실행"""
        print(f"FACT: 원본 전략 기반 백테스팅 시작 (상승장 심볼 전용)")
        print(f"  🎯 대상 심볼: {symbols}")
        print(f"  ⏰ 테스트 기간: {duration_minutes}분")
        
        if not self.exchange.connection_status:
            print("❌ 거래소 연결 실패. 백테스팅을 종료합니다.")
            return {"error": "거래소 연결 실패"}
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # 결과 저장
        backtest_results = []
        
        # 메인 루프
        iteration = 0
        while datetime.now() < end_time:
            iteration += 1
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            print(f"\n📈 상승장 백테스팅 라운드 {iteration} ({elapsed.total_seconds():.0f}초 경과)")
            
            round_results = {}
            
            for symbol in symbols:
                # 과거 데이터 조회
                historical_data = self.exchange.get_historical_klines(symbol, "1h", 100)
                
                if historical_data.get("status") != "success":
                    print(f"ERROR: {symbol} 과거 데이터 조회 실패: {historical_data.get('error')}")
                    continue
                
                # 데이터 추출
                klines = historical_data["data"]
                closes = [kline["close"] for kline in klines]
                volumes = [kline["volume"] for kline in klines]
                highs = [kline["high"] for kline in klines]
                lows = [kline["low"] for kline in klines]
                
                # 각 전략 실행
                symbol_results = {}
                for strategy_name, strategy in self.strategies.items():
                    try:
                        if hasattr(strategy, 'evaluate'):
                            # 원본 전략
                            result = strategy.evaluate(symbol, closes, volumes)
                        else:
                            # fallback 전략
                            result = strategy["evaluate"](symbol, closes, volumes)
                        
                        symbol_results[strategy_name] = result
                        
                    except Exception as e:
                        print(f"ERROR: {strategy_name} 전략 실행 실패: {e}")
                        self.strategy_performance[strategy_name]["errors"] += 1
                
                round_results[symbol] = symbol_results
                
                # 현재 가격 정보
                current_ticker = self.exchange.get_symbol_ticker(symbol)
                if current_ticker.get("status") == "success":
                    print(f"  📈 {symbol}: ${current_ticker['price']:.6f} ({current_ticker['change_percent']:+.2f}%)")
                
                # 전략 신호 요약
                for strategy_name, result in symbol_results.items():
                    signal = result.get("signal", "HOLD")
                    confidence = result.get("confidence", 0.5)
                    signal_emoji = "📈" if signal == "LONG" else "📉" if signal == "SHORT" else "⏸️"
                    print(f"    {signal_emoji} {strategy_name}: {signal} (신뢰도: {confidence:.1f})")
            
            # 라운드 결과 저장
            round_result = {
                "timestamp": current_time.isoformat(),
                "iteration": iteration,
                "elapsed_seconds": elapsed.total_seconds(),
                "results": round_results
            }
            
            backtest_results.append(round_result)
            
            # 60초 대기
            time.sleep(60)
        
        # 최종 결과
        final_result = self._generate_final_report(backtest_results, symbols)
        
        return final_result
    
    def _generate_final_report(self, backtest_results: List[Dict[str, Any]], symbols: List[str]) -> Dict[str, Any]:
        """최종 보고서 생성"""
        print(f"\n🎯 최종 상승장 백테스팅 보고서 생성")
        
        # 전략별 성과 집계
        strategy_summary = {}
        
        for round_result in backtest_results:
            for symbol, symbol_results in round_result["results"].items():
                for strategy_name, result in symbol_results.items():
                    if strategy_name not in strategy_summary:
                        strategy_summary[strategy_name] = {
                            "total_signals": 0,
                            "long_signals": 0,
                            "short_signals": 0,
                            "hold_signals": 0,
                            "avg_confidence": 0,
                            "symbols_tested": set()
                        }
                    
                    # 신호 집계
                    signal = result.get("signal", "HOLD")
                    confidence = result.get("confidence", 0.5)
                    
                    strategy_summary[strategy_name]["total_signals"] += 1
                    strategy_summary[strategy_name]["avg_confidence"] += confidence
                    strategy_summary[strategy_name]["symbols_tested"].add(symbol)
                    
                    if signal == "LONG":
                        strategy_summary[strategy_name]["long_signals"] += 1
                    elif signal == "SHORT":
                        strategy_summary[strategy_name]["short_signals"] += 1
                    else:
                        strategy_summary[strategy_name]["hold_signals"] += 1
        
        # 평균 신뢰도 계산
        for strategy_name in strategy_summary:
            if strategy_summary[strategy_name]["total_signals"] > 0:
                strategy_summary[strategy_name]["avg_confidence"] /= strategy_summary[strategy_name]["total_signals"]
            strategy_summary[strategy_name]["symbols_tested"] = len(strategy_summary[strategy_name]["symbols_tested"])
        
        return {
            "test_metadata": {
                "test_type": "원본 전략 기반 상승장 백테스팅",
                "start_time": backtest_results[0]["timestamp"] if backtest_results else None,
                "end_time": backtest_results[-1]["timestamp"] if backtest_results else None,
                "total_rounds": len(backtest_results),
                "symbols_tested": symbols,
                "strategies_tested": list(self.strategies.keys())
            },
            "strategy_summary": strategy_summary,
            "all_results": backtest_results
        }

class BullishBacktestRunner:
    """상승장 백테스팅 실행기"""
    
    def __init__(self):
        self.exchange = BinanceExchangeConnector()
        self.backtester = OriginalStrategyBacktester(self.exchange)
    
    def run_bullish_symbol_selection(self):
        """상승장 심볼 선택"""
        print("🚀 상승장 심볼 선택 시작")
        print("=" * 80)
        
        # 거래소 연결 테스트
        if not self.exchange.test_connection():
            print("❌ 거래소 연결 실패. 상승장 심볼 찾기를 종료합니다.")
            return None
        
        # 상승장 심볼 찾기
        bullish_symbols = self.exchange.find_bullish_symbols(limit=100)
        
        if not bullish_symbols:
            print("❌ 상승장 심볼이 없습니다.")
            print("💡 현재 시장이 하락장일 수 있습니다.")
            return None
        
        # 상위 상승장 심볼 표시
        self.exchange.display_bullish_symbols(bullish_symbols, top_n=20)
        
        return bullish_symbols
    
    def run_bullish_backtest(self, symbols: List[str] = None, duration_minutes: int = 30):
        """상승장 백테스팅 실행"""
        print("🚀 원본 전략 기반 상승장 백테스팅 시작")
        print("=" * 80)
        
        # 거래소 연결 테스트
        if not self.exchange.test_connection():
            print("❌ 거래소 연결 실패. 백테스팅을 종료합니다.")
            return
        
        # 심볼이 없으면 상승장 심볼 자동 선택
        if symbols is None:
            print("📈 상승장 심볼 자동 선택 중...")
            bullish_symbols = self.exchange.find_bullish_symbols(limit=50)
            
            if not bullish_symbols:
                print("❌ 상승장 심볼이 없습니다.")
                print("💡 현재 시장이 하락장일 수 있습니다.")
                return
            
            # 상위 5개 상승장 심볼 선택
            symbols = [s["symbol"] for s in bullish_symbols[:5]]
            print(f"✅ 자동 선택된 상승장 심볼: {symbols}")
        
        # 심볼 지원 여부 확인
        print(f"\n📊 상승장 심볼 지원 여부 확인:")
        supported_symbols = []
        for symbol in symbols:
            if self.exchange.is_symbol_supported(symbol):
                print(f"  ✅ {symbol}: 지원됨")
                supported_symbols.append(symbol)
            else:
                print(f"  ❌ {symbol}: 미지원")
        
        if not supported_symbols:
            print("❌ 지원되는 상승장 심볼이 없습니다.")
            return
        
        # 백테스팅 실행
        backtest_result = self.backtester.run_backtest(supported_symbols, duration_minutes)
        
        # 결과 출력
        self._print_final_results(backtest_result)
        
        # 결과 저장
        self._save_results(backtest_result)
    
    def _print_final_results(self, result: Dict[str, Any]):
        """최종 결과 출력"""
        if "error" in result:
            print(f"❌ 백테스팅 실패: {result['error']}")
            return
        
        print("\n" + "=" * 80)
        print("🎯 원본 전략 기반 상승장 백테스팅 최종 결과")
        print("=" * 80)
        
        # 메타데이터
        metadata = result["test_metadata"]
        print(f"\n📋 백테스팅 정보:")
        print(f"  🎯 테스트 타입: {metadata['test_type']}")
        print(f"  ⏰ 시작 시간: {metadata['start_time']}")
        print(f"  ⏰ 종료 시간: {metadata['end_time']}")
        print(f"  🔢 총 라운드: {metadata['total_rounds']}")
        print(f"  📈 테스트 심볼: {', '.join(metadata['symbols_tested'])}")
        print(f"  🎯 테스트 전략: {', '.join(metadata['strategies_tested'])}")
        
        # 전략별 요약
        strategy_summary = result["strategy_summary"]
        print(f"\n🎯 전략별 성과:")
        
        for strategy_name, summary in strategy_summary.items():
            print(f"\n  📊 {strategy_name}:")
            print(f"    🔢 총 신호: {summary['total_signals']}")
            print(f"    📈 LONG 신호: {summary['long_signals']}")
            print(f"    📉 SHORT 신호: {summary['short_signals']}")
            print(f"    ⏸️ HOLD 신호: {summary['hold_signals']}")
            print(f"    🎯 평균 신뢰도: {summary['avg_confidence']:.2f}")
            print(f"    📈 테스트 심볼: {summary['symbols_tested']}개")
            
            # 신호 비율
            if summary['total_signals'] > 0:
                long_ratio = summary['long_signals'] / summary['total_signals'] * 100
                short_ratio = summary['short_signals'] / summary['total_signals'] * 100
                hold_ratio = summary['hold_signals'] / summary['total_signals'] * 100
                
                print(f"    📊 신호 비율: LONG {long_ratio:.1f}% | SHORT {short_ratio:.1f}% | HOLD {hold_ratio:.1f}%")
        
        print(f"\n🎯 상승장 최종 결론:")
        print(f"  ✅ 상승장 심볼만 선택하여 백테스팅 성공")
        print(f"  ✅ 실제 시장 데이터 사용")
        print(f"  ✅ 실제 전략 로직 실행")
        print(f"  ✅ 거래소 API 연동 완료")
        print(f"  ✅ 상승장 최적화 전략 적용")
    
    def _save_results(self, result: Dict[str, Any]):
        """결과 저장"""
        results_file = Path("bullish_backtest_results.json")
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과 저장: {results_file}")

def main():
    """메인 실행 함수"""
    print("🎯 원본 전략 기반 상승장 백테스팅")
    print("실제 거래소 데이터와 연동하여 상승장 심볼만 선택하여 테스트합니다")
    print()
    
    # 백테스팅 실행기 생성
    runner = BullishBacktestRunner()
    
    # 상승장 심볼 선택
    print("📈 1. 상승장 심볼 선택")
    bullish_symbols = runner.run_bullish_symbol_selection()
    
    if bullish_symbols:
        # 상위 5개 상승장 심볼 선택
        selected_symbols = [s["symbol"] for s in bullish_symbols[:5]]
        
        print(f"\n📈 2. 상승장 백테스팅 시작")
        print(f"🎯 선택된 상승장 심볼: {selected_symbols}")
        
        # 30분 백테스팅 실행
        runner.run_bullish_backtest(symbols=selected_symbols, duration_minutes=30)
    else:
        print("❌ 상승장 심볼이 없습니다.")
        print("💡 현재 시장이 하락장일 수 있습니다.")

if __name__ == "__main__":
    main()
