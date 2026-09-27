# Synthetic Polish routing benchmark: 500 cases

Final Gemma500 evaluation completed 2026-09-27: **493/500 correct (98.6%), 7 wrong routes, 0 missing/invalid native calls**. All500 first attempts, no retries or mail. Previous score471/500;27 old failures fixed,2 remain,5 new regressions. All raw responses and seven failure bundles saved; offline audit passed and1866 prior hashes unchanged. Synthetic regression evidence, not held-out/general application acceptance. [Results, failures and repeat procedure](evidence/2026-09-27/gemma-final-500/README.md). No further run is implicit.

Final Gemma500 evaluation authorized 2026-09-27, unattended with a one-hour budget: [approach and checkpoints](evidence/2026-09-27/gemma-final-500/README.md). Current guidance, tool_choice=required and patched backend; each case once, all raw responses saved, no mail. This explicit authorization supersedes historical manual review gates for this run only.

## Authorization and scope

On 2026-09-25 the user explicitly approved creating a synthetic benchmark of
500 cases following the dataset research. This document records that approach.
The deliverable is a frozen, labelled dataset and a way to run it with the existing
HTTP → model → mailer → Mailpit acceptance test. Building/validating the corpus
does not establish model accuracy. No weight training or external mail is involved.

## Design

- 100 cases per existing department: human_resources, payroll, help_desk, it, other.
- 250 separately authored scenarios, 50 per department, with two variants each.
  Paired variants are correlated; this is 500 messages, not 500 independent intents.
- The base message contains a concrete request and useful context. The second
  version adds a resolved competing request, quoted history, or distracting context.
  The requested action must still support the same label.
- Polish is the evaluation language, with naturally occurring technical terms.
- Expected labels are authored from the existing routing policy, never inferred
  from Ollama/Laya predictions. No downloaded dataset needs relabelling.
- Source scenarios include an explanation of the expected department. Synthetic
  names, domains and situations have no connection to actual employees or tickets.
- Stable case IDs and scenario IDs identify pairs. Keep pairs together if creating
  future development/test splits. This corpus is evaluation-only; do not tune on it
  and then report its score as an independent held-out result.

## References and boundaries

Read the implementation in `services/router/router_app/adapters/agent.py` and the
original 15 cases before authoring. The existing policy distinguishes employee
payroll/leave/documents from recruitment/training/relations, and individual user
support from infrastructure/security incidents. The primary actionable request
wins when other subjects appear. Insufficient information and unrelated requests
belong to `other`. Do not change production routing policy to fit this dataset.

Message shapes (history, signatures, diagnostic details) were informed by inspected
public samples, without copying their messages or labels:

- <https://huggingface.co/datasets/Console-AI/IT-helpdesk-synthetic-tickets>
- <https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets>
- <https://zenodo.org/records/7648117>

## Authoring, validation and repeatability

The source catalogue is `verification/benchmark/scenarios/*.txt`: one UTF-8 line
per scenario, with `slug | rationale | message` fields and optional literal `\n`
paragraph breaks. A deterministic
standard-library builder creates `verification/benchmark/cases-500.json` and a
validation report. It uses no API, paid model, network or random generation.
Read this document before regenerating; edit the source intentionally, review the
diff and regenerate. Never regenerate automatically as part of model evaluation.

From the PoC root, with Python 3.12 and the existing development environment:

```sh
.venv/bin/python verification/benchmark/build.py
.venv/bin/python verification/benchmark/build.py --check
.venv/bin/ruff check services tests verification
.venv/bin/ruff format --check services tests verification
.venv/bin/pytest -q
```

To verify the actual container packaging without starting models or delivering mail:

```sh
docker compose --env-file .env.ollama-example --profile test build tests e2e
docker compose --env-file .env.ollama-example --profile test run --no-deps --rm tests
docker compose --env-file .env.ollama-example --profile test run --no-deps --rm e2e \
  python benchmark/build.py --check
```

Use the public-registry Docker client workaround in `APPROACH.md` only if this
host's credential helper is blocked. It was reused for these packaging checks.

Validation must check exact counts/balance, unique text and IDs, label/address
consistency, pair integrity, current HTTP limits and reproducible output. Record
length statistics and the dataset SHA-256. Inspect the actual messages and have an
independent critic check labels and diversity before calling the corpus complete.

## Running later

The original 15-case smoke test stays the default. Select the large corpus explicitly:

