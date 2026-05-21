# AI Coding Context

这份文档用于给后续 AI coding 工具提供项目上下文，避免只零散生成代码。

## 项目目标

构建一个面向日频模拟交易的多 Agent 股票决策支持系统。系统输出买入、卖出、持有或调仓建议，同时展示理由、风险提示和各 Agent 的中间分析结果。

项目不接入真实券商账户，不做实盘自动执行。当前中期版本证明了架构和任务流程可行；最终版本必须继续扩展到真实/缓存数据、10-20 只股票、完整 benchmark、baseline 对比、失败案例和基础回测指标。详细路线见 `docs/FINAL_ROADMAP.md`。

## 当前 minimal version

当前实现是一个零外部依赖的 Python 原型，并支持可选 OpenRouter LLM 调用：

- 输入：`data/sample/` 中的价格、新闻、基本面、组合约束。
- 核心代码：`src/stock_agent/`。
- 入口：`scripts/run_demo.py`。
- 测试：`tests/test_pipeline.py`。
- 输出：`reports/`。
- LLM：`src/stock_agent/llm.py` 使用 `OPENROUTER_API_KEY` 调用 OpenRouter chat completions，默认模型 `openrouter/free`。

## Agent 分工

- `MarketInformationAgent`：读取日频 OHLCV，计算 MA3/MA8、收益、动量、波动率，输出市场侧 score。
- `NewsSentimentAgent`：读取样例新闻和 sentiment，输出新闻平均情绪、事件风险和证据列表。
- `FundamentalAnalysisAgent`：读取收入增速、净利率、EPS 增速、债务权益比、自由现金流，输出基本面 score。
- `RiskManagementAgent`：检查最大持仓、最大交易、最低现金、波动率阈值，并在必要时调整建议。
- `DecisionAgent`：按权重综合市场、新闻、基本面结果，再合并风险检查，输出最终行动。
- `LLMDecisionAdvisor`：把上述 Agent 的结构化输出发送给 OpenRouter 免费模型，请模型进行保守复核，返回 JSON 格式的 action、rationale、risk_warnings 和 uncertainty。

## 任务和 benchmark

当前支持三类 proposal 中的代表任务：

- 单股票分析：`python scripts\run_demo.py --task single --ticker AAPL`
- 候选股票筛选：`python scripts\run_demo.py --task screen`
- 小型股票池调仓：`python scripts\run_demo.py --task rebalance`

benchmark 命令：

```powershell
python scripts\run_demo.py --task benchmark
```

启用真实 LLM 调用：

```powershell
$env:OPENROUTER_API_KEY="..."
python scripts\run_demo.py --task benchmark --llm required
```

`--llm auto` 会自动使用 key，否则保留规则 fallback；`--llm required` 用于证明真实 API 调用已成功；`--llm off` 用于稳定单元测试。

评估指标：

- 单股票任务是否有明确 action、理由和风险提示。
- 候选筛选是否能区分不同标的。
- 调仓是否满足仓位、交易和现金约束。
- 对比技术规则 baseline 和无风险管理 baseline。

## 从当前版本到最终版本

最终版本目标不是更大的 minimal demo，而是 proposal 中定义的“可解释、可验证、可交互”的股票决策支持原型。后续工作按以下顺序推进：

1. 数据层：增加 Kaggle/S&P 500 价格 CSV loader、Alpha Vantage 新闻缓存格式、SEC company facts 字段抽取。
2. 任务层：把三类任务改为从固定 benchmark case 文件读取输入，扩展到 10-20 只股票。
3. Agent 层：增强市场指标、新闻摘要/事件归因、基本面缺失处理、冲突检测和不确定性表达。
4. LLM 层：保留 OpenRouter 复核 Agent，同时增加新闻理解 prompt；所有 LLM 输出必须结构化、可缓存、可 fallback。
5. 评估层：加入单 Agent baseline、技术规则 baseline、无风险管理 baseline、结构性成功标准和回测辅助指标。
6. 展示层：优先做 CLI summary/table，可选 Streamlit 页面展示 Agent 中间输出。
7. 报告层：整理数据来源、系统设计、baseline 对比、失败案例和局限性。

具体里程碑、验收标准和交付清单见 `docs/FINAL_ROADMAP.md`。

## 修改代码时的注意事项

- 不要把真实 API key 写进代码库。
- 保留离线样例数据，保证没有网络时也能复现实验。
- 新增数据源时优先新增 loader/adapter，不要把 API 调用写进 Agent 内部。
- 新增真实数据时必须同时提供离线缓存或样例文件，保证没有 API key 时也能复现。
- 决策逻辑必须保留中间结果，不能只输出最终 action。
- LLM 输出必须解析为结构化 JSON；如果模型不可用，auto 模式需要保留可复现实验。
- 所有新增任务都应补充测试、benchmark case 和报告输出。
