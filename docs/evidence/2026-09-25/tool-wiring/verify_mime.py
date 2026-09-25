"""Read-only MIME audit of the completed run, including misclassified deliveries."""

import hashlib
import json
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = "http://127.0.0.1:8025"


def fetch(path, raw=False):
    with urlopen(BASE + path, timeout=15) as response:
        value = response.read()
    return value if raw else json.loads(value)


def main():
    lines = [json.loads(line) for line in (HERE / "ollama-500.jsonl").read_text().splitlines()]
    assert lines[-1].get("total") == 500, "requires a completed 500-case run"
    results = lines[:-1]
    corpus = (ROOT / "verification/benchmark/cases-500.json").read_bytes()
    cases = json.loads(corpus)
    assert len(results) == 500
    assert sorted(row["case"] for row in results) == list(range(1, 501))
    assert {row["run_id"] for row in lines} == {lines[-1]["run_id"]}
    assert {row["dataset_sha256"] for row in lines} == {hashlib.sha256(corpus).hexdigest()}
    assert len({row["request_id"] for row in results if "actual" in row}) == sum(
        "actual" in row for row in results
    )
    items = []
    start = 0
    while True:
        page = fetch(f"/api/v1/messages?start={start}&limit=100")
        items.extend(page["messages"])
        start += len(page["messages"])
        if start >= page["total"]:
            break
        assert page["messages"], "pagination stalled"
    checked = 0
    for row in results:
        if "actual" not in row:
            continue
        request_id = row["request_id"]
        matches = [item for item in items if request_id in item["Subject"]]
        assert len(matches) == 1, (request_id, "missing or duplicate message")
        raw = fetch(f"/api/v1/message/{matches[0]['ID']}/raw", raw=True)
        message = BytesParser(policy=policy.default).parsebytes(raw)
        index = row["case"] - 1
        sender = f"acceptance-{row['run_id']}-{index}@example.com"
        assert getaddresses(message.get_all("To", [])) == [("", row["actual"])], request_id
        assert getaddresses(message.get_all("Reply-To", [])) == [("", sender)], request_id
        assert str(message["X-Request-ID"]) == request_id, request_id
        assert str(message["Message-ID"]) == f"<{request_id}@message-router.local>", request_id
        assert (
            message.get_content().replace("\r\n", "\n").removesuffix("\n")
            == cases[index]["message"]
        ), request_id
        checked += 1
    print(
        json.dumps(
            {
                "run_id": lines[-1]["run_id"],
                "checked_deliveries": checked,
                "reply_to_original_body_correlation_and_no_duplicates": "pass",
                "mailpit_total": len(items),
            }
        )
    )


if __name__ == "__main__":
    main()
