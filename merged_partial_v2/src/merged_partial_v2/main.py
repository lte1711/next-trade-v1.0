import json
from pathlib import Path

from merged_partial_v2.exchange.credential_store import describe_credentials
from merged_partial_v2.exchange.local_binance_bridge import (
    get_recent_health_check_summary,
    get_recent_order_failure_summary,
)
from merged_partial_v2.pathing import merged_root, resolve_resource
from merged_partial_v2.simulation.strategy_engine import MergedPartialStrategyEngine


def _backtest_report_path(profile_name: str | None) -> Path | None:
    if not profile_name:
        return None
    report_name = f"{profile_name}_1year_backtest.json"
    merged_path = merged_root() / "backtest_reports" / report_name
    if merged_path.exists():
        return merged_path
    packaged_path = resolve_resource(f"backtest_reports/{report_name}")
    if packaged_path.exists():
        return packaged_path
    return None


def _compute_symbol_backtest_stats(trade_history: list[dict]) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for row in trade_history:
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        item = stats.setdefault(
            symbol,
            {
                "symbol": symbol,
                "entry_allocations": [],
                "total_allocation": 0.0,
                "realized_pnl": 0.0,
                "close_count": 0,
                "equity": 100.0,
                "peak_equity": 100.0,
                "max_drawdown_percent": 0.0,
            },
        )
        if str(row.get("action") or "").upper() == "ENTRY":
            item["entry_allocations"].append(float(row.get("allocation", 0.0) or 0.0))
            continue

        pnl_percent = row.get("pnl_percent")
        if pnl_percent is None:
            continue
        allocation = item["entry_allocations"].pop(0) if item["entry_allocations"] else 0.0
        item["total_allocation"] += allocation
        item["realized_pnl"] += float(row.get("realized_pnl", 0.0) or 0.0)
        item["close_count"] += 1
        item["equity"] *= 1 + (float(pnl_percent) / 100.0)
        item["peak_equity"] = max(item["peak_equity"], item["equity"])
        if item["peak_equity"] > 0:
            drawdown = ((item["equity"] - item["peak_equity"]) / item["peak_equity"]) * 100.0
            item["max_drawdown_percent"] = min(item["max_drawdown_percent"], drawdown)

    finalized: dict[str, dict] = {}
    for symbol, item in stats.items():
        if item["close_count"] <= 0:
            continue
        total_allocation = float(item["total_allocation"] or 0.0)
        pnl_percent = ((item["realized_pnl"] / total_allocation) * 100.0) if total_allocation > 0 else None
        finalized[symbol] = {
            "symbol": symbol,
            "trade_count": int(item["close_count"]),
            "allocation_sum": total_allocation,
            "realized_pnl": float(item["realized_pnl"]),
            "final_pnl_percent": pnl_percent,
            "max_drawdown_percent": float(item["max_drawdown_percent"]),
        }
    return finalized


def _load_backtest_input_history(report_payload: dict) -> list[dict]:
    source_path = report_payload.get("analysis_basis", {}).get("source_path")
    candidates: list[Path] = []
    if source_path:
        candidates.append(Path(source_path))
    candidates.append(merged_root().parent / "integrated_strategy_test" / "src" / "real_market_backtest_input.json")
    for path in candidates:
        if path.exists():
            with path.open("r", encoding="utf-8-sig") as handle:
                return json.load(handle)
    return []


def _compute_symbol_price_path_stats(history: list[dict], symbols: list[str]) -> dict[str, dict]:
    symbol_set = {symbol.upper() for symbol in symbols if symbol}
    series: dict[str, list[float]] = {symbol: [] for symbol in symbol_set}
    for day in history:
        for symbol, item in dict(day.get("symbols") or {}).items():
            normalized = str(symbol or "").upper()
            if normalized in symbol_set:
                price = float(item.get("price", 0.0) or 0.0)
                if price > 0:
                    series[normalized].append(price)

    stats: dict[str, dict] = {}
    for symbol, prices in series.items():
        if len(prices) < 2:
            continue
        first_price = prices[0]
        last_price = prices[-1]
        peak_price = first_price
        max_drawdown = 0.0
        for price in prices:
            peak_price = max(peak_price, price)
            if peak_price > 0:
                max_drawdown = min(max_drawdown, ((price - peak_price) / peak_price) * 100.0)
        stats[symbol] = {
            "symbol": symbol,
            "trade_count": 0,
            "allocation_sum": 1.0,
            "realized_pnl": last_price - first_price,
            "final_pnl_percent": ((last_price / first_price) - 1.0) * 100.0,
            "max_drawdown_percent": max_drawdown,
        }
    return stats


