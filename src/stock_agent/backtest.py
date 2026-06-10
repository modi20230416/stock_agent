from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import sqrt
from statistics import mean, pstdev
from typing import Any

from .models import PriceBar


@dataclass(frozen=True)
class BacktestResult:
    start_date: date
    end_date: date
    initial_value: float
    final_value: float
    cumulative_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    observations: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_value": round(self.initial_value, 4),
            "final_value": round(self.final_value, 4),
            "cumulative_return": round(self.cumulative_return, 4),
            "annualized_return": round(self.annualized_return, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "observations": self.observations,
        }


def _returns_by_date(prices: list[PriceBar], tickers: list[str]) -> dict[date, dict[str, float]]:
    selected = {ticker.upper() for ticker in tickers}
    by_ticker: dict[str, list[PriceBar]] = {}
    for bar in sorted(prices, key=lambda item: (item.ticker, item.date)):
        if bar.ticker in selected:
            by_ticker.setdefault(bar.ticker, []).append(bar)
    by_date: dict[date, dict[str, float]] = {}
    for ticker, bars in by_ticker.items():
        for previous, current in zip(bars, bars[1:]):
            if previous.close:
                by_date.setdefault(current.date, {})[ticker] = current.close / previous.close - 1.0
    return by_date


def equal_weight_backtest(prices: list[PriceBar], tickers: list[str], cash_weight: float = 0.1) -> BacktestResult:
    returns_by_date = _returns_by_date(prices, tickers)
    ordered_dates = sorted(returns_by_date)
    if not ordered_dates:
        today = date.today()
        return BacktestResult(today, today, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0)

    stock_weight = (1.0 - cash_weight) / max(1, len(tickers))
    daily_returns: list[float] = []
    value = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for current_date in ordered_dates:
        ticker_returns = returns_by_date[current_date]
        portfolio_return = sum(stock_weight * ticker_returns.get(ticker, 0.0) for ticker in tickers)
        daily_returns.append(portfolio_return)
        value *= 1.0 + portfolio_return
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1.0)

    cumulative_return = value - 1.0
    periods = len(daily_returns)
    annualized_return = (value ** (252 / periods) - 1.0) if periods else 0.0
    volatility = pstdev(daily_returns) if len(daily_returns) > 1 else 0.0
    sharpe = (mean(daily_returns) / volatility * sqrt(252)) if volatility else 0.0
    return BacktestResult(
        start_date=ordered_dates[0],
        end_date=ordered_dates[-1],
        initial_value=1.0,
        final_value=value,
        cumulative_return=cumulative_return,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe,
        observations=periods,
    )
