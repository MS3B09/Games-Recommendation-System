"""R3 public version boundary; domain semantics are covered separately in R2."""

import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from game_discovery.ai.chat import ChatRequest, ChatState, ChatStateV2Wire, respond
from game_discovery.ai.chat_contracts import ChatStateV2
from game_discovery.ai.provider import AIFailure
from game_discovery.api.main import create_app
from game_discovery.core.settings import Settings
from test_chat_rag import repository


class ChatR3Tests(unittest.TestCase):
    def setUp(self):
        self.repo = repository()
        self.model = MagicMock()
        self.model.complete.return_value = {"kind": "social", "reply": "Hello!"}

    def test_explicit_v2_roundtrip_is_neutral_and_increments_once(self):
        with TestClient(create_app(Settings(), repository=self.repo, chat_model=self.model)) as client:
            response = client.post("/api/v1/chat", json={"message": "hello", "state": {"version": 2}})
        self.assertEqual(response.status_code, 200)
        state = ChatStateV2Wire.model_validate(response.json()["state"])
        self.assertEqual(state.user_turn, 1)
        self.assertIsNone(state.criteria.min_price_cents)
        self.assertIsNone(state.criteria.max_price_cents)
        self.assertEqual(state.criteria.platforms, [])
        self.assertEqual(state.provenance, {})

    def test_omitted_state_and_legacy_request_return_legacy_shape(self):
        for body in ({"message": "hello"}, {"message": "hello", "state": {"query": "prior combat"}}):
            request = ChatRequest.model_validate(body)
            result = respond(request, self.model, self.repo, None, "test")
            self.assertIsInstance(result.state, ChatState)
            self.assertNotIn("version", result.model_dump()["state"])

    def test_future_missing_discriminator_and_bad_provenance_fail_before_provider(self):
        invalid = [
            {"version": 3}, {"version": "2"}, {"version": 2.0}, {"version": True},
            {"user_turn": 1}, {"version": None},
            {"version": 2, "criteria": {"required_modes": ["multiplayer"]}},
            {"version": 2, "user_turn": 1, "query": "combat"},
            {"version": 2, "user_turn": 1, "provenance": {"free_only": {"user_turn": 2}}},
            {"version": 2, "criteria": {"excluded_ids": [10]}},
            {"version": 2, "favorite_ids": [10]}, {"version": 2, "shown_ids": [10, 10]},
        ]
        with TestClient(create_app(Settings(), repository=self.repo, chat_model=self.model)) as client:
            for state in invalid:
                with self.subTest(state=state):
                    self.assertEqual(client.post("/api/v1/chat", json={"message": "hello", "state": state}).status_code, 422)
        self.model.complete.assert_not_called()

    def test_v2_retains_criteria_and_origins_across_trimmed_fact_turn(self):
        state = {"version": 2, "user_turn": 42, "criteria": {"required_modes": ["multiplayer"]},
            "provenance": {"required_modes": {"user_turn": 1}}, "query": "combat", "query_origin": {"user_turn": 1}}
        self.model.complete.side_effect = [
            {"kind": "game_facts", "title_mentions": ["Fixture"], "evaluate_prior_requirements": True},
            {"message": "This catalog records single-player support.", "game_ids": [10]}]
        with TestClient(create_app(Settings(), repository=self.repo, chat_model=self.model)) as client:
            response = client.post("/api/v1/chat", json={"message": "Would Fixture meet those requirements?", "state": state})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["games"][0]["game"]["app_id"], 10)
        self.assertEqual(result["state"]["user_turn"], 43)
        self.assertEqual(result["state"]["criteria"]["required_modes"], ["multiplayer"])
        self.assertEqual(result["state"]["provenance"]["required_modes"]["user_turn"], 1)
        self.assertIn("does not meet the required multiplayer", result["message"])
        self.assertEqual(result["state"]["referenced_ids"], [10])

    def test_retry_from_same_v2_snapshot_does_not_double_advance(self):
        request = ChatRequest(message="hello", state=ChatStateV2Wire(version=2, user_turn=5))
        first = respond(request, self.model, self.repo, None, "first")
        second = respond(request, self.model, self.repo, None, "retry")
        self.assertEqual(first.state, second.state)
        self.assertEqual(first.state.user_turn, 6)
        self.assertEqual(request.state.user_turn, 5)

    def test_provider_error_does_not_commit_client_state(self):
        request = ChatRequest(message="hello", state=ChatStateV2Wire(version=2, user_turn=5))
        self.model.complete.side_effect = AIFailure("private failure")
        with self.assertRaises(AIFailure):
            respond(request, self.model, self.repo, None, "test")
        self.assertEqual(request.state.user_turn, 5)

    def test_legacy_migration_quarantine_and_explicit_reset_on_wire(self):
        original = ChatStateV2(version=2, legacy_query="old story", legacy_criteria={"max_price_cents": 2000},
            legacy_excluded_ids=[10], shown_ids=[10])
        request = ChatRequest(message="more", state=ChatStateV2Wire.model_validate(original.model_dump()))
        self.model.complete.return_value = {"kind": "recommend", "query": "more"}
        reply = respond(request, self.model, self.repo, None, "test")
        self.assertFalse(reply.games)
        self.assertEqual(reply.state.legacy_query, "old story")
        self.repo.chat_candidates.assert_not_called()
        self.model.complete.return_value = {"kind": "social", "reply": "Starting over.", "reset_preferences": True}
        reset = respond(ChatRequest(message="start over", state=reply.state), self.model, self.repo, None, "reset")
        self.assertIsNone(reset.state.legacy_criteria)
        self.assertEqual(reset.state.legacy_excluded_ids, [])
        self.assertEqual(reset.state.legacy_query, "")


if __name__ == "__main__":
    unittest.main()
