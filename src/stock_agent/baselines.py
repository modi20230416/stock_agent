from __future__ import annotations

from datetime import date
from statistics import mean
from typing import Any

from .agents import DecisionAgent, FundamentalAnalysisAgent, MarketInformationAgent, NewsSentimentAgent, RiskManagementAgent
from .llm import LLMError, OpenRouterClient
from .models import Decision, PriceBar


class TechnicalRuleBaseline:
    """Simple moving-average baseline without news, fundamentals, or risk rules."""

    name = "technical_rule"

    def decide(self, ticker: str, prices: list[PriceBar], as_of: date) -> dict:
        history = sorted(
            [bar for bar in prices if bar.ticker == ticker and bar.date <= as_of],
            key=lambda bar: bar.date,
        )
        if len(history) < 5:
            return {
                "ticker": ticker,
                "action": "HOLD",
                "reason": "Insufficient price history.",
                "score": 0.0,
            }
        closes = [bar.close for bar in history[-8:]]
        last_close = closes[-1]
        moving_average = mean(closes)
        if last_close > moving_average * 1.01:
            action = "BUY"
            score = 1.0
        elif last_close < moving_average * 0.99:
            action = "SELL"
            score = -1.0
        else:
            action = "HOLD"
            score = 0.0
        return {
            "ticker": ticker,
            "action": action,
            "reason": f"Close={last_close:.2f}, MA8={moving_average:.2f}.",
            "score": score,
        }


class NoRiskEnsembleBaseline:
    """Uses the same analysis agents but intentionally skips risk management."""

    name = "no_risk_ensemble"

    def __init__(self) -> None:
        self.market_agent = MarketInformationAgent()
        self.news_agent = NewsSentimentAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()
        self.decision_agent = DecisionAgent(RiskManagementAgent({}))

    def decide(self, ticker: str, as_of: date, prices, news, fundamentals) -> dict:
        market = self.market_agent.analyze(ticker, prices, as_of)
        news_result = self.news_agent.analyze(ticker, news, as_of)
        fundamental = self.fundamental_agent.analyze(ticker, fundamentals, as_of)
        weighted_score = 0.45 * market.score + 0.25 * news_result.score + 0.25 * fundamental.score
        if weighted_score >= 0.75:
            action = "BUY"
        elif weighted_score <= -0.75:
            action = "SELL"
        else:
            action = "HOLD"
        return {
            "ticker": ticker,
            "action": action,
            "score": round(weighted_score, 4),
            "reason": [
                market.summary,
                news_result.summary,
                fundamental.summary,
            ],
            "risk_warnings": [],
        }


class DirectLLMBaseline:
    """Single-agent baseline that reads all structured inputs at once."""

    name = "direct_llm_single_agent"

    def __init__(
        self,
        client: OpenRouterClient | None = None,
        enabled: bool = True,
    ) -> None:
        self.client = client or OpenRouterClient()
        self.enabled = enabled
        self.market_agent = MarketInformationAgent()
        self.news_agent = NewsSentimentAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()

    def decide(self, ticker: str, as_of: date, prices, news, fundamentals) -> dict[str, Any]:
        market = self.market_agent.analyze(ticker, prices, as_of)
        news_result = self.news_agent.analyze(ticker, news, as_of)
        fundamental = self.fundamental_agent.analyze(ticker, fundamentals, as_of)
        fallback_score = 0.40 * market.score + 0.30 * news_result.score + 0.30 * fundamental.score
        fallback_action = "BUY" if fallback_score >= 0.75 else "SELL" if fallback_score <= -0.75 else "HOLD"

        if not self.enabled or not self.client.available:
            reason = (
                "Direct LLM baseline disabled; deterministic direct-agent fallback used."
                if not self.enabled
                else "OPENROUTER_API_KEY is not set; deterministic direct-agent fallback used."
            )
            return {
                "ticker": ticker,
                "action": fallback_action,
                "score": round(fallback_score, 4),
                "used_llm": False,
                "reason": reason,
            }

        system_prompt = (
            "You are a single-agent baseline for a course stock-decision benchmark. "
            "Given structured market, news, and fundamental summaries, return only JSON "
            "with action (BUY/SELL/HOLD), score (-2 to 2), and reason (short string). "
            "Do not give real investment advice."
        )
        payload = {
            "ticker": ticker,
            "as_of": as_of.isoformat(),
            "market": market.to_dict(),
            "news": news_result.to_dict(),
            "fundamental": fundamental.to_dict(),
        }
        try:
            parsed, raw = self.client.chat_json(system_prompt, payload, max_tokens=300)
        except LLMError as exc:
            return {
                "ticker": ticker,
                "action": fallback_action,
                "score": round(fallback_score, 4),
                "used_llm": False,
                "error": str(exc),
                "reason": "LLM baseline failed; deterministic fallback used.",
            }
        action = str(parsed.get("action", fallback_action)).upper()
        if action not in {"BUY", "SELL", "HOLD"}:
            action = fallback_action
        try:
            score = float(parsed.get("score", fallback_score))
        except (TypeError, ValueError):
            score = fallback_score
        return {
            "ticker": ticker,
            "action": action,
            "score": round(max(-2.0, min(2.0, score)), 4),
            "used_llm": True,
            "model": raw.model,
            "reason": str(parsed.get("reason", "")).strip(),
        }


def action_diversity(decisions: list[Decision] | list[dict]) -> int:
    return len({decision.action if isinstance(decision, Decision) else decision["action"] for decision in decisions})
