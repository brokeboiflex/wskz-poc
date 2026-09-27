import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from data_guard import frozen_exclusions, validate


def row(identifier="a", split="train", family="one", text="Nowy odrębny tekst."):
    return {"id": identifier, "split": split, "family": family, "message": text, "label": "other"}


class DataGuardTest(unittest.TestCase):
    def test_changed_exclusion_corpus_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "empty.json"
            path.write_text("[]")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                frozen_exclusions(path, path)
            benchmark = (
                Path(__file__).resolve().parents[2] / "verification/benchmark/cases-500.json"
            )
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                frozen_exclusions(benchmark, path)

    def test_same_family_cannot_cross_split(self):
        report = validate([row(), row("b", "test", text="Inna wypowiedź.")], [], complete=False)
        self.assertIn("family_split", {e["kind"] for e in report["errors"]})

    def test_benchmark_copy_rejected_even_if_id_changed(self):
        report = validate(
            [row(text="Proszę: NAPRAWIĆ urządzenie!")],
            [{"message": "proszę naprawić urządzenie"}],
            complete=False,
        )
        self.assertFalse(report["passed"])

    def test_cross_split_paraphrase_with_shared_fragments_flagged(self):
        text = (
            "Jeden dwa trzy cztery pięć sześć siedem osiem dziewięć dziesięć jedenaście dwanaście"
        )
        report = validate(
            [row(text=text), row("b", "test", "two", text + " dopisek")], [], complete=False
        )
        self.assertFalse(report["passed"])

    def test_short_exact_copy_rejected(self):
        self.assertFalse(
            validate([row(text="Pomocy!")], [{"message": "pomocy"}], complete=False)["passed"]
        )

    def test_duplicate_text_within_training_rejected(self):
        self.assertFalse(validate([row(), row("b", family="two")], [], complete=False)["passed"])

    def test_complete_corpus_cannot_be_faked_by_preflight(self):
        report = validate([row()], [])
        self.assertFalse(report["passed"])
        self.assertTrue(report["complete_corpus_required"])

    def test_invalid_label_rejected(self):
        record = row()
        record["label"] = "invented_department"
        self.assertFalse(validate([record], [], complete=False)["passed"])

    def test_lexical_pass_does_not_claim_semantic_independence(self):
        report = validate([row()], [], complete=False)
        self.assertTrue(report["passed"])
        self.assertTrue(report["semantic_review_required"])


if __name__ == "__main__":
    unittest.main()
