"""Collect exactly one reviewed Gemma result per frozen family; retain all attempts."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(plan_path, policy_path, runs):
    plan = json.loads(plan_path.read_text())
    policy = json.loads(policy_path.read_text())
    accepted, evidence = {}, []
    for run_number, run in enumerate(runs):
        editorial_path = run / "editorial-audit.json"
        if (
            editorial_path.exists()
            and json.loads(editorial_path.read_text()).get("excluded_entire_run") is True
        ):
            raise ValueError(f"Run excluded by independent editorial review: {run}")
        contract = json.loads((run / "contract.json").read_text())
        code = run / "generator-source.py"
        if (
            contract["plan_sha256"] != sha(plan_path)
            or contract["policy_sha256"] != sha(policy_path)
            or contract["generator_sha256"] != sha(code)
        ):
            raise ValueError("Generation plan/policy/source changed")
        spec = importlib.util.spec_from_file_location(f"saved_generator_{run_number}", code)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        count = 0
        for directory in sorted(run.iterdir()):
            if not directory.is_dir() or not directory.name.isdigit():
                continue
            index = int(directory.name)
            if not 0 <= index < len(plan["families"]):
                raise ValueError("Unexpected family index")
            family = plan["families"][index]
            if not (directory / "result.json").exists():
                # An unresolved request remains visible but cannot become data.
                evidence.append({"path": str(directory), "state": "unresolved"})
                continue
            result = module.audit_family(directory, family, index, policy)
            review_path = directory / "review.json"
            if not review_path.exists():
                raise ValueError(f"Unreviewed generation: {directory}")
            review = json.loads(review_path.read_text())
            if (
                review["result_sha256"] != sha(directory / "result.json")
                or len(review.get("note", "")) < 30
            ):
                raise ValueError("Review hash/note differs")
            item = {
                "path": str(directory),
                "state": review["decision"],
                "result_sha256": sha(directory / "result.json"),
                "review_sha256": sha(review_path),
            }
            evidence.append(item)
            if review["decision"] != "accept":
                continue
            if result.get("parse_error") or family["family"] in accepted:
                raise ValueError("Malformed or multiply accepted family")
            accepted[family["family"]] = {
                "family": family["family"],
                "messages": [row["message"] for row in result["messages"]],
                "evidence": item,
            }
            count += 1
        evidence.append(
            {"run": str(run), "contract_sha256": sha(run / "contract.json"), "accepted": count}
        )
    if len(accepted) != 600 or set(accepted) != {row["family"] for row in plan["families"]}:
        raise ValueError(f"Incomplete reviewed collection: {len(accepted)}/600")
    return [accepted[row["family"]] for row in plan["families"]], evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, evidence = collect(args.plan, args.policy, args.run)
    audit = args.output.with_name("collection-audit.json")
    if args.output.exists() or audit.exists():
        raise ValueError("Preserve existing collection")
    with args.output.open("x") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "complete": True,
        "families": len(rows),
        "plan_sha256": sha(args.plan),
        "policy_sha256": sha(args.policy),
        "accepted_sha256": sha(args.output),
        "collector_sha256": sha(Path(__file__)),
        "evidence": evidence,
        "ready_for_training": False,
        "limitation": "Collection proves raw-response provenance only. Lexical and semantic review remain mandatory.",
    }
    with audit.open("x") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"families": len(rows), "ready_for_training": False}))


if __name__ == "__main__":
    main()
