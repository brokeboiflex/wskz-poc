"""Deterministic validation-only selection; the old benchmark and new test are never read."""

import argparse
import json
from pathlib import Path

from evaluate import audit_saved, metrics, new_json, sha


def choose(history):
    if not history or [row["epoch"] for row in history] != list(range(1, len(history) + 1)):
        raise ValueError("Contiguous validation epochs required")
    if any(row["metrics"]["count"] != 500 for row in history):
        raise ValueError("Selection requires the entire validation split")
    best = max(
        history,
        key=lambda row: (row["metrics"]["macro_f1"], row["metrics"]["accuracy"], -row["epoch"]),
    )
    current = history[-1]["epoch"]
    return best, current >= 4 or current - best["epoch"] >= 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--epoch", type=int, choices=range(1, 5), required=True)
    args = parser.parse_args()
    acceptance = json.loads(args.approval.read_text())
    if acceptance.get("validation_sha256") != sha(args.validation):
        raise ValueError("Reviewed validation split differs")
    rows = [json.loads(line) for line in args.validation.read_text().splitlines()]
    if len(rows) != 500 or any(row.get("split") != "validation" for row in rows):
        raise ValueError("Only the frozen 500-row validation split is accepted")
    normalized = [
        {
            "id": row["id"],
            "family": row["family"],
            "message": row["message"],
            "expected": row["label"],
            "semantic_group": row["semantic_group"],
        }
        for row in rows
    ]
    policy = json.loads(args.policy.read_text())
    history = []
    for epoch in range(1, args.epoch + 1):
        output = args.run / f"validation-{epoch}"
        report = json.loads((output / "metrics.json").read_text())
        export = args.run / f"export/epoch-{epoch}"
        provenance = json.loads((export / "provenance.json").read_text())
        contract = report["contract"]
        if (
            contract["split"] != "validation"
            or contract["input_sha256"] != sha(args.validation)
            or contract["policy_sha256"] != sha(args.policy)
            or contract["weights_sha256"] != sha(export / "model.safetensors")
            or contract["weights_sha256"] != provenance["weights_sha256"]
            or report.get("review_complete") is not True
        ):
            raise ValueError("Validation provenance mismatch")
        results = audit_saved(output, normalized, policy)
        if len(results) != 500:
            raise ValueError("Incomplete validation evidence")
        actual = metrics(results)
        if any(report[key] != value for key, value in actual.items()):
            raise ValueError("Validation report differs from observed results")
        for index, result in enumerate(results):
            if not result["correct"] or (index + 1) % 10 == 0:
                review = json.loads((output / f"{index:03d}.review.json").read_text())
                if (
                    review["result_sha256"] != sha(output / f"{index:03d}.result.json")
                    or not review["note"]
                ):
                    raise ValueError("Validation inspection incomplete")
        history.append(
            {
                "epoch": epoch,
                "weights_sha256": contract["weights_sha256"],
                "metrics_sha256": sha(output / "metrics.json"),
                "metrics": actual,
            }
        )
    best, stop = choose(history)
    decision = {
        "epoch": args.epoch,
        "weights_sha256": history[-1]["weights_sha256"],
        "validation_sha256": sha(args.validation),
        "policy_sha256": sha(args.policy),
        "selected_epoch": best["epoch"],
        "selected_sha256": best["weights_sha256"],
        "review_complete": True,
        "stop": stop,
        "criterion": "macro_f1, accuracy, earlier epoch; patience=2; max_epochs=4",
        "history": history,
        "selector_sha256": sha(__file__),
    }
    new_json(args.run / f"validation-{args.epoch}/decision.json", decision)
    print(json.dumps(decision, ensure_ascii=False))


if __name__ == "__main__":
    main()
