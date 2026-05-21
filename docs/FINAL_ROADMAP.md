# 从当前版本到最终版本的工作计划

更新时间：2026-05-21

## 最终版本定义

最终版本不应停留在 minimal version。根据 proposal，最终系统应是一个面向日频模拟交易和投资研究的多 Agent 股票决策支持原型，能在小型股票池上稳定完成三类任务：

- 单股票分析：给定某股票在决策日前的价格、新闻和基本面信息，输出交易建议、理由和风险提示。
- 候选股票筛选：给定 10-20 只股票的小型股票池，输出排序、关注对象和规避对象。
- 小型股票池调仓：给定初始持仓和风险约束，输出目标权重、交易变化和约束检查结果。

最终版还需要具备：

- 可解释：展示市场、新闻、基本面、风险、LLM 复核等中间结果。
- 可验证：有 benchmark case、baseline 对比和失败案例分析。
- 可复现：无 API key 时可以使用离线缓存数据运行；有 API key 时可以刷新或扩展数据。
- 可演示：提供 CLI 或轻量展示层，让用户能查看三类任务的结果。

## 当前版本位置

当前版本已经完成：

- 多 Agent 框架和 LLM 复核 Agent。
- 4 只股票的离线样例数据。
- 三类任务的端到端流程。
- 技术指标 baseline 和无风险管理 baseline。
- 单元测试、benchmark 输出和 PyCharm/PowerShell 运行环境。

当前版本尚未完成最终版要求中的真实数据接入、10-20 只股票池、长文本新闻理解、真实 benchmark case、回测指标和展示层。

## 目标架构演进

### 数据层

从当前 `data/sample/` 扩展为：

- `data/raw/`：原始下载文件或 API 缓存。
- `data/processed/`：清洗后的价格、新闻、基本面和任务样例。
- `data/benchmark/`：固定 benchmark case，保证最终实验可复现。

新增适配器：

- 价格数据：Kaggle S&P 500 Stocks CSV loader，先支持本地 CSV，不强依赖在线下载。
- 新闻数据：Alpha Vantage News & Sentiment API 缓存格式；可补充 Finnhub company news。
- 基本面数据：SEC EDGAR company facts/companyfacts.zip 的字段抽取。

### Agent 层

从当前规则和 LLM 复核混合原型扩展为：

- 市场信息 Agent：加入更多日频指标，如 5/20 日均线、波动率、成交量异常、短期回撤。
- 新闻与情绪 Agent：支持新闻摘要、事件归因和情绪解释；用 LLM 处理 headline/summary 或缓存的长文本。
- 基本面 Agent：从 SEC 数据抽取 revenue、net income、EPS、margin、debt 等指标，并处理缺失数据。
- 风险管理 Agent：加入集中度、现金、单次交易、回撤和高波动惩罚规则。
- 决策 Agent：显式处理模块冲突，给出保守/进取程度和不确定性说明。
- LLM 复核 Agent：仅基于结构化证据做复核，不直接替代数据分析模块。

### 任务层

最终任务集应固定并可复现：

- 单股票分析：至少 6-10 个 case，覆盖正向、负向、冲突和缺失数据。
- 候选股票筛选：至少 2-3 个股票池 case，每个 10-20 只股票。
- 调仓任务：至少 3 个 portfolio case，覆盖超配、现金不足、高风险股票等情况。

### 评估层

最终评估包括：

- 结构性成功标准：是否有 action、理由、风险提示、中间结果。
- 风险约束：调仓是否违反最大持仓、最大交易、最低现金等约束。
- baseline 对比：技术指标规则、无风险管理版本、单 Agent 直接决策版本。
- 回测辅助指标：累计收益率、年化收益率、最大回撤、Sharpe ratio。
- 失败案例分析：新闻噪声、基本面缺失、市场剧烈波动、模块冲突。

### 展示层

优先实现轻量展示，不做复杂前端：

