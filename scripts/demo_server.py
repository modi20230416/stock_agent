"""Zero-dependency interactive demo web app for the multi-agent stock system.

Run a local web server that serves an interactive front end and calls the
real ``StockDecisionSystem`` pipeline on each request. Designed for recording
a short demo video: click a task, watch the multi-agent intermediate results,
ranking, rebalance and backtest render live in the browser.

Only the Python standard library is used (``http.server``), consistent with
the rest of the project. No external web framework is required.

Examples (PowerShell):

    .\\.venv\\Scripts\\python.exe scripts\\demo_server.py
    .\\.venv\\Scripts\\python.exe scripts\\demo_server.py --source real --llm off --port 8000

Then open http://127.0.0.1:8000 in a browser.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stock_agent.data_loader import validate_dataset
from stock_agent.pipeline import StockDecisionSystem

STATE: dict[str, object] = {}


def _data_dir(source: str, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    mapping = {
        "processed": ROOT / "data" / "processed",
        "sample": ROOT / "data" / "sample",
        "real": ROOT / "data" / "real",
    }
    chosen = mapping.get(source, mapping["processed"])
    if not chosen.exists():
        return ROOT / "data" / "processed"
    return chosen


INDEX_HTML = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>多 Agent 股票决策支持系统 - Demo</title>
<style>
  :root {
    --bg:#0f1420; --panel:#171e2e; --panel2:#1f2940; --ink:#e6ebf5; --muted:#8a97b1;
    --line:#2a3550; --accent:#4c8dff; --buy:#34c759; --sell:#ff5b5b; --hold:#ffb020;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.55 -apple-system,Segoe UI,Arial,sans-serif; }
  header { padding:20px 28px; border-bottom:1px solid var(--line); background:var(--panel); }
  header h1 { margin:0; font-size:20px; }
  header .sub { color:var(--muted); font-size:13px; margin-top:4px; }
  main { max-width:1180px; margin:0 auto; padding:22px 18px 60px; }
  .controls { display:flex; flex-wrap:wrap; gap:10px; align-items:center;
    background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px; margin-bottom:18px; }
  .controls label { color:var(--muted); font-size:12px; margin-right:4px; }
  input, select { background:var(--panel2); color:var(--ink); border:1px solid var(--line);
    border-radius:7px; padding:7px 9px; font-size:14px; }
  input { width:130px; } .wide { width:340px; }
  button { background:var(--accent); color:#fff; border:0; border-radius:7px;
    padding:8px 14px; font-size:14px; cursor:pointer; }
  button.ghost { background:var(--panel2); border:1px solid var(--line); color:var(--ink); }
  button:hover { filter:brightness(1.08); }
  .tabs { display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; }
  .tabs button { background:var(--panel2); border:1px solid var(--line); color:var(--muted); }
  .tabs button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
  section.card { background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:16px; margin-bottom:16px; }
  h2 { font-size:15px; margin:0 0 12px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
  .pill { display:inline-block; padding:3px 12px; border-radius:999px; font-weight:700; font-size:13px; }
  .BUY { background:rgba(52,199,89,.15); color:var(--buy); }
  .SELL { background:rgba(255,91,91,.15); color:var(--sell); }
  .HOLD { background:rgba(255,176,32,.15); color:var(--hold); }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }
  .metric { background:var(--panel2); border:1px solid var(--line); border-radius:8px; padding:11px; }
  .metric .l { color:var(--muted); font-size:11px; text-transform:uppercase; }
  .metric .v { font-size:20px; font-weight:700; margin-top:4px; }
  .agents { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; }
  .agent { background:var(--panel2); border:1px solid var(--line); border-radius:9px; padding:12px; }
  .agent h3 { margin:0 0 6px; font-size:13px; color:var(--accent); }
  .agent .score { font-size:12px; color:var(--muted); }
  .agent ul { margin:8px 0 0; padding-left:18px; font-size:13px; color:var(--ink); }
  .agent .warn { color:var(--hold); }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { padding:8px 7px; border-bottom:1px solid var(--line); text-align:left; }
  th { color:var(--muted); font-size:11px; text-transform:uppercase; }
  ul.reasons { margin:0; padding-left:18px; }
  .muted { color:var(--muted); }
  .loading { color:var(--accent); }
  pre { background:var(--panel2); border:1px solid var(--line); border-radius:8px;
    padding:12px; overflow:auto; font-size:12px; max-height:320px; }
</style>
</head>
<body>
<header>
  <h1>面向日频模拟交易的多 Agent 股票决策支持系统</h1>
  <div class="sub">Interactive demo · 离线确定性数据 · 不构成投资建议</div>
</header>
<main>
  <div class="controls">
    <span><label>数据源</label><select id="source">
      <option value="processed">processed</option>
      <option value="sample">sample</option>
      <option value="real">real</option>
    </select></span>
    <span><label>日期</label><input id="asof" value="2026-05-19"></span>
    <span><label>单股</label><input id="ticker" value="NVDA"></span>
    <span><label>股票池</label><input class="wide" id="pool" value="AAPL,MSFT,NVDA,TSLA,AMD,WMT"></span>
    <button class="ghost" id="reload">切换数据源</button>
    <span id="dsinfo" class="muted"></span>
  </div>

  <div class="tabs">
    <button data-tab="single" class="active">单股分析</button>
    <button data-tab="screen">候选筛选</button>
    <button data-tab="rebalance">组合调仓</button>
    <button data-tab="benchmark">Benchmark + 回测</button>
  </div>

  <div id="output"><section class="card"><span class="muted">选择任务并点击运行。</span></section></div>
</main>

<script>
const DEFAULT_SOURCE = "__DEFAULT_SOURCE__";
const $ = s => document.querySelector(s);
const out = $('#output');
let activeTab = 'single';

document.querySelectorAll('.tabs button').forEach(b => {
  b.onclick = () => {
    document.querySelectorAll('.tabs button').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    activeTab = b.dataset.tab;
    run();
  };
});
$('#reload').onclick = () => loadInfo().then(run);
['asof','ticker','pool','source'].forEach(id => $('#'+id).addEventListener('change', run));

function params() {
  return new URLSearchParams({
    source: $('#source').value, as_of: $('#asof').value,
    ticker: $('#ticker').value, pool: $('#pool').value,
  });
}
function pill(a){return `<span class="pill ${a}">${a}</span>`;}
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

function agentCard(name, r){
  const ev = (r.evidence||[]).map(e=>`<li>${esc(e)}</li>`).join('');
  const wn = (r.warnings||[]).map(e=>`<li class="warn">${esc(e)}</li>`).join('');
  return `<div class="agent"><h3>${esc(name)}</h3>
    <div class="score">score ${r.score} · conf ${r.confidence}</div>
    <div style="margin-top:6px">${esc(r.summary||'')}</div>
    <ul>${ev}${wn}</ul></div>`;
}

function renderSingle(d){
  const ar = d.agent_results||{};
  const agents = Object.keys(ar).map(k=>agentCard(k,ar[k])).join('');
  const reasons = (d.rationale||[]).map(r=>`<li>${esc(r)}</li>`).join('');
  const risks = (d.risk_warnings||[]).map(r=>`<li class="warn">${esc(r)}</li>`).join('');
  const llm = d.llm_review && d.llm_review.used ? `<div class="muted">LLM 复核已启用</div>`
    : `<div class="muted">LLM 复核：离线规则模式</div>`;
  out.innerHTML = `
    <section class="card"><h2>最终决策 · ${esc(d.ticker)} @ ${esc(d.as_of)}</h2>
      <div class="grid">
        <div class="metric"><div class="l">建议</div><div class="v">${pill(d.action)}</div></div>
        <div class="metric"><div class="l">综合得分</div><div class="v">${d.score}</div></div>
        <div class="metric"><div class="l">置信度</div><div class="v">${d.confidence}</div></div>
      </div>${llm}</section>
    <section class="card"><h2>支持理由</h2><ul class="reasons">${reasons}</ul></section>
    <section class="card"><h2>风险提示</h2><ul class="reasons">${risks}</ul></section>
    <section class="card"><h2>多 Agent 中间结果</h2><div class="agents">${agents}</div></section>`;
}

function renderScreen(d){
  const rows = d.ranking.map(r=>`<tr><td>${r.rank}</td><td><b>${esc(r.ticker)}</b></td>
    <td>${pill(r.action)}</td><td>${r.score}</td><td>${r.confidence}</td>
    <td class="muted">${esc(r.top_reason||'')}</td></tr>`).join('');
  out.innerHTML = `<section class="card"><h2>候选股票筛选 @ ${esc(d.as_of)}</h2>
    <table><thead><tr><th>#</th><th>股票</th><th>建议</th><th>得分</th><th>置信</th><th>首要理由</th></tr></thead>
    <tbody>${rows}</tbody></table></section>`;
}

function renderRebalance(d){
  const tw = d.target_weights||{}, tr = d.trades||{};
  const rows = Object.keys(tw).sort().map(k=>{
    const t = tr[k]||0; const sign = t>0?'+':'';
    return `<tr><td><b>${esc(k)}</b></td><td>${(tw[k]*100).toFixed(2)}%</td>
      <td>${sign}${(t*100).toFixed(2)}%</td></tr>`;}).join('');
  const warns = (d.warnings||[]).map(w=>`<li class="warn">${esc(w)}</li>`).join('') || '<li class="muted">无</li>';
  out.innerHTML = `<section class="card"><h2>组合调仓建议 @ ${esc(d.as_of)}</h2>
    <table><thead><tr><th>资产</th><th>目标权重</th><th>调仓</th></tr></thead><tbody>${rows}</tbody></table></section>
    <section class="card"><h2>约束检查 / 风控提示</h2><ul class="reasons">${warns}</ul></section>`;
}

function renderBenchmark(d){
  const c = d.success_criteria||{};
  const crit = Object.keys(c).map(k=>`<li>${c[k]?'✅':'❌'} ${esc(k.replace(/_/g,' '))}</li>`).join('');
  const eq = d.equal_weight_backtest||{}, dw = d.decision_weighted_backtest||{};
  out.innerHTML = `
    <section class="card"><h2>成功标准</h2><ul class="reasons">${crit}</ul></section>
    <section class="card"><h2>Equal-Weight 回测</h2><div class="grid">
      <div class="metric"><div class="l">累计收益</div><div class="v">${(eq.cumulative_return*100||0).toFixed(2)}%</div></div>
      <div class="metric"><div class="l">最大回撤</div><div class="v">${(eq.max_drawdown*100||0).toFixed(2)}%</div></div>
      <div class="metric"><div class="l">Sharpe</div><div class="v">${(eq.sharpe_ratio||0).toFixed(2)}</div></div>
    </div></section>
    <section class="card"><h2>Decision-Weighted 回测（成本+滑点感知）</h2><div class="grid">
      <div class="metric"><div class="l">Gross 收益</div><div class="v">${(dw.gross_cumulative_return*100||0).toFixed(2)}%</div></div>
      <div class="metric"><div class="l">Net 收益</div><div class="v">${(dw.net_cumulative_return*100||0).toFixed(2)}%</div></div>
      <div class="metric"><div class="l">交易成本</div><div class="v">${(dw.total_transaction_cost*100||0).toFixed(3)}%</div></div>
      <div class="metric"><div class="l">滑点/冲击</div><div class="v">${(dw.total_slippage*100||0).toFixed(3)}%</div></div>
      <div class="metric"><div class="l">调仓次数</div><div class="v">${dw.rebalance_count||0}</div></div>
      <div class="metric"><div class="l">Sharpe</div><div class="v">${(dw.sharpe_ratio||0).toFixed(2)}</div></div>
    </div></section>`;
}

async function run(){
  out.innerHTML = `<section class="card"><span class="loading">运行中…</span></section>`;
  try {
    const res = await fetch('/api/'+activeTab+'?'+params().toString());
    const d = await res.json();
    if (d.error){ out.innerHTML = `<section class="card"><span class="warn">${esc(d.error)}</span></section>`; return; }
    if (activeTab==='single') renderSingle(d);
    else if (activeTab==='screen') renderScreen(d);
    else if (activeTab==='rebalance') renderRebalance(d);
    else renderBenchmark(d);
  } catch(e){ out.innerHTML = `<section class="card"><span class="warn">请求失败: ${esc(e)}</span></section>`; }
}

async function loadInfo(){
  try {
    const res = await fetch('/api/info?source='+$('#source').value);
    const d = await res.json();
    $('#dsinfo').textContent = `数据集: ${d.data_dir.split(/[\\\\/]/).pop()} · ${d.tickers} 支股票 · ${d.price_rows} 行 · LLM ${d.llm}`;
  } catch(e){ $('#dsinfo').textContent = ''; }
}

$('#source').value = DEFAULT_SOURCE;
loadInfo().then(run);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quieter console for demo recording
        return

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _system(self, source: str) -> StockDecisionSystem:
        key = f"{source}"
        if key not in STATE:
            data_dir = _data_dir(source, STATE.get("explicit_dir"))
            STATE[key] = StockDecisionSystem.from_data_dir(data_dir, use_llm=STATE["llm"])
            STATE[f"{key}__dir"] = str(data_dir)
        return STATE[key]  # type: ignore[return-value]

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            default_source = str(STATE.get("default_source", "processed"))
            body = INDEX_HTML.replace("__DEFAULT_SOURCE__", default_source).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if not parsed.path.startswith("/api/"):
            self._send_json({"error": "not found"}, 404)
            return

        q = parse_qs(parsed.query)
        source = (q.get("source", ["processed"])[0])
        as_of = q.get("as_of", ["2026-05-19"])[0]
        ticker = q.get("ticker", ["NVDA"])[0]
        pool = [t.strip().upper() for t in q.get("pool", [""])[0].split(",") if t.strip()]

        try:
            system = self._system(source)
            endpoint = parsed.path[len("/api/"):]
            if endpoint == "info":
                payload = validate_dataset(
                    system.prices, system.news, system.fundamentals, system.portfolio
                )
                self._send_json(
                    {
                        "data_dir": STATE.get(f"{source}__dir", ""),
                        "tickers": payload["counts"]["tickers"],
                        "price_rows": payload["counts"]["prices"],
                        "llm": STATE["llm"],
                    }
                )
            elif endpoint == "single":
                self._send_json(system.analyze_single(ticker, as_of).to_dict())
            elif endpoint == "screen":
                self._send_json(
                    {"as_of": as_of, "ranking": system.screen_candidates(pool or None, as_of)}
                )
            elif endpoint == "rebalance":
                self._send_json(system.rebalance(pool or None, as_of).to_dict())
            elif endpoint == "benchmark":
                self._send_json(system.benchmark(pool or None, as_of))
            else:
                self._send_json({"error": f"unknown endpoint: {endpoint}"}, 404)
        except Exception as exc:  # surface errors to the UI
            self._send_json({"error": f"{type(exc).__name__}: {exc}"}, 500)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive demo web server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--source", default="processed", choices=["processed", "sample", "real"])
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--llm", default="off", choices=["auto", "required", "off"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    STATE["llm"] = args.llm
    STATE["explicit_dir"] = args.data_dir
    STATE["default_source"] = args.source
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Demo server running at {url}")
    print(f"Default source: {args.source} · LLM: {args.llm}")
    print("Open the URL in a browser, then Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping demo server.")
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
