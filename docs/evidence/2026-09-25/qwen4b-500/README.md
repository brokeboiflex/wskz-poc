# Observed 500-case run: Qwen3-4B-Instruct-2507

**Stopped by the user at 190/500. No further inference is running or authorized.**
All 190 completed cases were independently audited against saved traces and live
Mailpit. [Forensic findings and limits](FORENSIC_REVIEW.md); machine-readable
results: partial-summary.json. The remaining 310 cases were not executed.

Authorized by the user: "Ok full test now. All 500". The new full run uses the
unchanged 4B instruct configuration from ../qwen4b-instruct/, with raw tracing.
The recorded partial run contains 100 HR and 90 payroll cases. There is no
500-case completion artifact. Tracing was disabled after preserving service logs.

## Repeatable approach

Read [BENCHMARK_APPROACH.md](../../../BENCHMARK_APPROACH.md), particularly its
latest authorization. The frozen corpus contains 100 messages per department,
250 scenario pairs and 500 messages. No labels/rationales enter model requests.
Configuration is in model.env; reference wire body and model provenance are in
../qwen4b-instruct/. App/model settings are fixed for the entire run.

run.py wraps verification/e2e.py one case at a time, with the same public API,
LangChain tool, separate mailer and Mailpit path. It saves and independently
audits raw wire response, SDK result and MIME, including full MIME for wrong
routes. A native protocol failure must produce no mail. Every failure and each
ten-case checkpoint waits for operator review before another request.

```sh
MODEL_TRACE=true docker compose --env-file docs/evidence/2026-09-25/qwen4b-500/model.env up -d --no-deps --wait --wait-timeout 60 api
.venv/bin/python -u docs/evidence/2026-09-25/qwen4b-500/run.py
```

Do not rerun this command against an existing evidence directory. The runner
refuses an existing results.jsonl or started.json. On interruption inspect
existing logs and captured mail; never retry a possibly delivered request.
A deliberate repeat needs a new directory and separate run provenance.

## Evidence

- results.jsonl: one audited record per case, global position, original ID,
  full corpus SHA, raw tool response, parsed rejection reason and mail outcome.
- case-NNN.json, case-NNN-result.jsonl: exact input selection and unchanged
  single-case harness output. Each has its own synthetic sender/run ID.
- case-NNN-trace.json, case-NNN-api.txt: correlated actual raw and parsed model
  traces and delivery events. No transport headers/credentials are logged.
- case-NNN.eml: raw captured mail, including incorrectly routed deliveries.
- reviews.jsonl: operator acknowledgments after inspected checkpoints/failures.
- runtime-before.json: unchanged application hashes, image IDs and model digest
  from the immediately preceding model comparison.

The critic identified and fixed two restart/endpoint safeguards after this run
started. runner-at-start.py preserves the source loaded by the active process;
run.py now also creates started.json exclusively and pins child endpoints.
runner-review.json confirms no endpoint overrides were present in this run:
all requests used the intended localhost API and Mailpit. No process restart
or request replay occurred. The original first-case gap had passed with ten
audited results when the reviewer reported it. Recheck found no further blocker.

The audit was checked without inference against four saved actual traces/MIME,
and rejected four corrupted-correlation controls. The corpus builder --check
passed. No application code changed and no extra model probes are part of the
500-case evaluation. The run does not verify fresh bootstrap.

## Completion audit

After all cases, summarize.py reads all saved evidence and enumerates the entire
live Mailpit mailbox. It checks exactly one matching live message for each
delivery and zero for rejected cases, byte-compares saved/live MIME, reruns each
trace audit, and writes summary.json plus failures.json. It performs no inference.

```sh
.venv/bin/python docs/evidence/2026-09-25/qwen4b-500/summarize.py
MODEL_TRACE=false docker compose --env-file docs/evidence/2026-09-25/qwen4b-500/model.env up -d --no-deps --wait --wait-timeout 60 api
```

Save complete API/Ollama/mailer logs before the final API recreation. Report
correct routes separately from wrong routes, protocol errors and MIME defects;
include per-class counts, confusion matrix, latency and scenario-pair results.
This synthetic corpus has correlated variants and several previously inspected
diagnostic cases; the result is not a pristine held-out or production estimate.

## Read-only audit after the stop

```sh
.venv/bin/python docs/evidence/2026-09-25/qwen4b-500/summarize.py --partial
```

This reads saved API logs/traces, the unchanged corpus and live Mailpit; it makes
no model request and sends no email. The partial flag requires stop.json with
the exact completed count. It writes partial-summary.json and partial-failures.json.
It now independently verifies expected labels, boolean/derived score agreement,
trace event correlation, per-case selection hashes, whole-log request counts
and exhaustive live-mail matching. Unknown discrepancies fail the audit.

Do not replace api.txt/ollama.txt/mailer.txt with current container logs after
API recreation. stop.json and forensic-checks.json record the cancellation and
additional complete-log/repeated-input checks. All 950 API trace events map to
the 190 recorded requests; Ollama logs contain exactly 190 inference POSTs.

## Resume authorized, 2026-09-26

User requested commit, push and remaining cases. Resume the same observed method
at case 191 using `run.py --resume-after-190`; preserve cases 1-190, no replay.
The explicit flag validates the frozen prefix and refuses an existing resume
marker or case-191 artifacts. Keep per-case audits, failure/ten-case review gates
and unchanged model settings. Preserve first-segment logs separately, then join
API logs for the full audit. Save logs before disabling tracing. Commit and push
the implementation checkpoint, then completed evidence.
