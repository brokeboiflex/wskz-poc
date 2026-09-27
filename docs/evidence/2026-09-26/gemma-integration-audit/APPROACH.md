# Gemma integration isolation

User authorized establishing whether the repeatable Gemma tool-call failure is
an Ollama integration bug. Continue the observed diagnostic approach from
`../failed-cases-comparison/DIAGNOSIS_E2B.md` and `../../../OBSERVED_DEBUGGING.md`.
Native tool calling and the shared OpenAI-compatible interface remain required.

## Procedure

1. Preserve the frozen comparison and inspect existing raw tokens, rendered prompt,
   exact model metadata, runtime version and server logs.
2. Download only small public upstream source/template files. Record URLs,
   revisions and SHA-256 hashes. Compare Google's official Gemma E2B chat template
   against the captured Ollama prompt for exactly the saved messages and tools.
3. Inspect tokenization, rendering, sampling and parsing boundaries in the pinned
   Ollama and bundled llama.cpp implementation. Separate a confirmed mismatch
   from an untested causal hypothesis.
4. When a concrete hypothesis is available, run one isolated, recorded synthetic
   OpenAI-compatible request at a time. Preserve model weights, user message,
   declared tools and sampling unless a single explicitly documented diagnostic
   variable is being isolated. Capture the full request/response and inspect it
   before any further request. Never execute the returned tools or retry a request
   automatically. No bulk benchmark, application rewrite or production patch.
5. Save findings and remaining uncertainty in this directory, link from the PoC
   instructions and handoff, and retain all earlier evidence.

## Prerequisites, commands and outputs

Existing candidate Ollama container and downloaded `gemma4:e2b` weights; API
container is a transport host only. Python, Docker Compose and public source
access are required. No external credentials or email delivery are involved.

Read-only runtime checks: `docker compose ps -a`, targeted `docker compose logs
--no-color ollama`, and container process/model metadata inspection. Rendering
inspection may use `_debug_render_only`; this does not perform inference.
Actual inference always uses `/v1/chat/completions`, following the existing
`../simple-schema/probe.py` transport. Any new diagnostic command/script and its
exact parameters are saved here before execution.

Inputs: frozen request, rendered prompt, token trace, model config and comparison
metadata under `../failed-cases-comparison/`. Outputs: fetched references,
source manifest, template comparison, individually named diagnostic requests and
responses, and a final report. Scripts refuse overwriting completed evidence.

## Checkpoint and validation

No diagnostic is automatically resumed after interruption. Read saved outputs
and inspect running requests first. Frozen input hashes and the stopped31/147
Gemma and completed147/147 Qwen records must remain unchanged. A defect is causal
only when a controlled comparison supports it; source differences alone are not
proof. Passing one case does not establish model-wide reliability.

## Selected controlled comparison

The official Google template renders byte-identically to the saved Ollama prompt.
The bundled llama.cpp build identifies itself as `161755f29`. Its native Gemma
tool parser builds a grammar limiting function names; Ollama's rendered path
bypasses that integration. The native Gemma grammar currently has a TODO for
argument-schema enforcement, so do not claim full schema enforcement.

Use the same bundled unmodified `llama-server` binary and installed GGUF in a
temporary process inside the existing Ollama container. No new image, weights,
application code or model metadata changes. The process listens only on the
existing internal Docker network, port18081, not a published host port. Existing
Ollama models are already unloaded; no request is running. Copy the official
template to `/tmp/gemma-integration-audit.jinja`, then run `launch-native.sh`.
The launch script records its process ID and pins original context/batch settings
and the model's effective sampling defaults. `reasoning_effort:none` remains in
the original request. The exact saved request goes to `/v1/chat/completions`.

Run `python3 probe.py LABEL ENDPOINT REQUEST_FILE` once, from this directory or
with absolute paths. It saves request, transport output, response and summary;
refuses existing attempt directories; never sends email or automatically retries.
Inspect each result and server log before selecting a further control. An optional
second process with the stock `--skip-chat-parsing` flag can isolate the native
tool grammar, while retaining the same messages, tools, template and weights.
This is a diagnostic, not a proposal to return unparsed text in the application.

Stop only the temporary PID saved in `/tmp/gemma-integration-audit.pid`, after
verifying its command line. The normal Ollama service and model volume remain.
For repeatability, template comparison uses
`uv run --no-project --with jinja2==3.1.6 python compare_template.py`.

Native first probe generated the registered name but returned raw content: token52
(Gemma's special string delimiter) was decoded to an empty string. The bundled
native parser's `preserved_tokens` omits it. Test the existing `--special` CLI
option as an isolated output-decoding control, then `--special --skip-chat-parsing`
to disable the native grammar/parser while leaving prompt and weights unchanged.
No source patch or custom response repair is involved. Retain each launch log.
