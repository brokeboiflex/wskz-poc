# Final Gemma 500-case result

**493/500 correct routes (98.6%), 7 wrong routes, 0 missing or invalid native tool calls.** All 500 requests returned HTTP200 and one valid native call on the first attempt. No retries, response repair, tools executed or mail. The run completed in about 15 minutes, within the one-hour budget.

Compared with the earlier full500 run: accuracy increased from 471/500 (94.2%) to 493/500 (98.6%), a gain of 22 cases / 4.4 percentage points. 27 of the previous 29 failures are now correct, two remain wrong (086,287), and five previously correct cases regressed (113,117,147,174,472). All five original missing calls (034,101,288,404,434) and three guidance-only missing calls (012,066,074) now return correct native calls. This combined evaluation changes guidance and tool choice/backend; it does not isolate their separate effects.

| Case | Expected        | Actual          | Previous full500 |
| ---- | --------------- | --------------- | ---------------- |
| 086  | human_resources | other           | Same wrong route |
| 113  | payroll         | human_resources | Correct          |
| 117  | payroll         | human_resources | Correct          |
| 147  | payroll         | other           | Correct          |
| 174  | payroll         | human_resources | Correct          |
| 287  | help_desk       | other           | Same wrong route |
| 472  | other           | it              | Correct          |

HR99/100, payroll96/100, help desk99/100, IT100/100, other99/100. Remaining errors concern a recruitment-task question, leave/employment paperwork, recovering a work file and resolved network history. They are semantic routing mistakes, not tool transport failures. Every failed message, expected label, exact request and original response is in [FAILURES.md](FAILURES.md) and `failures/NNN/`.

## Evidence and scope

[Offline audit](audit-e2b.json) independently reclassifies all500 saved raw responses, checks unique ordered corpus IDs, exact payloads, native function/argument validation, failure bundles and summaries. All1866 historical artifact/source hashes remain unchanged. Service logs contain exactly500 POSTs to `/v1/chat/completions`. Runtime before/after matches the same container/image and unchanged Gemma model digest. No infrastructure error or timeout occurred. Independent review is recorded in critic-review.md.

Inputs and repeat/resume procedure are in [README.md](README.md). Model: Gemma4 E2B Q4_K_M, backend0.34.4-poc.tool-choice.2, required tool choice, approved guidance and the same minimal comparison schema. No application/configuration/weight changes were made for this run. Existing API still selects Qwen; Gemma was selected only in the evaluation requests.

This is regression evaluation on a synthetic corpus already used for diagnosis and guidance, with250 paired families. It is not an independent held-out accuracy estimate or full agent/mail acceptance. The application uses a richer schema than the frozen comparison schema. Mailpit remains absent and application/mailer SMTP readiness remains unhealthy. Median request time1.8s and sum909.394s include transport/cache/loading effects and do not constitute a controlled performance benchmark.

Operational limitation: if an outer subprocess timeout occurs in a future run, the start marker prevents replay but partial output may not be retained; inspect the unknown attempt and do not retry it automatically. That path was not exercised in this completed run.
