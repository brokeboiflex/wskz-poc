# Observed routing policy correction

User requested fixing missing calls and analysis of the completed failure report.
Reuse the approved observed transport-only method, one case at a time, inspecting
its response before the next. No full benchmark, model change, retries, tool
execution or mail. Keep the minimal schema and inference settings from
../english-minimal-500; change only the system prompt to prompt.txt initially.
This explicitly makes other a real catch-all destination and defines exclusive
company responsibilities. No example copies a corpus message.

Prerequisites: current API/Ollama containers and Qwen3 4B weights. Requests use
OpenAI-compatible /v1/chat/completions via the existing HTTP probe. Each attempt
has an exclusive request checkpoint. Do not replay existing files. Keep aggregate
outcomes and failure details only; successes are inspected live, not retained raw.
Commands: `.venv/bin/python docs/evidence/2026-09-26/routing-policy-fix/check.py CASE`.
First inspect representative missing cases 401,405,406,475,481,485,487 and routing
boundaries 97,109,151,201,273,465,474, plus IT control 393. Inspect before advancing.
No automatic expansion to the 500 corpus. A prompt cannot enforce native calls;
Ollama tool_choice support remains an independent server limitation.

Application verification uses the existing described schema (preserving Laya),
not the experimental minimal one. After rebuilding only api, use model.env
(Qwen4B, temperature0), enable MODEL_TRACE for synthetic cases401,475,201,
and run the existing verification/e2e.py once per case. Inspect correlated
request/response, parsed calls, delivery and MIME before the next case. Store
full traces only on failure and result metadata on success. Restore tracing off.

```sh
MODEL_TRACE=true docker compose --env-file docs/evidence/2026-09-26/routing-policy-fix/model.env up -d --no-deps --wait api
.venv/bin/python verification/e2e.py --cases docs/evidence/2026-09-26/routing-policy-fix/app-401.json
# Read correlated logs and MIME before the next separately selected case.
MODEL_TRACE=false docker compose --env-file docs/evidence/2026-09-26/routing-policy-fix/model.env up -d --no-deps --wait api
```

## Results and recovery

15 selected transport requests:15 native calls,14 correct routes,1 wrong route
(case474: vague current message still follows resolved leave history to payroll).
All seven selected previous missing-call cases returned native other calls.
This is diagnostic reuse of known cases, not held-out accuracy or a full rerun.
Full failure details are in failures.jsonl; successful raw outputs were read live
and not saved. Each started file preserves the exact request and each result file
is the checkpoint. Do not replay them.

The application change is SYSTEM_PROMPT only; schema, validation, LangChain agent
and delivery remain unchanged. 81 router, SDK-wire, Laya and architecture tests
passed. Fresh critic found no scope/genericness blocker and flagged the remaining
history error, schema difference and absence of server-enforced calls.

Read-only application inspection command (after each single-case E2E):
`.venv/bin/python docs/evidence/2026-09-26/routing-policy-fix/inspect_app.py CASE`.
It checks one correlated request, one native response, validated parsed call and
one delivery. The existing E2E script checks recipient, Reply-To, original body,
Message-ID and duplicate capture. Failure traces only are retained.

Application verification also passed3/3 selected cases401,475,201 through the
real LangChain agent and unchanged described schema: one native call and one
Mailpit email each, correct recipient, Reply-To and original body. Correlated
wire/parsed/delivery events were inspected before advancing. Active API uses
Qwen3 4B at temperature0; normal tracing restored off after inspection.
