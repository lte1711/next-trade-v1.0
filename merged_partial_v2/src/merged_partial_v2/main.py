import json
from pathlib import Path

from merged_partial_v2.exchange.credential_store import describe_credentials
from merged_partial_v2.exchange.local_binance_bridge import (
    get_recent_health_check_summary,
    get_recent_order_failure_summary,
)
from merged_partial_v2.pathing import merged_root, resolve_resource
from merged_partial_v2.simulation.strategy_engine import MergedPartialStrategyEngine


def load_merge_config() -> dict:
    config_path = resolve_resource("config.json")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_profile_metrics(config: dict) -> tuple[dict, dict]:
    selection_config = dict(config.get("profile_selection", {}))
    benchmark_metrics = dict(config.get("profile_benchmarks", {}))

    metrics_source = selection_config.get("metrics_source")
    if not metrics_source:
        return selection_config, benchmark_metrics

    metrics_path = merged_root() / metrics_source
    if not metrics_path.exists():
        metrics_path = resolve_resource(metrics_source)
    if not metrics_path.exists():
        return selection_config, benchmark_metrics

    with metrics_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    file_profiles = payload.get("profiles", {})
    if file_profiles:
        benchmark_metrics.update(file_profiles)

        current_metrics_profile = selection_config.get(
            "current_metrics_profile_name",
            selection_config.get("default_profile_name"),
        )
        if current_metrics_profile and current_metrics_profile in file_profiles:
            default_metrics = file_profiles[current_metrics_profile]
            selection_config["current_metrics"] = {
                "max_drawdown_percent": default_metrics.get("max_drawdown_percent"),
                "positive_months": default_metrics.get("positive_months"),
                "negative_months": default_metrics.get("negative_months"),
            }
            selection_config["current_metrics_profile_name"] = current_metrics_profile

    selection_config["metrics_source_resolved"] = str(metrics_path)
    return selection_config, benchmark_metrics


def build_operational_summary(profile_selection: dict, market_snapshot: dict) -> dict:
    selected_profile = profile_selection.get("selected_profile")
    benchmark = profile_selection.get("selected_profile_benchmark", {})
    selected_symbols = market_snapshot.get("selected_symbols", [])
    benchmark_pnl = benchmark.get("final_pnl_percent")
    benchmark_dd = benchmark.get("max_drawdown_percent")
    top_symbol = selected_symbols[0]["symbol"] if selected_symbols else None
    return {
        "selected_profile": selected_profile,
        "market_regime": market_snapshot.get("market_regime"),
        "selected_symbol_count": len(selected_symbols),
        "top_selected_symbol": top_symbol,
        "benchmark_final_pnl_percent": benchmark_pnl,
        "benchmark_max_drawdown_percent": benchmark_dd,
        "decision_line": (
            f"{selected_profile} selected | regime {market_snapshot.get('market_regime')} | "
            f"top symbol {top_symbol or '-'} | benchmark pnl "
            f"{benchmark_pnl if benchmark_pnl is not None else 'n/a'}% | "
            f"benchmark maxDD {benchmark_dd if benchmark_dd is not None else 'n/a'}%"
        ),
        "reason": (
            f"{selected_profile} selected using configured drawdown/month rules "
            f"in {profile_selection.get('metrics_source_resolved', 'config current_metrics')}."
        ),
    }


def build_paper_decision_summary(decision: dict) -> dict:
    recommendations = list(decision.get("recommendations", []))
    blocked = list(decision.get("blocked", []))
    top = recommendations[0]["symbol"] if recommendations else None
    return {
        "recommended_orders": len(recommendations),
        "blocked_candidates": len(blocked),
        "top_recommendation_symbol": top,
        "decision_line": decision.get("decision_line"),
    }


def build_compact_account_snapshot(account_snapshot: dict) -> dict:
    account = dict(account_snapshot.get("account", {}))
    positions = dict(account_snapshot.get("positions", {}))
    return {
        "account": {
            "ok": account.get("ok"),
            "ts": account.get("ts"),
            "source": account.get("source"),
            "account_equity": account.get("account_equity"),
            "wallet_balance": account.get("wallet_balance"),
            "unrealized_pnl": account.get("unrealized_pnl"),
        },
        "positions": {
            "ok": positions.get("ok"),
            "ts": positions.get("ts"),
            "source": positions.get("source"),
            "position_count": positions.get("position_count"),
            "active_position_count": positions.get("active_position_count"),
            "active_positions": positions.get("active_positions", []),
            "error": positions.get("error"),
        },
    }


