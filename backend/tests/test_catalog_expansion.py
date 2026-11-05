"""Bounded collection, private metadata and legacy artifact compatibility."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from pydantic import ValidationError

from game_discovery.catalog.contracts import DashboardMetadata, Game, Source, digest
from game_discovery.catalog.metadata import normalize_metadata, release_date
from game_discovery.jobs.catalog import collect, database_manifest, embed, load_games, load_metadata, normalize, validated_artifact
from test_catalog_m2 import fixture, payload


def source_response(value, url='https://store.steampowered.com/api/appdetails?appids=10&cc=us'):
    body = json.dumps(value).encode()
    source = Source(url=url, collected_at='2026-11-05T00:00:00Z', sha256=hashlib.sha256(body).hexdigest())
    return body, source


class CatalogExpansionTests(unittest.TestCase):
    @patch('game_discovery.jobs.catalog.time.sleep')
    def test_source_throttle_checkpoints_and_stops_before_next_id(self, sleep):
        with tempfile.TemporaryDirectory() as temporary, patch('game_discovery.jobs.catalog.fetch_source',
                side_effect=HTTPError('https://source.example', 429, 'limit', {'Retry-After': '60'}, None)) as fetch:
            run = Path(temporary)
            report = collect(run, [10, 11], False)
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(report['stopped']['phase'], 'appdetails')
            self.assertEqual(report['observations'][0]['http_status'], 429)
            self.assertEqual(report, json.loads((run / 'collection.json').read_text()))

    @patch('game_discovery.jobs.catalog.time.sleep')
    def test_reviews_are_summary_only_and_resume_reuses_verified_successes(self, sleep):
        response = {'response': {'query_summary': {'total_positive': 7, 'total_negative': 2,
                    'total_reviews': 9, 'review_score_desc': 'Mostly Positive'},
                    'reviews': [{'author': {'steamid': 'do-not-store'}, 'review': 'do-not-store'}]}}
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            with patch('game_discovery.jobs.catalog.fetch_source', side_effect=[source_response(payload()),
                    source_response(response, 'https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/')]) as fetch:
                first = collect(run, [10, 11], False, reviews=True, eligible_target=1)
            self.assertEqual(fetch.call_count, 2)
            self.assertEqual(first['eligible_complete'], 1)
            self.assertEqual(len(first['observations']), 1)
            self.assertNotIn('do-not-store', (run / '10-reviews.json').read_text())
            with patch('game_discovery.jobs.catalog.fetch_source') as fetch, \
                    patch('game_discovery.jobs.catalog.write_json') as write:
                collect(run, [10, 11], True, reviews=True, eligible_target=1)
            fetch.assert_not_called()
            write.assert_not_called()
            with self.assertRaisesRegex(ValueError, 'settings mismatch'):
                collect(run, [10, 11], True, reviews=False, eligible_target=1)
            manifest = normalize(run, metadata=True, target_count=1, required_ids=[10])
            games, _ = load_games(run)
            metadata = load_metadata(run, manifest, games)
            self.assertEqual(metadata[0].reviews.total, 9)
            self.assertNotIn('developers', Game.model_fields)
            self.assertEqual(games[0].semantic_hash, fixture().semantic_hash)
            (run / 'metadata.json').write_text('[]')
            with self.assertRaisesRegex(ValueError, 'metadata checksum'):
                load_games(run)
            with patch('game_discovery.jobs.catalog.normalize_payload',
                    return_value=fixture().model_copy(update={'eligibility': 'quarantined',
                        'eligibility_reason': 'software_genre_requires_verification'})), \
                    patch('game_discovery.jobs.catalog.fetch_source', side_effect=HTTPError(
                        'https://source.example', 503, 'temporary', {}, None)) as fetch:
                reclassified = collect(run, [10, 11], True, reviews=True, eligible_target=1)
            self.assertEqual(reclassified['eligible_complete'], 0)
            self.assertEqual(reclassified['observations'][0]['eligibility'], 'quarantined')
            self.assertEqual(reclassified['observations'][0]['eligibility_reason'], 'software_genre_requires_verification')
            self.assertEqual(reclassified['observations'][0]['reviews'], first['observations'][0]['reviews'])
            self.assertEqual(fetch.call_count, 1)  # Only the untouched replacement ID is fetched.
            self.assertEqual(reclassified['stopped']['app_id'], 11)

    @patch('game_discovery.jobs.catalog.time.sleep')
    def test_corrupt_saved_success_fails_instead_of_refetching(self, sleep):
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            with patch('game_discovery.jobs.catalog.fetch_source', return_value=source_response(payload())):
                collect(run, [10], False)
            (run / '10-appdetails.json').write_text('{}')
            with patch('game_discovery.jobs.catalog.fetch_source') as fetch:
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    collect(run, [10], True)
            fetch.assert_not_called()

    @patch('game_discovery.jobs.catalog.time.sleep')
    def test_unavailable_identity_is_visible_and_target_or_required_ids_must_be_met(self, sleep):
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            with patch('game_discovery.jobs.catalog.fetch_source', side_effect=[
                    source_response(payload()), source_response({'11': {'success': False}})]):
                report = collect(run, [10, 11], False)
            self.assertEqual(len(report['observations']), 2)
            self.assertNotIn('stopped', report)
            for target, required in ((2, [10]), (1, [11])):
                with self.assertRaisesRegex(ValueError, 'target or retained'):
                    normalize(run, metadata=True, target_count=target, required_ids=required)

    def test_metadata_preserves_names_partial_dates_unknowns_and_invalid_discount(self):
        raw = copy.deepcopy(payload()['10']['data'])
        raw.update(developers=['Thekla, Inc.', 'Thekla, Inc.'], release_date={'date': '2020'})
        raw['price_overview'].update(initial=2999, discount_percent=101)
        metadata = normalize_metadata(10, raw, fixture().evidence[0].source)
        self.assertEqual(metadata.developers, ['Thekla, Inc.'])
        self.assertEqual(metadata.original_price_cents, 2999)
        self.assertEqual(metadata.discount_percent, 101)
        self.assertEqual(metadata.release_date.precision, 'year')
        self.assertIsNone(metadata.release_date.month)
        self.assertEqual(release_date('May 2020').precision, 'month')
        self.assertEqual(release_date('Coming soon').precision, 'unknown')
        raw.pop('price_overview')
        raw['is_free'] = True
        self.assertIsNone(normalize_metadata(10, raw, fixture().evidence[0].source).original_price_cents)
        bad = metadata.model_dump()
        bad['original_price_cents'] = 1
        with self.assertRaises(ValidationError):
            DashboardMetadata.model_validate(bad)

    def test_collection_bounds_reject_bool_and_more_than_2500_ids_before_io(self):
        for ids in ([True], list(range(1, 2502)), [0], [2147483648], [1, 1]):
            with self.assertRaises(ValueError):
                collect(Path('not-created'), ids, False)

    def test_database_manifest_bounds_rejections_without_changing_artifact_identity(self):
        artifact = {'version': 'fixture', 'games_sha256': 'a' * 64,
                    'quarantine': [{'app_id': i, 'reason': 'software_genre_requires_verification'} for i in range(2500)]}
        before = copy.deepcopy(artifact)
        compact = database_manifest(artifact)
        self.assertEqual(artifact, before)
        self.assertNotIn('quarantine', compact)
        self.assertEqual(compact['quarantine_count'], 2500)
        self.assertEqual(compact['quarantine_sha256'], digest(artifact['quarantine']))
        self.assertEqual(compact['artifact_sha256'], digest(artifact))
        self.assertLess(len(json.dumps(compact)), 16384)

    @patch('game_discovery.jobs.catalog.time.sleep')
    def test_embedding_parts_resume_after_interruption_and_metadata_only_changes(self, sleep):
        class Vector:
            def tolist(self):
                return [1.0] + [0.0] * 383

        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / 'run'
            tokenizer, model = Path(temporary) / 'tokenizer.json', Path(temporary) / 'model.onnx'
            tokenizer.write_bytes(b'tokenizer fixture')
            model.write_bytes(b'model fixture')
            with patch('game_discovery.jobs.catalog.fetch_source', return_value=source_response(payload())):
                collect(run, [10], False)
            normalize(run)
            with patch('huggingface_hub.hf_hub_download', side_effect=lambda _, name, **kw: str(model if name.endswith('.onnx') else tokenizer)), \
                    patch('game_discovery.retrieval.encoder.OnnxEncoder') as encoder:
                encoder.return_value.encode.return_value = [Vector()]
                self.assertEqual(embed(run, Path(temporary), 8, False)['embedded'], 1)
                original = validated_artifact(run)[2]['embeddings_sha256']
                (run / 'embeddings.json').unlink()  # Simulated interruption before the final combined checkpoint.
                normalize(run, metadata=True)
                encoder.return_value.encode.reset_mock()
                result = embed(run, Path(temporary), 8, True)
                self.assertEqual((result['embedded'], result['reused']), (0, 1))
                encoder.return_value.encode.assert_not_called()
                self.assertEqual(validated_artifact(run)[2]['embeddings_sha256'], original)
