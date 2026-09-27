# Final Gemma 500-case evaluation

Completed: **493/500 correct (98.6%), 7 wrong routes, 0 missing/invalid calls**. All500 first attempts, no retries/mail. [Report](REPORT.md), [failures](FAILURES.md), [audit](audit-e2b.json).

Authorized 2026-09-27: "Ok final evaluation on 500 cases. Save tokens report only once done. U can set a hour timeout so you don't have to watch it". This explicitly authorizes an unattended batch, superseding manual per-failure/ten-case pauses for this run. No automatic acknowledgements or invented human reviews.

Repeat the previous Gemma transport/routing evaluation on all 500 frozen cases, with the approved guidance and deployed Ollama tool-choice patch. Each case gets one POST to `/v1/chat/completions`, `tool_choice=required`, Gemma `gemma4:e2b` Q4_K_M. Same minimal tool schema and parameters as earlier: temperature 0, top_p 0.8, max_tokens 1024, reasoning_effort none, stream false. Only message text enters the user prompt; expected labels and rationales remain offline. No retries, tuning, tool execution or mail. The production application schema is richer than this retained comparison schema; this is not full application acceptance.

Prerequisites: running Docker Compose API container with httpx for network transport, healthy Ollama `0.34.4-poc.tool-choice.2`, existing unchanged Gemma weights, Python 3, sufficient disk and memory. `backend-before.json` captures verified image/model identity; `freeze.json` hashes inputs and probe. `preserved-before.json` hashes earlier evidence and implementation files. Existing API model/configuration stays unchanged. Missing Mailpit does not block model-only HTTP evaluation.

From the PoC root:

```sh
python3 verification/benchmark/build.py --check
python3 -u docs/evidence/2026-09-27/gemma-final-500/run.py gemma > docs/evidence/2026-09-27/gemma-final-500/run.log 2>&1
python3 docs/evidence/2026-09-27/gemma-final-500/audit.py
```

The runner uses the existing single-request probe and scoring rules, with an overall one-hour budget and 180-second HTTP timeout. Cases run serially. Every start marker, exact request, raw response and stderr is saved under `gemma/`; outcomes and summary are durable checkpoints. All failures also go to `gemma/failures.jsonl` and the offline audit extracts individual `failures/NNN/` debug bundles. Infrastructure failure stops the batch and is not scored as model error. An unresolved start marker prevents replay; after interruption inspect it and logs before resuming the same command. Never delete a marker to retry an unknown request.

After completion, the offline audit reclassifies every saved raw response, checks 500 unique ordered cases and frozen requests, creates RESULTS.md/FAILURES.md/audit-e2b.json and checks historical hashes. Save final runtime identity and service logs. Prior evidence remains unchanged. Do not implicitly rerun this evaluation.

The corpus is synthetic: 250 paired scenario families, 100 examples per department, already used in diagnosis and prompt guidance. Report this as regression evaluation, not independent held-out accuracy or SMTP acceptance.
