# Final Version Benchmark

- As of: 2026-05-22
- Stock universe: AAPL, MSFT, NVDA, AMZN, GOOGL, META, JPM, XOM, UNH, TSLA, AMD, WMT
- Cases: 15 total (10 single, 2 screen, 3 rebalance)
- Pass rate: 15/15 (100.00%)

## Final Criteria
- PASS: case suite has 10 to 20 stocks
- PASS: dataset schema valid
- PASS: all cases pass
- PASS: multi agent beats minimal surface
- PASS: backtest available
- PASS: dynamic strategy backtest available
- PASS: stress test available

## Case Results

| Case | Task | Result | Key output |
| --- | --- | --- | --- |
| positive_ai_infrastructure | single | PASS | NVDA BUY score=1.305; focus=market |
| negative_auto_demand | single | PASS | TSLA SELL score=-0.7542; focus=market, negative |
| defensive_retail | single | PASS | WMT BUY score=0.82; focus=evidence reviewed |
| regulatory_healthcare | single | PASS | UNH HOLD score=-0.3792; focus=regulatory, margin |
| mixed_search_cloud | single | PASS | GOOGL HOLD score=0.7117; focus=evidence reviewed |
| chip_margin_conflict | single | PASS | AMD HOLD score=-0.2667; focus=product, margin |
| financial_credit_watch | single | PASS | JPM HOLD score=0.6492; focus=credit |
| energy_commodity_mixed | single | PASS | XOM HOLD score=-0.125; focus=commodity, capital, return |
| mega_cap_services | single | PASS | AAPL HOLD score=0.5533; focus=regulatory |
| cloud_quality | single | PASS | MSFT BUY score=1.1867; focus=growth |
| mega_cap_pool | screen | PASS | top=NVDA score=1.305 |
| cross_sector_pool | screen | PASS | top=NVDA score=1.305 |
| balanced_existing_portfolio | rebalance | PASS | cash=8.00%, warnings=1 |
| overweight_high_risk | rebalance | PASS | cash=10.00%, warnings=7 |
| cash_defensive_rotation | rebalance | PASS | cash=19.80%, warnings=6 |

## Baseline And Backtest

- Multi-agent risk warnings: 16
- Technical baseline action diversity: 2
- No-risk baseline action diversity: 3
- Direct LLM baseline used LLM count: 0
- Equal-weight cumulative return: 4.77%
- Equal-weight max drawdown: -1.37%
- Decision-weighted net cumulative return: 8.46%
- Decision-weighted gross cumulative return: 8.65%
- Decision-weighted total transaction cost: 0.1786%
- Decision-weighted base cost: 0.1710%
- Decision-weighted slippage/impact: 0.0075%
- Decision-weighted max drawdown: -1.18%
- Decision-weighted rebalances: 12
- Worst stress scenario: tech_ai_drawdown (-7.46%)
- Data validation: PASS (12 tickers)
