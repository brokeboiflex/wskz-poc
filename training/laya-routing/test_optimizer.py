"""Bitwise equality of low-peak-memory updates and standard PyTorch AdamW."""

import copy
import io
import unittest

import torch
from optimizer import step_and_release


class OptimizerTest(unittest.TestCase):
    def test_updates_and_resume_match_stock_adamw(self):
        torch.manual_seed(42)
        reference = torch.nn.Sequential(
            torch.nn.Linear(7, 11), torch.nn.GELU(), torch.nn.Linear(11, 5)
        )
        candidate = copy.deepcopy(reference)

        def opt(model):
            return torch.optim.AdamW(
                [
                    {"params": model[0].parameters(), "lr": 2.5e-5},
                    {"params": model[2].parameters(), "lr": 1e-4},
                ],
                weight_decay=0.01,
                foreach=False,
            )

        a, b = opt(reference), opt(candidate)
        for iteration in range(4):
            for _ in range(16):
                x = torch.randn(1, 7)
                target = torch.tensor([iteration % 5])
                for model in (reference, candidate):
                    (torch.nn.functional.cross_entropy(model(x), target) / 16).backward()
            for model in (reference, candidate):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, foreach=False)
            a.step()
            a.zero_grad(set_to_none=True)
            step_and_release(b)
            for p, q in zip(reference.parameters(), candidate.parameters(), strict=True):
                self.assertTrue(torch.equal(p, q))
                self.assertIsNone(q.grad)
            for key, state in a.state_dict()["state"].items():
                for name, tensor in state.items():
                    self.assertTrue(torch.equal(tensor, b.state_dict()["state"][key][name]))
            if iteration == 1:
                stream = io.BytesIO()
                torch.save({"model": candidate.state_dict(), "optimizer": b.state_dict()}, stream)
                stream.seek(0)
                saved = torch.load(stream, weights_only=True)
                candidate = copy.deepcopy(reference)
                candidate.load_state_dict(saved["model"])
                b = opt(candidate)
                b.load_state_dict(saved["optimizer"])


if __name__ == "__main__":
    unittest.main()
