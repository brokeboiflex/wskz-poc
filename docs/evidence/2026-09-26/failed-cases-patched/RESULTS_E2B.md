# Failed-case comparison

Both models tested on the same 147 previously failed cases, with frozen inputs and the same patched Ollama backend. No tools executed or emails sent.

| Model                         | Correct | Wrong route | Invalid/missing call | Median seconds | Total seconds |
| ----------------------------- | ------: | ----------: | -------------------: | -------------: | ------------: |
| qwen3:4b-instruct-2507-q4_K_M |     133 |          14 |                    0 |          3.461 |       550.458 |
| gemma4:e2b                    |     146 |           0 |                    1 |          2.350 |       351.059 |

This is failure-set recovery, not overall accuracy or application/SMTP acceptance. Successful raw responses were intentionally not retained; their outcomes can only be checked against recorded metadata. Timings include HTTP transport and any model-loading overhead, with Qwen run before Gemma.

See FAILURES_E2B.md for failed inputs and raw responses, backend-e2b.json for the common runtime and model identities, and audit-e2b.json for audit counts.

## Remaining failure and comparison

Gemma recovered146/147 selected cases (99.3%); Qwen recovered133/147 (90.5%).
All Qwen outcomes match the previous backend exactly. Gemma's original31 cases,
which all had invalid calls before the patch, now all pass in this fresh run.

Gemma's sole failure is original case434 (comparison index101): it outputs
`send_department_email{department:<|"|>other<|"|>}` as plain text with
`finish_reason=stop`, without `tool_calls`. This is a protocol failure even
though its text names the expected department. The repair therefore does not
establish100% first-generation native-call reliability.

The prior evidence, agent and frozen inputs remain unchanged;
`preservation-audit.json` records this check. No retries, delivery or full500
rerun. The patched Ollama service remains installed and healthy.
