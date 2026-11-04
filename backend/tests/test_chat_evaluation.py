"""R4 evaluator validity and approval-accounting regressions; no network/quota."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from game_discovery.ai.chat_contracts import ChatResult, ChatStateV2, ChatTurn, TurnPlan
from game_discovery.ai.chat_evidence import INTERPRET
from game_discovery.ai.provider import AIFailure
from game_discovery.ai.rag import TurnFrame
from game_discovery.catalog.contracts import Filters, Recommendation
from game_discovery.jobs.chat_evaluation import (
    PILOT_CALLS, PILOT_TOKENS, POLICY, OracleModel, RecordedRAG, SemanticBaseline, load_cases, metrics, oracle_plan,
)
from game_discovery.jobs.evaluate_chat import CappedBudget, JournalModel, header, save, summarize
from game_discovery.retrieval.contracts import RankedCandidate, RetrievalOutcome, RetrievalResult
from test_chat_rag import game, repository


class EvaluationTests(unittest.TestCase):
    def test_frozen_inventory_and_actual_turn_budget(self):
        cases = load_cases()
        real = [c for c in cases if c["source"] == "real_catalog"]
        self.assertEqual((len(cases), sum(len(c["turns"]) for c in cases)), (40, 53))
        self.assertEqual((len(real), sum(len(c["turns"]) for c in real)), (33, 44))
        pilot = next(c for c in cases if c["id"] == "M01")
        self.assertEqual(len(pilot["turns"]) * 2 * 2, PILOT_CALLS)
        self.assertEqual(PILOT_CALLS * (12000 + 1280), PILOT_TOKENS)

    def test_oracle_annotations_validate_without_expected_ids_in_semantic_query(self):
        cases = load_cases()
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        games = {i: game(i, f"Fixture title {i}") for c in cases for t in c["turns"]
                 for i in t["expect"].get("target_ids", []) + t["expect"].get("excluded_ids", []) + t["expect"].get("removed_excluded_ids", [])}
        for case in cases:
            if case["source"] != "real_catalog":
                continue
            for index, turn in enumerate(case["turns"]):
                plan = oracle_plan(case, index, games, policy)
                if plan.kind == "recommend":
                    self.assertEqual(plan.query, turn["user"])
                self.assertNotIn("target_ids", plan.model_dump())

    def test_oracle_is_explicitly_scripted_not_live_generation(self):
        model = OracleModel(TurnPlan(kind="recommend", query="puzzles"))
        self.assertEqual(model.complete(INTERPRET, {})["kind"], "recommend")
        value = model.complete("generate", {"games": [{"app_id": i} for i in range(10, 18)]})
        self.assertEqual(value["game_ids"], [10, 11, 12, 13])
        self.assertIn("not a generated answer-quality sample", value["message"])

    def test_budget_denial_is_recorded_without_transport_and_not_refunded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.json"
            report = header("pilot")
            report["provider_attempts"] = [{"reserved_token_bound": 4000}]
            delegate = MagicMock()
            delegate.reserve.return_value = False
            budget = CappedBudget(delegate, report, path)
            self.assertFalse(budget.reserve(4000))
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["provider_attempts"][0]["reservation"], "denied")
            self.assertEqual(saved["actual_quota_reservations"], 0)

    def test_journal_call_cap_fails_before_provider_or_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            report = header("pilot")
            report["provider_attempts"] = [{"reserved_token_bound": 1}] * PILOT_CALLS
            model = MagicMock()
            journal = JournalModel(model, report, Path(directory) / "pilot.json")
            with self.assertRaisesRegex(AIFailure, "evaluation_approval_exhausted"):
                journal.complete(INTERPRET, {})
            model.complete.assert_not_called()

    def test_journal_token_cap_fails_before_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            report = header("pilot")
            report["provider_attempts"] = [{"reserved_token_bound": PILOT_TOKENS - 1}]
            model = MagicMock()
            with self.assertRaisesRegex(AIFailure, "evaluation_approval_exhausted"):
                JournalModel(model, report, Path(directory) / "pilot.json").complete(INTERPRET, {})
            model.complete.assert_not_called()

    def test_retest_inherited_attempts_count_against_original_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            report = header("retest")
            report["provider_attempts"] = [{"reserved_token_bound": 4212, "reservation": "granted", "revision": "initial"}] * 6
            path = Path(directory) / "revision.json"
            model = MagicMock()
            model.complete.return_value = {"kind": "social", "reply": "Hello"}
            journal = JournalModel(model, report, path)
            for _ in range(6):
                journal.complete(INTERPRET, {"message": "Hello"})
            with self.assertRaisesRegex(AIFailure, "evaluation_approval_exhausted"):
                journal.complete(INTERPRET, {"message": "one more"})
            self.assertEqual(model.complete.call_count, 6)
            self.assertEqual(len(report["provider_attempts"]), 12)

    def test_started_attempt_is_durable_before_provider_even_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            report = header("pilot")
            path = Path(directory) / "pilot.json"
            model = MagicMock()
            def failed(*args):
                saved = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(saved["provider_attempts"][0]["status"], "started")
                self.assertGreater(saved["provider_attempts"][0]["reserved_token_bound"], 1280)
                raise AIFailure("ai_unavailable_or_invalid")
            model.complete.side_effect = failed
            with self.assertRaises(AIFailure):
                JournalModel(model, report, path).complete(INTERPRET, {"message": "hello"})
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["provider_attempts"][0]["status"], "failed")
            self.assertEqual(model.complete.call_count, 1)

    def test_atomic_save_preserves_one_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.json"
            save(path, {"attempts": [1]})
            save(path, {"attempts": [1, 2]})
            self.assertEqual(json.loads(path.read_text())["attempts"], [1, 2])
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_completed_live_ledger_is_a_noop_even_after_source_changes(self):
        from game_discovery.jobs.evaluate_chat import run
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.json"
            save(path, {"status": "completed_with_failures", "provider_attempts": [{"status": "failed"}]})
            with patch("game_discovery.jobs.evaluate_chat.PILOT_PATH", path), patch(
                    "game_discovery.jobs.evaluate_chat.create_runtime_engine") as engine:
                run(SimpleNamespace(mode="pilot", output=None, split="all"))
                engine.assert_not_called()
            self.assertEqual(json.loads(path.read_text())["provider_attempts"], [{"status": "failed"}])

    def test_requested_constraints_are_checked_independently_of_interpreter(self):
        fixture = game(10, modes=["single-player"])
        result = ChatResult(message="fixture", games=[Recommendation(game=fixture, reasons=[], tradeoffs=[])], state=ChatStateV2())
        frame = TurnFrame(ChatTurn(message="multiplayer"), filters=Filters())
        score = metrics({"kind": "recommend", "constraints": {"required_modes": ["multiplayer"]}}, result, frame, TurnPlan(kind="recommend"))
        self.assertEqual(score["hard_card_violation_ids"], [10])
        self.assertFalse(score["state_checks"]["effective_required_modes"])
        self.assertIsNone(score["human_relevance"])

    def test_seed_hits_do_not_become_recall_or_human_quality(self):
        fixture = game(10)
        retrieval = RetrievalResult("fixture", RetrievalOutcome(kind="found", evidence_ids=[10]),
                                    candidates=(RankedCandidate(fixture, 1),))
        frame = TurnFrame(ChatTurn(message="puzzles"), retrieval=retrieval)
        result = ChatResult(message="fixture", state=ChatStateV2(), retrieval=retrieval.outcome)
        score = metrics({"target_ids": [10], "anchor_ids": [10]}, result, frame, TurnPlan(kind="recommend"))
        self.assertTrue(score["target_hit_at_5"])
        self.assertTrue(score["anchor_seed_hit_in_evidence"])
        self.assertIsNone(score["recall_at_8"])
        self.assertIsNone(score["unsupported_prose_claims"])

    def test_failures_remain_in_denominator_of_execution_summary(self):
        result = summarize({"records": [{"method": "proposed", "status": "failed"}]})
        self.assertEqual(result["proposed"]["failed_turns"], 1)
        self.assertEqual(result["proposed"]["successful_turns"], 0)
        self.assertIsNone(result["proposed"]["target_hit_at_5"]["rate"])

    def test_baseline_fact_lookup_does_not_use_title_or_lexical_methods(self):
        repo = MagicMock()
        encoder = MagicMock(catalog_version="fixture", return_value=[0.1] * 384)
        connection = MagicMock()
        connection.execute.return_value = [(game(10).model_dump(mode="json"), .9)]
        repo.snapshot.return_value.__enter__.return_value = (connection, "fixture")
        baseline = SemanticBaseline(MagicMock(), repo, encoder)
        frame = TurnFrame(ChatTurn(message="Does spiderman exist?"),
                          plan=TurnPlan(kind="title_lookup", title_mentions=["spiderman"]), state=ChatStateV2())
        baseline.retrieve(frame)
        encoder.assert_called_once_with("Does spiderman exist?")
        repo.chat_title.assert_not_called()
        repo.chat_candidates.assert_not_called()
        sql = str(connection.execute.call_args.args[0])
        self.assertIn("limit 5", sql)
        self.assertNotIn("tsquery", sql)
        self.assertFalse(frame.retrieval.outcome.title_search_complete)

    def test_pilot_cannot_choose_a_fresh_ledger_or_full_set(self):
        with patch("sys.argv", ["evaluate_chat", "pilot", "--output", "fresh.json"]):
            from game_discovery.jobs.evaluate_chat import main
            with self.assertRaises(SystemExit):
                main()

    def test_six_live_style_selections_fail_atomically_without_hidden_retry(self):
        repo = repository([game(i, f"Fixture {i}", ["multiplayer"]) for i in range(10, 16)])
        model = MagicMock()
        model.complete.side_effect = [
            {"kind": "recommend", "query": "multiplayer games", "criteria_patch": [
                {"scope": "conversation", "set": {"required_modes": ["multiplayer"]}}]},
            {"message": "Six supplied games.", "game_ids": list(range(10, 16)), "claims": {"claims": []}}]
        rag = RecordedRAG(model, repo, None)
        state = ChatStateV2()
        with self.assertRaises(ValidationError) as raised:
            rag.invoke(ChatTurn(message="More multiplayer games", state=state))
        self.assertEqual(raised.exception.errors()[0]["loc"], ("game_ids",))
        self.assertEqual(raised.exception.errors()[0]["type"], "too_long")
        self.assertEqual(state, ChatStateV2())
        self.assertEqual(model.complete.call_count, 2)
        self.assertIsNotNone(rag.last_frame.packet)

    def test_free_to_play_does_not_make_missing_price_claimable(self):
        fixture = game(10)
        fixture.free_to_play = True
        fixture.price = None
        fixture.evidence = [e for e in fixture.evidence if e.field != "price_cents"]
        model = MagicMock()
        model.complete.side_effect = [{"kind": "recommend", "query": "exploration"},
            {"message": "Inspect the dated card.", "game_ids": [10], "claims": {"claims": [
                {"app_id": 10, "evidence_id": "10:price_cents", "field": "price_cents", "value": 0}]}}]
        with self.assertRaisesRegex(AIFailure, "chat_invented_selection"):
            RecordedRAG(model, repository([fixture]), None).invoke(ChatTurn(message="exploration"))
        self.assertEqual(model.complete.call_count, 2)


if __name__ == "__main__":
    unittest.main()
