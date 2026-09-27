"""Offline audit of the completed frozen comparison; never sends requests."""

import hashlib
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = {"qwen": "qwen3:4b-instruct-2507-q4_K_M", "gemma": "gemma4:e2b"}


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def classify(raw, request):
    assert raw["status"] == 200, "Infrastructure failure is not model accuracy"
    body = json.loads(raw["body"])
    try:
        assert len(body["choices"]) == 1
        choice = body["choices"][0]
        assert choice["finish_reason"] == "tool_calls"
        calls = choice["message"].get("tool_calls", [])
        assert len(calls) == 1
        assert calls[0]["function"]["name"] == "send_department_email"
        args = json.loads(calls[0]["function"]["arguments"])
        assert set(args) == {"department"}
        assert (
            args["department"]
            in request["tools"][0]["function"]["parameters"]["properties"]["department"]["enum"]
        )
        return args["department"]
    except (AssertionError, KeyError, TypeError, ValueError):
        return None


def main():
    frozen = json.loads((HERE / "freeze.json").read_text())
    for name, digest in frozen.items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    cases = json.loads((HERE / "cases.json").read_text())
    assert len(cases) == len({c["id"] for c in cases}) == 147
    base = json.loads((HERE / "request-template.json").read_text())
    manifest = json.loads((HERE / "backend-e2b.json").read_text())
    assert manifest["input_hashes"] == frozen
    assert (
        manifest["image_id"]
        == "sha256:006d00b95023fbfc98de1a193160edb1c48a314ebed61dc48c585f9db4157ca2"
    )
    report = [
        "# Failed-case comparison",
        "",
        "Both models tested on the same 147 previously failed cases, with frozen inputs and the same patched Ollama backend. No tools executed or emails sent.",
        "",
        "| Model | Correct | Wrong route | Invalid/missing call | Median seconds | Total seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    audit = {"input_hashes": frozen, "models": {}, "successful_raw_responses_retained": False}
    failure_report = ["# Comparison failures", ""]
    for key, model in MODELS.items():
        out = HERE / key
        outcomes = read_lines(out / "outcomes.jsonl")
        failures = read_lines(out / "failures.jsonl")
        reviews = read_lines(out / "reviews.jsonl")
        summary = json.loads((out / "summary.json").read_text())
        assert len(outcomes) == 147, f"{key}: comparison incomplete"
        assert [r["case_id"] for r in outcomes] == [c["id"] for c in cases]
        failed = {r["index"]: r for r in failures}
        assert len(failed) == len(failures)
        assert set(failed) == {r["index"] for r in outcomes if r["category"] != "correct"}
        counts = {category: 0 for category in ("correct", "wrong_route", "protocol_error")}
        required_reviews = []
        for index, (case, row) in enumerate(zip(cases, outcomes), 1):
            assert row["index"] == index and row["expected"] == case["department"]
            start = json.loads((out / f"{index:03d}-started.json").read_text())
            assert start["case_id"] == case["id"] and start["model"] == model
            counts[row["category"]] += 1
            expected_request = dict(
                base,
                model=model,
                messages=base["messages"] + [{"role": "user", "content": case["message"]}],
            )
            if row["category"] == "correct":
                assert row["actual"] == row["expected"] and row["reason"] is None
            else:
                failure = failed[index]
                assert all(failure[k] == v for k, v in row.items())
                assert failure["request"] == expected_request
                raw = json.loads(failure["raw_response"])
                actual = classify(raw, expected_request)
                category = (
                    "protocol_error"
                    if actual is None
                    else "correct"
                    if actual == case["department"]
                    else "wrong_route"
                )
                assert category == row["category"] and actual == row["actual"]
                failure_report.extend(
                    [
                        f"## {key}: {case['id']}",
                        "",
                        f"Expected: {row['expected']}; actual: {row['actual']}; category: {category}.",
                        "",
                        "Input:",
                        "",
                        case["message"],
                        "",
                        "Raw response:",
                        "",
                        "```json",
                        json.dumps(json.loads(raw["body"]), ensure_ascii=False, indent=2),
                        "```",
                        "",
                    ]
                )
            if row["category"] != "correct" or index % 10 == 0 or index == 147:
                required_reviews.append(index)
                assert any(r["after"] == index and r["action"] == "continue" for r in reviews), (
                    key,
                    index,
                )
        assert summary == dict(model=model, completed=147, planned=147, **counts)
        times = [r["seconds"] for r in outcomes]
        audit["models"][key] = dict(
            model=model,
            **counts,
            failures_audited=len(failures),
            required_reviews=len(required_reviews),
            median_seconds=statistics.median(times),
            total_seconds=round(sum(times), 3),
        )
        report.append(
            f"| {model} | {counts['correct']} | {counts['wrong_route']} | {counts['protocol_error']} | {statistics.median(times):.3f} | {sum(times):.3f} |"
        )
    report.extend(
        [
            "",
            "This is failure-set recovery, not overall accuracy or application/SMTP acceptance. Successful raw responses were intentionally not retained; their outcomes can only be checked against recorded metadata. Timings include HTTP transport and any model-loading overhead, with Qwen run before Gemma.",
            "",
            "See FAILURES_E2B.md for failed inputs and raw responses, backend-e2b.json for the common runtime and model identities, and audit-e2b.json for audit counts.",
            "",
        ]
    )
    (HERE / "audit-e2b.json").write_text(json.dumps(audit, indent=2) + "\n")
    (HERE / "RESULTS_E2B.md").write_text("\n".join(report))
    (HERE / "FAILURES_E2B.md").write_text("\n".join(failure_report))
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
