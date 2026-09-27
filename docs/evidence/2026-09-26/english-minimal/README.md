# English prompt and minimal schema

User approved the proposed English prompt/minimal schema and failure-only records.
Reuse three diagnostic cases394,235,393 at temperature0 on patched Ollama/Qwen4B.
No bulk benchmark or application change. No tool execution or mail.
Run each separately from repository root:
`.venv/bin/python docs/evidence/2026-09-26/english-minimal/test.py 394`
Inspect output before running235, then393. Prerequisites: API container/httpx and
Ollama running with the model installed. test.py reuses saved original messages
and sampling settings; only prompt/schema differ from the previous simple test.
Exact tested configuration: prompt.txt/tool.json. Persist detailed failed inputs,
raw responses and reason in failures.jsonl only. summary.json retains totals and
completed IDs to prevent replay; lock files mark attempted requests. On interruption
inspect before any resumption; never retry uncertain requests automatically.

Result:3/3 valid native calls and correct departments,0 failures. failures.jsonl
is empty. Successful raw responses were observed but not persisted per user
instruction. No emails or production changes. This small sample is not a
reliability estimate; case235 improves relative to the previous Polish prompt.
