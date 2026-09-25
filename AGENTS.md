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
