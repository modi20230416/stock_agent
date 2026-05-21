from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from .models import FundamentalRecord, NewsItem, PriceBar


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


def load_sample_dataset(data_dir: str | Path) -> tuple[list[PriceBar], list[NewsItem], list[FundamentalRecord], dict]:
    root = Path(data_dir)
    return (
        load_prices(root / "prices.csv"),
        load_news(root / "news.csv"),
        load_fundamentals(root / "fundamentals.csv"),
        load_portfolio(root / "portfolio.json"),
    )
