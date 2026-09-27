# Ollama parser backport

Approved by the user on 2026-09-26. Backport upstream PR17284, commit
72413e584cf98082b0e6159665529552baa4c1b0, onto Ollama0.13.5.
Source and patch checksums are pinned in services/ollama/Dockerfile.
Official runtime image and inference libraries remain unchanged; rebuild the Go
server with upstream parser regression tests and vet. No application changes.

## Execution and recovery

Prerequisites: Docker, network for source/Go dependencies, existing model volume.
Build: `docker compose build ollama`. Save build output in
`docs/evidence/2026-09-26/ollama-backport/build.txt`.
Activate: `docker compose up -d --no-deps --wait ollama`.
Enable API tracing with the existing qwen4b-500/model.env, using --no-deps.
Run only frozen case394 once through verification/e2e.py, saving exact request,
raw response, SDK trace and any MIME. Inspect before another request. Then one
successful control if needed. No bulk benchmark, retries or tool execution from
returned text. Save logs before restoring tracing=false. Existing evidence is
immutable; use new files for deliberate attempts. Rollback with a temporary
Compose override setting ollama.image=ollama/ollama:0.13.5 and --no-build.

## Scope and proper tool calling

The patch returns the original buffered generation when parsing produces zero
calls. Unknown names, malformed JSON and truncated calls stay failures; the
agent must not execute text. This fixes diagnostic data loss, not generation.

A complete server implementation should translate tools and tool_choice into
decoding constraints: declared function names only, arguments conforming to the
supported JSON Schema, and a required call when required/named is requested.
Validate after decoding and return explicit failure on truncation or unsupported
constraints. Honor none/auto/required/named rather than silently ignoring them.
Correct model template rendering and lossless parser finalization are also needed.
This is provider infrastructure work; keep LangChain ChatOpenAI generic.
Schema validity cannot guarantee the semantically correct department.

References: https://github.com/ollama/ollama/pull/17284 and
https://github.com/ollama/ollama/issues/17274.

## Exact focused validation commands

From the repository root, with no active benchmark process:

```sh
MODEL_TRACE=true docker compose --env-file docs/evidence/2026-09-25/qwen4b-500/model.env up -d --no-deps --wait api
cp docs/evidence/2026-09-25/qwen4b-500/case-394.json docs/evidence/2026-09-26/ollama-backport/case-394.json
.venv/bin/python verification/e2e.py --cases docs/evidence/2026-09-26/ollama-backport/case-394.json > docs/evidence/2026-09-26/ollama-backport/case-394-result.jsonl
.venv/bin/python docs/evidence/2026-09-26/ollama-backport/inspect.py case-394
docker compose logs --no-color ollama > docs/evidence/2026-09-26/ollama-backport/ollama.txt
MODEL_TRACE=false docker compose --env-file docs/evidence/2026-09-25/qwen4b-500/model.env up -d --no-deps --wait api
```

A nonzero E2E exit is expected if the recovered output is an invalid call.
Inspect its saved response, not just that exit status. Never overwrite completed
case artifacts on a repeat. inspect.py performs only log/Mailpit reads and checks
wire settings against the previous run, native-call agreement and delivery MIME.

Rollback (does not delete model/mail volumes):

```sh
cat > /tmp/wskz-ollama-rollback.yml <<'YAML'
services:
  ollama:
    image: ollama/ollama:0.13.5
YAML
docker compose -f docker-compose.yml -f /tmp/wskz-ollama-rollback.yml up -d --no-build --no-deps --wait ollama
```

Return to the patched service with the base Compose command and --build. Do not
run model-init during diagnostics: it issues a separate readiness inference.
If Docker Desktop's credential helper stalls on these public images, use a
temporary DOCKER_CONFIG containing auths={} and cliPluginsExtraDirs pointing at
the installed plugins, plus DOCKER_HOST from docker context inspect. No credentials
are needed or copied; keep this host workaround outside repository runtime config.

## Observed result

The patched version reports `0.13.5-poc.17284`. Build passed upstream tools tests
and vet; router suite passed 34 tests, including tool-like text causing no mail.
Case394 now exposes the generated block:

```json
{ "name": "send_department_it", "arguments": { "department": "it" } }
```

The registered name is `send_department_email`. The department was correct;
the invented function name was not. It was returned as content, rejected by the
unchanged agent with HTTP502 invalid_tool_call, and produced zero mail. Same
captured input/settings/schema as the previous run. This confirms the mechanism
for this reproduction, not every earlier empty response.

## Proper prevention, separately from this backport

For this application, an enforced named tool choice plus strict supported schema
should constrain generation to exactly `send_department_email` and a department
from the five allowed values. The model still decides the department. The grammar
must be derived generically from the incoming tools, not hardcoded to our names.
With one tool and no parallel calls, the server should generate one complete call
or signal failure. Budget exhaustion still can prevent completion; it must never
be reported as an ordinary successful stop with missing output.

Implement this in the inference server: preserve the OpenAI tool_choice and
strictness fields, compile the supported schema to the runner's grammar/token
constraints, enforce required/named from the beginning (not only after an optional
tool marker), and validate the parsed result. Reject unsupported strict schemas
or choices explicitly. Auto may legitimately return text; none must prohibit calls.
Strict schema enforcement is stronger than ordinary non-strict function calling.
Prompt instructions, temperature changes and post-generation name substitutions
are not enforcement. Grammar does not fix semantically wrong department choices.

That complete server feature is not included in PR17284 or this backport. The
backport fixes silent loss and gives actionable diagnostics. Our current Ollama
still ignores forced tool_choice, so setting MODEL_TOOL_CHOICE=named alone is
insufficient. Implementing/enabling actual constrained decoding is the next
functional fix; the generic LangChain application need not acquire provider code.