def build_backtest_scope_summary(profile_selection: dict, market_snapshot: dict, account_snapshot: dict) -> dict:
    selected_profile = profile_selection.get("selected_profile")
    benchmark = profile_selection.get("selected_profile_benchmark", {})
    active_positions = list((account_snapshot.get("positions") or {}).get("active_positions") or [])
    active_symbols = [
        str(row.get("symbol") or "").upper()
        for row in active_positions
        if str(row.get("symbol") or "").strip()
    ]
    candidate_symbols = active_symbols or [
        str(row.get("symbol") or "").upper()
        for row in market_snapshot.get("selected_symbols", [])
        if str(row.get("symbol") or "").strip()
    ]
    report_path = _backtest_report_path(selected_profile)
    if not report_path:
        return {
            "scope": "profile_benchmark",
            "scope_label": "프로필 기준",
            "symbol_count": len(candidate_symbols),
            "matched_symbol_count": 0,
            "symbols": candidate_symbols,
            "matched_symbols": [],
            "unmatched_symbols": candidate_symbols,
            "final_pnl_percent": benchmark.get("final_pnl_percent"),
            "max_drawdown_percent": benchmark.get("max_drawdown_percent"),
            "report_path": None,
            "reason": "백테스트 리포트가 없어 프로필 기준 값을 표시합니다.",
        }

    with report_path.open("r", encoding="utf-8-sig") as handle:
        report_payload = json.load(handle)
    symbol_stats = _compute_symbol_backtest_stats(list(report_payload.get("trade_history") or []))
    matched_stats = [symbol_stats[symbol] for symbol in candidate_symbols if symbol in symbol_stats]
    unmatched_symbols = [symbol for symbol in candidate_symbols if symbol not in symbol_stats]
    if not matched_stats:
        price_path_stats = _compute_symbol_price_path_stats(_load_backtest_input_history(report_payload), candidate_symbols)
        matched_stats = [price_path_stats[symbol] for symbol in candidate_symbols if symbol in price_path_stats]
        unmatched_symbols = [symbol for symbol in candidate_symbols if symbol not in price_path_stats]
        if matched_stats:
            total_weight = sum(float(item.get("allocation_sum", 0.0) or 0.0) for item in matched_stats)
            weighted_pnl = sum(
                float(item.get("final_pnl_percent", 0.0) or 0.0) * float(item.get("allocation_sum", 0.0) or 0.0)
                for item in matched_stats
            ) / total_weight
            max_drawdown = min(float(item.get("max_drawdown_percent", 0.0) or 0.0) for item in matched_stats)
            return {
                "scope": "active_symbols_price_path" if active_symbols else "selected_symbols_price_path",
                "scope_label": f"{'진행 중' if active_symbols else '선정'} {len(candidate_symbols)}종목 가격경로 기준",
                "symbol_count": len(candidate_symbols),
                "matched_symbol_count": len(matched_stats),
                "symbols": candidate_symbols,
                "matched_symbols": [item["symbol"] for item in matched_stats],
                "unmatched_symbols": unmatched_symbols,
                "final_pnl_percent": weighted_pnl,
                "max_drawdown_percent": max_drawdown,
                "report_path": str(report_path),
                "reason": (
                    f"진행 중 심볼 백테스트 체결 이력이 부족해 "
                    f"{len(matched_stats)}개 심볼의 1년 가격 경로로 자동 환산했습니다."
                ),
            }
    if not matched_stats:
        return {
            "scope": "profile_benchmark",
            "scope_label": "프로필 기준",
            "symbol_count": len(candidate_symbols),
            "matched_symbol_count": 0,
            "symbols": candidate_symbols,
            "matched_symbols": [],
            "unmatched_symbols": unmatched_symbols,
            "final_pnl_percent": benchmark.get("final_pnl_percent"),
            "max_drawdown_percent": benchmark.get("max_drawdown_percent"),
            "report_path": str(report_path),
            "reason": "진행 중 심볼과 일치하는 백테스트 종목이 없어 프로필 기준 값을 표시합니다.",
        }

    total_weight = sum(float(item.get("allocation_sum", 0.0) or 0.0) for item in matched_stats)
    if total_weight > 0:
        weighted_pnl = sum(
            float(item.get("final_pnl_percent", 0.0) or 0.0) * float(item.get("allocation_sum", 0.0) or 0.0)
            for item in matched_stats
        ) / total_weight
    else:
        weighted_pnl = None
    max_drawdown = min(float(item.get("max_drawdown_percent", 0.0) or 0.0) for item in matched_stats)
    return {
        "scope": "active_symbols" if active_symbols else "selected_symbols",
        "scope_label": f"{'진행 중' if active_symbols else '선정'} {len(candidate_symbols)}종목 기준",
        "symbol_count": len(candidate_symbols),
        "matched_symbol_count": len(matched_stats),
        "symbols": candidate_symbols,
        "matched_symbols": [item["symbol"] for item in matched_stats],
        "unmatched_symbols": unmatched_symbols,
        "final_pnl_percent": weighted_pnl,
        "max_drawdown_percent": max_drawdown,
        "report_path": str(report_path),
        "reason": (
            f"{'진행 중' if active_symbols else '선정'} 심볼 {len(candidate_symbols)}개 중 "
            f"{len(matched_stats)}개를 백테스트 거래 이력과 자동 매칭했습니다."
        ),
    }


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


