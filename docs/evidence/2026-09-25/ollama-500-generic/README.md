# Interrupted Ollama evaluation

## Latest checkpoint: stopped by user

The reauthorized run was stopped on the user's explicit instruction. Run
`2279baae02cc` has 241 completed records: 176 correct routes, 52 wrong departments,
and 13 HTTP 502 `invalid_tool_call` responses. All 13 matching API log reasons
are `missing_call`, not malformed JSON or invalid arguments. Of the 100 HR
messages, 41 went to help desk. These are partial, class-ordered results, not a
500-case accuracy score. No full-run MIME audit was performed. An in-flight
request at cancellation may finish independently; do not replay it automatically.
The E2E container was stopped (exit 137); results and API logs were preserved in
`docs/evidence/2026-09-25/ollama-500-generic/`. Do not resume without a new explicit
request. No model, prompt, schema or corpus changes were made during this run.

Approach, prerequisites and repeat commands: [BENCHMARK_APPROACH.md](../../../BENCHMARK_APPROACH.md).
`runtime.json` records configuration and agent hash; `results.jsonl` preserves
completed requests and corpus checksum. `audit.py` requires a completed 500-case
run and was not executed against this partial run. Do not claim a completed audit.
