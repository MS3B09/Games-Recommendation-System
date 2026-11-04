"""Observation must not change inference behavior or persist sensitive payloads."""
import json
import tempfile
import unittest
from email.message import Message
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from game_discovery.ai import provider
from game_discovery.jobs.serve_provider_receipts import observe_headers


class ProviderReceiptTests(unittest.TestCase):
    def test_success_preserves_exact_request_response_and_only_records_allowed_headers(self):
        headers = Message()
        headers['x-ratelimit-limit-tokens'] = '8000'
        headers['x-ratelimit-remaining-tokens'] = '4242'
        headers['x-ratelimit-reset-tokens'] = '7.66s'
        headers['set-cookie'] = 'must-not-be-recorded'
        response = SimpleNamespace(status=200, headers=headers)
        request = Request('https://provider.invalid', b'private conversation',
                          {'Authorization': 'Bearer must-not-be-recorded'})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'headers.jsonl'
            with patch.object(provider, 'urlopen', return_value=response) as network:
                with observe_headers(output):
                    self.assertIs(provider.urlopen(request, timeout=3), response)
                network.assert_called_once_with(request, timeout=3)
            receipt = json.loads(output.read_text())
        self.assertEqual(receipt['status'], 200)
        self.assertEqual(receipt['headers']['x-ratelimit-limit-tokens'], '8000')
        self.assertNotIn('private', json.dumps(receipt))
        self.assertNotIn('must-not-be-recorded', json.dumps(receipt))
        self.assertNotIn('set-cookie', receipt['headers'])

    def test_http_error_is_reraised_unchanged_without_reading_body_or_retrying(self):
        headers = Message()
        headers['retry-after'] = '2'
        headers['x-ratelimit-remaining-tokens'] = '0'
        body = BytesIO(b'private provider error body')
        error = HTTPError('https://provider.invalid', 429, 'limited', headers, body)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'headers.jsonl'
            with patch.object(provider, 'urlopen', side_effect=error) as network:
                with observe_headers(output), self.assertRaises(HTTPError) as caught:
                    provider.urlopen('request', timeout=3)
                network.assert_called_once_with('request', timeout=3)
            self.assertIs(caught.exception, error)
            self.assertEqual(body.tell(), 0)
            receipt = json.loads(output.read_text())
        self.assertEqual(receipt['status'], 429)
        self.assertEqual(receipt['headers']['retry-after'], '2')
        self.assertNotIn('private', json.dumps(receipt))

    def test_receipt_write_failure_cannot_change_success_or_create_a_retry(self):
        response = SimpleNamespace(status=200, headers={})
        with patch.object(provider, 'urlopen', return_value=response) as network:
            with observe_headers(Path('unused.jsonl')), patch.object(Path, 'open', side_effect=OSError), \
                    patch('sys.stderr'):
                self.assertIs(provider.urlopen('request', timeout=3), response)
            network.assert_called_once_with('request', timeout=3)


if __name__ == '__main__':
    unittest.main()
