from __future__ import annotations

from datetime import date
from statistics import mean, pstdev
from typing import Any

from .llm import LLMError, OpenRouterClient
from .models import AgentResult, FundamentalRecord, NewsItem, PriceBar


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _daily_returns(prices: list[PriceBar]) -> list[float]:
    returns: list[float] = []
    for previous, current in zip(prices, prices[1:]):
        if previous.close:
            returns.append((current.close / previous.close) - 1.0)
    return returns


class MarketInformationAgent:
    name = "market_information"

    def analyze(self, ticker: str, prices: list[PriceBar], as_of: date) -> AgentResult:
        history = sorted(
            [bar for bar in prices if bar.ticker == ticker and bar.date <= as_of],
            key=lambda bar: bar.date,
        )
        if len(history) < 4:
            return AgentResult(
                self.name,
                ticker,
                0.0,
                0.2,
                "Insufficient price history; market signal is uncertain.",
                warnings=["Need at least 4 daily bars for a stable technical summary."],
            )

        window = history[-12:]
        closes = [bar.close for bar in window]
        volumes = [bar.volume for bar in window]
        last_close = closes[-1]
        ma_short = mean(closes[-3:])
        ma_long = mean(closes[-8:]) if len(closes) >= 8 else mean(closes)
        total_return = (last_close / closes[0]) - 1.0
        momentum = (last_close / closes[max(0, len(closes) - 6)]) - 1.0
        returns = _daily_returns(window)
        volatility = pstdev(returns) if len(returns) > 1 else 0.0
        volume_change = (volumes[-1] / mean(volumes[:-1])) - 1.0 if len(volumes) > 1 else 0.0

        score = 0.0
        evidence: list[str] = []
        warnings: list[str] = []

        if last_close > ma_short > ma_long:
            score += 1.1
            evidence.append("Price is above both short and medium moving averages.")
        elif last_close < ma_short < ma_long:
            score -= 1.1
            evidence.append("Price is below both short and medium moving averages.")
        else:
            evidence.append("Moving-average structure is mixed.")

        if momentum > 0.04:
            score += 0.6
            evidence.append("Recent momentum is positive.")
        elif momentum < -0.04:
            score -= 0.6
            evidence.append("Recent momentum is negative.")

        if total_return > 0.06:
            score += 0.3
        elif total_return < -0.06:
            score -= 0.3

        if volatility > 0.035:
            score -= 0.35
            warnings.append("Daily volatility is above the prototype risk threshold.")

        confidence = _clip(0.35 + len(window) / 24 + abs(score) * 0.06, 0.2, 0.92)
        summary = (
            f"Close={last_close:.2f}, MA3={ma_short:.2f}, MA8={ma_long:.2f}, "
            f"12-day return={total_return:.1%}."
        )
        return AgentResult(
            self.name,
            ticker,
            _clip(score, -2.0, 2.0),
            confidence,
            summary,
            evidence,
            warnings,
            {
                "last_close": last_close,
                "ma_short": ma_short,
                "ma_long": ma_long,
                "total_return": total_return,
                "momentum": momentum,
                "daily_volatility": volatility,
                "volume_change": volume_change,
            },
        )


class NewsSentimentAgent:
    name = "news_sentiment"

    def analyze(self, ticker: str, news: list[NewsItem], as_of: date) -> AgentResult:
        items = sorted(
            [item for item in news if item.ticker == ticker and item.date <= as_of],
            key=lambda item: item.date,
        )[-5:]
        if not items:
            return AgentResult(
                self.name,
                ticker,
                0.0,
                0.15,
                "No recent news was available in the offline sample.",
                warnings=["Missing news input; final decision should be conservative."],
            )

        avg_sentiment = mean(item.sentiment for item in items)
        event_risk = any(item.sentiment <= -0.55 for item in items)
        score = _clip(avg_sentiment * 2.0, -2.0, 2.0)
        if event_risk:
            score -= 0.25

        latest = items[-1]
        evidence = [
            f"{item.date.isoformat()}: {item.headline} ({item.sentiment:+.2f})"
            for item in items
        ]
        warnings = ["At least one strongly negative news item was detected."] if event_risk else []
        confidence = _clip(0.25 + len(items) * 0.12 + abs(avg_sentiment) * 0.1, 0.2, 0.9)
        summary = (
            f"Average sample-news sentiment is {avg_sentiment:+.2f}; latest item: "
            f"{latest.headline}."
        )
        return AgentResult(
            self.name,
            ticker,
            score,
            confidence,
            summary,
            evidence,
            warnings,
            {"avg_sentiment": avg_sentiment, "news_count": len(items), "event_risk": event_risk},
        )


