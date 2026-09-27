# Gemma E2B tool-call investigation

Follow-up isolation is now recorded in
[gemma-integration-audit/REPORT.md](../gemma-integration-audit/REPORT.md): official
template equivalence and three same-request native-engine controls demonstrate
the effect of the tool-name grammar that Ollama's Gemma path bypasses. This
extends the earlier trace below; it does not resume the comparison or certify
full model reliability.

The user stopped the comparison at31/147 and requested the reason for failure.
`stop-e2b.json` records the checkpoint. No bulk resume or retries are authorized.

## Investigation approach

Read the saved request/response pairs, installed model metadata and pinned
Ollama0.34.4 source. Trace OpenAI conversion, actual renderer selection and tool
parsing. Use the server's `debug_render_only: true` template-inspection facility
to capture the exact prompt without generation (`_debug_render_only` is the
actual JSON key). This native endpoint call is
render-only introspection, not model inference; a subsequent render-only request
used the original OpenAI request plus the same debug flag and confirmed the
identical prompt with zero completion tokens. All actual inference remains
OpenAI-compatible. Save the request, response, rendered prompt and source
references. No prompt/schema edits, tool execution, mail or benchmark continuation.

Prerequisites: the existing candidate Ollama and API containers, the saved
`gemma/failures.jsonl` and `backend-e2b.json`. Read these before resuming.
Preserve frozen inputs and stopped outcomes; inspect existing diagnostic files
before repeating any command. Outputs are kept in this directory.

After rendering, one isolated replay of the first failed case with `logprobs=true`
captures generated tokens through the same OpenAI-compatible endpoint. It changes
only diagnostic metadata, not prompt, tools, sampling or thinking. This is a
root-cause probe requested by the user, not a comparison retry or bulk resume.
Save `gemma-token-request.json`, `gemma-token-response.json` and the decoded token
stream. Refuse existing output files so the diagnostic cannot silently replay.

## Confirmed mechanism

The tool definition reaches Gemma correctly, but Gemma generates a department
label in the function-name position. Ollama parses and exposes that undeclared
function name without enforcing the declared tool contract. Application-level
validation correctly rejects it. This is not a damaged download, memory failure,
HTTP failure, missing input schema, truncation or parser renaming of a valid call.

Evidence from the first failed case:

1. `gemma-openai-render-response.json` has zero generated tokens and contains
   `<|tool>declaration:send_department_email{...}` with the required `department`
   property and all five enum choices. Thinking is disabled as requested.
2. The isolated replay differs from the frozen request only by `logprobs=true`.
   Its generated tokens, before tool parsing, are exactly:

   ```text
   <|tool_call>call:human_resources{}<tool_call|><|tool_response>
   ```

3. `gemma-token-response.json` exposes that same name and empty arguments.
   The wrong name is already in generated tokens, so the parser did not invent it.
4. All31 stopped benchmark responses have a department label as function name:
   one `human_resources` and30 `payroll`. In this selected prefix, all31 names
   match the expected class;29 responses also include a department argument and
   two have empty arguments. These are still31 invalid calls, not31 successful
   routes. Only HR/payroll were reached; no general classification claim follows.

### Why the existing patches do not fix this

The installed model configuration (`gemma-installed-config.json`) explicitly sets
`renderer: gemma4` and `parser: gemma4`. This selects Ollama's dedicated rendered
completion path. The running Gemma llama-server process uses `--no-jinja`.
An initial inference from mixed logs that Gemma used native chat was incorrect;
the `peg-native` messages included the separate Qwen runner.

In pinned Ollama0.34.4:

- `server/routes.go`, `usesOllamaRenderedChat`, selects rendered mode for these
  config fields. `ChatHandler` renders tools into the prompt and invokes
  `r.Completion`; it does not pass the tool definitions as a generation constraint.
- `llm/llama_server.go`, `Completion`, only supplies grammar/JSON-schema
  constraints when `Format` is set. This request has no Format. Its tool names
  and department enum are instructions in the prompt, not enforced decoding rules.
- `model/parsers/gemma4.go`, `parseGemma4ToolCall`, takes the text after `call:`
  and before `{` as the function name. It does not reject undeclared function
  names. `openai.ToChatCompletion` consequently labels the result `tool_calls`.
- PR18391 patches generic `template/template.go` JSON serialization. PR17284
  patches generic `tools/tools.go` buffering. Neither changes the Gemma renderer,
  Gemma parser or decoder enforcement. Their passing tests did not verify this
  failure class.

Pinned references:

- https://github.com/ollama/ollama/blob/v0.34.4/server/routes.go
- https://github.com/ollama/ollama/blob/v0.34.4/llm/llama_server.go
- https://github.com/ollama/ollama/blob/v0.34.4/model/renderers/gemma4.go
- https://github.com/ollama/ollama/blob/v0.34.4/model/parsers/gemma4.go
- https://github.com/ollama/ollama/blob/v0.34.4/openai/openai.go

## What a fix must prove

Backend enforcement must constrain the function name to `send_department_email`
and its argument to the declared department enum, while preserving the public
OpenAI-compatible interface and application validation. Simply renaming whatever
function the model returned would conceal this failure and is not a fix.
Rejecting unknown names in the parser improves error reporting but cannot make
the model emit a valid call. A prompt example might mitigate generation behavior;
it is not equivalent to enforcement, and no such change has been tested here.

The exact generation/parsing mechanism is now demonstrated. This does not prove
why these weights prefer the wrong name internally, or that quantization,
non-thinking mode or another prompt is responsible. Do not claim a verified
repair. Start any future repair with this single traced case, including rendered
prompt, generated tokens and parsed call, before considering broader testing.

## Repeat commands and checkpoint

The benchmark remains stopped at31. There is no in-flight request and no automatic
resume. The candidate runtime remains available for diagnosis. Frozen inputs,
the147-case selection and completed Qwen evidence are unchanged.

Inspect saved artifacts first. The original diagnostic commands used the API
container only as an HTTP transport. To reproduce an explicitly requested
render-only check with the saved native render request, from the PoC root:

```sh
set -C
docker compose exec -T api python -c 'import json,sys,httpx; p=json.load(sys.stdin); assert p["_debug_render_only"] is True; r=httpx.post("http://ollama:11434/api/chat",json=p,timeout=60); r.raise_for_status(); print(r.text)' < docs/evidence/2026-09-26/failed-cases-comparison/gemma-render-request.json > docs/evidence/2026-09-26/failed-cases-comparison/gemma-render-repeat.json
```

The one token replay used this command shape with the saved diagnostic request;
it generates a new response and must not be run as an implicit benchmark retry:

```sh
set -C
docker compose exec -T api python -c 'import json,sys,httpx; r=httpx.post("http://ollama:11434/v1/chat/completions",json=json.load(sys.stdin),timeout=180); r.raise_for_status(); print(r.text)' < docs/evidence/2026-09-26/failed-cases-comparison/gemma-token-request.json > docs/evidence/2026-09-26/failed-cases-comparison/gemma-token-repeat.json
```

`diagnosis-audit.json` records the offline checks: unchanged frozen hashes, exactly
one metadata-only diagnostic replay, the declared/generated/parsed names, zero
render-only generation tokens and the durable stop review at31. No mail was sent.
