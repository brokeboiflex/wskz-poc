"""Observed one-attempt Chat Completions evaluation. No tool execution or SMTP."""

import argparse
import hashlib
import json
import random
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

LABELS = ("human_resources", "payroll", "help_desk", "it", "other")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_json(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def make_request(message, policy):
    options = list(policy["criteria"])
    return {
        "model": "laya-multilingual",
        "messages": [{"role": "user", "content": message}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "route_message",
                    "description": "Wybierz dział.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "department": {
                                "type": "string",
                                "enum": options,
                                "description": policy["instructions"],
                                "anyOf": [
                                    {"type": "string", "enum": [key], "description": value}
                                    for key, value in policy["criteria"].items()
                                ],
                            }
                        },
                        "required": ["department"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        "tool_choice": "required",
        "stream": False,
    }


def parse_response(body):
    response = json.loads(body)
    choices = response["choices"]
    if len(choices) != 1 or choices[0]["finish_reason"] != "tool_calls":
        raise ValueError("One finished tool call required")
    message = choices[0]["message"]
    if message.get("content") not in (None, ""):
        raise ValueError("Unexpected text alongside decision")
    calls = message["tool_calls"]
    if len(calls) != 1 or calls[0]["type"] != "function":
        raise ValueError("One function call required")
    function = calls[0]["function"]
    arguments = json.loads(function["arguments"])
    if function["name"] != "route_message" or set(arguments) != {"department"}:
        raise ValueError("Invalid decision contract")
    label = arguments["department"]
    if label not in LABELS:
        raise ValueError("Unknown department")
    return label


def clustered_accuracy(results, key, repetitions=2000):
    groups = defaultdict(list)
    for row in results:
        if not row.get(key):
            return None
        groups[row[key]].append(row["correct"])
    # Resample complete clusters, preserving dependency among their variants.
    values = list(groups.values())
    rng = random.Random(42)
    samples = []
    for _ in range(repetitions):
        selected = [rng.choice(values) for _ in values]
        samples.append(sum(sum(v) for v in selected) / sum(len(v) for v in selected))
    samples.sort()
    return {
        "clusters": len(values),
        "all_correct": sum(all(v) for v in values),
        "mean_cluster_accuracy": statistics.mean(sum(v) / len(v) for v in values),
        "accuracy_percentile_95_interval": [
            samples[int(repetitions * 0.025)],
            samples[int(repetitions * 0.975)],
        ],
        "bootstrap_repetitions": repetitions,
        "seed": 42,
        "limitation": "Synthetic clustered bootstrap is descriptive; few broad groups and common author limit generalization.",
    }


def metrics(results):
    counts = Counter((row["expected"], row["predicted"]) for row in results)
    per_class = {}
    for label in LABELS:
        tp = counts[label, label]
        actual = sum(n for (gold, _), n in counts.items() if gold == label)
        predicted = sum(n for (_, guess), n in counts.items() if guess == label)
        per_class[label] = {
            "support": actual,
            "precision": tp / predicted if predicted else 0.0,
            "recall": tp / actual if actual else 0.0,
            "f1": 2 * tp / (actual + predicted) if actual + predicted else 0.0,
        }
    families = defaultdict(list)
    for row in results:
        families[row["family"]].append(row["correct"])
    latencies = sorted(row["seconds"] for row in results)
    return {
        "count": len(results),
        "correct": sum(row["correct"] for row in results),
        "accuracy": sum(row["correct"] for row in results) / len(results),
        "macro_f1": sum(row["f1"] for row in per_class.values()) / len(LABELS),
        "protocol_errors": sum(row["predicted"] is None for row in results),
        "per_class": per_class,
        "confusion": {
            gold: {str(guess): counts[gold, guess] for guess in (*LABELS, None)} for gold in LABELS
        },
        "families": len(families),
        "family_all_correct": sum(all(values) for values in families.values()),
        "family_mean_accuracy": statistics.mean(sum(v) / len(v) for v in families.values()),
        "family_cluster_bootstrap": clustered_accuracy(results, "family"),
        "semantic_group_cluster_bootstrap": clustered_accuracy(results, "semantic_group"),
        "latency_seconds": {
            "median": statistics.median(latencies),
            "p95": latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))],
        },
    }


