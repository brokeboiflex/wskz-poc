"""Offline supervised adaptation. The trainer never reads the test corpus or runs inference."""

import argparse
import hashlib
import importlib.metadata
import json
import random
import resource
import shutil
import signal
import time
from pathlib import Path

from checkpoint import atomic_json, resolve, save
from optimizer import step_and_release

BASE_SHA = "9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204"
CONFIG = {
    "seed": 42,
    "batch": 16,
    "epochs": 4,
    "encoder_lr": 2.5e-5,
    "head_lr": 1e-4,
    "weight_decay": 0.01,
    "clip": 1.0,
    "max_training_seconds": 28800,
    "reserve_bytes": 4 * 1024**3,
    "checkpoint_every_steps": 20,
    "scheduler": None,
    "dtype": "float32",
    "max_len": 8192,
}


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def require_training_input(rows):
    from collections import Counter

    labels = {"human_resources", "payroll", "help_desk", "it", "other"}
    if len(rows) != 2000 or any(r.get("split") != "train" for r in rows):
        raise ValueError("Only the complete 2000-row training split is accepted")
    if Counter(r["label"] for r in rows) != {label: 400 for label in labels}:
        raise ValueError("Training class balance differs")
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate training IDs")


def resume_contract(state, contract):
    if state["contract"] != contract:
        raise ValueError("Resume rejected: data, model, policy, code or configuration changed")
    if state["scheduler"] is not None:
        raise ValueError("Unexpected scheduler")
    if state["position"] % CONFIG["batch"] and state["position"] != 2000:
        raise ValueError("Checkpoint is not at an optimizer boundary")


