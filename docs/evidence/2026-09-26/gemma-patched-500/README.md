# Gemma full 500-case run

Completed full Gemma check (2026-09-27 local time): **471/500 correct (94.2%)**, 24 wrong routes and 5 missing native calls. All 29 failures retain full requests and raw responses, plus individual debug bundles. All 77 manual review gates and offline audits pass. The earlier 147 outcomes reproduce exactly. No retries, tuning, tool execution or mail. Previous evidence, generic agent and Compose are unchanged. This is synthetic model transport/routing evidence, not full application acceptance.

[Results](RESULTS.md), [all failures](FAILURES.md), [audit](audit-e2b.json), [preservation audit](preservation-audit.json).

Authorized 2026-09-26: "Ok run all 500 through gemma, save all failures so we can debug them easily".
Same observed method as [the completed 147-case run](../failed-cases-patched/README.md), expanded to the original full corpus. Gemma only; each case once. Prior evidence is preserved.

## Inputs and prerequisites

Running Docker Compose API container for HTTP transport, healthy Ollama `0.34.4-poc.gemma-native.2`, installed `gemma4:e2b` Q4_K_M, Python 3. Same patched image and weights as the preceding check. `backend-e2b.json` captures runtime identity and resource limits.

`cases.json` is the byte-identical frozen `verification/benchmark/cases-500.json`: 500 Polish messages, 250 paired families, 100 per department. Prompt, minimal tool schema and request template are byte-identical to the previous run. SHA-256 values in `freeze.json`. Temperature 0, top_p 0.8, max_tokens 1024, reasoning_effort none, stream false. Send only message text, never labels or rationales. No retries, tuning, tool execution or mail.

## Execute and checkpoint

From the PoC root:

```sh
python3 -u docs/evidence/2026-09-26/gemma-patched-500/run.py gemma
```

The runner reuses the existing OpenAI-compatible HTTP probe at `/v1/chat/completions`. Inspect every failure's full input/raw response and every ten-case gate before manually entering `continue`. Never automatically acknowledge gates. Stop and inspect infrastructure failures before proceeding.

`gemma/outcomes.jsonl` records every result; `gemma/failures.jsonl` saves every failure with its full request, raw HTTP response, stderr, expected/actual department, stable case ID and timing. `gemma/summary.json`, `gemma/reviews.jsonl` and numbered started markers are checkpoints. Successful raw responses are intentionally omitted. Resume with the same command after inspecting checkpoints; completed cases are skipped. An unresolved started marker blocks replay. Never remove it to retry an unknown outcome.

## Offline audit and output

```sh
python3 docs/evidence/2026-09-26/gemma-patched-500/audit.py
```

Checks all 500 unique ordered cases, frozen inputs, backend identity, all saved failure requests/responses, native-call validation, summaries and every manual review gate. Produces `audit-e2b.json`, `RESULTS.md`, `FAILURES.md`. After completion save service logs, verify historical evidence/agent/Compose hashes against `preserved-before.json`, and record final backend identity. No application configuration changes.

This is model transport/routing evidence, not full agent/SMTP acceptance. Prior diagnostic exposure and paired cases limit generalization; success validation relies on outcome metadata because successful raw responses are not saved.

## Debugging artifacts and findings

All failures have separate `failures/NNN/` folders containing `request.json` (exact API payload), `raw-response.txt` (original HTTP probe output), `response.json` (readable response body), `case.json` (full corpus entry and rationale), `outcome.json`, and `stderr.txt`. The audit recreates these files offline from immutable `gemma/failures.jsonl`; it never sends requests. Do not replay cases implicitly.

Missing native calls: **034, 101, 288, 404, 434**. Each is HTTP200 with tool-like plain text and `finish_reason=stop`; all lack native `tool_calls`. Text contains the expected department but remains invalid. The mechanism was not diagnosed by this run. All24 wrong routes are valid native calls:20 HR requests sent to other,1 help-desk request sent to other,2 IT requests sent to other,1 IT request sent to help desk.

No infrastructure failures occurred. All147 overlapping cases match the preceding run. Backend and model settings were unchanged; 784 historical artifact/source hashes passed preservation verification. Successful raw responses remain intentionally unsaved. Median request duration2.356s and total1183.086s include transport/cache effects, not operator review pauses; not a controlled latency benchmark. Directory date follows the start date; completion was2026-09-27 in Europe/Warsaw.
