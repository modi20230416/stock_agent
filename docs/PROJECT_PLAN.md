# 项目工作计划

更新时间：2026-06-10

## 项目目标

本项目构建一个面向日频模拟交易的多 Agent 股票决策支持系统。系统不连接真实券商账户，不进行实盘交易，而是在离线数据和可选 LLM 复核条件下完成：

- 单股分析
- 候选股票筛选
- 小型组合调仓

中期目标是完成 minimal version，证明系统架构可行。当前已经进一步推进到 final project prototype，包含 12 支股票、15 个固定 benchmark cases、baseline 对比、基础回测指标和 Markdown 报告。

## 当前完成情况

已完成：

- Python 项目结构：`src/stock_agent/`
- 数据目录：`data/sample/`、`data/processed/`、`data/benchmark/`
- 运行入口：`scripts/run_demo.py`
- 数据生成脚本：`scripts/generate_final_data.py`
- 单元测试：`tests/test_pipeline.py`
- OpenRouter 可选 LLM 复核
- 三类任务：single、screen、rebalance
- Final benchmark：`--task final`
- 报告输出：`reports/final_benchmark_results.md`

当前验证：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

结果：

- 单元测试 7/7 通过。
- Final benchmark 15/15 cases 通过。
- 股票池 12 支，满足 10-20 支股票要求。

## 任务分解

### 1. 数据与 Benchmark

当前数据使用 deterministic offline dataset，便于课程复现。数据集包含价格、新闻、基本面和组合约束。Benchmark case suite 包含：

- 10 个单股分析 cases
- 2 个股票池筛选 cases
- 3 个组合调仓 cases

后续可选增强是真实数据 adapter，例如 Kaggle/S&P 500 CSV、Alpha Vantage 新闻缓存、SEC company facts 基本面抽取。

### 2. Agent 系统

当前 Agent 包括：

- MarketInformationAgent
- NewsSentimentAgent
- FundamentalAnalysisAgent
- RiskManagementAgent
- DecisionAgent
- LLMDecisionAdvisor

Agent 输出均保留结构化中间结果，避免只给最终结论。

### 3. Baseline 与评估

当前 baseline 包括：

- Technical rule baseline
- No-risk ensemble baseline
- Direct LLM/single-agent baseline

评估指标包括结构完整性、候选区分度、组合约束、风险提示数量，以及 equal-weight backtest 的累计收益、年化收益、最大回撤和 Sharpe ratio。

### 4. 报告与展示

当前优先使用 CLI 和 Markdown 报告展示结果。这样最稳妥、依赖最少，适合课程复现。可选增强是增加 Streamlit 页面。

## 小组协作建议

推荐分工：

- 成员 A：数据来源说明、数据 schema、benchmark cases。
- 成员 B：Agent 设计与 LLM 复核 prompt。
- 成员 C：baseline、backtest、评估结果分析。
- 成员 D：最终报告、README、演示脚本和截图。

推荐 Git 流程：

```powershell
git checkout main
git pull
git checkout -b feature/your-task
```

完成后 push 分支并开 Pull Request。不要提交 `.env`、真实 API key、`.venv` 或大型本地 JSON 报告。

## 后续增强优先级

1. 用真实 OpenRouter key 跑一次 `--task final --llm required`。
2. 增加真实历史价格 CSV loader。
3. 增加新闻 API 缓存格式。
4. 增加 SEC 基本面 adapter。
5. 增加 Streamlit 展示页面。
6. 将 equal-weight 辅助回测扩展为动态策略回测。
