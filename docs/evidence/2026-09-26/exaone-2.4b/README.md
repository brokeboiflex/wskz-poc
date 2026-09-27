# EXAONE 3.5 2.4B compatibility check

User authorized trying this model. Use stock exaone3.5:2.4b-instruct-q4_K_M
on the patched Ollama through the existing OpenAI-compatible endpoint.
Download with `docker compose exec -T ollama ollama pull exaone3.5:2.4b-instruct-q4_K_M`.
Inspect metadata/template first; replay the saved case394 wire request changing
only model, and omitting reasoning_effort (non-reasoning model). Save request,
HTTP status and raw response. No tools are executed by this transport probe.
If native tools are unsupported, stop: no fabricated tool support or template
rewriting, no bulk run. Existing API configuration remains on Qwen until the
candidate supports the required protocol. Prerequisites: Docker and model storage.
Evidence: pull.txt, model.txt, request.json, response.json. Do not overwrite
completed requests; downloads may resume. This reuses observed-debugging protocol.
