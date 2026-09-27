# Frozen failed-case comparison

**Stopped by user:** Qwen completed133/147 correct,14 wrong routes,0 protocol
errors. Gemma stopped at31/147, all31 invalid function names. No bulk resume.
[DIAGNOSIS_E2B.md](DIAGNOSIS_E2B.md) contains the rendered prompt, token trace,
confirmed cause and the requirements for a future repair. `stop-e2b.json` and
`diagnosis-audit.json` preserve the checkpoint. The full comparison audit remains
inapplicable because Gemma did not complete.

Latest correction, 2026-09-26: the user selected **Gemma 4 E2B Q4** and approved
resuming on the shared patched backend. Follow [PROCEED.md](PROCEED.md) and the
Resumer-root `next steps.md`. The E4B references and blocked status below are
historical evidence; the runner now uses `gemma4:e2b`.

After both models complete and all review gates are inspected, run the offline
audit from the PoC root:

```sh
python3 docs/evidence/2026-09-26/failed-cases-comparison/audit.py
```

It refuses incomplete runs and checks frozen inputs, exact failure requests,
native-call validation, all-case metadata, totals and review gates. It writes
`audit-e2b.json`, `RESULTS_E2B.md` and `FAILURES_E2B.md`; successful raw responses
remain intentionally unsaved. `backend-e2b.json` records the common runtime.

User approved comparison only on failed cases and instructed freeze everything.
Selection:147 unique failures (109wrong routes,38missing calls) from the completed
english-minimal-500 evaluation. Freeze the corrected routing-policy-fix prompt,
minimal diagnostic schema and identical temperature0,top_p0.8,max_tokens1024,
reasoning_effort=none,stream=false. Only model changes between Qwen3 4B Instruct
and Gemma4 E4B. No application edits, retries, prompt tuning or emails. Files and
SHA256 are in freeze.json. This is failure-set recovery, not overall accuracy.

First verify model compatibility with current Ollama0.13.5-poc.17284. Management
CLI pull is permitted; inference must use OpenAI-compatible Chat Completions.
Do not upgrade the server silently: that violates the frozen comparison.
If unsupported, record the blocker before any evaluation. No meaningful model-only
comparison is possible on different backend versions without explicitly changing
and refreezing the experiment. Preserve the current runtime and earlier evidence.

Preflight command from repository root:
`docker compose exec -T ollama ollama pull gemma4:e4b`

On compatibility success, reuse the observed transport runner method: serial
requests, inspect every failure and each10-case checkpoint, persist failure details
only plus outcome metadata. Never launch a bulk run before compatibility passes.

## Preflight result

Blocked before inference: current Ollama rejects gemma4:e4b with HTTP412,
"The model you are attempting to pull requires a newer version of Ollama."
Exact output: gemma-pull.txt. No inference, model switch or runtime upgrade occurred.
The frozen artifacts remain available. Comparison requires an explicitly approved
common newer backend for BOTH models, followed by a fresh freeze; results cannot
be compared as model-only changes across different Ollama versions.
