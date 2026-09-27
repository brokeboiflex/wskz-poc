"""Observed CPU training feasibility; no evaluation corpus or production writes."""

import argparse
import hashlib
import json
import random
import resource
import shutil
import time
from pathlib import Path

from optimizer import step_and_release


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, choices=(1, 2), default=2)
    parser.add_argument("--verify-checkpoint", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)

    def emit(event, **fields):
        record = {"event": event, **fields}
        print(json.dumps(record, ensure_ascii=False), flush=True)
        with (args.output / "events.jsonl").open("a") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    import numpy as np
    import torch
    import transformers
    from laya.common import QTYPES, build_model, build_sequence
    from safetensors.torch import load_file
    from transformers import AutoTokenizer

    root = Path(__file__).parent
    policy = json.loads((root / "policy.json").read_text())
    rows = [json.loads(line) for line in (root / "preflight-train.jsonl").read_text().splitlines()]
    assert len(rows) == 16 and all(row["split"] == "train" for row in rows)
    assert len({row["family"] for row in rows}) == 16
    labels = list(policy["criteria"])
    weights = args.model / "model.safetensors"
    expected = "9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204"
    actual = digest(weights)
    if actual != expected:
        raise RuntimeError("Base weights differ from approved snapshot")
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)
    cfg = json.loads((args.model / "rl_agent_config.json").read_text())
    tok = AutoTokenizer.from_pretrained(args.model / "tokenizer", local_files_only=True)
    q = {"t": "choice", "ins": policy["instructions"], "crit": policy["criteria"]}
    option_lengths = {
        k: len(tok(" " + k + ": " + v, add_special_tokens=False)["input_ids"])
        for k, v in policy["criteria"].items()
    }
    instruction_length = len(
        tok("choice question: " + q["ins"], add_special_tokens=False)["input_ids"]
    )
    assert max(option_lengths.values()) <= 48
    assert instruction_length + sum(option_lengths.values()) + 5 <= cfg["head_max_len"]
    items = []
    for row in rows:
        ids, markers = build_sequence(tok, row["message"], q, 8192, cfg["head_max_len"])
        state = tok(row["message"], add_special_tokens=False)["input_ids"]
        assert len(markers) == 5 and ids[-len(state) - 1 : -1] == state
        items.append((ids, markers, labels.index(row["label"])))
    emit(
        "inputs",
        weights_sha256=actual,
        policy_sha256=digest(root / "policy.json"),
        train_sha256=digest(root / "preflight-train.jsonl"),
        torch=torch.__version__,
        transformers=transformers.__version__,
        option_lengths=option_lengths,
        instruction_length=instruction_length,
        sequence_lengths=[len(x[0]) for x in items],
        disk_free_bytes=shutil.disk_usage(args.output).free,
    )
    start = time.monotonic()
    model = build_model(cfg, encoder_dir=str(args.model / "encoder"), pretrained=False)
    model.load_state_dict(load_file(weights), strict=True)
    model.float()
    model.encoder.config.reference_compile = False
    model.encoder.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False}
    )
    model.head_checkpointing = True
    model.train()
    # The action head is not part of choice loss; leave its weights untouched.
    for parameter in model.act_head.parameters():
        parameter.requires_grad_(False)
    encoder, head = [], []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            (encoder if name.startswith("encoder.") else head).append(parameter)
    optimizer = torch.optim.AdamW(
        [{"params": encoder, "lr": 2.5e-5}, {"params": head, "lr": 1e-4}],
        weight_decay=0.01,
        foreach=False,
    )
    all_bytes = sum(x.numel() * x.element_size() for x in model.state_dict().values())
    train_bytes = sum(x.numel() * x.element_size() for x in encoder + head)
    emit(
        "loaded",
        seconds=time.monotonic() - start,
        parameter_bytes=all_bytes,
        full_checkpoint_estimate_bytes=all_bytes + 2 * train_bytes,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
    )
    timings, update_times = [], []
    for step in range(args.steps):
        emit("step_started", step=step + 1, optimizer_states=len(optimizer.state))
        for row, (ids, markers, label) in zip(rows, items, strict=True):
            started = time.monotonic()
            logits, actions = model(
                torch.tensor([ids]),
                torch.ones((1, len(ids)), dtype=torch.long),
                torch.tensor([markers]),
                torch.ones((1, 5), dtype=torch.bool),
                torch.tensor([QTYPES["choice"]]),
            )
            loss = torch.nn.functional.cross_entropy(logits, torch.tensor([label]))
            (loss / 16).backward()
            seconds = time.monotonic() - started
            timings.append(seconds)
            emit(
                "train_microbatch",
                step=step + 1,
                id=row["id"],
                message=row["message"],
                label=row["label"],
                logits=logits.detach().tolist(),
                loss=loss.item(),
                seconds=seconds,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            )
            del logits, actions, loss
        norm = torch.nn.utils.clip_grad_norm_(encoder + head, 1.0, foreach=False)
        assert torch.isfinite(norm)
        step_start = time.monotonic()
        step_and_release(optimizer)
        update_times.append(time.monotonic() - step_start)
        emit(
            "optimizer_step",
            step=step + 1,
            seconds=update_times[-1],
            gradient_norm=norm.item(),
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        )
        optimizer.zero_grad(set_to_none=True)
    checkpoint_bytes = all_bytes + sum(
        value.numel() * value.element_size()
        for state in optimizer.state.values()
        for value in state.values()
        if isinstance(value, torch.Tensor)
    )
    # Exact state sizes, not an allocation. Two full files for atomic replacement,
    # and FP32 best weights to avoid introducing quantization into model selection.
    disk_required = checkpoint_bytes * 2 + all_bytes + 4 * 1024**3
    free = shutil.disk_usage(args.output).free
    checkpoint_probe = None
    if args.verify_checkpoint:
        if free < disk_required:
            raise RuntimeError("Checkpoint probe requires the full disk reserve")
        import gc

        from checkpoint import resolve, save
        from safetensors.torch import save_file

        def tensor_hashes(values):
            return {
                key: hashlib.sha256(
                    memoryview(value.detach().cpu().contiguous().numpy()).cast("B")
                ).hexdigest()
                for key, value in values.items()
            }

        before_model = tensor_hashes(model.state_dict())
        before_optimizer = {
            str(key): tensor_hashes(
                {name: value for name, value in state.items() if isinstance(value, torch.Tensor)}
            )
            for key, state in optimizer.state_dict()["state"].items()
        }
        payload = {
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "torch_rng": torch.get_rng_state(),
            "numpy_rng": np.random.get_state(),
            "python_rng": random.getstate(),
        }
        checkpoint_dir = args.output / "checkpoint"
        checkpoint_dir.mkdir()
        save_start = time.monotonic()
        saved = save(checkpoint_dir, payload, torch.save)
        save_seconds = time.monotonic() - save_start
        emit("checkpoint_saved", bytes=saved.stat().st_size, seconds=save_seconds)
        del payload, model, optimizer, encoder, head, parameter, norm
        gc.collect()
        loaded = torch.load(
            resolve(checkpoint_dir), map_location="cpu", mmap=True, weights_only=False
        )
        model = build_model(cfg, encoder_dir=str(args.model / "encoder"), pretrained=False)
        model.load_state_dict(loaded["model"], strict=True)
        model.float()
        for parameter in model.act_head.parameters():
            parameter.requires_grad_(False)
        encoder, head = [], []
        for name, parameter in model.named_parameters():
            if parameter.requires_grad:
                (encoder if name.startswith("encoder.") else head).append(parameter)
        optimizer = torch.optim.AdamW(
            [{"params": encoder, "lr": 2.5e-5}, {"params": head, "lr": 1e-4}],
            weight_decay=0.01,
            foreach=False,
        )
        optimizer.load_state_dict(loaded["optimizer"])
        assert tensor_hashes(model.state_dict()) == before_model
        after_optimizer = {
            str(key): tensor_hashes(
                {name: value for name, value in state.items() if isinstance(value, torch.Tensor)}
            )
            for key, state in optimizer.state_dict()["state"].items()
        }
        assert after_optimizer == before_optimizer
        torch.set_rng_state(loaded["torch_rng"])
        np.random.set_state(loaded["numpy_rng"])
        random.setstate(loaded["python_rng"])
        export = args.output / "probe-model.safetensors"
        save_file(
            {k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()}, str(export)
        )
        assert tensor_hashes(load_file(export)) == before_model
        checkpoint_probe = {
            "passed": True,
            "checkpoint_sha256": digest(saved),
            "export_sha256": digest(export),
            "checkpoint_bytes": saved.stat().st_size,
            "export_bytes": export.stat().st_size,
            "save_seconds": save_seconds,
            "tensor_exact_reload": True,
            "export_tensor_parity": True,
            "live_api_parity": False,
            "quality_evaluation": False,
        }
        emit("checkpoint_verified", **checkpoint_probe)
    result = {
        "optimizer_steps": args.steps,
        "microbatches": 16 * args.steps,
        "trained_weights_saved": args.verify_checkpoint,
        "checkpoint_probe": checkpoint_probe,
        "production_changed": False,
        "checkpoint_tensor_bytes": checkpoint_bytes,
        "atomic_checkpoint_plus_best_plus_reserve_bytes": disk_required,
        "disk_free_bytes": free,
        "disk_gate_passed": free >= disk_required,
        "four_epoch_train_seconds_estimate": (
            sum(timings) / len(timings) * 8000 + sum(update_times) / len(update_times) * 500
        ),
        "estimate_excludes_validation_and_checkpoint_io": True,
        "estimate_only_covers_preflight_sequence_lengths": True,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "script_sha256": digest(__file__),
        "optimizer_sha256": digest(root / "optimizer.py"),
    }
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    emit("completed", **result)


if __name__ == "__main__":
    main()
