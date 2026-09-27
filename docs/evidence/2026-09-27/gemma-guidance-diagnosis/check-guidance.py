"""Frozen observed comparison; no delivery, repair or automatic retry."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODELS = {"gemma": "gemma4:e2b"}
key = sys.argv[1]
model = MODELS[key]
for filename, expected in json.loads((HERE / "freeze.json").read_text()).items():
    assert hashlib.sha256((HERE / filename).read_bytes()).hexdigest() == expected
cases = json.loads((HERE / "cases.json").read_text())
corpus = json.loads((ROOT / "verification/benchmark/cases-500.json").read_text())
numbers = {c["id"]: i for i, c in enumerate(corpus, 1)}
assert len(cases) == 23 and len({c["id"] for c in cases}) == 23
base = json.loads((HERE / "request-template.json").read_text())
probe = (HERE.parents[1] / "2026-09-26/simple-schema/probe.py").read_text()
out = HERE / key
out.mkdir(exist_ok=True)
records = (
    [json.loads(x) for x in (out / "outcomes.jsonl").read_text().splitlines()]
    if (out / "outcomes.jsonl").exists()
    else []
)
assert [x["case_id"] for x in records] == [c["id"] for c in cases[: len(records)]]


def review(n):
    action = input("REVIEW continue/stop: ").strip()
    with (out / "reviews.jsonl").open("a") as f:
        f.write(json.dumps({"after": n, "action": action, "time": time.time()}) + "\n")
    if action != "continue":
        sys.exit(0)


if records and (records[-1]["category"] != "correct" or len(records) % 10 == 0):
    reviews = (
        [json.loads(x) for x in (out / "reviews.jsonl").read_text().splitlines()]
        if (out / "reviews.jsonl").exists()
        else []
    )
    if not any(r["after"] == len(records) and r["action"] == "continue" for r in reviews):
        print("REVIEW RESUMED LAST OUTCOME", json.dumps(records[-1]), flush=True)
        review(len(records))
for index, case in enumerate(cases[len(records) :], len(records) + 1):
    request = dict(
        base,
        model=model,
        messages=base["messages"] + [{"role": "user", "content": case["message"]}],
    )
    with (out / f"{index:03d}-started.json").open("x") as f:
        json.dump({"case_id": case["id"], "model": model, "time": time.time()}, f)
    started = time.monotonic()
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "api", "python", "-c", probe],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    (out / f"{index:03d}-request.json").write_text(
        json.dumps(request, ensure_ascii=False, indent=2)
    )
    (out / f"{index:03d}-raw.txt").write_text(r.stdout)
    category, actual, reason = "protocol_error", None, None
    try:
        assert r.returncode == 0, "transport process failed"
        raw = json.loads(r.stdout)
        assert raw["status"] == 200, f"HTTP {raw['status']}"
        body = json.loads(raw["body"])
        assert len(body["choices"]) == 1, "unexpected choices"
        choice = body["choices"][0]
        assert choice["finish_reason"] == "tool_calls", "missing or incomplete native call"
        calls = choice["message"].get("tool_calls", [])
        assert len(calls) == 1 and calls[0]["function"]["name"] == "send_department_email", (
            "invalid function call"
        )
        args = json.loads(calls[0]["function"]["arguments"])
        assert (
            set(args) == {"department"}
            and args["department"]
            in base["tools"][0]["function"]["parameters"]["properties"]["department"]["enum"]
        ), "invalid arguments"
        actual = args["department"]
        category = "correct" if actual == case["department"] else "wrong_route"
        if category == "wrong_route":
            reason = f"expected {case['department']}, received {actual}"
    except Exception as exc:
        reason = str(exc)
    outcome = {
        "index": index,
        "original_case": numbers[case["id"]],
        "case_id": case["id"],
        "expected": case["department"],
        "actual": actual,
        "category": category,
        "reason": reason,
        "seconds": round(time.monotonic() - started, 3),
    }
    if category != "correct":
        failure = dict(outcome, request=request, raw_response=r.stdout, stderr=r.stderr)
        with (out / "failures.jsonl").open("a") as f:
            f.write(json.dumps(failure, ensure_ascii=False) + "\n")
        print("FAILURE " + json.dumps(failure, ensure_ascii=False), flush=True)
    with (out / "outcomes.jsonl").open("a") as f:
        f.write(json.dumps(outcome) + "\n")
    records.append(outcome)
    counts = {
        c: sum(r["category"] == c for r in records)
        for c in ["correct", "wrong_route", "protocol_error"]
    }
    (out / "summary.json").write_text(
        json.dumps(dict(model=model, completed=index, planned=len(cases), **counts), indent=2)
        + "\n"
    )
    if category != "correct" or index % 10 == 0 or index == len(cases):
        print("PROGRESS " + json.dumps(dict(model=key, completed=index, **counts)), flush=True)
        review(index)
print("COMPLETE " + key, flush=True)
