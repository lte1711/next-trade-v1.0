from pathlib import Path
import json

from modules.simulator import ModularTradingSimulator


def main():
    """Main entry point for the modular simulator."""
    simulator = ModularTradingSimulator(
        symbol_count=10,
        replacement_threshold=-0.8,
    )

    result = simulator.run_simulation(duration_minutes=120, update_interval=3)

    if "error" in result:
        print(f"Simulation failed: {result['error']}")
        return

    metadata = result["simulation_metadata"]
    print("\n[Final]")
    print(
        f"Total Capital $ {metadata['initial_capital']:.2f} | "
        f"Invested $ {metadata['final_capital'] - metadata['cash_balance']:.2f} | "
        f"Cash $ {metadata['cash_balance']:.2f} | "
        f"Net PnL $ {metadata['net_pnl']:+.2f}"
    )
    print("Symbol | Initial Entry | Change Amount | Change % | Profit Potential | Current Amount")
    for perf in result["individual_performance"]:
        print(
            f"{perf['symbol']} | "
            f"${perf['initial_investment']:.2f} | "
            f"${perf['pnl']:+.2f} | "
            f"{perf['pnl_percent']:+.2f}% | "
            f"{perf['profit_potential']:.1f}% | "
            f"${perf['final_investment']:.2f}"
        )

    results_file = Path("modular_simulation_2hour_results.json")
    with open(results_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
