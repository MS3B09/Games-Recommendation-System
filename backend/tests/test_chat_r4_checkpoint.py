"""R4 multi-day checkpoint and independent scoring regressions, no inference."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from game_discovery.ai.chat_contracts import ChatResult, ChatStateV2, ChatTurn, TurnPlan
from game_discovery.ai.rag import TurnFrame
from game_discovery.catalog.contracts import Recommendation
from game_discovery.jobs.chat_evaluation import metrics
from game_discovery.jobs.continue_chat_evaluation import day_remaining, identity, run, same_source
from test_chat_rag import game


class R4CheckpointTests(unittest.TestCase):
    def test_daily_receipt_counts_only_subsequent_pending_or_granted_reservations(self):
        report = {"provider_attempts": [{"reservation": "granted", "reserved_token_bound": 9000},
            {"reservation": "granted", "reserved_token_bound": 4000},
            {"reservation": "pending", "reserved_token_bound": 5000},
            {"reservation": "denied", "reserved_token_bound": 6000}]}
        receipt = {"attempt_offset": 1, "calls": 12, "reserved_tokens": 92813}
        self.assertEqual(day_remaining(report, receipt, 50, 500000), (36, 398187))

    def test_comparison_sources_match_across_splits_but_prompt_changes_block_resume(self):
        development, held = identity("development"), identity("held_out")
        self.assertTrue(same_source(development, held))
        held["serving_source_sha256"] = {"changed": "hash"}
        self.assertFalse(same_source(development, held))

    def test_stale_quota_receipt_fails_before_engine_or_provider(self):
        with patch("game_discovery.jobs.continue_chat_evaluation.create_runtime_engine") as engine:
            with self.assertRaisesRegex(ValueError, "fresh_utc_day_quota_preflight_required"):
                run(SimpleNamespace(quota_day="2001-01-01"))
            engine.assert_not_called()

    def test_wrong_interpreted_kind_does_not_disable_expected_card_constraint_checks(self):
        single = game(modes=["single-player"])
        result = ChatResult(message="Fixture", state=ChatStateV2(), games=[
            Recommendation(game=single, reasons=[], tradeoffs=[])])
        score = metrics({"kind": "recommend", "constraints": {"required_modes": ["multiplayer"]}},
                        result, TurnFrame(ChatTurn(message="multiplayer games")),
                        TurnPlan(kind="game_facts", title_mentions=["Fixture"]))
        self.assertEqual(score["hard_card_violation_ids"], [10])
        self.assertFalse(score["state_checks"]["effective_required_modes"])

    def test_generic_clarification_is_not_scored_as_a_completed_recommendation(self):
        result = ChatResult(message="Which games do you mean?", state=ChatStateV2())
        score = metrics({"kind": "recommend"}, result, TurnFrame(ChatTurn(message="More options")),
                        TurnPlan(kind="recommend", reference="last_pair"))
        self.assertFalse(score["state_checks"]["recommendation_retrieval_performed"])


if __name__ == "__main__":
    unittest.main()
