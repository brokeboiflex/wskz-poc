"""Read-only model provenance; no inference and no benchmark access."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    path = args.models / "models/manifests/registry.ollama.ai/library/gemma4/e2b"
    expected = "7fbdbf8f5e45a75bb122155ed546e765b4d9c53a1285f62fd9f506baa1c5a47e"
    if digest(path) != expected:
        raise ValueError("Gemma manifest changed")
    manifest = json.loads(path.read_text())
    for entry in [manifest["config"], *manifest["layers"]]:
        blob = args.models / "models/blobs" / entry["digest"].replace(":", "-")
        if blob.stat().st_size != entry["size"] or digest(blob) != entry["digest"].split(":")[1]:
            raise ValueError("Gemma asset integrity mismatch")
    report = {
        "model": "gemma4:e2b",
        "manifest_sha256": expected,
        "manifest": manifest,
        "layers_verified": True,
        "server_image": "sha256:f3d9e1f71a3f6d54ac426206726a3f18b412eece49445cb6230bf60da52119b9",
        "script_sha256": digest(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(
        json.dumps({"model": report["model"], "layers_verified": True, "output": str(args.output)})
    )