def load_last_execution_report() -> dict:
    report_path = merged_root() / "execution_reports" / "last_execution_report.json"
    if not report_path.exists():
        return {"ok": False, "reason": "no_execution_report"}
    with report_path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    short_summary = payload.get("alert_summary")
    if not short_summary:
        short_summary = payload.get("reason") or payload.get("mode")
    return {
        "ok": True,
        "path": str(report_path),
        "mode": payload.get("mode"),
        "dry_run": payload.get("dry_run"),
        "executed": payload.get("executed"),
        "guard_passed": payload.get("guard_passed"),
        "reason": payload.get("reason"),
        "decision_line": payload.get("paper_decision", {}).get("decision_line"),
        "alert_summary": payload.get("alert_summary"),
        "short_summary": short_summary,
        "payload": payload,
    }


def load_last_autonomous_report() -> dict:
    report_path = merged_root() / "autonomous_reports" / "last_autonomous_report.json"
    if not report_path.exists():
        return {"ok": False, "reason": "no_autonomous_report"}
    with report_path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    return {
        "ok": True,
        "path": str(report_path),
        "mode": payload.get("mode"),
        "dry_run": payload.get("dry_run"),
        "entry_count": payload.get("entry_count"),
        "exit_count": payload.get("exit_count"),
        "decision_line": payload.get("decision_line"),
        "payload": payload,
    }


def build_snapshot_payload() -> dict:
    config = load_merge_config()
    selection_config, benchmark_metrics = load_profile_metrics(config)
    engine = MergedPartialStrategyEngine(
        exchange_base_url=config.get("exchange_base_url", "https://demo-fapi.binance.com"),
        symbol_count=config.get("default_symbol_count", 10),
        profile_name=selection_config.get("default_profile_name"),
        selection_config=selection_config,
        benchmark_metrics=benchmark_metrics,
    )
    profile_selection = engine.select_profile_from_metrics(
        max_drawdown_percent=selection_config.get("current_metrics", {}).get("max_drawdown_percent"),
        positive_months=selection_config.get("current_metrics", {}).get("positive_months"),
        negative_months=selection_config.get("current_metrics", {}).get("negative_months"),
        prefer_aggressive=selection_config.get("prefer_aggressive", False),
    )
    snapshot = engine.build_paper_decision(limit=80)

    selected_symbols = snapshot["market"]["selected_symbols"]
    operational_summary = build_operational_summary(profile_selection, snapshot["market"])
    paper_decision_summary = build_paper_decision_summary(snapshot["paper_decision"])
    print(f"Selected profile: {snapshot['market']['profile']['name']}")
    print(
        "Profile selection rule: "
        f"{profile_selection['selection_rule']}"
    )
    print(
        "Operational summary: "
        f"{operational_summary['decision_line']}"
    )
    print(f"Market regime: {snapshot['market']['market_regime']}")
    print(f"Selected symbols: {len(selected_symbols)}")
    print(f"Paper decision: {paper_decision_summary['decision_line']}")
    for item in selected_symbols[:10]:
        print(
            f"{item['symbol']} | "
            f"bullish={item['bullish_score']:.1f} | "
            f"potential={item['profit_potential']:.1f} | "
            f"change={item['change_percent']:+.2f}%"
        )

    return {
        "config": {
            "profile_selection": selection_config,
            "profile_benchmarks": benchmark_metrics,
        },
        "credential_status": describe_credentials(),
        "recent_health_check": get_recent_health_check_summary(),
        "recent_order_failures": get_recent_order_failure_summary(),
        "last_execution_report": load_last_execution_report(),
        "last_autonomous_report": load_last_autonomous_report(),
        "profile_selection": profile_selection,
        "operational_summary": operational_summary,
        "paper_decision_summary": paper_decision_summary,
        "market": snapshot["market"],
        "account": build_compact_account_snapshot(snapshot["account"]),
        "paper_decision": snapshot["paper_decision"],
    }


def write_snapshot_payload(output_payload: dict) -> Path:
    output_path = merged_root() / "merged_snapshot.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output_payload, handle, indent=2, ensure_ascii=False)
    return output_path


def main() -> None:
    """Build a merged snapshot and write it into the merge workspace."""
    output_payload = build_snapshot_payload()
    write_snapshot_payload(output_payload)


if __name__ == "__main__":
    main()
