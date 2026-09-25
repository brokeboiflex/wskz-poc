# Evidence audit after stopping the run

The user stopped testing on 2026-09-26 local time, at the case-190 review gate.
The old terminal session was gone and process inspection found no runner or
E2E child. No continuation was sent after case 190. No further inference or
email was initiated for this audit. Evidence remains under the run's original
2026-09-25 directory; reviews/stop markers use UTC timestamps.

## What is established

The 190 successes are real recorded executions, not a demonstrated counting
artifact. An exhaustive audit and a fresh independent critic both checked the
actual frozen input, raw provider response, SDK call and saved MIME. The parent
also enumerated the entire live Mailpit mailbox and checked all 190 raw emails.

- 190 unique inputs and request IDs; each received one model response and one
  matching captured email. Complete API logs contain 950 events; complete
  server logs contain 190 Chat Completions POSTs. No unrecorded attempts, retries
  or case-191 artifact were found.
- Expected labels agree with the frozen corpus. Correctness was recomputed from
  audited native calls and delivery recipients, rather than trusting passed.
  Every MIME recipient, Reply-To, body, Message-ID and request correlation agrees.
  Full-mail enumeration found no duplicate delivery for any run request.
- Every inference body has the same system prompt, schema and settings, plus
  only the original message. No expected class, scenario ID or rationale was
  added to the request. There is no per-class application branch or canned
  classifier; each call is a fresh system/user conversation with no previous
  case history. Image and application hashes remain unchanged.
- Cases 001/025/051/103 had identical model requests in the earlier 4B diagnostic
  run and returned the same correct department again here. This is four selected
  repeated successes, not a comprehensive stability measurement.
- Short provider completion IDs repeat, but timestamps, tool-call IDs and prompt
  token counts differ. The records do not show replayed cached responses.

The partial result is HR 100/100 and payroll 90/90, with zero protocol errors
or mail-integrity failures. Median public latency 5.5575 s, p95 9.623 s, maximum
20.997 s; request-time sum 1094.376 s excludes operator pauses.

## What this does not establish

The perfect prefix cannot justify a general reliability or no-fluke claim.

1. Class ordering matters: help desk, IT and other have zero completed cases.
   The difficult help-desk-versus-infrastructure boundary is unmeasured here.
2. 190 messages represent 95 scenario pairs, not 190 independent intents.
   Variants reuse the same message with five recurring history wrappers and
   explicitly resolved/closed distractors. They do not cover arbitrary ambiguous
   threads.
3. The corpus was already visible during debugging and prompt/model selection.
   The critic found all 190 cases in the preceding 1.7B run: 135 correct, 50 wrong
   routes and five missing calls. The later prompt/model changes benefited from
   this evidence. This run is not a pristine held-out evaluation.
4. Most cases have only one execution on this configuration. Stochastic
   repeatability, unseen paraphrases and distribution changes are unmeasured.
5. The larger model package changes both weights and stock template. Historical
   190-case comparison also changes the prompt. It does not isolate parameter
   count as the cause of improvement.

Fresh read-only critic fluke_evidence_critic independently recomputed all 190
results and confirmed these boundaries. No direct answer-key leakage or scoring
inflation was found. The conclusion is narrower than a guarantee: real success
on this inspected subset, with overall reliability still unproven.

Any later investigation would need newly authored, balanced unseen scenarios
and repeated individual runs with unchanged settings, while keeping scenario
pairs together. That is a description of missing evidence, not authorization
to resume testing.

## Audit corrections and reproducibility

The initial summary script assumed all 500 and trusted the recorded passed flag.
Before auditing this partial run, it gained an explicit --partial mode plus
checks for frozen expected labels, derived-score consistency, complete category
totals and every trace event's request ID. It refuses unknown inconsistencies.
These changes did not touch the application or regenerate any model result.

Run summarize.py --partial as documented in README.md for the exhaustive saved
trace/live MIME audit. partial-summary.json, partial-failures.json (empty),
forensic-checks.json and stop.json preserve the outcomes. The saved complete
service logs must not be overwritten after disabling tracing.
