"""Current-user explicit operations survive model omissions; synthetic catalog."""

import unittest
from unittest.mock import MagicMock

from game_discovery.ai.chat_contracts import ChatStateV2, ChatTurn, TurnPlan
from game_discovery.ai.chat_explicit import explicit_plan
from game_discovery.ai.chat_explicit import interpreted_plan
from pydantic import ValidationError
from game_discovery.ai.chat_evidence import natural_message
from game_discovery.ai.provider import AIFailure
from game_discovery.ai.rag import ConversationalRAG
from test_chat_rag import game, repository


class ExplicitChatTests(unittest.TestCase):
    def test_played_fact_and_undo_use_llm_operations_without_keyword_overrides(self):
        repo = repository([game(620, "Portal 2"), game(400, "Portal")])
        model = MagicMock()
        rag = ConversationalRAG(model, repo, None)
        model.complete.side_effect = [{"kind": "recommend", "query": "puzzle games", "exclusion_patch": [
            {"action": "add", "target": {"title": "Portal 2"}}]},
            {"message": "Inspect this puzzle adventure.", "game_ids": [400]}]
        first = rag.invoke(ChatTurn(message="I already played Portal 2. Recommend other puzzle games."))
        self.assertEqual([e.app_id for e in first.state.exclusions], [620])
        self.assertFalse(repo.chat_candidates.call_args.args[1].required_genres)
        self.assertEqual(repo.chat_candidates.call_args.args[1].excluded_ids, [620])
        model.complete.side_effect = [{"kind": "game_facts", "title_mentions": ["Portal 2"]},
                                     {"message": "Inspect the recorded facts.", "game_ids": [620]}]
        facts = rag.invoke(ChatTurn(message="Can you still tell me about Portal 2?", state=first.state))
        self.assertEqual(facts.games[0].game.app_id, 620)
        model.complete.side_effect = [{"kind": "recommend", "title_mentions": ["Portal 2"], "exclusion_patch": [
            {"action": "remove", "target": {"title": "Portal 2"}}]},
                                     {"message": "Included again in recommendations.", "game_ids": [620]}]
        undo = rag.invoke(ChatTurn(message="Include Portal 2 again in recommendations.", state=facts.state))
        self.assertFalse(undo.state.exclusions)
        self.assertEqual(undo.state.query, "puzzle games")
        self.assertEqual(undo.games[0].game.app_id, 620)
        self.assertEqual(model.complete.call_count, 6)

    def test_negation_quotes_and_questions_do_not_invent_explicit_operations(self):
        for message in ("I haven't played Portal 2.", "I have not played Portal 2.",
                        'My friend said "I played Portal 2."', "Do not include Portal 2 again.",
                        "Can I include Portal 2 again?"):
            plan = explicit_plan(ChatTurn(message=message), TurnPlan(kind="recommend", query="puzzles"))
            self.assertFalse(plan.exclusion_patch, message)
        for message in ("I've played Portal 2.", "I’ve already played Portal 2.", "I have played Portal 2."):
            self.assertEqual(explicit_plan(ChatTurn(message=message), TurnPlan(kind="recommend")).exclusion_patch[0].target.title, "Portal 2")

    def test_soft_genre_normalization_preserves_other_hard_criteria_and_explicit_genre_requests(self):
        value = TurnPlan(kind="recommend", criteria_patch=[{"scope": "conversation", "set": {
            "required_genres": ["Puzzle"], "platforms": ["linux"], "max_price_cents": 2000}}])
        soft = explicit_plan(ChatTurn(message="Puzzle games for Linux under my budget"), value)
        self.assertFalse(soft.criteria_patch[0].set.required_genres)
        self.assertEqual(soft.criteria_patch[0].set.platforms, ["linux"])
        self.assertEqual(soft.criteria_patch[0].set.max_price_cents, 2000)
        hard = explicit_plan(ChatTurn(message="Require the Puzzle genre on Linux"), value)
        self.assertEqual(hard.criteria_patch[0].set.required_genres, ["puzzle"])
        self.assertEqual(ChatStateV2().criteria.required_genres, [])

    def test_whole_catalog_absence_from_shortlist_is_rejected(self):
        with self.assertRaises(AIFailure):
            natural_message("None of the games in the provided catalog are listed with a puzzle genre.")
        self.assertEqual(natural_message("The supplied descriptions do not establish that fit."),
                         "The supplied descriptions do not establish that fit.")

    def test_explicit_undo_normalizes_clarify_with_title_before_semantic_validation_only(self):
        turn = ChatTurn(message="Include Portal 2 again in recommendations.")
        raw = {"kind": "clarify", "reply": "Included.", "title_mentions": ["Portal 2"],
               "exclusion_patch": [{"action": "remove", "target": {"title": "Portal 2"}}]}
        with self.assertRaises(ValidationError):
            TurnPlan.model_validate(raw)
        plan = interpreted_plan(turn, raw)
        self.assertEqual(plan.kind, "recommend")
        self.assertEqual(plan.exclusion_patch[0].action, "remove")
        with self.assertRaises(ValidationError):
            interpreted_plan(turn, raw | {"invented_id": 999})
        with self.assertRaises(ValidationError):
            interpreted_plan(ChatTurn(message="Tell me about a game"), raw)


if __name__ == "__main__":
    unittest.main()
