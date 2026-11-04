"""Quota-only resume preserves experimental identity and old outputs."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from game_discovery.jobs.continue_chat_evaluation import identity, same_source
from game_discovery.jobs.resume_chat_quota import AMENDMENT, prefix_digest, register_amendment, run, token_units


class QuotaAmendmentTests(unittest.TestCase):
    def test_error_interface_revision_preserves_archived_v6_and_cannot_silently_resume_it(self):
        from game_discovery.jobs.continue_chat_evaluation import JOURNALS
        path = JOURNALS["development"]
        # Portable CI may not have the owner's local journal.
        if not path.exists():
            self.skipTest("owner's retained journal not present")
        report = json.loads(path.read_text(encoding="utf-8"))
        from game_discovery.jobs.chat_evaluation import ROOT
        manifest = json.loads((ROOT / 'docs/reports/error-handling-prechange-manifest.json').read_text(encoding='utf-8'))
        for source, digest in report['serving_source_sha256'].items():
            self.assertEqual(manifest['files'][source.replace('\\', '/')], digest)
        self.assertFalse(same_source(report, identity('development')))

    def test_amendment_adds_metadata_without_rewriting_original_hashes_or_output_prefixes(self):
        amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        report = {"mode": "live_development", "records": [{"status": "failed"}],
                  "provider_attempts": [{"reservation": "granted"}], "runner_sha256": "original"}
        before = prefix_digest(report["records"], report["provider_attempts"])
        register_amendment(report, amendment, amendment["development_checkpoint_sha256_before_amendment"], "wrapper")
        register_amendment(report, amendment, "later-checkpoint", "wrapper")
        self.assertEqual(len(report["operational_amendments"]), 1)
        self.assertEqual(report["runner_sha256"], "original")
        self.assertEqual(before, prefix_digest(report["records"], report["provider_attempts"]))
        with self.assertRaises(ValueError):
            register_amendment(report, amendment, "later-checkpoint", "changed-wrapper")

    def test_stale_receipt_stops_before_configuration_database_or_inference(self):
        with patch("game_discovery.jobs.resume_chat_quota.Settings.from_environment") as settings:
            with self.assertRaisesRegex(ValueError, "fresh_utc_day"):
                run(SimpleNamespace(quota_day="2000-01-01"))
            settings.assert_not_called()

    def test_unknown_usage_remains_conservatively_charged_and_other_days_are_separate(self):
        attempts = [
            {"started_at": "2026-10-26T10:00:00Z", "reservation": "granted", "reserved_token_bound": 8000,
             "provider_usage": {"total_tokens": 2000}},
            {"started_at": "2026-10-26T11:00:00Z", "reservation": "granted", "reserved_token_bound": 6000},
            {"started_at": "2026-10-26T12:00:00Z", "reservation": "denied", "reserved_token_bound": 7000},
            {"started_at": "2026-10-27T01:00:00Z", "reservation": "pending", "reserved_token_bound": 5000},
        ]
        self.assertEqual(token_units(attempts, "2026-10-26"), 8000)
        self.assertEqual(token_units(attempts, "2026-10-27"), 5000)


if __name__ == "__main__":
    unittest.main()
