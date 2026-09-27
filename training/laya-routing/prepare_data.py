"""Split scenario identities before authoring; compile five authored variants per family."""

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
LABELS = ("human_resources", "payroll", "help_desk", "it", "other")


def expected_plan():
    rng = random.Random(42)
    plan = []
    for label in LABELS:
        slots = list(range(120))
        rng.shuffle(slots)
        allocation = {
            n: ("train" if i < 80 else "validation" if i < 100 else "test")
            for i, n in enumerate(slots)
        }
        plan.extend(
            {"family": f"{label}-{n:03d}", "label": label, "split": allocation[n]}
            for n in range(120)
        )
    return {"seed": 42, "variants_per_family": 5, "families": plan}


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        handle.write(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "build"))
    args = parser.parse_args()
    path = ROOT / "source/plan.json"
    if args.command == "plan":
        write_new(path, json.dumps(expected_plan(), ensure_ascii=False, indent=2) + "\n")
        print("600 family identities assigned; no messages created")
        return
    plan = json.loads(path.read_text())
    if plan != expected_plan():
        raise ValueError("Frozen family allocation differs")
    scenario_path = ROOT / "source/scenarios.json"
    scenario_plan = json.loads(scenario_path.read_text())
    review = json.loads((ROOT / "source/scenarios-review.json").read_text())
    scenario_sha = hashlib.sha256(scenario_path.read_bytes()).hexdigest()
    if review.get("approved_for_generation") is not True or review["plan_sha256"] != scenario_sha:
        raise ValueError("Frozen semantic plan review differs")
    by_family = {
        r["family"]: {k: r[k] for k in ("family", "label", "split", "semantic_group")}
        for r in scenario_plan["families"]
    }
    if [
        {k: r[k] for k in ("family", "label", "split")}
        for r in sorted(by_family.values(), key=lambda r: (LABELS.index(r["label"]), r["family"]))
    ] != plan["families"]:
        raise ValueError("Semantic plan changes original split allocation")
    seen, rows, sources = (
        set(),
        [],
        {
            "source/plan.json": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source/scenarios.json": scenario_sha,
        },
    )
    accepted = ROOT / "source/accepted-authored.jsonl"
    collection_path = ROOT / "source/collection-audit.json"
    collection = json.loads(collection_path.read_text())
    from collect_authored import collect

    current_rows, _, current_evidence, _ = collect(ROOT)
    if (
        collection.get("complete") is not True
        or collection.get("passed") is not True
        or collection.get("complete_corpus_required") is not True
        or collection["accepted_sha256"] != hashlib.sha256(accepted.read_bytes()).hexdigest()
        or collection["plan_sha256"] != scenario_sha
        or collection.get("policy_sha256")
        != hashlib.sha256((ROOT / "policy.json").read_bytes()).hexdigest()
        or collection.get("collector_sha256")
        != hashlib.sha256((ROOT / "collect_authored.py").read_bytes()).hexdigest()
        or collection.get("evidence") != current_evidence
        or [json.loads(line) for line in accepted.read_text().splitlines()] != current_rows
    ):
        raise ValueError("Complete audited authored collection is required")
    sources["source/collection-audit.json"] = hashlib.sha256(
        collection_path.read_bytes()
    ).hexdigest()
    for path in (accepted,):
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        for line in path.read_text().splitlines():
            source = json.loads(line)
            family = source["family"]
            if family in seen or family not in by_family:
                raise ValueError(f"Unexpected or duplicate family {family}")
            seen.add(family)
            messages = source["messages"]
            if len(messages) != 5 or any(not isinstance(s, str) or not s.strip() for s in messages):
                raise ValueError(f"Five authored messages required: {family}")
            for index, message in enumerate(messages):
                rows.append(
                    {
                        **by_family[family],
                        "id": f"new-{family}-{index}",
                        "variant": index,
                        "message": message,
                    }
                )
    if seen != set(by_family):
        raise ValueError(f"Missing families: {len(set(by_family) - seen)}")
    assert len(rows) == 3000
    if (ROOT / "data").exists():
        raise ValueError("Data already exists; do not silently regenerate a frozen corpus")
    # Validate everything before writing the first split.
    from data_guard import validate

    report = validate(rows, [], complete=True)
    if not report["passed"]:
        raise ValueError(json.dumps(report["errors"], ensure_ascii=False))
    manifest = {"seed": 42, "sources": sources, "splits": {}}
    for split in ("train", "validation", "test"):
        selected = [r for r in rows if r["split"] == split]
        selected.sort(key=lambda r: r["id"])
        output = ROOT / "data" / f"{split}.jsonl"
        content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in selected)
        write_new(output, content)
        manifest["splits"][split] = {
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "records": len(selected),
            "families": len({r["family"] for r in selected}),
            "semantic_groups": len({r["semantic_group"] for r in selected}),
            "labels": dict(Counter(r["label"] for r in selected)),
        }
    write_new(ROOT / "data/manifest.json", json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["splits"]))


if __name__ == "__main__":
    main()
