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
- Default launch is `docker compose up -d`. Provider changes use env only.
- Keep `README.md`, `docs/APPROACH.md`, `docs/VERIFICATION.md` and contracts current.
- Mailpit needs both internal `smtp` and non-internal `mailpit-ui` networks for
  its loopback web port to be published by Docker. Validate the web UI from the
  host as well as MIME inside Compose; internal E2E alone misses this regression.
- Keep Laya's `TORCHINDUCTOR_CACHE_DIR` on writable `/tmp`. The numeric runtime
  UID has no passwd entry; PyTorch's implicit cache path fails during preload.
- Runtime evidence from 2026-09-25: 68 container tests pass; Ollama E2E passes
  15/15, while Laya E2E fails with 6/15. Preserve that distinction in claims.
  Per-case evidence and repeat commands are linked from `docs/VERIFICATION.md`.
- Ollama bootstrap intermittently failed its native-tool readiness probe during
  runtime tests. Subsequent probes passed, but the cause remains unresolved.
  Do not call startup fully reliable or weaken the probe to hide the failure.
