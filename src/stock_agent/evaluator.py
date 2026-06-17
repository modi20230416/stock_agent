from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


def write_json_report(payload: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def data_validation_to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Dataset Validation",
        "",
        f"- Valid: {'PASS' if payload.get('valid') else 'FAIL'}",
        f"- Tickers: {payload.get('counts', {}).get('tickers', 0)}",
        f"- Price rows: {payload.get('counts', {}).get('prices', 0)}",
        f"- Price dates: {payload.get('counts', {}).get('price_dates', 0)}",
        f"- Date range: {payload.get('date_range', {}).get('start')} to {payload.get('date_range', {}).get('end')}",
        f"- Portfolio total weight: {payload.get('portfolio', {}).get('total_weight', 0.0):.2%}",
        "",
        "## Errors",
    ]
    errors = payload.get("errors", [])
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- None")
    lines.extend(["", "## Warnings"])
    warnings = payload.get("warnings", [])
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Coverage", "", "| Ticker | Price rows |", "| --- | ---: |"])
    for ticker, count in sorted(
        payload.get("coverage", {}).get("price_rows_by_ticker", {}).items()
    ):
        lines.append(f"| {ticker} | {count} |")
    return "\n".join(lines) + "\n"


def benchmark_to_markdown(payload: dict[str, Any]) -> str:
    criteria = payload["success_criteria"]
    multi = payload["multi_agent_with_risk"]
    technical = payload["technical_rule_baseline"]
    no_risk = payload["no_risk_ensemble_baseline"]
    direct = payload.get("direct_llm_baseline")
    backtest = payload.get("equal_weight_backtest")
    decision_backtest = payload.get("decision_weighted_backtest")
    stress_test = payload.get("stress_test") or []
    data_validation = payload.get("data_validation", {})
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
    if data_validation:
        lines.extend(
            [
                "",
                "## Data Validation",
                "",
                f"- Valid: {data_validation.get('valid', False)}",
                f"- Tickers: {data_validation.get('counts', {}).get('tickers', 0)}",
                f"- Price dates: {data_validation.get('counts', {}).get('price_dates', 0)}",
                f"- Warnings: {len(data_validation.get('warnings', []))}",
            ]
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
    if decision_backtest:
        lines.extend(
            [
                "",
                "## Decision-Weighted Strategy Backtest",
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Observations | {decision_backtest['observations']} |",
                f"| Rebalances | {decision_backtest['rebalance_count']} |",
                f"| Average turnover | {decision_backtest['average_turnover']:.2%} |",
                f"| Average cash | {decision_backtest['average_cash_weight']:.2%} |",
                f"| Cumulative return | {decision_backtest['cumulative_return']:.2%} |",
                f"| Max drawdown | {decision_backtest['max_drawdown']:.2%} |",
                f"| Sharpe ratio | {decision_backtest['sharpe_ratio']:.2f} |",
            ]
        )
    if stress_test:
        lines.extend(
            [
                "",
                "## Portfolio Stress Test",
                "",
                "| Scenario | Portfolio return | Worst contributors |",
                "| --- | ---: | --- |",
            ]
        )
        for item in stress_test:
            worst = ", ".join(
                f"{entry['asset']} {entry['contribution']:.2%}"
                for entry in item.get("worst_contributors", [])
            )
            lines.append(
                f"| {item['scenario']} | {item['portfolio_return']:.2%} | {worst} |"
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
    decision_backtest = baseline.get("decision_weighted_backtest")
    stress_test = baseline.get("stress_test") or []
    data_validation = baseline.get("data_validation", {})
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
        focus = ", ".join(item.get("focus_hits") or ["evidence reviewed"])
        lines.append(
            f"| {item['case']['id']} | single | {'PASS' if item['passed'] else 'FAIL'} | "
            f"{decision['ticker']} {decision['action']} score={decision['score']}; focus={focus} |"
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
    if decision_backtest:
        lines.extend(
            [
                f"- Decision-weighted cumulative return: {decision_backtest['cumulative_return']:.2%}",
                f"- Decision-weighted max drawdown: {decision_backtest['max_drawdown']:.2%}",
                f"- Decision-weighted rebalances: {decision_backtest['rebalance_count']}",
            ]
        )
    if stress_test:
        worst = min(stress_test, key=lambda item: item["portfolio_return"])
        lines.append(
            f"- Worst stress scenario: {worst['scenario']} ({worst['portfolio_return']:.2%})"
        )
    if data_validation:
        lines.append(
            f"- Data validation: {'PASS' if data_validation.get('valid') else 'FAIL'} "
            f"({data_validation.get('counts', {}).get('tickers', 0)} tickers)"
        )
    return "\n".join(lines) + "\n"


def final_benchmark_to_html(payload: dict[str, Any]) -> str:
    suite = payload["suite"]
    aggregate = payload["aggregate"]
    criteria = payload["success_criteria"]
    baseline = payload["baseline_comparison"]
    backtest = baseline["equal_weight_backtest"]
    decision_backtest = baseline.get("decision_weighted_backtest", {})
    stress_test = baseline.get("stress_test") or []
    data_validation = baseline.get("data_validation", {})

    case_rows: list[str] = []
    for item in payload["single_cases"]:
        decision = item["decision"]
        focus = ", ".join(item.get("focus_hits") or ["evidence reviewed"])
        case_rows.append(
            _case_row(
                item["case"]["id"],
                "single",
                item["passed"],
                f"{decision['ticker']} {decision['action']}",
                f"score={decision['score']}; focus={focus}",
            )
        )
    for item in payload["screen_cases"]:
        top = item["ranking"][0]
        case_rows.append(
            _case_row(
                item["case"]["id"],
                "screen",
                item["passed"],
                f"top={top['ticker']}",
                f"score={top['score']}; candidates={len(item['ranking'])}",
            )
        )
    for item in payload["rebalance_cases"]:
        recommendation = item["recommendation"]
        cash = recommendation["target_weights"].get("CASH", 0.0)
        case_rows.append(
            _case_row(
                item["case"]["id"],
                "rebalance",
                item["passed"],
                f"cash={cash:.2%}",
                f"warnings={len(recommendation['warnings'])}",
            )
        )

    criteria_items = "\n".join(
        (
            f'<li><span class="{_status_class(passed)}">'
            f"{'PASS' if passed else 'FAIL'}</span> "
            f"{escape(name.replace('_', ' '))}</li>"
        )
        for name, passed in criteria.items()
    )
    universe = ", ".join(suite["default_pool"])
    stress_rows = "".join(
        "<tr>"
        f"<th>{escape(item['scenario'])}</th>"
        f"<td>{item['portfolio_return']:.2%}</td>"
        f"<td>{escape(', '.join(entry['asset'] for entry in item.get('worst_contributors', [])))}</td>"
        "</tr>"
        for item in stress_test
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stock Agent Final Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --ink: #17202a;
      --muted: #5f6b7a;
      --line: #d9dee7;
      --panel: #ffffff;
      --pass: #176b3a;
      --fail: #a33a30;
      --accent: #1e5aa8;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 15px/1.55 Arial, Helvetica, sans-serif;
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 28px 36px 22px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 24px 18px 40px;
    }}
    h1, h2 {{
      margin: 0;
      line-height: 1.2;
    }}
    h1 {{
      font-size: 28px;
    }}
    h2 {{
      font-size: 18px;
      margin-bottom: 14px;
    }}
    .subtitle {{
      color: var(--muted);
      margin-top: 8px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .metric .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}
    .metric .value {{
      display: block;
      margin-top: 5px;
      font-size: 24px;
      font-weight: 700;
    }}
    section {{
      margin-bottom: 18px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: var(--panel);
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 9px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    .pass {{
      color: var(--pass);
      font-weight: 700;
    }}
    .fail {{
      color: var(--fail);
      font-weight: 700;
    }}
    .muted {{
      color: var(--muted);
    }}
    .criteria {{
      margin: 0;
      padding-left: 20px;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 18px;
    }}
    @media (max-width: 760px) {{
      header {{
        padding: 22px 18px 18px;
      }}
      .two-col {{
        grid-template-columns: 1fr;
      }}
      table {{
        font-size: 13px;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Stock Agent Final Dashboard</h1>
    <div class="subtitle">Deterministic offline benchmark; not investment advice.</div>
  </header>
  <main>
    <div class="grid">
      <div class="metric"><span class="label">As of</span><span class="value">{escape(suite['as_of'])}</span></div>
      <div class="metric"><span class="label">Pass rate</span><span class="value">{aggregate['pass_rate']:.0%}</span></div>
      <div class="metric"><span class="label">Cases</span><span class="value">{aggregate['passed_cases']}/{aggregate['total_cases']}</span></div>
      <div class="metric"><span class="label">Universe</span><span class="value">{len(suite['default_pool'])} stocks</span></div>
      <div class="metric"><span class="label">Data validation</span><span class="value">{'PASS' if data_validation.get('valid') else 'CHECK'}</span></div>
    </div>
    <section>
      <h2>Final Criteria</h2>
      <ul class="criteria">{criteria_items}</ul>
    </section>
    <section>
      <h2>Case Results</h2>
      <table>
        <thead><tr><th>Case</th><th>Task</th><th>Status</th><th>Output</th><th>Notes</th></tr></thead>
        <tbody>{''.join(case_rows)}</tbody>
      </table>
    </section>
    <div class="two-col">
      <section>
        <h2>Baseline Summary</h2>
        <table>
          <tbody>
            <tr><th>Multi-agent risk warnings</th><td>{baseline['multi_agent_with_risk']['risk_warning_count']}</td></tr>
            <tr><th>Technical action diversity</th><td>{baseline['technical_rule_baseline']['action_diversity']}</td></tr>
            <tr><th>No-risk action diversity</th><td>{baseline['no_risk_ensemble_baseline']['action_diversity']}</td></tr>
            <tr><th>Direct LLM used count</th><td>{baseline['direct_llm_baseline']['used_llm_count']}</td></tr>
          </tbody>
        </table>
      </section>
      <section>
        <h2>Equal-Weight Backtest</h2>
        <table>
          <tbody>
            <tr><th>Observations</th><td>{backtest['observations']}</td></tr>
            <tr><th>Cumulative return</th><td>{backtest['cumulative_return']:.2%}</td></tr>
            <tr><th>Annualized return</th><td>{backtest['annualized_return']:.2%}</td></tr>
            <tr><th>Max drawdown</th><td>{backtest['max_drawdown']:.2%}</td></tr>
            <tr><th>Sharpe ratio</th><td>{backtest['sharpe_ratio']:.2f}</td></tr>
          </tbody>
        </table>
      </section>
    </div>
    <div class="two-col">
      <section>
        <h2>Decision-Weighted Backtest</h2>
        <table>
          <tbody>
            <tr><th>Observations</th><td>{decision_backtest.get('observations', 0)}</td></tr>
            <tr><th>Rebalances</th><td>{decision_backtest.get('rebalance_count', 0)}</td></tr>
            <tr><th>Average turnover</th><td>{decision_backtest.get('average_turnover', 0.0):.2%}</td></tr>
            <tr><th>Cumulative return</th><td>{decision_backtest.get('cumulative_return', 0.0):.2%}</td></tr>
            <tr><th>Max drawdown</th><td>{decision_backtest.get('max_drawdown', 0.0):.2%}</td></tr>
            <tr><th>Sharpe ratio</th><td>{decision_backtest.get('sharpe_ratio', 0.0):.2f}</td></tr>
          </tbody>
        </table>
      </section>
      <section>
        <h2>Portfolio Stress Test</h2>
        <table>
          <tbody>
            {stress_rows}
          </tbody>
        </table>
      </section>
    </div>
    <section>
      <h2>Stock Universe</h2>
      <p class="muted">{escape(universe)}</p>
    </section>
  </main>
</body>
</html>
"""


def _case_row(case_id: str, task: str, passed: bool, output: str, notes: str) -> str:
    status = "PASS" if passed else "FAIL"
    return (
        "<tr>"
        f"<td>{escape(case_id)}</td>"
        f"<td>{escape(task)}</td>"
        f'<td><span class="{_status_class(passed)}">{status}</span></td>'
        f"<td>{escape(output)}</td>"
        f"<td>{escape(notes)}</td>"
        "</tr>"
    )


def _status_class(passed: bool) -> str:
    return "pass" if passed else "fail"
