# Observed model debugging

Authorized by the user on 2026-09-25: read logs, add observability and rerun to
explain failures. OpenAI-compatible inference is a hard constraint. The stopped
500-case benchmark stays stopped.

## Approach

Follow-up LangChain audit: compare the installed decorator and StructuredTool
conversion without inference, then isolate tool presentation on individual
previously observed failures. The diagnostic-only variant uses a plain enum
with category explanations in the argument description and a short function
description. Keep the captured system prompt/model/options unchanged. Use the
existing OpenAI-compatible token probe, inspect each result before another and
never execute its tools. Preserve the production schema/Laya contract during
this investigation. Evidence: `evidence/2026-09-25/langchain-tool-audit/`.
After inspecting those results, check one captured failing request with only
named tool_choice added by ChatOpenAI.bind_tools. Preserve the unchanged tool
schema and inspect the returned tokens; do not assume the server enforces it.

Existing evidence: `evidence/2026-09-25/ollama-500-generic/`. Its 13 missing-call
logs lack raw responses. Capture diagnostics using HTTPX's standard async event
hooks on the existing ChatOpenAI client, plus the agent's parsed response,
validation result and actual delivery outcome. No extra provider client or proxy.
Reference: https://www.python-httpx.org/advanced/event-hooks/.

Keep model, prompt, schema, inference options and recipient policy unchanged
initially. Select individual synthetic cases from the frozen corpus: one known
misroute, one missing-call case, and a successful control. Send each separately
through the public API and inspect its raw/parsed trace and Mailpit before choosing
another case. Additional individual reproductions may isolate the observed failure;
record all attempts, including non-reproductions. Never automatically retry a POST.

The observed missing-call response was empty despite 23 output tokens. The next
diagnostic replays its exact captured request with only standard OpenAI `logprobs`
and `top_logprobs` metadata enabled, using plain HTTP against `/v1/chat/completions`.
It records the response and never executes returned tools. Script and results
remain with the evidence. This distinguishes generated tokens from parsed calls
without introducing a provider-specific client or changing the production agent.

`MODEL_TRACE=true` enables content-bearing JSON trace records in API container
logs. They include serialized OpenAI request/response bodies, request ID, HTTP
status, duration, parsed model output, validation and delivery result. Headers,
API keys in transport headers and URL credentials are excluded. Raw bodies are
preserved, not redacted; never enable this on real messages or credential-bearing
payloads/provider error bodies. Default is false. This diagnostic
mode buffers non-streaming responses and is for synthetic local messages only.

Executed findings: [observed-debug/README.md](evidence/2026-09-25/observed-debug/README.md).
Two observed missing-call reproductions generated a department label as the
function name; the server omitted that invalid call from its API response.

## Commands, artifacts and recovery

Prerequisites: healthy existing Compose services, frozen corpus, host Python
environment and Mailpit on loopback. From the PoC root:

```sh
MODEL_TRACE=true docker compose --env-file .env.ollama-example up -d --build --no-deps api
docker compose logs --follow --no-color api
```

Use the public POST `/api/v1/messages` for one case at a time. Save the input case
ID, original body, response status/body and timestamps before inspecting correlated
logs. Save evidence in `docs/evidence/2026-09-25/observed-debug/`. Expected labels
belong in the inspection report, never the model request. Read Mailpit by request
ID and verify recipient and Reply-To for any successful delivery.

The existing harness can run one selected case (each run intentionally creates
a new request; keep distinct output filenames):

```sh
.venv/bin/python verification/e2e.py \
  --cases docs/evidence/2026-09-25/observed-debug/case-025.json
```

After capturing a wire request, the metadata-only probe can run inside the API
container to reach the configured endpoint using its existing HTTP library:

```sh
docker compose exec -T api sh -c 'cat > /tmp/observed-wire-request.json' \
  < docs/evidence/2026-09-25/observed-debug/case-051-wire-request.json
docker compose exec -T api python - \
  < docs/evidence/2026-09-25/observed-debug/logprobs_probe.py
```

It performs exactly one inference, prints the entire request and raw response,
and never executes the returned tools. `-e DIAGNOSTIC_TOP_LOGPROBS=5` before
`api` adds five alternatives per token instead of the default zero. Only use on
an endpoint supporting standard OpenAI logprobs. Inspect output before another
invocation. Do not change the production agent to depend on logprobs.

Stop on unexplained behavior, inspect the trace and only then choose the next
diagnostic. A terminated client does not prove server cancellation; inspect logs
and captured mail before any deliberate new reproduction. Preserve each attempt
and never overwrite earlier artifacts or delete mail/model volumes.

Restore ordinary logging after saving traces:

```sh
MODEL_TRACE=false docker compose --env-file .env.ollama-example up -d --no-deps api
```

Read this document and the saved findings before resuming. No automatic full-run
resume. Instrumentation tests must check that tracing preserves exact request and
response bodies, correlation across concurrent calls, and excludes credentials.

## Approved routing-policy change and observed replay

