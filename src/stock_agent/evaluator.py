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
    llm = payload.get("llm", {})
    lines = [
        "# Minimal Version Benchmark",
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
