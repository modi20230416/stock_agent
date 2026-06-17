# 项目迭代优化计划与执行记录

更新日期：2026-06-17

## 目标

在已经满足 proposal 的基础上，将项目从“可运行 final prototype”推进到“超过 proposal 的可评估系统”。优化方向不是继续堆功能，而是增强课程项目最容易被追问的部分：数据是否干净、评估是否充分、风险是否可解释、LLM 是否真的接通、结果是否可复现。

## 迭代计划

| 阶段 | 优化目标 | 执行动作 | 当前状态 |
| --- | --- | --- | --- |
| 1 | LLM 真实调用验证 | 使用 OpenRouter 免费模型 `openai/gpt-oss-20b:free` 跑 `--llm required` smoke test，并记录结果 | 已完成 |
| 2 | 数据质量提升 | 增加 dataset validation，检查 ticker 覆盖、OHLCV 合法性、新闻/基本面覆盖、组合权重与约束 | 已完成 |
| 3 | 修复数据问题 | 修正 processed portfolio 初始权重，使现金与持仓合计为 100% | 已完成 |
| 4 | 超越基础回测 | 在 equal-weight backtest 外增加 decision-weighted strategy backtest | 已完成 |
| 5 | 风险评估增强 | 增加组合压力测试，包括 broad market selloff、tech/AI drawdown、rates/credit tightening、energy spike、defensive rotation | 已完成 |
| 6 | 报告与展示增强 | 将新指标接入 Markdown benchmark、HTML dashboard、final report、presentation slides、README | 已完成 |
| 7 | 可复现验证 | 运行 unit tests、完整离线 demo、LaTeX 编译、密钥扫描 | 已完成 |

## 当前超额完成点

- Proposal 要求：单股分析、候选筛选、组合调仓。
- 当前实现：以上三类任务全部完成，并加入固定 15-case benchmark。
- Proposal 要求：多 Agent 与可解释输出。
- 当前实现：市场、新闻、基本面、风险、决策、可选 LLM 复核均输出结构化中间结果。
- Proposal 要求：可评估。
- 当前实现：baseline 对比、equal-weight backtest、decision-weighted backtest、stress test、dataset validation、HTML dashboard。
- Proposal 要求：可使用 LLM。
- 当前实现：OpenRouter 免费模型真实调用已验证，且无 key 时仍可离线复现。

## 最新验证结果

- Unit tests：7/7 passing
- Final benchmark：15/15 cases passing
- Final criteria：7/7 passing
- Dataset validation：PASS，无 warning
- Stock universe：12 tickers
- Equal-weight backtest：4.77% cumulative return，-1.37% max drawdown，Sharpe 2.44
- Decision-weighted backtest：8.65% cumulative return，-1.18% max drawdown，Sharpe 4.82，12 rebalances
- Worst stress scenario：`tech_ai_drawdown`，-7.46%
- OpenRouter smoke test：`openai/gpt-oss-20b:free`，`llm_review.used=true`

## 后续可选增强

这些不是最终提交阻塞项，适合答辩时作为 future work：

1. 接入缓存式真实行情 CSV adapter，例如 Kaggle/S&P 500 历史价格。
2. 接入 Alpha Vantage/Finnhub 新闻缓存文件。
3. 接入 SEC company facts 的基本面抽取脚本。
4. 给 decision-weighted backtest 加入交易成本、滑点和换手惩罚。
5. 录制 1-2 分钟 demo video，展示 `--task all`、dashboard 和 OpenRouter smoke test。
