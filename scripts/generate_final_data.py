from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
BENCHMARK = ROOT / "data" / "benchmark"


TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "JPM",
    "XOM",
    "UNH",
    "TSLA",
    "AMD",
    "WMT",
]


PROFILES = {
    "AAPL": {"start": 184.0, "drift": 0.0012, "wave": 0.004, "volume": 58_000_000},
    "MSFT": {"start": 420.0, "drift": 0.0015, "wave": 0.003, "volume": 28_000_000},
    "NVDA": {"start": 920.0, "drift": 0.0032, "wave": 0.011, "volume": 55_000_000},
    "AMZN": {"start": 178.0, "drift": 0.0016, "wave": 0.006, "volume": 44_000_000},
    "GOOGL": {"start": 168.0, "drift": 0.0005, "wave": 0.005, "volume": 31_000_000},
    "META": {"start": 470.0, "drift": 0.0021, "wave": 0.006, "volume": 22_000_000},
    "JPM": {"start": 205.0, "drift": 0.0007, "wave": 0.004, "volume": 13_000_000},
    "XOM": {"start": 114.0, "drift": -0.0002, "wave": 0.006, "volume": 18_000_000},
    "UNH": {"start": 520.0, "drift": -0.0008, "wave": 0.005, "volume": 4_800_000},
    "TSLA": {"start": 250.0, "drift": -0.0021, "wave": 0.014, "volume": 125_000_000},
    "AMD": {"start": 175.0, "drift": -0.0009, "wave": 0.015, "volume": 68_000_000},
    "WMT": {"start": 66.0, "drift": 0.0010, "wave": 0.003, "volume": 21_000_000},
}


FUNDAMENTALS = [
    ["AAPL", "2026Q1", 0.04, 0.25, 0.08, 1.20, True],
    ["MSFT", "2026Q1", 0.16, 0.36, 0.18, 0.45, True],
    ["NVDA", "2026Q1", 0.78, 0.49, 1.10, 0.25, True],
    ["AMZN", "2026Q1", 0.13, 0.11, 0.20, 0.72, True],
    ["GOOGL", "2026Q1", 0.08, 0.24, 0.07, 0.12, True],
    ["META", "2026Q1", 0.21, 0.34, 0.26, 0.18, True],
    ["JPM", "2026Q1", 0.05, 0.29, 0.06, 0.88, True],
    ["XOM", "2026Q1", -0.03, 0.12, -0.09, 0.38, True],
    ["UNH", "2026Q1", 0.02, 0.06, -0.04, 0.76, True],
    ["TSLA", "2026Q1", -0.06, 0.08, -0.22, 0.85, False],
    ["AMD", "2026Q1", 0.09, 0.07, -0.05, 0.55, False],
    ["WMT", "2026Q1", 0.06, 0.04, 0.11, 0.62, True],
]


