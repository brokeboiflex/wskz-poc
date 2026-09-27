"""Tokenize frozen splits without loading weights or making predictions."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    for name in ("base", "data", "policy", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    from laya.common import build_sequence
    from transformers import AutoTokenizer

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    policy = json.loads(args.policy.read_text())
    cfg = json.loads((args.base / "rl_agent_config.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(args.base / "tokenizer", local_files_only=True)
    question = {"t": "choice", "ins": policy["instructions"], "crit": policy["criteria"]}
    options = [
        len(tokenizer(" " + k + ": " + v, add_special_tokens=False)["input_ids"])
        for k, v in policy["criteria"].items()
    ]
    question_length = len(
        tokenizer("choice question: " + policy["instructions"], add_special_tokens=False)[
            "input_ids"
        ]
    )
    if max(options) > 48 or question_length + sum(options) + 5 > cfg["head_max_len"]:
        raise ValueError("Policy truncation")
    report = {
        "passed": True,
        "predictions_made": 0,
        "policy_sha256": sha(args.policy),
        "splits": {},
    }
    for split, count in (("train", 2000), ("validation", 500), ("test", 500)):
        path = args.data / f"{split}.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if len(rows) != count:
            raise ValueError("Incomplete corpus")
        lengths = []
        for row in rows:
            ids, markers = build_sequence(
                tokenizer, row["message"], question, 8192, cfg["head_max_len"]
            )
            raw = tokenizer(row["message"], add_special_tokens=False)["input_ids"]
            if not raw or ids[-len(raw) - 1 : -1] != raw or len(markers) != 5:
                raise ValueError(f"Truncated input: {row['id']}")
            lengths.append(len(ids))
        report["splits"][split] = {
            "sha256": sha(path),
            "records": count,
            "min_tokens": min(lengths),
            "max_tokens": max(lengths),
            "truncated": 0,
        }
    report["code_sha256"] = sha(Path(__file__))
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
