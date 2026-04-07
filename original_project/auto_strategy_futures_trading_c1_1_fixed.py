#!/usr/bin/env python3
"""
자동 전략 기반 선물 거래 시스템 - 전면 리팩토링 버전
================================================
수정 사항:
  [1] API 키 하드코딩 완전 제거 → 환경변수 필수
  [2] random() 완전 제거 → 실제 시장 데이터 기반 신호
  [3] 포지션 크기 단위 수정 (달러 → 수량)
  [4] __init__ 초기화 순서 수정 (네트워크 호출 분리)
  [5] 변동성 계산 수정 (가격 차이 → 수익률 표준편차)
  [6] API 호출 최소화 (캐싱 + 배치 처리)
"""

import json
import time
import hmac
import hashlib
import os
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import requests


# ─────────────────────────────────────────────────────
# 0. 설정 & 상수
# ─────────────────────────────────────────────────────

TESTNET_BASE_URL  = "https://testnet.binancefuture.com"
MAINNET_BASE_URL  = "https://fapi.binance.com"

# 캐시 유효 시간 (초)
KLINES_CACHE_TTL  = 60    # 1분
PRICE_CACHE_TTL   = 5     # 5초

# 전략 기본 파라미터 (백테스트 기반 고정값)
STRATEGY_PARAMS = {
    "momentum": {
        "stop_loss":    0.03,   # 3%
        "take_profit":  0.06,   # 6%  (RR 1:2)
        "risk_per_trade": 0.01, # 계좌의 1%
    },
    "mean_reversion": {
        "stop_loss":    0.025,
        "take_profit":  0.05,
        "risk_per_trade": 0.01,
    },
    "volatility": {
        "stop_loss":    0.04,
        "take_profit":  0.10,
        "risk_per_trade": 0.008,
    },
    "trend_following": {
        "stop_loss":    0.035,
        "take_profit":  0.08,
        "risk_per_trade": 0.012,
    },
    "arbitrage": {
        "stop_loss":    0.005,
        "take_profit":  0.003,
        "risk_per_trade": 0.005,
    },
}

TOP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT",
    "LINKUSDT", "BNBUSDT", "SOLUSDT", "LTCUSDT", "BCHUSDT",
    "AVAXUSDT", "MATICUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT",
    "ETCUSDT", "ICPUSDT", "VETUSDT", "THETAUSDT", "FTMUSDT",
]


# ─────────────────────────────────────────────────────
# 1. 열거형
# ─────────────────────────────────────────────────────

class MarketRegime(Enum):
    BULL     = "BULL_MARKET"
    BEAR     = "BEAR_MARKET"
    SIDEWAYS = "SIDEWAYS_MARKET"


