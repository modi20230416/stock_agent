"""Build a runnable dataset from real market prices.

This script connects the prototype to real, no-API-key market-data vendors
(Yahoo Finance chart JSON first, Stooq daily CSV fallback) and writes a
normalized ``prices.csv`` into a target data directory (default: ``data/real``).
News, fundamentals and the portfolio file are copied from an existing offline
dataset because real news/fundamentals require paid API keys; this keeps the
project reproducible while the *price* link is genuinely real.

Examples (PowerShell):

    # Fetch fresh real prices and cache them, then build data/real
    .\\.venv\\Scripts\\python.exe scripts\\ingest_real_data.py --refresh

    # Rebuild from cache only, no network (offline reproducible)
    .\\.venv\\Scripts\\python.exe scripts\\ingest_real_data.py --offline
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stock_agent.data_sources import fetch_many, write_prices_csv

DEFAULT_TICKERS = "AAPL,MSFT,NVDA,AMZN,GOOGL,META,JPM,XOM,UNH,TSLA,AMD,WMT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest real market prices into a dataset.")
    parser.add_argument("--tickers", default=DEFAULT_TICKERS)
    parser.add_argument("--out-dir", default=str(ROOT / "data" / "real"))
    parser.add_argument("--cache-dir", default=str(ROOT / "data" / "cache"))
    parser.add_argument(
        "--template-dir",
        default=str(ROOT / "data" / "processed"),
        help="Dataset providing news.csv/fundamentals.csv/portfolio.json.",
    )
    parser.add_argument("--start", default=None, help="ISO date lower bound, e.g. 2024-01-01.")
    parser.add_argument("--end", default=None, help="ISO date upper bound.")
    parser.add_argument("--offline", action="store_true", help="Use cache only, no network.")
    parser.add_argument("--refresh", action="store_true", help="Force fresh download.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tickers = [item.strip().upper() for item in args.tickers.split(",") if item.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = date.fromisoformat(args.start) if args.start else None
    end = date.fromisoformat(args.end) if args.end else None

    bars, report = fetch_many(
        tickers,
        cache_dir=args.cache_dir,
        offline=args.offline,
        refresh=args.refresh,
        start=start,
        end=end,
    )

    print("Per-ticker fetch report:")
    for item in report:
        status = item["error"] or f"{item['rows']} rows ({item['source']})"
        print(f"  {item['ticker']}: {status}")

    if not bars:
        print("ERROR: no price bars were fetched. Try removing --offline or run --refresh online.")
        return 1

    prices_path = out_dir / "prices.csv"
    written = write_prices_csv(bars, prices_path)
    print(f"Wrote {written} price rows to {prices_path}")

    template = Path(args.template_dir)
    for name in ("news.csv", "fundamentals.csv", "portfolio.json"):
        source = template / name
        if source.exists():
            shutil.copyfile(source, out_dir / name)
            print(f"Copied {name} from {template}")
        else:
            print(f"WARNING: template missing {name}; downstream tasks may need it.")

    fetched = sorted({bar.ticker for bar in bars})
    print(f"Real-data dataset ready at {out_dir} ({len(fetched)} tickers: {', '.join(fetched)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
