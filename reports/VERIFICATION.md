# 项目验证报告

更新日期：2026-06-17（Round 4 之后）

本报告基于**实际运行**（而非仅文档声明）记录验证结论。所有命令在离线模式 `--llm off` 下运行，结果可复现。

## 1. 验证命令

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task final --llm off
```

## 2. 实测结果

- 单元测试：16/16 passing（`Ran 16 tests ... OK`，含真实数据链路测试）。
- Final benchmark：`passed_cases=15 / total_cases=15`，`pass_rate=1.0`。
- Final criteria：`all_cases_pass=true`，全部 PASS。
- Dataset validation：PASS，12 tickers，720 price rows，60 price dates，无 warning。
- Equal-weight backtest：累计收益 4.77%，最大回撤 -1.37%，Sharpe 2.44。
- Decision-weighted backtest（成本+滑点感知）：gross 8.65% → net 8.46%，base cost 0.171% + slippage 0.0075% = total 0.1786%，Sharpe 4.82，12 rebalances。
- 多 Agent 中间结果（market/news/fundamental/risk/llm_review）结构化输出正常。

## 3. 对照 proposal 第 6 节预定义成功标准

| Proposal 成功标准 | 状态 | 证据 |
| --- | --- | --- |
| 单股分析输出建议 + 理由 + 至少一条风险提示 | PASS | `test_single_stock_has_required_fields` |
| 候选筛选能区分不同标的 | PASS | screen cases 2/2，score 有差异 |
| 调仓不违反持仓/现金/交易约束 | PASS | rebalance cases 3/3，权重和=100% |
| 信息冲突/数据不完整时显式表达不确定性 | PASS | DecisionAgent 跨 Agent 冲突检测 |
| 输出可追溯的中间 Agent 结果 | PASS | `agent_results` 完整输出 |
| Baseline 对比（单 Agent / 无风控 / 技术规则） | PASS | technical / no-risk / direct-LLM 均实现 |
| 离线可复现（无 API key 仍可运行） | PASS | `--llm off` 完整运行 |

**结论：项目已完整达到并超出 proposal 设计目标。**

## 4. 超出 proposal 的增强

- 15-case 固定 benchmark suite（10 single + 2 screen + 3 rebalance）。
- Equal-weight 与 decision-weighted 两套回测。
- 组合压力测试（5 个情景）。
- Dataset schema validation。
- 无依赖静态 HTML dashboard。
- 真实 OpenRouter 免费模型 smoke test。

## 5. 迭代优化对比（回测真实性逐轮增强）

| 指标 | Round 1（无摩擦） | Round 2（固定费率） | Round 3（费率+滑点冲击） |
| --- | --- | --- | --- |
| Decision-weighted cumulative return | 8.65% | gross 8.65% / net 8.47% | gross 8.65% / net 8.46% |
| Base cost | 未建模 | 0.171% | 0.171% |
| Slippage / 市场冲击 | 未建模 | 未建模 | 0.0075% |
| Total transaction cost | 未建模 | 0.171% | 0.1786% |
| 单元测试数量 | 7/7 | 8/8 | 9/9 |
| Final benchmark | 15/15 | 15/15 | 15/15 |

- Round 2 让动态回测从理想化无摩擦升级为考虑固定费率交易成本与换手惩罚。交易成本率可通过 constraints 的 `transaction_cost` 配置。
- Round 3 进一步引入市场冲击滑点：`slippage = impact_coefficient * turnover^2 * portfolio_volatility`，使成本随换手规模与组合波动率非线性放大。冲击系数可通过 constraints 的 `impact_coefficient` 配置（默认 0.05）。
- 成本恒等式 `total = base + slippage` 在测试中断言，且每轮均保证 `net ≤ gross`，逻辑自洽。equal-weight 无换手时 slippage=0，向后兼容。

## 6. Round 4 验证（真实数据链路）

打通真实行情数据链路，并实测验证：

| 验证项 | 结果 |
| --- | --- |
| 联网拉取真实日频价格（Yahoo Finance 主源） | PASS，12/12 tickers，各 114 行（2026 起）/ 缓存含约 500 交易日 |
| vendor CSV 归一化（Stooq/Yahoo/Adj Close 别名、日期窗口、缺列报错） | PASS，`test_data_sources.py` 7 项全过 |
| 磁盘缓存写入 | PASS，`data/cache/<TICKER>.csv` |
| 离线 fallback（无网络从缓存重建） | PASS，`--offline` 重建 1368/1503 行 |
| 真实数据集 validate | PASS，12 tickers，1368 price rows，无缺失新闻/基本面 |
| 真实数据单股分析 | PASS，NVDA HOLD score=0.2029，含跨 Agent 冲突检测 |
| 真实数据 equal-weight backtest（AAPL/MSFT/NVDA） | 累计收益 7.6%，最大回撤 -6.63%，Sharpe 0.64（比合成数据更贴近现实） |
| 确定性 final benchmark 无回归 | PASS，仍 15/15 |

数据链路：Yahoo Finance chart JSON（主，无 key）→ 失败时降级 Stooq CSV → 归一化 → 缓存 → `data/real`；离线模式直接复用缓存。纯标准库实现，向后兼容（默认仍走 processed）。`data/cache`、`data/real` 为可复现产物，已 gitignore。

命令：

```powershell
.\.venv\Scripts\python.exe scripts\ingest_real_data.py --refresh
.\.venv\Scripts\python.exe scripts\ingest_real_data.py --offline
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --source real --llm off
```