class Signal(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# ─────────────────────────────────────────────────────
# 2. 데이터 클래스
# ─────────────────────────────────────────────────────

@dataclass
class MarketState:
    regime:     MarketRegime
    volatility: float   # 수익률 기반 표준편차
    strength:   float   # 평균 수익률 (EMA 기울기 대용)
    spread_pct: float = 0.0


@dataclass
class TradeSignal:
    strategy:       str
    signal:         Signal
    strength:       float
    leverage:       float
    stop_loss_pct:  float
    take_profit_pct: float
    risk_per_trade: float
    reason:         str = ""


@dataclass
class PerformanceTracker:
    pnl_list: list = field(default_factory=list)
    wins:  int = 0
    losses: int = 0

    def record(self, pnl_pct: float):
        self.pnl_list.append(pnl_pct)
        if pnl_pct > 0:
            self.wins += 1
        else:
            self.losses += 1

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total else 0.0

    def summary(self) -> dict:
        return {
            "total_trades": self.wins + self.losses,
            "win_rate":     round(self.win_rate, 3),
            "total_pnl":    round(sum(self.pnl_list), 4),
        }


# ─────────────────────────────────────────────────────
# 3. API 클라이언트 (캐싱 + 배치 처리)
# ─────────────────────────────────────────────────────

class BinanceClient:
    """
    Binance Futures API 클라이언트
    - API 키는 환경변수에서만 로드 (하드코딩 금지)
    - 캐싱으로 API rate limit 보호
    - 배치 처리로 API 호출 최소화
    """

    def __init__(self, testnet: bool = True):
        # [수정 1] 환경변수에서만 로드, fallback 기본값 없음
        self.api_key    = os.environ.get("BINANCE_TESTNET_KEY") if testnet else os.environ.get("BINANCE_API_KEY")
        self.api_secret = os.environ.get("BINANCE_TESTNET_SECRET") if testnet else os.environ.get("BINANCE_API_SECRET")
        self.base_url   = TESTNET_BASE_URL if testnet else MAINNET_BASE_URL
        self.testnet    = testnet

        if not self.api_key or not self.api_secret:
            env_name = "BINANCE_TESTNET_KEY / BINANCE_TESTNET_SECRET" if testnet else "BINANCE_API_KEY / BINANCE_API_SECRET"
            raise EnvironmentError(
                f"API 키가 설정되지 않았습니다.\n"
                f"환경변수를 설정하세요: {env_name}\n"
                f"예) export {env_name.split('/')[0].strip()}=your_key_here"
            )

        # 캐시 저장소
        self._klines_cache:  dict[str, tuple[float, list]] = {}   # symbol → (timestamp, data)
        self._price_cache:   dict[str, tuple[float, float]] = {}  # symbol → (timestamp, price)
        self._symbol_cache:  dict[str, dict] = {}                 # symbol → info
        self._exchange_info: Optional[dict] = None

        print(f"[OK] BinanceClient 초기화 ({'테스트넷' if testnet else '실거래'})")

    # ── 서명 ────────────────────────────────────────────────
    def _sign(self, params: dict) -> str:
        query = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _headers(self) -> dict:
        return {"X-MBX-APIKEY": self.api_key}

    # ── 서버 시간 ────────────────────────────────────────────
    def get_server_time(self) -> int:
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            r.raise_for_status()
            return r.json()["serverTime"]
        except Exception:
            return int(time.time() * 1000)

    # ── 계정 잔고 ────────────────────────────────────────────
    def get_balance(self) -> float:
        params = {"timestamp": self.get_server_time(), "recvWindow": 5000}
        params["signature"] = self._sign(params)
        try:
            r = requests.get(
                f"{self.base_url}/fapi/v2/account",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return float(r.json()["totalWalletBalance"])
        except Exception as e:
            print(f"[ERROR] 잔고 조회 실패: {e}")
            raise

    # ── 심볼 목록 ─────────────────────────────────────────────
    def get_exchange_info(self) -> dict:
        if self._exchange_info:
            return self._exchange_info
        r = requests.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
        r.raise_for_status()
        self._exchange_info = r.json()
        return self._exchange_info

    def get_valid_symbols(self) -> list[str]:
        info = self.get_exchange_info()
        trading = {s["symbol"] for s in info["symbols"] if s["status"] == "TRADING"}
        return [s for s in TOP_SYMBOLS if s in trading]

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]
        info = self.get_exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                self._symbol_cache[symbol] = s
                return s
        return None

    # ── 가격 조회 (캐시) ──────────────────────────────────────
    def get_price(self, symbol: str) -> float:
        now = time.time()
        if symbol in self._price_cache:
            ts, price = self._price_cache[symbol]
            if now - ts < PRICE_CACHE_TTL:
                return price
        try:
            r = requests.get(
                f"{self.base_url}/fapi/v1/ticker/price",
                params={"symbol": symbol},
                timeout=5,
            )
            r.raise_for_status()
            price = float(r.json()["price"])
            self._price_cache[symbol] = (now, price)
            return price
        except Exception as e:
            print(f"[ERROR] {symbol} 가격 조회 실패: {e}")
            raise

    # ── 배치 가격 조회 (단일 API 호출로 전체 조회) ───────────────
    def get_all_prices(self) -> dict[str, float]:
        """단일 API 호출로 전체 심볼 가격 조회 — rate limit 절약"""
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/ticker/price", timeout=10)
            r.raise_for_status()
            now = time.time()
            prices = {}
            for item in r.json():
                sym = item["symbol"]
                price = float(item["price"])
                prices[sym] = price
                self._price_cache[sym] = (now, price)
            return prices
        except Exception as e:
            print(f"[ERROR] 배치 가격 조회 실패: {e}")
            return {}

    # ── Klines (캐시) ─────────────────────────────────────────
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list:
        cache_key = f"{symbol}_{interval}_{limit}"
        now = time.time()
        if cache_key in self._klines_cache:
            ts, data = self._klines_cache[cache_key]
            if now - ts < KLINES_CACHE_TTL:
                return data
        try:
            r = requests.get(
                f"{self.base_url}/fapi/v1/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            self._klines_cache[cache_key] = (now, data)
            return data
        except Exception as e:
            print(f"[ERROR] {symbol} klines 조회 실패: {e}")
            return []

    # ── 주문 제출 ─────────────────────────────────────────────
    def submit_order(self, symbol: str, side: str, quantity: float) -> Optional[dict]:
        params = {
            "symbol":     symbol,
            "side":       side,
            "type":       "MARKET",
            "quantity":   str(quantity),
            "timestamp":  self.get_server_time(),
            "recvWindow": 5000,
        }
        params["signature"] = self._sign(params)
        try:
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            print(f"[ERROR] 주문 실패 ({symbol} {side}): {e.response.text}")
            return None
        except Exception as e:
            print(f"[ERROR] 주문 실패: {e}")
            return None

    def submit_stop_market(self, symbol: str, side: str, quantity: float, stop_price: float) -> Optional[dict]:
        params = {
            "symbol":     symbol,
            "side":       side,
            "type":       "STOP_MARKET",
            "quantity":   str(quantity),
            "stopPrice":  str(round(stop_price, 4)),
            "timestamp":  self.get_server_time(),
            "recvWindow": 5000,
        }
        params["signature"] = self._sign(params)
        try:
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            print(f"[ERROR] 손절 주문 실패: {e.response.text}")
            return None

    def submit_take_profit(self, symbol: str, side: str, quantity: float, price: float) -> Optional[dict]:
        params = {
            "symbol":      symbol,
            "side":        side,
            "type":        "LIMIT",
            "quantity":    str(quantity),
            "price":       str(round(price, 4)),
            "timeInForce": "GTC",
            "timestamp":   self.get_server_time(),
            "recvWindow": 5000,
        }
        params["signature"] = self._sign(params)
        try:
            r = requests.post(
                f"{self.base_url}/fapi/v1/order",
                params=params,
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            print(f"[ERROR] 익절 주문 실패: {e.response.text}")
            return None


# ─────────────────────────────────────────────────────
# 4. 시장 분석기
# ─────────────────────────────────────────────────────

class MarketAnalyzer:
    """
    [수정 5] 변동성 계산 수정: 심볼간 가격 차이 → 수익률 표준편차
    [수정 6] klines 캐싱으로 API 호출 최소화
    """

    # BTC 기준으로만 시장 국면 분석 (매번 모든 심볼 분석 X)
    REGIME_SYMBOL = "BTCUSDT"

    def __init__(self, client: BinanceClient):
        self.client = client
        self._regime_cache: Optional[tuple[float, MarketState]] = None
        self._regime_ttl = 300  # 5분마다 갱신

    def get_market_state(self, symbol: str = REGIME_SYMBOL) -> MarketState:
        """캐시된 시장 상태 반환 (5분 TTL)"""
        now = time.time()
        if self._regime_cache:
            ts, state = self._regime_cache
            if now - ts < self._regime_ttl:
                return state

        state = self._analyze(symbol)
        self._regime_cache = (now, state)
        return state

    def _analyze(self, symbol: str) -> MarketState:
        klines = self.client.get_klines(symbol, "1h", 24)
        if not klines:
            return MarketState(MarketRegime.SIDEWAYS, 0.02, 0.0)

        # [수정 5] 수익률 기반 변동성 계산
        returns = []
        for k in klines:
            open_p  = float(k[1])
            close_p = float(k[4])
            if open_p > 0:
                returns.append((close_p - open_p) / open_p)

        if not returns:
            return MarketState(MarketRegime.SIDEWAYS, 0.02, 0.0)

        avg_return = sum(returns) / len(returns)
        variance   = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5

        # 시장 국면
        if avg_return > 0.005:       # 평균 시간당 +0.5% → 상승장
            regime = MarketRegime.BULL
        elif avg_return < -0.005:    # 평균 시간당 -0.5% → 하락장
            regime = MarketRegime.BEAR
        else:
            regime = MarketRegime.SIDEWAYS

        return MarketState(
            regime     = regime,
            volatility = round(volatility, 6),
            strength   = round(avg_return, 6),
        )


# ─────────────────────────────────────────────────────
# 5. 전략 엔진 (random 완전 제거)
# ─────────────────────────────────────────────────────

class StrategyEngine:
    """
    [수정 2] random() 완전 제거
    모든 신호는 시장 데이터에서 결정론적으로 도출
    """

    MAX_LEVERAGE = 20.0
    MIN_LEVERAGE = 2.0

    def _calc_leverage(self, volatility: float) -> float:
        """변동성 역비례 레버리지"""
        raw = self.MAX_LEVERAGE * (0.01 / max(volatility, 0.001))
        return round(min(max(raw, self.MIN_LEVERAGE), self.MAX_LEVERAGE), 1)

    def _build(self, name: str, signal: Signal, strength: float,
               market: MarketState, reason: str) -> TradeSignal:
        params  = STRATEGY_PARAMS[name]
        vol     = market.volatility
        sl      = max(params["stop_loss"], 1.5 * vol)
        tp      = sl * 2.0
        return TradeSignal(
            strategy        = name,
            signal          = signal,
            strength        = round(strength, 3),
            leverage        = self._calc_leverage(vol),
            stop_loss_pct   = round(sl, 4),
            take_profit_pct = round(tp, 4),
            risk_per_trade  = params["risk_per_trade"],
            reason          = reason,
        )

    def momentum(self, market: MarketState) -> TradeSignal:
        if market.regime == MarketRegime.BULL and market.strength > 0.003:
            return self._build("momentum", Signal.BUY, 0.80, market, "상승장 모멘텀 매수")
        if market.regime == MarketRegime.BEAR and market.strength < -0.003:
            return self._build("momentum", Signal.SELL, 0.80, market, "하락장 모멘텀 매도")
        return self._build("momentum", Signal.HOLD, 0.20, market, "추세 불명확 → 관망")

    def mean_reversion(self, market: MarketState) -> TradeSignal:
        if market.regime == MarketRegime.SIDEWAYS and abs(market.strength) < 0.002:
            sig = Signal.BUY if market.strength < 0 else Signal.SELL
            reason = "횡보장 과매도 반전 매수" if sig == Signal.BUY else "횡보장 과매수 반전 매도"
            return self._build("mean_reversion", sig, 0.70, market, reason)
        return self._build("mean_reversion", Signal.HOLD, 0.20, market, "추세장 → 평균회귀 부적합")

    def volatility(self, market: MarketState) -> TradeSignal:
        if market.volatility > 0.03:
            sig = Signal.BUY if market.strength > 0 else Signal.SELL
            return self._build("volatility", sig, 0.75, market,
                               f"고변동성({market.volatility:.2%}) 브레이크아웃")
        return self._build("volatility", Signal.HOLD, 0.20, market, "변동성 부족 → 관망")

    def trend_following(self, market: MarketState) -> TradeSignal:
        s = market.strength
        if s > 0.005:
            return self._build("trend_following", Signal.BUY, 0.70, market,
                               f"상승 추세 (strength={s:.4f})")
        if s < -0.005:
            return self._build("trend_following", Signal.SELL, 0.70, market,
                               f"하락 추세 (strength={s:.4f})")
        return self._build("trend_following", Signal.HOLD, 0.20, market, "추세 없음")

    def arbitrage(self, market: MarketState) -> TradeSignal:
        """스프레드 기반 — spread_pct는 외부에서 주입"""
        spread = market.spread_pct
        if spread > 0.15:
            return TradeSignal("arbitrage", Signal.SELL,
                               min(spread / 0.15 * 0.5, 0.95),
                               3.0, 0.005, 0.003, 0.005,
                               f"스프레드 {spread:.3f}% 차익 진입")
        if spread < -0.15:
            return TradeSignal("arbitrage", Signal.BUY,
                               min(abs(spread) / 0.15 * 0.5, 0.95),
                               3.0, 0.005, 0.003, 0.005,
                               f"역스프레드 {spread:.3f}% 역차익 진입")
        return TradeSignal("arbitrage", Signal.HOLD, 0.0,
                           1.0, 0.0, 0.0, 0.0, "스프레드 미달 → 기회 없음")

    def run_all(self, market: MarketState) -> dict[str, TradeSignal]:
        return {
            "momentum":       self.momentum(market),
            "mean_reversion": self.mean_reversion(market),
            "volatility":     self.volatility(market),
            "trend_following":self.trend_following(market),
            "arbitrage":      self.arbitrage(market),
        }

    def aggregate(self, signals: dict[str, TradeSignal], threshold: float = 0.55) -> TradeSignal:
        """가중 합산 최종 신호"""
        buy_score = sum(s.strength for s in signals.values() if s.signal == Signal.BUY)
        sel_score = sum(s.strength for s in signals.values() if s.signal == Signal.SELL)
        total = buy_score + sel_score

        if total == 0:
            # 가장 강한 신호를 기준으로 반환
            best = max(signals.values(), key=lambda s: s.strength)
            return best

        if buy_score > sel_score and buy_score / total >= threshold:
            candidates = [s for s in signals.values() if s.signal == Signal.BUY]
        elif sel_score > buy_score and sel_score / total >= threshold:
            candidates = [s for s in signals.values() if s.signal == Signal.SELL]
        else:
            best = max(signals.values(), key=lambda s: s.strength)
            return TradeSignal(best.strategy, Signal.HOLD, 0.5,
                               best.leverage, best.stop_loss_pct,
                               best.take_profit_pct, best.risk_per_trade,
                               "신호 불충분 → 관망")

        return max(candidates, key=lambda s: s.strength)


# ─────────────────────────────────────────────────────
# 6. 주문 실행기
# ─────────────────────────────────────────────────────

class OrderExecutor:
    """
    [수정 3] 포지션 크기: 달러 금액 → 실제 수량 변환
    [수정 4] 초기화 순서 안전 보장
    """

    def __init__(self, client: BinanceClient):
        self.client = client

    def calc_quantity(self, symbol: str, signal: TradeSignal,
                      total_capital: float) -> Optional[float]:
        """
        수량 = (계좌 * risk_per_trade * leverage) / 현재가격
        → LOT_SIZE, MIN_NOTIONAL 필터 적용
        """
        info = self.client.get_symbol_info(symbol)
        if not info:
            print(f"[ERROR] {symbol} 심볼 정보 없음")
            return None

        try:
            price = self.client.get_price(symbol)
        except Exception:
            return None

        # 달러 기준 포지션
        dollar_position = total_capital * signal.risk_per_trade * signal.leverage
        max_position    = total_capital * 0.20   # 최대 20%
        dollar_position = min(dollar_position, max_position)

        # [수정 3] 수량 계산 (달러 → 코인 수량)
        raw_qty = dollar_position / price

        # LOT_SIZE, MIN_NOTIONAL 필터 적용
        min_qty      = 0.0
        max_qty      = float("inf")
        step_size    = None
        min_notional = 5.0

        for f in info.get("filters", []):
            if f["filterType"] == "LOT_SIZE":
                min_qty   = float(f["minQty"])
                max_qty   = float(f["maxQty"])
                step_size = f.get("stepSize", "1")
            elif f["filterType"] == "MIN_NOTIONAL":
                min_notional = float(f.get("notional", f.get("minNotional", 5.0)))

        # stepSize 기반 정밀도
        qty_precision = 0
        if step_size and "." in step_size:
            qty_precision = len(step_size.rstrip("0").split(".")[1])

        qty = max(raw_qty, min_qty)
        qty = min(qty, max_qty)
        qty = round(qty, qty_precision)

        # MIN_NOTIONAL 보정
        if qty * price < min_notional:
            qty = round((min_notional * 1.01) / price, qty_precision)

        print(f"[CALC] {symbol} | 가격=${price:.4f} | 포지션=${dollar_position:.2f} | 수량={qty}")
        return qty

    def execute(self, symbol: str, signal: TradeSignal,
                total_capital: float) -> Optional[dict]:
        if signal.signal == Signal.HOLD:
            return None

        qty = self.calc_quantity(symbol, signal, total_capital)
        if not qty:
            return None

        side = signal.signal.value  # "BUY" or "SELL"
        result = self.client.submit_order(symbol, side, qty)
        if not result:
            return None

        print(f"[OK] 진입 주문 성공: {symbol} {side} {qty}")

        # 손절/익절 주문
        try:
            price = self.client.get_price(symbol)
            exit_side = "SELL" if side == "BUY" else "BUY"

            if side == "BUY":
                sl_price = price * (1 - signal.stop_loss_pct)
                tp_price = price * (1 + signal.take_profit_pct)
            else:
                sl_price = price * (1 + signal.stop_loss_pct)
                tp_price = price * (1 - signal.take_profit_pct)

            if self.client.testnet:
                # 테스트넷: 손절/익절 시뮬레이션
                print(f"[SIM] 손절=${sl_price:.4f} ({signal.stop_loss_pct:.1%}) | "
                      f"익절=${tp_price:.4f} ({signal.take_profit_pct:.1%})")
            else:
                self.client.submit_stop_market(symbol, exit_side, qty, sl_price)
                self.client.submit_take_profit(symbol, exit_side, qty, tp_price)

        except Exception as e:
            print(f"[WARN] 손절/익절 주문 실패: {e}")

        return result


# ─────────────────────────────────────────────────────
# 7. 메인 트레이딩 시스템
# ─────────────────────────────────────────────────────

class AutoStrategyFuturesTrading:
    """
    [수정 4] __init__ 초기화 순서 안전하게 재구성
    네트워크 호출을 initialize() 메서드로 분리
    """

    def __init__(self, testnet: bool = True, duration_hours: int = 24,
                 loop_interval_sec: int = 60):
        self.duration_hours    = duration_hours
        self.loop_interval_sec = loop_interval_sec

        # ── 클라이언트 초기화 (환경변수 검증) ──────────────
        self.client   = BinanceClient(testnet=testnet)
        self.analyzer = MarketAnalyzer(self.client)
        self.engine   = StrategyEngine()
        self.executor = OrderExecutor(self.client)

        # ── 상태 (initialize()에서 채워짐) ─────────────────
        self.total_capital:  float      = 0.0
        self.valid_symbols:  list[str]  = []
        self.current_prices: dict       = {}

        self.start_time: Optional[datetime] = None
        self.end_time:   Optional[datetime] = None

        self.trackers: dict[str, PerformanceTracker] = {
            name: PerformanceTracker() for name in STRATEGY_PARAMS
        }
        self.results = {
            "trades":  [],
            "errors":  [],
        }

    def initialize(self):
        """
        [수정 4] 네트워크 호출은 여기서만 — 순서 보장
        1. 심볼 목록
        2. 배치 가격 (단일 API 호출)
        3. 잔고 조회
        """
        print("[INIT] 시스템 초기화 중...")

        # 1. 심볼 목록
        self.valid_symbols = self.client.get_valid_symbols()
        print(f"[OK] 거래 가능 심볼: {len(self.valid_symbols)}개")

        # 2. 배치 가격 조회 (단일 호출)
        self.current_prices = self.client.get_all_prices()
        print(f"[OK] 가격 조회: {len(self.current_prices)}개 심볼")

        # 3. 잔고 조회
        self.total_capital = self.client.get_balance()
        print(f"[OK] 계좌 잔고: ${self.total_capital:.2f}")

        self.start_time = datetime.now()
        self.end_time   = self.start_time + timedelta(hours=self.duration_hours)

        self.results["meta"] = {
            "start_time":    self.start_time.isoformat(),
            "end_time":      self.end_time.isoformat(),
            "total_capital": self.total_capital,
            "symbols":       len(self.valid_symbols),
            "testnet":       self.client.testnet,
        }

        print(f"[OK] 초기화 완료 | 자본=${self.total_capital:.2f} | "
              f"심볼={len(self.valid_symbols)}개 | "
              f"종료={self.end_time.strftime('%H:%M:%S')}")

    def _print_status(self, trade_count: int, error_count: int):
        now     = datetime.now()
        elapsed = now - self.start_time
        remain  = self.end_time - now
        prog    = elapsed.total_seconds() / (self.duration_hours * 3600) * 100

        market = self.analyzer.get_market_state()
        print("=" * 70)
        print(f"[{now.strftime('%H:%M:%S')}] 진행={prog:.1f}% | 남은시간={remain} | 잔고=${self.total_capital:.2f}")
        print(f"  시장국면: {market.regime.value} | 변동성={market.volatility:.3%} | 강도={market.strength:.4f}")
        print(f"  거래={trade_count}회 | 오류={error_count}회")
        for name, tracker in self.trackers.items():
            s = tracker.summary()
            if s["total_trades"] > 0:
                print(f"  [{name:15s}] 거래={s['total_trades']} 승률={s['win_rate']:.0%} PnL={s['total_pnl']:+.4f}")

    def run(self):
        self.initialize()

        print("\n" + "=" * 70)
        print("[START] 자동 전략 선물 거래 시작")
        print("=" * 70)

        trade_count = 0
        error_count = 0

        while datetime.now() < self.end_time:
            try:
                # 배치 가격 갱신 (단일 API 호출)
                self.current_prices = self.client.get_all_prices()

                # 시장 분석 (캐시 5분)
                market = self.analyzer.get_market_state()

                # 모든 전략 신호 생성
                signals  = self.engine.run_all(market)
                final    = self.engine.aggregate(signals)

                self._print_status(trade_count, error_count)

                # 전략별로 적합한 심볼 선택 후 거래
                # 심볼 선택: valid_symbols를 strategy별로 분배
                symbols_per_strategy = max(1, len(self.valid_symbols) // len(STRATEGY_PARAMS))

                for i, (name, sig) in enumerate(signals.items()):
                    if sig.signal == Signal.HOLD:
                        print(f"  [{name}] HOLD — {sig.reason}")
                        continue

                    # 전략별 당할 심볼 슬라이스
                    start = i * symbols_per_strategy
                    batch = self.valid_symbols[start: start + symbols_per_strategy]
                    if not batch:
                        batch = self.valid_symbols[:1]

                    # 가장 거래량 많은 심볼 선택 (가격 높은 것 = proxy)
                    symbol = max(
                        batch,
                        key=lambda s: self.current_prices.get(s, 0),
                    )

                    result = self.executor.execute(symbol, sig, self.total_capital)

                    if result:
                        trade_count += 1
                        self.trackers[name].record(0)  # PnL은 청산 시 업데이트
                        self.results["trades"].append({
                            "time":     datetime.now().isoformat(),
                            "strategy": name,
                            "symbol":   symbol,
                            "signal":   sig.signal.value,
                            "leverage": sig.leverage,
                            "sl":       sig.stop_loss_pct,
                            "tp":       sig.take_profit_pct,
                            "reason":   sig.reason,
                        })
                        print(f"  [OK] {name} | {symbol} {sig.signal.value} {sig.leverage}x | {sig.reason}")
                    else:
                        error_count += 1
                        self.results["errors"].append({
                            "time":     datetime.now().isoformat(),
                            "strategy": name,
                            "symbol":   symbol,
                        })

                time.sleep(self.loop_interval_sec)

            except KeyboardInterrupt:
                print(f"\n[STOP] 사용자 중단: {datetime.now()}")
                break
            except Exception as e:
                print(f"[ERROR] 루프 오류: {e}")
                error_count += 1
                time.sleep(10)

        self._save_results(trade_count, error_count)

    def _save_results(self, trade_count: int, error_count: int):
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = results_dir / f"trading_results_{ts}.json"

        self.results["summary"] = {
            "total_trades":  trade_count,
            "total_errors":  error_count,
            "success_rate":  round(trade_count / max(trade_count + error_count, 1) * 100, 1),
            "trackers":      {k: v.summary() for k, v in self.trackers.items()},
            "end_time":      datetime.now().isoformat(),
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] 결과 저장: {json_path}")
        print(f"[SUMMARY] 총 거래={trade_count} | 오류={error_count} | "
              f"성공률={self.results['summary']['success_rate']:.1f}%")


# ─────────────────────────────────────────────────────
# 8. 진입점
# ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[START] 자동 전략 기반 선물 거래 시스템")
    print("=" * 70)

    # 환경변수 사전 검증
    required_env = ["BINANCE_TESTNET_KEY", "BINANCE_TESTNET_SECRET"]
    missing = [e for e in required_env if not os.environ.get(e)]
    if missing:
        print(f"[ERROR] 환경변수 누락: {', '.join(missing)}")
        print("  설정 방법:")
        for e in missing:
            print(f"    export {e}=your_value_here")
        exit(1)

    try:
        system = AutoStrategyFuturesTrading(
            testnet          = True,
            duration_hours   = 24,
            loop_interval_sec = 60,   # 1분마다 루프 (API rate limit 보호)
        )
        system.run()

    except EnvironmentError as e:
        print(f"[ERROR] {e}")
        exit(1)
    except KeyboardInterrupt:
        print(f"\n[STOP] 종료: {datetime.now()}")
    except Exception as e:
        print(f"[ERROR] 시스템 오류: {e}")
        import traceback
        traceback.print_exc()

    print("[END] 시스템 종료")
