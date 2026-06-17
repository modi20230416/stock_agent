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
    total_cost: float = 0.0
    gross_cumulative_return: float | None = None
    total_base_cost: float = 0.0
    total_slippage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        gross = (
            self.gross_cumulative_return
            if self.gross_cumulative_return is not None
            else self.cumulative_return
        )
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_value": round(self.initial_value, 4),
            "final_value": round(self.final_value, 4),
            "cumulative_return": round(self.cumulative_return, 4),
            "gross_cumulative_return": round(gross, 4),
            "net_cumulative_return": round(self.cumulative_return, 4),
            "total_cost": round(self.total_cost, 6),
            "total_base_cost": round(self.total_base_cost, 6),
            "total_slippage": round(self.total_slippage, 6),
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


def _portfolio_volatility(prices: list[PriceBar], tickers: list[str]) -> dict[str, float]:
    """Historical daily return volatility per ticker, used for slippage scaling."""
    returns_by_date = _returns_by_date(prices, tickers)
    series: dict[str, list[float]] = {}
    for ticker_returns in returns_by_date.values():
        for ticker, value in ticker_returns.items():
            series.setdefault(ticker, []).append(value)
    return {
        ticker: (pstdev(values) if len(values) > 1 else 0.0)
        for ticker, values in series.items()
    }


def _summarize_daily_returns(
    ordered_dates: list[date],
    daily_returns: list[float],
    initial_value: float = 1.0,
    daily_costs: list[float] | None = None,
    daily_base_costs: list[float] | None = None,
    daily_slippages: list[float] | None = None,
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
            total_cost=0.0,
            gross_cumulative_return=0.0,
            total_base_cost=0.0,
            total_slippage=0.0,
        )

    costs = daily_costs if daily_costs is not None else [0.0] * len(daily_returns)
    base_costs = daily_base_costs if daily_base_costs is not None else [0.0] * len(daily_returns)
    slippages = daily_slippages if daily_slippages is not None else [0.0] * len(daily_returns)
    net_returns = [
        gross - cost for gross, cost in zip(daily_returns, costs)
    ]

    value = initial_value
    peak = initial_value
    max_drawdown = 0.0
    for portfolio_return in net_returns:
        value *= 1.0 + portfolio_return
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1.0)

    gross_value = initial_value
    for gross_return in daily_returns:
        gross_value *= 1.0 + gross_return

    cumulative_return = value / initial_value - 1.0
    gross_cumulative_return = gross_value / initial_value - 1.0
    periods = len(net_returns)
    annualized_return = ((value / initial_value) ** (252 / periods) - 1.0) if periods else 0.0
    volatility = pstdev(net_returns) if len(net_returns) > 1 else 0.0
    sharpe = (mean(net_returns) / volatility * sqrt(252)) if volatility else 0.0
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
        total_cost=sum(costs),
        gross_cumulative_return=gross_cumulative_return,
        total_base_cost=sum(base_costs),
        total_slippage=sum(slippages),
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
    cost_per_turn: float = 0.0,
    turnover_by_date: dict[date, float] | None = None,
    impact_coefficient: float = 0.0,
) -> BacktestResult:
    """Weighted backtest with linear base cost plus a convex market-impact slippage.

    Slippage per rebalance is modeled as
        impact_coefficient * turnover^2 * portfolio_volatility
    so that larger trades into more volatile portfolios incur disproportionately
    higher execution cost, in line with square-root/quadratic impact literature.
    """
    returns_by_date = _returns_by_date(prices, tickers)
    ordered_dates = [current_date for current_date in sorted(returns_by_date) if current_date in weights_by_date]
    selected_tickers = [ticker.upper() for ticker in tickers]
    turnover_by_date = turnover_by_date or {}
    vol_by_ticker = _portfolio_volatility(prices, selected_tickers)
    daily_returns: list[float] = []
    daily_costs: list[float] = []
    daily_base_costs: list[float] = []
    daily_slippages: list[float] = []
    for current_date in ordered_dates:
        weights = weights_by_date[current_date]
        ticker_returns = returns_by_date[current_date]
        daily_returns.append(
            sum(weights.get(ticker, 0.0) * ticker_returns.get(ticker, 0.0) for ticker in selected_tickers)
        )
        turnover = turnover_by_date.get(current_date, 0.0)
        base_cost = turnover * cost_per_turn
        portfolio_vol = sum(
            weights.get(ticker, 0.0) * vol_by_ticker.get(ticker, 0.0)
            for ticker in selected_tickers
        )
        slippage = impact_coefficient * (turnover ** 2) * portfolio_vol
        daily_base_costs.append(base_cost)
        daily_slippages.append(slippage)
        daily_costs.append(base_cost + slippage)
    return _summarize_daily_returns(
        ordered_dates,
        daily_returns,
        daily_costs=daily_costs,
        daily_base_costs=daily_base_costs,
        daily_slippages=daily_slippages,
    )


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
