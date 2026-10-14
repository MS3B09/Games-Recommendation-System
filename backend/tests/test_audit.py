import csv
import tempfile
import unittest
from pathlib import Path

from game_discovery.jobs.audit import audit_csv, steam_app_id


class AuditTests(unittest.TestCase):
    def test_identity_rejects_lookalike_hosts_and_non_app_links(self):
        self.assertEqual(steam_app_id("https://store.steampowered.com/app/1145360/Hades/?snr=1"), 1145360)
        for url in ("https://store.steampowered.com.evil.test/app/123/",
                    "https://evil.test/app/123/", "https://store.steampowered.com/sub/123/",
                    "https://store.steampowered.com/app/0/", "not a URL"):
            self.assertIsNone(steam_app_id(url))

    def test_csv_missingness_duplicates_and_unknowns_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["", "title", "Link", "about_game", "Windows"])
                writer.writerow([0, "Hades", "https://store.steampowered.com/app/1145360/", "line one\nline two", 1])
                writer.writerow([1, "Hades", "https://store.steampowered.com/app/1145360/", "line one\nline two", 1])
                writer.writerow([2, "Music Soundtrack", "", "Unknown", "Unknown"])
                writer.writerow([3, "Broken"])
            report = audit_csv(path)
            self.assertEqual(report["rows"], 4)
            self.assertEqual(report["malformed_rows"], 1)
            self.assertEqual(report["duplicate_excess_rows"], {"id": 1, "title": 1, "row": 1})
            self.assertEqual(report["missing_by_column"]["about_game"], 1)
            self.assertEqual(report["platform_values"]["Windows"]["unknown_or_invalid"], 1)
            self.assertEqual(report["suspected_non_game_title_count"], 1)
            self.assertIsNone(report["provenance"]["collection_timestamp"])

    def test_duplicate_headers_fail_instead_of_losing_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_text("title,title\nA,B\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                audit_csv(path)
