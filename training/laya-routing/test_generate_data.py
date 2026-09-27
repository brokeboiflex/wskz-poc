import json
import tempfile
import unittest
from pathlib import Path

from generate_data import STYLES, audit_family, new_json, parse, request_for, sha


class GeneratorTests(unittest.TestCase):
    def body(self):
        return {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                style: (
                                    {
                                        "quote": "Przytoczona wypowiedz.",
                                        "message": "Biezaca sprawa.",
                                    }
                                    if style == "quotation"
                                    else {
                                        "past_problem": "Brakowalo dokumentu.",
                                        "resolution": "Dokument dostarczono.",
                                        "message": "Biezaca sprawa wymaga pomocy.",
                                    }
                                    if style == "resolved_history"
                                    else f"Przykład techniczny {index}, nie dane treningowe."
                                )
                                for index, style in enumerate(STYLES)
                            }
                        )
                    },
                }
            ]
        }

    def test_complete_json_and_styles(self):
        self.assertEqual(len(parse(json.dumps(self.body()))["messages"]), 5)

    def test_truncated_response_rejected(self):
        body = self.body()
        body["choices"][0]["finish_reason"] = "length"
        with self.assertRaises(ValueError):
            parse(json.dumps(body))

    def test_duplicates_and_label_leakage_rejected(self):
        body = self.body()
        content = json.loads(body["choices"][0]["message"]["content"])
        content["context"] = content["short"]
        body["choices"][0]["message"]["content"] = json.dumps(content)
        with self.assertRaises(ValueError):
            parse(json.dumps(body))
        content["context"] = "Wybrany dział: human_resources"
        body["choices"][0]["message"]["content"] = json.dumps(content)
        with self.assertRaises(ValueError):
            parse(json.dumps(body))

    def test_repeated_quotation_and_missing_resolution_rejected(self):
        body = self.body()
        payload = json.loads(body["choices"][0]["message"]["content"])
        payload["quotation"]["message"] = payload["quotation"]["quote"]
        body["choices"][0]["message"]["content"] = json.dumps(payload)
        with self.assertRaisesRegex(ValueError, "identical"):
            parse(json.dumps(body))
        payload["quotation"]["message"] = "Odrębna prośba."
        del payload["resolved_history"]["resolution"]
        body["choices"][0]["message"]["content"] = json.dumps(payload)
        with self.assertRaisesRegex(ValueError, "History"):
            parse(json.dumps(body))

    def test_authoring_request_does_not_expose_split_or_family_id(self):
        policy = json.loads(Path(__file__).with_name("policy.json").read_text())
        family = {
            "family": "hidden-family-id",
            "split": "test",
            "label": "help_desk",
            "scenario": "Wyłącznie opis nowego scenariusza.",
        }
        request = request_for(family, policy, 1)
        text = json.dumps(request)
        self.assertNotIn("hidden-family-id", text)
        self.assertNotIn('"split"', text)
        self.assertIn(family["scenario"], request["messages"][1]["content"])

    def test_evidence_chain_rejects_wrong_family_and_changed_messages(self):
        policy = json.loads(Path(__file__).with_name("policy.json").read_text())
        family = {"family": "unit", "label": "help_desk", "scenario": "Kontrola techniczna."}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            new_json(root / "request.json", request_for(family, policy, 0))
            (root / "response.txt").write_text(json.dumps(self.body()))
            new_json(root / "attempt.json", {"index": 0, "family": family})
            result = {
                "http_status": 200,
                "request_sha256": sha(root / "request.json"),
                "response_sha256": sha(root / "response.txt"),
                **parse(json.dumps(self.body())),
            }
            new_json(root / "result.json", result)
            audit_family(root, family, 0, policy)
            with self.assertRaisesRegex(ValueError, "chain"):
                audit_family(root, {**family, "family": "wrong"}, 0, policy)
            result["messages"][0]["message"] = "Niedozwolona zmiana zapisanego wyniku."
            (root / "result.json").write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError, "raw generation"):
                audit_family(root, family, 0, policy)


if __name__ == "__main__":
    unittest.main()
