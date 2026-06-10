from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class PriceBar:
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class NewsItem:
    ticker: str
    date: date
    headline: str
    summary: str
    sentiment: float
    event_type: str = "general"


@dataclass(frozen=True)
class FundamentalRecord:
    ticker: str
    period: str
    revenue_growth: float
    net_margin: float
    eps_growth: float
    debt_to_equity: float
    free_cash_flow_positive: bool


@dataclass
class AgentResult:
    agent_name: str
    ticker: str
    score: float
    confidence: float
    summary: str
    evidence: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["score"] = round(self.score, 4)
        payload["confidence"] = round(self.confidence, 4)
        return payload


@dataclass
class Decision:
    ticker: str
    as_of: date
    action: str
    score: float
    confidence: float
    rationale: list[str]
    risk_warnings: list[str]
    agent_results: dict[str, AgentResult]
    llm_review: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "as_of": self.as_of.isoformat(),
            "action": self.action,
            "score": round(self.score, 4),
            "confidence": round(self.confidence, 4),
            "rationale": self.rationale,
            "risk_warnings": self.risk_warnings,
            "agent_results": {
                name: result.to_dict() for name, result in self.agent_results.items()
            },
            "llm_review": self.llm_review,
        }


@dataclass
class PortfolioRecommendation:
    as_of: date
    target_weights: dict[str, float]
    trades: dict[str, float]
    warnings: list[str]
    decisions: list[Decision]

    def to_dict(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of.isoformat(),
            "target_weights": {
                key: round(value, 4) for key, value in sorted(self.target_weights.items())
            },
            "trades": {key: round(value, 4) for key, value in sorted(self.trades.items())},
            "warnings": self.warnings,
            "decisions": [decision.to_dict() for decision in self.decisions],
        }


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    task: str
    as_of: date
    tickers: list[str]
    ticker: str | None = None
    portfolio: dict[str, Any] | None = None
    expected_focus: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case_id,
            "task": self.task,
            "as_of": self.as_of.isoformat(),
            "tickers": self.tickers,
            "ticker": self.ticker,
            "portfolio": self.portfolio,
            "expected_focus": self.expected_focus,
        }