- CLI summary/table：用于命令行和报告截图。
- 可选 Streamlit 页面：展示股票池排序、单股票详情、调仓建议和 Agent 中间输出。

## 四周实施计划

### 第 1 周：真实数据和任务集基础

目标：把当前 4 股票样例扩展到可复现的真实/缓存数据框架。

任务：

- 新增 `data/raw/`、`data/processed/`、`data/benchmark/` 目录和说明。
- 实现价格 CSV loader，支持 10-20 只股票的日频 OHLCV 数据。
- 定义统一数据 schema：price/news/fundamental/portfolio/case。
- 为 Alpha Vantage 新闻数据设计离线缓存 JSON/CSV 格式。
- 为 SEC company facts 设计字段抽取格式。
- 构造第一版 benchmark case 文件。

验收标准：

- 无网络环境下能加载处理后的 10-20 只股票价格数据。
- 当前三类任务可以从 benchmark case 文件读取输入，而不是只依赖硬编码参数。
- 单元测试覆盖数据加载和基本 schema 校验。

### 第 2 周：Agent 能力增强和 LLM 新闻理解

目标：让系统能处理更真实的信息冲突、缺失和新闻解释。

任务：

- 扩展市场信息 Agent 指标和证据输出。
- 将新闻 Agent 从单纯 sentiment 字段扩展为“新闻摘要 + 事件类型 + 情绪理由”。
- 增加 LLM prompt，用于新闻摘要和事件归因；保留缓存结果避免重复调用。
- 扩展基本面 Agent，支持 SEC 字段缺失时的保守输出。
- 增加冲突检测，例如技术面看涨但新闻/基本面看跌。
- 增加不确定性等级：low/medium/high。

验收标准：

- 信息冲突 case 中，系统能显式指出冲突来源。
- 缺失新闻或基本面 case 中，系统不会过度自信。
- LLM 输出仍为结构化 JSON，失败时能 fallback。

### 第 3 周：评估、baseline 和回测

目标：从“能跑”推进到“能评估”。

任务：

- 增加单 Agent baseline：把全部输入直接交给 LLM 输出建议。
- 完善无风险管理 baseline 和技术指标 baseline。
- 实现简单日频回测框架，按决策输出更新组合。
- 计算累计收益率、年化收益率、最大回撤、Sharpe ratio。
- 将 benchmark 输出扩展为 JSON + Markdown summary。
- 增加失败案例分析模板。

验收标准：

- benchmark 至少包含 10 个单股票 case、2 个筛选 case、3 个调仓 case。
- 每个 baseline 都能在同一批 case 上运行。
- 报告中能展示至少一张 baseline 对比表和一段失败案例分析。

### 第 4 周：展示、报告和最终打磨

目标：形成可演示、可复现、可说明贡献边界的最终项目。

任务：

- 完成 CLI summary/table 输出。
- 可选实现 Streamlit 展示页。
- 整理最终报告：
  - 系统设计
  - 数据来源
  - Agent 流程
  - benchmark 和 baseline
  - 回测辅助指标
  - 失败案例
  - 局限性
- 完善 README 和复现脚本。
- 固定最终 demo 命令和结果截图。

验收标准：

- 新用户可以按 README 在 10 分钟内跑通 demo。
- 最终报告能明确区分复用部分和项目贡献。
- 演示能展示三类任务、Agent 中间输出和 benchmark 对比。

## 最终交付清单

- 可运行代码：`src/stock_agent/`
- 数据与 benchmark：`data/processed/`、`data/benchmark/`
- 运行脚本：`scripts/`
- 测试：`tests/`
- benchmark 输出：`reports/`
- 最终报告：`docs/` 或课程提交 PDF
- 复现说明：`README.md`

## 优先级原则

- 先保证离线可复现，再增加在线 API。
- 先完成三类任务的稳定评估，再追求复杂策略收益。
- 先保证风险约束和解释输出，再增加更激进的交易建议。
- 所有 LLM 调用都要可缓存、可 fallback、可审计。
