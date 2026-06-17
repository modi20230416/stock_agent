from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from .models import BenchmarkCase, FundamentalRecord, NewsItem, PriceBar


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def load_prices(path: str | Path) -> list[PriceBar]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            PriceBar(
                ticker=row["ticker"].upper(),
                date=parse_date(row["date"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]),
            )
            for row in reader
        ]


def load_news(path: str | Path) -> list[NewsItem]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            NewsItem(
                ticker=row["ticker"].upper(),
                date=parse_date(row["date"]),
                headline=row["headline"],
                summary=row["summary"],
                sentiment=float(row["sentiment"]),
                event_type=row.get("event_type", "general") or "general",
            )
            for row in reader
        ]


def load_fundamentals(path: str | Path) -> list[FundamentalRecord]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            FundamentalRecord(
                ticker=row["ticker"].upper(),
                period=row["period"],
                revenue_growth=float(row["revenue_growth"]),
                net_margin=float(row["net_margin"]),
                eps_growth=float(row["eps_growth"]),
                debt_to_equity=float(row["debt_to_equity"]),
                free_cash_flow_positive=row["free_cash_flow_positive"].strip().lower()
                in {"true", "1", "yes", "y"},
            )
            for row in reader
        ]


def load_portfolio(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_benchmark_cases(path: str | Path, data_dir: str | Path | None = None) -> dict:
    root = Path(data_dir) if data_dir is not None else Path(path).parent
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)

    cases: dict[str, list[BenchmarkCase]] = {
        "single": [],
        "screen": [],
        "rebalance": [],
    }
    for item in payload.get("single_cases", []):
        ticker = item["ticker"].upper()
        cases["single"].append(
            BenchmarkCase(
                case_id=item["id"],
                task="single",
                as_of=parse_date(item.get("as_of", payload["as_of"])),
                tickers=[ticker],
                ticker=ticker,
                expected_focus=item.get("expected_focus"),
            )
        )
    for item in payload.get("screen_cases", []):
        cases["screen"].append(
            BenchmarkCase(
                case_id=item["id"],
                task="screen",
                as_of=parse_date(item.get("as_of", payload["as_of"])),
                tickers=[ticker.upper() for ticker in item["tickers"]],
            )
        )
    for item in payload.get("rebalance_cases", []):
        portfolio = item.get("portfolio")
        if isinstance(portfolio, str):
            portfolio = load_portfolio(root / portfolio)
        cases["rebalance"].append(
            BenchmarkCase(
                case_id=item["id"],
                task="rebalance",
                as_of=parse_date(item.get("as_of", payload["as_of"])),
                tickers=[ticker.upper() for ticker in item["tickers"]],
                portfolio=portfolio,
            )
        )
    return {
        "as_of": payload.get("as_of"),
        "default_pool": [ticker.upper() for ticker in payload.get("default_pool", [])],
        "cases": cases,
    }


def load_vendor_prices(
    ticker: str,
    path: str | Path,
    start: date | None = None,
    end: date | None = None,
) -> list[PriceBar]:
    """Load a raw vendor CSV file (Stooq/Yahoo/Kaggle style) for one ticker.

    This normalizes external column names (e.g. ``Date,Open,High,Low,Close,Volume``
    or ``Adj Close``) into the internal OHLCV schema.
    """
    from .data_sources import normalize_vendor_csv

    csv_text = Path(path).read_text(encoding="utf-8")
    return normalize_vendor_csv(ticker, csv_text, start=start, end=end)


def load_sample_dataset(data_dir: str | Path) -> tuple[list[PriceBar], list[NewsItem], list[FundamentalRecord], dict]:
    root = Path(data_dir)
    return (
        load_prices(root / "prices.csv"),
        load_news(root / "news.csv"),
        load_fundamentals(root / "fundamentals.csv"),
        load_portfolio(root / "portfolio.json"),
    )


def load_dataset(
    data_dir: str | Path,
) -> tuple[list[PriceBar], list[NewsItem], list[FundamentalRecord], dict]:
    return load_sample_dataset(data_dir)


def validate_dataset(
    prices: list[PriceBar],
    news: list[NewsItem],
    fundamentals: list[FundamentalRecord],
    portfolio: dict,
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    price_tickers = sorted({bar.ticker for bar in prices})
    news_tickers = sorted({item.ticker for item in news})
    fundamental_tickers = sorted({item.ticker for item in fundamentals})
    price_dates = sorted({bar.date for bar in prices})

    if not prices:
        errors.append("prices.csv has no rows.")
    if not price_tickers:
        errors.append("No ticker universe could be inferred from prices.")
    if len(price_tickers) < 10:
        warnings.append("Ticker universe has fewer than 10 stocks; final benchmark expects 10-20.")
    if len(price_tickers) > 20:
        warnings.append("Ticker universe has more than 20 stocks; course benchmark may be too broad.")

    invalid_price_rows = [
        f"{bar.ticker}@{bar.date.isoformat()}"
        for bar in prices
        if bar.low > bar.high
        or bar.close <= 0
        or bar.open <= 0
        or bar.high <= 0
        or bar.low <= 0
        or bar.volume < 0
    ]
    if invalid_price_rows:
        errors.append(
            "Invalid OHLCV rows: " + ", ".join(invalid_price_rows[:5])
            + (" ..." if len(invalid_price_rows) > 5 else "")
        )

    missing_news = sorted(set(price_tickers) - set(news_tickers))
    missing_fundamentals = sorted(set(price_tickers) - set(fundamental_tickers))
    if missing_news:
        warnings.append("Missing news rows for: " + ", ".join(missing_news))
    if missing_fundamentals:
        errors.append("Missing fundamental rows for: " + ", ".join(missing_fundamentals))

    constraints = portfolio.get("constraints", {})
    positions = portfolio.get("positions", {})
    cash = float(portfolio.get("cash", 0.0))
    total_weight = cash + sum(float(weight) for weight in positions.values())
    if abs(total_weight - 1.0) > 1e-4:
        warnings.append(f"Portfolio weights sum to {total_weight:.4f}, not exactly 1.0.")
    if cash < 0:
        errors.append("Portfolio cash weight is negative.")
    if float(constraints.get("max_position_weight", 1.0)) <= 0:
        errors.append("max_position_weight must be positive.")
    if float(constraints.get("max_trade_weight", 1.0)) <= 0:
        errors.append("max_trade_weight must be positive.")
    min_cash = float(constraints.get("min_cash_weight", 0.0))
    if min_cash < 0 or min_cash > 1:
        errors.append("min_cash_weight must be in [0, 1].")

    coverage_by_ticker = {
        ticker: sum(1 for bar in prices if bar.ticker == ticker)
        for ticker in price_tickers
    }
    min_price_rows = min(coverage_by_ticker.values()) if coverage_by_ticker else 0
    if min_price_rows < 20:
        warnings.append("At least one ticker has fewer than 20 price rows.")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "prices": len(prices),
            "news": len(news),
            "fundamentals": len(fundamentals),
            "tickers": len(price_tickers),
            "price_dates": len(price_dates),
        },
        "date_range": {
            "start": price_dates[0].isoformat() if price_dates else None,
            "end": price_dates[-1].isoformat() if price_dates else None,
        },
        "coverage": {
            "price_rows_by_ticker": coverage_by_ticker,
            "missing_news_tickers": missing_news,
            "missing_fundamental_tickers": missing_fundamentals,
        },
        "portfolio": {
            "total_weight": round(total_weight, 6),
            "cash": round(cash, 6),
            "constraints": constraints,
        },
    }