```sh
docker compose --env-file .env.ollama-example up -d
docker compose --env-file .env.ollama-example --profile test run --build --rm e2e \
  python e2e.py --cases benchmark/cases-500.json
```

For Laya use `.env.laya-example` in both commands. Each run adds 500 captured emails.
Mailpit now defaults to 10,000 messages (`MAILPIT_MAX_MESSAGES`), so before a large run account for
existing mail and raise the retention limit as necessary to avoid automatic eviction.
Do not delete messages or volumes. Label, rationale and scenario metadata remain in
the test harness; the API receives only synthetic sender contact and message text.

Results contain case/scenario IDs and the exact corpus checksum. Preserve JSONL
output even if the process returns a failing exit status. An interrupted run is partial
evidence; there is no automatic resume/retry of possibly delivered requests. Keep
partial evidence and start any explicitly requested rerun with a new run ID.

## Checkpoint

Completed 2026-09-25: 500 unique messages, 250 scenario families, 100 cases per
department. All 250 source scenarios were inspected by an independent critic;
after revisions, the critic also inspected every `other` history variant, the
longer messages, composition rules, packaging and answer-key isolation. No
remaining correctness blocker was found for controlled synthetic evaluation.

The review removed artificial explanations of missing context and unnecessary
department exclusions, and added concrete detail to 50 source scenarios. Short
incomplete requests remain intentionally short. The final corpus contains:

| Message length (whitespace-separated words) | Cases |
| ------------------------------------------- | ----: |
| Under 30                                    |    19 |
| 30–59                                       |   208 |
| 60–99                                       |   211 |
| 100 or more                                 |    62 |

Median: 61 words; range: 16–176 words / 87–1,362 characters. Exact source and
dataset checksums are in `verification/benchmark/manifest.json`. Frozen corpus
SHA-256: `bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e`.

Host and rebuilt test container: **97 tests passed**. The E2E container also
passed deterministic corpus verification as its normal non-root user. Ruff,
Prettier and diff whitespace checks passed. Those are code/data checks, not a
500-case model score. **At this corpus-creation checkpoint no 500-case inference run had been performed.**
The later tool-wiring repair and live evaluation are recorded in
[TOOL_WIRING.md](TOOL_WIRING.md) and [VERIFICATION.md](VERIFICATION.md).

Limits: balanced synthetic class frequencies do not estimate live inbox
frequencies. History variants reuse five templates and mark earlier issues as
resolved explicitly. This does not test ambiguous unresolved threads, every
prompt-injection attack, maximal input lengths or multilingual performance.
Any future confidence interval or data split must account for paired scenarios.

## Reauthorized full check after generic-agent repair

The user explicitly requested "Check with all 500 messages" after the small
provider-switch smoke. This authorizes a new complete run on the current
Ollama 0.13.5 / qwen3:1.7b stack, using the frozen corpus and existing E2E
harness. No model/prompt/schema/corpus tuning or automatic request retries.
Evidence directory: `docs/evidence/2026-09-25/ollama-500-generic/`. Preserve
nonzero exit and separate wrong departments from HTTP/tool-call failures.
The earlier interrupted runs remain historical evidence.

## Latest checkpoint: stopped by user

The reauthorized run was stopped on the user's explicit instruction. Run
`2279baae02cc` has 241 completed records: 176 correct routes, 52 wrong departments,
and 13 HTTP 502 `invalid_tool_call` responses. All 13 matching API log reasons
are `missing_call`, not malformed JSON or invalid arguments. Of the 100 HR
messages, 41 went to help desk. These are partial, class-ordered results, not a
500-case accuracy score. No full-run MIME audit was performed. An in-flight
request at cancellation may finish independently; do not replay it automatically.
The E2E container was stopped (exit 137); results and API logs were preserved in
`docs/evidence/2026-09-25/ollama-500-generic/`. Do not resume without a new explicit
request. No model, prompt, schema or corpus changes were made during this run.

## Full 500-case observed run authorized after the model comparison

The user explicitly requested "Ok full test now. All 500". This supersedes the
stop instruction for a new run only; preserve the previous interrupted results.
Use qwen3:4b-instruct-2507-q4_K_M on existing Ollama 0.13.5, unchanged prompt,
schema, image and inference settings. Frozen dataset SHA-256:
`bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e`.

