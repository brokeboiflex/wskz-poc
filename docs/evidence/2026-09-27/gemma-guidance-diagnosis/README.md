# Minimal guidance and missing native-call diagnosis

User authorized a minimal separate guidance block for the 23 wrong routes to other, and investigation of the five missing native calls. This continues the individual observed diagnostic procedure in ../../2026-09-26/gemma-integration-audit/APPROACH.md and the frozen evaluation method in ../../2026-09-26/gemma-patched-500/README.md. Preserve historical artifacts; no full benchmark or model/backend repair is part of this task.

The application SYSTEM_PROMPT receives only a short <guidance> block explaining existing specialist responsibilities. No model-specific instructions, case IDs, response repair or retry code. Preserve tool schema and all other prompt text.

Diagnosis uses the original unchanged five requests, before any guidance, through /v1/chat/completions. Inspect pinned native parser/grammar and Ollama request forwarding. Launch the existing bundled native server and patched libllama-common in the normal Ollama container on internal port18081, with the same official template, weights and sampling as the previously approved integration diagnostic. Save logprobs on non-streaming native requests to distinguish model tokens from parser output; Ollama internally streams and cannot expose this combination. No returned tool is executed. Inspect every result before the next request. A single required-tool control may isolate lazy grammar versus required grammar; do not silently deploy it.

Prerequisites: Docker, API transport container, patched Ollama, installed Gemma E2B Q4, pinned local source snapshots. Scripts and exact launch/probe commands are saved beside this file before execution. Attempts refuse overwrite. On interruption inspect the attempt and PID before resuming; never replay an unknown outcome automatically. Stop only the recorded task-owned native PID, preserve normal Ollama and weights.

After diagnosis, validate the prompt edit with existing router/wire tests and a fresh independent critic. Focused guidance validation, if performed, uses the same prior minimal-schema request, only adds the new guidance block, and records all requests/responses without tool execution. No general accuracy improvement is claimed without a full subsequent evaluation.

## Completed commands and checkpoints

[Report](REPORT.md) records results and limits; [audit](audit.json) verifies retained evidence. Source prompt changed only by `guidance.txt`. The full frozen prompt and selected cases are hashed in `freeze.json`.

From the PoC root, focused guidance check (already complete; do not replay):

```sh
python3 -u docs/evidence/2026-09-27/gemma-guidance-diagnosis/check-guidance.py gemma
```

The runner saves every request/raw response, outcome/start marker and manual review, pauses on each failure and every ten cases, and resumes only an inspected completed prefix. It refuses unresolved started markers. It uses the same existing single-POST OpenAI-compatible probe; it never executes returned calls.

Native diagnosis launch (already completed and stopped):

```sh
docker cp docs/evidence/2026-09-27/gemma-guidance-diagnosis/gemma4-small.jinja message-router-ollama-1:/tmp/gemma-missing-diagnosis.jinja
docker cp docs/evidence/2026-09-27/gemma-guidance-diagnosis/launch-native.sh message-router-ollama-1:/tmp/gemma-missing-diagnosis.sh
docker exec -d message-router-ollama-1 sh -c 'sh /tmp/gemma-missing-diagnosis.sh > /tmp/gemma-missing-diagnosis.log 2>&1'
python3 docs/evidence/2026-09-27/gemma-guidance-diagnosis/probe.py tokens-434 http://ollama:18081/v1/chat/completions docs/evidence/2026-09-27/gemma-guidance-diagnosis/requests/434-tokens.json
```

The example label is an existing completed attempt and refuses overwrite. The other first-pass labels were `tokens-034`, `tokens-101`, `tokens-288`, `tokens-404`; the required control was `required-434`. Each used its corresponding file under `requests/`. Read every result before another diagnostic; no automatic loop or replay.

The second native launch used `launch-matched.sh`, copied to `/tmp/gemma-missing-matched.sh`, with log `/tmp/gemma-missing-matched.log`. It matches the captured normal Ollama runner arguments except internal listener address/port, equivalent file-based template, and debug verbosity. Its request files encode the normal Ollama forwarding options. Labels: `matched-034`, `matched-101`, `matched-288`, `matched-404`, `matched-stream-034`. Normal-Ollama checks used `ollama-034`, `ollama-required-434` and render-only `render-034` at `http://ollama:11434/v1/chat/completions`.

Do not run both loaded native/Ollama models concurrently. Before the second launch, `docker compose exec -T ollama ollama stop gemma4:e2b` unloaded the model without deleting weights. Stop only the PID recorded in `/tmp/gemma-missing-diagnosis.pid` or `/tmp/gemma-missing-matched.pid`, after checking `/proc/PID/cmdline` contains the task's port18081. Copy logs before stopping. Both task processes were stopped; the normal patched service remains healthy.

Validation, without inference:

```sh
.venv/bin/pytest -q tests/test_router.py tests/test_openai_wire.py tests/test_laya.py tests/test_architecture.py
python3 docs/evidence/2026-09-27/gemma-guidance-diagnosis/audit.py
```

No new evaluation or backend repair is implied by these completed checkpoints.
