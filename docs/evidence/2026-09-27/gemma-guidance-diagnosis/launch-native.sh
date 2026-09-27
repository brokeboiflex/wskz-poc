#!/bin/sh
set -eu
# Execute inside the existing Ollama container. Optional argument is a stock flag.
echo $$ > /tmp/gemma-missing-diagnosis.pid
exec /usr/lib/ollama/llama-server \
  --model /root/.ollama/models/blobs/sha256-4e30e2665218745ef463f722c0bf86be0cab6ee676320f1cfadf91e989107448 \
  --mmproj /root/.ollama/models/blobs/sha256-4e30e2665218745ef463f722c0bf86be0cab6ee676320f1cfadf91e989107448 \
  --alias gemma4:e2b --host 0.0.0.0 --port 18081 --no-webui --offline \
  -c 4096 -np 1 --load-mode none --flash-attn auto -b 512 -ub 512 \
  --context-shift --keep 4 --jinja \
  --chat-template-file /tmp/gemma-missing-diagnosis.jinja \
  --temp 0 --top-k 64 --top-p 0.8 --min-p 0 --typical 1 \
  --repeat-penalty 1 --repeat-last-n 64 --reasoning off \
  --log-verbosity 5 --no-log-prefix --no-log-timestamps "$@"
