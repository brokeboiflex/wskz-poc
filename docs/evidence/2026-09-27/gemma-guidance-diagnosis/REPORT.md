# Guidance change and native-call diagnosis

## Result

Added only a three-bullet `<guidance>` block to the shared `SYSTEM_PROMPT` in `services/router/router_app/adapters/agent.py`. It clarifies existing HR coordination/advice responsibilities, work-file recovery and account-security incidents, and reserves `other` for requests outside specialist responsibilities. The exact addition is in `guidance.txt`; the rest of the prompt and tool schema are unchanged. No provider-specific application code, corrective retry or response repair was added. The source change has not rebuilt/redeployed the API container.

Focused check of the23 previous wrong routes to `other`, one new request per case on the normal patched Ollama endpoint:

| Outcome              | Before | With guidance |
| -------------------- | -----: | ------------: |
| Correct native route |      0 |            18 |
| Wrong route          |     23 |             2 |
| Missing native call  |      0 |             3 |

Remaining wrong routes:86 (recruitment-task question with resolved network history),287 (recovering a work file), both still `other`. New protocol failures:12,66,74; each names the correct HR department in ordinary text but is not a native call. Those are failures, not successful recoveries. Do not infer a new full500 score or absence of regressions on untested cases.

All23 requests/raw responses are retained in `gemma/`, all8 manual review gates passed, and `audit.py` reclassifies all23 raw responses. Existing router, real OpenAI-wire, Laya and architecture checks:81 passed. Independent critic found no scope/policy/genericity blocker in the minimal addition. An initial test command named a nonexistent `test_laya_contract.py`; no tests ran in that invocation. The corrected invocation uses `test_laya.py`.

## Why a function-shaped answer was not a native call

The five original failures (034,101,288,404,434) had identical structural symptoms: ordinary `content` beginning `send_department_email{...}`, `finish_reason=stop`, no native `tool_calls`. These are not HTTP errors, token-budget truncations or wrong function names.

The original requests omit `tool_choice`. In the pinned native server that means `auto`. The Gemma parser sets `grammar_lazy=true` and activates its tool grammar only after the generated `<|tool_call>` token. A proper call is framed as `<|tool_call>call:NAME{...}<tool_call|>`. If generation starts directly with the function name, the lazy grammar does not activate and the parser correctly returns text. A natural-language instruction to always call a tool does not enforce this framing.

For case434, the saved raw generated-token trace directly proves that the model omitted the opening marker and `call:`; it did not generate a valid native call that Ollama later dropped. It emits the correct department in text and stops after13 completion tokens. Changing only `tool_choice` to `required` in the same native request changes generation to the valid full framing and a native call (17 completion tokens). Prompt, message, model, tools, logprobs and sampling are identical; cache reuse differs and is recorded. This is bounded causal evidence for the missing-framing mechanism, not universal correctness or complete argument-schema enforcement.

The current Ollama compatibility layer does not declare `tool_choice` in `openai.ChatCompletionRequest`, and its native-chat adapter does not forward it. A recorded request with `tool_choice=required` through normal Ollama still returns the same plain text for434. Therefore setting an application flag alone does not currently enforce the requirement. The remaining integration work belongs in generic tool-choice transport/enforcement in the backend. It was diagnosed, not patched in this task.

## Reproduction limits

All five original requests were examined, and each was probed individually against the bundled native server with raw token probabilities. Only434 reproduced its original protocol failure. The other four produced valid native calls in isolation;288 chose `other` instead of the expected help desk. A second isolated server matched the normal Ollama runner arguments and native request options;034,101,288,404 again produced native calls. A streaming034 control also passed. A cold normal-Ollama034 check passed as well. Rendered034 prompts match exactly after normalizing the BOS representation.

Thus the shared permissive path and the434 generation failure are established; the precise runtime/history/numerical condition that made the other four omit framing during the500-case run is **not established**. Do not describe them as proven random, blame cache corruption without evidence, or claim a token-level reproduction of all five. The new guidance run demonstrates that missing calls can move to other messages when the prompt changes.

## Evidence and references

- `tokens-NNN/`: original messages and prompt with diagnostic logprobs, full native responses and emitted-token text; five individual requests.
- `required-434/`: native `required` control; `ollama-required-434/`: the unsupported flag through Ollama.
- `matched-NNN/`, `matched-stream-034/`, `ollama-034/`: reproduction controls. `requests/434-matched.json` was prepared but not executed.
- `render-034/`, `ollama-prompt-034.txt`, `prompt-comparison.json`: rendering-only comparison, no generated tokens.
- `native.log`, `matched-native.log`, `native-command.txt`, `ollama-native-command.json`: runtime traces and exact command arguments. Both temporary native processes are stopped; normal Ollama remains patched and healthy.
- `source/`: snapshots of the actual inspected local implementation. Ollama v0.34.4 with the existing Gemma patch, native commit161755f29e415e2c33efe906e91843c068efd664.
- [Google format reference](https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4): special-token framing contract.
- [Pinned native parser](https://github.com/ggml-org/llama.cpp/blob/161755f29e415e2c33efe906e91843c068efd664/common/parsers/gemma4.cpp): lazy grammar, trigger, required mode.
- [Upstream required-grammar change](https://github.com/ggml-org/llama.cpp/pull/29115): inspected for context; the local native required branch already works for the saved434 control. No additional upstream patch was applied.

There were23 guidance generations and13 individually observed diagnostic generations, plus one render-only request. No automatic retries, returned-tool execution, emails, backend replacement, weight changes or full benchmark rerun.693 files from the preceding500-case evidence remain byte-identical. The previous94.2% score remains historical.
