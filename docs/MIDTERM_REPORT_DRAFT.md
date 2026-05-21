# 中期报告草稿

## 项目标题

面向日频模拟交易的多 Agent 股票决策支持系统设计与实现

## 一、项目目标和场景

本项目面向日频模拟交易和投资研究场景，构建一个多 Agent 股票决策支持系统。系统不接入真实券商账户，也不进行实盘交易，而是在离线样例或历史数据上输出买入、卖出、持有或调仓建议，并展示各模块的中间分析结果、支持理由和风险提示。

中期阶段的核心目标是完成一个 minimal version，以验证 proposal 中设计的多 Agent 架构是否可运行、可解释、可评估。

## 二、当前实现进展

目前已经完成一个 Python 原型，代码位于 `src/stock_agent/`，运行入口为 `scripts/run_demo.py`。该原型使用 `data/sample/` 中的离线样例数据，包括 AAPL、MSFT、TSLA、NVDA 的日频价格、新闻情绪、基本面指标和初始组合约束。

为避免中期版本过于规则化，当前版本已经接入 OpenRouter。系统默认使用 `openrouter/free` 免费模型路由：前几个规则 Agent 先产生结构化市场、新闻、基本面和风险分析，然后 LLM Agent 读取这些中间结果，对最终 action、理由、风险提示和不确定性进行保守复核。如果没有设置 API key，系统会自动回退到离线规则版本，以保证 benchmark 可复现。

当前实现了五个关键模块：

- 市场信息 Agent：基于日频价格计算移动均线、动量、收益率和波动率。
- 新闻与情绪 Agent：根据样例新闻 sentiment 汇总利好、利空和事件风险。
- 基本面分析 Agent：根据收入增速、EPS 增速、净利率、债务权益比和自由现金流输出基本面评价。
- 风险管理 Agent：检查最大持仓、最大交易、最低现金和波动率约束。
- 决策 Agent：综合前述模块，输出最终建议和可解释理由。
- LLM 复核 Agent：调用 OpenRouter 免费模型，对结构化 Agent 结果进行最终审阅，并返回 JSON 格式的理由、风险提示和不确定性说明。

除核心算法流程外，当前版本也已经完成基本工程化配置：项目包含 `.venv` 虚拟环境、`pyproject.toml`、环境初始化脚本 `scripts/setup_env.ps1`、PyCharm 运行配置和单元测试配置。因此，中期版本不仅能在命令行中运行，也能在 IDE 中复现实验结果。

## 三、已跑通的代表性任务

### 1. 单股票分析

命令：

```powershell
python scripts\run_demo.py --task single --ticker AAPL
```

启用真实 LLM 调用时使用：

```powershell
$env:OPENROUTER_API_KEY="..."
python scripts\run_demo.py --task single --ticker AAPL --llm required
```

系统会输出最终 action、综合 score、confidence、市场/新闻/基本面/风险四类中间结果和风险提示。以 AAPL 样例为例，系统输出 HOLD，并解释其技术面偏正向，但新闻和基本面信号相对温和，同时给出债务权益比相关风险提示。

### 2. 候选股票筛选

命令：

```powershell
python scripts\run_demo.py --task screen --tickers AAPL,MSFT,TSLA,NVDA
```

系统能对候选股票排序，而不是对所有标的给出相似结论。当前样例中，NVDA 和 MSFT 排名靠前，TSLA 因价格趋势、新闻和基本面均偏弱而被排在末位。

### 3. 小型股票池调仓

命令：

```powershell
python scripts\run_demo.py --task rebalance
```

系统会根据初始持仓和风险约束生成 target weights 和 trades。当前样例中，组合建议降低 TSLA、增加 NVDA/MSFT，同时保留现金缓冲，并限制单次交易幅度不超过约束。

## 四、benchmark 与 baseline

中期版本实现了两个 baseline：

- 简单技术指标规则：只使用价格和移动均线，不使用新闻、基本面或风险管理。
- 无风险管理 ensemble：使用市场、新闻、基本面信号，但不经过风险 Agent。

benchmark 命令：

```powershell
python scripts\run_demo.py --task benchmark
```

输出文件为 `reports/benchmark_results.md` 和 `reports/benchmark_results.json`。

当前 benchmark 检查的成功标准包括：

- 单股票分析是否有明确 action、理由和风险提示。
- 候选筛选是否能区分不同股票。
- 调仓结果是否满足最大持仓、最低现金等约束。
- 系统是否显式展示风险或不确定性。

当前运行结果中，上述标准均通过。多 Agent + 风险管理 + LLM 复核版本相较 baseline 的主要优势不是声称收益更高，而是输出更完整、风险提示更明确，并且调仓建议不会违反预设约束。LLM 的作用是利用自然语言推理能力检查结构化证据是否一致，而不是直接替代价格、新闻和风险模块。

## 五、当前局限

当前版本仍是 minimal version，主要用于验证可行性，存在以下局限：

- 使用离线小样例数据，还没有接入 Kaggle、Alpha Vantage、SEC 等真实数据源。
- 新闻情绪目前仍使用样例 sentiment 字段；LLM 已用于最终复核，但还未扩展为完整长文本新闻理解和事件归因模块。
- benchmark 主要检查结构完整性、可解释性和风险约束，尚未加入完整历史回测收益指标。
- 股票池规模为 4 只，后续需要扩展到 proposal 中计划的 10-20 只。
- 真实 LLM 调用依赖 OpenRouter API key；没有 key 时系统会使用规则 fallback，以保证离线可复现。

## 六、后续计划

接下来四周计划如下：

- 第 1 周：接入真实价格、新闻和基本面数据，并保留离线缓存以保证复现。
- 第 2 周：增强新闻 Agent 和冲突检测能力，使系统能处理信息冲突和数据缺失。
- 第 3 周：扩展 benchmark，加入累计收益率、最大回撤、Sharpe ratio 等回测指标。
- 第 4 周：完善展示层、失败案例分析和最终报告。

## 七、中期结论

中期阶段已经完成项目关键组件和端到端 LLM minimal version。系统能够在小型股票池上完成单股票分析、候选筛选和调仓任务，输出结构化建议、解释理由、风险提示、LLM 复核结果和 benchmark 对比结果。因此，项目具备继续推进的可行性，后续重点将从架构验证转向真实数据接入、评估扩展和展示完善。
