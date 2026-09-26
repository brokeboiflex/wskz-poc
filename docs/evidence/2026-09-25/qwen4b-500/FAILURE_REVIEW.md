# Failure review

## Stopped at 400; failure-log review, 2026-09-26

User stopped the remaining-case run to inspect bugs. No further inference.
400 cases: 375 correct, 6 wrong routes, 19 missing tool calls; 100 other cases
unexecuted. All 400 raw traces and 381 live MIME messages audited successfully.
The 19 failures are upstream HTTP 200 with empty assistant content, absent
tool_calls and finish_reason=stop. LangChain receives the same empty result;
no invalid_tool_calls, no delivery. This locates the loss before the SDK.
17/19 missing calls have history wrappers; two are base messages.
Six semantic errors use valid send_department_email: laptop speed (both variants)
and overheating to IT, HR portal login and payslip download to payroll, and
compromised account with resolved printer history to help desk.

Pinned Ollama tools/tools.go searches only supplied function names; a generated
unknown name returns no call and can remain buffered. Earlier 1.7B token probes
proved that mechanism, but this 4B run has no pre-parser token logging. Do not
claim all 19 are proven wrong-name generations. Saved server logs show no matching
crash, timeout or explicit truncation; CPU quota warnings are startup warnings.
Next useful diagnostic is a single separately recorded OpenAI-compatible logprobs
request for a failed case, inspected before any further request. It was NOT run.
Do not restart bulk tests or implement output repair.

The runner was interrupted at its case294 gate during conversation, then resumed
at295 after confirming no case295 artifact/process existed. No case replayed.
Final user stop was at the case400 gate, with no request in flight.
Original190 logs are in api-first-190.txt; resumed210 in api-resumed.txt; api.txt
is their concatenation. Original partial summaries are preserved as partial-190-*.
Tracing disabled after log capture. The implementation checkpoint96ccefe was pushed.
