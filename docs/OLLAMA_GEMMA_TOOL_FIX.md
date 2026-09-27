# Approved Ollama Gemma tool integration patch

Update2026-09-27: generic tool-choice transport is now patched in **0.34.4-poc.tool-choice.2**, preserving the Gemma integration described below. Required is enabled through existing app configuration; guidance deployed. Eight saved missing calls, Qwen and protocol controls pass. [New approach, evidence and current rollback](evidence/2026-09-27/ollama-tool-choice/README.md). Earlier image versions below are historical.

The user explicitly authorized patching Ollama after the controlled diagnosis in
[gemma-integration-audit](evidence/2026-09-26/gemma-integration-audit/REPORT.md).
This approval covers implementing the backend correction, building the image,
focused observed validation and applying the verified image locally. It does not
resume the stopped bulk benchmark or authorize publishing upstream messages.

## Implementation approach

Keep LangChain, the generic agent, prompts, tool schemas and model weights
unchanged. Work against pinned Ollama0.34.4 and the bundled llama.cpp engine.
Integrate its existing native Gemma tool-call path using the verified official
chat template and preserve the special tokens that its parser requires. The
first candidate using stock `--special` passed the tool case but leaked
`<turn|>` into plain text; it was rejected. The final patch adds only the missing
string delimiter to the native parser preserved-token list and rebuilds the
matching `libllama-common`, leaving the official engine/backend libraries intact.
The generic native history adapter also preserves assistant reasoning content. Do not
rename generated functions, add application model branches, introduce retries,
or replace native tool calling with structured classification.

Package the fix as a reviewable backend patch beside the existing candidate
patches with checksums, a reproducible Docker build and regression tests. Inspect
native-chat support, multimodal conversion, thinking controls and streaming
before selecting the smallest change. Preserve unsupported paths instead of
silently routing every model through an unverified template.

## Validation and application

1. Add meaningful backend tests for execution-path selection, tool transport,
   template/preserved-token handling and unaffected model paths. Demonstrate the
   regression against the unpatched code where feasible.
2. Build and test the isolated image without replacing the current service.
3. Use the existing model volume and an isolated local candidate endpoint; run
   one observed OpenAI-compatible request at a time. Start with the exact saved
   Gemma failure, then a Qwen control and narrow native-tool/streaming checks.
   Capture raw requests/responses and inspect every outcome. No automatic retry,
   returned-tool execution, email or bulk benchmark.
4. Apply the validated image to the existing Ollama service and record its
   image/version, health, unchanged agent/input hashes and remaining limitations.
   Preserve the previous image as rollback. Change only Ollama deployment files
   needed to reproduce the approved patch.

## Inputs, outputs and recovery

Inputs: `services/ollama-candidate/`, official pinned sources, downloaded model
volume, frozen request and source snapshots in the integration audit. Prerequisites:
Docker/build cache, disk space, public source access, and the current API container
as a transport host. No external credentials are required or recorded.

Outputs: patch/build files, backend regression evidence, individually recorded
diagnostics and final verification under `evidence/2026-09-26/ollama-gemma-fix/`.
Exact build/launch/probe/rollback commands and checksums are added here as the
implementation is finalized. Completed diagnostic directories are checkpoints;
read them before resuming and never overwrite or replay them automatically.
BuildKit caches may resume interrupted builds. Keep the147-case comparison frozen.

Known limit: the bundled native Gemma grammar constrains function names and value
syntax but does not yet enforce the complete JSON argument schema. Retain generic
application validation; do not claim all models or all requests are guaranteed.

## Final build and observed commands

Run from the PoC root. Completed artifacts must be read before another run;
`probe.py`/`render.py` refuse to overwrite their output directory. Use a new label
only for an explicitly intended diagnostic and inspect it before the next case.
These are individual checks, not a benchmark loop.

