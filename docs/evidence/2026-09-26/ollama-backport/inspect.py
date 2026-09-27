"""Read-only audit of one saved diagnostic; no inference or mail submission."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location(
    "audit", ROOT / "docs/evidence/2026-09-25/qwen4b-500/run.py"
)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
stem = sys.argv[1]
row = json.loads((HERE / f"{stem}-result.jsonl").read_text().splitlines()[0])
case = json.loads((HERE / f"{stem}.json").read_text())[0]
logs = subprocess.check_output(["docker", "compose", "logs", "--no-color", "api"], cwd=ROOT, text=True)
(HERE / "api.txt").write_text(logs)
events = [json.loads(line.split("model_trace ", 1)[1]) for line in logs.splitlines() if "model_trace " in line]
events = [e for e in events if e["request_id"] == row["request_id"]]
audit.save(HERE / f"{stem}-trace.json", events)
items, start = [], 0
while True:
    page = audit.fetch(f"/api/v1/messages?limit=100&start={start}")
    items.extend(page["messages"])
    start += len(page["messages"])
    if start >= page["total"]:
        break
    assert page["messages"]
matches = [m for m in items if row["request_id"] in m["Subject"]]
assert len(matches) <= 1
raw = audit.fetch(f"/api/v1/message/{matches[0]['ID']}/raw", True) if matches else None
if raw is not None:
    (HERE / f"{stem}.eml").write_bytes(raw)
result = audit.audit(case, row, events, raw)
audit.save(HERE / f"{stem}-inspection.json", result)
print(json.dumps(result, ensure_ascii=False, indent=2))
