# Routing reliability research, 2026-09-25

Scope: user requested web research after stopping the 500-case evaluation.
No inference, model downloads, runtime changes or benchmark restart were performed.
Recommendations below are untested in this application.

## Evidence from this application

The interrupted run `2279baae02cc` completed 241 records: 176 correct routes,
52 wrong departments and 13 HTTP errors classified as `invalid_tool_call`.
All 13 matching API log reasons are `missing_call`. This means no recognized
call reached the validator; it does not distinguish model prose from a server
parser failure. Raw responses were not preserved for those requests.
41 of the 100 HR cases went to help desk, including explicit training requests.
The ordered partial run is not a balanced 500-case accuracy measurement.

Current code uses LangChain `create_agent`, one terminal email tool, one enum
argument and validation before delivery. The system prompt focuses on invocation;
department policy appears in the tool description and described schema alternatives.
There is no explicit `tool_choice` setting. Installed LangChain's factory passes
`request.tool_choice` through `bind_tools`; `ModelRequest.override` supports it.

The runtime used Ollama 0.13.5 / qwen3:1.7b, reasoning disabled, temperature 0.7,
top_p 0.8 and 1024 output tokens. Read-only Ollama logs show a 4096-token context
and no truncation warning in the available logs. This does not prove every
prompt's token count, but there is no evidence here that context exhaustion
caused the observed mistakes.

## Findings and recommendations

### 1. Separate classification from tool-protocol reliability

[LangChain documents forcing tool calls](https://docs.langchain.com/oss/python/langchain/models#tool-calling)
through `tool_choice`. A server that honors required or named choice can constrain
the response to a call; the choice of department can still be wrong.

The pinned [Ollama 0.13.5 request type](https://github.com/ollama/ollama/blob/v0.13.5/openai/openai.go#L90-L109)
does not contain `tool_choice`. Adding a client parameter cannot enforce an
unsupported server feature. A later [0.32.15 issue](https://github.com/ollama/ollama/issues/17921)
also reports ignored choices, but that report concerns its stated model/runtime,
not every Ollama configuration.

Use the framework's standard request settings on backends that support them.
Verify server behavior rather than inferring support from an OpenAI-compatible URL.
Keep the single-call validator and never parse prose into an email action.

### 2. Compare an instruction-focused model before adding agent machinery

First candidate: `qwen3:4b-instruct-2507-q4_K_M`, listed by
[Ollama at 2.5 GB](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M).
This is weight/download size, not total runtime RAM.
The [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
describes a non-thinking model with improved instruction following and tool use.
Its reported BFCL-v3 score is 61.9 versus 57.6 for the original Qwen3-4B
non-thinking configuration; these are publisher benchmark results, not Polish
message-routing accuracy or a direct measurement against our 1.7B deployment.

Use the explicit instruct tag: the current
[Ollama tag list](https://ollama.com/library/qwen3/tags) maps plain `qwen3:4b`
to the thinking variant. An env-only model change is a candidate experiment,
not a proven fix. Verify the downloaded artifact, template and compatibility
with the pinned server before declaring it usable.

### 3. Make the classification policy explicit in the system prompt

[LangChain tools](https://docs.langchain.com/oss/python/langchain/tools) use
descriptions and argument schemas to guide models; descriptions can include
[few-shot examples](https://reference.langchain.com/python/langchain-core/tools/base/BaseTool/description).
My application-specific recommendation is a short Polish routing policy in the
system prompt with explicit boundaries: training/recruitment/employee relations
to HR, employment administration/pay/leave to payroll, individual technical
support to help desk, infrastructure/security to IT, insufficient or unrelated
requests to other. Classify the current actionable request; ignore resolved history.

This recommendation is a hypothesis about clarity, not evidence that Polish
prompts always outperform English or that schema composition caused this failure.
Our current help-desk description begins with general help to a single user;
making its technical scope explicit is worth testing without changing policy.
Keep one tool and one department argument. Do not add a classifier agent, reviewer
agent, correction loop or framework migration. Keep the Laya adapter's standard
schema contract intact; removing anyOf would require separately preserving its
typed-choice descriptions and verifying that adapter.

### 4. Verify the serving template and parser instead of upgrading blindly

[Qwen's function-calling guide](https://qwen.readthedocs.io/en/latest/framework/function_call.html)
recommends Hermes-style tool use and documents an OpenAI-compatible vLLM setup.
Application-level LangChain can remain unchanged when a serving backend performs
the correct template rendering and parsing.

Ollama's [template serialization issue](https://github.com/ollama/ollama/issues/14601)
has an [open proposed fix](https://github.com/ollama/ollama/pull/18391), checked
2026-09-25. The existing pre-regression pin addresses that specific defect,
not all possible model or tool-calling defects. Do not introduce local template
patches or assume latest is fixed.

If an alternative backend is later requested, [vLLM documents required/named
tool choice and constrained decoding](https://docs.vllm.ai/en/latest/features/tool_calling/),
and [llama.cpp documents tool calling with Jinja templates](https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md).
These are alternative serving options, not replacements for the assignment's
required Ollama path. Hardware/version support and the exact schema need separate
verification. Schema constraints enforce structure, not correct classification.

For the optional OpenRouter path,
[require_parameters](https://openrouter.ai/docs/guides/routing/provider-selection#requiring-providers-to-support-all-parameters)
restricts provider selection to those supporting supplied parameters. It belongs
in provider configuration, not a provider-name branch in the shared agent.
Our current env template does not yet expose that extra provider configuration.

### 5. Do not treat sampling as the established root cause

[Qwen3-1.7B's model card](https://huggingface.co/Qwen/Qwen3-1.7B) recommends
temperature 0.7 and top_p 0.8 in non-thinking mode, which match our settings.
Lower temperature can be compared, but is not a documented guaranteed correction
for these errors. Merely enabling thinking also introduces a different output
budget and parser path; it should not be silently combined with other changes.

## Proposed next investigation, not executed or authorized by this research

1. Capture exact synthetic request, rendered prompt and raw response on a small
   diagnostic set, without executing email tools. Distinguish absent generation
   from parser loss before choosing a fix for missing calls.
2. Compare the current model with the explicit 4B instruct model while holding
   prompt, schema and server constant. Record model digest, settings and latency.
3. Independently compare the clearer system policy. Use separately authored
   development examples, not frozen evaluation messages copied into the prompt.
4. Test supported forced-call behavior separately from department accuracy.
5. Only after a configuration is selected and further evaluation is requested,
   perform end-to-end delivery checks and a held-out evaluation. Keep scenario
   pairs together and report protocol failures separately from wrong routes.

The 500-case run stays stopped. Read `BENCHMARK_APPROACH.md` before any future
explicitly requested evaluation; preserve the partial evidence and do not replay
possibly delivered requests automatically.