def build_operational_summary(profile_selection: dict, market_snapshot: dict, account_snapshot: dict) -> dict:
    selected_profile = profile_selection.get("selected_profile")
    benchmark = profile_selection.get("selected_profile_benchmark", {})
    selected_symbols = market_snapshot.get("selected_symbols", [])
    backtest_scope = build_backtest_scope_summary(profile_selection, market_snapshot, account_snapshot)
    benchmark_pnl = backtest_scope.get("final_pnl_percent", benchmark.get("final_pnl_percent"))
    benchmark_dd = backtest_scope.get("max_drawdown_percent", benchmark.get("max_drawdown_percent"))
    top_symbol = selected_symbols[0]["symbol"] if selected_symbols else None
    return {
        "selected_profile": selected_profile,
        "market_regime": market_snapshot.get("market_regime"),
        "selected_symbol_count": len(selected_symbols),
        "top_selected_symbol": top_symbol,
        "benchmark_final_pnl_percent": benchmark_pnl,
        "benchmark_max_drawdown_percent": benchmark_dd,
        "backtest_scope": backtest_scope.get("scope"),
        "backtest_scope_label": backtest_scope.get("scope_label"),
        "backtest_symbol_count": backtest_scope.get("symbol_count"),
        "backtest_matched_symbol_count": backtest_scope.get("matched_symbol_count"),
        "backtest_symbols": backtest_scope.get("symbols"),
        "backtest_matched_symbols": backtest_scope.get("matched_symbols"),
        "backtest_unmatched_symbols": backtest_scope.get("unmatched_symbols"),
        "backtest_report_path": backtest_scope.get("report_path"),
        "decision_line": (
            f"{selected_profile} selected | regime {market_snapshot.get('market_regime')} | "
            f"{backtest_scope.get('scope_label', '프로필 기준')} | top symbol {top_symbol or '-'} | benchmark pnl "
            f"{benchmark_pnl if benchmark_pnl is not None else 'n/a'}% | "
            f"benchmark maxDD {benchmark_dd if benchmark_dd is not None else 'n/a'}%"
        ),
        "reason": (
            f"{backtest_scope.get('reason')} "
            f"프로필 선택 기준: {profile_selection.get('metrics_source_resolved', 'config current_metrics')}."
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
        symbol_count=config.get("default_symbol_count", 5),
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
    snapshot = engine.build_paper_decision(limit=int(config.get("autonomous", {}).get("scan_limit", 100) or 100))

    selected_symbols = snapshot["market"]["selected_symbols"]
    operational_summary = build_operational_summary(profile_selection, snapshot["market"], snapshot["account"])
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
