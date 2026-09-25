"""Read-only MIME check for both saved smoke runs, including misclassified deliveries."""

import hashlib
import json
import sys
from email.utils import getaddresses
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "verification"))
from e2e import captured  # noqa: E402

cases = json.loads((HERE.parent / "tool-wiring/focused-smoke-cases.json").read_text())
checked = []
scores = {}
checksum = hashlib.sha256(
    (HERE.parent / "tool-wiring/focused-smoke-cases.json").read_bytes()
).hexdigest()
for provider in ("ollama", "laya"):
    rows = [
        json.loads(line) for line in (HERE / f"{provider}-smoke.jsonl").read_text().splitlines()
    ]
    assert rows[-1]["total"] == len(cases) == 5
    assert rows[-1]["dataset_sha256"] == checksum
    scores[provider] = sum(row["passed"] for row in rows[:-1])
    for row, case in zip(rows[:-1], cases, strict=True):
        assert row["case_id"] == case["id"]
        message = captured(row)
        sender = f"acceptance-{row['run_id']}-{row['case'] - 1}@example.com"
        assert getaddresses(message.get_all("To", [])) == [("", row["actual"])]
        assert getaddresses(message.get_all("Reply-To", [])) == [("", sender)]
        assert str(message["X-Request-ID"]) == row["request_id"]
        assert str(message["Message-ID"]) == f"<{row['request_id']}@message-router.local>"
        assert message.get_content().replace("\r\n", "\n").removesuffix("\n") == case["message"]
        checked.append(row["request_id"])
assert len(set(checked)) == len(checked) == 10
print(
    json.dumps(
        {
            "captured_deliveries": len(checked),
            "mime_checks_passed": True,
            "routing_correct": scores,
        },
        indent=2,
    )
)
