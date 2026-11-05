"""Audit safety checks: no actual database, source requests or inference."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError


spec = importlib.util.spec_from_file_location(
    'catalog_capacity_audit', Path(__file__).resolve().parents[1] / 'scripts/catalog_capacity_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CapacityAuditTests(unittest.TestCase):
    def test_failure_checkpoints_and_stops_without_requesting_next_id(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            leads = [{'app_id': 10}, {'app_id': 20}]
            with patch.object(audit, 'fetch', side_effect=HTTPError('https://source.example', 429, 'rate', {}, None)) as fetch:
                result = audit.collect(output, leads)
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(result['status'], 'stopped_on_source_failure')
            saved = json.loads((output / 'pilot/collection.json').read_text())
            self.assertEqual(saved['observations'], [{'app_id': 10, 'error_type': 'HTTPError', 'http_status': 429}])
            with patch.object(audit, 'fetch') as fetch:
                with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                    audit.collect(output, [{'app_id': 20}])
            fetch.assert_not_called()

    def test_resume_does_not_retry_failed_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            audit.write_json(output / 'pilot/collection.json', {'app_ids': [10], 'observations': [
                {'app_id': 10, 'error_type': 'ValueError'}]})
            with patch.object(audit, 'fetch') as fetch, patch.object(audit, 'normalize', return_value={'games': 0}):
                self.assertEqual(audit.collect(output, [{'app_id': 10}]), {'games': 0})
            fetch.assert_not_called()

    def test_model_independent_statistics_and_project_guard(self):
        self.assertEqual(audit.percentile([4, 1, 3, 2, 5, 6]), {'samples': 6, 'p50_ms': 3, 'p95_ms': 6})
        with self.assertRaisesRegex(ValueError, 'project'):
            audit.engine_for({'DATABASE_URL': 'postgresql://user:pw@wrong.example/db'}, 'DATABASE_URL', 'https://mmdmxjiawlbridvvhtrt.supabase.co')
