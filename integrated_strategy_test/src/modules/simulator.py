"""
Main simulator orchestration for the modular trading workflow.
"""

import io
import time
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List

from .market_analyzer import MarketAnalyzer
from .portfolio_manager import PortfolioManager
from .realtime_data import RealTimeDataFetcher


class ModularTradingSimulator:
    """Coordinates analysis, selection, portfolio updates, and reporting."""

    def __init__(self, symbol_count: int = 10, replacement_threshold: float = -0.8):
        self.symbol_count = symbol_count
        self.replacement_threshold = replacement_threshold

        self.market_analyzer = MarketAnalyzer()
        self.portfolio_manager = PortfolioManager(initial_capital=1000.0, trading_fee=0.0004)
        self.realtime_fetcher = RealTimeDataFetcher()

        self.market_regime_thresholds = {
            "EXTREME": 70.0,
            "HIGH_VOLATILITY": 75.0,
            "NORMAL": 80.0,
        }

        self.market_regime = "NORMAL"
        self.current_strategy = "balanced"
        self.simulation_start_time: datetime | None = None
        self.simulation_end_time: datetime | None = None

    def analyze_market_regime(self) -> str:
        """Classify the market from average absolute 24h changes."""
        volatility = self._calculate_market_volatility()
        if volatility > 5.0:
            return "EXTREME"
        if volatility > 2.5:
            return "HIGH_VOLATILITY"
        return "NORMAL"

    def _calculate_market_volatility(self) -> float:
        """Approximate market volatility from top symbols' 24h changes."""
        try:
            top_symbols = self.market_analyzer.get_top_volume_symbols(20)
            if not top_symbols:
                return 2.5

            changes = [abs(symbol_data.get("change_percent", 0)) for symbol_data in top_symbols]
            return sum(changes) / len(changes)

        except Exception as exc:
            print(f"  market volatility calculation failed: {exc}")
            return 2.5

    def evaluate_profitability_potential(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep only symbols whose bullish and profit potential clear the regime threshold."""
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)

        profitable_symbols: List[Dict[str, Any]] = []
        for symbol_data in symbols:
            bullish_score = symbol_data.get("bullish_score", 0)
            if bullish_score < current_threshold:
                continue

            profit_potential = self.realtime_fetcher._calculate_profit_potential(symbol_data)
            if profit_potential >= current_threshold:
                symbol_data["profit_potential"] = profit_potential
                profitable_symbols.append(symbol_data)

        profitable_symbols.sort(key=lambda item: item["profit_potential"], reverse=True)
        return profitable_symbols

    def select_optimal_symbols(self, profitable_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select the best symbols allowed by the current regime."""
        if self.market_regime == "EXTREME":
            max_symbols = min(self.symbol_count, 5)
        elif self.market_regime == "HIGH_VOLATILITY":
            max_symbols = min(self.symbol_count, 7)
        else:
            max_symbols = self.symbol_count

        return profitable_symbols[:max_symbols]

    def dynamic_portfolio_rebalancing(self) -> bool:
        """Remove weak positions and add strong candidates."""
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)

        current_portfolio = self.portfolio_manager.get_current_portfolio()
        current_investments = current_portfolio["investments"]

        symbols_to_remove: List[str] = []
        for symbol, investment in current_investments.items():
            real_time_data = self._run_quietly(self.realtime_fetcher.get_real_time_symbol_data, [symbol])
            if not real_time_data:
                continue

            current_symbol_data = real_time_data[0]
            investment["current_price"] = current_symbol_data["price"]
            current_value = investment["shares"] * current_symbol_data["price"]
            current_pnl = current_value - investment["net_investment"]
            current_pnl_percent = (current_pnl / investment["net_investment"]) * 100 if investment["net_investment"] else 0
            current_potential = self.realtime_fetcher._calculate_profit_potential(current_symbol_data)

            if current_pnl_percent <= self.replacement_threshold:
                symbols_to_remove.append(symbol)
            elif current_potential < current_threshold:
                symbols_to_remove.append(symbol)

        available_symbols: List[Dict[str, Any]] = []
        top_volume_symbols = self._run_quietly(self.market_analyzer.get_top_volume_symbols, 80)
        if top_volume_symbols:
            candidate_symbols = [item["symbol"] for item in top_volume_symbols]
            real_time_candidates = self._run_quietly(self.realtime_fetcher.get_real_time_symbol_data, candidate_symbols)
            high_potential_symbols = self._run_quietly(
                self.realtime_fetcher.find_high_potential_symbols,
                real_time_candidates, current_threshold
            )

            for symbol_data in high_potential_symbols:
                if symbol_data["symbol"] not in current_investments:
                    available_symbols.append(symbol_data)

        rebalancing_made = False
        for symbol in symbols_to_remove:
            removal_result = self._run_quietly(self.portfolio_manager.remove_investment, symbol)
            if removal_result:
                rebalancing_made = True

        if available_symbols:
            open_slots = max(self.symbol_count - len(self.portfolio_manager.investments), 0)
            affordable_slots = int(self.portfolio_manager.cash_balance // 100.0)
            max_new_symbols = min(len(available_symbols), open_slots, affordable_slots)
            new_symbols = available_symbols[:max_new_symbols]

            for symbol_data in new_symbols:
                if self._run_quietly(
                    self.portfolio_manager.add_investment,
                    symbol_data["symbol"],
                    symbol_data,
                    amount=100.0,
                ):
                    rebalancing_made = True

        return rebalancing_made

    def run_simulation(self, duration_minutes: int = 30, update_interval: int = 3) -> Dict[str, Any]:
        """Run the modular simulation for the requested duration."""
        self.simulation_start_time = datetime.now()
        self.simulation_end_time = self.simulation_start_time + timedelta(minutes=duration_minutes)

        top_volume_symbols = self._run_quietly(self.market_analyzer.get_top_volume_symbols, 80)
        if not top_volume_symbols:
            return {"error": "Failed to fetch top volume symbols"}

        evaluated_symbols = self._run_quietly(
            self.market_analyzer.evaluate_bullish_potential_advanced,
            top_volume_symbols,
        )
        if not evaluated_symbols:
            return {"error": "Failed to evaluate bullish potential"}

        profitable_symbols = self.evaluate_profitability_potential(evaluated_symbols)
        if not profitable_symbols:
            return self._continuous_market_analysis(duration_minutes, update_interval)

        selected_symbols = self.select_optimal_symbols(profitable_symbols)
        if not selected_symbols:
            return self._continuous_market_analysis(duration_minutes, update_interval)

        allocations = self._run_quietly(self.portfolio_manager.allocate_capital_fixed_amount, selected_symbols)
        self._run_quietly(self.portfolio_manager.initialize_investments, allocations)
        self._print_position_snapshot("초기 진입")

        iteration = 0
        max_iterations = duration_minutes // update_interval
        while datetime.now() < self.simulation_end_time and iteration < max_iterations:
            iteration += 1
            self.market_regime = self._run_quietly(self.analyze_market_regime)

            current_prices = self._fetch_portfolio_prices()
            performance = self.portfolio_manager.update_investment_performance(current_prices=current_prices)
            self.dynamic_portfolio_rebalancing()
            self._print_position_snapshot(f"진행 {iteration}/{max_iterations}")

            time.sleep(update_interval * 60)

        return self._generate_final_report()

    def _continuous_market_analysis(self, duration_minutes: int, update_interval: int) -> Dict[str, Any]:
        """Continue scanning until a valid entry is found or time expires."""
        analysis_count = 0
        max_attempts = duration_minutes // update_interval
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        while datetime.now() < end_time and analysis_count < max_attempts:
            analysis_count += 1
            self.market_regime = self._run_quietly(self.analyze_market_regime)
            top_volume_symbols = self._run_quietly(self.market_analyzer.get_top_volume_symbols, 80)
            if top_volume_symbols:
                evaluated_symbols = self._run_quietly(
                    self.market_analyzer.evaluate_bullish_potential_advanced,
                    top_volume_symbols,
                )
                if evaluated_symbols:
                    profitable_symbols = self.evaluate_profitability_potential(evaluated_symbols)
                    if profitable_symbols:
                        selected_symbols = self.select_optimal_symbols(profitable_symbols)
                        if selected_symbols:
                            return self._start_simulation_with_symbols(
                                selected_symbols, duration_minutes, update_interval, end_time
                            )

            time.sleep(update_interval * 60)

        return {
            "error": f"No entry candidate found within {duration_minutes} minutes",
            "analysis_attempts": analysis_count,
            "duration_minutes": duration_minutes,
        }

    def _start_simulation_with_symbols(
        self,
        selected_symbols: List[Dict[str, Any]],
        duration_minutes: int,
        update_interval: int,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """Start the main loop immediately after a delayed entry signal appears."""
        allocations = self._run_quietly(self.portfolio_manager.allocate_capital_fixed_amount, selected_symbols)
        self._run_quietly(self.portfolio_manager.initialize_investments, allocations)
        self._print_position_snapshot("초기 진입")

        remaining_time = (end_time - datetime.now()).total_seconds() / 60
        if remaining_time <= 0:
            remaining_time = 1

        iteration = 0
        max_iterations = int(remaining_time // update_interval)
        while datetime.now() < end_time and iteration < max_iterations:
            iteration += 1
            self.market_regime = self._run_quietly(self.analyze_market_regime)

            current_prices = self._fetch_portfolio_prices()
            performance = self.portfolio_manager.update_investment_performance(current_prices=current_prices)
            self.dynamic_portfolio_rebalancing()
            self._print_position_snapshot(f"진행 {iteration}/{max_iterations}")

            time.sleep(update_interval * 60)

        return self._generate_final_report()

    def _fetch_portfolio_prices(self) -> Dict[str, float]:
        """Fetch the latest prices for the currently invested symbols."""
        symbols = list(self.portfolio_manager.investments.keys())
        if not symbols:
            return {}

        real_time_data = self._run_quietly(self.realtime_fetcher.get_real_time_symbol_data, symbols)
        return {item["symbol"]: item["price"] for item in real_time_data}

    def _generate_final_report(self) -> Dict[str, Any]:
        """Build the final simulation output structure."""
        portfolio_summary = self.portfolio_manager.get_performance_summary()
        if "error" in portfolio_summary:
            return {"error": portfolio_summary["error"]}

        metadata = {
            "simulation_start_time": self.simulation_start_time.isoformat(),
            "simulation_end_time": datetime.now().isoformat(),
            "duration_minutes": (datetime.now() - self.simulation_start_time).total_seconds() / 60,
            "total_rounds": len(self.portfolio_manager.performance_history),
            "initial_capital": self.portfolio_manager.initial_capital,
            "final_capital": portfolio_summary["total_value"],
            "cash_balance": portfolio_summary["cash_balance"],
            "total_pnl": portfolio_summary["total_pnl"],
            "pnl_percent": portfolio_summary["pnl_percent"],
            "total_fees_paid": portfolio_summary["total_fees_paid"],
            "net_pnl": portfolio_summary["net_pnl"],
            "net_pnl_percent": portfolio_summary["net_pnl_percent"],
            "invested_symbols": len(self.portfolio_manager.investments),
            "max_symbols": self.symbol_count,
            "final_market_regime": self.market_regime,
            "replacement_threshold": self.replacement_threshold,
        }

        return {
            "simulation_metadata": metadata,
            "individual_performance": portfolio_summary["individual_performance"],
            "performance_history": self.portfolio_manager.performance_history,
        }

    def _run_quietly(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run a noisy helper while suppressing stdout."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            return func(*args, **kwargs)

    def _print_position_snapshot(self, label: str) -> None:
        """Print only the active symbol summary requested by the user."""
        print(f"\n[{label}]")
        if not self.portfolio_manager.investments:
            print("진행중 심볼 없음")
            return

        print("심볼 | 초기진입액 | 변화액 | 변화 % | 상승평가율")
        for symbol, investment in self.portfolio_manager.investments.items():
            initial_amount = investment["initial_investment"]
            change_amount = investment["pnl"]
            change_percent = investment["pnl_percent"]
            profit_potential = investment.get("profit_potential", 0.0)
            print(
                f"{symbol} | "
                f"${initial_amount:.2f} | "
                f"${change_amount:+.2f} | "
                f"{change_percent:+.2f}% | "
                f"{profit_potential:.1f}%"
            )
