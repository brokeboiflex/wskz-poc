import copy
import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import checkpoint
from evaluate import LABELS, audit_saved, make_request, metrics, new_json, parse_response, sha
from select_checkpoint import choose
from train import require_training_input, resume_contract


class CheckpointTests(unittest.TestCase):
    def test_interrupted_payload_keeps_previous_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = checkpoint.save(root, {"steps": 7}, pickle.dump)

            def interrupted(_value, handle):
                handle.write(b"incomplete")
                raise OSError("interrupted write")

            with self.assertRaises(OSError):
                checkpoint.save(root, {"steps": 8}, interrupted)
            self.assertEqual(checkpoint.resolve(root), previous)
            self.assertEqual(pickle.loads(previous.read_bytes()), {"steps": 7})

    def test_interrupted_pointer_keeps_previous_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = checkpoint.save(root, {"steps": 7}, pickle.dump)
            with patch("checkpoint.atomic_json", side_effect=OSError("interrupted pointer")):
                with self.assertRaises(OSError):
                    checkpoint.save(root, {"steps": 8}, pickle.dump)
            self.assertEqual(checkpoint.resolve(root), previous)

    def test_successful_pointer_retires_only_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unrelated = root / "unrelated.txt"
            unrelated.write_text("preserve")
            previous = checkpoint.save(root, {"steps": 7}, pickle.dump)
            current = checkpoint.save(root, {"steps": 8}, pickle.dump)
            self.assertEqual(checkpoint.resolve(root), current)
            self.assertFalse(previous.exists())
            self.assertEqual(unrelated.read_text(), "preserve")
            current.write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "integrity"):
                checkpoint.resolve(root)


class SelectionTests(unittest.TestCase):
    def row(self, epoch, f1, accuracy=0.9):
        return {"epoch": epoch, "metrics": {"count": 500, "macro_f1": f1, "accuracy": accuracy}}

    def test_macro_f1_precedes_accuracy(self):
        best, stop = choose([self.row(1, 0.9, 0.99), self.row(2, 0.91, 0.95)])
        self.assertEqual(best["epoch"], 2)
        self.assertFalse(stop)

    def test_tie_and_patience_use_earlier_epoch(self):
        best, stop = choose([self.row(1, 0.9), self.row(2, 0.9), self.row(3, 0.9)])
        self.assertEqual(best["epoch"], 1)
        self.assertTrue(stop)

    def test_missing_epoch_or_partial_validation_is_rejected(self):
        with self.assertRaises(ValueError):
            choose([self.row(2, 0.9)])
        row = self.row(1, 0.9)
        row["metrics"]["count"] = 499
        with self.assertRaises(ValueError):
            choose([row])


class DataAndResumeTests(unittest.TestCase):
    def test_training_rejects_test_rows_despite_correct_counts(self):
        rows = [
            {"id": str(index), "split": "train", "label": LABELS[index % 5]}
            for index in range(2000)
        ]
        require_training_input(rows)
        rows[0]["split"] = "test"
        with self.assertRaises(ValueError):
            require_training_input(rows)

    def test_resume_rejects_changed_code_and_partial_gradient_boundary(self):
        contract = {"code": "frozen", "data": "frozen"}
        state = {"contract": contract, "scheduler": None, "position": 16}
        resume_contract(state, contract)
        with self.assertRaises(ValueError):
            resume_contract(state, {**contract, "code": "changed"})
        with self.assertRaises(ValueError):
            resume_contract({**state, "position": 17}, contract)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(Path(__file__).with_name("policy.json").read_text())

    @staticmethod
    def response(label):
        return json.dumps(
            {
                "choices": [
                    {
                        "finish_reason": "tool_calls",
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "type": "function",
                                    "function": {
                                        "name": "route_message",
                                        "arguments": json.dumps({"department": label}),
                                    },
                                }
                            ],
                        },
                    }
                ]
            }
        )

    def test_wire_contains_only_message_and_public_policy(self):
        request = make_request("Jedyna treść wiadomości.", self.policy)
        self.assertEqual(
            request["messages"], [{"role": "user", "content": "Jedyna treść wiadomości."}]
        )
        self.assertNotIn("expected", json.dumps(request))
        self.assertNotIn("family", json.dumps(request))
        self.assertNotIn("rationale", json.dumps(request))
        self.assertEqual(parse_response(self.response("it")), "it")
        response = json.loads(self.response("it"))
        response["choices"][0]["message"]["tool_calls"].append(
            copy.deepcopy(response["choices"][0]["message"]["tool_calls"][0])
        )
        with self.assertRaises(ValueError):
            parse_response(json.dumps(response))

    def test_protocol_errors_are_not_dropped_from_scores(self):
        rows = [
            {"expected": label, "predicted": label, "correct": True, "family": label, "seconds": 1}
            for label in LABELS
        ]
        rows[0].update(predicted=None, correct=False)
        report = metrics(rows)
        self.assertEqual(report["accuracy"], 0.8)
        self.assertEqual(report["macro_f1"], 0.8)
        self.assertEqual(report["protocol_errors"], 1)

    def test_cluster_intervals_preserve_shared_group_uncertainty(self):
        rows = [
            {
                "expected": "it",
                "predicted": "it" if good else "other",
                "correct": good,
                "family": str(index),
                "semantic_group": "good" if good else "bad",
                "seconds": 1,
            }
            for index, good in enumerate([True] * 5 + [False] * 5)
        ]
        report = metrics(rows)
        group = report["semantic_group_cluster_bootstrap"]
        self.assertEqual(group["clusters"], 2)
        self.assertEqual(group["accuracy_percentile_95_interval"], [0.0, 1.0])
        self.assertEqual(report, metrics(rows))

    def test_evidence_audit_rejects_changed_response_and_forged_prediction(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            row = {
                "id": "example",
                "family": "one",
                "message": "Pomoc z komputerem",
                "expected": "help_desk",
            }
            request = output / "000.request.json"
            response = output / "000.response.txt"
            new_json(request, make_request(row["message"], self.policy))
            response.write_text(self.response("help_desk"))
            new_json(output / "000.attempt.json", {"id": row["id"], "request_sha256": sha(request)})
            result = {
                **row,
                "predicted": "help_desk",
                "correct": True,
                "http_status": 200,
                "request_sha256": sha(request),
                "response_sha256": sha(response),
            }
            result_path = output / "000.result.json"
            new_json(result_path, result)
            self.assertEqual(len(audit_saved(output, [row], self.policy)), 1)
            result_path.write_text(json.dumps({**result, "predicted": "it", "correct": False}))
            with self.assertRaisesRegex(ValueError, "prediction"):
                audit_saved(output, [row], self.policy)
            result_path.write_text(json.dumps(result))
            response.write_text(self.response("it"))
            with self.assertRaisesRegex(ValueError, "chain"):
                audit_saved(output, [row], self.policy)


if __name__ == "__main__":
    unittest.main()
