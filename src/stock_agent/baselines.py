from __future__ import annotations

from datetime import date
from statistics import mean

from .agents import DecisionAgent, FundamentalAnalysisAgent, MarketInformationAgent, NewsSentimentAgent, RiskManagementAgent
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


def action_diversity(decisions: list[Decision] | list[dict]) -> int:
    return len({decision.action if isinstance(decision, Decision) else decision["action"] for decision in decisions})
