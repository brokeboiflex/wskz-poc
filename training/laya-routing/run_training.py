"""Launch the approved isolated epoch; persist exact command and container identity."""

import argparse
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    evidence = root / "runs" / args.name
    evidence.mkdir(exist_ok=False)
    if subprocess.check_output(["docker", "ps", "-q"], text=True).strip():
        raise RuntimeError("Other containers active; inspect resource contention first")
    command = [
        "docker",
        "run",
        "-d",
        "--name",
        args.name,
        "--network",
        "none",
        "--memory",
        "10g",
        "--memory-swap",
        "10g",
        "--mount",
        "source=message-router_laya-models,target=/models,readonly",
    ]
    for name in (
        "train.py",
        "optimizer.py",
        "checkpoint.py",
        "select_checkpoint.py",
        "evaluate.py",
    ):
        command += ["--mount", f"type=bind,source={root / name},target=/code/{name},readonly"]
    for name in ("train.jsonl", "acceptance.json"):
        command += [
            "--mount",
            f"type=bind,source={root / 'data' / name},target=/inputs/{name},readonly",
        ]
    command += [
        "--mount",
        f"type=bind,source={root / 'policy.json'},target=/inputs/policy.json,readonly",
        "--mount",
        f"type=bind,source={root / 'work'},target=/workrun",
        "--env",
        "HF_HUB_OFFLINE=1",
        "--env",
        "TRANSFORMERS_OFFLINE=1",
        "--entrypoint",
        "python",
        "sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989",
        "-u",
        "/code/train.py",
        "--base",
        "/models/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual",
        "--train",
        "/inputs/train.jsonl",
        "--policy",
        "/inputs/policy.json",
        "--approval",
        "/inputs/acceptance.json",
        "--run",
        "/workrun/run-20260927",
    ]
    if args.resume:
        command.append("--resume")
    (evidence / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    (evidence / "container-id.txt").write_text(result.stdout)
    print(result.stdout.strip())


if __name__ == "__main__":
    main()
