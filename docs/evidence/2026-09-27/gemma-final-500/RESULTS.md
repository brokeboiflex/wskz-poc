# Gemma full 500-case evaluation

Gemma tested on all 500 frozen synthetic cases with the corrected prompt, minimal schema and patched Ollama backend. No tools executed or emails sent.

| Model      | Correct | Wrong route | Invalid/missing call | Median seconds | Total seconds |
| ---------- | ------: | ----------: | -------------------: | -------------: | ------------: |
| gemma4:e2b |     493 |           7 |                    0 |          1.800 |       909.394 |

| Department      | Correct | Wrong route | Invalid/missing call |
| --------------- | ------: | ----------: | -------------------: |
| help_desk       |      99 |           1 |                    0 |
| human_resources |      99 |           1 |                    0 |
| it              |     100 |           0 |                    0 |
| other           |      99 |           1 |                    0 |
| payroll         |      96 |           4 |                    0 |

This is a synthetic corpus score, not application/SMTP acceptance or an independent held-out evaluation. The 500 messages represent 250 paired scenario families, with prior diagnostic exposure. Every raw response is retained and independently reclassified by this audit. Guidance was informed by this corpus, so the result measures regression accuracy, not unseen-data generalization. Timings include HTTP transport and any model-loading overhead.

See FAILURES.md for failed inputs and raw responses, backend-before.json for the common runtime and model identities, and audit-e2b.json for audit counts.
