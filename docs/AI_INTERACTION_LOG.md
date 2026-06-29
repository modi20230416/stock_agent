# AI 协作交互记录 — 项目开发全过程

> 说明：`docs/AI_COLLAB_CONTEXT.md` 负责提供当前上下文；本文件按时间线整理 AI 交互，便于回看、交接和追踪每一轮迭代。

## 当前快照

- 最新提交：`0c709da`，README 已整理为导师审批 / 组员复现版。
- 当前状态：`tests` 16/16 passing，`final benchmark` 15/15 passing，真实数据链路已打通。
- 主要可交付物：`reports/VERIFICATION.md`、`reports/final_benchmark_results.md`、`reports/final_dashboard.html`、`docs/ITERATION_OPTIMIZATION_PLAN.md`、`README.md`。

## 第一阶段：项目验证（初始）

### 交互 1
**用户指令**：验证项目有无达到设计目标，并设计迭代优化计划不断更新，完成输出

**AI 行动**：
- 读取 README、initial_pitch、src 全部模块、tests、迭代计划、benchmark 报告
- 实际运行 `unittest discover -s tests` → 7/7 通过
- 实际运行 `scripts/run_demo.py --task final --llm off` → 15/15 cases，`pass_rate=1.0`
- 对照 proposal 第 6 节 5 项成功标准逐条验证：全部 PASS
- 发现现有迭代计划 7 个阶段已全部"已完成"

**用户反馈**：选择"实际执行下一轮优化项"

---

## 第二阶段：Round 2 — 交易成本感知回测

### 交互 2
**用户指令**：确认（方案）

**AI 输出**：仍处于 plan mode → 用户退出 plan mode

### 交互 3
**用户指令**：完成优化

**AI 行动**：

| 文件 | 改动 |
|------|------|
| `src/stock_agent/backtest.py` | `BacktestResult` 增加 `total_cost`/`gross_cumulative_return`；`weighted_backtest` 增加 `cost_per_turn` 与 `turnover_by_date`，net 收益逐日扣减成本 |
| `src/stock_agent/pipeline.py` | `_decision_weighted_backtest` 按日记录换手，默认 10 bps 单边，输出 gross/net/total_cost |
| `src/stock_agent/evaluator.py` | Markdown（两处）+ HTML dashboard 增加 gross/net + 成本行 |
| `tests/test_pipeline.py` | 新增 `test_decision_weighted_backtest_includes_cost` |
| `docs/ITERATION_OPTIMIZATION_PLAN.md` | 新增 Round 2 计划表（R2-1~R2-6 全部完成） |
| `README.md` | status 段同步 net-of-cost 指标 |
| `reports/VERIFICATION.md` | 新建实测验证报告 |

**验证结果**：
- 8/8 测试通过（原 7 + 1）
- 15/15 benchmark，`pass_rate=1.0`
- decision-weighted：gross 8.65% → net 8.47%，成本 0.171%

---

## 第三阶段：Round 3 — 滑点 / 市场冲击成本模型

### 交互 4
**用户指令**：继续 round 3 优化

**AI 行动**：

| 文件 | 改动 |
|------|------|
| `src/stock_agent/backtest.py` | 新增 `_portfolio_volatility`；`BacktestResult` 增加 `total_base_cost`/`total_slippage`；`weighted_backtest` 增加 `impact_coefficient`（默认 0.05），按 `slippage = impact_coefficient × turnover² × portfolio_vol` 拆分 base/slippage |
| `src/stock_agent/pipeline.py` | 传入 `impact_coefficient`，输出 `total_base_cost`/`total_slippage`/`impact_coefficient` |
| `src/stock_agent/evaluator.py` | Markdown + HTML dashboard 增加 base cost/slippage 行 |
| `tests/test_pipeline.py` | 新增 `test_decision_weighted_backtest_models_slippage` |
| 文档 | ITERATION_OPTIMIZATION_PLAN Round 3 表、README status、VERIFICATION 三轮对比 |

**验证结果**：
- 9/9 测试通过（+ 1 滑点测试）
- 15/15 benchmark
- decision-weighted：gross 8.65% → net 8.46%，base 0.171% + slippage 0.0075% = total 0.1786%

---

## 第四阶段：Round 4 — 打通真实数据链路

### 交互 5
**用户指令**：打通真实数据链路

**AI 行动**：

| 文件 | 改动 |
|------|------|
| `src/stock_agent/data_sources.py` | 新建。Yahoo Finance chart JSON 主源 + Stooq CSV 备用；`normalize_vendor_csv` 兼容多种列别名；`fetch_prices` 支持 refresh/offline，下载即缓存；`fetch_many` 批量；`write_prices_csv` 回写 |
| `src/stock_agent/data_loader.py` | 增加 `load_vendor_prices` 归一化入口 |
| `scripts/ingest_real_data.py` | 新建。拉取真实行情，合并离线 news/fundamentals，构建 `data/real` |
| `scripts/run_demo.py` | 增加 `--source processed|sample|real` |
| `tests/test_data_sources.py` | 新建。7 项链路测试 |
| `.gitignore` | 忽略 `data/cache/`、`data/real/` |

