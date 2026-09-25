"""Acceptance evidence from real HTTP, inference, SMTP and captured RFC822 mail.

No fakes, deletion, provider keys or arbitrary-recipient sends. Nonzero exit if
any case fails. Each execution intentionally creates new synthetic messages.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

API = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
MAILPIT = os.environ.get("MAILPIT_URL", "http://localhost:8025").rstrip("/")
RECIPIENTS = {
    "human-resources@example.com",
    "kadry@example.com",
    "help-desk@example.com",
    "it@example.com",
    "other@example.com",
}


def load_cases(path):
    """Validate the full corpus before any request can initiate delivery."""
    data = path.read_bytes()
    cases = json.loads(data)
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty JSON array")
    ids = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"case {index + 1}: expected object")
        body = case.get("message")
        if not isinstance(body, str) or not body.strip() or len(body) > 4000:
            raise ValueError(f"case {index + 1}: invalid message")
        if not isinstance(case.get("recipient"), str) or case["recipient"] not in RECIPIENTS:
            raise ValueError(f"case {index + 1}: invalid expected recipient")
        case_id = case.get("id", f"smoke-{index + 1:03d}")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise ValueError(f"case {index + 1}: invalid or duplicate ID")
        ids.add(case_id)
    return cases, hashlib.sha256(data).hexdigest()


def submission(case, sender):
    """Never expose the answer key, rationale, ID or department to inference."""
    return {"email": sender, "message": case["message"]}


def fetch(url, body=None, raw=False):
    request = Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=240) as response:
        data = response.read()
    return data if raw else json.loads(data)


def captured(receipt):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        items = fetch(MAILPIT + "/api/v1/messages?limit=100")["messages"]
        matches = [item for item in items if receipt["request_id"] in item["Subject"]]
        if matches:
            assert len(matches) == 1, "duplicate captured email"
            raw = fetch(
                MAILPIT + "/api/v1/message/" + quote(matches[0]["ID"], safe="") + "/raw", raw=True
            )
            return BytesParser(policy=policy.default).parsebytes(raw)
        time.sleep(0.5)
    raise AssertionError("no captured email")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("cases.json"))
    args = parser.parse_args(argv)
    cases, checksum = load_cases(args.cases)
    run_id = uuid4().hex[:12]
    assert fetch(API + "/health/ready")["status"] == "ready"
    assert b"swagger" in fetch(API + "/api/v1/docs", raw=True).lower()
    assert "/api/v1/messages" in fetch(API + "/api/v1/openapi.json")["paths"]
    results = []
    for index, case in enumerate(cases):
        sender = f"acceptance-{run_id}-{index}@example.com"
        start = time.perf_counter()
        result = {
            "case": index + 1,
            "case_id": case.get("id", f"smoke-{index + 1:03d}"),
            "scenario_id": case.get("scenario_id"),
            "variant": case.get("variant", "smoke"),
            "run_id": run_id,
            "dataset_sha256": checksum,
            "expected": case["recipient"],
        }
        try:
            receipt = fetch(API + "/api/v1/messages", submission(case, sender))
            result["actual"] = receipt["recipient"]
            result["request_id"] = receipt["request_id"]
            assert receipt["status"] == "submitted", "submission not confirmed"
            message = captured(receipt)
            assert getaddresses(message.get_all("To", [])) == [("", case["recipient"])], (
                "wrong MIME recipient"
            )
            assert getaddresses(message.get_all("Reply-To", [])) == [("", sender)], "wrong Reply-To"
            assert str(message["Message-ID"]) == receipt["message_id"], "wrong Message-ID"
            assert str(message["X-Request-ID"]) == receipt["request_id"], "wrong correlation"
            assert (
                message.get_content().replace("\r\n", "\n").removesuffix("\n") == case["message"]
            ), "original text changed"
            assert receipt["recipient"] == case["recipient"], "wrong API recipient"
            result["passed"] = True
        except Exception as exc:
            result["passed"] = False
            result["error"] = str(exc)
        result["seconds"] = round(time.perf_counter() - start, 3)
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    passed = sum(item["passed"] for item in results)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "dataset_sha256": checksum,
                "passed": passed,
                "total": len(results),
            },
            ensure_ascii=False,
        )
    )
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
