# Stock Agent Benchmark

- As of: 2026-05-22
- Tickers: AAPL, MSFT, NVDA, AMZN, GOOGL, META, JPM, XOM, UNH, TSLA, AMD, WMT
- LLM mode: off
- LLM model: openai/gpt-oss-20b:free
- LLM used count: 0

## Success Criteria
- PASS: dataset schema valid
- PASS: single stock has action reason and risk
- PASS: screening distinguishes candidates
- PASS: rebalance respects constraints
- PASS: uncertainty is explicit

## Data Validation

- Valid: True
- Tickers: 12
- Price dates: 60
- Warnings: 0

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

## Decision-Weighted Strategy Backtest

| Metric | Value |
| --- | ---: |
| Observations | 59 |
| Rebalances | 12 |
| Average turnover | 14.25% |
| Average cash | 8.00% |
| Cost per turn | 0.1000% |
| Impact coefficient | 0.0500 |
| Base cost | 0.1710% |
| Slippage/impact | 0.0075% |
| Total transaction cost | 0.1786% |
| Gross cumulative return | 8.65% |
| Net cumulative return | 8.46% |
| Max drawdown | -1.18% |
| Sharpe ratio | 4.73 |

## Portfolio Stress Test

| Scenario | Portfolio return | Worst contributors |
| --- | ---: | --- |
| broad_market_selloff | -7.36% | NVDA -1.04%, MSFT -0.99%, META -0.96% |
| tech_ai_drawdown | -7.46% | NVDA -1.82%, MSFT -1.11%, META -1.08% |
| rates_credit_tightening | -4.57% | NVDA -0.91%, JPM -0.74%, MSFT -0.49% |
| energy_price_spike | -1.76% | NVDA -0.33%, MSFT -0.31%, META -0.30% |
| defensive_rotation | -2.13% | NVDA -0.46%, MSFT -0.43%, META -0.42% |

## Rebalance Target

| Asset | Target weight | Trade |
| --- | ---: | ---: |
| AAPL | 7.63% | -4.37% |
| AMD | 3.01% | -2.99% |
| AMZN | 10.82% | +3.82% |
| CASH | 8.00% | -4.00% |
| GOOGL | 8.53% | +2.53% |
| JPM | 8.17% | +1.17% |
| META | 12.05% | +6.05% |
| MSFT | 12.33% | +0.33% |
| NVDA | 13.00% | +7.00% |
| TSLA | 0.00% | -8.00% |
| UNH | 2.37% | -3.63% |
| WMT | 10.27% | +5.27% |
| XOM | 3.81% | -3.19% |

## Rebalance Warnings
- Positions were reduced to restore the minimum cash buffer.
