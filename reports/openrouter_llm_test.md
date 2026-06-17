# OpenRouter LLM Smoke Test

- Date: 2026-06-17
- Model: `openai/gpt-oss-20b:free`
- Command shape: `scripts/run_demo.py --task single --ticker AAPL --llm required`
- API key handling: provided through the process environment only; not written to `.env`, source code, reports, or Git.

## Result

- Ticker: AAPL
- Final action: HOLD
- Final score: 0.5033
- Final confidence: 0.6729
- `llm_review.used`: true
- LLM rationale items: 3
- LLM risk warning items: 2
- Note: LLM-generated rationale text may vary slightly between calls; this record captures the default-model smoke test that verified `llm_review.used=true`.

This confirms that the OpenRouter path can make a live free-model request, parse the model JSON response, and merge the review back into the stock decision output.
