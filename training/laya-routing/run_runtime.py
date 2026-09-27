"""Start isolated, hash-checked runtime and adapter; never starts an evaluation."""

import argparse
import json
import subprocess
from pathlib import Path

from evaluate import new_json, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch", type=int, choices=range(1, 5))
    parser.add_argument("--base", action="store_true")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    if args.base == bool(args.epoch):
        parser.error("Specify exactly one of --base or --epoch")
    root = Path(__file__).resolve().parent
    run = root / "work/run-20260927"
    contract = json.loads((run / "contract.json").read_text())
    evidence = root / "runs" / args.name
    if subprocess.check_output(["docker", "ps", "-q"], text=True).strip():
        raise RuntimeError("Inspect and stop task training/evaluation before serving")
    evidence.mkdir(exist_ok=False)
    assets = evidence / "base-assets.json"
    new_json(assets, contract["base_assets"])
    network = "wskz-laya-evaluation"
    found = subprocess.run(
        ["docker", "network", "inspect", network], capture_output=True, text=True
    )
    if found.returncode:
        subprocess.run(["docker", "network", "create", "--internal", network], check=True)
    elif not json.loads(found.stdout)[0]["Internal"]:
        raise RuntimeError("Evaluation network must be internal")
    runtime = args.name + "-runtime"
    command = [
        "docker",
        "run",
        "-d",
        "--name",
        runtime,
        "--network",
        network,
        "--memory",
        "10g",
        "--memory-swap",
        "10g",
    ]
    if args.base:
        command += ["--mount", "source=message-router_laya-models,target=/models,readonly"]
        path = "/models/hub/models--convaiinnovations--laya/snapshots/55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851/multilingual"
        weights = contract["base_assets"]["model.safetensors"]
    else:
        export = run / f"export/epoch-{args.epoch}"
        weights = sha(export / "model.safetensors")
        if json.loads((export / "provenance.json").read_text())["weights_sha256"] != weights:
            raise ValueError("Export provenance mismatch")
        command += ["--mount", f"type=bind,source={export},target=/checkpoint,readonly"]
        path = "/checkpoint"
    for source, target in (
        (root / "serve_checkpoint.py", "/code/serve_checkpoint.py"),
        (root.parents[1] / "services/laya-runtime/runtime.py", "/runtime-source/runtime.py"),
        (assets, "/inputs/base-assets.json"),
    ):
        command += ["--mount", f"type=bind,source={source},target={target},readonly"]
    for value in (
        f"CHECKPOINT_PATH={path}",
        f"CHECKPOINT_SHA256={weights}",
        "BASE_ASSETS_MANIFEST=/inputs/base-assets.json",
        "LAYA_CPU_AMP=0",
        "HF_HUB_OFFLINE=1",
        "TRANSFORMERS_OFFLINE=1",
        "PYTHONPATH=/code",
    ):
        command += ["--env", value]
    command += [
        "--entrypoint",
        "uvicorn",
        contract["runtime_image"],
        "serve_checkpoint:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--workers",
        "1",
        "--no-access-log",
    ]
    new_json(evidence / "runtime-command.json", command)
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    (evidence / "runtime-id.txt").write_text(result.stdout)
    adapter = [
        "docker",
        "run",
        "-d",
        "--name",
        args.name + "-adapter",
        "--network",
        network,
        "--publish",
        "127.0.0.1:18091:8000",
        "--mount",
        f"type=bind,source={root / 'serve_adapter.py'},target=/code/serve_adapter.py,readonly",
        "--env",
        "PYTHONPATH=/code:/app",
        "--env",
        f"LAYA_BASE_URL=http://{runtime}:8000",
        "--env",
        "LAYA_MODEL=multilingual",
        "--entrypoint",
        "uvicorn",
        "sha256:37701ba29c1d2f7c2f2bb31ae307ee21b77642216f3931f16355456fd7506e5b",
        "serve_adapter:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--workers",
        "1",
        "--no-access-log",
    ]
    new_json(evidence / "adapter-command.json", adapter)
    result = subprocess.run(adapter, check=True, text=True, capture_output=True)
    (evidence / "adapter-id.txt").write_text(result.stdout)
    # Docker does not publish host ports on an internal-only network. Only the
    # HTTP adapter gets the ingress bridge; the model remains internal-only.
    ingress = ["docker", "network", "connect", "bridge", args.name + "-adapter"]
    new_json(evidence / "ingress-command.json", ingress)
    subprocess.run(ingress, check=True)
    new_json(evidence / "identity.json", {"weights_sha256": weights, "epoch": args.epoch})
    print(json.dumps({"runtime": runtime, "weights_sha256": weights}))


if __name__ == "__main__":
    main()
