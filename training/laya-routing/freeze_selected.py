"""Freeze final evaluation from the completed validation-only selection chain."""

import json
from pathlib import Path

from evaluate import audit_saved, metrics, new_json, sha
from select_checkpoint import choose


def main():
    root = Path(__file__).resolve().parent
    run = root / "work/run-20260927"
    decisions = sorted(run.glob("validation-*/decision.json"))
    decision = json.loads(decisions[-1].read_text())
    best, stop = choose(decision["history"])
    if not stop or not decision["stop"] or best["weights_sha256"] != decision["selected_sha256"]:
        raise ValueError("Selection has not reached the frozen stopping condition")
    policy = json.loads((root / "policy.json").read_text())
    acceptance = json.loads((root / "data/acceptance.json").read_text())
    contract = json.loads((run / "contract.json").read_text())
    if (
        sha(root / "data/acceptance.json") != contract["approval_sha256"]
        or sha(root / "policy.json") != decision["policy_sha256"]
        or sha(root / "data/validation.jsonl") != decision["validation_sha256"]
        or sha(root / "select_checkpoint.py") != decision["selector_sha256"]
    ):
        raise ValueError("Frozen training/selection provenance changed")
    normalized = [
        {
            "id": row["id"],
            "family": row["family"],
            "message": row["message"],
            "expected": row["label"],
            "semantic_group": row["semantic_group"],
        }
        for row in map(json.loads, (root / "data/validation.jsonl").read_text().splitlines())
    ]
    for epoch in decision["history"]:
        output = run / f"validation-{epoch['epoch']}"
        results = audit_saved(output, normalized, policy)
        if len(results) != 500 or metrics(results) != epoch["metrics"]:
            raise ValueError("Validation evidence changed")
        if sha(output / "metrics.json") != epoch["metrics_sha256"]:
            raise ValueError("Validation report changed")
        for index, result in enumerate(results):
            if not result["correct"] or (index + 1) % 10 == 0:
                review = json.loads((output / f"{index:03d}.review.json").read_text())
                if not review["note"] or review["result_sha256"] != sha(
                    output / f"{index:03d}.result.json"
                ):
                    raise ValueError("Missing validation review")
    selected = run / f"export/epoch-{best['epoch']}/model.safetensors"
    if sha(selected) != best["weights_sha256"]:
        raise ValueError("Selected weights changed")
    test_hash = sha(root / "data/test.jsonl")
    regression_hash = sha(root.parents[1] / "verification/benchmark/cases-500.json")
    if (
        test_hash != acceptance["test_sha256"]
        or regression_hash != "bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e"
    ):
        raise ValueError("Final test hash changed")
    freeze = {
        "base_sha256": contract["base_assets"]["model.safetensors"],
        "selected_sha256": best["weights_sha256"],
        "selected_epoch": best["epoch"],
        "policy_sha256": decision["policy_sha256"],
        "test_sha256": test_hash,
        "regression_sha256": regression_hash,
        "decision_sha256": sha(decisions[-1]),
        "evaluation_script_sha256": sha(root / "evaluate.py"),
        "freeze_script_sha256": sha(__file__),
    }
    new_json(run / "final-freeze.json", freeze)
    print(json.dumps(freeze))


if __name__ == "__main__":
    main()
