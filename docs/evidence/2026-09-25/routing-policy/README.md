# Routing-policy revision: observed results

Implemented the user-approved shorter function description, explicit department
policy in the system prompt and optional MODEL_TOOL_CHOICE. The schema's
described enum alternatives are unchanged, preserving Laya classifier input.
The system instructions also distinguish technical help desk from general
requests for help and department values from the function name.

The same Ollama 0.13.5 / qwen3:1.7b was used, with reasoning_effort=none,
temperature=0.7, top_p=0.8 and max_tokens=1024. tool_choice is omitted for this
backend because prior observed evidence showed it ignores named selection.
No model, weights, parser, retry policy or validation changes were made.

| Case                      | Before                 | After                           |
| ------------------------- | ---------------------- | ------------------------------- |
| 025: language training    | Wrong help desk route  | Correct HR route, one mail      |
| 051: harassment reporting | Missing call, HTTP 502 | Missing call, HTTP 502, no mail |
| 103: leave request        | Missing call, HTTP 502 | Missing call, HTTP 502, no mail |
| 001: interview scheduling | Correct HR route       | Correct HR route, one mail      |

These are four selected diagnostic cases, each run once through the public API
and inspected before the next. Two succeeded; this is not an accuracy estimate
or proof that the training case now always succeeds. Earlier comparison traces
are in ../observed-debug/. The 500-case benchmark remains stopped.

After inspecting case 051, one additional metadata-only inference enabled the
standard OpenAI logprobs fields. Its generated tokens again showed:

```json
{ "name": "help_desk", "arguments": { "department": "help_desk" } }
```

The server returned empty content with no tool calls. This reproduces the known
function-name confusion despite clearer instructions; its department selection
is also wrong. LangChain receives the already empty API message. The production
agent does not repair or execute token text. This probe sends no mail. Case 103
also had an empty wire response; no token-level replay was made for that case
in this revision, so its internal generation is not established by this run.

The prompt change has not resolved the local model/backend failure. Keep the
client generic; changing model/backend via environment is a separate experiment.
Named tool selection requests enforcement from supporting backends, not from
this pinned server. OpenRouter was not called. No new Laya inference was run.

## Checks and evidence

- 77 focused tests passed: test_openai_wire.py, test_router.py,
  test_model_trace.py and test_laya.py. Real SDK tests cover blank/auto/required/
  named serialization, single invocation/delivery, and exact Laya classifier input.
- Ruff and Compose validation passed for all three provider examples.
- Fresh read-only critic routing_policy_critic found no blocker after inspecting
  actual application code, installed LangChain source, env wiring and tests.
- case-NNN-result.jsonl: public API results with request IDs.
- case-NNN-trace.json and case-NNN-wire-request.json: actual inference bodies,
  parsing/validation and delivery events. Each public request made one inference.
- inspection.jsonl and case-001.eml/case-025.eml: one mail per successful request,
  correct original body, recipient, Reply-To and correlation; no mail on failures.
- case-051-logprobs.json and case-051-generated.txt: separate diagnostic replay.
- api.txt: saved content-bearing trace log before disabling tracing.

Follow [OBSERVED_DEBUGGING.md](../../../OBSERVED_DEBUGGING.md) to repeat an
individual case. inspect.py reads current logs/Mailpit and rewrites evidence,
so use a new evidence directory after API recreation. The token probe is
../observed-debug/logprobs_probe.py; copy the chosen wire body to the API
container's /tmp/observed-wire-request.json before invoking it. Preserve every
attempt, including failures. Raw tracing is restored to false after capture.
