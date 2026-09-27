# Message router PoC

Gemma work accepted as complete. Gemma is now the default; Qwen weights removed and all PoC containers stopped. [Delivered work, cleanup, validation and restart](docs/GEMMA_COMPLETION.md). Historical checkpoints below describe their original runtime.

Final Gemma500 evaluation completed 2026-09-27: **493/500 correct (98.6%), 7 wrong routes, 0 missing/invalid native calls**. All500 first attempts, no retries or mail. Previous score471/500;27 old failures fixed,2 remain,5 new regressions. All raw responses and seven failure bundles saved; offline audit passed and1866 prior hashes unchanged. Synthetic regression evidence, not held-out/general application acceptance. [Results, failures and repeat procedure](docs/evidence/2026-09-27/gemma-final-500/README.md). No further run is implicit.

Final Gemma500 evaluation authorized 2026-09-27, unattended with a one-hour budget: [approach and checkpoints](docs/evidence/2026-09-27/gemma-final-500/README.md). Current guidance, tool_choice=required and patched backend; each case once, all raw responses saved, no mail. This explicit authorization supersedes historical manual review gates for this run only.

Latest repair (2026-09-27): **Ollama0.34.4-poc.tool-choice.2 is applied**. Generic native `tool_choice` transport now works; existing `MODEL_TOOL_CHOICE=required` is enabled and approved guidance is deployed. All8 saved missing-call cases pass on the first required request, including434; auto still reproduces434. Qwen, streaming, named, none and plain-text controls pass;81 application regressions and backend tests/vet pass. No full500 rerun or mail. Unsupported rendered required/none fails explicitly; API/mailer SMTP readiness remains blocked by pre-existing absent Mailpit. [Evidence, commands and rollback](docs/evidence/2026-09-27/ollama-tool-choice/README.md).

Previous prompt/diagnosis checkpoint (2026-09-27): added a minimal generic `<guidance>` block only. Focused23-case check:18 correct native routes,2 wrong routes,3 missing calls;81 regression tests pass. Raw tokens reproduce case434 missing the opening tool marker; native `tool_choice=required` corrects that case, but Ollama ignores the field. The other four original missing-call cases did not reproduce in isolation, so their precise trigger remains unresolved. No backend repair or full500 rerun. Source prompt not redeployed to the API container. [Evidence and repeat procedure](docs/evidence/2026-09-27/gemma-guidance-diagnosis/README.md).

Laya generalization request (2026-09-27): user approved with "Dajesz". Read
[the approved approach](docs/LAYA_GENERALIZATION_APPROACH.md) before training
or evaluation. It excludes the existing 500 cases from training/model selection,
requires a separate frozen test, and preserves Gemma and historical evidence.
Resource preflight is blocked: serial AdamW completed one transient update, then
steady-state probe OOMed during step two at a 6500 MiB limit. Disk checkpoint
budget also fails. No trained weights saved, full corpus or 500-case evaluation.
See [evidence and resume conditions](training/laya-routing/README.md). Do not
change the method or use the old benchmark for model selection.

Completed full Gemma check (2026-09-27 local time): **471/500 correct (94.2%)**, 24 wrong routes and 5 missing native calls. All 29 failures retain full requests and raw responses, plus individual debug bundles. All 77 manual review gates and offline audits pass. The earlier 147 outcomes reproduce exactly. No retries, tuning, tool execution or mail. Previous evidence, generic agent and Compose are unchanged. This is synthetic model transport/routing evidence, not full application acceptance.
[Results, failures and repeat procedure](docs/evidence/2026-09-26/gemma-patched-500/README.md). No further run is implicit.

