# AI Coding Context

这份文档用于给后续 AI coding 工具或小组成员提供项目上下文，避免只进行零散问答或孤立代码生成。

## 项目目标

构建一个面向日频模拟交易和投资研究的多 Agent 股票决策支持系统。系统输入离线价格、新闻、基本面和组合约束数据，输出：

- 单股 BUY/SELL/HOLD 建议
- 候选股票池排序
- 组合目标权重和交易变化
- Agent 中间解释、风险提示和可选 LLM 复核结果

系统不连接真实券商账户，不做实盘自动交易，不构成投资建议。

## 当前版本状态

当前已经完成 final project prototype：

- 12 支股票离线数据：`data/processed/`
- 15 个 benchmark cases：`data/benchmark/cases.json`
- CLI 入口：`scripts/run_demo.py`
- 数据生成脚本：`scripts/generate_final_data.py`
- 核心代码：`src/stock_agent/`
- 测试：`tests/test_pipeline.py`
- final benchmark 摘要：`reports/final_benchmark_results.md`

验证结果：

- 单元测试：6/6 通过
- Final benchmark：15/15 cases 通过

## 快速复现

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

如果要启用真实 OpenRouter 调用：

```powershell
$env:OPENROUTER_API_KEY="..."
$env:OPENROUTER_MODEL="openrouter/free"
.\.venv\Scripts\python.exe scripts\run_demo.py --task final --llm required
```

## 核心文件

- `src/stock_agent/models.py`
  - `PriceBar`
  - `NewsItem`
  - `FundamentalRecord`
  - `AgentResult`
  - `Decision`
  - `PortfolioRecommendation`
  - `BenchmarkCase`

- `src/stock_agent/data_loader.py`
  - 读取 prices/news/fundamentals/portfolio
  - 读取 benchmark case suite

- `src/stock_agent/agents.py`
  - `MarketInformationAgent`
  - `NewsSentimentAgent`
  - `FundamentalAnalysisAgent`
  - `RiskManagementAgent`
  - `DecisionAgent`
  - `LLMDecisionAdvisor`

- `src/stock_agent/pipeline.py`
  - `StockDecisionSystem`
  - 单股分析、筛选、调仓、benchmark、final benchmark cases

- `src/stock_agent/baselines.py`
  - `TechnicalRuleBaseline`
  - `NoRiskEnsembleBaseline`
  - `DirectLLMBaseline`

- `src/stock_agent/backtest.py`
  - `equal_weight_backtest`

- `src/stock_agent/llm.py`
  - OpenRouter API client
  - JSON extraction and fallback error handling

- `src/stock_agent/evaluator.py`
  - JSON report writer
  - Markdown benchmark report renderer

## Agent 分工

### MarketInformationAgent

使用日频 OHLCV 数据，输出 MA5、MA20、20 日收益、短期 momentum、波动率、成交量变化和 drawdown。市场信号只基于 `as_of` 及之前的数据。

### NewsSentimentAgent

读取离线新闻 headline/summary/sentiment/event_type。输出平均情绪、最新新闻、事件类型集合和负面事件风险。

### FundamentalAnalysisAgent

使用 revenue growth、EPS growth、net margin、debt-to-equity、free cash flow positive 等字段，输出基本面 score、证据和缺失/弱项提示。

### RiskManagementAgent

检查：

- 最大单股权重
- 最大单次交易变化
- 最低现金比例
- 波动率上限

调仓时负责修正目标权重，保证组合约束不被破坏。

### DecisionAgent

融合市场、新闻和基本面 Agent 结果，再经过风控 Agent。当前版本显式检测跨 Agent 冲突，例如市场强但新闻/基本面弱时降低 confidence 并加入风险提示。

### LLMDecisionAdvisor

可选调用 OpenRouter。它读取结构化 Agent 输出，要求模型返回 JSON，字段包括 action、score_adjustment、confidence_adjustment、rationale、risk_warnings、uncertainty。没有 key 或调用失败时，`auto` 模式会 fallback。

## Benchmark 设计

Final case suite 位于 `data/benchmark/cases.json`：

- 10 个 single-stock cases
- 2 个 screening cases
- 3 个 rebalance cases

通过标准包括：

- 单股结果必须有 action、rationale、risk warnings 和四类 agent 结果。
- Screening 必须返回完整排序，并且 score 或 action 能区分候选股票。
- Rebalance 必须满足组合约束。
- 股票池必须在 10-20 支范围内。
- Baseline 和 backtest 必须可运行。

## 扩展注意事项

- 不要把真实 API key 写入代码、`.env` 或文档。
- 不要把 API 调用直接塞进 Agent 内部；新增真实数据源时优先写 loader/adapter，并保留离线缓存。
- LLM 输出必须解析为结构化 JSON，失败时要 fallback。
- 新增任务或数据字段时，同步更新 tests 和 benchmark cases。
- 保持无第三方运行依赖，除非确实需要；如果增加依赖，要更新 `pyproject.toml` 和 `requirements.txt`。
- 报告 JSON 可以本地生成但默认不提交；Markdown 摘要可以提交，方便老师和组员阅读。

## 推荐下一步

如果继续增强，优先级如下：

1. 用真实 OpenRouter key 跑一次 `--task final --llm required`。
2. 增加真实 CSV loader，例如 Kaggle/S&P 500 历史价格数据。
3. 设计新闻 API 缓存格式，再接 Alpha Vantage 或 Finnhub。
4. 增加 Streamlit 展示页。
5. 把 equal-weight 辅助回测升级为动态策略回测。
