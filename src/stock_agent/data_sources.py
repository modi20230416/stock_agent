"""Real market-data link with offline-friendly caching.

This module connects the prototype to real, no-API-key market-data vendors
(Yahoo Finance chart JSON first, Stooq daily CSV fallback) while preserving the
project's reproducibility guarantees:

- Every successful download is cached to disk under ``cache_dir``.
- If the network is unavailable, the cached vendor CSV is reused.
- Vendor CSVs are normalized into the internal OHLCV schema used by the
  rest of the system, so downstream agents and backtests are unchanged.

Only the Python standard library is used (``urllib``, ``csv``), consistent
with the rest of the codebase.
"""

from __future__ import annotations

import csv
import io
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from .models import PriceBar

STOOQ_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"
YAHOO_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?range={range}&interval=1d"
)
_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Vendor CSV header variants mapped to the internal field name.
_COLUMN_ALIASES: dict[str, str] = {
    "date": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "adj close": "close",
    "adj_close": "close",
    "volume": "volume",
    "vol": "volume",
}


class DataSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchResult:
    ticker: str
    bars: list[PriceBar]
    source: str  # "network" or "cache"
    rows: int


def _stooq_symbol(ticker: str) -> str:
    """Stooq uses lowercase symbols with a market suffix for US equities."""
    symbol = ticker.strip().lower()
    if "." not in symbol:
        symbol = f"{symbol}.us"
    return symbol


def _cache_path(cache_dir: str | Path, ticker: str) -> Path:
    return Path(cache_dir) / f"{ticker.upper()}.csv"


