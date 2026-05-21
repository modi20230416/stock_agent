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
from .baselines import NoRiskEnsembleBaseline, TechnicalRuleBaseline, action_diversity
from .data_loader import load_sample_dataset, parse_date
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
        decisions = [self.analyze_single(ticker, as_of) for ticker in candidate_tickers]
        rebalance = self.rebalance(candidate_tickers, as_of)
        technical = TechnicalRuleBaseline()
        no_risk = NoRiskEnsembleBaseline()
        technical_outputs = [
            technical.decide(ticker, self.prices, parse_date(as_of) if isinstance(as_of, str) else as_of)
            for ticker in candidate_tickers
        ]
        no_risk_outputs = [
            no_risk.decide(
                ticker,
                parse_date(as_of) if isinstance(as_of, str) else as_of,
                self.prices,
                self.news,
                self.fundamentals,
            )
            for ticker in candidate_tickers
        ]
        violations = self._constraint_violations(rebalance.target_weights)
        return {
            "as_of": as_of if isinstance(as_of, str) else as_of.isoformat(),
            "tickers": candidate_tickers,
            "llm": {
                "mode": self.use_llm,
                "model": self.llm_advisor.client.model,
                "used_count": sum(1 for decision in decisions if (decision.llm_review or {}).get("used")),
            },
            "success_criteria": {
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
            "rebalance": rebalance.to_dict(),
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
