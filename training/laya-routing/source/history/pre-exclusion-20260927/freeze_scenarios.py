"""Freeze authored semantic families using the original seed42 split allocation."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from prepare_data import expected_plan
from scenario_groups import GROUPS

ROOT = Path(__file__).parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    original = json.loads((ROOT / "source/plan.json").read_text())
    if original != expected_plan():
        raise ValueError("Original seed42 allocation changed")
    slots = defaultdict(list)
    for row in original["families"]:
        slots[row["label"], row["split"]].append(row["family"])
    families, groups, definitions = [], set(), set()
    for label, split, group, scenarios in GROUPS:
        group_id = f"{label}:{group}"
        if group_id in groups:
            raise ValueError("Duplicate semantic group")
        groups.add(group_id)
        lines = [line.strip() for line in scenarios.splitlines() if line.strip()]
        if len(lines) != 10:
            raise ValueError(f"Ten explicit scenarios required: {group_id}")
        for scenario in lines:
            if scenario.casefold() in definitions:
                raise ValueError("Duplicate scenario definition")
            definitions.add(scenario.casefold())
            if not slots[label, split]:
                raise ValueError("Semantic allocation exceeds frozen split count")
            family = slots[label, split].pop(0)
            families.append(
                {
                    "family": family,
                    "label": label,
                    "split": split,
                    "semantic_group": group_id,
                    "scenario": scenario,
                }
            )
    if any(slots.values()) or len(families) != 600 or len(groups) != 60:
        raise ValueError("Incomplete semantic plan")
    return {
        "seed": 42,
        "variants_per_family": 5,
        "policy_sha256": digest(ROOT / "policy.json"),
        "original_allocation_sha256": digest(ROOT / "source/plan.json"),
        "definitions_sha256": digest(ROOT / "scenario_groups.py"),
        "counts": dict(Counter(row["split"] for row in families)),
        "families": families,
        "limitation": "Train/validation/test contain40/10/10 broad semantic groups; five variants per specific family are correlated.",
    }


if __name__ == "__main__":
    result = build()
    with (ROOT / "source/scenarios.json").open("x") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(
        json.dumps(
            {"families": len(result["families"]), "counts": result["counts"], "semantic_groups": 60}
        )
    )
