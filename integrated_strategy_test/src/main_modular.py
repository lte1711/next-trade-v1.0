from pathlib import Path
import json

from modules.simulator import ModularTradingSimulator


def main():
    """Main entry point for the modular simulator."""
    simulator = ModularTradingSimulator(
        symbol_count=10,
        replacement_threshold=-0.8,
    )

    result = simulator.run_simulation(duration_minutes=30, update_interval=3)

    if "error" in result:
        print(f"시뮬레이션 실패: {result['error']}")
        return

    print("\n[최종]")
    print("심볼 | 초기진입액 | 변화액 | 변화 % | 상승평가율")
    for perf in result["individual_performance"]:
        print(
            f"{perf['symbol']} | "
            f"${perf['initial_investment']:.2f} | "
            f"${perf['pnl']:+.2f} | "
            f"{perf['pnl_percent']:+.2f}% | "
            f"{perf['profit_potential']:.1f}%"
        )

    results_file = Path("modular_simulation_results.json")
    with open(results_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
