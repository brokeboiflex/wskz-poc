# Message router PoC

This is a standalone project. Do not import Resumer or sibling service code.
Read `docs/APPROACH.md` before resuming automation. The user approved implementation
and synthetic local testing on 2026-09-25, including separate containers, the
Service Layer Pattern and a fresh independent critic after implementation.

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
- Pass the tool's JSON schema dictionary to StructuredTool: LangChain's Pydantic
  subset loses the `x-choice` metadata. Validate calls with SendArguments before
  tool execution. Keep the real ChatOpenAI-to-adapter regression test.
- Mailpit needs both internal `smtp` and non-internal `mailpit-ui` networks for
  its loopback web port to be published by Docker. Validate the web UI from the
  host as well as MIME inside Compose; internal E2E alone misses this regression.
- Keep Laya's `TORCHINDUCTOR_CACHE_DIR` on writable `/tmp`. The numeric runtime
  UID has no passwd entry; PyTorch's implicit cache path fails during preload.
- Current semantic correction: 85 container tests pass; Laya E2E improves from
  6/15 to 13/15 but still fails acceptance. Ollama E2E passes 15/15 with the
  new department schema; results are recorded in `docs/VERIFICATION.md`.
  Per-case evidence and repeat commands are linked from `docs/VERIFICATION.md`.
- Ollama bootstrap intermittently failed its native-tool readiness probe during
  runtime tests. Subsequent probes passed, but the cause remains unresolved.
  Do not call startup fully reliable or weaken the probe to hide the failure.
- Resource measurement reuses the approved synthetic test: see
  `docs/RESOURCE_MEASUREMENT.md`. Both model runtimes use about 1.9 GiB in this
  CPU setup; Laya's advantage is CPU time, not materially lower RAM.
  That repeat scored 13/15 for each provider, including two new Ollama mistakes.
  Preserve the distinction between the earlier 15/15 and this later 13/15 run.
