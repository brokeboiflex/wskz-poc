"""Final exhaustive read-only audit and statistics. Never calls the model/API POST."""

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("observed_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--partial", action="store_true", help="Audit only an explicitly stopped prefix"
)
args = parser.parse_args()
rows = [json.loads(line) for line in (HERE / "results.jsonl").read_text().splitlines()]
cases = json.loads(runner.CORPUS.read_text())
assert len(cases) == 500
n = len(rows)
assert 0 < n <= 500
if args.partial:
    assert n < 500 and json.loads((HERE / "stop.json").read_text())["completed"] == n
else:
    assert n == 500, "Incomplete run: use --partial only after an explicit stop"
cases = cases[:n]
assert [r["case"] for r in rows] == list(range(1, n + 1))
assert [r["case_id"] for r in rows] == [c["id"] for c in cases]
assert len({r["request_id"] for r in rows}) == n
logs = (HERE / "api.txt").read_text()
all_events = [
    json.loads(line.split("model_trace ", 1)[1])
    for line in logs.splitlines()
    if "model_trace " in line
]
assert {e["request_id"] for e in all_events} == {r["request_id"] for r in rows}, (
    "unaccounted request"
)
for event in ("request", "response", "parsed"):
    assert sum(e["event"] == event for e in all_events) == n, (event, "hidden or missing inference")
assert hashlib.sha256(runner.CORPUS.read_bytes()).hexdigest() == runner.SHA
items, start = [], 0
while True:
    page = runner.fetch(f"/api/v1/messages?limit=100&start={start}")
    items.extend(page["messages"])
    start += len(page["messages"])
    if start >= page["total"]:
        break
    assert page["messages"]

matrix = defaultdict(Counter)
classes = defaultdict(Counter)
variants = defaultdict(Counter)
families = defaultdict(list)
failures = []
mail_count = 0
for row, case in zip(rows, cases, strict=True):
    stem = f"case-{row['case']:03d}"
    trace = json.loads((HERE / f"{stem}-trace.json").read_text())
    assert row["expected"] == case["recipient"]
    assert type(row["passed"]) is bool
    assert all(e["request_id"] == row["request_id"] for e in trace)
    assert trace == [e for e in all_events if e["request_id"] == row["request_id"]]
    selected = HERE / f"{stem}.json"
    assert json.loads(selected.read_text()) == [case]
    assert hashlib.sha256(selected.read_bytes()).hexdigest() == row["selection_sha256"]
    matches = [m for m in items if row["request_id"] in m["Subject"]]
    assert len(matches) == row["mail_count"], (stem, "duplicate/missing captured mail")
    raw = None
    if matches:
        raw = runner.fetch(f"/api/v1/message/{matches[0]['ID']}/raw", True)
        assert raw == (HERE / f"{stem}.eml").read_bytes(), (stem, "live mail differs")
        mail_count += 1
    inspection = runner.audit(case, row, trace, raw)
    assert all(row[key] == value for key, value in inspection.items())
    assert row["passed"] == (row.get("actual") == case["recipient"]), "score inconsistency"
    if raw is not None:
        completed = next(e for e in trace if e["event"] == "delivery_completed")
        started = next(e for e in trace if e["event"] == "delivery_started")
        call = json.loads(inspection["raw_message"]["tool_calls"][0]["function"]["arguments"])
        assert completed["status"] == "submitted"
        assert started["department"] == call["department"]
    actual = row.get("actual", "HTTP/tool error")
    matrix[row["expected"]][actual] += 1
    for counter in (classes[case["department"]], variants[case["variant"]]):
        counter["total"] += 1
        counter["correct"] += row["passed"]
        counter["wrong_route"] += "actual" in row and row["actual"] != row["expected"]
        counter["protocol_error"] += "actual" not in row
    families[case["scenario_id"]].append(row["passed"])
    if not row["passed"]:
        failures.append(
            {
                "case": row["case"],
                "case_id": row["case_id"],
                "message": case["message"],
                "expected": row["expected"],
                "actual": row.get("actual"),
                "raw_message": row["raw_message"],
                "rejection_reason": row["rejection_reason"],
                "request_id": row["request_id"],
            }
        )
assert all(len(v) in (1, 2) for v in families.values())
if not args.partial:
    assert len(families) == 250 and all(len(v) == 2 for v in families.values())
latency = sorted(r["seconds"] for r in rows)
summary = {
    "status": "partial_stopped" if args.partial else "complete",
    "planned": 500,
    "unexecuted": 500 - n,
    "dataset_sha256": runner.SHA,
    "model": runner.REFERENCE["model"],
    "total": len(rows),
    "correct": sum(r["passed"] for r in rows),
    "wrong_route": sum("actual" in r and r["actual"] != r["expected"] for r in rows),
    "protocol_error": sum("actual" not in r for r in rows),
    "mail_count": mail_count,
    "trace_and_live_mime_audits": len(rows),
    "per_department": classes,
    "confusion_matrix": matrix,
    "per_variant": variants,
    "scenario_families": len(families),
    "families_incomplete": sum(len(v) < 2 for v in families.values()),
    "families_both_correct": sum(len(v) == 2 and all(v) for v in families.values()),
    "families_one_correct": sum(sum(v) == 1 for v in families.values()),
    "families_neither_correct": sum(not any(v) for v in families.values()),
    "latency_seconds": {
        "median": median(latency),
        "p95": latency[math.ceil(n * 0.95) - 1],
        "max": max(latency),
        "request_total": sum(latency),
    },
}
assert summary["correct"] + summary["wrong_route"] + summary["protocol_error"] == n
summary["unexecuted_departments"] = sorted(set(runner.RECIPIENTS) - set(classes))
prefix = "partial-" if args.partial else ""
runner.save(HERE / f"{prefix}summary.json", summary)
runner.save(HERE / f"{prefix}failures.json", failures)
print(json.dumps(summary, ensure_ascii=False, indent=2))
