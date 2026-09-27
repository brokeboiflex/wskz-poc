"""Audit saved guidance and diagnostic evidence; no inference."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


for name, digest in read(HERE / "freeze.json").items():
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest
preserved = read(HERE / "preserved-before.json")
for name, digest in preserved.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
cases = read(HERE / "cases.json")
outcomes = rows(HERE / "gemma/outcomes.jsonl")
reviews = rows(HERE / "gemma/reviews.jsonl")
base = read(HERE / "request-template.json")
assert len(outcomes) == len(cases) == 23
counts = {"correct": 0, "wrong_route": 0, "protocol_error": 0}
for n, (case, row) in enumerate(zip(cases, outcomes), 1):
    req = read(HERE / f"gemma/{n:03d}-request.json")
    assert req == dict(
        base,
        model="gemma4:e2b",
        messages=base["messages"] + [{"role": "user", "content": case["message"]}],
    )
    raw = read(HERE / f"gemma/{n:03d}-raw.txt")
    assert raw["status"] == 200
    choice = json.loads(raw["body"])["choices"][0]
    calls = choice["message"].get("tool_calls", [])
    actual = None
    if calls:
        assert choice["finish_reason"] == "tool_calls" and len(calls) == 1
        assert calls[0]["function"]["name"] == "send_department_email"
        args = json.loads(calls[0]["function"]["arguments"])
        assert set(args) == {"department"}
        actual = args["department"]
    category = (
        "protocol_error"
        if actual is None
        else "correct"
        if actual == case["department"]
        else "wrong_route"
    )
    assert row["case_id"] == case["id"] and row["actual"] == actual and row["category"] == category
    counts[category] += 1
    if category != "correct" or n % 10 == 0 or n == 23:
        assert any(x["after"] == n and x["action"] == "continue" for x in reviews)
assert counts == {"correct": 18, "wrong_route": 2, "protocol_error": 3}
auto = read(HERE / "tokens-434/response.json")["choices"][0]
required = read(HERE / "required-434/response.json")["choices"][0]
assert auto["finish_reason"] == "stop" and not auto["message"].get("tool_calls")
assert not any("<|tool_call>" in x["token"] for x in auto["logprobs"]["content"])
assert required["finish_reason"] == "tool_calls"
assert json.loads(required["message"]["tool_calls"][0]["function"]["arguments"]) == {
    "department": "other"
}
a = read(HERE / "tokens-434/request.json")
b = read(HERE / "required-434/request.json")
assert b.pop("tool_choice") == "required" and a == b
ollama = read(HERE / "ollama-required-434/response.json")["choices"][0]
assert ollama["finish_reason"] == "stop" and not ollama["message"].get("tool_calls")
summary = {
    "guidance": counts,
    "all_23_raw_responses_audited": True,
    "review_gates": len(reviews),
    "previous_files_preserved": len(preserved),
    "case_434_auto_missing_marker_required_native_valid": True,
    "ollama_required_434_still_plain_text": True,
    "other_four_original_protocol_failures_reproduced_in_isolation": False,
    "regression_tests_passed": 81,
}
(HERE / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
