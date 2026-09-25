"""Observed serial benchmark. No retry; operator gates before further inference."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CORPUS = ROOT / "verification/benchmark/cases-500.json"
SHA = "bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e"
REFERENCE = json.loads((HERE.parent / "qwen4b-instruct/case-025-wire-request.json").read_text())
RECIPIENTS = {
    "human_resources": "human-resources@example.com",
    "payroll": "kadry@example.com",
    "help_desk": "help-desk@example.com",
    "it": "it@example.com",
    "other": "other@example.com",
}


def fetch(path, raw=False):
    with urlopen("http://127.0.0.1:8025" + path, timeout=15) as response:
        body = response.read()
    return body if raw else json.loads(body)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def append(path, value):
    with path.open("a") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()


def audit(case, row, events, raw_mail):
    """Inspect saved wire, SDK and MIME evidence independently of route correctness."""
    request = [e for e in events if e["event"] == "request"]
    response = [e for e in events if e["event"] == "response"]
    assert len(request) == len(response) == 1, "missing/repeated inference"
    body = json.loads(request[0]["body"])
    expected = json.loads(json.dumps(REFERENCE))
    expected["messages"][-1] = {"role": "user", "content": case["message"]}
    assert body == expected, "wire settings drift or answer-key leakage"
    wire = json.loads(response[0]["body"])
    assert response[0]["status"] == 200, f"upstream HTTP {response[0]['status']}"
    choice = wire["choices"][0]
    parsed = [e for e in events if e["event"] == "parsed"]
    assert len(parsed) == 1, "missing/repeated parsed response"
    parsed = parsed[0]
    completed = [e for e in events if e["event"] == "delivery_completed"]
    started = [e for e in events if e["event"] == "delivery_started"]
    if "actual" in row:
        assert parsed["rejection_reason"] is None
        calls = choice["message"].get("tool_calls", [])
        assert len(calls) == 1 and calls[0]["function"]["name"] == "send_department_email"
        args = json.loads(calls[0]["function"]["arguments"])
        assert set(args) == {"department"} and RECIPIENTS[args["department"]] == row["actual"]
        sdk = parsed["response"]["tool_calls"]
        assert len(sdk) == 1 and sdk[0]["name"] == "send_department_email"
        assert sdk[0]["args"] == args
        assert len(started) == len(completed) == 1
        assert completed[0]["recipient"] == row["actual"]
        assert raw_mail is not None, "missing mail"
        message = BytesParser(policy=policy.default).parsebytes(raw_mail)
        assert getaddresses(message.get_all("To", [])) == [("", row["actual"])]
        assert getaddresses(message.get_all("Reply-To", [])) == [
            ("", f"acceptance-{row['run_id']}-0@example.com")
        ]
        assert str(message["X-Request-ID"]) == row["request_id"]
        assert str(message["Message-ID"]) == completed[0]["message_id"]
        assert message.get_content().replace("\r\n", "\n").removesuffix("\n") == case["message"]
    else:
        assert not completed and not started and raw_mail is None, "delivery after rejection"
        assert row.get("http_status") == 502 and parsed["rejection_reason"], "unknown failure"
    return {
        "raw_message": choice["message"],
        "finish_reason": choice["finish_reason"],
        "usage": wire.get("usage"),
        "rejection_reason": parsed["rejection_reason"],
        "trace_mail_audit_passed": True,
        "mail_count": int(raw_mail is not None),
    }


def main():
    assert hashlib.sha256(CORPUS.read_bytes()).hexdigest() == SHA
    cases = json.loads(CORPUS.read_text())
    assert len(cases) == 500
    assert not (HERE / "results.jsonl").exists(), "Existing run: inspect, never blindly replay"
    assert fetch("/api/v1/messages?limit=1")["total"] + 500 < 10000, "Mailpit retention"
    save(HERE / "started.json", {"utc": datetime.now(timezone.utc).isoformat(), "corpus": SHA})
    rows = []
    for index, case in enumerate(cases, 1):
        stem = f"case-{index:03d}"
        case_path = HERE / f"{stem}.json"
        save(case_path, [case])
        since = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result = subprocess.run(
            [sys.executable, str(ROOT / "verification/e2e.py"), "--cases", str(case_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        (HERE / f"{stem}-result.jsonl").write_text(result.stdout)
        if result.stderr:
            (HERE / f"{stem}-stderr.txt").write_text(result.stderr)
        row = json.loads(result.stdout.splitlines()[0])
        logs = subprocess.check_output(
            ["docker", "compose", "logs", "--no-color", "--since", since, "api"],
            cwd=ROOT,
            text=True,
        )
        (HERE / f"{stem}-api.txt").write_text(logs)
        events = [
            json.loads(line.split("model_trace ", 1)[1])
            for line in logs.splitlines()
            if "model_trace " in line
        ]
        events = [e for e in events if e["request_id"] == row["request_id"]]
        save(HERE / f"{stem}-trace.json", events)
        matches = [
            item
            for item in fetch("/api/v1/messages?limit=100")["messages"]
            if row["request_id"] in item["Subject"]
        ]
        assert len(matches) <= 1, "duplicate captured mail"
        raw = fetch(f"/api/v1/message/{matches[0]['ID']}/raw", True) if matches else None
        if raw is not None:
            (HERE / f"{stem}.eml").write_bytes(raw)
        inspection = audit(case, row, events, raw)
        row.update(inspection)
        row.update(case=index, selection_sha256=row["dataset_sha256"], dataset_sha256=SHA)
        rows.append(row)
        append(HERE / "results.jsonl", row)
        summary = {
            "completed": index,
            "correct": sum(r["passed"] for r in rows),
            "wrong_route": sum("actual" in r and r["actual"] != r["expected"] for r in rows),
            "protocol_error": sum("actual" not in r for r in rows),
        }
        save(HERE / "progress.json", summary)
        print(
            json.dumps(
                {
                    "case": index,
                    "id": row["case_id"],
                    "actual": row.get("actual"),
                    "passed": row["passed"],
                    "audit": True,
                    "seconds": row["seconds"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if not row["passed"]:
            print(
                "FAILURE " + json.dumps({"input": case, "result": row}, ensure_ascii=False),
                flush=True,
            )
        if (not row["passed"] or index % 10 == 0) and index < 500:
            print("PROGRESS " + json.dumps(summary), flush=True)
            action = input("REVIEW: enter continue after inspection, or stop: ").strip()
            append(
                HERE / "reviews.jsonl",
                {
                    "after_case": index,
                    "action": action,
                    "utc": datetime.now(timezone.utc).isoformat(),
                },
            )
            if action != "continue":
                return 130
    print("COMPLETE " + json.dumps(summary), flush=True)
    return 0 if all(r["passed"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
