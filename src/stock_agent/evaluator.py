from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_report(payload: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def benchmark_to_markdown(payload: dict[str, Any]) -> str:
    criteria = payload["success_criteria"]
    multi = payload["multi_agent_with_risk"]
    technical = payload["technical_rule_baseline"]
    no_risk = payload["no_risk_ensemble_baseline"]
    direct = payload.get("direct_llm_baseline")
    backtest = payload.get("equal_weight_backtest")
    llm = payload.get("llm", {})
    lines = [
        "# Stock Agent Benchmark",
        "",
        f"- As of: {payload['as_of']}",
        f"- Tickers: {', '.join(payload['tickers'])}",
        f"- LLM mode: {llm.get('mode', 'unknown')}",
        f"- LLM model: {llm.get('model', 'unknown')}",
        f"- LLM used count: {llm.get('used_count', 0)}",
        "",
        "## Success Criteria",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'}: {name.replace('_', ' ')}"
        for name, passed in criteria.items()
    )
    lines.extend(
        [
            "",
            "## Baseline Comparison",
            "",
            "| System | Actions | Action diversity | Risk warnings | Constraint violations |",
            "| --- | --- | ---: | ---: | --- |",
            f"| Multi-agent + risk | {multi['actions']} | {multi['action_diversity']} | {multi['risk_warning_count']} | {multi['constraint_violations']} |",
            f"| Technical rule | {technical['actions']} | {technical['action_diversity']} | {technical['risk_warning_count']} | N/A |",
            f"| No-risk ensemble | {no_risk['actions']} | {no_risk['action_diversity']} | {no_risk['risk_warning_count']} | N/A |",
        ]
    )
    if direct:
        lines.append(
            f"| Direct LLM/single-agent | {direct['actions']} | {direct['action_diversity']} | N/A | N/A |"
        )
    if backtest:
        lines.extend(
            [
                "",
                "## Equal-Weight Backtest",
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Observations | {backtest['observations']} |",
                f"| Cumulative return | {backtest['cumulative_return']:.2%} |",
                f"| Annualized return | {backtest['annualized_return']:.2%} |",
                f"| Max drawdown | {backtest['max_drawdown']:.2%} |",
                f"| Sharpe ratio | {backtest['sharpe_ratio']:.2f} |",
            ]
        )
    lines.extend(
        [
            "",
            "## Rebalance Target",
            "",
            "| Asset | Target weight | Trade |",
            "| --- | ---: | ---: |",
        ]
    )
    rebalance = payload["rebalance"]
    for asset, weight in rebalance["target_weights"].items():
        trade = rebalance["trades"].get(asset, 0.0)
        lines.append(f"| {asset} | {weight:.2%} | {trade:+.2%} |")
    if rebalance["warnings"]:
        lines.extend(["", "## Rebalance Warnings"])
        lines.extend(f"- {warning}" for warning in rebalance["warnings"])
    return "\n".join(lines) + "\n"


def final_benchmark_to_markdown(payload: dict[str, Any]) -> str:
    suite = payload["suite"]
    aggregate = payload["aggregate"]
    criteria = payload["success_criteria"]
    baseline = payload["baseline_comparison"]
    backtest = baseline["equal_weight_backtest"]
    lines = [
        "# Final Version Benchmark",
        "",
        f"- As of: {suite['as_of']}",
        f"- Stock universe: {', '.join(suite['default_pool'])}",
        f"- Cases: {suite['case_counts']['total']} total "
        f"({suite['case_counts']['single']} single, "
        f"{suite['case_counts']['screen']} screen, "
        f"{suite['case_counts']['rebalance']} rebalance)",
        f"- Pass rate: {aggregate['passed_cases']}/{aggregate['total_cases']} "
        f"({aggregate['pass_rate']:.2%})",
        "",
        "## Final Criteria",
    ]
    lines.extend(
        f"- {'PASS' if passed else 'FAIL'}: {name.replace('_', ' ')}"
        for name, passed in criteria.items()
    )
    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Task | Result | Key output |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload["single_cases"]:
        decision = item["decision"]
        lines.append(
            f"| {item['case']['id']} | single | {'PASS' if item['passed'] else 'FAIL'} | "
            f"{decision['ticker']} {decision['action']} score={decision['score']} |"
        )
    for item in payload["screen_cases"]:
        top = item["ranking"][0]
        lines.append(
            f"| {item['case']['id']} | screen | {'PASS' if item['passed'] else 'FAIL'} | "
            f"top={top['ticker']} score={top['score']} |"
        )
    for item in payload["rebalance_cases"]:
        recommendation = item["recommendation"]
        cash = recommendation["target_weights"].get("CASH", 0.0)
        lines.append(
            f"| {item['case']['id']} | rebalance | {'PASS' if item['passed'] else 'FAIL'} | "
            f"cash={cash:.2%}, warnings={len(recommendation['warnings'])} |"
        )
    lines.extend(
        [
            "",
            "## Baseline And Backtest",
            "",
            f"- Multi-agent risk warnings: {baseline['multi_agent_with_risk']['risk_warning_count']}",
            f"- Technical baseline action diversity: {baseline['technical_rule_baseline']['action_diversity']}",
            f"- No-risk baseline action diversity: {baseline['no_risk_ensemble_baseline']['action_diversity']}",
            f"- Direct LLM baseline used LLM count: {baseline['direct_llm_baseline']['used_llm_count']}",
            f"- Equal-weight cumulative return: {backtest['cumulative_return']:.2%}",
            f"- Equal-weight max drawdown: {backtest['max_drawdown']:.2%}",
        ]
    )
    return "\n".join(lines) + "\n"
