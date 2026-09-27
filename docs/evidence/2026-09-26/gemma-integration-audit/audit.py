"""Verify the saved causal comparison offline; never performs inference."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "failed-cases-comparison"


def read(path):
    return json.loads(path.read_text())


original_request = read(PREVIOUS / "gemma-token-request.json")
original_response = read(PREVIOUS / "gemma-token-response.json")
labels = ["native-first", "native-special", "native-unconstrained"]
responses = {}
for label in labels:
    attempt = HERE / label
    assert read(attempt / "request.json") == original_request, label
    assert read(attempt / "summary.json")["http_status"] == 200, label
    responses[label] = read(attempt / "response.json")
    assert responses[label]["usage"]["prompt_tokens"] == 506, label

assert original_request["model"] == "gemma4:e2b"
assert original_request["temperature"] == 0
assert original_request["reasoning_effort"] == "none"
assert read(HERE / "template-comparison.json")["identical"]
official = (HERE / "google-rendered-prompt.txt").read_text()
native = read(HERE / "native-render-response.json")["prompt"]
assert native == official.removeprefix("<bos>")

original_tokens = "".join(
    token["token"] for token in original_response["choices"][0]["logprobs"]["content"]
)
assert original_tokens == (HERE / "native-unconstrained/generated-tokens.txt").read_text()
assert "call:human_resources{}" in original_tokens

first = responses["native-first"]["choices"][0]
fixed = responses["native-special"]["choices"][0]
assert first["finish_reason"] == "stop"
assert not first["message"].get("tool_calls")
assert fixed["finish_reason"] == "tool_calls"
calls = fixed["message"]["tool_calls"]
assert len(calls) == 1
assert calls[0]["function"]["name"] == "send_department_email"
assert json.loads(calls[0]["function"]["arguments"]) == {"department": "human_resources"}

first_tokens = first["logprobs"]["content"]
fixed_tokens = fixed["logprobs"]["content"]
assert [t["id"] for t in first_tokens] == [t["id"] for t in fixed_tokens]
assert len([t for t in first_tokens if t["id"] == 52]) == 2
assert all(t["token"] == "" for t in first_tokens if t["id"] == 52)
assert all(t["token"] == '<|"|>' for t in fixed_tokens if t["id"] == 52)
assert fixed_tokens[3]["token"] == "send"
assert fixed_tokens[3]["top_logprobs"][0]["token"] == "human"

for filename, expected in read(PREVIOUS / "freeze.json").items():
    assert hashlib.sha256((PREVIOUS / filename).read_bytes()).hexdigest() == expected
assert read(PREVIOUS / "gemma/summary.json")["completed"] == 31
assert read(PREVIOUS / "qwen/summary.json")["completed"] == 147

result = {
    "passed": True,
    "new_diagnostic_generations": len(labels),
    "identical_request_in_every_diagnostic": True,
    "official_template_matches_ollama": True,
    "native_prompt_matches_after_bos_handling": True,
    "unconstrained_control_reproduces_original_tokens_exactly": True,
    "native_tool_grammar_forces_registered_function_name": True,
    "special_token_flag_changes_decoding_not_generated_token_ids": True,
    "native_special_returns_one_valid_correct_tool_call": True,
    "frozen_comparison_unchanged": True,
    "bulk_resumed": False,
    "tool_execution": False,
    "application_or_backend_code_patched": False,
    "full_argument_schema_enforcement_proven": False,
    "full_model_reliability_proven": False,
}
(HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