def _http_get(url: str, timeout: int, ticker: str) -> str:
    request = urllib.request.Request(
        url, headers={"User-Agent": _BROWSER_UA, "Accept": "*/*"}, method="GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as handle:
            return handle.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise DataSourceError(f"Network fetch failed for {ticker}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise DataSourceError(f"Network fetch timed out for {ticker}.") from exc


def _yahoo_json_to_csv(ticker: str, payload: str) -> str:
    """Convert a Yahoo chart JSON payload into canonical OHLCV CSV text."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DataSourceError(f"Yahoo returned non-JSON for {ticker}.") from exc
    chart = (data.get("chart") or {}).get("result") or []
    if not chart:
        raise DataSourceError(f"Yahoo returned no result for {ticker}.")
    result = chart[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    rows = ["Date,Open,High,Low,Close,Volume"]
    for index, ts in enumerate(timestamps):
        try:
            o, h, low_v, c, v = (
                opens[index],
                highs[index],
                lows[index],
                closes[index],
                volumes[index],
            )
        except IndexError:
            continue
        if None in (o, h, low_v, c):
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        rows.append(f"{day},{o},{h},{low_v},{c},{int(v or 0)}")
    if len(rows) <= 1:
        raise DataSourceError(f"Yahoo payload for {ticker} had no usable rows.")
    return "\n".join(rows) + "\n"


def download_vendor_csv(ticker: str, timeout: int = 30, yahoo_range: str = "2y") -> str:
    """Download canonical OHLCV CSV text for a ticker.

    Primary source: Yahoo Finance chart JSON (no API key). Fallback: Stooq CSV.
    Both are normalized to ``Date,Open,High,Low,Close,Volume`` CSV text so the
    on-disk cache format is uniform regardless of provider.
    """
    errors: list[str] = []
    # 1) Yahoo Finance chart JSON.
    try:
        payload = _http_get(
            YAHOO_URL.format(symbol=ticker.upper(), range=yahoo_range), timeout, ticker
        )
        return _yahoo_json_to_csv(ticker, payload)
    except DataSourceError as exc:
        errors.append(f"yahoo: {exc}")

    # 2) Stooq CSV fallback.
    try:
        text = _http_get(STOOQ_URL.format(symbol=_stooq_symbol(ticker)), timeout, ticker)
        if "Date" in text or "date" in text:
            return text
        errors.append(f"stooq: non-CSV response {text[:80]!r}")
    except DataSourceError as exc:
        errors.append(f"stooq: {exc}")

    raise DataSourceError(f"All vendors failed for {ticker}: {'; '.join(errors)}")


def normalize_vendor_csv(
    ticker: str,
    csv_text: str,
    start: date | None = None,
    end: date | None = None,
) -> list[PriceBar]:
    """Convert a vendor daily CSV (Stooq/Yahoo/Kaggle style) to internal PriceBars."""
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    if reader.fieldnames is None:
        raise DataSourceError(f"Vendor CSV for {ticker} has no header.")
    field_map: dict[str, str] = {}
    for raw_name in reader.fieldnames:
        key = raw_name.strip().lower()
        if key in _COLUMN_ALIASES:
            field_map[_COLUMN_ALIASES[key]] = raw_name
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(field_map)
    if missing:
        raise DataSourceError(
            f"Vendor CSV for {ticker} is missing columns: {sorted(missing)}"
        )

    bars: list[PriceBar] = []
    for row in reader:
        raw_date = (row.get(field_map["date"]) or "").strip()
        if not raw_date:
            continue
        try:
            bar_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if start and bar_date < start:
            continue
        if end and bar_date > end:
            continue
        try:
            open_ = float(row[field_map["open"]])
            high = float(row[field_map["high"]])
            low = float(row[field_map["low"]])
            close = float(row[field_map["close"]])
            volume = int(float(row[field_map["volume"]]))
        except (TypeError, ValueError):
            continue
        if min(open_, high, low, close) <= 0:
            continue
        bars.append(
            PriceBar(
                ticker=ticker.upper(),
                date=bar_date,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )
    bars.sort(key=lambda bar: bar.date)
    return bars


def fetch_prices(
    ticker: str,
    cache_dir: str | Path,
    offline: bool = False,
    refresh: bool = False,
    start: date | None = None,
    end: date | None = None,
    timeout: int = 30,
) -> FetchResult:
    """Fetch prices for one ticker with disk caching and offline fallback.

    Resolution order:
    1. If ``refresh`` and not ``offline``: download fresh, write cache.
    2. Else if cache exists: use cache.
    3. Else if not ``offline``: download, write cache.
    4. Else: raise (no cache and offline).
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(cache_dir, ticker)

    if refresh and not offline:
        csv_text = download_vendor_csv(ticker, timeout=timeout)
        cache_file.write_text(csv_text, encoding="utf-8")
        bars = normalize_vendor_csv(ticker, csv_text, start=start, end=end)
        return FetchResult(ticker.upper(), bars, "network", len(bars))

    if cache_file.exists():
        csv_text = cache_file.read_text(encoding="utf-8")
        bars = normalize_vendor_csv(ticker, csv_text, start=start, end=end)
        return FetchResult(ticker.upper(), bars, "cache", len(bars))

    if offline:
        raise DataSourceError(
            f"No cached data for {ticker} in {cache_dir} and offline=True."
        )

    csv_text = download_vendor_csv(ticker, timeout=timeout)
    cache_file.write_text(csv_text, encoding="utf-8")
    bars = normalize_vendor_csv(ticker, csv_text, start=start, end=end)
    return FetchResult(ticker.upper(), bars, "network", len(bars))


def fetch_many(
    tickers: list[str],
    cache_dir: str | Path,
    offline: bool = False,
    refresh: bool = False,
    start: date | None = None,
    end: date | None = None,
    timeout: int = 30,
) -> tuple[list[PriceBar], list[dict]]:
    """Fetch prices for many tickers. Returns (all_bars, per_ticker_report)."""
    all_bars: list[PriceBar] = []
    report: list[dict] = []
    for ticker in tickers:
        try:
            result = fetch_prices(
                ticker,
                cache_dir,
                offline=offline,
                refresh=refresh,
                start=start,
                end=end,
                timeout=timeout,
            )
            all_bars.extend(result.bars)
            report.append(
                {
                    "ticker": result.ticker,
                    "source": result.source,
                    "rows": result.rows,
                    "error": None,
                }
            )
        except DataSourceError as exc:
            report.append(
                {"ticker": ticker.upper(), "source": "none", "rows": 0, "error": str(exc)}
            )
    return all_bars, report


def write_prices_csv(bars: list[PriceBar], path: str | Path) -> int:
    """Write internal PriceBars back to the canonical prices.csv schema."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(bars, key=lambda bar: (bar.ticker, bar.date))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ticker", "date", "open", "high", "low", "close", "volume"])
        for bar in ordered:
            writer.writerow(
                [
                    bar.ticker,
                    bar.date.isoformat(),
                    f"{bar.open:.4f}",
                    f"{bar.high:.4f}",
                    f"{bar.low:.4f}",
                    f"{bar.close:.4f}",
                    bar.volume,
                ]
            )
    return len(ordered)
