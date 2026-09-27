"""Training-only host for an exact local checkpoint behind the existing HTTP adapter."""

import hashlib
import json
import os
import sys
from pathlib import Path
from threading import Lock

sys.path.insert(0, "/runtime-source")
from runtime import InferenceService, create_app  # noqa: E402


class CheckpointPredictor:
    def __init__(self):
        import torch
        from laya import Agent

        path = Path(os.environ["CHECKPOINT_PATH"])
        expected = os.environ["CHECKPOINT_SHA256"]
        if os.environ.get("LAYA_CPU_AMP", "").lower() not in ("", "0", "false", "off"):
            raise ValueError("Evaluation requires the FP32 CPU path")
        with (path / "model.safetensors").open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != expected:
            raise ValueError("Checkpoint hash mismatch")
        self.weights_sha256 = actual
        manifest_path = Path(os.environ["BASE_ASSETS_MANIFEST"])
        assets = json.loads(manifest_path.read_text())
        for name, expected_hash in assets.items():
            if name == "model.safetensors":
                continue
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Invalid base asset manifest")
            with (path / relative).open("rb") as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != expected_hash:
                    raise ValueError(f"Tokenizer/configuration asset differs: {name}")
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        self.agent = Agent(str(path), device="cpu", compile=False)
        self.lock = Lock()
        print(json.dumps({"checkpoint_sha256": actual, "device": "cpu"}), flush=True)

    def predict(self, state, questions):
        with self.lock:
            return self.agent.system_one(state, questions, max_len=8192)


# This module is only mounted in the isolated training evaluation runtime.
predictor = CheckpointPredictor()
app = create_app(InferenceService(predictor))


@app.get("/health/checkpoint")
def checkpoint_identity():
    return {"weights_sha256": predictor.weights_sha256, "device": "cpu"}
