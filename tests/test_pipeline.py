from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

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
        self.assertTrue(benchmark["success_criteria"]["single_stock_has_action_reason_and_risk"])
        self.assertTrue(benchmark["success_criteria"]["rebalance_respects_constraints"])

    def test_final_case_suite_runs(self) -> None:
        system = StockDecisionSystem.from_data_dir(ROOT / "data" / "processed", use_llm="off")
        benchmark = system.benchmark_cases(
            ROOT / "data" / "benchmark" / "cases.json",
            data_dir=ROOT / "data" / "processed",
        )
        self.assertEqual(benchmark["suite"]["case_counts"]["total"], 15)
        self.assertEqual(benchmark["aggregate"]["passed_cases"], 15)
        self.assertTrue(benchmark["success_criteria"]["case_suite_has_10_to_20_stocks"])
        self.assertTrue(benchmark["success_criteria"]["all_cases_pass"])
        self.assertGreater(
            benchmark["baseline_comparison"]["equal_weight_backtest"]["observations"],
            0,
        )
        self.assertIn("direct_llm_baseline", benchmark["baseline_comparison"])

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
