# Authorized failed-case check after native Gemma repair

Completed: Gemma146/147 correct,0 wrong routes,1 missing native call;
Qwen133/147 correct,14 wrong routes,0 protocol errors. Both offline audits pass.
Qwen outcomes exactly match its earlier run. Gemma case434 returned tool-like
plain text instead of native `tool_calls`; it was recorded once, without retry.
[Results](RESULTS_E2B.md), [failure details](FAILURES_E2B.md),
[audit](audit-e2b.json), [preservation](preservation-audit.json).

The user requested this run on 2026-09-26: “Ok so failed cases check now?”
This explicitly resumes evaluation of the same 147 selected failed cases on the
newly applied `0.34.4-poc.gemma-native.2` backend. It does not resume all 500 cases.
The preceding comparison remains immutable; this directory starts both models
from case 1 because the backend changed. Run Qwen, then Gemma on the same backend.

Follow the existing observed procedure in
[PROCEED.md](../failed-cases-comparison/PROCEED.md): identical case order, prompt,
minimal schema, temperature0, top_p0.8, max_tokens1024, reasoning_effort=none,
stream=false. Byte-identical frozen inputs are copied here, with their existing
hashes. The model is the only request difference. No retries, tuning, returned
tool execution, email or application changes. Success metadata and failure-only
raw evidence are retained, as previously requested.

Prerequisites: Docker, healthy patched Ollama, existing model volume, and the API
container as HTTP transport. API/mailer readiness is unnecessary for this
transport-only check; no delivery calls are made. Management metadata in
`backend-e2b.json` verifies installed model digests, backend image and resources.
`preserved-before.json` freezes historical evidence and the generic agent.

Run from the standalone PoC root:

```sh
python3 docs/evidence/2026-09-26/failed-cases-patched/compare.py qwen
python3 docs/evidence/2026-09-26/failed-cases-patched/compare.py gemma
```

Run serially. Inspect each failure's full input/raw response and every ten-case
summary before manually entering `continue`. Never automatically acknowledge
review gates. Inspect logs and stop on infrastructure errors; do not score those
as model routing errors. No diagnostic logprobs flag is used in these frozen
requests. Keep the same Docker resources, backend and model parameters throughout.

Each model's `outcomes.jsonl`, `failures.jsonl`, `summary.json`, numbered started
markers and `reviews.jsonl` are checkpoints. The same command skips completed
cases, reviews an unresolved last gate, and refuses an unresolved started marker.
Do not remove markers or replay a request whose completion is unknown.

After both complete and every review is recorded:

```sh
python3 docs/evidence/2026-09-26/failed-cases-patched/audit.py
```

The existing offline audit is reused with only its expected backend identity
updated. It checks all 147 cases per model, exact failure requests, native-call
validation, summaries, timings and review gates. Outputs: `audit-e2b.json`,
`RESULTS_E2B.md`, `FAILURES_E2B.md`. Separately verify every hash in
`preserved-before.json` and save final runtime identity/logs.

The patched backend remains installed after the test. The old instruction to
restore0.13.5 belongs to the earlier experiment and is superseded by the user's
approved patch deployment. This measures recovery on a selected failure set,
not general accuracy, every agent workflow or SMTP/application acceptance.

## Observed execution notes

The original 147-case source and its stopped Gemma31/Qwen147 results remain
unchanged. Both new runs completed all147 cases; all28 Qwen and16 Gemma review
gates were manually inspected. No HTTP/infrastructure failure occurred.

The lingering Gemma model from the prior smoke check was unloaded after Qwen
case5; Qwen was unloaded before starting Gemma. No weights were removed or
resources changed. Timings include cold loading, cache effects and transport,
so these are not controlled latency benchmarks. Normal Ollama remains healthy
on the patched image. No application model configuration was changed.

The sole Gemma failure is original case434, `other` with resolved leave history
and a current private kettle-exchange request. Its response is ordinary text:
`send_department_email{department:<|"|>other<|"|>}` with `finish_reason=stop`.
The intended department appears in text but this does not constitute a native
call and is counted as failure. No response repair, retry or prompt tuning ran.
This check does not diagnose that remaining failure's generation mechanism.
