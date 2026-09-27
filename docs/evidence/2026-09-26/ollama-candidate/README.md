# Newer patched Ollama candidate

User asked whether newer Ollama is still bugged and could be patched. Prepare an
isolated image; do not replace the running server or change the frozen comparison.
No model inference, download, application change or evaluation is part of this build.

## Approach and reproduction

Prerequisites: Docker with BuildKit and network access to public images, GitHub
and Go modules. From the standalone message-router repository root (`poc/message-router`):

```sh
set -C # refuse to overwrite an existing evidence log
docker build --progress=plain -t wskz-ollama-candidate:0.34.4-poc.18391.17284 services/ollama-candidate > docs/evidence/2026-09-26/ollama-candidate/build.txt 2>&1
```

The Dockerfile pins source and patch SHA256. It applies upstream PR18391 commit
c787f425f262c5cb6c75880ed09845b2a67b43c2 (JSON template serialization) and PR17284
commit72413e584cf98082b0e6159665529552baa4c1b0 (unparsed output preservation).
It first removes only the template implementation change, requires the new test
to fail with invalid JSON, restores the fix, runs template/thinking/tools tests
and template/tools vet, then compiles the Go server. Official0.34.4 inference
libraries remain in the final image. Existing old-server Dockerfile is untouched.
BuildKit cache is the checkpoint; rerun the same build after interruption, saving
subsequent logs under a new name. Never overwrite completed evidence.

The credential-helper workaround documented in docs/OLLAMA_BACKPORT.md is allowed
for these public images. It changes build authentication configuration only.

## Limits

These patches fix serialization and diagnostic loss. They do not enforce
required/named tool_choice or guarantee correct department selection. Gemma uses
a separate parser, so PR17284 does not establish lossless Gemma parsing.
No inference compatibility or routing improvement is established by unit tests.
To compare models later, both must run on the same candidate backend with the
same frozen inputs/settings; retain the original blocked freeze and create a
new backend manifest. Do not silently compare new Gemma results to old Qwen runs.

References:

- https://github.com/ollama/ollama/pull/18391
- https://github.com/ollama/ollama/pull/17284
- https://github.com/ollama/ollama/issues/17921

Startup check after build (isolated ephemeral container, no ports, model volumes,
weights or inference):

```sh
set -C
docker run --rm --entrypoint sh wskz-ollama-candidate:0.34.4-poc.18391.17284 -c '
  ollama serve & server_pid=$!
  trap "kill $server_pid; wait $server_pid" EXIT
  for attempt in $(seq 1 30); do
    if ollama list; then ollama --version; exit 0; fi
    sleep 1
  done
  exit 1
' > docs/evidence/2026-09-26/ollama-candidate/startup.txt 2>&1
```

## Result

Build and isolated startup passed. `build.txt` records the expected stock
regression failure, passing patched template/thinking/tools suites, vet and
compilation. `pinned-build.txt` confirms the final digest-pinned Dockerfile builds
from those same cached layers. `startup.txt` confirms empty model inventory and
version0.34.4-poc.18391.17284. No inference or emails occurred.

Fresh independent critic found no blocker in this isolated build scope after
reviewing patches, checksums, tests and isolation. All four frozen comparison
input hashes remain unchanged; the running stack still uses0.13.5-poc.17284.
Startup does not verify model loading or inference compatibility.
