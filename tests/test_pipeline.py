from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stock_agent.data_loader import validate_dataset
from stock_agent.evaluator import (
    data_validation_to_markdown,
    final_benchmark_to_html,
    final_benchmark_to_markdown,
)
from stock_agent.pipeline import StockDecisionSystem


class StockDecisionSystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.system = StockDecisionSystem.from_data_dir(ROOT / "data" / "sample", use_llm="off")

    def test_single_stock_has_required_fields(self) -> None:
        decision = self.system.analyze_single("AAPL", "2026-05-19")
        self.assertIn(decision.action, {"BUY", "SELL", "HOLD"})
        self.assertGreater(len(decision.rationale), 0)
        self.assertGreater(len(decision.risk_warnings), 0)
        self.assertIn("market", decision.agent_results)
        self.assertIn("risk", decision.agent_results)

    def test_screening_distinguishes_candidates(self) -> None:
        ranking = self.system.screen_candidates(["AAPL", "MSFT", "TSLA", "NVDA"], "2026-05-19")
        self.assertEqual(len(ranking), 4)
        scores = {item["score"] for item in ranking}
        self.assertGreaterEqual(len(scores), 2)

    def test_rebalance_respects_constraints(self) -> None:
        recommendation = self.system.rebalance(["AAPL", "MSFT", "TSLA", "NVDA"], "2026-05-19")
        constraints = self.system.constraints
        max_position = constraints["max_position_weight"]
        min_cash = constraints["min_cash_weight"]
        self.assertAlmostEqual(sum(recommendation.target_weights.values()), 1.0, places=6)
        self.assertGreaterEqual(recommendation.target_weights["CASH"], min_cash)
        for ticker, weight in recommendation.target_weights.items():
            if ticker != "CASH":
                self.assertLessEqual(weight, max_position + 1e-6)

    def test_benchmark_success_criteria_are_reported(self) -> None:
        benchmark = self.system.benchmark(["AAPL", "MSFT", "TSLA", "NVDA"], "2026-05-19")
        self.assertIn("success_criteria", benchmark)
        self.assertEqual(benchmark["llm"]["mode"], "off")
        self.assertTrue(benchmark["data_validation"]["valid"])
        self.assertGreater(benchmark["decision_weighted_backtest"]["observations"], 0)
        self.assertGreaterEqual(len(benchmark["stress_test"]), 3)
        decision_backtest = benchmark["decision_weighted_backtest"]
        self.assertIn("net_cumulative_return", decision_backtest)
        self.assertIn("gross_cumulative_return", decision_backtest)
        self.assertIn("total_transaction_cost", decision_backtest)
        self.assertGreaterEqual(decision_backtest["total_transaction_cost"], 0.0)
        self.assertLessEqual(
            decision_backtest["net_cumulative_return"],
            decision_backtest["gross_cumulative_return"] + 1e-9,
        )
        self.assertTrue(benchmark["success_criteria"]["single_stock_has_action_reason_and_risk"])
        self.assertTrue(benchmark["success_criteria"]["rebalance_respects_constraints"])

    def test_decision_weighted_backtest_includes_cost(self) -> None:
        benchmark = self.system.benchmark(["AAPL", "MSFT", "TSLA", "NVDA"], "2026-05-19")
        decision_backtest = benchmark["decision_weighted_backtest"]
        self.assertIn("cost_per_turn", decision_backtest)
        self.assertGreater(decision_backtest["cost_per_turn"], 0.0)
        self.assertGreaterEqual(decision_backtest["total_transaction_cost"], 0.0)
        # Net return must never exceed gross return once costs are deducted.
        self.assertLessEqual(
            decision_backtest["net_cumulative_return"],
            decision_backtest["gross_cumulative_return"] + 1e-9,
        )

    def test_decision_weighted_backtest_models_slippage(self) -> None:
        benchmark = self.system.benchmark(["AAPL", "MSFT", "TSLA", "NVDA"], "2026-05-19")
        decision_backtest = benchmark["decision_weighted_backtest"]
        self.assertIn("impact_coefficient", decision_backtest)
        self.assertIn("total_base_cost", decision_backtest)
        self.assertIn("total_slippage", decision_backtest)
        self.assertGreaterEqual(decision_backtest["total_slippage"], 0.0)
        # Total cost must equal base cost plus slippage (within rounding).
        self.assertAlmostEqual(
            decision_backtest["total_transaction_cost"],
            decision_backtest["total_base_cost"] + decision_backtest["total_slippage"],
            places=5,
        )
        # Net return is never above gross once base cost and slippage are deducted.
        self.assertLessEqual(
            decision_backtest["net_cumulative_return"],
            decision_backtest["gross_cumulative_return"] + 1e-9,
        )

    def test_final_case_suite_runs(self) -> None:
        system = StockDecisionSystem.from_data_dir(ROOT / "data" / "processed", use_llm="off")
        benchmark = system.benchmark_cases(
            ROOT / "data" / "benchmark" / "cases.json",
            data_dir=ROOT / "data" / "processed",
        )
        self.assertEqual(benchmark["suite"]["case_counts"]["total"], 15)
        self.assertEqual(benchmark["aggregate"]["passed_cases"], 15)
        self.assertTrue(benchmark["success_criteria"]["case_suite_has_10_to_20_stocks"])
        self.assertTrue(benchmark["success_criteria"]["dataset_schema_valid"])
        self.assertTrue(benchmark["success_criteria"]["all_cases_pass"])
        self.assertTrue(benchmark["success_criteria"]["dynamic_strategy_backtest_available"])
        self.assertTrue(benchmark["success_criteria"]["stress_test_available"])
        self.assertGreater(
            benchmark["baseline_comparison"]["equal_weight_backtest"]["observations"],
            0,
        )
        self.assertGreater(
            benchmark["baseline_comparison"]["decision_weighted_backtest"]["observations"],
            0,
        )
        self.assertIn("direct_llm_baseline", benchmark["baseline_comparison"])
        markdown = final_benchmark_to_markdown(benchmark)
        html = final_benchmark_to_html(benchmark)
        self.assertIn("Pass rate: 15/15", markdown)
        self.assertIn("Decision-weighted net cumulative return", markdown)
        self.assertIn("Decision-weighted total transaction cost", markdown)
        self.assertIn("Stock Agent Final Dashboard", html)
        self.assertIn("Decision-Weighted Backtest", html)
        self.assertIn("positive_ai_infrastructure", html)

    def test_dataset_validation_report(self) -> None:
        payload = validate_dataset(
            self.system.prices,
            self.system.news,
            self.system.fundamentals,
            self.system.portfolio,
        )
        self.assertTrue(payload["valid"])
        self.assertGreaterEqual(payload["counts"]["tickers"], 4)
        markdown = data_validation_to_markdown(payload)
        self.assertIn("Dataset Validation", markdown)

    def test_llm_off_disables_direct_llm_baseline(self) -> None:
        original_key = os.environ.get("OPENROUTER_API_KEY")
        os.environ["OPENROUTER_API_KEY"] = "fake-key-should-not-be-used"
        try:
            benchmark = self.system.benchmark(["AAPL", "MSFT", "TSLA", "NVDA"], "2026-05-19")
        finally:
            if original_key is None:
                os.environ.pop("OPENROUTER_API_KEY", None)
            else:
                os.environ["OPENROUTER_API_KEY"] = original_key
        self.assertEqual(benchmark["direct_llm_baseline"]["used_llm_count"], 0)


if __name__ == "__main__":
    unittest.main()
