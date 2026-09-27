# English minimal schema: full500 observed evaluation

User explicitly approved500 after the three-case diagnostic and requested only
failure details saved. Same patched Ollama/Qwen4B, temperature0, top_p0.8,
reasoning_effort=none, max_tokens1024. Exact prompt/schema in prompt.txt/tool.json.
Frozen corpus SHA is enforced by run.py. No labels sent to model. Each case uses
one OpenAI-compatible POST via existing API container HTTP transport; no retries,
no application changes, tool execution or mail. This measures model protocol and
routing only, not full API/SMTP acceptance. Existing bulk evidence is untouched.

Command: `.venv/bin/python -u docs/evidence/2026-09-26/english-minimal-500/run.py`.
Prerequisites: running API/Ollama and installed4B model, host Python. The script
refuses an existing started.json. It validates every raw response before advancing,
prints/saves full failures and pauses at each failure/every10 for operator review.
failures.jsonl holds all failed inputs/raw outputs/reasons. summary.json holds
counts only; checkpoint/reviews prevent unnoticed skips/replays. Successful raw
responses are deliberately not retained. On interruption inspect checkpoint and
process state; no automatic resume or replay. Final audit checks failure totals
against summary; reliability limits include250 paired families and prior exposure.

## Completed result

500/500 completed: 353 correct (70.6%), 109 wrong routes, 38 missing native
calls. Native calls: 462/500. HR 99/100, payroll 68/100, help desk 59/100,
IT 100/100, other 27/100 correct. All 38 protocol failures occurred in other:
the model returned plain labels, JSON text, explanations or clarification
requests instead of native tool calls. This does not establish a parser bug;
no raw generated token stream was captured. The simplified setup is not a
complete fix and has not replaced the application prompt/schema.

[FAILURES.md](FAILURES.md) lists failures only with inputs and assistant outputs.
[failures.jsonl](failures.jsonl) retains full requests and raw HTTP responses.
[summary.json](summary.json) contains aggregate results.
[audit.json](audit.json) records the offline consistency audit of all 147 failures,
frozen inputs/settings, per-class totals and 182 operator review gates.
Success counts can only be checked against aggregates because their raw responses
were intentionally not saved. No delivery or MIME claims apply to this run.

Repeat the offline audit without model requests:

```sh
.venv/bin/python docs/evidence/2026-09-26/english-minimal-500/audit.py
```

Do not rerun run.py over this evidence. It refuses the existing start marker;
any future inference run needs explicit authorization and a fresh evidence path.
