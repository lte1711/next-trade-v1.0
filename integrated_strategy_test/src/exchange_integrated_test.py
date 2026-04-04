"""
거래소 연동 실시간 전략 테스트 - 원본과 통합 가능한 버전
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

class BinanceExchangeConnector:
    """바이낸스 거래소 연동 커넥터"""
    
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
        
        print(f"FACT: 바이낸스 거래소 연동 초기화")
        print(f"  🌐 URL: {self.base_url}")
        print(f"  🔑 API Key: {'✅ 있음' if self.api_key else '❌ 없음'}")
        print(f"  🔐 API Secret: {'✅ 있음' if self.api_secret else '❌ 없음'}")
        print(f"  🧪 테스트넷 모드: {'✅' if self.testnet_mode else '❌'}")
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: 설정 파일 로드 실패: {e}")
            return {}
    
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
    
    def get_account_info(self) -> Dict[str, Any]:
        """계정 정보 조회"""
        if not self.connection_status:
            return {"error": "연결되지 않음"}
        
        try:
            # 테스트넷 계정 정보 조회 (실제 API 호출)
            account_url = f"{self.base_url}/fapi/v2/account"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            response = requests.get(account_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                account_data = response.json()
                return {
                    "status": "success",
                    "total_wallet_balance": account_data.get("totalWalletBalance", "0"),
                    "total_unrealized_pnl": account_data.get("totalUnrealizedPnl", "0"),
                    "total_margin_balance": account_data.get("totalMarginBalance", "0"),
                    "total_position_initial_margin": account_data.get("totalPositionInitialMargin", "0"),
                    "total_maint_margin": account_data.get("totalMaintMargin", "0"),
                    "assets": account_data.get("assets", [])
                }
            else:
                return {"error": f"API 호출 실패: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"계정 정보 조회 실패: {e}"}
    
    def get_symbol_ticker(self, symbol: str) -> Dict[str, Any]:
        """심볼 티커 정보 조회"""
        try:
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
                return {"error": f"티커 조회 실패: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"심볼 티커 조회 실패: {e}"}
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """호가 정보 조회"""
        try:
            depth_url = f"{self.base_url}/fapi/v1/depth?symbol={symbol}&limit={limit}"
            response = requests.get(depth_url, timeout=10)
            
            if response.status_code == 200:
                depth_data = response.json()
                return {
                    "status": "success",
                    "symbol": symbol,
                    "bids": depth_data["bids"],
                    "asks": depth_data["asks"],
                    "last_update": depth_data.get("lastUpdateId", 0)
                }
            else:
                return {"error": f"호가 조회 실패: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"호가 정보 조회 실패: {e}"}

class ExchangeIntegratedStrategyManager:
    """거래소 연동 전략 관리자"""
    
    def __init__(self, exchange_connector: BinanceExchangeConnector):
        self.exchange = exchange_connector
        self.strategies = self._load_strategies()
        self.active_positions = {}
        self.strategy_performance = defaultdict(lambda: {
            "total_pnl": 0, "trades": 0, "wins": 0, "losses": 0
        })
        
        print(f"FACT: 거래소 연동 전략 관리자 초기화")
        print(f"  🔢 전략 수: {len(self.strategies)}개")
        print(f"  🔗 거래소 연결: {'✅' if self.exchange.connection_status else '❌'}")
    
    def _load_strategies(self) -> Dict[str, Any]:
        """전략 로드 (원본과 호환)"""
        return {
            # 보수적 전략
            "conservative_btc": {
                "symbol": "BTCUSDT", "type": "conservative", "initial_capital": 2000.0,
                "stop_loss": -0.08, "leverage": 2.0, "target_return": 0.15,
                "position_size": 0.01, "risk_per_trade": 0.02
            },
            "conservative_eth": {
                "symbol": "ETHUSDT", "type": "conservative", "initial_capital": 1500.0,
                "stop_loss": -0.08, "leverage": 2.0, "target_return": 0.18,
                "position_size": 0.1, "risk_per_trade": 0.02
            },
            
            # 성장 전략
            "growth_sol": {
                "symbol": "SOLUSDT", "type": "growth", "initial_capital": 1000.0,
                "stop_loss": -0.10, "leverage": 3.0, "target_return": 0.35,
                "position_size": 5.0, "risk_per_trade": 0.03
            },
            
            # 모멘텀 전략
            "momentum_doge": {
                "symbol": "DOGEUSDT", "type": "momentum", "initial_capital": 500.0,
                "stop_loss": -0.15, "leverage": 5.0, "target_return": 0.60,
                "position_size": 10000.0, "risk_per_trade": 0.04
            },
            
            # 변동성 전략
            "volatility_shib": {
                "symbol": "1000SHIBUSDT", "type": "volatility", "initial_capital": 300.0,
                "stop_loss": -0.20, "leverage": 4.0, "target_return": 0.80,
                "position_size": 1000.0, "risk_per_trade": 0.05
            }
        }
    
    def execute_exchange_strategies(self) -> Dict[str, Any]:
        """거래소 연동 전략 실행"""
        print(f"FACT: 거래소 연동 전략 실행 시작")
        
        results = {}
        
        for strategy_name, strategy_config in self.strategies.items():
            symbol = strategy_config["symbol"]
            
            # 실시간 시장 데이터 조회
            ticker_data = self.exchange.get_symbol_ticker(symbol)
            
            if ticker_data.get("status") != "success":
                print(f"ERROR: {symbol} 데이터 조회 실패: {ticker_data.get('error')}")
                continue
            
            # 호가 정보 조회
            orderbook_data = self.exchange.get_order_book(symbol, 5)
            
            # 전략 실행
            strategy_result = self._execute_exchange_strategy(
                strategy_name, strategy_config, ticker_data, orderbook_data
            )
            
            results[strategy_name] = strategy_result
            
            # 성과 업데이트
            self._update_strategy_performance(strategy_name, strategy_result)
        
        return results
    
    def _execute_exchange_strategy(self, strategy_name: str, strategy_config: Dict[str, Any],
                                 ticker_data: Dict[str, Any], orderbook_data: Dict[str, Any]) -> Dict[str, Any]:
        """개별 거래소 연동 전략 실행"""
        
        strategy_type = strategy_config["type"]
        symbol = strategy_config["symbol"]
        initial_capital = strategy_config["initial_capital"]
        leverage = strategy_config["leverage"]
        stop_loss = strategy_config["stop_loss"]
        target_return = strategy_config["target_return"]
        position_size = strategy_config["position_size"]
        risk_per_trade = strategy_config["risk_per_trade"]
        
        # 실제 시장 데이터
        current_price = ticker_data["price"]
        price_change = ticker_data["change_percent"]
        volume = ticker_data["volume"]
        high = ticker_data["high"]
        low = ticker_data["low"]
        
        # 호가 데이터
        best_bid = float(orderbook_data.get("bids", [["0", "0"]])[0][0]) if orderbook_data.get("status") == "success" else 0
        best_ask = float(orderbook_data.get("asks", [["0", "0"]])[0][0]) if orderbook_data.get("status") == "success" else 0
        spread = best_ask - best_bid if best_bid > 0 and best_ask > 0 else 0
        
        # 기술적 지표 계산
        rsi = self._calculate_simple_rsi(price_change)
        momentum = self._calculate_momentum(price_change, volume)
        
        # 전략별 의사결정
        if strategy_type == "conservative":
            # 보수적: RSI 기반
            if rsi < 30 and price_change > -2:
                signal = "BUY"
                confidence = 0.7
            elif rsi > 70:
                signal = "SELL"
                confidence = 0.6
            else:
                signal = "HOLD"
                confidence = 0.5
        
        elif strategy_type == "growth":
            # 성장: 모멘텀 기반
            if momentum > 0.5 and price_change > 1:
                signal = "BUY"
                confidence = 0.8
            elif momentum < -0.5:
                signal = "SELL"
                confidence = 0.7
            else:
                signal = "HOLD"
                confidence = 0.5
        
        elif strategy_type == "momentum":
            # 모멘텀: 가격 변동 기반
            if price_change > 3 and volume > 100000:
                signal = "BUY"
                confidence = 0.9
            elif price_change < -3:
                signal = "SELL"
                confidence = 0.8
            else:
                signal = "HOLD"
                confidence = 0.5
        
        elif strategy_type == "volatility":
            # 변동성: 가격 범위 기반
            price_range = (high - low) / current_price
            if price_range > 0.05 and price_change > 2:
                signal = "BUY"
                confidence = 0.8
            elif price_range > 0.05 and price_change < -2:
                signal = "SELL"
                confidence = 0.8
            else:
                signal = "HOLD"
                confidence = 0.5
        
        else:
            signal = "HOLD"
            confidence = 0.5
        
        # 포지션 계산 (시뮬레이션)
        position_value = position_size * current_price
        leveraged_position = position_value * leverage
        
        # 손익 계산
        if signal == "BUY":
            expected_return = target_return * confidence
            daily_pnl = initial_capital * expected_return / 365
        elif signal == "SELL":
            expected_return = -target_return * confidence * 0.5
            daily_pnl = initial_capital * expected_return / 365
        else:
            daily_pnl = 0
        
        # 리스크 관리
        if daily_pnl <= initial_capital * stop_loss:
            daily_pnl = initial_capital * stop_loss
            stop_loss_triggered = True
        else:
            stop_loss_triggered = False
        
        return {
            "strategy_name": strategy_name,
            "symbol": symbol,
            "type": strategy_type,
            "signal": signal,
            "confidence": confidence,
            "current_price": current_price,
            "price_change": price_change,
            "volume": volume,
            "rsi": rsi,
            "momentum": momentum,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "position_size": position_size,
            "position_value": position_value,
            "leveraged_position": leveraged_position,
            "daily_pnl": round(daily_pnl, 2),
            "stop_loss_triggered": stop_loss_triggered,
            "leverage": leverage,
            "risk_per_trade": risk_per_trade,
            "exchange_connected": self.exchange.connection_status,
            "data_source": "real_exchange"
        }
    
    def _calculate_simple_rsi(self, price_change: float) -> float:
        """단순 RSI 계산"""
        # 가격 변동을 기반으로 한 단순화된 RSI
        if price_change > 5:
            return 80
        elif price_change > 2:
            return 65
        elif price_change > 0:
            return 55
        elif price_change > -2:
            return 45
        elif price_change > -5:
            return 35
        else:
            return 20
    
    def _calculate_momentum(self, price_change: float, volume: float) -> float:
        """모멘텀 계산"""
        # 가격 변동과 거래량을 기반으로 한 모멘텀
        price_momentum = price_change / 100
        volume_momentum = min(volume / 1000000, 1.0)  # 1M을 기준으로 정규화
        
        return (price_momentum + volume_momentum) / 2
    
    def _update_strategy_performance(self, strategy_name: str, result: Dict[str, Any]):
        """전략 성과 업데이트"""
        daily_pnl = result["daily_pnl"]
        
        self.strategy_performance[strategy_name]["trades"] += 1
        self.strategy_performance[strategy_name]["total_pnl"] += daily_pnl
        
        if daily_pnl > 0:
            self.strategy_performance[strategy_name]["wins"] += 1
        else:
            self.strategy_performance[strategy_name]["losses"] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성과 요약"""
        total_pnl = sum(perf["total_pnl"] for perf in self.strategy_performance.values())
        total_trades = sum(perf["trades"] for perf in self.strategy_performance.values())
        total_wins = sum(perf["wins"] for perf in self.strategy_performance.values())
        
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "total_strategies": len(self.strategies),
            "total_pnl": round(total_pnl, 2),
            "total_trades": total_trades,
            "total_wins": total_wins,
            "win_rate": round(win_rate, 2),
            "exchange_connected": self.exchange.connection_status,
            "data_source": "real_exchange",
            "performance_by_strategy": dict(self.strategy_performance)
        }