Evidence: docs/evidence/2026-09-25/qwen4b-500/. The observed runner wraps the
existing single-case E2E harness. It runs serially, saves exact input/result,
correlated raw wire trace and raw MIME, and validates every case before starting
the next. It pauses on each failure and every ten cases for operator review.
The operator reads the actual failed message and raw/parsed output before
continuing. A failed case is never retried. Do not change settings, prompt or
labels during the run. Only synthetic Mailpit delivery is permitted.

The per-case gate checks one request/response, unchanged wire payload except
message text, no answer-key leakage, valid native call/parsed agreement, delivery
correlation and full MIME even when the department is wrong. Failed requests
must have no mail. Wrong routes and protocol failures are reported separately.
Unknown audit errors stop execution. Capture whole service logs and perform an
independent final Mailpit duplicate audit. No extra diagnostic inferences are
part of these 500 cases. Raw content tracing is disabled after saving evidence.

Commands from the PoC root:

```sh
MODEL_TRACE=true docker compose --env-file docs/evidence/2026-09-25/qwen4b-500/model.env up -d --no-deps --wait --wait-timeout 60 api
.venv/bin/python -u docs/evidence/2026-09-25/qwen4b-500/run.py
```

The runner requires the existing .venv, healthy API/Mailpit and enough Mailpit
retention for 500 new messages. It refuses an existing results.jsonl to prevent
accidental replay. Review gates accept continue to advance, stop to terminate.
After interruption inspect the last request/logs and preserve the partial run;
there is no automatic resume or replay of uncertain deliveries. Store operator
reviews, complete results, confusion matrix, per-class counts, latency and
paired-family results. This is synthetic evaluation; prior diagnostic use of
some cases means it is not a pristine held-out test.

## Latest instruction: stop and audit existing evidence, 2026-09-26

The user stopped testing at 190 completed cases and asked to rule out a fluke.
No further inference, benchmark continuation or synthetic email is authorized
by this audit. The runner is absent and stopped at the case-190 review gate.
Preserve full service logs, audit the saved raw wire traces against the frozen
inputs and current app, verify all live captured MIME and duplicates, and
recompute scores from raw outcomes rather than trusting passed flags. Check
class coverage, paired scenarios, previous diagnostic exposure, label leakage
and hidden retries. A fresh independent critic reviews saved evidence only.

Use summarize.py --partial for this explicit partial run; write partial-summary.json
and partial-failures.json, never a 500-case completion artifact. Restore raw
tracing to false after preserving logs. Neither a clean forensic audit nor a
perfect class-ordered prefix proves repeatability or general accuracy.

## Resume authorized, 2026-09-26

User requested commit, push and remaining cases. Resume the same observed method
at case 191 using `run.py --resume-after-190`; preserve cases 1-190, no replay.
The explicit flag validates the frozen prefix and refuses an existing resume
marker or case-191 artifacts. Keep per-case audits, failure/ten-case review gates
and unchanged model settings. Preserve first-segment logs separately, then join
API logs for the full audit. Save logs before disabling tracing. Commit and push
the implementation checkpoint, then completed evidence.

## Latest checkpoint: stopped at 400

User stopped testing to inspect failures. No further inference. Results: 375 correct,
6 wrong routes, 19 upstream missing calls; 381 live MIME audits passed. See
`docs/evidence/2026-09-25/qwen4b-500/FAILURE_REVIEW.md` (path from repository root).

## Completed English minimal-schema evaluation, 2026-09-26

User authorized all 500 cases with failure-only records. Completed unchanged
Qwen3 4B / patched Ollama / temperature 0: 353 correct, 109 wrong routes,
38 missing native calls. All missing calls were in the other category and
returned ordinary text with finish_reason=stop, not native tool_calls.
This is transport-only evidence: no emails or application schema changes.
All 147 failures and 182 review gates passed the offline consistency audit;
successful raw responses were intentionally not retained. No further run is
implicit. Approach, exact prompt/schema, failure report and audit command:
`docs/evidence/2026-09-26/english-minimal-500/README.md` (repository-root path).

## Full Gemma run completed, 2026-09-27 local time

User explicitly requested all 500 cases through Gemma and saving every failure for debugging. Reused the observed transport-only method, frozen corrected prompt/minimal schema and patched backend from the previous 147-case check. Result: 471 correct, 24 wrong routes, 5 missing native calls; 29 full failure records, 77 reviewed gates, audits passed. Prior 147 outcomes match exactly. No retries or mail. The full approach, resume command, failure bundles and limits are in [gemma-patched-500/README.md](evidence/2026-09-26/gemma-patched-500/README.md).
