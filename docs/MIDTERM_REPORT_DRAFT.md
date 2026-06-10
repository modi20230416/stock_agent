# 中期报告草稿

## 项目题目

面向日频模拟交易的多 Agent 股票决策支持系统设计与实现

## 一、项目目标和场景

本项目面向日频模拟交易和投资研究场景，构建一个多 Agent 股票决策支持系统。系统不连接真实券商账户，也不进行实盘交易，而是在离线样例或历史数据上输出买入、卖出、持有或调仓建议，并展示各模块的中间分析结果、支持理由和风险提示。

中期阶段的核心目标是完成一个 minimal version，以验证 proposal 中设计的多 Agent 架构是否可运行、可解释、可评估。

## 二、当前实现进展

中期版本已经实现 Python 原型，代码位于 `src/stock_agent/`，运行入口为 `scripts/run_demo.py`。该原型使用 `data/sample/` 中的离线样例数据，包括 AAPL、MSFT、TSLA、NVDA 的日频价格、新闻情绪、基本面指标和初始组合约束。

系统已经接入 OpenRouter。前几个规则 Agent 先产生结构化市场、新闻、基本面和风险分析，然后 LLM Agent 读取这些中间结果，对最终 action、理由、风险提示和不确定性进行保守复核。如果没有设置 API key，系统会自动 fallback 到离线规则版本，以保证 benchmark 可复现。

当前实现的关键模块包括：

- 市场信息 Agent：基于日频价格计算移动均线、收益率、动量和波动率。
- 新闻情绪 Agent：根据样例新闻 sentiment 汇总利好、利空和事件风险。
- 基本面分析 Agent：根据收入增长、EPS 增长、净利率、债务权益比和自由现金流输出评价。
- 风险管理 Agent：检查最大持仓、最大交易、最低现金和波动率约束。
- 决策 Agent：综合前述模块，输出最终建议和解释。
- LLM 复核 Agent：调用 OpenRouter 免费模型，对结构化 Agent 结果进行最终审阅。

## 三、已跑通的代表性任务

### 1. 单股分析

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task single --ticker AAPL --llm auto
```

系统输出 action、score、confidence、四类 Agent 中间结果和风险提示。

### 2. 候选股票筛选

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task screen --tickers AAPL,MSFT,TSLA,NVDA --llm auto
```

系统能够对候选股票排序，而不是对所有股票输出相同结论。

### 3. 小型组合调仓

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task rebalance --llm auto
```

系统根据初始持仓和风险约束生成 target weights 和 trades，并检查组合约束。

## 四、Benchmark 与 Baseline

中期版本实现了两个 baseline：

- 技术指标规则 baseline：只使用价格和移动均线。
- 无风险管理 ensemble baseline：使用市场、新闻和基本面信号，但不经过风险 Agent。

Benchmark 命令：

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --llm auto
```

检查标准包括：

- 单股分析是否有明确 action、理由和风险提示。
- 筛选任务是否能区分候选股票。
- 调仓结果是否满足持仓和现金约束。
- 系统是否显式展示风险或不确定性。

## 五、当前局限

中期版本主要用于验证可行性，仍有以下局限：

- 股票池规模较小。
- 数据来自离线样例，尚未扩展到真实或缓存数据。
- benchmark 主要检查结构完整性和约束满足情况。
- 回测指标尚不完整。

## 六、后续计划

后续四周计划：

1. 扩展到 10-20 支股票的离线/缓存数据。
2. 定义固定 benchmark case suite。
3. 增强 Agent 的事件类型、冲突检测和不确定性表达。
4. 增加 direct LLM baseline、基础回测指标和 Markdown 报告。
5. 整理最终报告和演示材料。

## 七、中期结论

中期阶段已经完成项目关键组件和端到端 LLM minimal version。系统能够在小型股票池上完成单股分析、候选筛选和调仓任务，并输出结构化建议、解释理由、风险提示、LLM 复核结果和 benchmark 对比结果。因此，项目具备继续推进到最终版本的可行性。
