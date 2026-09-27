# Gemma failure isolated to the tool-generation integration

The controlled comparison confirms an Ollama integration gap: the installed
Gemma path bypasses native tool-name constraints available in its bundled
llama.cpp engine. The same Gemma weights and identical OpenAI request produce
a valid native call when that existing path is used with special-token output
enabled. Disabling the native parser/grammar reproduces the exact original
invalid generated tokens. No model-specific application change, retry, response
repair, source patch or replacement weights were used.

This is not proof that Gemma follows tool instructions correctly by itself.
Without constraints, these weights prefer the wrong function name even with
Google's official prompt format. The integration's missing enforcement exposes
that behavior. The experiment identifies why the currently selected runtime path
fails; it does not establish a defect in Google's weights or a universal fix for
every message.

## Controlled evidence

All three new requests are exactly equal to the saved token diagnostic request,
including model `gemma4:e2b`, original messages/tool, temperature0, top_p0.8,
max_tokens1024, reasoning_effort:none and logprobs:true. Each configuration gets
one generation, with no corrective turn, inference retry or tool execution.

| Configuration                                            | Generated function                              | API result                                                             |
| -------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------- |
| Original Ollama rendered path, saved evidence            | `human_resources` with `{}`                     | Invalid native call                                                    |
| Bundled native llama.cpp, official template              | `send_department_email` with correct department | Raw content because special string delimiters disappear before parsing |
| Same native process configuration plus stock `--special` | `send_department_email` with correct department | Valid native `tool_calls`, correct `human_resources` argument          |
| Same plus stock `--skip-chat-parsing`                    | `human_resources` with `{}`                     | Raw generated tokens exactly reproduce original Ollama failure         |

The two constrained runs generate the same nineteen token IDs. The only relevant
output difference is decoding: without `--special`, both token52 occurrences
become empty strings; with it, they remain Gemma's `<|"|>` string delimiters and
the native parser extracts the call. The unconstrained control generates the
original nine tokens exactly, including `<|tool_response>`.

At the function-name decision, native logprobs show `human` as the highest
unconstrained candidate (logprob approximately -0.000005), while the grammar
selects `send`. This directly distinguishes decoder enforcement from the model
spontaneously learning a better answer or an output parser renaming the call.

Files: `native-first/`, `native-special/`, `native-unconstrained/`, their server
logs, `template-comparison.json`, `native-render-response.json`, and `audit.json`.
The former comparison remains at Gemma31/147 and Qwen147/147.

## Rendering and model identity

Google revision `3e22461f65e89153144f8adb70e3b8c2cc9845a7` provides the canonical
E2B template. Applying it to the captured request produces exactly the same
2459-character prompt as Ollama, SHA-256
`429593d26b94af857cbd9da332fceaf13a8328f314a279935f7f5d548f03d5a9`.
The direct native `/apply-template` result differs only by the initial `<bos>`:
llama.cpp adds it during tokenization, as Ollama's completion path also expects.
Both paths account for506 input tokens. There is no observed tool declaration,
system prompt, thinking-mode, BOS-count or context-truncation mismatch.

Every direct test uses the original installed GGUF blob
`sha256-4e30e2665218745ef463f722c0bf86be0cab6ee676320f1cfadf91e989107448`,
including the same mmproj blob, context4096, one slot, batch512 and microbatch512.
The executable is the installed `/usr/lib/ollama/llama-server`, build `161755f29`;
its version and binary hash are saved. Ollama remains
`0.34.4-poc.18391.17284`. No binary or weight was rebuilt or replaced.

## Source-level cause and ownership

1. Ollama's `chatModeForModel` selects its rendered-completion path for models
   with configured Renderer/Parser metadata. The Gemma config has both set to
   `gemma4`; Qwen uses native chat, confirmed in the saved runtime log.
2. The rendered Gemma path supplies a prompt and preserved tokens to Completion,
   but not structured tools. Completion only sets grammar/schema when Format is
   set, and this native-tool request has no Format. Therefore it lacks tool-name
   constraints. This wiring belongs to Ollama, not LangChain or our agent.
3. The bundled native Gemma integration builds literal permitted function names
   from the declared tools and enables a lazy tool-call grammar. Its native chat
   handler passes this grammar into sampling. The direct experiment demonstrates
   the effect on this exact request.
4. A separate bundled llama.cpp defect affects native response parsing: its
   Gemma `preserved_tokens` list omits `<|"|>` although its argument grammar and
   parser require that delimiter. The stock `--special` option preserves it.
   Ollama's own Gemma parser already preserves this token, so this second defect
   is not the cause of the original Ollama wrong-name output.
5. Qwen's native auto-parser path builds a tool-call grammar when tools and a
   tool-call marker are present. The same outer API therefore does not mean the
   two model integrations use the same enforcement. Qwen's recorded147 valid
   calls still include14 wrong departments, a separate semantic failure class.

Pinned upstream references:

- [Ollama execution-path selection](https://github.com/ollama/ollama/blob/v0.34.4/server/routes.go)
- [Ollama completion and native-chat transport](https://github.com/ollama/ollama/blob/v0.34.4/llm/llama_server.go)
- [Bundled Gemma grammar and preserved tokens](https://github.com/ggml-org/llama.cpp/blob/161755f29/common/parsers/gemma4.cpp)
- [Native chat grammar forwarding](https://github.com/ggml-org/llama.cpp/blob/161755f29/tools/server/server-common.cpp)
- [Native auto-parser grammar construction](https://github.com/ggml-org/llama.cpp/blob/161755f29/common/chat-auto-parser-generator.cpp)
- [Google's exact template revision](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/chat_template.jinja)

## Limits and next engineering decision

The first-try success is one deliberately isolated failing request. No500-case
or147-case evaluation was resumed. The native Gemma grammar contains an explicit
TODO for parameter-schema constraints: it constrains tool names and basic value
syntax but does not yet enforce the complete declared argument schema. Do not
claim that this configuration guarantees required arguments, enums or routing
accuracy for arbitrary tools/messages.

This establishes the missing integration behavior, not a deployed PoC fix. A
proper fix belongs upstream in the runner: consistent native tool enforcement
and token preservation behind the same OpenAI-compatible interface. Replacing
the application's native tool calling with classification, retries or function
name rewriting is unnecessary for this investigation and was not done. No
upstream issue or pull request was posted.

## Reproduction and final state

Read [APPROACH.md](APPROACH.md) before any inference. The executable scripts and
individual request/response artifacts preserve the exact procedure. From the
PoC root, offline verification is:

```sh
.venv/bin/python docs/evidence/2026-09-26/gemma-integration-audit/audit.py
```

The temporary runner was stopped after the three diagnostics. Normal Ollama
remains healthy on its original service port, with its previous image and model
metadata. No additional port was published to the host, no email was sent, and
no application code or main Compose configuration was changed in this audit.
