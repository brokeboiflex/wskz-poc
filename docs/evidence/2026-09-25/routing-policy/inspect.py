"""Read existing case results, correlated API traces and Mailpit; sends no requests to LLM."""

import json
import subprocess
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def fetch(path, raw=False):
    with urlopen("http://127.0.0.1:8025" + path, timeout=15) as response:
        body = response.read()
    return body if raw else json.loads(body)


logs = subprocess.check_output(
    ["docker", "compose", "logs", "--no-color", "api"], cwd=ROOT, text=True
)
(HERE / "api.txt").write_text(logs)
events = [
    json.loads(line.split("model_trace ", 1)[1])
    for line in logs.splitlines()
    if "model_trace " in line
]
items, start = [], 0
while True:
    page = fetch(f"/api/v1/messages?limit=100&start={start}")
    items.extend(page["messages"])
    start += len(page["messages"])
    if start >= page["total"]:
        break
    assert page["messages"]

for path in sorted(HERE.glob("case-*-result.jsonl")):
    stem = path.name.removesuffix("-result.jsonl")
    row = json.loads(path.read_text().splitlines()[0])
    case = json.loads((HERE / f"{stem}.json").read_text())[0]
    trace = [event for event in events if event["request_id"] == row["request_id"]]
    (HERE / f"{stem}-trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n")
    requests = [event for event in trace if event["event"] == "request"]
    responses = [event for event in trace if event["event"] == "response"]
    assert len(requests) == len(responses) == 1, (stem, "missing or repeated inference")
    (HERE / f"{stem}-wire-request.json").write_text(requests[0]["body"])
    wire = json.loads(requests[0]["body"])
    assert wire["messages"][-1] == {"role": "user", "content": case["message"]}
    raw_response = json.loads(responses[0]["body"])
    parsed = next(event for event in trace if event["event"] == "parsed")
    matches = [item for item in items if row["request_id"] in item["Subject"]]
    if "actual" in row:
        assert len(matches) == 1, (stem, "missing or duplicated mail")
        raw = fetch(f"/api/v1/message/{matches[0]['ID']}/raw", raw=True)
        (HERE / f"{stem}.eml").write_bytes(raw)
        message = BytesParser(policy=policy.default).parsebytes(raw)
        assert getaddresses(message.get_all("To", [])) == [("", row["actual"])]
        assert getaddresses(message.get_all("Reply-To", [])) == [
            ("", f"acceptance-{row['run_id']}-0@example.com")
        ]
        assert str(message["X-Request-ID"]) == row["request_id"]
        assert message.get_content().replace("\r\n", "\n").removesuffix("\n") == case["message"]
    else:
        assert not matches, (stem, "mail after rejected response")
    print(
        json.dumps(
            {
                "case": stem,
                "request_id": row["request_id"],
                "expected": row["expected"],
                "actual": row.get("actual"),
                "raw_message": raw_response["choices"][0]["message"],
                "usage": raw_response.get("usage"),
                "rejection_reason": parsed["rejection_reason"],
                "mail_count": len(matches),
                "mail_checks_passed": True,
            },
            ensure_ascii=False,
        )
    )
