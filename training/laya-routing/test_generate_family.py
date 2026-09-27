import json
import tempfile
import unittest
from pathlib import Path

from generate_family import STYLES, audit_family, new_json, parse, request_for, sha


class FamilyAuthorTests(unittest.TestCase):
    def test_truncation_is_never_accepted(self):
        with self.assertRaisesRegex(ValueError, "finish"):
            parse(
                json.dumps(
                    {"choices": [{"finish_reason": "length", "message": {"content": "tekst"}}]}
                )
            )

    def test_all_five_raw_variants_and_family_identity_are_audited(self):
        policy = json.loads(Path(__file__).with_name("policy.json").read_text())
        family = {
            "family": "private-id",
            "split": "test",
            "label": "other",
            "scenario": "Nowa sprawa.",
        }
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            new_json(root / "attempt.json", {"index": 2, "family": family})
            records, messages = [], []
            for variant, style in enumerate(STYLES):
                request = root / f"{variant}.request.json"
                response = root / f"{variant}.response.txt"
                payload = request_for(family, policy, 2, variant)
                self.assertNotIn("private-id", json.dumps(payload))
                self.assertNotIn('"split"', json.dumps(payload))
                new_json(request, payload)
                text = f"Techniczny tekst testowy numer {variant}."
                response.write_text(
                    json.dumps(
                        {"choices": [{"finish_reason": "stop", "message": {"content": text}}]}
                    )
                )
                record = {
                    "http_status": 200,
                    "request_sha256": sha(request),
                    "response_sha256": sha(response),
                    "message": text,
                }
                record_path = root / f"{variant}.result.json"
                new_json(record_path, record)
                records.append({"variant": variant, "result_sha256": sha(record_path)})
                messages.append({"style": style, "message": text})
            new_json(
                root / "result.json",
                {"messages": messages, "variants": records, "parse_error": None},
            )
            self.assertEqual(len(audit_family(root, family, 2, policy)["messages"]), 5)
            with self.assertRaisesRegex(ValueError, "identity"):
                audit_family(root, {**family, "family": "wrong"}, 2, policy)
            (root / "4.response.txt").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "chain"):
                audit_family(root, family, 2, policy)


if __name__ == "__main__":
    unittest.main()
