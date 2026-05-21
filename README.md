# 面向日频模拟交易的多 Agent 股票决策支持系统

这是课程项目的中期 minimal version。目标不是真实自动交易，而是在离线、可复现的小型样例上跑通 proposal 中的关键组件，证明后续四周继续扩展为真实数据 + 更完整 benchmark 是可行的。

## 当前已实现内容

- 多 Agent 流程：市场信息、新闻情绪、基本面、风险管理、最终决策。
- OpenRouter LLM 复核：有 `OPENROUTER_API_KEY` 时调用 `openrouter/free`，由免费模型对结构化 Agent 输出进行最终审阅。
- 三类任务：单股票分析、候选股票筛选、小型股票池调仓。
- baseline 对比：简单技术指标规则、无风险管理的 ensemble。
- benchmark 输出：成功标准检查、风险提示数量、候选区分度、调仓约束检查。
- 离线样例数据：`AAPL/MSFT/TSLA/NVDA` 的价格、新闻、基本面和组合约束。
- 当前进度记录：`docs/PROGRESS.md`。
- 最终版本路线图：`docs/FINAL_ROADMAP.md`。

## 快速运行

建议先初始化项目虚拟环境。Windows PowerShell 中运行：

```powershell
.\scripts\setup_env.ps1
```

这个脚本会创建 `.venv`、以 editable 方式安装当前项目，并运行单元测试。

也可以手动运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\run_demo.py --task all --llm auto
```

如果要启用真实 LLM 调用，先在当前 PowerShell 会话设置 OpenRouter key：

```powershell
$env:OPENROUTER_API_KEY="你的 OpenRouter key"
python scripts\run_demo.py --task single --ticker AAPL --llm required
```

默认模型是 `openrouter/free`。如需指定某个免费模型，可设置：

```powershell
$env:OPENROUTER_MODEL="meta-llama/llama-3.2-3b-instruct:free"
```

`--llm auto` 会在有 key 时调用 LLM、没有 key 时回退到规则版；`--llm required` 会在 LLM 调用失败时直接报错，适合中期演示前验证“确实调用了模型”；`--llm off` 用于离线测试。

运行后会生成：

- `reports/single_analysis.json`
- `reports/candidate_screening.json`
- `reports/rebalance.json`
- `reports/benchmark_results.json`
- `reports/benchmark_results.md`

## 常用命令

```powershell
# 单股票分析
.\.venv\Scripts\python.exe scripts\run_demo.py --task single --ticker AAPL --as-of 2026-05-19 --llm auto

# 候选股票筛选
.\.venv\Scripts\python.exe scripts\run_demo.py --task screen --tickers AAPL,MSFT,TSLA,NVDA

# 调仓建议
.\.venv\Scripts\python.exe scripts\run_demo.py --task rebalance --tickers AAPL,MSFT,TSLA,NVDA

# benchmark 对比
.\.venv\Scripts\python.exe scripts\run_demo.py --task benchmark --llm auto
```

## PyCharm 运行

项目已包含 PyCharm 配置：

- Interpreter: `.venv\Scripts\python.exe`
- Run configuration: `Run Demo All`
- Test configuration: `Run Unit Tests`

如果 PyCharm 已经打开过项目，请在 IDE 中点击 `File -> Reload All from Disk`，或关闭后重新打开 `C:\Users\modi2023\Desktop\大模型project`。然后选择右上角的 `Run Demo All` 运行。

如果右下角或运行配置显示 `No interpreter`，关闭 PyCharm 后重新打开项目。解释器已注册为：

```text
Python 3.11 (stock-agent-course-project)
C:\Users\modi2023\Desktop\大模型project\.venv\Scripts\python.exe
```

仍未出现时，在 `Settings -> Project -> Python Interpreter -> Add Interpreter -> Existing` 手动选择上面的 `python.exe`。

## 项目结构

```text
data/sample/              离线样例数据和组合约束
docs/                     中期报告草稿、AI 协作上下文、后续计划
reports/                  demo 和 benchmark 输出
scripts/run_demo.py       命令行入口
src/stock_agent/          多 Agent 原型实现
tests/                    单元测试
```

## 中期交付判断

这个版本已经覆盖老师要求的“尝试完成 minimal version 或至少实现关键组件”：

- 可运行：`run_demo.py` 可以端到端输出结果。
- 可解释：每个最终建议都保留各 Agent 的中间结论、证据和风险提示。
- LLM Agent：有 OpenRouter key 时，系统会把规则 Agent 的结构化结果交给免费 LLM 做保守复核，并记录实际使用的模型名。
- 可验证：`tests/` 和 `reports/benchmark_results.md` 检查三类任务是否满足预定义成功标准。
- 可扩展：数据加载层已和 Agent 逻辑分离，后续可以替换为 Kaggle/Alpha Vantage/SEC 数据。

本系统只用于课程研究和模拟交易，不构成投资建议。
