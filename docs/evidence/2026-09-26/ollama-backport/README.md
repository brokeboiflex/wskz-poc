# Ollama backport evidence

Build and upstream parser tests/vet: build.txt. Router tests: router-tests.txt
(34 passed). Runtime version:0.13.5-poc.17284. Image digest:image-id.txt.

case394 reproduces wrong function name send_department_it with correct department
it. Patched Ollama preserves it as content; unchanged app rejects it with502,
zero mail. case393 control succeeds with1native call/1mail, correct recipient,
Reply-To and original body. Full wire and parsed traces are case-_-trace.json;
inspection outcomes are case-_-inspection.json. api.txt and ollama.txt were saved
before turning tracing off. No other model requests were issued for this backport.

inspect.py performs read-only wire/MIME audits using existing500-run audit logic.
Source inputs remain in case-_.json; outcomes in case-_-result.jsonl.
Approach/reproduction/rollback: [OLLAMA_BACKPORT.md](../../../OLLAMA_BACKPORT.md).
