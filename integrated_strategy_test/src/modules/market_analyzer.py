"""
모듈화된 테스트 프로그램 - 시장 분석 모듈
시장 데이터 분석 및 평가 기능 담당
"""

import requests
import statistics
from typing import Dict, List, Any
from datetime import datetime


class MarketAnalyzer:
    """시장 분석기"""
    
    def __init__(self, exchange_base_url: str = "https://demo-fapi.binance.com"):
        self.exchange_base_url = exchange_base_url
        self.supported_symbols = set()
    
    def get_top_volume_symbols(self, limit: int = 80) -> List[Dict[str, Any]]:
        """거래량 기준 상위 심볼 조회"""
        print(f"FACT: 상위 거래량 심볼 조회 시작 (상위 {limit}개)")
        
        try:
            # 24시간 거래량 기준 심볼 조회
            response = requests.get(f"{self.exchange_base_url}/fapi/v1/ticker/24hr", timeout=10)
            if response.status_code != 200:
                print(f"❌ API 응답 오류: {response.status_code}")
                return []
            
            data = response.json()
            
            # 거래량 기준 정렬
            filtered_data = []
            for item in data:
                try:
                    symbol = item['symbol']
                    volume = float(item['volume'])
                    price = float(item['lastPrice'])
                    change_percent = float(item['priceChangePercent'])
                    
                    # USDT 마켓만 필터링
                    if symbol.endswith('USDT') and volume > 0:
                        filtered_data.append({
                            'symbol': symbol,
                            'volume': volume,
                            'price': price,
                            'change_percent': change_percent,
                            'quoteVolume': float(item['quoteVolume'])
                        })
                except (ValueError, KeyError) as e:
                    print(f"  ⚠️ {item.get('symbol', 'Unknown')} 데이터 파싱 오류: {e}")
                    continue
            
            # 거래량 기준 정렬
            filtered_data.sort(key=lambda x: x['volume'], reverse=True)
            
            # 상위 심볼 선택
            top_symbols = filtered_data[:limit]
            
            print(f"  ✅ 상위 {len(top_symbols)}개 심볼 조회 성공")
            for i, symbol in enumerate(top_symbols[:5], 1):
                print(f"    {i}. {symbol['symbol']}: 거래량 {symbol['volume']:,.0f}")
            
            return top_symbols
            
        except Exception as e:
            print(f"❌ 상위 심볼 조회 실패: {e}")
            return []
    
    def evaluate_bullish_potential_advanced(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """상승 가능성 고급 평가"""
        print(f"FACT: 상승 가능성 고급 평가 시작 ({len(symbols)}개 심볼)")
        
        evaluated_symbols = []
        failed_count = 0
        
        for symbol_data in symbols:
            try:
                # 기본 데이터 확인
                symbol = symbol_data['symbol']
                price = symbol_data['price']
                volume = symbol_data['volume']
                change_percent = symbol_data['change_percent']
                
                # 기술적 지표 계산
                indicators = self._calculate_indicators_from_symbol(symbol)
                
                # 상승 점수 계산
                bullish_score_result = self._calculate_bullish_score(symbol_data, indicators)
                
                # 평가된 심볼 데이터 구성
                evaluated_symbol = {
                    "symbol": symbol,
                    "price": price,
                    "volume": volume,
                    "change_percent": change_percent,
                    **indicators,
                    **bullish_score_result
                }
                evaluated_symbols.append(evaluated_symbol)
                
            except Exception as e:
                failed_count += 1
                print(f"  ❌ {symbol_data.get('symbol', 'Unknown')} 평가 실패: {e}")
        
        # 상승 점수 기준 정렬
        evaluated_symbols.sort(key=lambda x: x["bullish_score"], reverse=True)
        
        # 순위 부여
        for i, symbol in enumerate(evaluated_symbols, 1):
            symbol["bullish_rank"] = i
        
        print(f"  📊 평가 성공: {len(evaluated_symbols)}개, 실패: {failed_count}개")
        return evaluated_symbols
    
    def _calculate_indicators_from_symbol(self, symbol: str) -> Dict[str, Any]:
        """심볼별 기술적 지표 계산"""
        try:
            # Klines 데이터 조회
            klines_response = requests.get(
                f"{self.exchange_base_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=100", 
                timeout=10
            )
            
            if klines_response.status_code != 200:
                print(f"  ⚠️ {symbol} Klines 데이터 조회 실패")
                return self._get_default_indicators()
            
            klines = klines_response.json()
            
            # 데이터 추출
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            
            return self._calculate_indicators(closes, volumes, highs, lows)
            
        except Exception as e:
            print(f"  ❌ {symbol} 지표 계산 실패: {e}")
            return self._get_default_indicators()
    
    def _calculate_indicators(self, closes: List[float], volumes: List[float], highs: List[float], lows: List[float]) -> Dict[str, Any]:
        """기술적 지표 계산"""
        indicators = {}
        
        # RSI
        indicators["rsi"] = self._calculate_rsi(closes, 14)
        
        # MACD
        indicators["macd_signal"] = self._calculate_macd_signal(closes)
        
        # 이동평균
        indicators["sma_20"] = sum(closes[-20:]) / 20
        indicators["sma_50"] = sum(closes[-50:]) / 50 if len(closes) >= 50 else indicators["sma_20"]
        
        # 볼린저 밴드
        bb_upper, bb_lower = self._calculate_bollinger_bands(closes, 20)
        indicators["bb_upper"] = bb_upper
        indicators["bb_lower"] = bb_lower
        
        # 변동성
        if len(closes) >= 2:
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            indicators["volatility"] = statistics.stdev(returns) * 100 if returns else 0
        else:
            indicators["volatility"] = 0
        
        # 거래량 모멘텀
        if len(volumes) >= 10:
            recent_vol = sum(volumes[-5:]) / 5
            prev_vol = sum(volumes[-10:-5]) / 5
            indicators["volume_momentum"] = (recent_vol - prev_vol) / prev_vol * 100 if prev_vol > 0 else 0
        else:
            indicators["volume_momentum"] = 0
        
        return indicators
    
    def _get_default_indicators(self) -> Dict[str, Any]:
        """기본 기술적 지표"""
        return {
            "rsi": 50,
            "macd_signal": "NEUTRAL",
            "sma_20": 0,
            "sma_50": 0,
            "bb_upper": 0,
            "bb_lower": 0,
            "volatility": 0,
            "volume_momentum": 0
        }
    
    def _calculate_bullish_score(self, symbol_data: Dict[str, Any], indicators: Dict[str, Any]) -> Dict[str, Any]:
        """상승 점수 계산"""
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
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """RSI 계산"""
        if len(closes) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            delta = closes[i] - closes[i-1]
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(delta))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
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
        variance = sum((x - sma) ** 2 for x in closes[-period:]) / period
        std = variance ** 0.5
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, lower_band
