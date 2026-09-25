# Qwen/Ollama integration repair, 2026-09-25

The user requested a working integration, then stopped the 500-case benchmark
and challenged the custom orchestration and workarounds. The final approach is
LangChain's agent factory with a compatible Ollama release. No benchmark restart.

## Actual upstream defect and version choice

The actual prompt on Ollama 0.17.7 reproduced
[issue #14601](https://github.com/ollama/ollama/issues/14601): Qwen's bare
`{{ .Function }}` rendered a Go struct instead of a JSON tool definition.
A valid OpenAI HTTP payload therefore did not mean the model saw a valid schema.

The upstream [bisect and render reproduction](https://github.com/ollama/ollama/issues/14601#issuecomment-5636865937)
identify **0.13.5 as working and 0.14.0 as the regression**. The proposed
[fix #18391](https://github.com/ollama/ollama/pull/18391) is still unmerged.
The affected implementation also remains in stable 0.34.4. Merely selecting the
latest release is not a demonstrated fix.

Compose pins **ollama/ollama:0.13.5**, with the stock qwen3:1.7b template and weights.
Bootstrap downloads missing weights and performs one native readiness tool call.
It does not rewrite model templates, patch Ollama, or retry malformed calls.
An invalid readiness response blocks API startup.

## Application flow

`RoutingService -> LangChainRoutingAgent -> create_agent(ChatOpenAI, tool)`.
LangChain binds the tool, invokes the model, and executes the registered tool.
The tool's `return_direct=True` ends the graph immediately after delivery.
One `wrap_model_call` middleware enforces the inference timeout and checks that
there is exactly one complete call to the allowed tool with a valid department.
These checks run before any mailer side effect, including for parallel calls.

There is no custom agent loop, corrective feedback prompt, or model retry.
Invalid output returns `invalid_tool_call`; provider errors and inference timeout
return `model_unavailable`. Mailer errors propagate without another inference or
send. Pydantic describes and validates data; LangChain runs the agent.

The tool uses standard JSON Schema: a string enum with described singleton
alternatives in anyOf. No x-choice extension is sent to any provider. Laya's
adapter translates those standard descriptions into the same classifier question
and ordered criteria. The application retains the original sender/body and maps
the chosen department to its mailbox.

## Necessary provider configuration

Pinned ChatOpenAI rewrites ordinary `max_tokens` to `max_completion_tokens`, while
Ollama 0.13.5 reads `max_tokens`. The client's `extra_body` supplies the configured
wire field after that rewrite. `MODEL_TOKEN_LIMIT_FIELD` allows either field.
See [LangChain #30113](https://github.com/langchain-ai/langchain/issues/30113) and
[Ollama 0.13.5 conversion](https://github.com/ollama/ollama/blob/v0.13.5/openai/openai.go).

Ollama defaults explicitly select non-thinking mode (`reasoning_effort=none`),
temperature 0.7 and top_p 0.8, following the
[Qwen3 model card](https://huggingface.co/Qwen/Qwen3-1.7B/blob/main/README.md).
Empty reasoning/sampling env values omit those fields for other providers.
Bootstrap uses the same values as the API. Its single cold-start call has a 600s
socket timeout and rejects late responses; this is not hard cancellation of a
slow-dripping synchronous HTTP body.

The earlier token-exhaustion heuristic was removed after the strict neutrality
review. Token counts do not establish whether a valid tool call was truncated.
Only explicit length termination and malformed/invalid calls are rejected. If a
provider hides its termination reason, the application cannot reconstruct it.
There is no provider-specific normalization or heuristic in the agent.

References for framework behavior: [create_agent](https://docs.langchain.com/oss/python/langchain/agents),
[model-call middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom).
Pinned factory source was inspected for tool binding, error propagation and the
`return_direct` exit path; real SDK tests exercise this flow.

## Repeat and checkpoint

Read `APPROACH.md` for prerequisites and the public-registry Docker client
workaround on this host. From this project root:

```sh
.venv/bin/python -m pip install -r services/router/requirements.txt -r tests/requirements.txt
.venv/bin/ruff check services tests verification
.venv/bin/ruff format --check services tests verification
.venv/bin/pytest -q
docker compose --profile test build api model-init tests
docker compose up -d
docker compose --profile test run --no-deps --rm tests
curl --fail http://localhost:8000/health/ready
```

The ordinary 15-case smoke remains available in `verification/cases.json`.
Do not resume the stopped 500-case run. No external mail, model training,
production credentials, message deletion, or volume deletion is involved.
After an uncertain SMTP outcome, inspect its request ID instead of repeating
POST. Every new public request creates a new delivery ID.

During diagnosis, a template patch and up-to-three-attempt correction loop were
tried, then removed following the user's simplification request. The stock model was
restored by re-pulling its tag after Docker recovery; its manifest exactly matches
the original. Historical
before/after renders and interrupted outputs remain under
`docs/evidence/2026-09-25/tool-wiring/`. `template-patch-partial.jsonl` is the
cancelled run of that earlier implementation, not a score for the final code.
The 500-case audit helpers are historical, unexecuted helpers for a complete run.
Final focused checks and remaining limitations are in `VERIFICATION.md`.

Earlier checkpoint: 116 host/container tests, valid stock-template rendering on 0.13.5,
and 5/5 live smoke messages through Mailpit, including Reply-To/body/recipient
checks. The fresh critic found no blocking code issue. Services remain running.
Repeat the focused smoke, if needed, with:

```sh
.venv/bin/python verification/e2e.py \
  --cases docs/evidence/2026-09-25/tool-wiring/focused-smoke-cases.json
```

This creates five new synthetic emails. It is not a general accuracy benchmark.

## Provider-neutrality follow-up

The user requested removal of both accommodations identified by a fresh critic.
The agent no longer reads token usage or emits custom schema extensions. No
provider/model-name branches or additional compatibility proxy were introduced.
References: [standard schema composition](https://json-schema.org/understanding-json-schema/reference/combining),
[LangChain tool schemas](https://docs.langchain.com/oss/python/langchain/tools).

120 host/container tests pass. Real SDK serialization tests change URL, key,
model and token-field selection solely through env and verify a complete call
at the token limit sends exactly once. Laya tests verify the exact same question,
criteria and original message after translating the standard schema. These
controlled responses prove our client/adapter contract, not every remote model.
Deployment still requires a matching /models entry and Chat Completions tool
support, including the standard schema keywords used here.

Live smoke uses the same five existing cases, first with .env.ollama-example,
then .env.laya-example, then restores Ollama. The source/case checksum is unchanged.
Store new results in docs/evidence/2026-09-25/generic-agent/; no 500-case rerun.

Final follow-up evidence in `docs/evidence/2026-09-25/generic-agent/`:
120 container tests; Ollama 5/5 correct routes; Laya 4/5 correct routes with all
five delivered. Laya repeats its previously recorded computer-to-IT mistake.
All ten captured messages passed independent MIME/Reply-To/body/duplicate checks.
The stock Ollama render preserves the standard anyOf descriptions. A fresh critic
found no blockers and independently passed 101 tests. Ollama is restored and
healthy; Laya containers are stopped. No remote paid provider was called.

To repeat this small integration check with a selected env file:

```sh
docker compose --env-file .env.laya-example up -d --wait --wait-timeout 300
.venv/bin/python verification/e2e.py \
  --cases docs/evidence/2026-09-25/tool-wiring/focused-smoke-cases.json
docker compose --env-file .env.laya-example stop laya-adapter laya-runtime
docker compose --env-file .env.ollama-example up -d --wait --wait-timeout 180
```

The failed Laya score is preserved; do not tune on these examples or describe
successful delivery as correct classification. `audit_smoke.py` reads the saved
runs and Mailpit without sending or modifying messages.

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