Latest completed failed-set check: both models ran all147 frozen cases on
`0.34.4-poc.gemma-native.2`. Gemma146correct/0wrong/1missing native call;
Qwen133correct/14wrong/0protocol errors, identical to its earlier outcomes.
Gemma case434 emits tool-like plain text, so first-call reliability is not100%.
All44 review gates and offline audits pass. No retries, tuning, mail or full500
run. Historical comparison and agent unchanged. Approach/results:
[failed-cases-patched](docs/evidence/2026-09-26/failed-cases-patched/README.md).
No additional evaluation is implicit.

Latest authorized repair: Ollama `0.34.4-poc.gemma-native.2` is applied locally.
Read [repeatable approach](docs/OLLAMA_GEMMA_TOOL_FIX.md) and
[report](docs/evidence/2026-09-26/ollama-gemma-fix/REPORT.md). The small Gemma GGUF
adapter uses native grammar and the exact official template; a narrow native
parser token fix replaces the rejected broad `--special` flag. Agent, prompt,
tools and weights are unchanged. First-tool Gemma, clean plain text, arbitrary
streaming tool, Qwen control and post-promotion smoke pass. Continuation still
fails on both old/new backends; tools+logprobs remain unsupported in native chat;
full argument-schema constraints/accuracy are not established. No mail or bulk
benchmark ran. Compose now builds services/ollama-candidate. Prior0.13.5 pin
instructions below are historical and superseded by this explicit repair.

Previous controlled diagnosis: the user requested establishing whether this is an
Ollama integration defect. See [report](docs/evidence/2026-09-26/gemma-integration-audit/REPORT.md)
and [approach](docs/evidence/2026-09-26/gemma-integration-audit/APPROACH.md).
The official Google prompt matches byte-for-byte. The same weights/request
succeed through the bundled native tool grammar with stock `--special`; disabling
the native grammar/parser reproduces the original invalid tokens exactly.
Ollama's Gemma rendered path bypasses this grammar. A separate native llama.cpp
delimiter-preservation defect was isolated. Three observed diagnostic generations,
no retries or application/backend source patches. Temporary process stopped;
normal Ollama unchanged. Do not claim full argument-schema enforcement or broad
model reliability from this one case. The bulk comparison remains stopped.

Latest instruction: user STOPPED the Gemma comparison at31/147 and requested
root-cause investigation. No bulk resume. Qwen completed133/147 correct; Gemma
returned31 invalid function names. See failed-cases-comparison/stop-e2b.json.
Inspect the actual backend rendering/parsing path before further inference.
The subsequent single token probe confirmed the model itself emits a department
as function name despite a correct rendered declaration. Gemma's dedicated
rendered completion path lacks tool-schema decoding constraints; its parser
passes through unknown names. The generic template/parser patches do not cover
this path. Evidence: `docs/evidence/2026-09-26/failed-cases-comparison/DIAGNOSIS_E2B.md`.
No repair or bulk resume occurred. Preserve the stopped checkpoint.

Latest handoff: [next steps.md](<../../next steps.md>) records the user's correction
to **Gemma 4 E2B Q4** and the approved common-backend 147-case comparison.
Read it before resuming; historical E4B references are superseded. The user has
now authorized execution of that handoff; the runner mapping is corrected to E2B.
Follow the comparison PROCEED.md and preserve all four frozen input hashes.

This is a standalone project. Do not import Resumer or sibling service code.
Read `docs/APPROACH.md` before resuming automation. The user approved implementation
and synthetic local testing on 2026-09-25, including separate containers, the
Service Layer Pattern and a fresh independent critic after implementation.

## Hard constraints: model API and observed debugging

- All model inference must use the OpenAI-compatible Chat Completions API. The
  shared agent uses LangChain ChatOpenAI; the infrastructure readiness probe uses
  standard HTTP against the same API. No ChatOllama, Ollama SDK, native inference endpoints,
  provider-specific client branches or response-repair code in the shared agent.
  Change providers through environment configuration. Model download/container
  provisioning remains infrastructure, not an alternative inference client.
