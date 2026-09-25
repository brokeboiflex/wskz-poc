"""Summarize completed evidence without calling services or changing the corpus."""

import collections
import hashlib
import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
rows = [json.loads(line) for line in (HERE / "ollama-500.jsonl").read_text().splitlines()]
summary = rows.pop()
assert summary.get("total") == len(rows) == 500, "requires completed run"
assert sorted(row["case"] for row in rows) == list(range(1, 501))
assert {row["run_id"] for row in rows} == {summary["run_id"]}
checksum = hashlib.sha256((ROOT / "verification/benchmark/cases-500.json").read_bytes()).hexdigest()
assert {row["dataset_sha256"] for row in rows} == {checksum}
assert summary["dataset_sha256"] == checksum
assert summary["passed"] == sum(row["passed"] for row in rows)
ids = {row.get("request_id") for row in rows}
rejections = []
for line in (HERE / "api.txt").read_text().splitlines():
    match = re.search(r"tool_call_rejected request_id=(\S+) attempt=(\d+) reason=(\S+)", line)
    if match and match[1] in ids:
        rejections.append(match.groups())
by_department = {}
for department in sorted({row["expected"] for row in rows}):
    group = [row for row in rows if row["expected"] == department]
    by_department[department] = {
        "cases": len(group),
        "api_deliveries": sum("actual" in row for row in group),
        "correct_department": sum(row.get("actual") == row["expected"] for row in group),
        "e2e_passed": sum(row["passed"] for row in group),
    }
print(
    json.dumps(
        {
            **summary,
            "api_deliveries": sum("actual" in row for row in rows),
            "correct_department": sum(row.get("actual") == row["expected"] for row in rows),
            "http_errors": dict(collections.Counter(row["code"] for row in rows if "code" in row)),
            "requests_with_rejected_model_attempts": len({entry[0] for entry in rejections}),
            "rejected_model_attempts": dict(collections.Counter(entry[2] for entry in rejections)),
            "total_case_seconds": round(sum(row["seconds"] for row in rows), 3),
            "median_case_seconds": statistics.median(row["seconds"] for row in rows),
            "by_department": by_department,
        },
        ensure_ascii=False,
        indent=2,
    )
)