**验证结果**：
- 联网拉取成功：Yahoo Finance 获取 12 支股票各 114 个交易日（缓存约 500 交易日）
- 离线 fallback：`--offline` 从缓存重建全部 1368 行
- 真实数据 validate：PASS，12 tickers，1368 rows，无缺失
- 16/16 测试通过（+ 7 项真实数据链路测试）
- 确定性 benchmark：仍 15/15，无回归

---

## 第五阶段：Demo 前端 — 演示视频录制准备

### 交互 6
**用户指令**：准备 demo 视频演示用前端

**AI 行动**：

| 文件 | 改动 |
|------|------|
| `scripts/demo_server.py` | 新建。Python 标准库 `http.server` 实现，全部 HTML/CSS/JS 内嵌，零外部依赖。后端实时调用 `StockDecisionSystem` pipeline，4 个 API（single/screen/rebalance/benchmark）+ info |

**前端功能**：
- 四个标签页：单股分析（决策+Agent 中间结果卡片）→ 候选筛选（排序表）→ 组合调仓（权重+交易+风控）→ Benchmark+回测（成功标准+双口径 metrics）
- 顶部控件：数据源切换（processed/sample/real）、日期、单股代码、股票池
- 暗色主题，BUY/SELL/HOLD 彩色标签

**验证结果**：启动服务器 → curl 逐一验证 `/api/info`/`/api/single`/`/api/screen`/`/api/rebalance`/`/api/benchmark` 全部正常返回

---

## 第六阶段：项目经历总结生成

### 交互 7
**用户指令**：按描述/职责/成果三段总结为项目经历

**AI 行动**：
- 读取 2021030019_莫迪_4152.pdf（Initial Pitch）
- 读取 基于TimeRCD的时间序列异常检测系统优化与根因分析.pdf（毕业论文）
- 读取 总结报告.pdf（实习报告）
- 生成三段项目经历：股票多 Agent 系统 / TimeRCD 异常检测 / 约车活动运营优化
- 控制总篇幅（4 轮迭代 => 合并为要点，职责/成果各 3-4 条）

**用户反馈**：太长，请压缩 → AI 压缩到约 40%

### 交互 8
**用户指令**：整理到生成项目经历前的 AI 交互记录

**AI 行动**：
- 遍历所有交互记录，按阶段整理为完整时间线文档
- 标记用户指令、AI 行动、改动文件、验证结果、用户反馈关键节点

### 交互 9
**用户指令**：整理 AI 交互记录，方便后续审批与组员接力

**AI 行动**：
- 将历史交互按阶段整理成更清晰的时间线，并补充当前 final 状态
- 将 README 重写为导师审批 / 组员复现导向，补齐一键复现、真实数据链路、OpenRouter、协作流程
- 让记录文件和上下文文件分工明确：`AI_INTERACTION_LOG.md` 负责 chronology，`AI_COLLAB_CONTEXT.md` 负责 live context

**结果**：
- README 已推送到 GitHub，适合导师审批和组员复现
- 当前仓库状态与记录一致：16/16 tests，15/15 benchmark，真实数据链路可用
- 后续继续新增功能时，可直接在本文件末尾追加新交互段

---

## 统计汇总

| 指标 | 数值 |
|------|------|
| 优化轮次 | 4 轮（Round 1~4） |
| 新增/修改文件 | 约 20 个 |
| 新增测试 | 9 项（7 数据源 + 1 成本 + 1 滑点） |
| 测试通过率 | 7/7 → 8/8 → 9/9 → 16/16 |
| Benchmark 通过率 | 始终 15/15 |
| 用户交互次数 | 9 次核心交互 |

## 交接说明

- 想看“现在是什么状态”：先读 [docs/AI_COLLAB_CONTEXT.md](docs/AI_COLLAB_CONTEXT.md) 和 [README.md](../README.md)。
- 想看“怎么走到现在”：按本文件的时间线从前往后读。
- 想复现结果：先跑 `python -m unittest discover -s tests`，再跑 `scripts/run_demo.py --task final --llm off`。
- 想继续加功能：优先在 `docs/ITERATION_OPTIMIZATION_PLAN.md` 里新增一轮计划，再同步测试和报告。

## 关键设计决策记录

| 决策 | 考量 | 最后选择 |
|------|------|---------|
| 冲击模型形式 | 平方根 vs 二次 | 二次（turnover²），凸性更强，参数更少 |
| 默认交易成本 | 5/10/20 bps | 10 bps，取学术文献中值 |
| 默认冲击系数 | 0.01/0.05/0.1 | 0.05，中等冲击，产生可观测但不主导的滑点 |
| 真实数据源 | Alpha Vantage/Stooq/Yahoo | Yahoo Finance（主）+ Stooq（备用），均无需 API key |
| 数据缓存策略 | gitignore / 保留 | gitignore，通过 ingest 脚本可复现 |
| 前端方案 | Streamlit / Flask / http.server | Python stdlib http.server，零依赖，与项目一致 |
