#!/bin/sh
set -eu
echo $$ > /tmp/gemma-missing-matched.pid
exec /usr/lib/ollama/llama-server --model /root/.ollama/models/blobs/sha256-4e30e2665218745ef463f722c0bf86be0cab6ee676320f1cfadf91e989107448 --port 18081 --host 0.0.0.0 --no-webui --offline -c 4096 -np 1 --log-verbosity 5 --no-log-prefix --no-log-timestamps --jinja --chat-template-file /tmp/gemma-missing-diagnosis.jinja --mmproj /root/.ollama/models/blobs/sha256-4e30e2665218745ef463f722c0bf86be0cab6ee676320f1cfadf91e989107448 --load-mode none --flash-attn auto -b 512 -ub 512 --context-shift --keep 4
