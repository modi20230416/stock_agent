from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stock_agent.data_sources import (
    DataSourceError,
    fetch_prices,
    normalize_vendor_csv,
    write_prices_csv,
)

# Vendor CSV in Stooq/Yahoo style, including an Adj Close alias column.
STOOQ_CSV = """Date,Open,High,Low,Close,Volume
2026-03-02,183.82,185.18,182.13,183.48,52200000
2026-03-03,183.66,185.36,182.31,184.00,59449999
2026-03-04,184.10,186.00,183.50,185.20,48000000
"""

YAHOO_CSV = """Date,Open,High,Low,Close,Adj Close,Volume
2026-03-02,100.0,101.0,99.0,100.5,100.5,1000000
2026-03-03,100.5,102.0,100.0,101.5,101.5,1200000
"""


class DataSourceTest(unittest.TestCase):
    def test_normalize_stooq_csv(self) -> None:
        bars = normalize_vendor_csv("AAPL", STOOQ_CSV)
        self.assertEqual(len(bars), 3)
        self.assertEqual(bars[0].ticker, "AAPL")
        self.assertEqual(bars[0].date, date(2026, 3, 2))
        self.assertAlmostEqual(bars[0].close, 183.48)
        # Bars are sorted ascending by date.
        self.assertTrue(all(a.date <= b.date for a, b in zip(bars, bars[1:])))

    def test_normalize_yahoo_adj_close_alias(self) -> None:
        bars = normalize_vendor_csv("TEST", YAHOO_CSV)
        self.assertEqual(len(bars), 2)
        # Adj Close should map to close.
        self.assertAlmostEqual(bars[0].close, 100.5)

    def test_normalize_applies_date_window(self) -> None:
        bars = normalize_vendor_csv(
            "AAPL", STOOQ_CSV, start=date(2026, 3, 3), end=date(2026, 3, 3)
        )
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0].date, date(2026, 3, 3))

    def test_missing_columns_raise(self) -> None:
        with self.assertRaises(DataSourceError):
            normalize_vendor_csv("BAD", "Date,Open,Close\n2026-03-02,1,2\n")

    def test_cache_fallback_offline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            (cache_dir / "AAPL.csv").write_text(STOOQ_CSV, encoding="utf-8")
            result = fetch_prices("AAPL", cache_dir, offline=True)
            self.assertEqual(result.source, "cache")
            self.assertEqual(result.rows, 3)
            self.assertEqual(result.bars[0].ticker, "AAPL")

    def test_offline_without_cache_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DataSourceError):
                fetch_prices("NOPE", tmp, offline=True)

    def test_roundtrip_write_prices_csv(self) -> None:
        bars = normalize_vendor_csv("AAPL", STOOQ_CSV)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "prices.csv"
            count = write_prices_csv(bars, out)
            self.assertEqual(count, 3)
            text = out.read_text(encoding="utf-8")
            self.assertIn("ticker,date,open,high,low,close,volume", text)
            self.assertIn("AAPL,2026-03-02", text)


if __name__ == "__main__":
    unittest.main()
