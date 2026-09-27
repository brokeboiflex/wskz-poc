"""Parse authored messages verbatim; never generate, label, or paraphrase text."""

import argparse
import hashlib
import json
from pathlib import Path

from data_guard import frozen_exclusions, validate

ROOT = Path(__file__).parent
PLAN_SHA = "561b082828ec7b8219d29d9adc2bdeac6cac59ad49e3f256d401800391510b99"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(root=ROOT, *, require_complete=True):
    plan_path = root / "source/scenarios.json"
    if sha(plan_path) != PLAN_SHA:
        raise ValueError("Frozen scenario plan changed")
    plan = json.loads(plan_path.read_text())["families"]
    expected = {r["family"]: r for r in plan}
    accepted, evidence, unreviewed = {}, [], []
    for path in sorted((root / "source/authored").glob("*.txt")):
        blocks = path.read_text().strip().split("\n\n")
        batch = []
        for block in blocks:
            lines = block.splitlines()
            if len(lines) != 6 or any(not line.strip() or line != line.strip() for line in lines):
                raise ValueError(f"Expected ID and five verbatim single-line messages: {path}")
            family, *messages = lines
            if family not in expected or family in accepted:
                raise ValueError(f"Unknown or duplicate family: {family}")
            accepted[family] = {"family": family, "messages": messages}
            batch.append(family)
        review_path = root / "source/authored-reviews" / f"{path.stem}.json"
        reviewed = False
        if review_path.exists():
            review = json.loads(review_path.read_text())
            counts = review.get("counts", {})
            reviewed = (
                review.get("approved_for_initial_quality") is True
                and review.get("source_sha256") == sha(path)
                and review.get("plan_sha256") == PLAN_SHA
                and review.get("inputs", {}).get("policy", {}).get("sha256")
                == sha(root / "policy.json")
                and counts.get("families_reviewed") == len(batch)
                and counts.get("messages_reviewed") == len(batch) * 5
                and counts.get("blocking_findings") == 0
                and {r["family"] for r in review.get("families", [])} == set(batch)
                and all(r.get("verdict") == "pass" for r in review.get("families", []))
            )
        item = {"source": str(path.relative_to(root)), "sha256": sha(path), "families": batch}
        if reviewed:
            item["review"] = str(review_path.relative_to(root))
            item["review_sha256"] = sha(review_path)
        else:
            unreviewed.append(path.name)
        evidence.append(item)
    missing = set(expected) - set(accepted)
    if require_complete and (missing or unreviewed):
        raise ValueError(
            f"Incomplete reviewed corpus: missing={len(missing)}, unreviewed={unreviewed}"
        )
    rows = [accepted[r["family"]] for r in plan if r["family"] in accepted]
    flattened = [
        {
            **{
                k: expected[row["family"]][k]
                for k in ("family", "label", "split", "semantic_group")
            },
            "id": f"new-{row['family']}-{i}",
            "variant": i,
            "message": message,
        }
        for row in rows
        for i, message in enumerate(row["messages"])
    ]
    return rows, flattened, evidence, unreviewed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--status", action="store_true", help="Inspect partial corpus; writes no dataset"
    )
    parser.add_argument(
        "--audit-output", type=Path, help="Exclusive lexical report, no excluded text"
    )
    args = parser.parse_args()
    rows, flattened, evidence, unreviewed = collect(require_complete=not args.status)
    if args.status and not args.audit_output:
        print(
            json.dumps(
                {"families": len(rows), "messages": len(flattened), "unreviewed": unreviewed}
            )
        )
        return
    project = ROOT.parents[1]
    forbidden = frozen_exclusions(
        project / "verification/benchmark/cases-500.json", project / "verification/cases.json"
    )
    report = validate(flattened, forbidden, complete=not args.status)
    report.update({"plan_sha256": PLAN_SHA, "evidence": evidence, "ready_for_training": False})
    if args.audit_output:
        with args.audit_output.open("x") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    if not report["passed"]:
        raise ValueError(f"Lexical audit failed: {len(report['errors'])} findings; see report")
    if args.status:
        print(json.dumps({"families": len(rows), "lexical_passed": True, "complete": False}))
        return
    output = ROOT / "source/accepted-authored.jsonl"
    audit = ROOT / "source/collection-audit.json"
    if output.exists() or audit.exists():
        raise ValueError("Preserve existing collection")
    with output.open("x") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report.update(
        {
            "complete": True,
            "families": len(rows),
            "accepted_sha256": sha(output),
            "policy_sha256": sha(ROOT / "policy.json"),
            "collector_sha256": sha(Path(__file__)),
            "final_semantic_exclusion_review_required": True,
        }
    )
    with audit.open("x") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(
        json.dumps({"families": len(rows), "messages": len(flattened), "ready_for_training": False})
    )


if __name__ == "__main__":
    main()
