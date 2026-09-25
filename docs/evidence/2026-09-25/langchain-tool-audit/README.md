# LangChain tool setup audit

Read the official [tools](https://docs.langchain.com/oss/python/langchain/tools),
[agents](https://docs.langchain.com/oss/python/langchain/agents),
[ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai) and
[tool calling](https://docs.langchain.com/oss/python/langchain/models#tool-calling)
documentation, then inspected the actual installed source:

- langchain 1.2.15: agents/factory.py automatically binds registered tools and
  forwards ModelRequest.tool_choice through model.bind_tools.
- langchain-core 1.2.31: tools/convert.py implements @tool through
  StructuredTool.from_function. Dict args_schema is explicitly supported.
- langchain-openai 1.1.14: chat_models/base.py converts a named tool_choice into
  the standard OpenAI function-selection object. Strictness depends on the server.
- langgraph 1.1.5 executes the registered tool; return_direct stops after delivery.

`compare_tools.py` proved exact equality between our current emitted tool schema
and the @tool decorator supplied the same name, description and schema. Current
registration is valid; changing decorators alone cannot change model behavior.
The captured production requests contain one correct function definition, one
required enum argument, the system prompt and the original user message.

## Individually observed diagnostics

No production code, model, prompt, sampling settings or Laya contract changed.
The existing OpenAI-compatible logprobs probe ran three individual diagnostic
requests. Each result was read before the next. Tools were never executed.

| Case / variant                               | Raw generated result                                       | API result          |
| -------------------------------------------- | ---------------------------------------------------------- | ------------------- |
| 051 / simpler @tool schema                   | function help_desk, department help_desk                   | Empty message       |
| 025 / simpler @tool schema                   | function send_department_email, department human_resources | Correct native call |
| 051 / original schema plus named tool_choice | function help_desk, department help_desk                   | Empty message       |

The simpler schema retains every category and its existing description, moves
category explanations to the argument description, removes redundant anyOf and
uses a short function description. AdditionalProperties remains false. The
system prompt and all other original request fields are unchanged.

The named-choice payload was produced by the installed ChatOpenAI.bind_tools,
not handwritten. It selects send_department_email explicitly and uses exactly
the original tool schema. The server still returned no call; logprobs reveal
an invented help_desk function. This is direct evidence that named choice was
not enforced for this request, consistent with the pinned server request type.

These are diagnostic reproductions, not an accuracy evaluation. Simplification
helped one observed input but did not fix the other. Sampling remains stochastic;
one successful generation does not establish a reliable causal improvement.
Nothing here proves that 1.7B model size alone is the root cause.

## What is established and what remains

The missing-call mechanism is model-generated function-name confusion plus the
server's omission of unrecognized calls. SDK binding/parsing does not introduce
those names. Named tool choice is omitted in the current application, but adding
it alone does not fix this server. Incorrect department selection is separately
present in valid native calls.

The next implementation candidate is a clearer routing policy and concise tool
presentation, retaining one agent/tool/enum and OpenAI-compatible inference.
Do not simply remove anyOf in production: Laya consumes its descriptions and
must retain an equivalent, verified classification contract. Named tool choice
should be used where the configured backend demonstrably supports it. If the
current model remains unreliable, compare another tool-capable model through
env settings, with the same observed procedure. No parser repair, manual JSON
execution or retry loop follows from this audit. There is no proven complete fix
yet and the bulk benchmark remains stopped.

## Reproduce or inspect

Read [OBSERVED_DEBUGGING.md](../../../OBSERVED_DEBUGGING.md) first. Offline only:

```sh
PYTHONPATH=services/router .venv/bin/python \
  docs/evidence/2026-09-25/langchain-tool-audit/compare_tools.py
```

This regenerates diagnostic payloads and verifies decorator equivalence; it
does not call a model. Individual model probes use the previously documented
logprobs_probe.py and a selected captured payload, never all cases automatically.
Exact requests and full raw responses are saved beside this report. The API
remains on the original implementation, with MODEL_TRACE=false.
