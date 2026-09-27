# Gemma full 500-case evaluation

Gemma tested on all 500 frozen synthetic cases with the corrected prompt, minimal schema and patched Ollama backend. No tools executed or emails sent.

| Model      | Correct | Wrong route | Invalid/missing call | Median seconds | Total seconds |
| ---------- | ------: | ----------: | -------------------: | -------------: | ------------: |
| gemma4:e2b |     471 |          24 |                    5 |          2.356 |      1183.086 |

| Department      | Correct | Wrong route | Invalid/missing call |
| --------------- | ------: | ----------: | -------------------: |
| help_desk       |      98 |           1 |                    1 |
| human_resources |      79 |          20 |                    1 |
| it              |      97 |           3 |                    0 |
| other           |      98 |           0 |                    2 |
| payroll         |      99 |           0 |                    1 |

This is a synthetic corpus score, not application/SMTP acceptance or an independent held-out evaluation. The 500 messages represent 250 paired scenario families, with prior diagnostic exposure. Successful raw responses were intentionally not retained; their outcomes can only be checked against recorded metadata. Timings include HTTP transport and any model-loading overhead.

See FAILURES.md for failed inputs and raw responses, backend-e2b.json for the common runtime and model identities, and audit-e2b.json for audit counts.
