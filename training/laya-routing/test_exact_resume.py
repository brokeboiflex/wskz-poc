"""CPU dropout/AdamW resume proof using the actual rolling checkpoint implementation."""

import random
import tempfile
from pathlib import Path

import numpy as np
import torch
from checkpoint import resolve, save
from optimizer import step_and_release


def run(interrupt):
    torch.manual_seed(42)
    random.seed(42)
    np.random.seed(42)
    model = torch.nn.Sequential(torch.nn.Linear(4, 8), torch.nn.Dropout(0.2), torch.nn.Linear(8, 5))
    optimizer = torch.optim.AdamW(model.parameters(), lr=2.5e-5, weight_decay=0.01, foreach=False)
    order = random.sample(range(32), 32)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for step in range(4):
            for index in order:
                sample = torch.tensor(np.random.normal(size=(1, 4)), dtype=torch.float32)
                loss = torch.nn.functional.cross_entropy(model(sample), torch.tensor([index % 5]))
                (loss / len(order)).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, foreach=False)
            step_and_release(optimizer)
            optimizer.zero_grad(set_to_none=True)
            if interrupt and step == 1:
                save(
                    root,
                    {
                        "model": model.state_dict(),
                        "optimizer": optimizer.state_dict(),
                        "torch_rng": torch.get_rng_state(),
                        "numpy_rng": np.random.get_state(),
                        "python_rng": random.getstate(),
                        "order": order,
                    },
                    torch.save,
                )
                restored = torch.load(resolve(root), mmap=True, weights_only=False)
                replacement = torch.nn.Sequential(
                    torch.nn.Linear(4, 8), torch.nn.Dropout(0.2), torch.nn.Linear(8, 5)
                )
                replacement.load_state_dict(restored["model"])
                model = replacement
                optimizer = torch.optim.AdamW(
                    model.parameters(), lr=2.5e-5, weight_decay=0.01, foreach=False
                )
                optimizer.load_state_dict(restored["optimizer"])
                order = restored["order"]
                torch.set_rng_state(restored["torch_rng"])
                np.random.set_state(restored["numpy_rng"])
                random.setstate(restored["python_rng"])
    return model.state_dict(), optimizer.state_dict()


def main():
    uninterrupted, uninterrupted_optimizer = run(False)
    resumed, resumed_optimizer = run(True)
    assert all(torch.equal(value, resumed[key]) for key, value in uninterrupted.items())
    assert uninterrupted_optimizer["param_groups"] == resumed_optimizer["param_groups"]
    for key, state in uninterrupted_optimizer["state"].items():
        assert all(
            torch.equal(value, resumed_optimizer["state"][key][name])
            for name, value in state.items()
        )
    print(
        "Bitwise equality: uninterrupted vs resumed CPU dropout model and AdamW state after four updates"
    )


if __name__ == "__main__":
    main()
