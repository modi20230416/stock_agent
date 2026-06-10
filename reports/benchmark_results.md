# Stock Agent Benchmark

- As of: 2026-05-22
- Tickers: AAPL, MSFT, NVDA, AMZN, GOOGL, META, JPM, XOM, UNH, TSLA, AMD, WMT
- LLM mode: off
- LLM model: openrouter/free
- LLM used count: 0

## Success Criteria
- PASS: single stock has action reason and risk
- PASS: screening distinguishes candidates
- PASS: rebalance respects constraints
- PASS: uncertainty is explicit

## Baseline Comparison

| System | Actions | Action diversity | Risk warnings | Constraint violations |
| --- | --- | ---: | ---: | --- |
| Multi-agent + risk | {'AAPL': 'HOLD', 'MSFT': 'BUY', 'NVDA': 'BUY', 'AMZN': 'BUY', 'GOOGL': 'HOLD', 'META': 'BUY', 'JPM': 'HOLD', 'XOM': 'HOLD', 'UNH': 'HOLD', 'TSLA': 'SELL', 'AMD': 'HOLD', 'WMT': 'BUY'} | 3 | 16 | [] |
| Technical rule | {'AAPL': 'HOLD', 'MSFT': 'HOLD', 'NVDA': 'BUY', 'AMZN': 'HOLD', 'GOOGL': 'HOLD', 'META': 'HOLD', 'JPM': 'HOLD', 'XOM': 'HOLD', 'UNH': 'HOLD', 'TSLA': 'HOLD', 'AMD': 'HOLD', 'WMT': 'HOLD'} | 2 | 0 | N/A |
| No-risk ensemble | {'AAPL': 'HOLD', 'MSFT': 'BUY', 'NVDA': 'BUY', 'AMZN': 'BUY', 'GOOGL': 'HOLD', 'META': 'BUY', 'JPM': 'HOLD', 'XOM': 'HOLD', 'UNH': 'HOLD', 'TSLA': 'SELL', 'AMD': 'HOLD', 'WMT': 'BUY'} | 3 | 0 | N/A |
| Direct LLM/single-agent | {'AAPL': 'HOLD', 'MSFT': 'BUY', 'NVDA': 'BUY', 'AMZN': 'BUY', 'GOOGL': 'HOLD', 'META': 'BUY', 'JPM': 'HOLD', 'XOM': 'HOLD', 'UNH': 'HOLD', 'TSLA': 'SELL', 'AMD': 'HOLD', 'WMT': 'BUY'} | 3 | N/A | N/A |

## Equal-Weight Backtest

| Metric | Value |
| --- | ---: |
| Observations | 59 |
| Cumulative return | 4.77% |
| Annualized return | 22.03% |
| Max drawdown | -1.37% |
| Sharpe ratio | 2.44 |

## Rebalance Target

| Asset | Target weight | Trade |
| --- | ---: | ---: |
| AAPL | 7.55% | -4.45% |
| AMD | 2.98% | -4.02% |
| AMZN | 10.71% | +2.71% |
| CASH | 8.00% | -4.00% |
| GOOGL | 8.43% | +1.43% |
| JPM | 8.09% | +0.09% |
| META | 11.92% | +4.92% |
| MSFT | 12.20% | +0.20% |
| NVDA | 12.86% | +5.86% |
| TSLA | 0.99% | -8.01% |
| UNH | 2.35% | -4.65% |
| WMT | 10.16% | +4.16% |
| XOM | 3.77% | -4.23% |

## Rebalance Warnings
- TSLA trade was limited to 8.0%.
- Positions were reduced to restore the minimum cash buffer.
