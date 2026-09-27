# Gemma work completed

The user accepted the Gemma work as complete on 2026-09-27 and requested documentation, commit/push of all PoC changes, Qwen removal and stopping remaining processes. The seven semantic errors remain recorded; no further prompt tuning or evaluation is implied.

## Delivered

- Integrated the small Gemma4 GGUF with Ollama's native template/grammar and fixed preservation of native tool delimiters. Backend changes live in checksummed patches under `services/ollama-candidate/`; generic application code has no model-specific repairs or retries.
- Added generic OpenAI `tool_choice` transport to Ollama's native runner. Required/none requests on unsupported rendered paths fail explicitly. Final version: `0.34.4-poc.tool-choice.2`.
- Added a minimal generic guidance block clarifying the existing department responsibilities.
- Evaluated all500 frozen synthetic cases once: **493 correct (98.6%),7 wrong routes,0 missing/invalid native calls**. Previous result471/500;27 previous failures fixed,2 persist,5 new routing errors. Every response and failure is saved and independently audited. [Final evidence and commands](evidence/2026-09-27/gemma-final-500/README.md).
- Selected `gemma4:e2b` Q4_K_M as the default in Compose, application settings, model initialization and local/example Ollama environment. Default temperature0, top_p0.8, reasoning none, max_tokens1024 and required tool choice. Empty optional values still support alternate providers. Bootstrap now forwards configured tool choice, including its own readiness function for named selection.
- Removed the installed `qwen3:4b-instruct-2507-q4_K_M` model; the model list contains only Gemma. Historical Qwen comparisons and backend compatibility tests remain as evidence.
- Stopped all PoC containers. Validation/training containers were already stopped; no remaining host benchmark/training process was found. Model volumes and evidence remain available.

## Cleanup and repeat procedure

Prerequisites: Docker Desktop/Compose, existing PoC model volume, repo Python virtualenv. Commands were run from the PoC root:

```sh
docker exec message-router-ollama-1 ollama rm qwen3:4b-instruct-2507-q4_K_M
docker exec message-router-ollama-1 ollama list
docker compose --profile laya stop
docker ps --format '{{.Names}} {{.Status}}'
.venv/bin/pytest -q
docker compose --env-file .env.ollama-example config --quiet
```

Cleanup logs, model inventory and validation output are under `docs/evidence/2026-09-27/gemma-completion/`. Removal was explicitly authorized. For repeated cleanup first inspect `ollama list` and container status; do not restart stopped services merely to repeat removal. No automatic inference or mail was performed during closure.

To start the configured Gemma stack later, rebuild changed application/bootstrap sources:

```sh
docker compose up -d --build
```

This future command starts the readiness probe and services; it was not run during closure because the user requested stopping processes. Existing stopped containers may retain their old environment until recreated. Real `.env` stays ignored. Provider changes remain environment-driven; the OpenRouter example requires an explicitly chosen tool-capable model.

Validation at closure: **134 tests passed**, Ruff and Compose configuration checks passed. The full500 run and backend Go tests were completed earlier; no extra model inference was performed.

## Evidence limits and other work

The500-case result uses a previously exposed synthetic corpus with250 paired families and the minimal comparison schema. It does not prove unseen-data accuracy or full agent/SMTP acceptance. Mailpit was absent before cleanup; no mail acceptance claim is added. The retained backend continuation/schema limits are documented in [the backend report](OLLAMA_GEMMA_TOOL_FIX.md).

Separate Laya training work is included in the requested all-changes checkpoint with its existing blocked status. No trained weights or successful Laya generalization result are claimed. See [Laya approach](LAYA_GENERALIZATION_APPROACH.md).

Earlier completed evidence hashes describe the source/configuration at evaluation time. Closure deliberately changes defaults in Compose/bootstrap; a historical whole-worktree preservation check can therefore report those later changes. Frozen benchmark payloads, responses and outcomes are unchanged.
