# Ollama native Gemma tool integration fix

Applied locally on 2026-09-26: `0.34.4-poc.gemma-native.2`, Linux ARM64.
The normal Ollama service is healthy and its post-promotion check returns
`send_department_email({"department":"human_resources"})` on the first generation.
This fixes the captured initial tool-call defect. It is not full model or PoC acceptance.

## Changes

- Ollama routes its existing small Gemma GGUF renderer/parser metadata through
  native chat with Google's exact pinned template. Renamed models use the same
  metadata. Other renderer families, large Gemma, MLX and selected Go templates
  retain their existing paths. No application model-name branches.
- The matching native Gemma parser preserves its missing `<|"|>` string token.
  Only `libllama-common` is rebuilt from the exact bundled source with Ollama's
  compatibility overlay. The official inference engine, backend libraries,
  models, generic agent, tools and prompt remain unchanged.
- The generic native message adapter now forwards assistant reasoning history.
- Compose reproduces this build, including the existing PR18391/17284 patches.

The first candidate used `--special`. It fixed the tool case but leaked
`<turn|>` into ordinary text, so it was rejected. The final candidate does not
use that flag or strip tokens from responses. It fixes the native preserved-token list.

## Evidence

| Check                                                       | Result                                            |
| ----------------------------------------------------------- | ------------------------------------------------- |
| Go regression on original routing                           | Expected failure: bypasses native grammar         |
| Go server, runner, renderers, parsers, OpenAI tests and vet | Passed                                            |
| Native template/grammar test before delimiter patch         | Expected failure: missing delimiter               |
| Same native test after patch                                | Passed                                            |
| Final-image symbol resolution and loaded library            | Passed on ARM64                                   |
| Original failing Gemma message                              | Valid HR tool call, 506 input / 19 output tokens  |
| Ordinary Gemma response                                     | Exactly `READY`, no protocol marker               |
| Streaming different function                                | `lookup_forecast({"city":"Łódź"})`, SSE completes |
| Qwen control                                                | Valid HR tool call                                |
| Normal Ollama service after promotion                       | Same valid Gemma call, 506 / 19 tokens            |
| Frozen agent and benchmark inputs/checkpoints               | Unchanged; Gemma31 / Qwen147                      |

Every generation was individually observed; no automatic retry, delivery or bulk
benchmark ran. Requests, raw HTTP bodies/SSE, parsed summaries and logs are saved
beside this report. `audit.py` verifies them offline. `provenance.json` records
image, patch and binary hashes. `build-native.log` records the native regression;
`build-2.log` retains the intermediate archive checksum mismatch; the final build
uses the verified full-commit archive checksum. Earlier `build.log` and rejected
candidate evidence remain intact.

## Limits retained

1. The captured diagnostic request contains `logprobs:true`. Ollama's existing
   native adapter internally streams, and llama.cpp rejects tools plus streaming
   logprobs before generating anything. The successful inference request omits
   only that diagnostic flag; messages, schema and sampling settings are identical.
2. A tool-result continuation fixture gives no useful answer on either backend:
   the old backend returns `<|tool_response>`, the patched backend empty content.
   Both generate one token, with identical requests and matching rendered prompts
   after BOS handling. This is an existing failure; its deeper cause was not
   established. The PoC's `return_direct=True` delivery flow does not use continuation.
3. Native Gemma grammar constrains function names and value syntax, not the whole
   argument schema. Generic validation remains required. No universal first-try
   semantic accuracy guarantee follows from this repair.
4. Multimodal Gemma, large Gemma, MLX and other CPU/GPU architectures were not
   newly validated. The native Go conversion tests cover existing media transport.
5. No SMTP/full delivery test ran. API and mailer remain unhealthy because their
   Mailpit dependency is not running; Ollama itself is healthy. Model configuration
   on the application remains Qwen and can still be changed through environment.

Independent review inspected code and actual runtime artifacts and accepted
bounded local promotion for the initial terminal tool call, with these limits.
Temporary validation containers are stopped. The previous image is retained.

Build, checkpoint, replay and rollback instructions:
[OLLAMA_GEMMA_TOOL_FIX.md](../../../OLLAMA_GEMMA_TOOL_FIX.md).
