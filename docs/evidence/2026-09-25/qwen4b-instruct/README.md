# Qwen3-4B-Instruct-2507: observed model comparison

All four selected public API cases passed with
`qwen3:4b-instruct-2507-q4_K_M`, versus two passing and two missing calls with
`qwen3:1.7b` under the same revised prompt. Each request was submitted separately;
the raw request/response, parsed call and captured MIME were inspected before
the next request. No application code, image, schema or prompt change was made.

| Case                      | Previous 1.7B          | 4B instruct | Public request time   |
| ------------------------- | ---------------------- | ----------- | --------------------- |
| 025: language training    | HR, pass               | HR, pass    | 20.363 s (first load) |
| 051: harassment reporting | Missing call, HTTP 502 | HR, pass    | 3.685 s               |
| 103: leave request        | Missing call, HTTP 502 | Kadry, pass | 4.402 s               |
| 001: interview scheduling | HR, pass               | HR, pass    | 3.962 s               |

Every raw response contained exactly one `send_department_email` call, using
`human_resources` or `payroll` as appropriate. Every call produced one captured
email with the expected recipient, Reply-To, original message body and request
ID. No retries, token repairs, extra inference after sending or diagnostic
logprobs replays were needed. The model server logs show exactly four Chat
Completions requests during this experiment.

This supports using the instruction-focused model as the next candidate. It
does not establish general reliability: these are four previously selected
diagnostic cases, covering HR and payroll only, with one sample per case. No
500-case evaluation, clean bootstrap verification or new Laya/OpenRouter test
was run. The full benchmark remains stopped.

## Configuration and runtime

The published [Ollama model tag](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M)
is the explicit instruct checkpoint, matching the
[Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507). Download
completed successfully with digest verification. The stock template and
parameters are preserved in model.modelfile.txt; no local template patch.

- Manifest SHA-256: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
- Ollama 0.13.5; Q4_K_M quantization; CPU only; serving context 4096.
- Request settings unchanged: reasoning_effort=none, temperature=0.7, top_p=0.8,
  max_tokens=1024, tool_choice omitted.
- comparison.json verifies that only the model field changed in each request
  versus ../routing-policy/. The model package includes a different stock chat
  template, so this is a package comparison, not an isolated weight-size test.
- runtime.json records unchanged application hashes and API image ID.
- Docker memory snapshot: 3.514 GiB for the Ollama container after a request;
  this is not peak RAM or a full resource benchmark. Ollama reported 3.5 GB
  model allocation and CPU serving.
- Ollama logged a CPU quota parsing warning for the value max during model load;
  all four completions nevertheless returned HTTP 200. No truncation observed.

The API remains on this candidate, healthy, with MODEL_TRACE=false. The
repository's default model remains qwen3:1.7b; a normal Compose recreation
without this experiment's env will restore that default. The final runtime
state is recorded in final-state.json.

## Logs and reproduction

- api.txt, ollama.txt and mailer.txt: saved service logs for the run.
- case-NNN-trace.json: correlated request, raw response, parsed result and delivery.
- case-NNN-wire-request.json: exact OpenAI-compatible body.
- case-NNN-result.jsonl: public API outcome and request ID.
- case-NNN.eml and inspection.jsonl: captured MIME and independent checks.
- model.env, model-manifest.json, model.modelfile.txt, model-info.txt, pull.log:
  model configuration, provenance and raw download output.
- resource-snapshot.json and loaded-model.txt: read-only runtime snapshots.

Read [OBSERVED_DEBUGGING.md](../../../OBSERVED_DEBUGGING.md) before repeating.
From the repository root, keep the candidate active without raw content tracing:

```sh
MODEL_TRACE=false docker compose --env-file docs/evidence/2026-09-25/qwen4b-instruct/model.env up -d --no-deps --wait --wait-timeout 60 api
```

For another observed run, use MODEL_TRACE=true and a fresh evidence directory;
copy inspect.py and the chosen single-case input there, then save the harness
result as case-NNN-result.jsonl. Run inspect.py before another case or API
recreation. Its output must go to inspection.jsonl and its saved logs/traces
must be preserved before disabling tracing. Do not rerun inspect.py here now:
it regenerates artifacts from current container logs, which were recreated.

Restore the original model if needed (weights and captured messages are kept):

```sh
MODEL_TRACE=false docker compose --env-file .env.ollama-example up -d --no-deps --wait --wait-timeout 60 api
```

## Independent evidence review

Fresh read-only critic model_comparison_critic found no evidence blocker. It
compared actual wire bodies, all 20 correlated log events, captured MIME and
application/manifest hashes, and independently confirmed one live Mailpit
message per request. The critic emphasized the limited HR/payroll sample and
that the new model package includes both different weights and a stock template.
It performed no inference or mutations.
