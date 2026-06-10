# 最终报告草稿

## 1. 项目概述

本项目实现了一个面向日频模拟交易的多 Agent 股票决策支持系统。系统不连接真实券商账户，不进行实盘交易，而是在离线可复现数据集上完成单股分析、候选股票筛选和小型组合调仓三类任务。系统输出 BUY/SELL/HOLD 或组合权重建议，同时保留市场、新闻、基本面、风险管理和可选 LLM 复核的中间结果。

项目目标不是证明某个交易策略一定盈利，而是验证 proposal 中提出的多 Agent 决策框架是否能够在小型股票池上稳定运行、可解释、可评估、可扩展。

## 2. 系统架构

系统分为五层：

1. 数据层：读取价格、新闻、基本面、组合约束和 benchmark cases。
2. Agent 层：分别负责市场信息、新闻情绪、基本面分析、风险管理和最终决策。
3. LLM 复核层：可选调用 OpenRouter，对结构化 Agent 输出进行保守复核。
4. 评估层：运行 fixed benchmark cases、baseline 对比和 equal-weight backtest。
5. 报告层：输出 JSON 详情和 Markdown 摘要。

核心入口是 `StockDecisionSystem`。它组合多个 Agent，并提供 `analyze_single`、`screen_candidates`、`rebalance`、`benchmark` 和 `benchmark_cases` 五类接口。

## 3. 数据与任务集

当前 final prototype 使用 deterministic offline dataset，位于 `data/processed/`。数据集包含 12 支股票：

```text
AAPL, MSFT, NVDA, AMZN, GOOGL, META, JPM, XOM, UNH, TSLA, AMD, WMT
```

每支股票包含 60 个交易日的 OHLCV 数据、3 条新闻事件和 1 条基本面记录。新闻数据包含 `event_type` 字段，用于表达 demand、regulatory、margin、guidance 等事件类型。

Benchmark case suite 位于 `data/benchmark/cases.json`，共 15 个 cases：

- 10 个单股分析 cases
- 2 个候选股票筛选 cases
- 3 个组合调仓 cases

这些 cases 覆盖正向成长、负向需求、监管压力、产品与利润率冲突、信用风险、能源价格波动、防御型消费等场景。

## 4. Agent 设计

### 市场信息 Agent

市场 Agent 使用日频 OHLCV 数据计算 MA5、MA20、20 日收益、短期 momentum、波动率、成交量变化和 drawdown，并输出市场侧 score、confidence、summary 和 evidence。

### 新闻情绪 Agent

新闻 Agent 聚合离线新闻的 sentiment 和 event_type，输出平均情绪、最新新闻、事件类型集合和负面事件风险提示。

### 基本面 Agent

基本面 Agent 根据收入增长、EPS 增长、净利率、债务权益比和自由现金流状态评估公司基本面。如果数据偏弱或缺失，会加入风险提示。

### 风险管理 Agent

风险 Agent 检查最大持仓比例、最大单次交易变化、最低现金比例和波动率上限。在调仓任务中，它会修正目标权重，保证组合不违反约束。

### 决策 Agent

决策 Agent 对市场、新闻和基本面信号进行加权融合，然后经过风险修正。当前版本还会显式检测跨 Agent 冲突，例如技术面偏强但新闻和基本面偏弱时，系统会降低信心并在风险提示中说明冲突来源。

### LLM 复核 Agent

LLM 复核 Agent 使用 OpenRouter API。它只读取结构化 Agent 输出，并要求模型返回 JSON。没有 API key 时，系统可以完全离线运行；设置 `OPENROUTER_API_KEY` 后，可以用 `--llm required` 强制验证真实 LLM 调用。

## 5. Baseline 与评估

当前实现了三个 baseline：

- Technical rule baseline：只使用价格和移动均线。
- No-risk ensemble baseline：使用市场、新闻和基本面信号，但跳过风险管理。
- Direct LLM/single-agent baseline：把结构化输入直接交给单一 LLM 或 deterministic fallback。

Final benchmark 的成功标准包括：

- 单股分析必须有 action、rationale、risk warnings 和四类 Agent 中间结果。
- Screening 必须返回完整排序并区分候选股票。
- Rebalance 必须满足组合约束。
- 股票池规模必须在 10-20 支范围内。
- Baseline 和 backtest 必须可运行。

## 6. 实验结果

运行命令：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

当前结果：

- 单元测试：6/6 通过。
- Final benchmark：15/15 cases 通过。
- Final criteria：全部通过。
- 股票池规模：12 支。
- Multi-agent risk warnings：16。
- Equal-weight cumulative return：4.77%。
- Equal-weight max drawdown：-1.37%。

详细摘要见 `reports/final_benchmark_results.md`。

## 7. 项目贡献

相比中期 minimal version，最终版本的主要推进包括：

- 从 4 支股票扩展到 12 支股票。
- 从单次 demo 扩展到 15 个固定 benchmark cases。
- 增加新闻事件类型、市场回撤、跨 Agent 冲突检测。
- 增加 direct LLM baseline 和 equal-weight backtest。
- 增加 final benchmark runner 和 Markdown 报告。
- 增加 final case suite 单元测试。
- 更新 README 和 AI 协作上下文，支持多人继续开发。

## 8. 局限性

当前数据集是离线 deterministic dataset，而非实时市场数据。这样做的优点是便于课程复现，缺点是无法代表真实市场分布。系统输出主要用于模拟研究，不应被解释为真实投资建议。当前 backtest 也是辅助性 equal-weight 指标，尚未实现基于每日动态决策信号的真实策略回测。

## 9. 后续工作

后续可继续扩展：

- 接入 Kaggle/S&P 500 历史价格 CSV。
- 接入 Alpha Vantage 或 Finnhub 新闻 API，并保存离线缓存。
- 接入 SEC company facts，生成真实基本面指标。
- 增加 Streamlit 可视化展示页。
- 将 equal-weight 辅助回测升级为动态策略回测。
- 用真实 OpenRouter key 运行一次 `--task final --llm required`，记录 LLM 复核结果。
