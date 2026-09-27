"""Check captured evidence offline. No inference, retries or delivery."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREVIOUS = HERE.parent / "failed-cases-comparison"


def read(path):
    return json.loads(path.read_text())


def call(label, name, arguments):
    summary = read(HERE / label / "summary.json")
    assert summary["http_status"] == 200, label
    assert summary["finish_reason"] == "tool_calls", label
    assert not summary["message"].get("content"), label
    calls = summary["message"]["tool_calls"]
    assert len(calls) == 1, label
    assert calls[0]["function"]["name"] == name, label
    assert json.loads(calls[0]["function"]["arguments"]) == arguments, label


for label in ("gemma-fixed-original", "qwen-control", "promoted-gemma"):
    call(label, "send_department_email", {"department": "human_resources"})
call("gemma-stream", "lookup_forecast", {"city": "Łódź"})
assert read(HERE / "gemma-stream/summary.json")["stream_done"]
plain = read(HERE / "gemma-fixed-plain/summary.json")
assert plain["http_status"] == 200 and plain["message"]["content"] == "READY"

original = read(PREVIOUS / "gemma-token-request.json")
original.pop("logprobs")
assert read(HERE / "gemma-fixed-original/request.json") == original
assert read(HERE / "promoted-gemma/request.json") == original
assert read(HERE / "promoted-gemma/summary.json")["usage"]["completion_tokens"] == 19

# The rejected candidate and pre-existing continuation failure remain evidence.
assert read(HERE / "gemma-original/summary.json")["http_status"] == 400
assert read(HERE / "gemma-plain/summary.json")["message"]["content"] == "READY<turn|>"
assert read(HERE / "gemma-continuation/request.json") == read(
    HERE / "gemma-continuation-baseline/request.json"
)
assert read(HERE / "gemma-continuation/summary.json")["message"]["content"] == ""
assert (
    read(HERE / "gemma-continuation-baseline/summary.json")["message"]["content"]
    == "<|tool_response>"
)
assert (HERE / "continuation-native-render/prompt.txt").read_text() == (
    HERE / "continuation-baseline-render/prompt.txt"
).read_text().removeprefix("<bos>")

for path, digest in read(HERE / "unchanged-inputs.json").items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
for path, digest in read(PREVIOUS / "freeze.json").items():
    assert hashlib.sha256((PREVIOUS / path).read_bytes()).hexdigest() == digest, path
assert read(PREVIOUS / "gemma/summary.json")["completed"] == 31
assert read(PREVIOUS / "qwen/summary.json")["completed"] == 147
for path, digest in read(HERE / "provenance.json")["patches"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path

assert "undefined symbol" not in (HERE / "native-linkage.txt").read_text()
assert "/usr/lib/ollama/libllama-common.so.0" in (HERE / "loaded-library.txt").read_text()
build = (HERE / "build-native.log").read_text()
assert "Missing Gemma string delimiter" in build
assert "Native grammar and narrow delimiter preservation passed" in build

result = {
    "passed": True,
    "fixed_initial_tool_call": True,
    "streaming_arbitrary_tool_and_unicode": True,
    "plain_output_clean": True,
    "qwen_control_passed": True,
    "promoted_service_smoke_passed": True,
    "continuation_limitation_preserved": True,
    "agent_and_frozen_comparison_unchanged": True,
    "bulk_resumed": False,
    "tool_execution": False,
    "full_application_or_model_acceptance": False,
}
(HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
