"""R4 next-day diagnostics and cheap timing regressions; no inference/quota."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from game_discovery.ai.chat_contracts import ChatResult, ChatStateV2
from game_discovery.ai.provider import AIFailure, GroqAssistant
from game_discovery.core.settings import Settings
from game_discovery.jobs.evaluate_chat import JOURNAL_INTERVALS, header, record_turn, save


class R4ResumeTests(unittest.TestCase):
    def test_safe_transport_category_is_recorded_without_retry_or_private_error_text(self):
        model = GroqAssistant(Settings(), MagicMock())
        with patch("game_discovery.ai.provider.urlopen", side_effect=TimeoutError("PRIVATE_SECRET")) as network:
            with self.assertRaisesRegex(AIFailure, "ai_timeout") as raised:
                model.complete("Return JSON", {})
        self.assertEqual(model.last_error_type, "TimeoutError")
        self.assertNotIn("PRIVATE_SECRET", str(raised.exception))
        self.assertEqual(network.call_count, 1)

    def test_journal_intervals_are_request_local_and_restore_after_turn(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            report = header("offline")
            report["catalog_version"] = "fixture"
            def invoke(turn, observer):
                save(path, report)
                return ChatResult(message="Hello", state=ChatStateV2())
            rag = SimpleNamespace(invoke=invoke, last_frame=None)
            case = {"id": "fixture", "split": "development", "turns": [{"user": "Hello", "expect": {}}]}
            record_turn(case, 0, "proposed", rag, None, ChatStateV2(), [], SimpleNamespace(samples=[]), report, path)
            row = report["records"][0]
            self.assertEqual(row["status"], "ok")
            self.assertGreater(row["journal_write_ms"], 0)
            self.assertLessEqual(row["serving_equivalent_domain_ms"], row["duration_ms"])
            self.assertAlmostEqual(row["duration_ms"], row["serving_equivalent_domain_ms"] + row["journal_write_ms"], places=2)
            self.assertIsNone(JOURNAL_INTERVALS.get())
            self.assertEqual(json.loads(path.read_text())["records"][0]["journal_write_ms"], row["journal_write_ms"])


if __name__ == "__main__":
    unittest.main()