- Do not run unobserved model tests. Read existing logs first; capture the actual
  request, raw response, parsed tool call, validation and delivery outcome with
  one request ID. Inspect each diagnostic case before continuing. A failure count
  alone is not debugging evidence. Never resume a bulk benchmark implicitly.
- The user authorized observed debugging after stopping the bulk run. Follow
  `docs/OBSERVED_DEBUGGING.md`; enable content tracing only for synthetic local
  cases, exclude transport credentials from logs, and restore normal logging afterward.
- `CLAUDE.md` imports this file as the repository instruction source.
- Observed diagnosis: model sometimes emits a department label as function name;
  the server hides it as empty content/no calls. Other errors use the correct
  function with a wrong department. Evidence: observed-debug/README.md under
  docs/evidence/2026-09-25. Do not label every missing_call as malformed JSON.
- LangChain setup audit: @tool emits the same schema as our StructuredTool when
  configured identically. A simpler diagnostic schema did not fix every failure;
  an observed named tool_choice request was not enforced by the current server.
  See docs/evidence/2026-09-25/langchain-tool-audit/README.md before claiming a fix.

- Domain and service modules depend only on Python standard library and their own ports.
- HTTP controllers validate/map requests; composition roots wire concrete adapters.
- Services communicate through versioned HTTP contracts or SMTP. No shared database,
  shared application package, filesystem calls into another service, or sibling build contexts.
- Only the agent's validated tool call can initiate delivery. Model text never proves sending.
- Mailer owns its SQLite delivery ledger. Never retry unknown SMTP outcomes automatically.
- Laya is a typed classifier behind a separate compatibility adapter, not native LLM tool calling.
- Use synthetic messages and Mailpit for tests. No production mail or keys from other projects.
- The approved 500-case Polish benchmark is in `verification/benchmark/cases-500.json`.
  Read `docs/BENCHMARK_APPROACH.md` before rebuilding or running it. There are 250
  scenario families with two correlated variants each, 100 cases per department.
  Preserve family grouping in any future splits and never send labels/rationales
  to the model. The original 15-case smoke test remains the default.
- Default launch is `docker compose up -d`. Provider changes use env only.
- Keep optional profiles documented in Compose: Laya runtime and adapter are
  disabled by default. Enabling a profile and selecting the model endpoint are
  separate settings; disabling a profile does not stop existing containers.
- Keep `README.md`, `docs/APPROACH.md`, `docs/VERIFICATION.md` and contracts current.
- The user approved correcting Laya's semantic routing on 2026-09-25.
  The model chooses a department from message content and descriptions; only the
  application maps that choice to a mailbox. Preserve this separation.
  `docs/LAYA_TUNING_APPROACH.md` records the executed integration correction and
  the separate, unexecuted weight-training proposal. No weights were trained.
- Tool schemas use standard JSON Schema only: enum plus described singleton
  alternatives in anyOf. No provider extensions in the shared agent. Laya's
  adapter translates those descriptions into typed choices. Keep the real SDK
  wire regression proving the classifier receives the same question/criteria.
- Mailpit needs both internal `smtp` and non-internal `mailpit-ui` networks for
  its loopback web port to be published by Docker. Validate the web UI from the
  host as well as MIME inside Compose; internal E2E alone misses this regression.
- Keep Laya's `TORCHINDUCTOR_CACHE_DIR` on writable `/tmp`. The numeric runtime
  UID has no passwd entry; PyTorch's implicit cache path fails during preload.
- Earlier semantic-correction checkpoint: 85 container tests passed; Laya E2E improves from
  6/15 to 13/15 but still fails acceptance. Ollama E2E passes 15/15 with the
  new department schema; results are recorded in `docs/VERIFICATION.md`.
  Per-case evidence and repeat commands are linked from `docs/VERIFICATION.md`.
- Earlier Ollama bootstrap runs intermittently failed their native-tool readiness
  probe. The later tool-wiring work below found malformed template serialization
  and led to a pre-regression Ollama pin plus explicit inference settings.
  Preserve earlier failures as evidence; do not weaken the native-call gate.
