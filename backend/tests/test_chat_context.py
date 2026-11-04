"""Contextual follow-up regressions. Scripted LLM; no inference/accounting."""

import unittest
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from game_discovery.ai.chat_contracts import ChatStateV2, ChatTurn, TurnPlan
from game_discovery.ai.chat_evidence import GENERATE, input_bytes
from game_discovery.ai.rag import ConversationalRAG
from game_discovery.ai.provider import AIFailure
from game_discovery.catalog.contracts import ConversationMessage
from test_chat_rag import game, repository


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.repo = repository([
            game(10, "Zombie Couch", ["local-co-op", "multiplayer"], "Survive zombies together."),
            game(20, "Zombie Online", ["online-co-op", "multiplayer"], "Survive zombies online."),
            game(30, "Zombie Solo", ["single-player"], "Survive zombies alone."),
            game(40, "Zombie Unknown", [], "A zombie adventure."),
        ])
        self.model = MagicMock()
        self.rag = ConversationalRAG(self.model, self.repo, None)

    def test_reported_zombie_followup_has_transcript_titles_and_both_mode_records(self):
        self.model.complete.side_effect = [
            {"kind": "recommend", "query": "zombie survival"},
            {"message": "Try Zombie Couch or Zombie Online.", "game_ids": [10, 20]},
            {"kind": "game_facts", "reference": "last_shown", "requested_facts": ["modes"]},
            {"message": "Zombie Couch has recorded local co-op. Zombie Online lists online co-op, but local co-op is not confirmed.",
             "game_ids": [10, 20]},
        ]
        first = self.rag.invoke(ChatTurn(message="Recommend some zombie games"))
        history = [ConversationMessage(role="user", content="Recommend some zombie games"),
                   ConversationMessage(role="assistant", content=first.message)]
        with patch("game_discovery.ai.chat_explicit.interpreted_plan", side_effect=AssertionError("no keyword router")):
            second = self.rag.invoke(ChatTurn(message="Which one support Local Co Op play style ?",
                                             messages=history, state=first.state))
        interpret = self.model.complete.call_args_list[2].args[1]
        generate = self.model.complete.call_args_list[3].args[1]
        self.assertEqual(interpret["messages"], [m.model_dump() for m in history])
        self.assertEqual(interpret["references"]["shown_games"], [
            {"position": 1, "title": "Zombie Couch"}, {"position": 2, "title": "Zombie Online"}])
        self.assertEqual(generate["messages"], interpret["messages"])
        self.assertEqual([g["modes"] for g in generate["games"]], [
            ["local-co-op", "multiplayer"], ["online-co-op", "multiplayer"]])
        self.assertEqual(second.state.criteria, first.state.criteria)
        self.assertEqual(second.state.query, "zombie survival")
        self.assertEqual(self.repo.chat_candidates.call_count, 1)
        self.assertEqual(self.model.complete.call_count, 4)

    def test_fact_question_can_inspect_all_four_or_a_positional_subset(self):
        for plan, ids in [
            ({"reference": "last_shown"}, [10, 20, 30, 40]),
            ({"shown_positions": [3, 1]}, [30, 10]),
            ({"title_mentions": ["Zombie Couch", "Zombie Online", "Zombie Solo"]}, [10, 20, 30]),
            ({"reference": "last_pair"}, [10, 20]),
        ]:
            with self.subTest(plan=plan):
                self.model.complete.side_effect = [
                    {"kind": "game_facts", "requested_facts": ["modes"], **plan},
                    {"message": "Here are their recorded play modes.", "game_ids": ids}]
                state = ChatStateV2(shown_ids=[10, 20] if plan.get("reference") == "last_pair" else [10, 20, 30, 40])
                result = self.rag.invoke(ChatTurn(message="Which can we play together on one machine?", state=state))
                self.assertEqual([g.game.app_id for g in result.games], ids)
                self.assertEqual(result.state.referenced_ids, ids if len(ids) <= 2 else [])
                self.assertLessEqual(input_bytes(GENERATE, self.model.complete.call_args.args[1]), 12000)

    def test_full_older_messages_reach_both_llm_stages_when_they_fit(self):
        history = [ConversationMessage(role="user", content="My sibling prefers quiet exploration. " + "x" * 710)]
        history += [ConversationMessage(role="assistant" if i % 2 else "user", content="A short exchange.") for i in range(10)]
        self.model.complete.side_effect = [
            {"kind": "game_facts", "title_mentions": ["Zombie Couch"]},
            {"message": "The catalog describes zombie survival; quiet exploration is not confirmed.", "game_ids": [10]}]
        self.rag.invoke(ChatTurn(message="Would that suit the person I mentioned earlier?", messages=history))
        for call in self.model.complete.call_args_list:
            self.assertEqual(call.args[1]["messages"], [m.model_dump() for m in history])
            self.assertFalse(call.args[1]["context_truncated"])
            self.assertLessEqual(input_bytes(*call.args), 12000)

    def test_other_one_can_resolve_earlier_title_after_a_single_card_answer(self):
        state = ChatStateV2(shown_ids=[10], referenced_ids=[10, 20])
        history = [ConversationMessage(role="assistant", content="Try Zombie Couch and Zombie Online."),
                   ConversationMessage(role="user", content="Which supports local play?"),
                   ConversationMessage(role="assistant", content="Zombie Couch has recorded local co-op.")]
        self.model.complete.side_effect = [
            {"kind": "game_facts", "title_mentions": ["Zombie Online"], "requested_facts": ["modes"]},
            {"message": "Zombie Online has recorded online co-op.", "game_ids": [20]}]
        result = self.rag.invoke(ChatTurn(message="And the other one, over the internet?", state=state, messages=history))
        packet = self.model.complete.call_args_list[0].args[1]
        self.assertEqual(packet["references"]["recent_targets"], ["Zombie Couch", "Zombie Online"])
        self.assertEqual(packet["references"]["shown_games"], [{"position": 1, "title": "Zombie Couch"}])
        self.assertEqual(result.games[0].game.app_id, 20)
        self.assertEqual(self.model.complete.call_args.args[1]["messages"], [m.model_dump() for m in history])

    def test_validation_diagnostics_identify_stage_without_logging_private_context(self):
        self.model.complete.return_value = {"kind": "game_facts", "title_mentions": ["Zombie Couch"],
                                            "reference": "last_shown"}
        with self.assertLogs("game_discovery.ai.rag", level="WARNING") as logged, self.assertRaises(ValidationError):
            self.rag.invoke(ChatTurn(message="private user message"))
        self.assertIn("stage=interpret", logged.output[0])
        self.assertNotIn("private user message", logged.output[0])
        self.assertNotIn("Zombie Couch", logged.output[0])
        self.model.complete.side_effect = AIFailure("private provider detail")
        with self.assertLogs("game_discovery.ai.rag", level="WARNING") as logged, self.assertRaises(AIFailure):
            self.rag.invoke(ChatTurn(message="private user message"))
        self.assertIn("unexpected_error", logged.output[0])
        self.assertNotIn("private provider detail", logged.output[0])

    def test_oversized_utf8_history_is_marked_without_losing_mode_evidence(self):
        self.model.complete.side_effect = [
            {"kind": "game_facts", "reference": "last_shown", "requested_facts": ["modes"]},
            {"message": "Local co-op is recorded for Zombie Couch only.", "game_ids": [10, 20]}]
        self.rag.invoke(ChatTurn(message="Which supports couch co-op?", state=ChatStateV2(shown_ids=[10, 20]),
            messages=[ConversationMessage(role="user", content="🎮" * 1000)] * 8))
        for call in self.model.complete.call_args_list:
            self.assertTrue(call.args[1]["context_truncated"])
            self.assertLessEqual(input_bytes(*call.args), 12000)
        self.assertEqual(len(self.model.complete.call_args.args[1]["games"]), 2)

    def test_long_transcript_does_not_collapse_recommendation_evidence_to_one_game(self):
        self.model.complete.side_effect = [
            {"kind": "recommend", "query": "zombie survival"},
            {"message": "Here are some options.", "game_ids": [10, 20]}]
        self.rag.invoke(ChatTurn(message="More zombie options?", messages=[
            ConversationMessage(role="user", content="🎮" * 500)] * 12))
        packet = self.model.complete.call_args.args[1]
        self.assertEqual(len(packet["games"]), 4)
        self.assertTrue(packet["context_truncated"])
        self.assertLessEqual(input_bytes(GENERATE, packet), 12000)

    def test_invalid_or_missing_reference_never_selects_an_arbitrary_game(self):
        self.model.complete.return_value = {"kind": "game_facts", "shown_positions": [4]}
        original = ChatStateV2(shown_ids=[10, 20])
        result = self.rag.invoke(ChatTurn(message="What about the last one?", state=original))
        self.assertEqual(result.state, original)
        self.assertEqual(self.model.complete.call_count, 1)
        for value in ([0], [5], [1, 1], [True]):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                TurnPlan(kind="game_facts", shown_positions=value)

    def test_llm_can_express_preference_changes_without_required_keyword_spellings(self):
        self.model.complete.side_effect = [
            {"kind": "recommend", "query": "zombie games", "criteria_patch": [
                {"scope": "conversation", "set": {"required_genres": ["Action"]}}],
             "exclusion_patch": [{"action": "add", "target": {"title": "Zombie Solo"}}]},
            {"message": "Try this option.", "game_ids": []}]
        result = self.rag.invoke(ChatTurn(message="Keep it in Action, and leave out the one I finished yesterday."))
        self.assertEqual(result.state.criteria.required_genres, ["action"])
        self.assertEqual([e.app_id for e in result.state.exclusions], [30])


if __name__ == "__main__":
    unittest.main()
