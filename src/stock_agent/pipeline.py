from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .agents import (
    DecisionAgent,
    FundamentalAnalysisAgent,
    LLMDecisionAdvisor,
    MarketInformationAgent,
    NewsSentimentAgent,
    RiskManagementAgent,
)
from .backtest import equal_weight_backtest, stress_test_portfolio, weighted_backtest
from .baselines import (
    DirectLLMBaseline,
    NoRiskEnsembleBaseline,
    TechnicalRuleBaseline,
    action_diversity,
)
from .data_loader import load_benchmark_cases, load_sample_dataset, parse_date, validate_dataset
from .models import Decision, FundamentalRecord, NewsItem, PortfolioRecommendation, PriceBar


class StockDecisionSystem:
    def __init__(
        self,
        prices: list[PriceBar],
        news: list[NewsItem],
        fundamentals: list[FundamentalRecord],
        portfolio: dict[str, Any],
        use_llm: str = "auto",
    ) -> None:
        self.prices = prices
        self.news = news
        self.fundamentals = fundamentals
        self.portfolio = portfolio
        self.use_llm = use_llm
        self.constraints = portfolio.get("constraints", {})
        self.market_agent = MarketInformationAgent()
        self.news_agent = NewsSentimentAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()
        self.risk_agent = RiskManagementAgent(self.constraints)
        self.decision_agent = DecisionAgent(self.risk_agent)
        self.llm_advisor = LLMDecisionAdvisor()

    @classmethod
    def from_data_dir(
        cls, data_dir: str | Path, use_llm: str = "auto"
    ) -> "StockDecisionSystem":
        prices, news, fundamentals, portfolio = load_sample_dataset(data_dir)
        return cls(prices, news, fundamentals, portfolio, use_llm=use_llm)

    def tickers(self) -> list[str]:
        return sorted({bar.ticker for bar in self.prices})

    def current_weight(self, ticker: str) -> float:
        positions = self.portfolio.get("positions", {})
        return float(positions.get(ticker, 0.0))

    def with_portfolio(self, portfolio: dict[str, Any]) -> "StockDecisionSystem":
        return StockDecisionSystem(
            self.prices,
            self.news,
            self.fundamentals,
            portfolio,
            use_llm=self.use_llm,
        )

    def analyze_single(self, ticker: str, as_of: str | date) -> Decision:
        parsed_as_of = parse_date(as_of) if isinstance(as_of, str) else as_of
        ticker = ticker.upper()
        market = self.market_agent.analyze(ticker, self.prices, parsed_as_of)
        news = self.news_agent.analyze(ticker, self.news, parsed_as_of)
        fundamental = self.fundamental_agent.analyze(
            ticker, self.fundamentals, parsed_as_of
        )
        action, score, confidence, rationale, risk = self.decision_agent.decide(
            ticker,
            parsed_as_of,
            market,
            news,
            fundamental,
            self.current_weight(ticker),
        )
        risk_warnings = list(dict.fromkeys(market.warnings + news.warnings + fundamental.warnings + risk.warnings))
        llm_review = self._maybe_review_with_llm(
            ticker, parsed_as_of, action, score, confidence, market, news, fundamental, risk
        )
        if llm_review and llm_review.get("used"):
            action = llm_review["action"]
            score = max(-2.0, min(2.0, score + llm_review["score_adjustment"]))
            confidence = max(
                0.15, min(0.95, confidence + llm_review["confidence_adjustment"])
            )
            rationale.extend([f"LLM: {item}" for item in llm_review["rationale"]])
            risk_warnings = list(
                dict.fromkeys(risk_warnings + llm_review["risk_warnings"])
            )
            if llm_review.get("uncertainty"):
                risk_warnings.append(f"LLM uncertainty: {llm_review['uncertainty']}")
        return Decision(
            ticker=ticker,
            as_of=parsed_as_of,
            action=action,
            score=score,
            confidence=confidence,
            rationale=rationale,
            risk_warnings=risk_warnings,
            agent_results={
                "market": market,
                "news": news,
                "fundamental": fundamental,
                "risk": risk,
            },
            llm_review=llm_review,
        )

    def _maybe_review_with_llm(
        self,
        ticker: str,
        as_of: date,
        action: str,
        score: float,
        confidence: float,
        market,
        news,
        fundamental,
        risk,
    ) -> dict[str, Any] | None:
        if self.use_llm == "off":
            return {"enabled": False, "used": False, "reason": "LLM disabled."}
        if self.use_llm not in {"auto", "required"}:
            raise ValueError("use_llm must be one of: auto, required, off")
        if self.use_llm == "auto" and not self.llm_advisor.available:
            return {
                "enabled": True,
                "used": False,
                "reason": "OPENROUTER_API_KEY is not set; using rule-based fallback.",
                "model": self.llm_advisor.client.model,
            }
        review = self.llm_advisor.review(
            ticker, as_of, action, score, confidence, market, news, fundamental, risk
        )
        if self.use_llm == "required" and not review.get("used"):
            raise RuntimeError(review.get("error") or "LLM review failed.")
        return review

    def screen_candidates(self, tickers: list[str] | None, as_of: str | date) -> list[dict]:
        candidate_tickers = [ticker.upper() for ticker in (tickers or self.tickers())]
        decisions = [self.analyze_single(ticker, as_of) for ticker in candidate_tickers]
        ranked = sorted(decisions, key=lambda decision: decision.score, reverse=True)
        return [
            {
                "rank": index + 1,
                "ticker": decision.ticker,
                "action": decision.action,
                "score": round(decision.score, 4),
                "confidence": round(decision.confidence, 4),
                "top_reason": decision.rationale[0],
                "risk_warnings": decision.risk_warnings,
            }
            for index, decision in enumerate(ranked)
        ]

    def rebalance(self, tickers: list[str] | None, as_of: str | date) -> PortfolioRecommendation:
        parsed_as_of = parse_date(as_of) if isinstance(as_of, str) else as_of
        candidate_tickers = [ticker.upper() for ticker in (tickers or self.tickers())]
        decisions = [self.analyze_single(ticker, parsed_as_of) for ticker in candidate_tickers]
        current_weights = {
            ticker.upper(): float(weight)
            for ticker, weight in self.portfolio.get("positions", {}).items()
        }
        current_weights["CASH"] = float(self.portfolio.get("cash", 0.0))

        preferences: dict[str, float] = {}
        for decision in decisions:
            if decision.action == "SELL":
                preferences[decision.ticker] = 0.0
            elif decision.action == "BUY":
                preferences[decision.ticker] = max(0.2, decision.score + 1.0)
            else:
                preferences[decision.ticker] = max(0.15, decision.score + 0.8)

        total_preference = sum(preferences.values())
        investable = 1.0 - self.risk_agent.min_cash_weight
        if total_preference <= 0:
            desired_weights = {
                ticker: current_weights.get(ticker, 0.0) for ticker in candidate_tickers
            }
        else:
            desired_weights = {
                ticker: (value / total_preference) * investable
                for ticker, value in preferences.items()
            }
        desired_weights["CASH"] = self.risk_agent.min_cash_weight
        target, trades, warnings = self.risk_agent.apply_portfolio_constraints(
            current_weights, desired_weights
        )
        return PortfolioRecommendation(parsed_as_of, target, trades, warnings, decisions)

    def benchmark(self, tickers: list[str] | None, as_of: str | date) -> dict[str, Any]:
        candidate_tickers = [ticker.upper() for ticker in (tickers or self.tickers())]
        parsed_as_of = parse_date(as_of) if isinstance(as_of, str) else as_of
        decisions = [self.analyze_single(ticker, as_of) for ticker in candidate_tickers]
        rebalance = self.rebalance(candidate_tickers, as_of)
        technical = TechnicalRuleBaseline()
        no_risk = NoRiskEnsembleBaseline()
        direct_llm = DirectLLMBaseline(enabled=self.use_llm != "off")
        technical_outputs = [
            technical.decide(ticker, self.prices, parsed_as_of)
            for ticker in candidate_tickers
        ]
        no_risk_outputs = [
            no_risk.decide(
                ticker,
                parsed_as_of,
                self.prices,
                self.news,
                self.fundamentals,
            )
            for ticker in candidate_tickers
        ]
        direct_outputs = [
            direct_llm.decide(
                ticker,
                parsed_as_of,
                self.prices,
                self.news,
                self.fundamentals,
            )
            for ticker in candidate_tickers
        ]
        violations = self._constraint_violations(rebalance.target_weights)
        backtest = equal_weight_backtest(self.prices, candidate_tickers)
        decision_backtest = self._decision_weighted_backtest(candidate_tickers)
        stress_test = stress_test_portfolio(rebalance.target_weights)
        data_validation = validate_dataset(
            self.prices, self.news, self.fundamentals, self.portfolio
        )
        return {
            "as_of": as_of if isinstance(as_of, str) else as_of.isoformat(),
            "tickers": candidate_tickers,
            "data_validation": data_validation,
            "llm": {
                "mode": self.use_llm,
                "model": self.llm_advisor.client.model,
                "used_count": sum(1 for decision in decisions if (decision.llm_review or {}).get("used")),
            },
            "success_criteria": {
                "dataset_schema_valid": data_validation["valid"],
                "single_stock_has_action_reason_and_risk": all(
                    decision.action and decision.rationale and decision.risk_warnings
                    for decision in decisions
                ),
                "screening_distinguishes_candidates": action_diversity(decisions) >= 2
                or len({round(decision.score, 2) for decision in decisions}) >= 2,
                "rebalance_respects_constraints": not violations,
                "uncertainty_is_explicit": any(
                    any("Missing" in warning or "uncertain" in warning.lower() for warning in decision.risk_warnings)
                    for decision in decisions
                )
                or all(decision.risk_warnings for decision in decisions),
            },
            "multi_agent_with_risk": {
                "actions": {decision.ticker: decision.action for decision in decisions},
                "scores": {decision.ticker: round(decision.score, 4) for decision in decisions},
                "risk_warning_count": sum(len(decision.risk_warnings) for decision in decisions),
                "action_diversity": action_diversity(decisions),
                "constraint_violations": violations,
            },
            "technical_rule_baseline": {
                "actions": {item["ticker"]: item["action"] for item in technical_outputs},
                "scores": {item["ticker"]: item["score"] for item in technical_outputs},
                "risk_warning_count": 0,
                "action_diversity": action_diversity(technical_outputs),
            },
            "no_risk_ensemble_baseline": {
                "actions": {item["ticker"]: item["action"] for item in no_risk_outputs},
                "scores": {item["ticker"]: item["score"] for item in no_risk_outputs},
                "risk_warning_count": 0,
                "action_diversity": action_diversity(no_risk_outputs),
            },
            "direct_llm_baseline": {
                "actions": {item["ticker"]: item["action"] for item in direct_outputs},
                "scores": {item["ticker"]: item["score"] for item in direct_outputs},
                "used_llm_count": sum(1 for item in direct_outputs if item.get("used_llm")),
                "action_diversity": action_diversity(direct_outputs),
            },
            "equal_weight_backtest": backtest.to_dict(),
            "decision_weighted_backtest": decision_backtest,
            "stress_test": stress_test,
            "rebalance": rebalance.to_dict(),
        }

    def benchmark_cases(
        self,
        cases_file: str | Path,
        data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        suite = load_benchmark_cases(cases_file, data_dir=data_dir)
        cases = suite["cases"]
        default_pool = suite["default_pool"] or self.tickers()
        as_of = suite["as_of"]

        single_results = []
        for case in cases["single"]:
            if case.ticker is None:
                continue
            decision = self.analyze_single(case.ticker, case.as_of)
            expected_focus = (case.expected_focus or "").lower()
            evidence_text = " ".join(
                decision.rationale
                + decision.risk_warnings
                + [
                    result.summary
                    for result in decision.agent_results.values()
                ]
            ).lower()
            focus_tokens = [
                token.strip(".,;:()")
                for token in expected_focus.split()
                if len(token.strip(".,;:()")) >= 5
            ]
            focus_hits = [token for token in focus_tokens if token in evidence_text]
            single_results.append(
                {
                    "case": case.to_dict(),
                    "decision": decision.to_dict(),
                    "focus_hits": focus_hits,
                    "passed": bool(decision.action and decision.rationale and decision.risk_warnings)
                    and {"market", "news", "fundamental", "risk"}.issubset(decision.agent_results),
                }
            )

        screen_results = []
        for case in cases["screen"]:
            ranking = self.screen_candidates(case.tickers, case.as_of)
            score_diversity = len({item["score"] for item in ranking})
            action_count = len({item["action"] for item in ranking})
            screen_results.append(
                {
                    "case": case.to_dict(),
                    "ranking": ranking,
                    "passed": len(ranking) == len(case.tickers)
                    and (score_diversity >= 2 or action_count >= 2),
                }
            )

        rebalance_results = []
        for case in cases["rebalance"]:
            case_system = self.with_portfolio(case.portfolio) if case.portfolio else self
            recommendation = case_system.rebalance(case.tickers, case.as_of)
            violations = case_system._constraint_violations(recommendation.target_weights)
            rebalance_results.append(
                {
                    "case": case.to_dict(),
                    "recommendation": recommendation.to_dict(),
                    "constraint_violations": violations,
                    "passed": not violations,
                }
            )

        all_case_results = single_results + screen_results + rebalance_results
        passed_cases = sum(1 for item in all_case_results if item["passed"])
        total_cases = len(all_case_results)
        baseline = self.benchmark(default_pool, as_of)
        return {
            "suite": {
                "as_of": as_of,
                "default_pool": default_pool,
                "case_counts": {
                    "single": len(single_results),
                    "screen": len(screen_results),
                    "rebalance": len(rebalance_results),
                    "total": total_cases,
                },
            },
            "aggregate": {
                "passed_cases": passed_cases,
                "total_cases": total_cases,
                "pass_rate": round(passed_cases / total_cases, 4) if total_cases else 0.0,
            },
            "success_criteria": {
                "case_suite_has_10_to_20_stocks": 10 <= len(default_pool) <= 20,
                "dataset_schema_valid": baseline["data_validation"]["valid"],
                "all_cases_pass": passed_cases == total_cases and total_cases > 0,
                "multi_agent_beats_minimal_surface": (
                    baseline["multi_agent_with_risk"]["risk_warning_count"]
                    > baseline["technical_rule_baseline"]["risk_warning_count"]
                    and not baseline["multi_agent_with_risk"]["constraint_violations"]
                ),
                "backtest_available": baseline["equal_weight_backtest"]["observations"] > 0,
                "dynamic_strategy_backtest_available": baseline["decision_weighted_backtest"]["observations"] > 0,
                "stress_test_available": len(baseline["stress_test"]) >= 3,
            },
            "single_cases": single_results,
            "screen_cases": screen_results,
            "rebalance_cases": rebalance_results,
            "baseline_comparison": baseline,
        }

    def _constraint_violations(self, weights: dict[str, float]) -> list[str]:
        violations: list[str] = []
        max_position = self.risk_agent.max_position_weight
        min_cash = self.risk_agent.min_cash_weight
        for ticker, weight in weights.items():
            if ticker != "CASH" and weight > max_position + 1e-6:
                violations.append(f"{ticker} exceeds max position weight.")
        if weights.get("CASH", 0.0) + 1e-6 < min_cash:
            violations.append("Cash is below minimum cash weight.")
        if abs(sum(weights.values()) - 1.0) > 1e-6:
            violations.append("Target weights do not sum to 1.")
        return violations

    def _decision_weighted_backtest(
        self, tickers: list[str], rebalance_interval_days: int = 5
    ) -> dict[str, Any]:
        selected = [ticker.upper() for ticker in tickers]
        dates = sorted({bar.date for bar in self.prices if bar.ticker in selected})
        if len(dates) < 2:
            empty = equal_weight_backtest(self.prices, selected).to_dict()
            empty.update(
                {
                    "method": "decision_weighted",
                    "rebalance_interval_days": rebalance_interval_days,
                    "rebalance_count": 0,
                    "average_turnover": 0.0,
                    "average_cash_weight": 0.0,
                    "risk_warning_count": 0,
                }
            )
            return empty

        rule_system = (
            self
            if self.use_llm == "off"
            else StockDecisionSystem(
                self.prices,
                self.news,
                self.fundamentals,
                self.portfolio,
                use_llm="off",
            )
        )
        current_weights = {
            ticker.upper(): float(weight)
            for ticker, weight in self.portfolio.get("positions", {}).items()
        }
        current_weights["CASH"] = float(self.portfolio.get("cash", 0.0))
        weights_by_date: dict[date, dict[str, float]] = {}
        turnover_total = 0.0
        cash_total = 0.0
        warning_count = 0
        rebalance_count = 0

        for index in range(1, len(dates)):
            signal_date = dates[index - 1]
            return_date = dates[index]
            if index == 1 or (index - 1) % rebalance_interval_days == 0:
                portfolio_state = {
                    "positions": {
                        ticker: weight
                        for ticker, weight in current_weights.items()
                        if ticker != "CASH"
                    },
                    "cash": current_weights.get("CASH", 0.0),
                    "constraints": self.constraints,
                }
                recommendation = rule_system.with_portfolio(portfolio_state).rebalance(
                    selected, signal_date
                )
                current_weights = recommendation.target_weights
                turnover_total += sum(
                    abs(value)
                    for asset, value in recommendation.trades.items()
                    if asset != "CASH"
                )
                cash_total += current_weights.get("CASH", 0.0)
                warning_count += len(recommendation.warnings)
                rebalance_count += 1
            weights_by_date[return_date] = dict(current_weights)

        result = weighted_backtest(self.prices, selected, weights_by_date).to_dict()
        result.update(
            {
                "method": "decision_weighted",
                "rebalance_interval_days": rebalance_interval_days,
                "rebalance_count": rebalance_count,
                "average_turnover": round(
                    turnover_total / rebalance_count if rebalance_count else 0.0, 4
                ),
                "average_cash_weight": round(
                    cash_total / rebalance_count if rebalance_count else 0.0, 4
                ),
                "risk_warning_count": warning_count,
            }
        )
        return result
