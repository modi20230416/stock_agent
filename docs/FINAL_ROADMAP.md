# 从 Minimal Version 到 Final Version 的路线图与完成状态

更新时间：2026-06-10

## Final Version 定义

根据 proposal，最终版本应当不是一个只会回答单个股票问题的 demo，而是一个可复现的小型多 Agent 股票决策支持系统。它需要稳定完成三类任务：

- 单股分析：给定股票和日期，输出 BUY/SELL/HOLD、score、confidence、解释理由和风险提示。
- 候选股票筛选：给定 10-20 支股票的小型股票池，输出排序和候选区分结果。
- 小型组合调仓：给定初始持仓和风险约束，输出目标权重、交易变化和约束检查。

最终版本还需要具备：

- 可解释：保留市场、新闻、基本面、风险和 LLM 复核的中间结果。
- 可验证：提供固定 benchmark cases、baseline 对比和回测辅助指标。
- 可复现：没有 API key 时仍可用离线数据完整运行。
- 可协作：文档清楚，组员可以 clone 后在本地运行和扩展。

## 当前完成状态

当前仓库已经完成一个可演示的 final project prototype：

- 12 支股票 final 离线数据集：AAPL、MSFT、NVDA、AMZN、GOOGL、META、JPM、XOM、UNH、TSLA、AMD、WMT。
- 15 个固定 benchmark cases：
  - 10 个 single-stock cases
  - 2 个 screening cases
  - 3 个 rebalance cases
- Agent 增强：
  - 市场 Agent 支持 MA5/MA20、20 日收益、波动率、成交量变化、回撤。
  - 新闻 Agent 支持事件类型和事件风险。
  - 决策 Agent 支持多模块冲突检测。
  - 风控 Agent 支持持仓、现金、交易和波动率约束。
- Baseline 与评估：
  - Technical rule baseline
  - No-risk ensemble baseline
  - Direct LLM/single-agent baseline
  - Equal-weight backtest
- CLI：
  - `--task single`
  - `--task screen`
  - `--task rebalance`
  - `--task benchmark`
  - `--task final`
  - `--task all`

验证命令：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

当前结果：

- 单元测试：6/6 通过。
- Final benchmark：15/15 cases 通过。
- Final criteria：全部通过。

## 架构

```text
data/processed/ + data/benchmark/
        |
        v
StockDecisionSystem
        |
        +-- MarketInformationAgent
        +-- NewsSentimentAgent
        +-- FundamentalAnalysisAgent
        +-- RiskManagementAgent
        +-- DecisionAgent
        +-- LLMDecisionAdvisor (optional OpenRouter)
        |
        v
Decision / Ranking / PortfolioRecommendation
        |
        +-- Baseline comparison
        +-- Equal-weight backtest
        +-- Markdown/HTML/JSON reports
```

## 原计划与完成情况

| 模块 | 原计划 | 当前状态 |
| --- | --- | --- |
| 数据层 | 从 4 支股票扩展到 10-20 支，增加 benchmark cases | 已完成：12 支股票、15 个 cases |
| 市场 Agent | 增加更多日频指标 | 已完成：MA5/MA20、收益、波动率、成交量、回撤 |
| 新闻 Agent | 增加事件类型和更清楚证据 | 已完成：event_type、事件风险、证据列表 |
| 基本面 Agent | 保留结构化基本面指标 | 已完成：收入、EPS、净利率、债务、FCF |
| 风控 Agent | 检查组合约束 | 已完成：持仓、交易、现金、波动率 |
| 决策 Agent | 显式处理冲突和不确定性 | 已完成：跨 Agent 冲突检测和风险提示 |
| LLM | OpenRouter 复核，可 fallback | 已完成：`auto`、`required`、`off` 三种模式 |
| Baseline | 技术、无风控、单 Agent/LLM baseline | 已完成 |
| 回测 | 输出基础收益风险指标 | 已完成：equal-weight 辅助回测 |
| 报告 | JSON + Markdown + HTML dashboard | 已完成 |
| 测试 | 覆盖核心任务和 final cases | 已完成 |

## 当前 final benchmark 摘要

`reports/final_benchmark_results.md` 显示：

- Cases：15 total
- Pass rate：15/15
- 股票池规模：12
- Multi-agent risk warnings：16
- Equal-weight cumulative return：4.77%
- Equal-weight max drawdown：-1.37%

这些结果来自 deterministic offline dataset，便于课程复现和小组协作。真实市场数据接入可以作为 future work，不影响当前版本的可运行性。

## Future Work

如果还有时间，优先顺序如下：

1. 用真实 OpenRouter key 跑 `--llm required`，保存 LLM 实际调用报告。
2. 增加真实 CSV 数据 adapter，例如 Kaggle/S&P 500 历史价格数据。
3. 为 Alpha Vantage/Finnhub 新闻 API 设计缓存文件格式。
4. 为 SEC company facts 增加基本面字段抽取脚本。
5. 实现 Streamlit 页面，展示排序、单股详情、调仓和 Agent 中间输出。
6. 将 equal-weight 回测升级成动态策略回测。

## 最终交付清单

- 代码：`src/stock_agent/`
- 数据：`data/processed/`、`data/benchmark/`
- 脚本：`scripts/run_demo.py`、`scripts/generate_final_data.py`
- 测试：`tests/test_pipeline.py`
- 报告：`reports/final_benchmark_results.md`
- 展示页：`reports/final_dashboard.html`
- 文档：`README.md`、`docs/PROGRESS.md`、`docs/AI_COLLAB_CONTEXT.md`

## 复现原则

- 不提交真实 API key。
- 没有网络时仍能完整运行 final benchmark。
- 所有 Agent 都输出结构化中间结果。
- LLM 调用失败时必须 fallback。
- 新增功能必须补充测试或 benchmark case。