def audit_saved(output, normalized, policy):
    results = []
    for index, row in enumerate(normalized):
        path = output / f"{index:03d}.result.json"
        if not path.exists():
            break
        result = json.loads(path.read_text())
        request = output / f"{index:03d}.request.json"
        response = output / f"{index:03d}.response.txt"
        attempt = json.loads((output / f"{index:03d}.attempt.json").read_text())
        if (
            any(result.get(key) != value for key, value in row.items())
            or json.loads(request.read_text()) != make_request(row["message"], policy)
            or result["request_sha256"] != sha(request)
            or result["response_sha256"] != sha(response)
            or attempt["request_sha256"] != sha(request)
            or attempt["id"] != row["id"]
        ):
            raise ValueError(f"Evidence chain mismatch at {index}")
        try:
            predicted = (
                parse_response(response.read_text()) if result["http_status"] == 200 else None
            )
        except (ValueError, KeyError, TypeError, IndexError):
            predicted = None
        if result["predicted"] != predicted or result["correct"] != (predicted == row["expected"]):
            raise ValueError(f"Saved prediction differs from raw response at {index}")
        results.append(result)
    if len(list(output.glob("*.result.json"))) != len(results):
        raise ValueError("Noncontiguous result sequence")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "review", "report"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:18091/v1/chat/completions")
    parser.add_argument("--weights-sha256", required=True)
    parser.add_argument("--split", choices=("validation", "test", "regression"), required=True)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--note")
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text())
    if args.input.suffix == ".jsonl":
        rows = [json.loads(line) for line in args.input.read_text().splitlines()]
    else:
        # Old regression schema is normalized only in the evaluation harness.
        rows = json.loads(args.input.read_text())
    if len(rows) != 500:
        raise ValueError("Complete 500-row evaluation required")
    normalized = []
    for row in rows:
        if args.split != "regression" and row.get("split") != args.split:
            raise ValueError("Evaluation split mismatch")
        expected = row.get("label", row.get("department"))
        if expected not in LABELS:
            raise ValueError("Invalid expected department")
        normalized.append(
            {
                "id": row["id"],
                "family": row.get("family", row.get("scenario_id", row["id"])),
                "message": row["message"],
                "expected": expected,
                **({"semantic_group": row["semantic_group"]} if "semantic_group" in row else {}),
            }
        )
    if len({row["id"] for row in normalized}) != 500:
        raise ValueError("Duplicate evaluation ID")
    if args.split in {"test", "regression"}:
        if args.freeze is None:
            raise ValueError("Final model/policy freeze is required before either final test")
        freeze = json.loads(args.freeze.read_text())
        if (
            args.weights_sha256 not in (freeze["base_sha256"], freeze["selected_sha256"])
            or sha(args.policy) != freeze["policy_sha256"]
            or sha(args.input) != freeze[f"{args.split}_sha256"]
        ):
            raise ValueError("Final evaluation differs from frozen artifacts")
    args.output.mkdir(parents=True, exist_ok=True)
    contract = {
        "input_sha256": sha(args.input),
        "policy_sha256": sha(args.policy),
        "weights_sha256": args.weights_sha256,
        "split": args.split,
        "endpoint": args.endpoint,
        "script_sha256": sha(__file__),
    }
    contract_path = args.output / "contract.json"
    if not contract_path.exists():
        new_json(contract_path, contract)
    if json.loads(contract_path.read_text()) != contract:
        raise ValueError("Evaluation contract changed")
    results = audit_saved(args.output, normalized, policy)
    pending = None
    for index, result in enumerate(results):
        if not result["correct"] or (index + 1) % 10 == 0:
            review_path = args.output / f"{index:03d}.review.json"
            if not review_path.exists():
                pending = index
                break
            review = json.loads(review_path.read_text())
            if review["result_sha256"] != sha(
                args.output / f"{index:03d}.result.json"
            ) or not review.get("note"):
                raise ValueError("Review is not bound to the current result")
    if args.command == "review":
        if pending is None or not args.note or len(args.note.strip()) < 20:
            raise ValueError("A pending gate and substantive inspection note are required")
        new_json(
            args.output / f"{pending:03d}.review.json",
            {
                "result_sha256": sha(args.output / f"{pending:03d}.result.json"),
                "note": args.note,
                "time": time.time(),
            },
        )
        print(json.dumps({"reviewed_index": pending}))
        return
    if pending is not None:
        print(
            json.dumps({"review_required": pending, "result": results[pending]}, ensure_ascii=False)
        )
        return
    if args.command == "report":
        if len(results) != 500:
            raise ValueError("Incomplete evaluation")
        report = {**metrics(results), "contract": contract, "review_complete": True}
        new_json(args.output / "metrics.json", report)
        print(json.dumps(report, ensure_ascii=False))
        return
    endpoint = urlsplit(args.endpoint)
    if (
        endpoint.hostname not in ("127.0.0.1", "localhost")
        or endpoint.path != "/v1/chat/completions"
    ):
        raise ValueError("Evaluation is restricted to the isolated local Chat Completions API")
    identity_url = urlunsplit((endpoint.scheme, endpoint.netloc, "/health/checkpoint", "", ""))
    with urllib.request.urlopen(identity_url, timeout=10) as response:
        identity = json.load(response)
    if identity.get("weights_sha256") != args.weights_sha256:
        raise ValueError("Live runtime is serving different weights")
    for index in range(len(results), 500):
        row = normalized[index]
        request_path = args.output / f"{index:03d}.request.json"
        if request_path.exists():
            raise ValueError(f"Unresolved prior request {index}; no automatic retry")
        payload = make_request(row["message"], policy)
        new_json(request_path, payload)
        new_json(
            args.output / f"{index:03d}.attempt.json",
            {"time": time.time(), "id": row["id"], "request_sha256": sha(request_path)},
        )
        start = time.monotonic()
        request = urllib.request.Request(
            args.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                status, body = response.status, response.read().decode()
        except urllib.error.HTTPError as exc:
            status, body = exc.code, exc.read().decode()
        except (OSError, TimeoutError) as exc:
            # Request may have reached the model; never retry it silently.
            new_json(
                args.output / f"{index:03d}.transport-error.json",
                {"type": type(exc).__name__, "message": str(exc)},
            )
            raise
        seconds = time.monotonic() - start
        with (args.output / f"{index:03d}.response.txt").open("x") as handle:
            handle.write(body)
        error, predicted = None, None
        try:
            if status != 200:
                raise ValueError(f"HTTP {status}")
            predicted = parse_response(body)
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            error = str(exc)
        result = {
            **row,
            "predicted": predicted,
            "correct": predicted == row["expected"],
            "seconds": seconds,
            "http_status": status,
            "error": error,
            "request_sha256": sha(request_path),
            "response_sha256": sha(args.output / f"{index:03d}.response.txt"),
        }
        new_json(args.output / f"{index:03d}.result.json", result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if not result["correct"] or (index + 1) % 10 == 0:
            print(json.dumps({"review_required": index}), flush=True)
            return


if __name__ == "__main__":
    main()
