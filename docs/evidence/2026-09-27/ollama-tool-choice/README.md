# Approved generic Ollama tool-choice transport patch

User authorized the proposed patch with “No to dajesz”: accept standard tool_choice, forward it to the existing native grammar, enable required through existing application configuration, validate recorded failures through the normal OpenAI-compatible endpoint. This follows ../gemma-guidance-diagnosis/README.md and ../../../OLLAMA_GEMMA_TOOL_FIX.md. No full benchmark, response repair, retries or new model-specific application code.

Implement and test the missing OpenAI -> API -> native-runner field. Preserve omitted/auto behavior, support none by removing offered tools, and normalize a named function into a single declared tool plus required. Reject invalid/missing choices and unsupported required execution paths explicitly rather than silently ignoring them. Existing native templates/grammars own enforcement. Preserve all prior Gemma/backend patches.

Build a checksummed additional patch into version0.34.4-poc.tool-choice.1; reuse the already-tested native library layer. Before deployment validate in an isolated container using existing weights read-only, one observed request at a time, through /v1/chat/completions. Check original five missing calls and three new guidance missing calls, required434, auto/none/plain-text/stream/named controls and Qwen compatibility. Save all requests and raw responses. Do not execute tools or send mail. Use existing regression suites and an independent critic.

After successful review promote only the Ollama image, configure MODEL_TOOL_CHOICE=required using existing environment wiring and rebuild the API to include the already-approved guidance. Preserve the app model and unrelated Laya work. Record exact runtime identity, retained rollback image, tests, constraints and commands here. Existing attempts are checkpoints; never replay unknown in-flight requests. Docker build cache may resume interrupted builds. No model or evidence deletion.

## Completed 2026-09-27

Final image is **0.34.4-poc.tool-choice.2**, superseding candidate .1 after independent review. [Report](REPORT.md), [offline audit](audit.json), [review](critic-review.md), [runtime identity](promoted-runtime.json). All eight recorded missing-call cases returned one correct native call on their first required request. `auto` still reproduces434; `required` repairs it. Qwen, named, streaming, none and plain-text controls pass. No full500 rerun.

Prerequisites: Docker Desktop with existing `message-router` Compose network, API container containing httpx, model volume `message-router_ollama-models` containing the unchanged Gemma E2B and Qwen4B weights; Python3 for local evidence scripts. Run commands from the PoC root. Keep only one large inference model loaded. The shared API remains Qwen4B, temperature0/top_p0.8/reasoning none; existing `.env` now sets `MODEL_TOOL_CHOICE=required`. Secrets remain only in the ignored `.env`.

Build (normal Docker configuration works when registry access is available):

```sh
docker build --progress=plain -t wskz-ollama-candidate:0.34.4-poc.tool-choice.2 services/ollama-candidate
```

This session used the existing public-only Docker client config with `docker --config /tmp/wskz-docker-public --host unix:///Users/mini/.docker/run/docker.sock build ...` because the normal registry credential helper previously stalled. The Dockerfile pins/checksums source and every patch, proves the transport regression fails without forwarding, then runs Go tests/vet and builds the binary. Native library build remains the already-tested cached layer. `build-v2.log` is the final build; `build.log` records superseded .1.

Candidate launch used an isolated name, existing internal network, read-only weights and no host port:

```sh
docker run -d --name wskz-tool-choice-validation-v2 --network message-router_inference \
  -v message-router_ollama-models:/root/.ollama:ro \
  -e OLLAMA_HOST=0.0.0.0:11434 -e OLLAMA_NUM_PARALLEL=1 \
  -e OLLAMA_CONTEXT_LENGTH=4096 -e OLLAMA_KEEP_ALIVE=5m \
  wskz-ollama-candidate:0.34.4-poc.tool-choice.2
```

Each diagnostic was invoked separately and inspected before the next one:

```sh
python3 docs/evidence/2026-09-27/ollama-tool-choice/probe.py required-434 \
  http://wskz-tool-choice-validation-v2:11434/v1/chat/completions \
  docs/evidence/2026-09-27/ollama-tool-choice/requests/original-434.json
```

`probe.py` refuses an existing attempt directory. Every attempt saves request, endpoint/start time, transport stdout/stderr, raw response and parsed summary; streaming also retains original SSE. Frozen original cases034/101/288/404/434 and guidance cases012/066/074 differ from the historical requests only by required. Guidance local request ordinals are002/008/013, respectively. Candidate .1 ran only `qwen-required`; all remaining checks used .2. `images.json` binds candidate names to exact images. Both validation containers are now stopped, retained for inspection.

Before switching candidate models, `docker exec wskz-tool-choice-validation-v2 ollama stop gemma4:e2b` unloaded Gemma. No weights were removed. The normal post-promotion smoke uses endpoint `http://ollama:11434/v1/chat/completions`, label `promoted-434`, same frozen434 request.

The regular API build timed out fetching Python registry metadata (`api-build.log`). Because dependencies were unchanged, the source-only rebuild reused the exact previous API image, tagged `message-router-api:before-tool-choice`, with `Dockerfile.api-cached`; its only new layer copies current `router_app`. `api-build-cached.log` records success. The normal service Dockerfile remains unchanged.

```sh
docker tag sha256:2cb21baff3a6f71e9a436a8c5366a721bb8bdaec943a3da38d7e9a4871740133 message-router-api:before-tool-choice
docker build -f docs/evidence/2026-09-27/ollama-tool-choice/Dockerfile.api-cached \
  -t message-router-api:latest services/router
docker compose up -d --no-deps --no-build ollama api
```

Promotion preserves the running API's model and inference settings in ignored `.env`, changing only tool choice to required, and deploys the previously approved guidance. Runtime source hash matches the workspace. Mailpit was already absent; API/mailer readiness remains blocked by SMTP, so this is not mail-delivery acceptance.

Offline verification and safe checkpoint inspection:

```sh
.venv/bin/pytest -q tests/test_router.py tests/test_openai_wire.py tests/test_laya.py tests/test_architecture.py
python3 docs/evidence/2026-09-27/ollama-tool-choice/audit.py
docker compose ps
docker compose exec -T ollama ollama --version
```

The audit validates calls, departments, request preservation and907 historical file hashes. Existing attempt directories are durable checkpoints; inspect before resuming and do not overwrite or automatically retry an in-flight request. Build cache may resume builds. No further evaluation is implicitly authorized.

Rollback retains `wskz-ollama-candidate:0.34.4-poc.gemma-native.2` with image ID `sha256:006d00b95023fbfc98de1a193160edb1c48a314ebed61dc48c585f9db4157ca2`. To roll back, restore that Compose image tag and blank `MODEL_TOOL_CHOICE` in local `.env`, then `docker compose up -d --no-deps --no-build ollama api`. To also restore the pre-guidance API image, tag `message-router-api:before-tool-choice` as `message-router-api:latest` first. Do not delete models, evidence or unrelated Laya artifacts.