NEWS = {
    "AAPL": [
        ("2026-04-07", "Apple suppliers report stable demand", "Channel checks suggest modestly improving device component orders.", 0.25, "demand"),
        ("2026-04-24", "Services revenue outlook improves", "Analysts raise estimates for recurring services revenue.", 0.45, "estimate_revision"),
        ("2026-05-15", "Regulatory review weighs on app store policy", "Potential policy changes may pressure service margins.", -0.35, "regulatory"),
    ],
    "MSFT": [
        ("2026-04-08", "Azure demand remains resilient", "Enterprise cloud spending continues to support growth.", 0.55, "demand"),
        ("2026-05-01", "AI infrastructure spending increases", "Capex is high but management frames it as demand-backed expansion.", 0.20, "capex"),
        ("2026-05-19", "Security product bundle gains customers", "New enterprise contracts add recurring revenue visibility.", 0.40, "contract"),
    ],
    "NVDA": [
        ("2026-04-10", "Data center demand remains strong", "Hyperscale customers continue ordering AI accelerators.", 0.70, "demand"),
        ("2026-05-03", "Export control discussion creates uncertainty", "Potential restrictions could affect selected international sales.", -0.30, "regulatory"),
        ("2026-05-20", "Analysts lift AI chip revenue estimates", "Consensus estimates rise after channel checks.", 0.65, "estimate_revision"),
    ],
    "AMZN": [
        ("2026-04-09", "Cloud margins improve", "AWS efficiency initiatives support operating margin.", 0.42, "margin"),
        ("2026-05-05", "Retail fulfillment costs ease", "Lower logistics pressure improves profitability outlook.", 0.35, "cost"),
        ("2026-05-18", "Antitrust review remains an overhang", "Regulatory scrutiny could limit aggressive bundling.", -0.25, "regulatory"),
    ],
    "GOOGL": [
        ("2026-04-11", "Search ad growth is steady", "Core advertising demand remains stable.", 0.20, "demand"),
        ("2026-05-02", "AI product rollout receives mixed feedback", "User adoption is promising but monetization timing is unclear.", 0.05, "product"),
        ("2026-05-17", "Cloud contract pipeline improves", "Enterprise cloud wins support medium-term growth.", 0.30, "contract"),
    ],
    "META": [
        ("2026-04-12", "Advertising engagement improves", "Reels and AI targeting lift ad conversion metrics.", 0.55, "demand"),
        ("2026-05-06", "Reality Labs spending remains high", "Long-horizon investment continues to weigh on expenses.", -0.20, "capex"),
        ("2026-05-21", "Analysts raise operating margin forecast", "Cost control and ad demand improve consensus estimates.", 0.50, "estimate_revision"),
    ],
    "JPM": [
        ("2026-04-15", "Loan growth stays moderate", "Corporate loan demand is stable but not accelerating.", 0.10, "credit"),
        ("2026-05-08", "Credit card delinquencies edge higher", "Consumer credit normalization raises monitoring needs.", -0.30, "credit"),
        ("2026-05-16", "Net interest income guidance unchanged", "Management keeps annual outlook broadly intact.", 0.15, "guidance"),
    ],
    "XOM": [
        ("2026-04-16", "Crude prices soften", "Energy prices decline after inventory data.", -0.30, "commodity"),
        ("2026-05-09", "Refining margins stabilize", "Downstream margins recover from recent weakness.", 0.20, "margin"),
        ("2026-05-20", "Capital return plan remains steady", "Buybacks and dividends remain a support factor.", 0.25, "capital_return"),
    ],
    "UNH": [
        ("2026-04-17", "Medical cost trend pressure continues", "Utilization remains above prior expectations.", -0.45, "cost"),
        ("2026-05-07", "Regulatory review adds uncertainty", "Managed care reimbursement rules face scrutiny.", -0.50, "regulatory"),
        ("2026-05-22", "Membership growth is slower", "Management cites slower enrollment in selected plans.", -0.35, "guidance"),
    ],
    "TSLA": [
        ("2026-04-18", "Price cuts expand in key markets", "Lower prices may pressure automotive gross margin.", -0.55, "pricing"),
        ("2026-05-10", "Recall notice affects selected vehicles", "Software-related recall creates near-term headline risk.", -0.45, "product"),
        ("2026-05-19", "Delivery estimates revised lower", "Analysts cite demand uncertainty and rising competition.", -0.60, "estimate_revision"),
    ],
    "AMD": [
        ("2026-04-19", "AI accelerator roadmap gets attention", "New products could improve positioning later in the year.", 0.35, "product"),
        ("2026-05-12", "PC demand recovery is uneven", "Client segment demand remains mixed across channels.", -0.15, "demand"),
        ("2026-05-20", "Margin guidance disappoints", "Investors focus on lower-than-expected near-term gross margin.", -0.45, "guidance"),
    ],
    "WMT": [
        ("2026-04-20", "Grocery traffic remains resilient", "Consumer staples demand supports comparable sales.", 0.35, "demand"),
        ("2026-05-11", "E-commerce unit improves contribution margin", "Fulfillment efficiency offsets delivery investments.", 0.30, "margin"),
        ("2026-05-21", "Consumer trade-down trend supports sales", "Value positioning remains a defensive support.", 0.25, "macro"),
    ],
}


def business_days(start: date, count: int) -> list[date]:
    days: list[date] = []
    current = start
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def deterministic_return(index: int, drift: float, wave: float) -> float:
    pattern = ((index * 7) % 11 - 5) / 5
    shock = 0.0
    if index in {14, 31, 48}:
        shock = wave * 1.5
    if index in {22, 39, 55}:
        shock = -wave * 1.2
    return drift + wave * pattern + shock


def write_prices() -> None:
    dates = business_days(date(2026, 3, 2), 60)
    path = PROCESSED / "prices.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ticker", "date", "open", "high", "low", "close", "volume"])
        for ticker in TICKERS:
            profile = PROFILES[ticker]
            close = float(profile["start"])
            for index, day in enumerate(dates):
                ret = deterministic_return(index, float(profile["drift"]), float(profile["wave"]))
                open_price = close * (1 + ret * 0.35)
                close = close * (1 + ret)
                spread = 0.006 + abs(ret) * 0.5
                high = max(open_price, close) * (1 + spread)
                low = min(open_price, close) * (1 - spread)
                volume = int(profile["volume"] * (1 + (((index * 5) % 9) - 4) * 0.025))
                writer.writerow(
                    [
                        ticker,
                        day.isoformat(),
                        f"{open_price:.2f}",
                        f"{high:.2f}",
                        f"{low:.2f}",
                        f"{close:.2f}",
                        volume,
                    ]
                )


def write_news() -> None:
    path = PROCESSED / "news.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ticker", "date", "headline", "summary", "sentiment", "event_type"])
        for ticker, items in NEWS.items():
            for item in items:
                writer.writerow([ticker, *item])


def write_fundamentals() -> None:
    path = PROCESSED / "fundamentals.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "ticker",
                "period",
                "revenue_growth",
                "net_margin",
                "eps_growth",
                "debt_to_equity",
                "free_cash_flow_positive",
            ]
        )
        writer.writerows(FUNDAMENTALS)


