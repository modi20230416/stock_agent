from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stock_agent.evaluator import (
    benchmark_to_markdown,
    final_benchmark_to_markdown,
    write_json_report,
)
from stock_agent.pipeline import StockDecisionSystem

DEFAULT_DATA_DIR = ROOT / "data" / "processed"
if not DEFAULT_DATA_DIR.exists():
    DEFAULT_DATA_DIR = ROOT / "data" / "sample"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the multi-agent stock decision prototype."
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output-dir", default=str(ROOT / "reports"))
    parser.add_argument("--as-of", default="2026-05-22")
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument(
        "--tickers",
        default="AAPL,MSFT,NVDA,AMZN,GOOGL,META,JPM,XOM,UNH,TSLA,AMD,WMT",
        help="Comma-separated stock pool for screening/rebalance/benchmark.",
    )
    parser.add_argument(
        "--cases-file",
        default=str(ROOT / "data" / "benchmark" / "cases.json"),
        help="Benchmark case suite for the final project version.",
    )
    parser.add_argument(
        "--task",
        choices=["single", "screen", "rebalance", "benchmark", "final", "all"],
        default="all",
    )
    parser.add_argument(
        "--llm",
        choices=["auto", "required", "off"],
        default="auto",
        help=(
            "Use OpenRouter LLM review. auto uses OPENROUTER_API_KEY when present "
            "and falls back to rules; required fails if the API call fails; off "
            "runs the deterministic baseline only."
        ),
    )
    return parser.parse_args()


def write_payload(payload, path: Path) -> None:
    write_json_report(payload, path)
    print(f"Wrote {path}")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tickers = [item.strip().upper() for item in args.tickers.split(",") if item.strip()]
    system = StockDecisionSystem.from_data_dir(args.data_dir, use_llm=args.llm)
    results = {}

    if args.task in {"single", "all"}:
        decision = system.analyze_single(args.ticker, args.as_of)
        payload = decision.to_dict()
        write_payload(payload, output_dir / "single_analysis.json")
        results["single"] = payload

    if args.task in {"screen", "all"}:
        payload = {"as_of": args.as_of, "ranking": system.screen_candidates(tickers, args.as_of)}
        write_payload(payload, output_dir / "candidate_screening.json")
        results["screen"] = payload

    if args.task in {"rebalance", "all"}:
        payload = system.rebalance(tickers, args.as_of).to_dict()
        write_payload(payload, output_dir / "rebalance.json")
        results["rebalance"] = payload

    if args.task in {"benchmark", "all"}:
        payload = system.benchmark(tickers, args.as_of)
        write_payload(payload, output_dir / "benchmark_results.json")
        markdown = benchmark_to_markdown(payload)
        markdown_path = output_dir / "benchmark_results.md"
        markdown_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote {markdown_path}")
        results["benchmark"] = payload

    if args.task in {"final", "all"}:
        payload = system.benchmark_cases(args.cases_file, data_dir=args.data_dir)
        write_payload(payload, output_dir / "final_benchmark_results.json")
        markdown = final_benchmark_to_markdown(payload)
        markdown_path = output_dir / "final_benchmark_results.md"
        markdown_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote {markdown_path}")
        results["final"] = payload

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
