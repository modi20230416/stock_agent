# Multi-Agent Stock Decision Support System

面向日频模拟交易的多 Agent 股票决策支持系统。该项目是课程项目原型，用于验证“多 Agent + 可选 LLM 复核”在股票分析、候选筛选和小型组合调仓中的可行性。系统不连接真实券商账户，不自动下单，也不构成投资建议。

GitHub 仓库：[https://github.com/modi20230416/stock_agent](https://github.com/modi20230416/stock_agent)

## 项目状态

当前版本已达到并超过 proposal 目标，适合作为最终项目提交与导师审批材料。

| 项目 | 当前结果 |
| --- | --- |
| Python 测试 | 16/16 passing |
| Final benchmark | 15/15 cases passing |
| Final criteria | 7/7 passing |
| 离线复现 | 支持，无 API key 也可完整运行 |
| 股票池规模 | 12 支股票，满足 proposal 的 10-20 支要求 |
| 数据校验 | PASS，12 tickers，720 price rows，60 price dates，无 warning |
| 动态回测 | Decision-weighted backtest，12 次调仓 |
| 成本建模 | 交易成本 + 滑点/市场冲击 |
| 压力测试 | 5 个组合压力场景 |
| 真实数据链路 | Yahoo Finance 主源，Stooq fallback，支持缓存与离线重建 |
| LLM 复核 | OpenRouter 可选；无 key 时自动走离线规则 |

核心指标见 [reports/final_benchmark_results.md](reports/final_benchmark_results.md)，完整验证记录见 [reports/VERIFICATION.md](reports/VERIFICATION.md)。

## 导师审批入口

建议按以下顺序检查：

1. [reports/VERIFICATION.md](reports/VERIFICATION.md)：最终验证命令、测试结果、proposal 成功标准对照。
2. [reports/final_benchmark_results.md](reports/final_benchmark_results.md)：15 个固定 benchmark case 的通过情况。
3. [reports/final_dashboard.html](reports/final_dashboard.html)：静态 dashboard，可直接用浏览器打开。
4. [llm_course_project_report_template/final_report.pdf](llm_course_project_report_template/final_report.pdf)：最终报告 PDF。
5. [llm_course_project_report_template/final_presentation.pdf](llm_course_project_report_template/final_presentation.pdf)：最终展示 slides。
6. [docs/ITERATION_OPTIMIZATION_PLAN.md](docs/ITERATION_OPTIMIZATION_PLAN.md)：从 minimal version 到最终增强版的迭代记录。

## 一键复现

### Windows PowerShell

```powershell
git clone https://github.com/modi20230416/stock_agent.git
cd stock_agent

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task final --llm off
```

如果本机 `python` 不是 3.11+，可改用：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

### macOS / Linux

```bash
git clone https://github.com/modi20230416/stock_agent.git
cd stock_agent

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e .

python -m unittest discover -s tests
python scripts/run_demo.py --task final --llm off
```

### 生成全部报告

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

生成结果位于 `reports/`。其中 Markdown/HTML 摘要适合提交和审阅；JSON 文件为本地生成详情，默认不提交到 GitHub。

## 常用运行命令

所有命令默认使用 `data/processed` 离线确定性数据集，便于复现。

```powershell
# 数据集 schema 与覆盖率校验
.\.venv\Scripts\python.exe scripts\run_demo.py --task validate --llm off

# 单股分析
.\.venv\Scripts\python.exe scripts\run_demo.py --task single --ticker NVDA --llm off

# 候选股票筛选
.\.venv\Scripts\python.exe scripts\run_demo.py --task screen --tickers AAPL,MSFT,NVDA,TSLA,AMD,WMT --llm off

# 组合调仓
.\.venv\Scripts\python.exe scripts\run_demo.py --task rebalance --llm off

# baseline、回测、压力测试综合评估
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --llm off

# 固定 15-case final benchmark
.\.venv\Scripts\python.exe scripts\run_demo.py --task final --llm off
```

可选参数：

| 参数 | 说明 |
| --- | --- |
| `--source processed` | 默认离线最终数据集，推荐用于复现和评分 |
| `--source sample` | 中期 minimal sample 数据 |
| `--source real` | 使用 `scripts/ingest_real_data.py` 构建出的真实价格数据集 |
| `--llm off` | 完全离线，推荐用于测试 |
| `--llm auto` | 有 OpenRouter key 时启用 LLM，否则自动 fallback |
| `--llm required` | 强制调用 OpenRouter，失败则报错 |

## 交互式 Demo

项目提供零额外依赖的本地 web demo，便于导师演示或录制视频。后端使用 Python 标准库 `http.server`。

```powershell
.\.venv\Scripts\python.exe scripts\demo_server.py
```

启动后打开：

```text
http://127.0.0.1:8000
```

可指定端口、数据源和 LLM 模式：

```powershell
.\.venv\Scripts\python.exe scripts\demo_server.py --port 8000 --source real --llm off
```

页面包含四个标签页：单股分析、候选筛选、组合调仓、Benchmark + 回测。

## 真实数据链路

默认评分与复现使用 `data/processed`。如需展示真实行情，可构建 `data/real`：

```powershell
# 联网拉取真实日频价格并写入缓存
.\.venv\Scripts\python.exe scripts\ingest_real_data.py --refresh

# 无网络时从缓存重建 data/real
.\.venv\Scripts\python.exe scripts\ingest_real_data.py --offline

# 指定股票池和开始日期
.\.venv\Scripts\python.exe scripts\ingest_real_data.py --refresh --tickers AAPL,MSFT,NVDA --start 2024-01-01
```

构建后运行：

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task validate --source real --llm off
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --source real --llm off
```

说明：

- 真实价格来自 Yahoo Finance chart JSON；失败时降级到 Stooq CSV。
- `data/cache/` 和 `data/real/` 是可复现生成物，已加入 `.gitignore`，不提交到 GitHub。
- real 数据集目前使用真实价格；新闻与基本面仍复用离线数据，因为真实新闻/基本面通常需要付费 API。

## OpenRouter LLM

LLM 是可选增强，不是复现项目的必要条件。没有 API key 时，系统仍可通过 `--llm off` 完整运行。

PowerShell 设置方式：

```powershell
$env:OPENROUTER_API_KEY="你的 OpenRouter key"
$env:OPENROUTER_MODEL="openai/gpt-oss-20b:free"
.\.venv\Scripts\python.exe scripts\run_demo.py --task single --ticker AAPL --llm required
```

注意：

- 不要把真实 API key 写入代码、README、报告或提交到 GitHub。
- `.env` 与 `.env.*` 已被 `.gitignore` 忽略。
- 代码读取的是环境变量；如果使用 IDE，需要在运行配置中设置环境变量。

## 项目结构

```text
data/sample/                         中期 minimal sample 数据
data/processed/                      最终离线确定性数据集
data/benchmark/cases.json            固定 15-case benchmark suite
data/cache/                          真实行情下载缓存，gitignore
data/real/                           真实行情构建数据集，gitignore

src/stock_agent/agents.py            market/news/fundamental/risk/decision agents
src/stock_agent/backtest.py          equal-weight、decision-weighted、成本与滑点回测
src/stock_agent/baselines.py         baseline 对比方法
src/stock_agent/data_loader.py       数据读取与 schema validation
src/stock_agent/data_sources.py      Yahoo/Stooq 真实行情链路
src/stock_agent/evaluator.py         Markdown/HTML 报告生成
src/stock_agent/llm.py               OpenRouter LLM adapter
src/stock_agent/pipeline.py          StockDecisionSystem 主流程

scripts/run_demo.py                  CLI 入口
scripts/demo_server.py               交互式 demo web server
scripts/ingest_real_data.py          构建 data/real
scripts/generate_final_data.py       生成离线 processed 数据
scripts/setup_env.ps1                Windows 环境初始化脚本

tests/                               单元测试与 benchmark 测试
reports/                             可审阅 Markdown/HTML 报告
docs/                                计划、进度、AI 协作上下文、迭代记录
llm_course_project_report_template/  最终报告与 slides
```

## 组员协作流程

首次下载：

```powershell
git clone https://github.com/modi20230416/stock_agent.git
cd stock_agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

开始新任务前：

```powershell
git checkout main
git pull origin main
git checkout -b feature/your-task-name
```

完成修改后：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task final --llm off

git status
git add <changed-files>
git commit -m "Describe your change"
git push -u origin feature/your-task-name
```

然后在 GitHub 上发起 Pull Request，让其他组员 review 后合并。除非团队明确同意，不建议直接在 `main` 上开发。

### 提交前检查清单

- `python -m unittest discover -s tests` 通过。
- `scripts/run_demo.py --task final --llm off` 仍为 15/15。
- 没有提交 `.env`、真实 API key、`.venv/`、`data/cache/`、`data/real/`。
- 如果改了输出格式，同时更新 `README.md`、`docs/ITERATION_OPTIMIZATION_PLAN.md` 或相关报告。
- 如果新增功能，补充对应测试。

## PyCharm 使用

推荐直接打开仓库根目录，而不是桌面目录：

```text
stock_agent/
```

解释器选择：

```text
<repo>\.venv\Scripts\python.exe
```

如果显示 `No interpreter`：

```text
Settings -> Project -> Python Interpreter -> Add Interpreter -> Existing
```

选择 `.venv\Scripts\python.exe` 即可。若项目树错误显示成桌面，关闭 PyCharm 后通过 `File -> Open` 重新打开仓库根目录。

## 技术说明

- Python 版本：3.11+
- 运行时依赖：当前核心项目只使用 Python 标准库。
- 安装方式：`pip install -e .`
- 网络依赖：仅 `scripts/ingest_real_data.py --refresh` 和 OpenRouter LLM 调用需要网络。
- 复现默认路径：`--llm off` + `--source processed`。

## 风险与边界

本项目仅用于课程研究与工程原型展示。输出中的 BUY/SELL/HOLD 是算法演示结果，不应作为真实投资建议。真实数据链路只接入公开日频价格，且新闻/基本面仍采用离线样例数据；若未来用于更严肃的研究，需要接入合规数据源、交易成本校准、样本外评估和更严格的风险控制。