class FundamentalAnalysisAgent:
    name = "fundamental_analysis"

    def analyze(
        self, ticker: str, fundamentals: list[FundamentalRecord], as_of: date
    ) -> AgentResult:
        records = [record for record in fundamentals if record.ticker == ticker]
        if not records:
            return AgentResult(
                self.name,
                ticker,
                0.0,
                0.15,
                "No fundamental record was available.",
                warnings=["Missing fundamentals; long-term signal is uncertain."],
            )

        record = sorted(records, key=lambda item: item.period)[-1]
        score = 0.0
        evidence: list[str] = []
        warnings: list[str] = []

        if record.revenue_growth > 0.10:
            score += 0.55
            evidence.append("Revenue growth is above 10%.")
        elif record.revenue_growth < 0:
            score -= 0.55
            evidence.append("Revenue growth is negative.")

        if record.eps_growth > 0.10:
            score += 0.55
            evidence.append("EPS growth is above 10%.")
        elif record.eps_growth < 0:
            score -= 0.55
            evidence.append("EPS growth is negative.")

        if record.net_margin > 0.25:
            score += 0.4
            evidence.append("Net margin is strong.")
        elif record.net_margin < 0.10:
            score -= 0.35
            evidence.append("Net margin is thin.")

        if record.debt_to_equity < 0.7:
            score += 0.25
            evidence.append("Debt-to-equity is moderate.")
        elif record.debt_to_equity > 1.0:
            score -= 0.25
            warnings.append("Debt-to-equity is above the preferred threshold.")

        if record.free_cash_flow_positive:
            score += 0.25
            evidence.append("Free cash flow is positive.")
        else:
            score -= 0.25
            warnings.append("Free cash flow is not positive in the sample record.")

        confidence = _clip(0.55 + abs(score) * 0.08, 0.35, 0.9)
        summary = (
            f"{record.period}: revenue growth={record.revenue_growth:.1%}, "
            f"EPS growth={record.eps_growth:.1%}, net margin={record.net_margin:.1%}."
        )
        return AgentResult(
            self.name,
            ticker,
            _clip(score, -2.0, 2.0),
            confidence,
            summary,
            evidence,
            warnings,
            {
                "period": record.period,
                "revenue_growth": record.revenue_growth,
                "net_margin": record.net_margin,
                "eps_growth": record.eps_growth,
                "debt_to_equity": record.debt_to_equity,
                "free_cash_flow_positive": record.free_cash_flow_positive,
            },
        )


class RiskManagementAgent:
    name = "risk_management"

    def __init__(self, constraints: dict[str, float] | None = None) -> None:
        self.constraints = constraints or {}

    @property
    def max_position_weight(self) -> float:
        return float(self.constraints.get("max_position_weight", 0.35))

    @property
    def max_trade_weight(self) -> float:
        return float(self.constraints.get("max_trade_weight", 0.15))

    @property
    def min_cash_weight(self) -> float:
        return float(self.constraints.get("min_cash_weight", 0.10))

    @property
    def volatility_limit(self) -> float:
        return float(self.constraints.get("volatility_limit", 0.035))

    def check_single(
        self,
        ticker: str,
        proposed_action: str,
        current_weight: float,
        market_result: AgentResult,
    ) -> tuple[AgentResult, str]:
        warnings: list[str] = []
        adjusted_action = proposed_action
        penalty = 0.0
        volatility = float(market_result.metrics.get("daily_volatility", 0.0))

        if current_weight > self.max_position_weight:
            warnings.append(
                f"Current weight {current_weight:.1%} exceeds max position "
                f"{self.max_position_weight:.1%}."
            )
            penalty -= 0.45

        if proposed_action == "BUY" and current_weight >= self.max_position_weight:
            warnings.append("BUY was downgraded because the position is already at the cap.")
            adjusted_action = "HOLD"
            penalty -= 0.35

        if proposed_action == "BUY" and volatility > self.volatility_limit:
            warnings.append(
                f"BUY is high risk because volatility {volatility:.2%} is above "
                f"{self.volatility_limit:.2%}."
            )
            adjusted_action = "HOLD"
            penalty -= 0.35

        if proposed_action == "SELL" and current_weight <= 0.01:
            warnings.append("SELL has little effect because the current position is near zero.")

        if not warnings:
            warnings.append("No prototype risk-rule violation detected.")

        summary = f"Risk check kept action as {adjusted_action}." if adjusted_action == proposed_action else f"Risk check changed action from {proposed_action} to {adjusted_action}."
        return (
            AgentResult(
                self.name,
                ticker,
                penalty,
                0.8,
                summary,
                [f"Current weight={current_weight:.1%}."],
                warnings,
                {
                    "current_weight": current_weight,
                    "volatility": volatility,
                    "max_position_weight": self.max_position_weight,
                    "max_trade_weight": self.max_trade_weight,
                    "min_cash_weight": self.min_cash_weight,
                },
            ),
            adjusted_action,
        )

    def apply_portfolio_constraints(
        self, current_weights: dict[str, float], desired_weights: dict[str, float]
    ) -> tuple[dict[str, float], dict[str, float], list[str]]:
        warnings: list[str] = []
        stock_keys = [key for key in desired_weights if key != "CASH"]
        target = {key: max(0.0, desired_weights.get(key, 0.0)) for key in stock_keys}

        for ticker in stock_keys:
            if target[ticker] > self.max_position_weight:
                target[ticker] = self.max_position_weight
                warnings.append(f"{ticker} target was capped at {self.max_position_weight:.1%}.")

        stock_total = sum(target.values())
        max_stock_total = max(0.0, 1.0 - self.min_cash_weight)
        if stock_total > max_stock_total:
            scale = max_stock_total / stock_total
            for ticker in stock_keys:
                target[ticker] *= scale
            warnings.append("Targets were scaled down to preserve the minimum cash weight.")

        for ticker in stock_keys:
            current = current_weights.get(ticker, 0.0)
            trade = target[ticker] - current
            if abs(trade) > self.max_trade_weight:
                direction = 1.0 if trade > 0 else -1.0
                target[ticker] = current + direction * self.max_trade_weight
                warnings.append(f"{ticker} trade was limited to {self.max_trade_weight:.1%}.")

        stock_total = sum(target.values())
        cash = max(0.0, 1.0 - stock_total)
        if cash < self.min_cash_weight:
            reduce_by = self.min_cash_weight - cash
            reducible = sum(target.values())
            if reducible > 0:
                for ticker in stock_keys:
                    target[ticker] -= reduce_by * (target[ticker] / reducible)
                cash = self.min_cash_weight
                warnings.append("Positions were reduced to restore the minimum cash buffer.")

        target["CASH"] = cash
        trades = {
            key: target.get(key, 0.0) - current_weights.get(key, 0.0)
            for key in sorted(set(current_weights) | set(target))
        }
        total = sum(target.values())
        if abs(total - 1.0) > 1e-6 and target:
            target["CASH"] += 1.0 - total
        return target, trades, warnings