- Resource measurement reuses the approved synthetic test: see
  `docs/RESOURCE_MEASUREMENT.md`. Both model runtimes use about 1.9 GiB in this
  CPU setup; Laya's advantage is CPU time, not materially lower RAM.
  That repeat scored 13/15 for each provider, including two new Ollama mistakes.
  Preserve the distinction between the earlier 15/15 and this later 13/15 run.

## Tool-call integration correction, 2026-09-25

- Read `docs/TOOL_WIRING.md` before repeating Qwen diagnosis/benchmark. It records
  pinned upstream references, confirmed wire defects, commands and partial evidence.
- Use composition-root `build_model` in real wire tests. ChatOpenAI rewrites the
  normal max_tokens parameter; preserve the configured wire field via extra_body.
- Bootstrap and API share env inference settings, not service code. Empty reasoning
  and sampling options must remain omitted for Laya and arbitrary providers.
- Reject explicit length termination, malformed calls and invalid tool arguments.
  Never infer truncation from token counts; valid calls at the limit are allowed.
  Do not add provider-specific response heuristics to the shared agent.
- Use LangChain create_agent for binding, invocation and terminal tool execution.
  A single wrap_model_call middleware validates before delivery. No hand-written
  agent loop, corrective retry prompts or retries after mailer invocation.
- The earlier0.13.5 pin is superseded by the reviewed0.34.4 backend patch in
  OLLAMA_GEMMA_TOOL_FIX.md. Keep the pinned template serialization correction;
  do not reintroduce startup template rewriting.
- Preserve rejection categories and correlation without logging message content
  by default; opt-in synthetic debugging follows OBSERVED_DEBUGGING.md.
  Schema validation cannot guarantee the model chooses the correct department.
- User stopped the 500-case benchmark. Its interrupted output is partial historical
  evidence only; do not resume it without an explicit request. Use focused unit,
  contract and small live smoke checks for this repair.
- Earlier repair checkpoint: 116 host/container tests, verified stock Qwen template
  on Ollama 0.13.5, 5/5 live smoke messages with MIME checks. Fresh critic found no
  code blocker. Keep this narrow integration evidence separate from model accuracy.
- Provider-neutrality correction: x-choice and token-count rejection removed.
  120 host/container tests pass, including env-only switches through the real SDK
  and exact preservation of Laya input. Live evidence is in docs/VERIFICATION.md.
- Latest live provider switch: Ollama 5/5, Laya 4/5 correct routes (same known
  computer-to-IT error); all 10 captured mails passed MIME checks. Default Ollama
  restored healthy, optional Laya stopped. Do not claim Laya accuracy fixed.

- User explicitly reauthorized the full 500-case check ("Check with all 500 messages")
  after the generic-agent repair. Run the frozen corpus on the current Ollama
  configuration, record all failures, and preserve historical interrupted runs.

- Latest user instruction stopped the reauthorized run at 241 completed cases:
  176 correct, 52 wrong departments, 13 missing tool calls. Preserve the partial
  evidence; do not resume without explicit authorization. See BENCHMARK_APPROACH.md.
- Read `docs/MODEL_RELIABILITY_RESEARCH.md` for the subsequent upstream research.
  Its proposed experiments are unexecuted; the research request did not restart testing.

- Routing-policy revision: category criteria are also in the system prompt; the
  tool description is short. Preserve Laya's described enum contract.
  MODEL_TOOL_CHOICE is optional (blank/auto/required/named), applied through the
  existing LangChain middleware. Never claim named selection is enforced by
  every compatible endpoint. Follow OBSERVED_DEBUGGING.md for observed replays.

- Routing-policy replay: 77 targeted tests pass; two of four selected public
  cases still fail with missing calls. Case 051's separate token probe again
  used a department as the function name. See routing-policy/README.md under
  docs/evidence/2026-09-25. Do not describe the local model/backend as fixed.

