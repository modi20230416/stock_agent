# 项目迭代优化计划与执行记录

更新日期：2026-06-17（Round 4）

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

## Round 2 迭代计划（交易成本感知回测）

Round 1 的 7 个阶段已全部完成，系统已达到并超出 proposal 设计目标。Round 2 聚焦答辩时最容易被追问的回测真实性问题：原 decision-weighted backtest 假设无摩擦，会高估策略收益。

| 阶段 | 优化目标 | 执行动作 | 当前状态 |
| --- | --- | --- | --- |
| R2-1 | 回测引入交易成本 | `weighted_backtest` 增加 `cost_per_turn` 与按日 `turnover_by_date`，按换手扣减日收益 | 已完成 |
| R2-2 | 输出 gross/net 双口径 | `_decision_weighted_backtest` 输出 `gross_cumulative_return`、`net_cumulative_return`、`total_transaction_cost`、`cost_per_turn` | 已完成 |
| R2-3 | 成本可配置 | 通过 portfolio constraints 的 `transaction_cost` 覆盖默认 10 bps 单边 | 已完成 |
| R2-4 | 报告与展示同步 | Markdown benchmark、HTML dashboard 增加 gross/net 与交易成本行 | 已完成 |
| R2-5 | 测试覆盖 | 新增 `test_decision_weighted_backtest_includes_cost`，断言 net ≤ gross、成本 ≥ 0 | 已完成 |
| R2-6 | 可复现验证 | 重跑 unit tests 与离线 final benchmark | 已完成 |

设计原则：向后兼容（新字段为增量，equal-weight 无换手时 gross=net）、完全离线确定性、新功能配套测试。

## Round 3 迭代计划（滑点 / 市场冲击成本模型）

Round 2 引入了固定费率交易成本。Round 3 进一步细化执行成本：现实中成本不是恒定费率，而应随换手规模与组合波动率非线性放大（市场冲击）。这让 net 回测对换手敏感，避免高频调仓被低估成本。

冲击模型：
```
slippage = impact_coefficient * turnover^2 * portfolio_volatility
total_cost_per_rebalance = base_cost + slippage
```
其中 `portfolio_volatility` 由各标的历史日收益波动率按权重加权得到，`turnover^2` 体现凸性冲击。

| 阶段 | 优化目标 | 执行动作 | 当前状态 |
| --- | --- | --- | --- |
| R3-1 | 计算标的波动率 | `backtest._portfolio_volatility` 基于历史日收益 `pstdev` 输出每标的波动率 | 已完成 |
| R3-2 | 滑点/冲击建模 | `weighted_backtest` 增加 `impact_coefficient`，按 `turnover^2 * portfolio_vol` 计入滑点 | 已完成 |
| R3-3 | 成本拆分输出 | `BacktestResult` 与 `_decision_weighted_backtest` 输出 `total_base_cost`、`total_slippage`、`impact_coefficient` | 已完成 |
| R3-4 | 成本可配置 | 通过 constraints 的 `impact_coefficient` 覆盖默认 0.05 | 已完成 |
| R3-5 | 报告与展示同步 | Markdown benchmark、HTML dashboard 增加 base cost / slippage / impact 行 | 已完成 |
| R3-6 | 测试覆盖 | 新增 `test_decision_weighted_backtest_models_slippage`，断言 total=base+slippage、net ≤ gross | 已完成 |
| R3-7 | 可复现验证 | 重跑 unit tests 与离线 `--task all` | 已完成 |

设计原则：向后兼容（`impact_coefficient` 默认参数，equal-weight 无换手时 slippage=0）、完全离线确定性、成本恒等式 total=base+slippage 可验证。

## Round 4 迭代计划（打通真实数据链路）

前三轮都在确定性离线数据上做评估。Round 4 打通真实行情数据链路：系统现在能从真实、无需 API key 的市场数据源拉取日频价格，归一化为内部 OHLCV schema，并保留磁盘缓存与离线 fallback，保证课程可复现性不被破坏。

