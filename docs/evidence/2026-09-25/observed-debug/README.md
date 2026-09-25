# Observed diagnosis, 2026-09-25

Model/prompt/schema unchanged: Ollama 0.13.5, qwen3:1.7b, temperature 0.7,
top_p 0.8, reasoning none, 1024 output tokens. All inference used the
OpenAI-compatible `/v1/chat/completions` endpoint. No Ollama client was added.
The 500-case benchmark was not restarted.

## Findings

| Frozen case               | Observed public API result | Explanation from trace                                        |
| ------------------------- | -------------------------- | ------------------------------------------------------------- |
| 001, interview scheduling | Correct HR delivery        | Native send_department_email call with human_resources        |
| 025, language training    | Wrong help-desk delivery   | Raw server response already chose help_desk; SDK preserves it |
| 051, harassment procedure | 502, missing_call          | Raw server response empty despite 23 generated tokens         |
| 103, leave request        | 502, missing_call          | Raw server response empty despite 21 generated tokens         |

Every case was submitted separately, then its trace inspected before proceeding.
Requests include only original message text and the production prompt/tool schema;
the expected department stays in the test harness.

The standard OpenAI `logprobs` field exposed the missing generated text:

```json
{ "name": "help_desk", "arguments": { "department": "help_desk" } }
```

That is case 051's metadata-enabled reproduction. The model substituted a
department label for the only registered function name, `send_department_email`.
The server returned empty content and no tool_calls, hiding the invalid name
before LangChain could classify it as wrong_tool.

Case 103's first metadata-enabled reproduction returned a valid
`send_department_email`/`payroll` call. After inspecting that non-reproduction,
a second observed request asked for five alternative token log probabilities:

```json
{ "name": "payroll", "arguments": { "department": "payroll" } }
```

This again produced an empty API message. At the function-name position, the
reported log probabilities favored `pay` (-0.5363) over `send` (-0.8792).
The model selected the correct department while confusing it with the function
name. Those token scores are diagnostic sampling evidence, not calibrated
classification confidence. All requests and responses, including the successful
non-reproduction, are preserved; these are three extra inference requests with
no tool execution or mail delivery.

The pinned upstream [parser source](https://github.com/ollama/ollama/blob/v0.13.5/tools/tools.go)
corroborates this mechanism: parseToolCall searches registered function names,
and Content returns empty for this XML-tag format when no call is recognized. The raw token strings
were inspected only; the application never repairs or executes them.

This localizes two problems: incorrect semantic selection, and hallucinated
function names hidden by server parsing. It does not explain every historical
failure, prove a model/prompt fix, or justify increasing the model size blindly.
All four public requests used 741-754 prompt tokens and 21-23 completion tokens;
none reported length termination. LangChain correctly preserved each wire result.

## Evidence and reproduction

- `case-NNN.json`: exact single-case input selected from the frozen corpus.
- `case-NNN-result.jsonl`: public API/Mailpit harness outcome, request ID and run ID.
- `case-NNN-trace.json`: correlated request, raw response, parsed result, validation
  and actual delivery events. `case-NNN-wire-request.json` is the exact model body.
- `case-051-logprobs.json`, `case-103-logprobs.json`,
  `case-103-logprobs-second.json`: diagnostic request settings plus raw HTTP body.
- `case-*-generated*.txt`: concatenated reported output tokens, never executed.
- `inspection.jsonl`, `case-001.eml`, `case-025.eml`: independent mail checks.
  Both delivered messages preserved original body, Reply-To and correlation, with
  one mail per request. The two rejected public requests produced no captured mail.
- `api.txt`: complete observed API log snapshot before disabling traces.

Read [OBSERVED_DEBUGGING.md](../../../OBSERVED_DEBUGGING.md) first. To inspect
saved results while this same API log history and Mailpit data remain available:

```sh
.venv/bin/python docs/evidence/2026-09-25/observed-debug/inspect.py
```

That helper is read-only against services but regenerates evidence files from
current logs; after API recreation use saved traces directly instead.
Single-case inference commands and token-probe commands are in the approach doc.
Do not rerun all files as a batch or overwrite earlier attempts.

The first docker cp into the read-only API rootfs failed before inference.
The request file was then written through exec into its writable /tmp; no
container security setting was relaxed. Raw tracing was disabled after evidence
capture. 46 targeted instrumentation/SDK/router tests passed in the foreground;
the fresh read-only critic found no instrumentation blocker.
