# 项目进度更新

更新时间：2026-05-21

## 当前阶段结论

项目已经从 proposal 阶段推进到可运行的 LLM minimal version。当前版本可以在本地 PyCharm 或 PowerShell 中复现，已经覆盖 proposal 中规划的三类核心任务：单股票分析、候选股票筛选和小型组合调仓。

当前系统仍然是课程中期原型，不声称能稳定盈利，也不构成投资建议；其主要价值是证明多 Agent 决策流程、LLM 复核、风险约束和 benchmark 评估路径是可行的。

## 已完成

- 项目结构搭建：`src/stock_agent/`、`data/sample/`、`scripts/`、`tests/`、`docs/`、`reports/`。
- 离线样例数据：AAPL、MSFT、TSLA、NVDA 的价格、新闻、基本面和组合约束。
- 多 Agent 原型：
  - 市场信息 Agent
  - 新闻情绪 Agent
  - 基本面分析 Agent
  - 风险管理 Agent
  - 决策 Agent
  - OpenRouter LLM 复核 Agent
- 三类任务：
  - 单股票分析
  - 候选股票筛选
  - 小型股票池调仓
- baseline 对比：
  - 简单技术指标规则
  - 无风险管理 ensemble
- benchmark 输出：
  - `reports/benchmark_results.json`
  - `reports/benchmark_results.md`
- 工程环境：
  - `.venv` 虚拟环境
  - `pyproject.toml`
  - `requirements.txt`
  - `scripts/setup_env.ps1`
  - PyCharm 运行配置 `Run Demo All`
  - PyCharm 测试配置 `Run Unit Tests`

## 当前验证结果

已通过以下命令验证：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --llm auto
```

测试结果：

- 单元测试：4/4 通过。
- benchmark 成功标准：全部通过。
- 当前离线 fallback 模式：`LLM used count = 0`，因为尚未在运行环境中设置 `OPENROUTER_API_KEY`。
- 设置 OpenRouter API key 后，可以通过 `--llm required` 强制验证真实 LLM 调用。

## 当前 benchmark 摘要

- AAPL：HOLD
- MSFT：BUY
- TSLA：SELL
- NVDA：BUY

调仓结果满足当前约束：

- 最大单只持仓不超过 35%。
- 单次交易变动不超过 15%。
- 保留最低现金比例。

## 已解决的问题

- 初始版本过于规则化：已加入 OpenRouter LLM 复核模块。
- 无项目环境：已创建 `.venv`、`pyproject.toml` 和环境初始化脚本。
- PyCharm `No interpreter`：已注册项目虚拟环境解释器。
- PyCharm 运行配置报 module null：已修正运行配置。
- PyCharm Project 视图误打开 Desktop：已清理 `.idea` 缓存并重建模块配置。

## 尚未完成

- 尚未接入真实历史价格数据集。
- 尚未接入 Alpha Vantage 新闻 API 或离线缓存。
- 尚未接入 SEC company facts 基本面数据。
- 新闻 Agent 目前仍基于样例 sentiment 字段，尚未做长文本新闻理解。
- 尚未加入完整历史回测收益指标，如累计收益率、最大回撤和 Sharpe ratio。
- 股票池仍是 4 只，后续需要扩展到 10-20 只。

## 下一步计划

下一步不应只围绕 minimal version 打磨，而应进入最终版本建设。详细计划见 `docs/FINAL_ROADMAP.md`。

近期优先级：

1. 用 OpenRouter API key 跑一次 `--llm required`，将 LLM 实际调用结果写入 benchmark。
2. 增加真实数据 loader，优先支持 CSV 价格数据和新闻缓存。
3. 将三类任务改为从固定 benchmark case 文件读取输入。
4. 增加缺失数据、信息冲突、高波动场景的 benchmark case。
5. 加入基础回测指标，形成更完整的最终报告实验部分。