数据链路设计：
```
Yahoo Finance chart JSON（主，无 key） ──┐
                                          ├─→ 归一化 CSV → data/cache/<TICKER>.csv → data/real/prices.csv
Stooq daily CSV（备用 fallback）      ──┘                       ↑离线时直接复用缓存
```

| 阶段 | 优化目标 | 执行动作 | 当前状态 |
| --- | --- | --- | --- |
| R4-1 | 真实行情接入 | 新增 `data_sources.py`：Yahoo chart JSON 主源 + Stooq CSV 备用，纯标准库实现 | 已完成 |
| R4-2 | vendor 归一化 | `normalize_vendor_csv` 兼容 `Date/Open/High/Low/Close/Adj Close/Volume` 等列别名，过滤非法行、支持日期窗口 | 已完成 |
| R4-3 | 缓存与离线 fallback | `fetch_prices` 支持 `refresh/offline`，下载即缓存，无网络时复用缓存 | 已完成 |
| R4-4 | 数据集构建脚本 | 新增 `scripts/ingest_real_data.py`，拉取真实价格并合并离线 news/fundamentals 生成 `data/real` | 已完成 |
| R4-5 | CLI 接入 | `run_demo.py` 增加 `--source processed/sample/real` | 已完成 |
| R4-6 | 测试覆盖 | 新增 `tests/test_data_sources.py`：归一化、Adj Close 别名、日期窗口、缺列报错、缓存 fallback、离线无缓存报错、回写往返 | 已完成 |
| R4-7 | 真实链路验证 | 联网拉取 12 支股票真实日频价格，离线 fallback 重建，真实数据上跑 validate/single/benchmark | 已完成 |

设计原则：纯标准库（无 pandas/requests）、多源降级、下载即缓存、离线可复现、向后兼容（默认仍走 processed）。`data/cache` 与 `data/real` 为可复现产物，已加入 `.gitignore`。

## 最新验证结果（Round 4 之后）

- Unit tests：16/16 passing（新增 7 个真实数据链路测试）
- 真实数据链路：Yahoo Finance 成功拉取 12 支股票真实日频价格（缓存含约 500 个交易日），离线 fallback 从缓存重建通过
- 真实数据集 validate：PASS，12 tickers，1368 price rows，无缺失新闻/基本面
- 真实数据 equal-weight backtest（示例 AAPL/MSFT/NVDA）：累计收益 7.6%，最大回撤 -6.63%，Sharpe 0.64（比合成数据更贴近现实）
- 确定性 final benchmark（processed）：仍 15/15 passing，无回归
- Final benchmark：15/15 cases passing
- Final criteria：7/7 passing
- Dataset validation：PASS，无 warning
- Stock universe：12 tickers
- Equal-weight backtest：4.77% cumulative return，-1.37% max drawdown，Sharpe 2.44（无换手，gross=net，slippage=0）
- Decision-weighted backtest：gross 8.65% → net 8.46%，base cost 0.171% + slippage 0.0075% = total 0.1786%，12 rebalances
- Worst stress scenario：`tech_ai_drawdown`，-7.46%
- OpenRouter smoke test：`openai/gpt-oss-20b:free`，`llm_review.used=true`

## 后续可选增强（Round 5 候选）

这些不是最终提交阻塞项，适合答辩时作为 future work：

1. ~~接入缓存式真实行情 CSV adapter。~~（Round 4 已打通 Yahoo/Stooq 真实行情链路 + 缓存 + 离线 fallback）
2. 接入 Alpha Vantage/Finnhub 新闻缓存文件（real 数据集目前仍复用离线新闻）。
3. 接入 SEC company facts 的基本面抽取脚本（real 数据集目前仍复用离线基本面）。
4. ~~给 decision-weighted backtest 加入交易成本、滑点和换手惩罚。~~（Round 2/3 完成）
5. 将凸性冲击升级为平方根（square-root）冲击并加入 bid-ask 价差项。
6. 基于真实数据生成新的 benchmark cases，使 15 个用例也能跑在真实价格上。
7. 录制 1-2 分钟 demo video，展示 `--task all`、`--source real`、dashboard 和 OpenRouter smoke test。
