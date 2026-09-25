"""Summarize the frozen 500-case run and audit all matching captured MIME (read-only)."""

import hashlib
import json
import re
import statistics
from collections import Counter
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def fetch(path, raw=False):
    with urlopen("http://127.0.0.1:8025" + path, timeout=15) as response:
        data = response.read()
    return data if raw else json.loads(data)


def main():
    lines = [json.loads(line) for line in (HERE / "results.jsonl").read_text().splitlines()]
    assert lines[-1].get("total") == 500, "full run required"
    rows = lines[:-1]
    corpus = (ROOT / "verification/benchmark/cases-500.json").read_bytes()
    cases = json.loads(corpus)
    assert len(rows) == len(cases) == 500
    assert [row["case"] for row in rows] == list(range(1, 501))
    assert {row["run_id"] for row in lines} == {lines[-1]["run_id"]}
    assert {row["dataset_sha256"] for row in lines} == {hashlib.sha256(corpus).hexdigest()}
    assert lines[-1]["passed"] == sum(row["passed"] for row in rows)
    ids = [row["request_id"] for row in rows if "request_id" in row]
    assert len(ids) == len(set(ids))
    items, start = [], 0
    while True:
        page = fetch(f"/api/v1/messages?start={start}&limit=100")
        items.extend(page["messages"])
        start += len(page["messages"])
        if start >= page["total"]:
            break
        assert page["messages"], "pagination stalled"
    captured = 0
    for row, case in zip(rows, cases, strict=True):
        assert row["case_id"] == case["id"]
        assert row["expected"] == case["recipient"]
        request_id = row.get("request_id")
        matches = [item for item in items if request_id and request_id in item["Subject"]]
        if "actual" not in row:
            assert not matches, (row["case"], "email despite unsuccessful API response")
            continue
        assert len(matches) == 1, (request_id, "missing or duplicate email")
        raw = fetch(f"/api/v1/message/{matches[0]['ID']}/raw", raw=True)
        message = BytesParser(policy=policy.default).parsebytes(raw)
        sender = f"acceptance-{row['run_id']}-{row['case'] - 1}@example.com"
        assert getaddresses(message.get_all("To", [])) == [("", row["actual"])]
        assert getaddresses(message.get_all("Reply-To", [])) == [("", sender)]
        assert str(message["X-Request-ID"]) == request_id
        assert str(message["Message-ID"]) == f"<{request_id}@message-router.local>"
        assert message.get_content().replace("\r\n", "\n").removesuffix("\n") == case["message"]
        captured += 1
    rejection_reasons = Counter()
    run_ids = set(ids)
    for line in (HERE / "api.txt").read_text().splitlines():
        match = re.search(r"tool_call_rejected request_id=(\S+) reason=(\S+)", line)
        if match and match[1] in run_ids:
            rejection_reasons[match[2]] += 1
    departments = {}
    for label in sorted({row["expected"] for row in rows}):
        subset = [row for row in rows if row["expected"] == label]
        departments[label] = {
            "total": len(subset),
            "correct": sum(row.get("actual") == label for row in subset),
            "delivered": sum("actual" in row for row in subset),
            "predictions": dict(Counter(row.get("actual", "(HTTP error)") for row in subset)),
        }
    seconds = sorted(row["seconds"] for row in rows)
    print(
        json.dumps(
            {
                "run_id": lines[-1]["run_id"],
                "dataset_sha256": lines[-1]["dataset_sha256"],
                "cases": len(rows),
                "correct_routes": sum(row.get("actual") == row["expected"] for row in rows),
                "e2e_passed": lines[-1]["passed"],
                "delivered_and_mime_verified": captured,
                "wrong_routes": sum(
                    "actual" in row and row["actual"] != row["expected"] for row in rows
                ),
                "http_errors": dict(
                    Counter(
                        row.get("code", row.get("error")) for row in rows if "actual" not in row
                    )
                ),
                "tool_rejection_reasons": dict(rejection_reasons),
                "by_department": departments,
                "total_request_seconds": round(sum(seconds), 3),
                "median_request_seconds": statistics.median(seconds),
                "p95_request_seconds": seconds[474],
                "no_duplicate_deliveries_or_delivery_after_http_error": True,
                "mailpit_total": len(items),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
