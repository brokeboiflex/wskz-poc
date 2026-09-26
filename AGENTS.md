# Message router PoC

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
- Pin Ollama 0.13.5, verified before the Qwen tool rendering regression introduced
  in 0.14.0. Upstream #14601 / #18391 remains open as of this repair; 0.34.4 also
  retains the affected code. Do not reintroduce startup template rewriting.
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