```sh
docker build --progress=plain \
  -t wskz-ollama-candidate:0.34.4-poc.gemma-native.2 services/ollama-candidate

docker run -d --name wskz-gemma-fix-validation-2 \
  --network message-router_inference \
  -v message-router_ollama-models:/root/.ollama:ro \
  -e OLLAMA_HOST=0.0.0.0:11434 -e OLLAMA_NUM_PARALLEL=1 \
  -e OLLAMA_CONTEXT_LENGTH=4096 -e OLLAMA_KEEP_ALIVE=5m -e OLLAMA_DEBUG=1 \
  wskz-ollama-candidate:0.34.4-poc.gemma-native.2

python3 docs/evidence/2026-09-26/ollama-gemma-fix/probe.py \
  gemma-fixed-original \
  http://wskz-gemma-fix-validation-2:11434/v1/chat/completions \
  docs/evidence/2026-09-26/ollama-gemma-fix/gemma-request.json
```

The example label/container above already exists as a completed checkpoint; do
not rerun it blindly. Other individually inspected labels/inputs were
`gemma-fixed-plain` / `plain-request.json`, `gemma-stream` / `stream-request.json`,
`gemma-continuation` / `continuation-request.json`, and `qwen-control` /
`qwen-request.json`. The continuation failed on both candidate and baseline;
see the report. The diagnostic `logprobs` flag was omitted after a recorded
HTTP400, because the shared native adapter always requests internal streaming.
No sampling or input content was changed in the original-case check.

Only one loaded large model was kept at a time. `ollama stop gemma4:e2b` inside
its container unloads it without removing weights. Model volume is read-only in
validation containers. No tools or mailer are invoked by these probes.

After inspecting results and stopping the temporary candidate:

```sh
docker stop wskz-gemma-fix-validation-2
docker compose config --quiet
docker compose up -d --no-build --no-deps --wait ollama
docker compose exec -T ollama ollama --version
python3 docs/evidence/2026-09-26/ollama-gemma-fix/probe.py \
  promoted-gemma http://ollama:11434/v1/chat/completions \
  docs/evidence/2026-09-26/ollama-gemma-fix/gemma-request.json
python3 docs/evidence/2026-09-26/ollama-gemma-fix/audit.py
```

Normal Compose now builds `services/ollama-candidate` and uses the final image;
no `/tmp` override is needed. The application model remains env-configured.
No tracing flag was added to the normal service. ARM64 local validation only.

During this run Docker's `docker-credential-desktop get` hung on public pulls.
The build succeeded with an isolated config containing empty `auths` and
`cliPluginsExtraDirs: ["/Users/mini/.docker/cli-plugins"]`, using:

```sh
docker --config /tmp/wskz-docker-public \
  --host unix:///Users/mini/.docker/run/docker.sock build --progress=plain \
  -t wskz-ollama-candidate:0.34.4-poc.gemma-native.2 services/ollama-candidate
```

This is an optional local build workaround; no credentials or permanent Docker
settings were changed. The Dockerfile pins Ollama, native source and patches;
[provenance.json](evidence/2026-09-26/ollama-gemma-fix/provenance.json) records
final image and binary hashes. BuildKit caches resume interrupted builds.

## Rollback

The previous image `wskz-ollama-candidate:0.34.4-poc.18391.17284` is retained.
For an intentional rollback, save this override as `/tmp/wskz-ollama-rollback.yml`:

```yaml
services:
  ollama:
    image: wskz-ollama-candidate:0.34.4-poc.18391.17284
```

Then run:

```sh
docker compose -f docker-compose.yml -f /tmp/wskz-ollama-rollback.yml \
  up -d --no-build --no-deps --wait ollama
```

This restores the prior integration failure. Normal Compose again selects the
new image; update the tracked Compose explicitly if rollback must persist.
Never delete the model volume or frozen benchmark artifacts as part of rollback.

Final results and limitations: [REPORT.md](evidence/2026-09-26/ollama-gemma-fix/REPORT.md).
