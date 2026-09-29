# Message router PoC

## Current scope and documentation

This is a standalone project. Do not import Resumer or sibling service code.
README.md is the canonical project documentation: startup, service contracts,
routing policy, backend patches, verification, debugging and experiment limits.
The user requested removal of the historical docs directory on 2026-09-29 after
preserving important information in README. This overrides older instructions
to maintain that directory or preserve its contents in the working tree.
Do not recreate it or require its old approach files. Keep README current.
Frozen training authorship/review records retain historical references and hashes;
do not rewrite them to repair archival links. README supersedes those instructions.

Final task acceptance on 2026-09-28 passed 134 tests on both host and container,
15/15 observed HTTP → native Gemma tool → SMTP/Mailpit cases, and an additional
README request. Fresh-clone/source-build/empty-model-volume initialization was
verified before the orchestration-only readiness fix. Two immediate-HTTP
restart checks verified that fix. Keep the default `ready` service depending on
healthy API. README records provenance, retained local evidence and limits.

Gemma `gemma4:e2b` is the default, with patched Ollama
`0.34.4-poc.tool-choice.2`, temperature 0 and required tool choice.
Historical same-500 results: Gemma 493/500; validation-selected Laya epoch 1
432/500. These are exposed synthetic regression results, not unseen-data
accuracy or SMTP acceptance. No comparable RAM/cost ratio was measured.

Laya training ended after two epochs on the user's instruction. Validation:
epoch 1 447/500, epoch 2 443/500. The separate held-out test was not run.
No further training, inference benchmark or critic is implicitly authorized.
Read README's Laya section and training/laya-routing/RUNBOOK.md before any
separately requested continuation. Keep frozen training data/code/checkpoint
hashes intact; never use the old benchmark to tune or select the model.

## Implementation constraints

- Domain/service modules depend only on the standard library and their ports.
  Controllers validate/map requests; composition roots wire adapters.
- Services communicate through versioned HTTP or SMTP. No shared database,
  shared application package, sibling imports or sibling build contexts.
- All application model inference uses OpenAI-compatible Chat Completions.
  The shared agent uses LangChain ChatOpenAI; infrastructure readiness uses
  standard HTTP. No ChatOllama, Ollama SDK, provider-specific application branch,
  response repair, guessed tool calls or corrective retries.
- Use LangChain `create_agent` and one validation middleware. The single
  `return_direct=True` tool ends execution. Only its validated call initiates
  delivery; model text never proves sending. No inference after delivery.
- Model input contains message text and department criteria, not sender address,
  mailbox credentials, expected labels, benchmark IDs or rationales.
  The model chooses a department; only the application maps it to a mailbox.
- Preserve the standard enum plus described singleton anyOf schema. Laya's
  adapter translates descriptions into typed choices; it is not native LLM
  tool calling. Keep real SDK wire and provider-neutrality regressions.
- Validate the exact tool name, one department argument and its enum value.
  Reject malformed/multiple/missing calls and explicit length termination.
  Token usage at the limit alone is not proof of truncation.
- Keep `MODEL_TOKEN_LIMIT_FIELD` serialization through the calibrated
  `extra_body` path. Preserve omitted optional settings for other providers.
  Bootstrap and API share settings through env, not shared service code.
- Mailer owns its SQLite ledger and reserves delivery before SMTP. Never retry
  unknown outcomes automatically or equate queued with submitted. A new public
  POST is a new request, not an idempotent replay of the previous one.
- Tests use synthetic messages and Mailpit only. Never use another project's
  keys, production mail or arbitrary external recipients.
- Preserve checksummed backend patches, native token preservation and tool-choice
  transport under services/ollama. Do not replace them with stock
  upstream, template rewrites at startup or application-specific heuristics.

## Operation and verification

- Default launch is `docker compose up -d`; provider selection uses env only.
  Laya profiles are optional. Disabling a profile does not stop its containers.
- Preserve the `ready` startup barrier, model-init native-tool readiness gate,
  internal SMTP network, loopback ports and Mailpit's extra mailpit-ui network.
  Check Swagger and Mailpit from the host, not just inside Compose.
- Keep Laya's TORCHINDUCTOR_CACHE_DIR on writable /tmp for its numeric UID.
- Read README's diagnostics and existing logs before requested model tests.
  Observe correlated request, raw response, parsed call, validation and actual
  delivery. Inspect each diagnostic before continuing; do not resume bulk runs
  implicitly. Default acceptance corpus is verification/cases.json (15 cases).
- Trace content only for synthetic local data. Preserve relevant logs before
  recreating containers and restore MODEL_TRACE=false after diagnostics.
  Never replay uncertain submissions or hide failures with retries.
- The 500-case benchmark has 250 paired scenario families, 100 cases per
  department. Preserve family grouping, first-attempt outcomes and evidence
  boundaries; do not call it an independent real-world test.
- Cleanup of documentation does not authorize restarting services, retraining,
  deleting weights, mail volumes, local evidence or other project directories.
- Commit, branch or push only when explicitly requested. Preserve unrelated
  changes. CLAUDE.md imports this file as the instruction source.
