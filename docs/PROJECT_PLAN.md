# 项目工作计划

当前日期为 2026-05-21，本周五截止对应 2026-05-22 23:59。中期目标是提交一个能证明项目可行性的 minimal version，而不是一次性完成最终系统。

中期之后的目标是沿 proposal 继续推进到最终版本：真实/缓存数据、10-20 只股票、完整 benchmark、baseline 对比、失败案例分析、基础回测指标和轻量展示层。详细路线见 `docs/FINAL_ROADMAP.md`。

## 1. 中期前必须完成

- 搭建代码结构和离线样例数据。
- 实现关键 Agent：市场、新闻、基本面、风险、决策，以及 OpenRouter LLM 复核 Agent。
- 跑通三类任务：单股票分析、候选筛选、组合调仓。
- 提供 baseline：技术指标规则、无风险管理版本。
- 生成 benchmark 报告，展示是否满足 proposal 中的成功标准。
- 写 README 和 AI coding context，方便后续持续开发。

当前状态：已完成。没有 API key 时可离线复现；设置 `OPENROUTER_API_KEY` 后可通过 `--llm required` 强制调用免费模型。

最新进度更新见 `docs/PROGRESS.md`。当前工程环境已经完成 PyCharm 配置修复，项目可通过 `.venv` 或 PyCharm 的 `Run Demo All` 运行。

## 2. 中期报告建议呈现方式

报告中建议突出四点：

- 已经从 proposal 进入可运行 LLM 原型，核心流程可执行。
- 多 Agent 输出不是黑盒，能展示中间分析和证据。
- LLM 不直接凭空决策，而是读取规则 Agent 的结构化上下文后做保守复核。
- benchmark 不是收益率导向，而是先检查稳定性、可解释性和约束满足。
- 当前离线样例是范围控制手段，后续会替换为真实数据和更大测试集。

## 3. 后续四周计划概览

详细任务拆解和验收标准已迁移到 `docs/FINAL_ROADMAP.md`。这里保留高层摘要。

### 第 1 周：真实数据和任务集基础

- 增加 Kaggle/S&P 500 CSV 价格数据 loader。
- 增加 Alpha Vantage news/sentiment 的离线缓存格式。
- 增加 SEC company facts 的字段抽取脚本。
- 将三类任务改为从 benchmark case 文件读取输入。

### 第 2 周：Agent 能力增强

- 为新闻 Agent 增加 LLM prompt 或金融文本摘要模块。
- 增加冲突检测：例如技术面看涨但新闻/基本面看跌。
- 增加不确定性表达：缺数据、冲突、风险过高时输出保守建议。
- 扩展市场、新闻、基本面和风险 Agent 的证据输出。

### 第 3 周：评估和回测

- 扩展 benchmark case 至 10-20 只股票。
- 加入回测统计：累计收益率、最大回撤、Sharpe ratio。
- 与 baseline 做定量和定性对比。
- 增加单 Agent LLM baseline 和失败案例分析模板。

### 第 4 周：展示和最终整理

- 增加轻量展示层，展示三类任务和 Agent 中间输出。
- 整理失败案例分析。
- 完成最终报告、演示脚本和复现实验说明。
- 固定最终 demo 命令和截图材料。

## 4. 当前风险和控制

- 数据 API 不稳定：保留离线缓存和样例数据。
- 金融建议难以定义“正确”：评估先关注结构完整、风险约束、解释质量。
- 范围容易膨胀：坚持日频、小股票池、模拟交易，不做实盘或高频。
- IDE/环境配置可能影响复现：已补充 `.venv`、`pyproject.toml`、`setup_env.ps1` 和 PyCharm 运行配置，降低演示时的环境风险。