The user approved implementation ("Ok do these changes and let’s see"). Shorten
the tool description, move the department policy into the system prompt and
clarify the function-name/argument distinction. Preserve the described enum
alternatives and Laya's exact classifier input. Add MODEL_TOOL_CHOICE with blank
(omit), auto, required or named, using LangChain ModelRequest.override in the
existing middleware. named lets ChatOpenAI serialize the sole registered tool
name. Examples select blank for pinned Ollama, required for Laya and named for
OpenRouter. Unsupported choices are not silently downgraded or retried.

References: [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools),
[custom middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom),
and the installed ModelRequest/agent factory and ChatOpenAI.bind_tools source.

Keep the same qwen3:1.7b model and inference settings to inspect the prompt
change first. Run the existing single-case harness on cases 025, 051, 103 and
001, inspecting the correlated raw request/response and captured MIME after
each. Stop to diagnose any unexplained failure before continuing. Store new
artifacts in evidence/2026-09-25/routing-policy/, never overwrite the earlier
observed-debug evidence. Its copied inspect.py reads current logs and Mailpit
without inference; run it after each case and before recreating the API. If
needed, use the existing metadata-only logprobs probe for an individual failure.
Do not execute tools from token traces. Restore MODEL_TRACE=false afterward.

Reproduction from the PoC root (select one case, then inspect):

```sh
.venv/bin/python verification/e2e.py --cases docs/evidence/2026-09-25/routing-policy/case-025.json
.venv/bin/python docs/evidence/2026-09-25/routing-policy/inspect.py
```

Prerequisites, API build and tracing commands above are unchanged. Completed
case files are checkpoints, not a queue to replay. Preserve separate output
files for each deliberate additional attempt. The full benchmark stays stopped.

## Approved model comparison: Qwen3-4B-Instruct-2507

The user approved checking a different model with logs. Compare the exact
qwen3:4b-instruct-2507-q4_K_M tag through the existing OpenAI-compatible client
on Ollama 0.13.5. Preserve application code, prompt, tool schema and sampling
settings from routing-policy/; only OPENAI_MODEL changes. Keep the stock model
template. If unsupported options prevent inference, capture the error before
considering a separately recorded configuration change. No silent fallback.

Artifacts: evidence/2026-09-25/qwen4b-instruct/. model.env records the complete
public model settings, with no external credentials. Prerequisites: existing
healthy Compose services, Docker storage for the published 2.5 GB weights,
network for downloading and the existing host .venv. Native Ollama CLI is used
only for download and metadata, never inference. Capture model digest, stock
template/parameters and resource metadata.

```sh
docker compose exec -T ollama ollama pull qwen3:4b-instruct-2507-q4_K_M
docker compose exec -T ollama ollama show qwen3:4b-instruct-2507-q4_K_M --modelfile
MODEL_TRACE=true docker compose --env-file docs/evidence/2026-09-25/qwen4b-instruct/model.env up -d --no-deps --wait --wait-timeout 60 api
```

The API image is unchanged. --no-deps prevents an extra unobserved bootstrap
inference: readiness is inspected via /models and the first fully logged public
request. Replay case 025, inspect, then 051, inspect, then 103 and 001 in the same
way. Never run a case loop. Example of one public request and read-only inspection:

```sh
.venv/bin/python verification/e2e.py --cases docs/evidence/2026-09-25/qwen4b-instruct/case-025.json
.venv/bin/python docs/evidence/2026-09-25/qwen4b-instruct/inspect.py
```

Redirect each harness output to its own case-NNN-result.jsonl and the inspection
to inspection.jsonl; preserve API logs before any container recreation. Follow
the existing metadata-only logprobs procedure if a missing call needs diagnosis.
No bulk benchmark, paid API, model-specific application code or tool repair.
Interrupted downloads may resume through pull using preserved volumes. Completed
case artifacts are checkpoints: inspect them instead of automatically replaying.
Capture all outcomes, then turn MODEL_TRACE off and record the final active model.
The run does not automatically promote a model to repository defaults.

## Latest authorization: observed full 500-case run

The user explicitly requested all 500 cases after the 4B comparison. Follow the
latest section of BENCHMARK_APPROACH.md and qwen4b-500/run.py. Serial per-case
trace/MIME audits and operator gates on failures/every ten cases replace the
four-case-only scope for this authorized run. Keep all model/app settings fixed.

## Latest state: user stopped at 190; read-only audit completed

The user stopped the full run. No further inference or test emails. Follow the
latest BENCHMARK_APPROACH.md section and qwen4b-500/FORENSIC_REVIEW.md for the
completed evidence audit. Raw tracing is off; complete service logs are saved.

## Latest checkpoint: stopped at 400

User stopped testing to inspect failures. No further inference. Results: 375 correct,
6 wrong routes, 19 upstream missing calls; 381 live MIME audits passed. See
`docs/evidence/2026-09-25/qwen4b-500/FAILURE_REVIEW.md` (path from repository root).