class DecisionAgent:
    name = "decision"

    def __init__(self, risk_agent: RiskManagementAgent) -> None:
        self.risk_agent = risk_agent

    def decide(
        self,
        ticker: str,
        as_of: date,
        market: AgentResult,
        news: AgentResult,
        fundamental: AgentResult,
        current_weight: float,
    ):
        weighted_score = (
            0.45 * market.score + 0.25 * news.score + 0.25 * fundamental.score
        )
        if weighted_score >= 0.75:
            action = "BUY"
        elif weighted_score <= -0.75:
            action = "SELL"
        else:
            action = "HOLD"

        risk, adjusted_action = self.risk_agent.check_single(
            ticker, action, current_weight, market
        )
        final_score = _clip(weighted_score + risk.score, -2.0, 2.0)
        confidence = _clip(
            mean([market.confidence, news.confidence, fundamental.confidence, risk.confidence])
            - (0.08 if adjusted_action != action else 0.0),
            0.15,
            0.95,
        )
        rationale = [
            f"Market: {market.summary}",
            f"News: {news.summary}",
            f"Fundamental: {fundamental.summary}",
            f"Risk: {risk.summary}",
        ]
        return adjusted_action, final_score, confidence, rationale, risk


class LLMDecisionAdvisor:
    name = "llm_decision_advisor"

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client or OpenRouterClient()

    @property
    def available(self) -> bool:
        return self.client.available

    def review(
        self,
        ticker: str,
        as_of: date,
        action: str,
        score: float,
        confidence: float,
        market: AgentResult,
        news: AgentResult,
        fundamental: AgentResult,
        risk: AgentResult,
    ) -> dict[str, Any]:
        system_prompt = (
            "You are a cautious financial research assistant for a course project. "
            "You do not provide real investment advice. Review the structured outputs "
            "from market, news, fundamental, and risk agents for a daily simulated "
            "trading prototype. Return only one JSON object with keys: action "
            "(BUY, SELL, or HOLD), score_adjustment (-0.3 to 0.3), "
            "confidence_adjustment (-0.2 to 0.2), rationale (array of 2-4 short "
            "strings), risk_warnings (array of 1-4 short strings), uncertainty "
            "(short string). Be conservative when evidence conflicts or risk is high."
        )
        payload = {
            "ticker": ticker,
            "as_of": as_of.isoformat(),
            "rule_based_decision": {
                "action": action,
                "score": round(score, 4),
                "confidence": round(confidence, 4),
            },
            "agent_results": {
                "market": market.to_dict(),
                "news": news.to_dict(),
                "fundamental": fundamental.to_dict(),
                "risk": risk.to_dict(),
            },
        }
        try:
            review, raw = self.client.chat_json(system_prompt, payload)
        except LLMError as exc:
            return {
                "enabled": True,
                "used": False,
                "error": str(exc),
                "model": self.client.model,
            }

        reviewed_action = str(review.get("action", action)).upper()
        if reviewed_action not in {"BUY", "SELL", "HOLD"}:
            reviewed_action = action
        score_adjustment = _clip(float(review.get("score_adjustment", 0.0)), -0.3, 0.3)
        confidence_adjustment = _clip(
            float(review.get("confidence_adjustment", 0.0)), -0.2, 0.2
        )
        return {
            "enabled": True,
            "used": True,
            "model": raw.model,
            "usage": raw.usage,
            "action": reviewed_action,
            "score_adjustment": score_adjustment,
            "confidence_adjustment": confidence_adjustment,
            "rationale": _ensure_string_list(review.get("rationale")),
            "risk_warnings": _ensure_string_list(review.get("risk_warnings")),
            "uncertainty": str(review.get("uncertainty", "")).strip(),
        }


def _ensure_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
