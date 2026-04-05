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
    """Coordinate symbol analysis, selection, portfolio updates, and reporting."""

    def __init__(self, symbol_count: int = 10, replacement_threshold: float = -0.8):
        self.symbol_count = symbol_count
        self.replacement_threshold = replacement_threshold

        self.market_analyzer = MarketAnalyzer()
        self.portfolio_manager = PortfolioManager(initial_capital=1000.0, trading_fee=0.0004)
        self.realtime_fetcher = RealTimeDataFetcher()

        self.market_regime_thresholds = {
            "EXTREME": 80.0,
            "HIGH_VOLATILITY": 78.0,
            "NORMAL": 80.0,
        }
        self.entry_buffer = 3.0
        self.exit_buffer = 3.0

        self.market_regime = "NORMAL"
        self.current_strategy = "balanced"
        self.simulation_start_time: datetime | None = None
        self.simulation_end_time: datetime | None = None
        self.last_snapshot_symbols: set[str] = set()
        self.last_snapshot_amounts: Dict[str, float] = {}

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

            changes = [abs(symbol_data.get("change_percent", 0.0)) for symbol_data in top_symbols]
            return sum(changes) / len(changes)
        except Exception as exc:
            print(f"  market volatility calculation failed: {exc}")
            return 2.5

    def evaluate_profitability_potential(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep symbols whose bullish score and profit potential clear the regime threshold."""
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
        profitable_symbols: List[Dict[str, Any]] = []

        for symbol_data in symbols:
            bullish_score = symbol_data.get("bullish_score", 0.0)
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
            max_symbols = min(self.symbol_count, 3)
        elif self.market_regime == "HIGH_VOLATILITY":
            max_symbols = min(self.symbol_count, 5)
        else:
            max_symbols = self.symbol_count
        return profitable_symbols[:max_symbols]

    def dynamic_portfolio_rebalancing(self) -> bool:
        """Remove weak positions and add strong candidates with churn control."""
        current_threshold = self.market_regime_thresholds.get(self.market_regime, 80.0)
        add_threshold = min(current_threshold + self.entry_buffer, 100.0)
        remove_threshold = max(current_threshold - self.exit_buffer, 0.0)

        current_investments = self.portfolio_manager.get_current_portfolio()["investments"]
        invested_symbols = list(current_investments.keys())
        held_symbol_data = {
            item["symbol"]: item
            for item in self._run_quietly(self.realtime_fetcher.get_real_time_symbol_data, invested_symbols)
        }

        symbols_to_remove: List[tuple[str, str]] = []
        for symbol, investment in current_investments.items():
            current_symbol_data = held_symbol_data.get(symbol)
            if not current_symbol_data:
                continue

            current_potential = self.realtime_fetcher._calculate_profit_potential(current_symbol_data)
            investment["profit_potential"] = current_potential
            investment["bullish_score"] = current_symbol_data.get("bullish_score", investment["bullish_score"])

            current_value = investment["shares"] * current_symbol_data["price"]
            current_pnl = current_value - investment["net_investment"]
            current_pnl_percent = (current_pnl / investment["net_investment"]) * 100 if investment["net_investment"] else 0.0
            holding_minutes = self.portfolio_manager.get_holding_minutes(symbol)

            investment["current_price"] = current_symbol_data["price"]
            investment["current_investment"] = current_value
            investment["pnl"] = current_pnl
            investment["pnl_percent"] = current_pnl_percent

            if current_pnl_percent <= self.replacement_threshold:
                symbols_to_remove.append((symbol, "loss_threshold"))
                continue

            if current_pnl_percent >= investment["take_profit"]:
                symbols_to_remove.append((symbol, "take_profit"))
                continue

            if holding_minutes < self.portfolio_manager.minimum_hold_minutes:
                continue

            if current_potential < remove_threshold:
                symbols_to_remove.append((symbol, "potential_drop"))

        available_symbols: List[Dict[str, Any]] = []
        top_volume_symbols = self._run_quietly(self.market_analyzer.get_top_volume_symbols, 80)
        if top_volume_symbols:
            candidate_symbols = [item["symbol"] for item in top_volume_symbols]
            real_time_candidates = self._run_quietly(self.realtime_fetcher.get_real_time_symbol_data, candidate_symbols)
            high_potential_symbols = self._run_quietly(
                self.realtime_fetcher.find_high_potential_symbols, real_time_candidates, add_threshold
            )

            for symbol_data in high_potential_symbols:
                symbol = symbol_data["symbol"]
                if symbol in current_investments:
                    continue
                if not self.portfolio_manager.can_reenter_symbol(symbol):
                    continue
                available_symbols.append(symbol_data)

        rebalancing_made = False
        for symbol, reason in symbols_to_remove:
            removal_result = self._run_quietly(self.portfolio_manager.remove_investment, symbol, reason)
            if removal_result:
                rebalancing_made = True

        if available_symbols:
            open_slots = max(self.symbol_count - len(self.portfolio_manager.investments), 0)
            affordable_slots = int(self.portfolio_manager.cash_balance // 100.0)
            max_new_symbols = min(len(available_symbols), open_slots, affordable_slots)
            new_symbols = available_symbols[:max_new_symbols]

            for symbol_data in new_symbols:
                added = self._run_quietly(
                    self.portfolio_manager.add_investment,
                    symbol_data["symbol"],
                    symbol_data,
                    amount=100.0,
                )
                if added:
                    rebalancing_made = True

        return rebalancing_made

    def run_simulation(self, duration_minutes: int = 30, update_interval: int = 3) -> Dict[str, Any]:
        """Run the modular simulation for the requested duration."""
        self.simulation_start_time = datetime.now()
        self.simulation_end_time = self.simulation_start_time + timedelta(minutes=duration_minutes)

        top_volume_symbols = self._run_quietly(self.market_analyzer.get_top_volume_symbols, 80)
        if not top_volume_symbols:
            return {"error": "Failed to fetch top volume symbols"}

        self.market_regime = self._run_quietly(self.analyze_market_regime)
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
        self._refresh_portfolio_state()
        self._print_position_snapshot("Initial Entry")

        iteration = 0
        max_iterations = max(duration_minutes // update_interval, 1)
        while datetime.now() < self.simulation_end_time and iteration < max_iterations:
            iteration += 1
            self.market_regime = self._run_quietly(self.analyze_market_regime)
            self._refresh_portfolio_state()
            self.dynamic_portfolio_rebalancing()
            self._refresh_portfolio_state()
            self._print_position_snapshot(f"Progress {iteration}/{max_iterations}")
            time.sleep(update_interval * 60)

        return self._generate_final_report()

    def _continuous_market_analysis(self, duration_minutes: int, update_interval: int) -> Dict[str, Any]:
        """Continue scanning until a valid entry is found or time expires."""
        analysis_count = 0
        max_attempts = max(duration_minutes // update_interval, 1)
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
                            return self._start_simulation_with_symbols(selected_symbols, update_interval, end_time)

            time.sleep(update_interval * 60)

        return {
            "error": f"No entry candidate found within {duration_minutes} minutes",
            "analysis_attempts": analysis_count,
            "duration_minutes": duration_minutes,
        }

    def _start_simulation_with_symbols(
        self,
        selected_symbols: List[Dict[str, Any]],
        update_interval: int,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """Start the main loop after a delayed entry signal appears."""
        allocations = self._run_quietly(self.portfolio_manager.allocate_capital_fixed_amount, selected_symbols)
        self._run_quietly(self.portfolio_manager.initialize_investments, allocations)
        self._refresh_portfolio_state()
        self._print_position_snapshot("Initial Entry")

        remaining_time = max((end_time - datetime.now()).total_seconds() / 60, 1.0)
        iteration = 0
        max_iterations = max(int(remaining_time // update_interval), 1)
        while datetime.now() < end_time and iteration < max_iterations:
            iteration += 1
            self.market_regime = self._run_quietly(self.analyze_market_regime)
            self._refresh_portfolio_state()
            self.dynamic_portfolio_rebalancing()
            self._refresh_portfolio_state()
            self._print_position_snapshot(f"Progress {iteration}/{max_iterations}")
            time.sleep(update_interval * 60)

        return self._generate_final_report()

    def _refresh_portfolio_state(self) -> Dict[str, Any]:
        """Refresh prices and aggregate performance for the current holdings."""
        current_prices = self._fetch_portfolio_prices()
        return self.portfolio_manager.update_investment_performance(current_prices=current_prices)

    def _fetch_portfolio_prices(self) -> Dict[str, float]:
        """Fetch the latest prices for the currently invested symbols."""
        symbols = list(self.portfolio_manager.investments.keys())
        if not symbols:
            return {}

        real_time_data = self._run_quietly(self.realtime_fetcher.get_real_time_symbol_data, symbols)
        for item in real_time_data:
            investment = self.portfolio_manager.investments.get(item["symbol"])
            if investment:
                investment["profit_potential"] = self.realtime_fetcher._calculate_profit_potential(item)
                investment["bullish_score"] = item.get("bullish_score", investment["bullish_score"])
        return {item["symbol"]: item["price"] for item in real_time_data}

    def _generate_final_report(self) -> Dict[str, Any]:
        """Build the final simulation output structure."""
        portfolio_summary = self.portfolio_manager.get_performance_summary()
        if "error" in portfolio_summary:
            return {"error": portfolio_summary["error"]}

        metadata = {
            "simulation_start_time": self.simulation_start_time.isoformat() if self.simulation_start_time else None,
            "simulation_end_time": datetime.now().isoformat(),
            "duration_minutes": (
                (datetime.now() - self.simulation_start_time).total_seconds() / 60
                if self.simulation_start_time
                else 0.0
            ),
            "total_rounds": len(self.portfolio_manager.performance_history),
            "initial_capital": self.portfolio_manager.initial_capital,
            "final_capital": portfolio_summary["total_value"],
            "cash_balance": portfolio_summary["cash_balance"],
            "realized_pnl": portfolio_summary["realized_pnl"],
            "unrealized_pnl": portfolio_summary["unrealized_pnl"],
            "total_pnl": portfolio_summary["total_pnl"],
            "pnl_percent": portfolio_summary["pnl_percent"],
            "total_fees_paid": portfolio_summary["total_fees_paid"],
            "net_pnl": portfolio_summary["net_pnl"],
            "net_pnl_percent": portfolio_summary["net_pnl_percent"],
            "invested_symbols": len(self.portfolio_manager.investments),
            "max_symbols": self.symbol_count,
            "final_market_regime": self.market_regime,
            "replacement_threshold": self.replacement_threshold,
            "minimum_hold_minutes": self.portfolio_manager.minimum_hold_minutes,
            "reentry_cooldown_minutes": self.portfolio_manager.reentry_cooldown_minutes,
            "entry_buffer": self.entry_buffer,
            "exit_buffer": self.exit_buffer,
        }

        return {
            "simulation_metadata": metadata,
            "individual_performance": portfolio_summary["individual_performance"],
            "performance_history": self.portfolio_manager.performance_history,
            "replacement_history": self.portfolio_manager.replacement_history,
        }

    def _run_quietly(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run a noisy helper while suppressing routine stdout."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            return func(*args, **kwargs)

    def _print_position_snapshot(self, label: str) -> None:
        """Print only the active symbol summary requested by the user."""
        print(f"\n[{label}]")
        current_symbols = set(self.portfolio_manager.investments.keys())
        added_symbols = sorted(current_symbols - self.last_snapshot_symbols)
        removed_symbols = sorted(self.last_snapshot_symbols - current_symbols)

        invested_amount = sum(
            investment["current_investment"] for investment in self.portfolio_manager.investments.values()
        )
        total_equity = self.portfolio_manager.cash_balance + invested_amount
        net_profit = total_equity - self.portfolio_manager.initial_capital

        print(
            f"Total Capital $ {self.portfolio_manager.initial_capital:.2f} | "
            f"Invested $ {invested_amount:.2f} | "
            f"Cash $ {self.portfolio_manager.cash_balance:.2f} | "
            f"Net PnL $ {net_profit:+.2f}"
        )
        print(
            f"Added Since Last Round: {', '.join(added_symbols) if added_symbols else '-'} | "
            f"Removed Since Last Round: {', '.join(removed_symbols) if removed_symbols else '-'}"
        )

        if not self.portfolio_manager.investments:
            print("No active positions")
            self.last_snapshot_symbols = current_symbols
            return

        print("Symbol | Prev Round Amount | Change Amount | Change % | Profit Potential | Current Amount")
        for symbol, investment in self.portfolio_manager.investments.items():
            previous_amount = self.last_snapshot_amounts.get(symbol, investment["initial_investment"])
            print(
                f"{symbol} | "
                f"${previous_amount:.2f} | "
                f"${investment['pnl']:+.2f} | "
                f"{investment['pnl_percent']:+.2f}% | "
                f"{investment.get('profit_potential', 0.0):.1f}% | "
                f"${investment['current_investment']:.2f}"
            )
        self.last_snapshot_symbols = current_symbols
        self.last_snapshot_amounts = {
            symbol: investment["current_investment"]
            for symbol, investment in self.portfolio_manager.investments.items()
        }
