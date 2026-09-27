# Approved common-backend comparison

**Superseded by user stop:** Gemma stopped at31/147. Do not execute the comparison
commands below without a new request. Follow [DIAGNOSIS_E2B.md](DIAGNOSIS_E2B.md)
for the completed root-cause investigation and saved evidence.

Correction and resume, 2026-09-26: the user selected **Gemma 4 E2B Q4**, then
explicitly requested proceeding with `next steps.md` at the Resumer root.
The runner now selects `gemma4:e2b`; the original E4B preflight evidence remains
historical. Both models remain non-thinking: the exact Qwen Instruct model does
not support thinking. No frozen inputs or request settings changed.

User explicitly authorized proceeding after candidate patch verification. Original
blocked freeze remains immutable. Both models now use the same candidate image
`sha256:2ed7eee57edd0a0a2ce423a9ba38259daa01aaed2be337608e9ae1e0fbc0fb31`,
Ollama0.34.4-poc.18391.17284. Only model differs between requests. All147 original
failed cases, corrected prompt, minimal tool schema and sampling settings remain
byte-identical to freeze.json. No mail, agent edit, retries or prompt adjustment.
This measures recovery on a selected failure set, not general accuracy.

Prerequisites: candidate built using ../ollama-candidate/README.md, Docker,
existing Qwen weights, network to download Gemma4 E2B Q4. Activate with a temporary
Compose override setting ollama.image to the candidate tag and use
`docker compose -f docker-compose.yml -f /tmp/wskz-comparison-ollama.yml up -d --no-build --no-deps --wait ollama`.
Then `docker compose exec -T ollama ollama pull gemma4:e2b` (management only).
Save model metadata/digests and backend manifest before evaluation. Do not change
Docker resources or backend parameters between models. If model cannot load,
inspect logs before continuing; never turn infrastructure errors into route scores.

Run `python3 docs/evidence/2026-09-26/failed-cases-comparison/compare.py MODEL_KEY`
from the standalone message-router repository root. MODEL_KEY is qwen or gemma.
The runner uses existing HTTP probe through the API container to
http://ollama:11434/v1/chat/completions. No native inference or tool execution.
Run serially, inspect every failure and every10 completed cases before typing
continue. Saves only failure request/raw response details, outcome metadata for
all cases, and review gates. Failure pauses include raw response and case text.
Never automatically acknowledge gates. Preserve started markers: resume skips
completed cases but refuses an unresolved in-flight request, avoiding duplicates.

After both models, audit case coverage, hashes, exact request differences, review
gates and protocol validation; create comparison table and failure-only report.
Keep the application unchanged and restore the previous0.13.5 server afterward
using base Compose with --no-build --no-deps --wait ollama. Do not run model-init.
No model promotion is implied by a selected-subset result.
