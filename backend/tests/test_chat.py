import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from game_discovery.ai.chat import ChatRequest, ChatState, respond
from game_discovery.ai.provider import AIFailure, GroqAssistant
from game_discovery.api.main import create_app
from game_discovery.catalog.contracts import Filters
from game_discovery.catalog.discovery import recommendation
from game_discovery.catalog.repository import GamePage, ResolvedGames
from game_discovery.core.settings import Settings
from test_catalog_m2 import fixture
from test_chat_rag import repository


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.repo = repository()
        self.game = fixture()
        self.result = recommendation(self.game, [], Filters())
        self.repo.discover.return_value = ("fixture", [self.result])
        self.repo.resolve.return_value = ResolvedGames(catalog_version="fixture", items=[self.game], unknown_ids=[])
        self.repo.search.return_value = GamePage(catalog_version="fixture", items=[self.game], total=1, offset=0)
        self.model = MagicMock()

    def outputs(self, intent=None, answer=None):
        self.model.complete.side_effect = [intent or {"kind": "recommend", "query": "combat"},
            answer or {"message": "Here is a catalog option to explore. Check its evidence for the details.", "game_ids": [10]}]

    def test_main_inputs_are_rejected_and_no_main_defaults_enter_chat(self):
        self.outputs()
        with TestClient(create_app(Settings(), repository=self.repo, chat_model=self.model)) as client:
            for field, value in (("favorite_ids", [10]), ("preferences", {"max_price_cents": 2000}), ("feedback", [])):
                self.assertEqual(client.post("/api/v1/chat", json={"message": "combat", field: value}).status_code, 422)
            reply = client.post("/api/v1/chat", json={"message": "combat"})
        self.assertEqual(reply.status_code, 200)
        filters = self.repo.chat_candidates.call_args.args[1]
        self.assertIsNone(filters.max_price_cents)
        self.assertEqual(filters.platforms, [])
        self.repo.discover.assert_not_called()
        self.assertEqual(reply.json()["games"][0]["game"]["price"]["amount_cents"], 1999)

    def test_different_main_discoveries_do_not_change_chat_inputs_or_prompts(self):
        observed = []
        for main in ({"favorite_ids": [10], "filters": {"max_price_cents": 1, "platforms": ["linux"]}},
                     {"favorite_ids": [], "filters": {"max_price_cents": 8000, "platforms": ["windows"]}}):
            self.outputs()
            self.model.complete.reset_mock()
            with TestClient(create_app(Settings(), repository=self.repo, chat_model=self.model)) as client:
                self.assertEqual(client.post("/api/v1/discover", json=main).status_code, 200)
                self.assertEqual(client.post("/api/v1/chat", json={"message": "combat"}).status_code, 200)
            observed.append((self.repo.chat_candidates.call_args.args[0],
                self.repo.chat_candidates.call_args.args[1].model_dump(),
                self.model.complete.call_args_list[0].args))
        self.assertEqual(observed[0], observed[1])

    def test_greeting_or_clarification_uses_one_call_without_recommendations(self):
        self.model.complete.return_value = {"kind": "clarify", "reply": "Would you prefer solo play or co-op?"}
        reply = respond(ChatRequest(message="Something different"), self.model, self.repo, None, "test")
        self.assertFalse(reply.games)
        self.assertIn("co-op", reply.message)
        self.repo.discover.assert_not_called()
        self.assertEqual(self.model.complete.call_count, 1)

    def test_chat_limits_override_only_chat_state_and_never_relax_on_no_match(self):
        self.outputs({"kind": "recommend", "reset_preferences": True, "query": "co-op", "criteria_patch": [
            {"scope": "conversation", "set": {"max_price_cents": 4000, "platforms": ["linux"]}}]})
        reply = respond(ChatRequest(message="Start over: Linux under forty", state=ChatState(criteria=Filters(max_price_cents=2000))),
                        self.model, self.repo, None, "test")
        self.assertEqual(reply.state.criteria.max_price_cents, 4000)
        self.assertEqual(reply.state.criteria.platforms, ["linux"])
        self.assertFalse(reply.games)
        self.assertIn("haven't relaxed", reply.message)
        self.assertEqual(self.model.complete.call_count, 1)

    def test_chat_rejection_is_structured_retained_and_not_feedback(self):
        self.outputs({"kind": "recommend", "query": "more combat", "exclusion_patch": [
            {"action": "add", "target": {"shown_position": 1}}]})
        reply = respond(ChatRequest(message="Already played that", state=ChatState(shown_ids=[10])), self.model, self.repo, None, "test")
        self.assertEqual(reply.state.excluded_ids, [10])
        self.assertEqual(self.repo.chat_candidates.call_args.args[1].excluded_ids, [10])
        self.repo.discover.assert_not_called()
        self.assertFalse(reply.games)

    def test_named_played_title_is_resolved_from_catalog(self):
        self.outputs({"kind": "recommend", "query": "other combat games", "exclusion_patch": [
            {"action": "add", "target": {"title": "Fixture"}}]})
        reply = respond(ChatRequest(message="Played Fixture"), self.model, self.repo, None, "test")
        self.assertEqual(reply.state.excluded_ids, [10])
        self.repo.chat_title.assert_called_once_with("Fixture", None)

    def test_unknown_title_requests_clarification_without_guessing_id(self):
        self.outputs({"kind": "recommend", "exclusion_patch": [
            {"action": "add", "target": {"title": "Different title"}}]})
        reply = respond(ChatRequest(message="Played Different title"), self.model, self.repo, None, "test")
        self.assertIn("this catalog", reply.message)
        self.assertFalse(reply.state.excluded_ids)
        self.repo.discover.assert_not_called()

    def test_provider_cannot_fabricate_exclusion_ids_or_games(self):
        for intent, answer in (({"kind": "recommend", "exclude_ids": [999]}, None),
                               (None, {"message": "Try this.", "game_ids": [999]})):
            self.outputs(intent, answer)
            with self.subTest(intent=intent), self.assertRaises((AIFailure, ValueError)):
                respond(ChatRequest(message="combat"), self.model, self.repo, None, "test")

    def test_unsupported_claim_fails_instead_of_reaching_user(self):
        self.outputs(answer={"message": "Explore this.", "game_ids": [10], "claims": {"claims": [
            {"app_id": 10, "evidence_id": "invented", "field": "description", "value": "Guaranteed relaxing"}]}})
        with self.assertRaises((AIFailure, ValueError)):
            respond(ChatRequest(message="relaxing"), self.model, self.repo, None, "test")

    def test_specific_game_facts_bypass_recommendation_conditions_and_note_mismatch(self):
        self.outputs({"kind": "game_facts", "title_mentions": ["Fixture"], "evaluate_prior_requirements": True,
            "criteria_patch": [{"scope": "turn", "set": {"max_price_cents": 1000}}]})
        reply = respond(ChatRequest(message="What about Fixture under ten?"), self.model, self.repo, None, "test")
        self.assertEqual(reply.games[0].game.app_id, 10)
        self.assertIn("do not satisfy", reply.message)
        self.repo.discover.assert_not_called()

    def test_unconfigured_or_failed_chat_does_not_disable_main_discovery(self):
        for model in (None, MagicMock()):
            if model is not None:
                model.complete.side_effect = TimeoutError("should not leak secrets")
            with TestClient(create_app(Settings(), repository=self.repo, chat_model=model)) as client:
                if model is not None:
                    model.complete.side_effect = AIFailure("private provider detail")
                reply = client.post("/api/v1/chat", json={"message": "hello"})
                self.assertEqual(reply.status_code, 503 if model is None else 500)
                self.assertNotIn("private", reply.text)
                self.assertEqual(client.post("/api/v1/discover", json={}).status_code, 200)

    def test_chat_quota_failure_makes_no_provider_call(self):
        budget = MagicMock()
        budget.reserve.return_value = False
        model = GroqAssistant(Settings(), budget)
        with patch("game_discovery.ai.provider.urlopen") as network, TestClient(create_app(Settings(), repository=self.repo, chat_model=model)) as client:
            self.assertEqual(client.post("/api/v1/chat", json={"message": "hello"}).status_code, 503)
            network.assert_not_called()

    def test_chat_request_bounds_and_rate_limit(self):
        self.model.complete.return_value = {"kind": "social", "reply": "Hello! What would you like to play?"}
        with TestClient(create_app(Settings(), repository=self.repo, chat_model=self.model)) as client:
            for body in ({"message": " "}, {"message": "x" * 2001}, {"message": "hello", "messages": [{"role": "user", "content": "x" * 2000}] * 7}):
                self.assertEqual(client.post("/api/v1/chat", json=body).status_code, 422)
            self.assertEqual(client.post("/api/v1/chat", json={"message": "hello"}).status_code, 200)
            limited = client.post("/api/v1/chat", json={"message": "again"})
            self.assertEqual(limited.status_code, 429)
            self.assertEqual(limited.headers["retry-after"], "30")


if __name__ == "__main__":
    unittest.main()