def main():
    parser = argparse.ArgumentParser()
    for name in ("base", "train", "policy", "approval", "run"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    import numpy as np
    import torch
    from laya.common import QTYPES, build_model, build_sequence
    from safetensors.torch import load_file, save_file
    from transformers import AutoTokenizer

    # Acceptance records the reviews and the user's explicit no-more-critic instruction.
    acceptance = json.loads(args.approval.read_text())
    policy = json.loads(args.policy.read_text())
    rows = [json.loads(line) for line in args.train.read_text().splitlines()]
    require_training_input(rows)
    if acceptance.get("ready_for_training") is not True or not acceptance.get("review_notes"):
        raise ValueError("Hash-bound data acceptance required")
    weights = args.base / "model.safetensors"
    assets = {
        str(path.relative_to(args.base)): sha(path)
        for path in sorted(args.base.rglob("*"))
        if path.is_file()
    }
    if assets.get("model.safetensors") != BASE_SHA:
        raise ValueError("Unapproved base weights")
    contract = {
        "train_sha256": sha(args.train),
        "policy_sha256": sha(args.policy),
        "approval_sha256": sha(args.approval),
        "trainer_sha256": sha(__file__),
        "optimizer_sha256": sha(Path(__file__).with_name("optimizer.py")),
        "checkpoint_code_sha256": sha(Path(__file__).with_name("checkpoint.py")),
        "selector_sha256": sha(Path(__file__).with_name("select_checkpoint.py")),
        "base_assets": assets,
        "configuration": CONFIG,
        "torch": torch.__version__,
        "libraries": {
            package: importlib.metadata.version(package)
            for package in ("laya", "transformers", "numpy", "safetensors")
        },
        "runtime_image": "sha256:4d0ffa68273f122a8bb1db1a14d1503b7cca218c91d05c4970ede69601107989",
    }
    if acceptance.get("train_sha256") != contract["train_sha256"]:
        raise ValueError("Reviewed training data differs")
    if acceptance.get("policy_sha256") != contract["policy_sha256"]:
        raise ValueError("Reviewed policy differs")
    if args.resume:
        if not (args.run / "checkpoints/latest.json").exists():
            raise ValueError("Resume requested without a complete checkpoint")
    else:
        args.run.mkdir(parents=True, exist_ok=False)
        (args.run / "checkpoints").mkdir()
        atomic_json(args.run / "contract.json", contract)
    if json.loads((args.run / "contract.json").read_text()) != contract:
        raise ValueError("Run contract differs")

    def emit(event, **fields):
        record = {"event": event, "time": time.time(), **fields}
        with (args.run / "events.jsonl").open("a") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
        print(json.dumps(record, ensure_ascii=False), flush=True)

    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(CONFIG["seed"])
    np.random.seed(CONFIG["seed"])
    random.seed(CONFIG["seed"])
    cfg = json.loads((args.base / "rl_agent_config.json").read_text())
    tok = AutoTokenizer.from_pretrained(args.base / "tokenizer", local_files_only=True)
    question = {"t": "choice", "ins": policy["instructions"], "crit": policy["criteria"]}
    labels = list(policy["criteria"])
    option_lengths = [
        len(tok(" " + key + ": " + value, add_special_tokens=False)["input_ids"])
        for key, value in policy["criteria"].items()
    ]
    question_length = len(
        tok("choice question: " + policy["instructions"], add_special_tokens=False)["input_ids"]
    )
    if max(option_lengths) > 48 or question_length + sum(option_lengths) + 5 > cfg["head_max_len"]:
        raise ValueError("Question/options would be truncated")
    items = []
    for row in rows:
        ids, markers = build_sequence(
            tok, row["message"], question, CONFIG["max_len"], cfg["head_max_len"]
        )
        raw = tok(row["message"], add_special_tokens=False)["input_ids"]
        if not raw or ids[-len(raw) - 1 : -1] != raw or len(markers) != 5:
            raise ValueError(f"Truncation or malformed sequence: {row['id']}")
        items.append((ids, markers, labels.index(row["label"])))
    atomic_json(
        args.run / "tokenization.json",
        {"lengths": [len(item[0]) for item in items], "truncated": 0, "contract": contract},
    )
    model = build_model(cfg, encoder_dir=str(args.base / "encoder"), pretrained=False)
    model.float()
    model.encoder.config.reference_compile = False
    model.encoder.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False}
    )
    model.head_checkpointing = True
    for parameter in model.act_head.parameters():
        parameter.requires_grad_(False)
    encoder, head = [], []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            (encoder if name.startswith("encoder.") else head).append(parameter)
    optimizer = torch.optim.AdamW(
        [
            {"params": encoder, "lr": CONFIG["encoder_lr"]},
            {"params": head, "lr": CONFIG["head_lr"]},
        ],
        weight_decay=CONFIG["weight_decay"],
        foreach=False,
    )
    state = {
        "contract": contract,
        "epoch": 1,
        "position": 0,
        "steps": 0,
        "order": random.sample(range(len(rows)), len(rows)),
        "training_seconds": 0.0,
        "scheduler": None,
        "phase": "training",
    }
    if args.resume:
        # Only task-owned, integrity-checked checkpoints are deserialized.
        path = resolve(args.run / "checkpoints")
        restored = torch.load(path, mmap=True, weights_only=False, map_location="cpu")
        resume_contract(restored, contract)
        model.load_state_dict(restored.pop("model"), strict=True)
        optimizer.load_state_dict(restored.pop("optimizer"))
        torch.set_rng_state(restored.pop("torch_rng"))
        np.random.set_state(restored.pop("numpy_rng"))
        random.setstate(restored.pop("python_rng"))
        state = restored
        if state["phase"] == "awaiting_validation":
            from select_checkpoint import choose

            decision = json.loads(
                (args.run / f"validation-{state['epoch']}/decision.json").read_text()
            )
            export_meta = json.loads(
                (args.run / f"export/epoch-{state['epoch']}/provenance.json").read_text()
            )
            if (
                decision.get("epoch") != state["epoch"]
                or decision.get("weights_sha256") != export_meta["weights_sha256"]
                or decision.get("validation_sha256") != acceptance.get("validation_sha256")
                or decision.get("review_complete") is not True
                or decision.get("selector_sha256") != contract["selector_sha256"]
                or decision.get("policy_sha256") != contract["policy_sha256"]
            ):
                raise ValueError("Complete reviewed validation for this exact epoch is required")
            selected, should_stop = choose(decision["history"])
            if (
                decision["selected_epoch"] != selected["epoch"]
                or decision["selected_sha256"] != selected["weights_sha256"]
                or decision["stop"] != should_stop
                or len(decision["history"]) != state["epoch"]
            ):
                raise ValueError("Validation decision violates the fixed selection rule")
            for prior in decision["history"]:
                if prior["metrics_sha256"] != sha(
                    args.run / f"validation-{prior['epoch']}/metrics.json"
                ):
                    raise ValueError("Validation history changed since selection")
            if decision.get("stop") is not False or state["epoch"] >= CONFIG["epochs"]:
                emit("stopped_after_validation", decision=decision)
                return
            state.update(
                epoch=state["epoch"] + 1,
                position=0,
                order=random.sample(range(len(rows)), len(rows)),
                phase="training",
            )
    else:
        model.load_state_dict(load_file(weights), strict=True)
    model.train()
    stopped = False

    def stop_requested(_signum, _frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop_requested)
    signal.signal(signal.SIGINT, stop_requested)
    model_bytes = sum(v.numel() * v.element_size() for v in model.state_dict().values())
    checkpoint_bound = model_bytes + 2 * sum(p.numel() * p.element_size() for p in encoder + head)

    def disk_gate():
        # A new full checkpoint plus an export and reserve must fit now; latest already occupies disk.
        return (
            shutil.disk_usage(args.run).free
            >= checkpoint_bound + model_bytes + CONFIG["reserve_bytes"]
        )

    def checkpoint():
        if shutil.disk_usage(args.run).free < checkpoint_bound + CONFIG["reserve_bytes"]:
            raise ValueError(
                "Cannot checkpoint within disk reserve; previous complete generation preserved"
            )
        payload = {
            **state,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "torch_rng": torch.get_rng_state(),
            "numpy_rng": np.random.get_state(),
            "python_rng": random.getstate(),
        }
        save(args.run / "checkpoints", payload, torch.save)
        emit("checkpoint", epoch=state["epoch"], position=state["position"], steps=state["steps"])

    if not disk_gate():
        raise ValueError("Insufficient disk for checkpoint, export and 4 GiB reserve")
    # Initial state permits exact replay if the first update is interrupted.
    if not args.resume:
        checkpoint()
    while state["position"] < len(rows):
        if (
            stopped
            or state["training_seconds"] >= CONFIG["max_training_seconds"]
            or not disk_gate()
        ):
            checkpoint()
            emit(
                "paused",
                reason="signal, training time or disk gate",
                state={k: v for k, v in state.items() if k != "order"},
            )
            return
        started = time.monotonic()
        batch = state["order"][state["position"] : state["position"] + CONFIG["batch"]]
        losses = []
        for index in batch:
            ids, markers, label = items[index]
            logits, action = model(
                torch.tensor([ids]),
                torch.ones((1, len(ids)), dtype=torch.long),
                torch.tensor([markers]),
                torch.ones((1, 5), dtype=torch.bool),
                torch.tensor([QTYPES["choice"]]),
            )
            loss = torch.nn.functional.cross_entropy(logits, torch.tensor([label]))
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite loss; last complete checkpoint preserved")
            (loss / len(batch)).backward()
            losses.append(float(loss.detach()))
            del logits, action, loss
        norm = torch.nn.utils.clip_grad_norm_(encoder + head, CONFIG["clip"], foreach=False)
        if not torch.isfinite(norm):
            raise ValueError("Nonfinite gradient; last complete checkpoint preserved")
        step_and_release(optimizer)
        optimizer.zero_grad(set_to_none=True)
        state["position"] += len(batch)
        state["steps"] += 1
        state["training_seconds"] += time.monotonic() - started
        emit(
            "optimizer_step",
            epoch=state["epoch"],
            position=state["position"],
            steps=state["steps"],
            losses=losses,
            ids=[rows[i]["id"] for i in batch],
            gradient_norm=float(norm),
            training_seconds=state["training_seconds"],
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        )
        if state["steps"] % CONFIG["checkpoint_every_steps"] == 0:
            checkpoint()
    state["phase"] = "completing_export"
    checkpoint()
    export = args.run / f"export/epoch-{state['epoch']}"
    if export.exists():
        provenance = json.loads((export / "provenance.json").read_text())
        if (
            provenance["contract"] != contract
            or provenance["epoch"] != state["epoch"]
            or provenance["steps"] != state["steps"]
            or provenance["weights_sha256"] != sha(export / "model.safetensors")
        ):
            raise ValueError("Existing export does not match completing checkpoint")
        state["phase"] = "awaiting_validation"
        checkpoint()
        emit("awaiting_validation", epoch=state["epoch"], export=str(export))
        return
    import uuid

    temporary = export.with_name(export.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.mkdir(parents=True, exist_ok=False)
    for name in ("encoder", "tokenizer"):
        shutil.copytree(args.base / name, temporary / name)
    shutil.copy2(args.base / "rl_agent_config.json", temporary)
    save_file(model.state_dict(), temporary / "model.safetensors")
    atomic_json(
        temporary / "provenance.json",
        {
            "contract": contract,
            "epoch": state["epoch"],
            "steps": state["steps"],
            "weights_sha256": sha(temporary / "model.safetensors"),
        },
    )
    temporary.rename(export)
    state["phase"] = "awaiting_validation"
    checkpoint()
    emit("awaiting_validation", epoch=state["epoch"], export=str(export))


if __name__ == "__main__":
    main()