- Observed model-only comparison: qwen3:4b-instruct-2507-q4_K_M passed all four
  selected cases where the revised 1.7B run passed two. Application image and
  per-case wire payloads unchanged except model. See qwen4b-instruct/README.md
  under docs/evidence/2026-09-25. Candidate remains active with tracing off;
  repository defaults unchanged. Four HR/payroll examples do not establish
  broader accuracy or a clean bootstrap pass. The 500-case run stays stopped.

- Latest user instruction explicitly authorizes a new full 500-case run on
  qwen3:4b-instruct-2507-q4_K_M. Follow the final section of
  docs/BENCHMARK_APPROACH.md: per-case trace/MIME audit, pause on every failure
  and every ten cases for operator review, no retries/tuning. Evidence directory
  docs/evidence/2026-09-25/qwen4b-500/. Earlier stopped runs remain untouched.

- Latest user instruction STOPPED testing at 190/500 and requested an evidence
  audit. Do not resume or run additional inference. The saved run has 100 HR
  and 90 payroll cases only (95 scenario pairs); remaining classes untested.
  See stop.json and the latest BENCHMARK_APPROACH.md section. Preserve evidence
  and distinguish verified real deliveries from unproven general reliability.

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

## Approved Ollama backport

User approved PR17284 backport and focused observed verification. Follow
`docs/OLLAMA_BACKPORT.md` (repository root). Bulk testing remains stopped.

## Temperature and schema diagnostic, 2026-09-26

User requested temperature reduction and simpler schema, superseding EXAONE.
Observed four transport-only requests: temperature0 alone still invalid on394;
removing anyOf gives3/3 valid calls,2/3 correct departments. No production schema
change or mail. Approach/evidence: docs/evidence/2026-09-26/simple-schema/README.md
(path from repository root). Bulk benchmark remains stopped.

## English minimal-schema diagnostic

User approved testing the English prompt/minimal schema with failure-only records.
Three observed cases394,235,393 passed native call and route checks at temperature0.
Zero failures; no mail or production changes. Details and repeat approach:
`docs/evidence/2026-09-26/english-minimal/README.md` (repository-root path).

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

## Missing-call policy correction, 2026-09-26

The user requested fixing missing calls and explaining the500 failures.
Read `docs/evidence/2026-09-26/routing-policy-fix/README.md` and ANALYSIS.md
(repository-root directory) before resuming. The application system prompt now
requires forwarding every message, explicitly including other, and clarifies
company-specific category boundaries. Schema/Laya criteria and agent code remain
unchanged. Observed minimal-schema diagnostic:15native calls,14correct routes;
case474 remains wrong due to resolved history. Seven former missing calls pass.
81 router/wire/Laya/architecture tests pass. This is a prompt mitigation, not
server-enforced tool calling or a full500 pass. Do not restart the bulk run.

## Frozen failed-case comparison, 2026-09-26

User authorized comparing Qwen and Gemma4 E4B only on the147 previously failed
cases, freezing everything else. Inputs/settings are hashed under
`docs/evidence/2026-09-26/failed-cases-comparison/`. Preflight blocked: current
Ollama0.13.5-poc.17284 rejects Gemma4 with HTTP412 requiring a newer server.
No inference or runtime upgrade occurred. Do not change the frozen backend
implicitly; read that directory README before resuming.

## Isolated newer Ollama candidate, 2026-09-26

User requested investigating/patching newer Ollama. Build-only approach and logs:
`docs/evidence/2026-09-26/ollama-candidate/README.md`. Candidate0.34.4 carries
upstream PR18391 (template JSON) and PR17284 (unparsed output). Main Compose,
running0.13.5 and frozen147-case comparison remain unchanged. These patches
do not enforce tool_choice or establish Gemma inference correctness.
