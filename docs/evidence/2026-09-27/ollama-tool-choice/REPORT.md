# Generic tool-choice transport repair

Applied locally: **Ollama0.34.4-poc.tool-choice.2**. Standard `tool_choice` now crosses OpenAI compatibility decoding, Ollama chat request and native runner transport. The existing native grammar enforces `required`; the application uses its existing `MODEL_TOOL_CHOICE=required` setting. No new application code, model branches, text repair or corrective retries. Previously approved guidance is now deployed in the API container.

## Observed results

All eight previously missing calls passed on their first required request:

| Frozen case | Correct native department |
| ----------- | ------------------------- |
| Original034 | human_resources           |
| Original101 | payroll                   |
| Original288 | help_desk                 |
| Original404 | other                     |
| Original434 | other                     |
| Guidance012 | human_resources           |
| Guidance066 | human_resources           |
| Guidance074 | human_resources           |

For each, the request differs from its saved historical input only by `tool_choice: required`; prompt, schema, weights, sampling and message are unchanged. Offline audit proves exact JSON equality with that single addition. Runtime/cache history is not identical to the earlier500 run.

The same434 under explicit `auto` still emits tool-shaped ordinary text; required, named selection and streaming emit a valid `send_department_email({department:"other"})` native call. This directly verifies the requested backend transport repair through the normal OpenAI-compatible API. The normal promoted Ollama endpoint also passes434. Qwen4B required and auto controls pass. Native none returns no calls; plain no-tools control returns exactly READY; invalid mode and undeclared named tool return HTTP400.

There were19 individually observed HTTP requests, including2 rejected validation requests and1 Qwen control on candidate .1. There were no tool executions, mail sends or automatic retries. The separate post-promotion434 request verifies deployment, not a retry used to rescue a failed test.

## Implementation and review

`services/ollama-candidate/tool-choice.patch` is provider infrastructure, independent of this application's tool names or departments. SHA256: `70dd8f868adc85edcf1ff0f8b2a577ee9de48a52a2dc67bc9893a348b088bbec`.

- Omitted/auto preserve optional-tool behavior.
- Required needs declared tools and forwards required to native decoding.
- Named selection validates declaration membership and forwards only that declared tool with required.
- None removes offered tools and forwards none to native decoding.
- Unsupported rendered required/none requests fail explicitly before inference. They are not silently treated as auto. Existing model execution paths remain unchanged.

Independent review found rendered parsers can emit tool calls even with an empty offered-tool list. Candidate .2 fixes this by rejecting explicit none on unsupported rendered paths; regression covers both native and rendered behavior. Fresh re-review found no remaining local blocker.

The Docker build demonstrated a failing forwarding regression with that field removed, then passed api/openai/llm/server suites, go vet and formatting with the patch restored. Existing native library tests/build were reused unchanged. All81 application/wire/Laya/architecture regressions pass. `audit.py` passes and confirms907 previous evidence files remain byte-identical.

Final running image ID: `sha256:f3d9e1f71a3f6d54ac426206726a3f18b412eece49445cb6230bf60da52119b9`. Image config digest: `sha256:d7afe4c143839560e527e08118f36be1285cd5ad7c634a0cdf131fb514b2cde0`. Runtime version and API configuration/source hash are saved in `promoted-runtime.json`. Qwen4B remains the configured API model. Tests explicitly selected Gemma without changing the application model.

## Limits and operational state

This fixes the supported local native tool-choice contract, not general model correctness. No new full500 score; remaining semantic routing errors were not retested. The exact runtime trigger for the four non-reproduced historical omissions remains unknown; their current first required calls pass. Full JSON Schema conformance and successful multi-turn tool continuation were not established by this repair. Previously documented continuation limitation remains.

Cloud/remote downstream enforcement and rendered execution paths are not certified. A uniform API does not make every model/backend capability identical; unsupported enforcement now fails explicitly locally.

Normal Ollama is healthy. API source and required configuration are deployed; the normal API rebuild hit a registry timeout, so the successful source-only image reused its exact previous dependency image. API/mailer SMTP readiness was already failing because Mailpit was absent; this task did not change that state or test delivery. Both candidate containers are stopped. Models, historical evidence and concurrent Laya work are preserved. [Commands, checkpoint/resume and rollback](README.md).
