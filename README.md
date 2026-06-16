# 面向日频模拟交易的多 Agent 股票决策支持系统

这是一个课程项目原型，目标是构建可复现、可解释、可评估的多 Agent 股票决策支持系统。系统不会连接真实券商账户，也不构成投资建议；它用于在离线数据和可选 LLM 复核条件下完成三类任务：单股分析、候选股票筛选、小型组合调仓。

当前版本已经从中期 minimal version 推进到 final project prototype：

- 数据集：`data/processed/` 提供 12 支股票、60 个交易日的离线 OHLCV、新闻事件、基本面和组合约束数据。
- Benchmark：`data/benchmark/cases.json` 固定 15 个用例，包括 10 个单股分析、2 个股票池筛选、3 个调仓场景。
- Agent：市场信息、新闻情绪、基本面、风险管理、决策 Agent，以及可选 OpenRouter LLM 复核 Agent。
- Baseline：技术规则 baseline、无风险管理 ensemble baseline、direct LLM/single-agent baseline。
- 回测指标：equal-weight 辅助回测，输出累计收益、年化收益、最大回撤、Sharpe ratio。
- 报告：运行后生成 JSON 详情、Markdown 摘要和静态 HTML dashboard，其中 final benchmark 当前 15/15 通过。

## 快速运行

Windows PowerShell：

```powershell
.\scripts\setup_env.ps1
```

如果想手动初始化：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

运行最终版本 benchmark：

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task final --llm off
```

运行全部任务并生成所有报告：

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

常用任务：

```powershell
# 单股分析
.\.venv\Scripts\python.exe scripts\run_demo.py --task single --ticker NVDA --llm off

# 候选池筛选
.\.venv\Scripts\python.exe scripts\run_demo.py --task screen --tickers AAPL,MSFT,NVDA,TSLA,AMD,WMT --llm off

# 组合调仓
.\.venv\Scripts\python.exe scripts\run_demo.py --task rebalance --llm off

# baseline + backtest 对比
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --llm off
```

## OpenRouter API

没有 API key 时，系统会自动使用离线规则结果，保证测试和 benchmark 可复现。要启用真实 LLM 调用，在 PowerShell 里设置：

```powershell
$env:OPENROUTER_API_KEY="你的 OpenRouter key"
$env:OPENROUTER_MODEL="openrouter/free"
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --llm required
```

`--llm auto`：有 key 就调用 OpenRouter，没有 key 就 fallback。
`--llm required`：强制调用 OpenRouter，调用失败会报错。
`--llm off`：完全离线，适合测试和复现。

不要把真实 API key 写进代码或提交到 GitHub。

## 输出文件

运行 `--task all` 后会生成：

- `reports/single_analysis.json`
- `reports/candidate_screening.json`
- `reports/rebalance.json`
- `reports/benchmark_results.json`
- `reports/benchmark_results.md`
- `reports/final_benchmark_results.json`
- `reports/final_benchmark_results.md`
- `reports/final_dashboard.html`

## Final submission materials

- Final report source/PDF: `llm_course_project_report_template/final_report.tex`, `llm_course_project_report_template/final_report.pdf`
- Presentation source/PDF: `llm_course_project_report_template/final_presentation.tex`, `llm_course_project_report_template/final_presentation.pdf`
- Benchmark summary: `reports/final_benchmark_results.md`
- Static dashboard: `reports/final_dashboard.html`

仓库默认提交 Markdown/HTML 摘要，JSON 详情作为本地生成产物保留在 `.gitignore` 中。

## PyCharm 运行

建议直接打开项目目录：

```text
C:\Users\modi2023\Desktop\大模型project
```

解释器选择：

```text
C:\Users\modi2023\Desktop\大模型project\.venv\Scripts\python.exe
```

如果 PyCharm 显示 `No interpreter`，进入：

```text
Settings -> Project -> Python Interpreter -> Add Interpreter -> Existing
```

然后选择上面的 `python.exe`。如果项目树又变成 Desktop，关闭 PyCharm 后从 `File -> Open` 重新打开 `大模型project` 目录。

## 项目结构

```text
data/sample/              中期 minimal sample 数据
data/processed/           final version 离线处理后数据
data/benchmark/           固定 benchmark case suite
docs/                     项目计划、进度、AI 协作上下文、报告草稿
reports/                  benchmark Markdown/HTML 摘要和本地 JSON 详情
scripts/generate_final_data.py  生成 final 离线数据集
scripts/run_demo.py       CLI 运行入口
src/stock_agent/          多 Agent 系统实现
tests/                    单元测试和 final benchmark 测试
```

## 当前验证结果

已通过：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm off
```

当前结果：

- 单元测试：6/6 通过。
- Final benchmark：15/15 cases 通过。
- 股票池规模：12 支，满足 10-20 支股票要求。
- 风控调仓：3 个 portfolio cases 均满足持仓、现金和交易约束。
- Equal-weight backtest：已输出累计收益、年化收益、最大回撤和 Sharpe ratio。

## 多人协作

推荐流程：

```powershell
git clone https://github.com/modi20230416/stock_agent.git
cd stock_agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

组员协作时建议每个人从 `main` 新建自己的分支：

```powershell
git checkout -b feature/your-task-name
```

完成后提交并 push，再在 GitHub 上开 Pull Request。不要提交 `.env`、真实 API key、`.venv` 或大型本地 JSON 报告。
