"""Offline audit only; never invokes inference or sends mail."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CASES = json.loads((ROOT / "verification/benchmark/cases-500.json").read_text())
checks = []
rows = []


def check(condition, description):
    assert condition, description
    checks.append(description)


def read(label, name):
    return json.loads((HERE / label / name).read_text())


for label in [
    "required-034",
    "required-101",
    "required-288",
    "required-404",
    "required-434",
    "guidance-012",
    "guidance-066",
    "guidance-074",
]:
    req = read(label, "request.json")
    number = label.split("-")[1]
    local_number = {"012": "002", "066": "008", "074": "013"}.get(number, number)
    source = ROOT / (
        f"docs/evidence/2026-09-26/gemma-patched-500/failures/{number}/request.json"
        if label.startswith("required")
        else f"docs/evidence/2026-09-27/gemma-guidance-diagnosis/gemma/{local_number}-request.json"
    )
    original = json.loads(source.read_text())
    check(req == dict(original, tool_choice="required"), label + ": only tool_choice changed")
    response = read(label, "response.json")
    transport = json.loads((HERE / label / "transport.stdout").read_text())
    check(transport["status"] == 200, label + ": HTTP200")
    choice = response["choices"][0]
    calls = choice["message"].get("tool_calls", [])
    check(len(calls) == 1 and choice["finish_reason"] == "tool_calls", label + ": one native call")
    call = calls[0]["function"]
    check(call["name"] == "send_department_email", label + ": declared function")
    args = json.loads(call["arguments"])
    expected = CASES[int(label.split("-")[1]) - 1]["department"]
    check(args == {"department": expected}, label + ": correct department")
    check(req["tool_choice"] == "required", label + ": required on wire")
    rows.append({"case": label, "department": args["department"], "correct": True})

for label in ["named", "stream", "qwen-required", "qwen-required-v2", "qwen-auto", "promoted-434"]:
    choice = read(label, "response.json")["choices"][0]
    check(
        choice["finish_reason"] == "tool_calls" and len(choice["message"]["tool_calls"]) == 1,
        label + ": native call",
    )
    check(
        json.loads(choice["message"]["tool_calls"][0]["function"]["arguments"])
        == {"department": "other"},
        label + ": correct args",
    )
check(read("stream", "summary.json")["stream_done"], "stream: final DONE")
for label in ["none", "plain", "auto"]:
    msg = read(label, "response.json")["choices"][0]["message"]
    check(not msg.get("tool_calls"), label + ": no native calls")
check(
    read("auto", "response.json")["choices"][0]["message"]["content"].startswith(
        "send_department_email{"
    ),
    "auto: reproduces missing native framing",
)
check(
    read("plain", "response.json")["choices"][0]["message"]["content"] == "READY",
    "plain: clean text",
)
for label in ["invalid", "unknown-name"]:
    check(read(label, "summary.json")["http_status"] == 400, label + ": rejected")

preserved = json.loads((HERE / "preservation.json").read_text())
for path, sha in preserved.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha, path
check(True, f"{len(preserved)} historical files byte-identical")
result = {"passed": True, "checks": checks, "cases": rows, "preserved_files": len(preserved)}
(HERE / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
