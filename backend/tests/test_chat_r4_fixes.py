"""R4 transport contract and capability regressions; no network or quota writes."""

import json
import unittest
from unittest.mock import MagicMock, patch

from game_discovery.ai.chat_contracts import ChatStateV2, ChatTurn
from game_discovery.ai.chat_evidence import GENERATE, INTERPRET, input_bytes
from game_discovery.ai.provider import AIFailure, GroqAssistant
from game_discovery.ai.rag import ConversationalRAG
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.core.settings import Settings
from test_chat_rag import repository


class R4FixTests(unittest.TestCase):
    def test_schema_is_sent_once_and_included_in_reservation_and_context_bound(self):
        budget = MagicMock()
        budget.reserve.return_value = True
        model = GroqAssistant(Settings(groq_model="openai/gpt-oss-120b"), budget)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"choices": [{"message": {
            "content": json.dumps({"message": "Inspect these records.", "game_ids": [], "claims": {"claims": []}})}}]}).encode()
        data = {"games": []}
        with patch("game_discovery.ai.provider.urlopen", return_value=response) as network:
            model.complete(GENERATE, data)
        payload = json.loads(network.call_args.args[0].data)
        format = payload["response_format"]
        self.assertEqual(format["type"], "json_schema")
        self.assertTrue(format["json_schema"]["strict"])
        schema = format["json_schema"]["schema"]
        self.assertEqual(schema["properties"]["game_ids"]["maxItems"], 4)
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        for definition in [schema, *schema["$defs"].values()]:
            self.assertFalse(definition["additionalProperties"])
            self.assertEqual(set(definition["required"]), set(definition["properties"]))
        reserved_bytes = len(json.dumps({"messages": payload["messages"], "response_format": format}, ensure_ascii=False).encode())
        self.assertEqual(input_bytes(GENERATE, data), reserved_bytes)
        budget.reserve.assert_called_once_with(reserved_bytes + 1280)
        self.assertEqual(network.call_count, 1)
        with patch("game_discovery.ai.provider.urlopen") as network, self.assertRaises(AIFailure):
            model.complete(GENERATE, {"games": ["x" * 12000]})
        network.assert_not_called()
        self.assertEqual(budget.reserve.call_count, 1)

    def test_ordinary_transport_retains_json_mode_and_previous_accounting(self):
        budget = MagicMock()
        model = GroqAssistant(Settings(), budget)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"choices":[{"message":{"content":"{}"}}]}'
        with patch("game_discovery.ai.provider.urlopen", return_value=response) as network:
            model.complete(INTERPRET, {"message": "Hello"})
        payload = json.loads(network.call_args.args[0].data)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        budget.reserve.assert_called_once_with(len(json.dumps(payload["messages"], ensure_ascii=False).encode()) + 1280)

    def test_unsupported_platform_has_unavailable_metadata_without_reads_or_state_commit(self):
        model = MagicMock()
        model.complete.return_value = {"kind": "clarify", "reply": "Please choose a recorded PC platform."}
        repo = repository()
        rag = ConversationalRAG(model, repo, None)
        state = ChatStateV2()
        for platform in ("PlayStation 5", "PS5", "Xbox", "Nintendo Switch"):
            reply = rag.invoke(ChatTurn(message="Recommend games on " + platform + " only.", state=state))
            self.assertEqual(reply.retrieval.kind, "retrieval_unavailable")
            self.assertFalse(reply.retrieval.semantic_available)
            self.assertIsNone(reply.retrieval.degraded_reason)
            self.assertEqual(reply.state, state)
            self.assertFalse(reply.games)
        self.assertFalse(repo.mock_calls)
        self.assertEqual(model.complete.call_count, 4)
        ordinary = rag.invoke(ChatTurn(message="What would you recommend?"))
        self.assertIsNone(ordinary.retrieval)

    def test_snapshot_preserves_readonly_timeout_role_and_version_guards(self):
        engine = MagicMock()
        connection = engine.connect.return_value.execution_options.return_value.__enter__.return_value
        connection.execute.return_value.one.return_value = (False, "fixture", "2s")
        with CatalogRepository(engine).snapshot() as (_, version):
            self.assertEqual(version, "fixture")
        engine.connect.return_value.execution_options.assert_called_with(
            isolation_level="REPEATABLE READ", postgresql_readonly=True)
        self.assertEqual(connection.execute.call_count, 1)
        self.assertIn("set_config('statement_timeout','2s',true)", str(connection.execute.call_args.args[0]))
        for row, code in (((True, "fixture", "2s"), "database_role_misconfigured"),
                          ((False, None, "2s"), "catalog_not_initialized")):
            connection.execute.return_value.one.return_value = row
            with self.assertRaises(CatalogFailure) as raised, CatalogRepository(engine).snapshot():
                pass
            self.assertEqual(raised.exception.code, code)


if __name__ == "__main__":
    unittest.main()
