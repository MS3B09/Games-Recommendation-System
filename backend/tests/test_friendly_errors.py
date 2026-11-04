import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from fastapi.testclient import TestClient
from game_discovery.ai.provider import AIFailure, DatabaseBudget, GroqAssistant, provider_retry_at
from game_discovery.api.main import create_app
from game_discovery.core.settings import Settings


class FriendlyErrorTests(unittest.TestCase):
    def test_unexpected_service_failure_never_echoes_or_logs_private_exception(self):
        repository = MagicMock()
        repository.facets.side_effect = RuntimeError('PRIVATE_DATABASE_PASSWORD')
        with self.assertLogs('game_discovery.errors', level='WARNING') as logs, TestClient(create_app(Settings(), repository=repository)) as client:
            response = client.get('/api/v1/facets')
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('PRIVATE', response.text)
        self.assertNotIn('PRIVATE', '\n'.join(logs.output))

    def test_chat_reasons_have_distinct_safe_contracts(self):
        cases = [('ai_daily_calls', 'chat_daily_calls', 429, 'discover'),
                 ('ai_daily_units', 'chat_daily_units', 429, 'discover'),
                 ('ai_minute_limit', 'chat_rate_limited', 429, 'retry'),
                 ('ai_provider_limited', 'chat_provider_limited', 429, 'retry'),
                 ('ai_accounting_unavailable', 'chat_accounting_unavailable', 503, 'retry'),
                 ('ai_timeout', 'chat_timeout', 504, 'retry'),
                 ('ai_provider_configuration', 'chat_service_configuration', 503, 'discover'),
                 ('chat_invalid_prose', 'chat_invalid_answer', 502, 'edit'),
                 ('chat_answer_context_limit', 'chat_context_limit', 422, 'new_chat'),
                 ('chat_required_context_limit', 'chat_message_too_detailed', 422, 'edit'),
                 ('chat_required_evidence_limit', 'chat_evidence_unavailable', 503, 'discover'),
                 ('PRIVATE_RAW_EXCEPTION', 'unexpected_error', 500, 'retry')]
        for internal, public, status, recovery in cases:
            with self.subTest(internal=internal):
                model = MagicMock()
                when = datetime.now(UTC) + timedelta(seconds=20) if status == 429 else None
                model.complete.side_effect = AIFailure(internal, retry_at=when)
                with TestClient(create_app(Settings(), repository=MagicMock(), chat_model=model)) as client:
                    response = client.post('/api/v1/chat', json={'message': 'hello'})
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()['code'], public)
                self.assertEqual(response.json()['recovery'], recovery)
                self.assertNotIn('PRIVATE', response.text)
                if when:
                    self.assertIsNotNone(response.json()['retry_at'])
                    self.assertIn('Retry-After', response.headers)

    def test_accounting_outage_is_not_called_daily_exhaustion(self):
        engine = MagicMock()
        engine.begin.side_effect = RuntimeError('PRIVATE_DSN')
        budget = DatabaseBudget(engine, 100, 1500000)
        model = GroqAssistant(Settings(), budget)
        with patch('game_discovery.ai.provider.urlopen') as network:
            with self.assertRaisesRegex(AIFailure, 'ai_accounting_unavailable'):
                model.complete('Return JSON', {})
            network.assert_not_called()

    def test_denied_atomic_reservation_keeps_reason_and_reset(self):
        engine = MagicMock()
        when = datetime.now(UTC) + timedelta(hours=1)
        engine.begin.return_value.__enter__.return_value.execute.return_value.one.return_value = (False, 'daily_calls', when)
        with self.assertRaises(AIFailure) as caught:
            DatabaseBudget(engine, 100, 1500000).reserve_or_raise(1000)
        self.assertEqual(caught.exception.code, 'ai_daily_calls')
        self.assertEqual(caught.exception.retry_at, when)

    def test_provider_failure_categories_do_not_retry_or_expose_bodies(self):
        for error, code in [(HTTPError('https://example.invalid', 429, 'private', {'Retry-After': '12'}, None), 'ai_provider_limited'),
                            (HTTPError('https://example.invalid', 403, 'private', {}, None), 'ai_provider_configuration'),
                            (HTTPError('https://example.invalid', 500, 'private', {}, None), 'ai_provider_unavailable'),
                            (URLError(TimeoutError('private')), 'ai_timeout')]:
            budget = MagicMock()
            budget.reserve.return_value = True
            with patch('game_discovery.ai.provider.urlopen', side_effect=error) as network:
                with self.assertRaises(AIFailure) as caught:
                    GroqAssistant(Settings(), budget).complete('JSON', {})
                self.assertEqual(caught.exception.code, code)
                self.assertNotIn('private', str(caught.exception))
                self.assertEqual(network.call_count, 1)

    def test_retry_after_rejects_unknown_or_unbounded_values(self):
        for value in (None, 'garbage', 'nan', '-10', '1000000000000'):
            self.assertIsNone(provider_retry_at(value))
        self.assertIsNotNone(provider_retry_at('10'))

    def test_input_errors_explain_the_field_without_echoing_input(self):
        with TestClient(create_app(Settings(), repository=MagicMock())) as client:
            response = client.post('/api/v1/chat', json={'message': 'PRIVATE' * 400})
            self.assertEqual(response.json()['code'], 'chat_message_too_long')
            self.assertEqual(response.json()['field'], 'message')
            self.assertNotIn('PRIVATE', response.text)
            response = client.post('/api/v1/discover', json={'filters': {'min_price_cents': 2000, 'max_price_cents': 1000}})
            self.assertEqual(response.json()['code'], 'invalid_price_range')

    def test_peer_cooldown_reports_remaining_time_not_another_full_wait(self):
        model = MagicMock()
        model.complete.side_effect = AIFailure('ai_provider_unavailable')
        clock = MagicMock()
        clock.monotonic.side_effect = [100, 111, 111]
        with patch('game_discovery.ai.provider.time', clock), TestClient(create_app(Settings(), repository=MagicMock(), chat_model=model)) as client:
            client.post('/api/v1/chat', json={'message': 'hello'})
            response = client.post('/api/v1/chat', json={'message': 'hello again'})
        self.assertEqual(response.json()['code'], 'chat_rate_limited')
        self.assertLessEqual(int(response.headers['Retry-After']), 19)
        self.assertEqual(model.complete.call_count, 1)
