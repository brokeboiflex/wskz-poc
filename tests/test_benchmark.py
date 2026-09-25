"""Corpus integrity and E2E answer-key isolation; no model-accuracy assertions."""

import hashlib
import importlib.util
import json
from email.message import EmailMessage
from pathlib import Path

import pytest
from router_app.adapters.agent import DEPARTMENT_RECIPIENTS

ROOT = Path(__file__).resolve().parents[1]


def module_from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = module_from_file("benchmark_builder", ROOT / "verification/benchmark/build.py")
e2e = module_from_file("benchmark_e2e", ROOT / "verification/e2e.py")


def test_frozen_corpus_matches_authored_sources_and_current_policy():
    cases = builder.build_cases()
    builder.validate(cases)
    path = ROOT / "verification/benchmark/cases-500.json"
    assert path.read_text() == builder.serialize(cases)
    for case in cases:
        assert DEPARTMENT_RECIPIENTS[case["department"]].value == case["recipient"]
    manifest = json.loads((path.parent / "manifest.json").read_text())
    assert manifest == builder.report(cases, path.read_text())
    assert manifest["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_pairs_have_same_label_and_retain_original_message():
    cases, _ = e2e.load_cases(ROOT / "verification/benchmark/cases-500.json")
    for base, contextual in zip(cases[::2], cases[1::2], strict=True):
        assert base["scenario_id"] == contextual["scenario_id"]
        assert base["recipient"] == contextual["recipient"]
        assert base["variant"] == "base"
        assert contextual["variant"] in builder.STYLES
        assert base["message"] in contextual["message"]
        assert len(base["message"]) < len(contextual["message"]) <= 4000


def test_submission_does_not_expose_answer_key():
    cases, _ = e2e.load_cases(ROOT / "verification/benchmark/cases-500.json")
    for case in cases:
        assert e2e.submission(case, "synthetic@example.com") == {
            "email": "synthetic@example.com",
            "message": case["message"],
        }


@pytest.mark.parametrize(
    "invalid",
    [
        [],
        {},
        ["not an object"],
        [{"message": "", "recipient": "it@example.com"}],
        [{"message": "x" * 4001, "recipient": "it@example.com"}],
        [{"message": "Hello", "recipient": "arbitrary@example.com"}],
    ],
)
def test_invalid_dataset_is_rejected_before_http(tmp_path, monkeypatch, invalid):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(invalid))
    monkeypatch.setattr(e2e, "fetch", lambda *a, **kw: pytest.fail("HTTP before validation"))
    with pytest.raises(ValueError):
        e2e.main(["--cases", str(path)])


def test_duplicate_ids_rejected_even_if_later_in_corpus(tmp_path, monkeypatch):
    good = {"id": "same", "message": "Test", "recipient": "it@example.com"}
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps([good, good]))
    monkeypatch.setattr(e2e, "fetch", lambda *a, **kw: pytest.fail("HTTP before validation"))
    with pytest.raises(ValueError, match="duplicate ID"):
        e2e.main(["--cases", str(path)])


def test_original_smoke_corpus_still_loads():
    cases, checksum = e2e.load_cases(ROOT / "verification/cases.json")
    assert len(cases) == 15
    assert len(checksum) == 64


def test_selected_dataset_flows_through_runner_and_records_provenance(
    tmp_path, monkeypatch, capsys
):
    case = builder.build_cases()[0]
    path = tmp_path / "selected.json"
    path.write_text(json.dumps([case]))
    sent = []

    def fetch(url, body=None, raw=False):
        if url.endswith("/health/ready"):
            return {"status": "ready"}
        if url.endswith("/api/v1/docs"):
            return b"swagger"
        if url.endswith("/api/v1/openapi.json"):
            return {"paths": {"/api/v1/messages": {}}}
        assert url.endswith("/api/v1/messages")
        sent.append(body)
        return {
            "status": "submitted",
            "recipient": case["recipient"],
            "request_id": "test-request",
            "message_id": "<test@example.com>",
        }

    def captured(receipt):
        message = EmailMessage()
        message["To"] = case["recipient"]
        message["Reply-To"] = sent[0]["email"]
        message["Message-ID"] = receipt["message_id"]
        message["X-Request-ID"] = receipt["request_id"]
        message.set_content(case["message"])
        return message

    monkeypatch.setattr(e2e, "fetch", fetch)
    monkeypatch.setattr(e2e, "captured", captured)
    assert e2e.main(["--cases", str(path)]) == 0
    assert set(sent[0]) == {"email", "message"}
    assert sent[0]["message"] == case["message"]
    result, summary = map(json.loads, capsys.readouterr().out.splitlines())
    assert result["case_id"] == case["id"]
    assert result["scenario_id"] == case["scenario_id"]
    assert result["dataset_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert summary["dataset_sha256"] == result["dataset_sha256"]
    assert summary["passed"] == summary["total"] == 1
