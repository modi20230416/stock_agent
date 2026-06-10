# 项目进度更新

更新时间：2026-06-10

## 当前结论

项目已经从中期 minimal version 推进到可演示的 final project prototype。当前版本不再只是 4 支股票的规则原型，而是包含 12 支股票离线数据、固定 benchmark case suite、增强 Agent、OpenRouter 可选 LLM 复核、三类 baseline、组合约束检查和基础回测指标的完整课程项目版本。

系统仍然只用于课程研究和模拟决策，不连接真实券商账户，也不构成投资建议。

## 已完成

- 工程环境
  - `.venv` 虚拟环境
  - `pyproject.toml`
  - `scripts/setup_env.ps1`
  - PyCharm 可使用 `.venv\Scripts\python.exe` 运行
  - GitHub 仓库：`https://github.com/modi20230416/stock_agent`

- 数据层
  - `data/sample/`：中期 minimal sample
  - `data/processed/`：12 支股票、60 个交易日的 final 离线数据
  - `data/benchmark/cases.json`：15 个固定 benchmark cases
  - `scripts/generate_final_data.py`：可重新生成 deterministic final dataset

- Agent 层
  - MarketInformationAgent：MA5/MA20、20 日收益、波动率、成交量变化、短期回撤
  - NewsSentimentAgent：新闻情绪、事件类型、事件风险提示
  - FundamentalAnalysisAgent：收入增长、EPS 增长、净利率、债务权益比、自由现金流
  - RiskManagementAgent：最大持仓、最大交易、最低现金、波动率约束
  - DecisionAgent：多 Agent 加权、风险修正、显式冲突检测
  - LLMDecisionAdvisor：OpenRouter 结构化 JSON 复核，可 fallback

- 任务层
  - 单股分析
  - 候选股票筛选
  - 小型组合调仓
  - Final benchmark case suite runner

- 评估层
  - 技术规则 baseline
  - 无风险管理 ensemble baseline
  - Direct LLM/single-agent baseline
  - Equal-weight backtest：累计收益、年化收益、最大回撤、Sharpe ratio
  - JSON 详情报告和 Markdown 摘要报告

- 测试
  - 单股分析结构完整性
  - 股票池筛选区分度
  - 调仓约束
  - benchmark 成功标准
  - final case suite 15/15 通过

## 当前验证结果

已运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

结果：

- 单元测试：6/6 通过。
- Final benchmark：15/15 cases 通过。
- 股票池：12 支股票，满足 proposal 中 10-20 支股票范围。
- Screening cases：2/2 通过。
- Rebalance cases：3/3 通过，均满足组合约束。
- Backtest：已生成 equal-weight 辅助回测指标。

当前 final benchmark 摘要见：

```text
reports/final_benchmark_results.md
```

## 与中期版本相比的推进

中期版本重点证明“能跑通”。当前 final prototype 重点证明“能评估、能比较、能复现”：

- 股票池从 4 支扩展到 12 支。
- benchmark 从单次 demo 扩展为 15 个固定 cases。
- Agent 输出增加事件类型、回撤、冲突检测和更完整风险提示。
- baseline 从 2 个扩展到 3 个。
- 增加基础回测指标。
- CLI 增加 `--task final`，可一键生成最终评估报告。
- 文档更新为 final project 复现说明。

## 尚未纳入当前仓库的可选增强

这些不是当前 final prototype 的阻塞项，但适合作为答辩时的 future work：

- 接入真实 Kaggle/S&P 500 历史价格 CSV。
- 接入 Alpha Vantage/Finnhub 新闻 API 缓存。
- 接入 SEC company facts 的真实基本面字段抽取。
- 增加 Streamlit 展示页面。
- 将回测从 equal-weight 辅助指标扩展为基于每日决策信号的动态策略回测。
- 为 LLM 新闻摘要和事件归因增加缓存文件，减少重复 API 调用。

## 下一步建议

1. 用真实 OpenRouter key 运行一次：

```powershell
$env:OPENROUTER_API_KEY="你的 key"
.\.venv\Scripts\python.exe scripts\run_demo.py --task final --llm required
```

2. 将 `reports/final_benchmark_results.md` 中的 15/15 结果截图或摘录到课程最终报告。

3. 小组成员分别负责：
   - 数据源说明与局限性
   - Agent 设计图和 prompt/JSON 结构
   - benchmark 与 baseline 分析
   - 最终报告和演示材料
