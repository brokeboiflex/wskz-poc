#!/bin/sh
set -eu
audit_pid=$(cat /tmp/gemma-integration-audit.pid)
audit_cmd=$(tr '\000' ' ' < "/proc/$audit_pid/cmdline")
case "$audit_cmd" in
  '/usr/lib/ollama/llama-server '*'--port 18081 '*)
    kill -TERM "$audit_pid"
    ;;
  *)
    echo "Refusing to stop unexpected process: $audit_pid" >&2
    exit 1
    ;;
esac
