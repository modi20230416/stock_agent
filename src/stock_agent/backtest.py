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


def _summarize_daily_returns(
    ordered_dates: list[date], daily_returns: list[float], initial_value: float = 1.0
) -> BacktestResult:
    if not ordered_dates:
        today = date.today()
        return BacktestResult(
            today,
            today,
            initial_value,
            initial_value,
            0.0,
            0.0,
            0.0,
            0.0,
            0,
        )

    value = initial_value
    peak = initial_value
    max_drawdown = 0.0
    for portfolio_return in daily_returns:
        value *= 1.0 + portfolio_return
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1.0)

    cumulative_return = value / initial_value - 1.0
    periods = len(daily_returns)
    annualized_return = ((value / initial_value) ** (252 / periods) - 1.0) if periods else 0.0
    volatility = pstdev(daily_returns) if len(daily_returns) > 1 else 0.0
    sharpe = (mean(daily_returns) / volatility * sqrt(252)) if volatility else 0.0
    return BacktestResult(
        start_date=ordered_dates[0],
        end_date=ordered_dates[-1],
        initial_value=initial_value,
        final_value=value,
        cumulative_return=cumulative_return,
        annualized_return=annualized_return,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe,
        observations=periods,
    )


def equal_weight_backtest(prices: list[PriceBar], tickers: list[str], cash_weight: float = 0.1) -> BacktestResult:
    returns_by_date = _returns_by_date(prices, tickers)
    ordered_dates = sorted(returns_by_date)
    selected_tickers = [ticker.upper() for ticker in tickers]
    stock_weight = (1.0 - cash_weight) / max(1, len(selected_tickers))
    daily_returns = [
        sum(stock_weight * returns_by_date[current_date].get(ticker, 0.0) for ticker in selected_tickers)
        for current_date in ordered_dates
    ]
    return _summarize_daily_returns(ordered_dates, daily_returns)


def weighted_backtest(
    prices: list[PriceBar],
    tickers: list[str],
    weights_by_date: dict[date, dict[str, float]],
) -> BacktestResult:
    returns_by_date = _returns_by_date(prices, tickers)
    ordered_dates = [current_date for current_date in sorted(returns_by_date) if current_date in weights_by_date]
    selected_tickers = [ticker.upper() for ticker in tickers]
    daily_returns: list[float] = []
    for current_date in ordered_dates:
        weights = weights_by_date[current_date]
        ticker_returns = returns_by_date[current_date]
        daily_returns.append(
            sum(weights.get(ticker, 0.0) * ticker_returns.get(ticker, 0.0) for ticker in selected_tickers)
        )
    return _summarize_daily_returns(ordered_dates, daily_returns)


def stress_test_portfolio(weights: dict[str, float]) -> list[dict[str, Any]]:
    scenarios: dict[str, dict[str, float]] = {
        "broad_market_selloff": {"*": -0.08},
        "tech_ai_drawdown": {
            "*": -0.03,
            "AAPL": -0.10,
            "MSFT": -0.09,
            "NVDA": -0.14,
            "AMZN": -0.08,
            "GOOGL": -0.08,
            "META": -0.09,
            "AMD": -0.13,
            "TSLA": -0.12,
        },
        "rates_credit_tightening": {
            "*": -0.04,
            "JPM": -0.09,
            "TSLA": -0.07,
            "AMD": -0.07,
            "NVDA": -0.07,
        },
        "energy_price_spike": {
            "*": -0.025,
            "XOM": 0.07,
            "WMT": -0.01,
            "UNH": -0.015,
        },
        "defensive_rotation": {
            "*": -0.035,
            "WMT": 0.025,
            "UNH": 0.015,
            "JPM": -0.01,
            "XOM": 0.005,
        },
    }
    results: list[dict[str, Any]] = []
    for scenario, shocks in scenarios.items():
        contributions: dict[str, float] = {}
        for asset, weight in weights.items():
            ticker = asset.upper()
            if ticker == "CASH":
                shock = 0.0
            else:
                shock = shocks.get(ticker, shocks.get("*", 0.0))
            contributions[ticker] = weight * shock
        portfolio_return = sum(contributions.values())
        worst = sorted(
            (
                {"asset": asset, "contribution": round(value, 4)}
                for asset, value in contributions.items()
                if asset != "CASH"
            ),
            key=lambda item: item["contribution"],
        )[:3]
        results.append(
            {
                "scenario": scenario,
                "portfolio_return": round(portfolio_return, 4),
                "worst_contributors": worst,
            }
        )
    return results
