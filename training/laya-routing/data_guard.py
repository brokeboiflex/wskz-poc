"""Offline leakage screening. Never emits old benchmark text or uses model scores."""

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LABELS = {"human_resources", "payroll", "help_desk", "it", "other"}
COUNTS = {"train": 2000, "validation": 500, "test": 500}
OLD_SHA = "bd3cf10bc628dc0c27349201b443ef95a9b11112b272573766d323c547f5cd0e"
SMOKE_SHA = "34b55ac3f3854c93547500fa60e7b4344dc41f42c1be31a0fb9c016d91da131b"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_exclusions(benchmark, smoke):
    if sha(benchmark) != OLD_SHA or sha(smoke) != SMOKE_SHA:
        raise ValueError("Frozen benchmark/smoke hash mismatch")
    old, small = json.loads(benchmark.read_text()), json.loads(smoke.read_text())
    if len(old) != 500 or len(small) != 15:
        raise ValueError("Frozen corpus counts differ")
    return old + small


def normalize(message):
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", message).casefold()))


def shingles(message):
    words = normalize(message).split()
    return {tuple(words[i : i + 3]) for i in range(len(words) - 2)}


def validate(rows, forbidden, *, complete=True):
    """Return failures; full CLI always demands 2000/500/500, balanced classes."""
    errors = []
    families = defaultdict(set)
    groups = defaultdict(set)
    family_groups = defaultdict(set)
    counts = Counter()
    ids, seen = set(), {}
    valid = []
    for row in rows:
        if not isinstance(row, dict) or not all(
            isinstance(row.get(k), str) and row[k].strip()
            for k in ("id", "family", "split", "label", "message")
        ):
            errors.append({"kind": "invalid_record"})
            continue
        identifier = row["id"]
        if identifier in ids:
            errors.append({"kind": "duplicate_id", "id": identifier})
        ids.add(identifier)
        if row["split"] not in COUNTS or row["label"] not in LABELS:
            errors.append({"kind": "invalid_split_or_label", "id": identifier})
            continue
        text = normalize(row["message"])
        if not text or len(row["message"]) > 4000:
            errors.append({"kind": "invalid_message", "id": identifier})
        if text in seen:
            errors.append({"kind": "duplicate_text", "ids": [seen[text], identifier]})
        seen[text] = identifier
        families[row["family"]].add(row["split"])
        group = row.get("semantic_group")
        if isinstance(group, str) and group.strip():
            groups[group].add(row["split"])
            family_groups[row["family"]].add(group)
        elif complete:
            errors.append({"kind": "missing_semantic_group", "id": identifier})
        counts[row["split"], row["label"]] += 1
        valid.append((row, text, shingles(text)))
    for family, splits in families.items():
        if len(splits) != 1:
            errors.append({"kind": "family_split", "family": family, "splits": sorted(splits)})
    for group, splits in groups.items():
        if len(splits) != 1:
            errors.append(
                {"kind": "semantic_group_split", "group": group, "splits": sorted(splits)}
            )
    for family, values in family_groups.items():
        if len(values) != 1:
            errors.append({"kind": "family_group_mismatch", "family": family})
    if complete:
        for split, expected in (("train", 40), ("validation", 10), ("test", 10)):
            actual = sum(splits == {split} for splits in groups.values())
            if actual != expected:
                errors.append(
                    {
                        "kind": "semantic_group_count",
                        "split": split,
                        "actual": actual,
                        "expected": expected,
                    }
                )
        for split, total in COUNTS.items():
            for label in sorted(LABELS):
                if counts[split, label] != total // 5:
                    errors.append(
                        {
                            "kind": "wrong_count",
                            "split": split,
                            "label": label,
                            "actual": counts[split, label],
                            "expected": total // 5,
                        }
                    )
    old = [
        (row["message"], normalize(row["message"]), shingles(row["message"])) for row in forbidden
    ]
    # Inverted index avoids comparing unrelated pairs in larger corpora.
    index = defaultdict(set)
    targets = [(f"new:{row['id']}", text, grams, row["split"]) for row, text, grams in valid]
    targets += [
        (f"excluded:{i}", text, grams, "excluded") for i, (_, text, grams) in enumerate(old)
    ]
    for i, (_, text, grams, _) in enumerate(targets):
        index[("exact", text)].add(i)
        for gram in grams:
            index[gram].add(i)
    for i, (row, text, grams) in enumerate(valid):
        candidates = set(index[("exact", text)])
        for gram in grams:
            candidates.update(index[gram])
        for j in sorted(candidates):
            if j <= i:
                continue
            name, other_text, other_grams, split = targets[j]
            if split == row["split"]:
                continue
            union = grams | other_grams
            intersection = len(grams & other_grams)
            jaccard = intersection / max(1, len(union))
            containment = intersection / max(1, min(len(grams), len(other_grams)))
            exact = text == other_text
            if exact or jaccard >= 0.45 or (intersection >= 8 and containment >= 0.70):
                errors.append(
                    {
                        "kind": "excluded_or_cross_split_overlap",
                        "id": row["id"],
                        "match": name,
                        "exact": exact,
                        "jaccard": jaccard,
                        "containment": containment,
                    }
                )
    return {
        "passed": not errors,
        "complete_corpus_required": complete,
        "records": len(rows),
        "families": len(families),
        "semantic_groups": len(groups),
        "counts": {f"{s}/{label}": count for (s, label), count in sorted(counts.items())},
        "errors": errors,
        "semantic_review_required": True,
        "limitation": "Lexical screening cannot prove absence of paraphrase or semantic leakage.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--smoke", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text().splitlines()]
    forbidden = frozen_exclusions(args.benchmark, args.smoke)
    if args.preflight_only and (len(rows) != 16 or any(r["split"] != "train" for r in rows)):
        raise SystemExit("Preflight mode accepts only sixteen train records")
    report = validate(rows, forbidden, complete=not args.preflight_only)
    report["ready_for_training"] = False
    report["readiness_reason"] = (
        "A separate semantic review bound to input hashes is still required."
    )
    report["inputs"] = {str(p): sha(p) for p in (args.input, args.benchmark, args.smoke)}
    with args.output.open("x") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "records": report["records"],
                "errors": len(report["errors"]),
                "complete": not args.preflight_only,
            }
        )
    )
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
