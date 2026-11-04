"""Human review must stay pending without actual complete owner judgments."""

import unittest

from game_discovery.jobs.chat_evaluation import METHODS
from game_discovery.jobs.prepare_chat_review import human_summary, label


class HumanReviewTests(unittest.TestCase):
    def test_labels_are_stable_and_methods_masked_differently(self):
        self.assertNotEqual(label("M01", METHODS[0]), label("M01", METHODS[1]))
        self.assertEqual(label("M01", METHODS[0]), label("M01", METHODS[0]))

    def test_empty_partial_or_unconfirmed_review_cannot_pass(self):
        for review in ({"entries": []}, {"entries": [], "owner_confirmation": "owner_reviewed"}):
            self.assertEqual(human_summary(review, {})["human_quality_gate"], "pending")

    def test_complete_synthetic_review_detects_regression_and_rejects_invalid_counts(self):
        entries, keys = [], {}
        for turn in range(31):
            for method in METHODS:
                key = f"synthetic:{turn}:{method}"
                keys[key] = method
                entries.append({"review_id": key, "case_id": "synthetic", "turn": turn, "split": "held_out",
                                "relevance": 1 if method == "proposed" else 2,
                                "factual_claims_total": 1, "unsupported_prose_claims": 0, "false_absence_claims": 0})
        review = {"entries": entries, "owner_confirmation": "owner_reviewed"}
        self.assertEqual(human_summary(review, keys)["human_quality_gate"], "fail")
        entries[0]["unsupported_prose_claims"] = 2
        with self.assertRaises(ValueError):
            human_summary(review, keys)
        entries[0]["unsupported_prose_claims"] = 0
        entries[0]["false_absence_claims"] = 1
        with self.assertRaises(ValueError):
            human_summary(review, keys)


if __name__ == "__main__":
    unittest.main()
