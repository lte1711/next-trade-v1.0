"""
Portfolio management for the modular trading simulator.
"""

from datetime import datetime
from typing import Any, Dict, List


class PortfolioManager:
    """Tracks cash, positions, fees, and performance history."""

    def __init__(self, initial_capital: float = 1000.0, trading_fee: float = 0.0004):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.cash_balance = initial_capital
        self.trading_fee = trading_fee
        self.total_fees_paid = 0.0

        self.investments: Dict[str, Dict[str, Any]] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.replacement_history: List[Dict[str, Any]] = []

        self.last_replacement_time = None
        self.replacements_this_hour = 0
        self.replacements_today = 0
        self.last_hour_reset = datetime.now().hour
        self.last_day_reset = datetime.now().date()

        self.replacement_cooldown: Dict[str, Any] = {}
        self.replacement_blacklist: Dict[str, Any] = {}
        self.recent_replacements: List[Dict[str, Any]] = []

    def allocate_capital_fixed_amount(self, selected_symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Allocate a fixed amount per selected symbol."""
        print("FACT: fixed-amount capital allocation started ($100 per symbol)")

        fixed_amount = 100.0
        allocations: Dict[str, Any] = {}

        for symbol_data in selected_symbols:
            symbol = symbol_data["symbol"]
            required_amount = (len(allocations) + 1) * fixed_amount
            if required_amount > self.cash_balance:
                print(
                    f"  capital limit reached: next allocation would require ${required_amount:.2f}, "
                    f"available cash is ${self.cash_balance:.2f}"
                )
                break

            allocations[symbol] = {
                "allocation": fixed_amount,
                "percentage": (fixed_amount / self.initial_capital) * 100,
                "symbol_data": symbol_data,
                "profit_potential": symbol_data.get("profit_potential", 0),
                "fixed_amount": True,
            }

        used_capital = len(allocations) * fixed_amount
        print(f"  allocated ${used_capital:.2f} across {len(allocations)} symbols")
        print(f"  remaining cash after allocation plan: ${self.cash_balance - used_capital:.2f}")
        return allocations

    def initialize_investments(self, allocations: Dict[str, Any]):
        """Initialize portfolio positions from an allocation plan."""
        print("FACT: investment initialization started")

        self.investments = {}
        allocated_total = 0.0
        total_buy_fees = 0.0

        for symbol, allocation_data in allocations.items():
            symbol_data = allocation_data["symbol_data"]
            allocation = allocation_data["allocation"]

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
                "rank": symbol_data.get("bullish_rank", 1),
                "bullish_score": symbol_data["bullish_score"],
                "fees_paid": fee,
                "take_profit": 5.0,
                "stop_loss": -3.0,
                "profit_potential": symbol_data.get("profit_potential", 50),
            }

            allocated_total += allocation
            total_buy_fees += fee

        self.cash_balance = max(self.initial_capital - allocated_total, 0.0)
        self.total_fees_paid = total_buy_fees
        self.current_capital = self.cash_balance + sum(
            investment["current_investment"] for investment in self.investments.values()
        )

        print(f"  initialized {len(self.investments)} investments")
        print(f"  initial fees paid: ${self.total_fees_paid:.2f}")
        print(f"  remaining cash: ${self.cash_balance:.2f}")

    def update_investment_performance(
        self, current_prices: Dict[str, float] | None = None
    ) -> Dict[str, Any]:
        """Update mark-to-market values and aggregate performance."""
        invested_value = 0.0
        total_pnl = 0.0

        for symbol, investment in self.investments.items():
            try:
                current_price = (
                    current_prices.get(symbol, investment["current_price"])
                    if current_prices
                    else investment["current_price"]
                )
                current_value = investment["shares"] * current_price
                pnl = current_value - investment["net_investment"]
                pnl_percent = (pnl / investment["net_investment"]) * 100 if investment["net_investment"] else 0.0

                investment["current_price"] = current_price
                investment["current_investment"] = current_value
                investment["pnl"] = pnl
                investment["pnl_percent"] = pnl_percent
                investment["last_update"] = datetime.now().isoformat()

                invested_value += current_value
                total_pnl += pnl

            except Exception as exc:
                print(f"  {symbol} performance update failed: {exc}")

        total_value = self.cash_balance + invested_value
        self.current_capital = total_value

        performance_record = {
            "timestamp": datetime.now().isoformat(),
            "total_value": total_value,
            "cash_balance": self.cash_balance,
            "invested_value": invested_value,
            "total_pnl": total_pnl,
            "pnl_percent": (total_pnl / self.initial_capital) * 100,
            "total_fees_paid": self.total_fees_paid,
            "net_pnl": total_pnl - self.total_fees_paid,
            "net_pnl_percent": ((total_pnl - self.total_fees_paid) / self.initial_capital) * 100,
            "invested_symbols": len(self.investments),
        }
        self.performance_history.append(performance_record)

        return {
            "total_value": total_value,
            "cash_balance": self.cash_balance,
            "invested_value": invested_value,
            "total_pnl": total_pnl,
            "pnl_percent": (total_pnl / self.initial_capital) * 100,
            "total_fees_paid": self.total_fees_paid,
            "net_pnl": total_pnl - self.total_fees_paid,
            "net_pnl_percent": ((total_pnl - self.total_fees_paid) / self.initial_capital) * 100,
        }

    def get_current_portfolio(self) -> Dict[str, Any]:
        """Return the current portfolio state."""
        return {
            "investments": self.investments,
            "total_value": self.current_capital,
            "cash_balance": self.cash_balance,
            "total_fees_paid": self.total_fees_paid,
            "performance_history": self.performance_history,
            "replacement_history": self.replacement_history,
        }

    def add_investment(self, symbol: str, symbol_data: Dict[str, Any], amount: float = 100.0):
        """Add a new position if cash is available."""
        if symbol in self.investments:
            print(f"  {symbol} is already in the portfolio")
            return False

        if amount > self.cash_balance:
            print(f"  insufficient cash for {symbol}: need ${amount:.2f}, have ${self.cash_balance:.2f}")
            return False

        fee = amount * self.trading_fee
        net_investment = amount - fee
        price = symbol_data["price"]
        shares = net_investment / price

        self.investments[symbol] = {
            "initial_investment": amount,
            "net_investment": net_investment,
            "current_investment": net_investment,
            "initial_price": price,
            "current_price": price,
            "shares": shares,
            "initial_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "pnl": 0.0,
            "pnl_percent": 0.0,
            "rank": symbol_data.get("bullish_rank", 1),
            "bullish_score": symbol_data["bullish_score"],
            "fees_paid": fee,
            "take_profit": 5.0,
            "stop_loss": -3.0,
            "profit_potential": symbol_data.get("profit_potential", 0),
        }

        self.cash_balance -= amount
        self.total_fees_paid += fee
        self.current_capital = self.cash_balance + sum(
            investment["current_investment"] for investment in self.investments.values()
        )
        print(f"  added {symbol}: invested ${net_investment:.2f} after ${fee:.2f} fee")
        return True

    def remove_investment(self, symbol: str) -> Dict[str, Any]:
        """Close an existing position and return the trade summary."""
        if symbol not in self.investments:
            print(f"  {symbol} is not currently invested")
            return {}

        investment = self.investments[symbol]
        current_value = investment["current_investment"]
        sell_fee = current_value * self.trading_fee
        net_proceeds = current_value - sell_fee

        del self.investments[symbol]
        self.cash_balance += net_proceeds
        self.total_fees_paid += sell_fee
        self.current_capital = self.cash_balance + sum(
            active["current_investment"] for active in self.investments.values()
        )

        result = {
            "symbol": symbol,
            "net_proceeds": net_proceeds,
            "sell_fee": sell_fee,
            "investment": investment,
        }
        print(f"  removed {symbol}: recovered ${net_proceeds:.2f} after ${sell_fee:.2f} fee")
        return result

    def get_performance_summary(self) -> Dict[str, Any]:
        """Return the latest aggregate and per-symbol performance summary."""
        if not self.performance_history:
            return {"error": "No performance history available"}

        latest_performance = self.performance_history[-1]
        individual_performance = []
        for symbol, investment in self.investments.items():
            individual_performance.append(
                {
                    "symbol": symbol,
                    "initial_investment": investment["initial_investment"],
                    "net_investment": investment["net_investment"],
                    "final_investment": investment["current_investment"],
                    "pnl": investment["pnl"],
                    "pnl_percent": investment["pnl_percent"],
                    "rank": investment["rank"],
                    "bullish_score": investment["bullish_score"],
                    "fees_paid": investment["fees_paid"],
                    "profit_potential": investment.get("profit_potential", 50),
                }
            )

        individual_performance.sort(key=lambda item: item["pnl_percent"], reverse=True)
        return {
            "total_value": latest_performance["total_value"],
            "cash_balance": latest_performance["cash_balance"],
            "total_pnl": latest_performance["total_pnl"],
            "pnl_percent": latest_performance["pnl_percent"],
            "total_fees_paid": latest_performance["total_fees_paid"],
            "net_pnl": latest_performance["net_pnl"],
            "net_pnl_percent": latest_performance["net_pnl_percent"],
            "individual_performance": individual_performance,
        }
