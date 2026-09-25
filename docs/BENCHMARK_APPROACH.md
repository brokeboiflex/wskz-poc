# Synthetic Polish routing benchmark: 500 cases

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
Mailpit currently retains only 1,000 messages, so before a large run account for
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
500-case model score. **No 500-case inference run has been performed.**

Limits: balanced synthetic class frequencies do not estimate live inbox
frequencies. History variants reuse five templates and mark earlier issues as
resolved explicitly. This does not test ambiguous unresolved threads, every
prompt-injection attack, maximal input lengths or multilingual performance.
Any future confidence interval or data split must account for paired scenarios.