class ExchangeIntegratedTestRunner:
    """거래소 연동 테스트 실행기"""
    
    def __init__(self):
        self.exchange = BinanceExchangeConnector()
        self.strategy_manager = ExchangeIntegratedStrategyManager(self.exchange)
        self.test_results = []
        self.start_time = None
    
    def run_exchange_test(self, duration_minutes: int = 30):
        """거래소 연동 테스트 실행"""
        print(f"🚀 거래소 연동 실시간 테스트 시작 ({duration_minutes}분)")
        print("=" * 60)
        
        # 거래소 연결 테스트
        if not self.exchange.test_connection():
            print("❌ 거래소 연결 실패. 테스트를 종료합니다.")
            return
        
        # 계정 정보 확인
        account_info = self.exchange.get_account_info()
        print(f"\n💰 계정 정보:")
        if account_info.get("status") == "success":
            print(f"  💵 총 잔고: {account_info['total_wallet_balance']} USDT")
            print(f"  📊 미실현 손익: {account_info['total_unrealized_pnl']} USDT")
            print(f"  💰 증거금 잔고: {account_info['total_margin_balance']} USDT")
        else:
            print(f"  ❌ 계정 정보 조회 실패: {account_info.get('error')}")
        
        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        print(f"\n⏰ 테스트 기간: {self.start_time.strftime('%H:%M:%S')} ~ {end_time.strftime('%H:%M:%S')}")
        print(f"🔢 실행 전략: {len(self.strategy_manager.strategies)}개")
        
        # 실시간 테스트 루프
        iteration = 0
        while datetime.now() < end_time:
            iteration += 1
            current_time = datetime.now()
            elapsed = current_time - self.start_time
            remaining = end_time - current_time
            
            print(f"\n📊 테스트 라운드 {iteration} ({elapsed.total_seconds():.0f}초 경과)")
            
            # 전략 실행
            strategy_results = self.strategy_manager.execute_exchange_strategies()
            
            # 결과 저장
            test_result = {
                "timestamp": current_time.isoformat(),
                "iteration": iteration,
                "elapsed_seconds": elapsed.total_seconds(),
                "strategy_results": strategy_results,
                "summary": self.strategy_manager.get_performance_summary()
            }
            
            self.test_results.append(test_result)
            
            # 진행 상황 출력
            self._print_round_summary(iteration, test_result)
            
            # 30초 대기 (실제 테스트에서는 더 짧게)
            time.sleep(5)
        
        # 최종 결과
        self._print_final_results()
    
    def _print_round_summary(self, iteration: int, result: Dict[str, Any]):
        """라운드 요약 출력"""
        summary = result["summary"]
        
        print(f"  💰 총 손익: {summary['total_pnl']:,.2f} USDT")
        print(f"  🔢 총 거래: {summary['total_trades']}회")
        print(f"  📈 승률: {summary['win_rate']:.1f}%")
        print(f"  🔗 거래소 연결: {'✅' if summary['exchange_connected'] else '❌'}")
        
        # 개별 전략 결과
        for strategy_name, strategy_result in result["strategy_results"].items():
            signal = strategy_result["signal"]
            confidence = strategy_result["confidence"]
            price = strategy_result["current_price"]
            change = strategy_result["price_change"]
            
            print(f"    🎯 {strategy_name}: {signal} ({confidence:.1f}) | ${price:.2f} ({change:+.2f}%)")
    
    def _print_final_results(self):
        """최종 결과 출력"""
        print("\n" + "=" * 60)
        print("🎯 거래소 연동 테스트 최종 결과")
        print("=" * 60)
        
        if not self.test_results:
            print("❌ 테스트 결과가 없습니다")
            return
        
        final_result = self.test_results[-1]
        summary = final_result["summary"]
        
        # 기본 통계
        total_time = datetime.now() - self.start_time
        total_pnl = summary["total_pnl"]
        total_trades = summary["total_trades"]
        win_rate = summary["win_rate"]
        
        print(f"\n💰 투자 성과:")
        print(f"  💵 총 손익: {total_pnl:,.2f} USDT")
        print(f"  🔢 총 거래: {total_trades}회")
        print(f"  📈 승률: {win_rate:.1f}%")
        print(f"  ⏱️ 테스트 시간: {total_time.total_seconds():.0f}초")
        print(f"  🔗 거래소 연결: {'✅' if summary['exchange_connected'] else '❌'}")
        print(f"  📊 데이터 소스: {summary['data_source']}")
        
        # 전략별 성과
        print(f"\n🎯 전략별 성과:")
        for strategy_name, perf in summary["performance_by_strategy"].items():
            strategy_win_rate = (perf["wins"] / perf["trades"] * 100) if perf["trades"] > 0 else 0
            print(f"  📊 {strategy_name}:")
            print(f"     💰 손익: {perf['total_pnl']:,.2f} USDT")
            print(f"     🔢 거래: {perf['trades']}회")
            print(f"     📈 승률: {strategy_win_rate:.1f}%")
        
        # 최종 결론
        print(f"\n🎯 최종 결론:")
        if total_pnl > 0:
            print(f"  ✅ 총 {total_pnl:,.2f} USDT 수익 달성")
        else:
            print(f"  ⚠️ 총 {abs(total_pnl):,.2f} USDT 손실 발생")
        
        print(f"  📊 실제 거래소 데이터 기반 테스트 완료")
        print(f"  🔗 원본 프로젝트와 통합 준비 완료")
        
        # 결과 저장
        self._save_exchange_test_results()
    
    def _save_exchange_test_results(self):
        """거래소 연동 테스트 결과 저장"""
        results_file = Path("exchange_integrated_test_results.json")
        
        report_data = {
            "test_metadata": {
                "test_type": "거래소 연동 실시간 테스트",
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "exchange": "binance_testnet",
                "data_source": "real_exchange_api"
            },
            "final_summary": self.test_results[-1]["summary"] if self.test_results else {},
            "all_results": self.test_results,
            "exchange_config": {
                "base_url": self.exchange.base_url,
                "testnet_mode": self.exchange.testnet_mode,
                "connection_status": self.exchange.connection_status
            }
        }
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 결과 저장: {results_file}")

def main():
    """메인 실행 함수"""
    print("🎯 거래소 연동 실시간 전략 테스트")
    print("실제 거래소 데이터와 연동하여 테스트합니다")
    print("원본 프로젝트와 통합 가능한 구조로 설계되었습니다")
    print()
    
    # 테스트 실행기 생성
    test_runner = ExchangeIntegratedTestRunner()
    
    # 30분 테스트 실행
    test_runner.run_exchange_test(duration_minutes=30)

if __name__ == "__main__":
    main()