def write_portfolio() -> None:
    payload = {
        "cash": 0.12,
        "positions": {
            "AAPL": 0.12,
            "MSFT": 0.12,
            "NVDA": 0.07,
            "AMZN": 0.08,
            "GOOGL": 0.07,
            "META": 0.07,
            "JPM": 0.08,
            "XOM": 0.08,
            "UNH": 0.07,
            "TSLA": 0.09,
            "AMD": 0.07,
            "WMT": 0.06,
        },
        "constraints": {
            "max_position_weight": 0.18,
            "max_trade_weight": 0.08,
            "min_cash_weight": 0.08,
            "volatility_limit": 0.025,
            "max_drawdown_warning": 0.08,
            "min_confidence": 0.35,
        },
    }
    (PROCESSED / "portfolio.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_cases() -> None:
    payload = {
        "as_of": "2026-05-22",
        "default_pool": TICKERS,
        "single_cases": [
            {"id": "positive_ai_infrastructure", "ticker": "NVDA", "as_of": "2026-05-22", "expected_focus": "strong market, news, and fundamentals"},
            {"id": "negative_auto_demand", "ticker": "TSLA", "as_of": "2026-05-22", "expected_focus": "weak market, negative news, weak fundamentals"},
            {"id": "defensive_retail", "ticker": "WMT", "as_of": "2026-05-22", "expected_focus": "defensive steady profile"},
            {"id": "regulatory_healthcare", "ticker": "UNH", "as_of": "2026-05-22", "expected_focus": "negative regulatory and margin pressure"},
            {"id": "mixed_search_cloud", "ticker": "GOOGL", "as_of": "2026-05-22", "expected_focus": "mixed but stable profile"},
            {"id": "chip_margin_conflict", "ticker": "AMD", "as_of": "2026-05-22", "expected_focus": "conflicting product optimism and margin pressure"},
            {"id": "financial_credit_watch", "ticker": "JPM", "as_of": "2026-05-22", "expected_focus": "credit risk monitoring"},
            {"id": "energy_commodity_mixed", "ticker": "XOM", "as_of": "2026-05-22", "expected_focus": "commodity weakness with capital return support"},
            {"id": "mega_cap_services", "ticker": "AAPL", "as_of": "2026-05-22", "expected_focus": "positive technicals with regulatory overhang"},
            {"id": "cloud_quality", "ticker": "MSFT", "as_of": "2026-05-22", "expected_focus": "quality growth and cloud strength"},
        ],
        "screen_cases": [
            {
                "id": "mega_cap_pool",
                "as_of": "2026-05-22",
                "tickers": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"],
            },
            {
                "id": "cross_sector_pool",
                "as_of": "2026-05-22",
                "tickers": TICKERS,
            },
        ],
        "rebalance_cases": [
            {
                "id": "balanced_existing_portfolio",
                "as_of": "2026-05-22",
                "tickers": TICKERS,
                "portfolio": "portfolio.json",
            },
            {
                "id": "overweight_high_risk",
                "as_of": "2026-05-22",
                "tickers": ["TSLA", "AMD", "NVDA", "MSFT", "WMT", "UNH"],
                "portfolio": {
                    "cash": 0.05,
                    "positions": {"TSLA": 0.28, "AMD": 0.20, "NVDA": 0.15, "MSFT": 0.12, "WMT": 0.10, "UNH": 0.10},
                    "constraints": {
                        "max_position_weight": 0.22,
                        "max_trade_weight": 0.10,
                        "min_cash_weight": 0.10,
                        "volatility_limit": 0.025,
                    },
                },
            },
            {
                "id": "cash_defensive_rotation",
                "as_of": "2026-05-22",
                "tickers": ["AAPL", "MSFT", "JPM", "XOM", "UNH", "WMT"],
                "portfolio": {
                    "cash": 0.25,
                    "positions": {"AAPL": 0.12, "MSFT": 0.10, "JPM": 0.14, "XOM": 0.16, "UNH": 0.13, "WMT": 0.10},
                    "constraints": {
                        "max_position_weight": 0.20,
                        "max_trade_weight": 0.08,
                        "min_cash_weight": 0.12,
                        "volatility_limit": 0.022,
                    },
                },
            },
        ],
    }
    (BENCHMARK / "cases.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_readmes() -> None:
    (PROCESSED / "README.md").write_text(
        "# Processed Offline Dataset\n\n"
        "Deterministic course-project demo dataset with 12 large-cap tickers, "
        "60 business days of daily OHLCV data, sample news/events, fundamentals, "
        "and a portfolio configuration. Replace these files with Kaggle, "
        "Alpha Vantage, and SEC-derived cached files when real data is available.\n",
        encoding="utf-8",
    )
    (BENCHMARK / "README.md").write_text(
        "# Benchmark Cases\n\n"
        "`cases.json` defines fixed single-stock, screening, and rebalance cases "
        "used by the final-version benchmark runner.\n",
        encoding="utf-8",
    )


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    BENCHMARK.mkdir(parents=True, exist_ok=True)
    write_prices()
    write_news()
    write_fundamentals()
    write_portfolio()
    write_cases()
    write_readmes()
    print(f"Wrote processed data to {PROCESSED}")
    print(f"Wrote benchmark cases to {BENCHMARK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
