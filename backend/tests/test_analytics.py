import copy
import unittest
from unittest.mock import MagicMock
from contextlib import contextmanager

from fastapi.testclient import TestClient

from game_discovery.api.main import create_app
from game_discovery.catalog.analytics import AnalyticsResponse, build_analytics, validate_analytics
from game_discovery.catalog.contracts import digest, semantic_hash
from game_discovery.catalog.metadata import normalize_metadata
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.readiness import CatalogReadiness
from game_discovery.db.readiness import probe_catalog
from pydantic import SecretStr
from test_catalog_m2 import fixture


def pairs(prices=(0, 499, 500, 999, 1000, 1999, 2000, 4999, 5000, 9999, 10000, None)):
    games, metadata = [], []
    for i, price in enumerate(prices):
        game = fixture().model_copy(deep=True)
        game.app_id = i + 1
        game.description = 'Puzzle puzzle adventure. The game with players.'
        game.genres = ['Free to Play', 'Free to Play', 'Early Access']
        game.free_to_play = (True, False, None)[i % 3]
        game.semantic_hash = semantic_hash(game)
        source = game.evidence[0].source
        raw = {'developers': ['Studio, Inc.', ' studio, inc. ', 'Another Studio'],
               'release_date': {'date': 'Jan 2020' if i % 2 else '2020'},
               'price_overview': {'currency': 'USD', 'initial': price, 'discount_percent': [0, 10, 25, 50, 75, 90, 100, 101, -1, None, 9, 24][i % 12]}}
        games.append(game)
        metadata.append(normalize_metadata(game.app_id, raw, source))
    return games, metadata


class AnalyticsTests(unittest.TestCase):
    def test_edges_unknown_denominators_full_names_and_description_counts(self):
        games, meta = pairs()
        data = build_analytics(games, meta, 'fixture-v1')
        self.assertEqual([x.count for x in data.price_ranges], [2, 2, 2, 2, 2, 1])
        self.assertEqual(data.coverage['original_price'].unknown, 1)
        self.assertEqual(data.avg_price_cents, sum(m.original_price_cents for m in meta if m.original_price_cents is not None)/11)
        self.assertEqual(data.coverage['discount'].model_dump(), {'known': 9, 'unknown': 1, 'invalid': 2})
        self.assertEqual([x.count for x in data.discount_ranges], [2, 2, 1, 1, 1, 1, 1])
        self.assertEqual(data.total_developers, 2)
        self.assertEqual([x.count for x in data.developers], [12, 12])
        self.assertTrue(any(x.label == 'Studio, Inc.' for x in data.developers))
        self.assertEqual({x.label: x.count for x in data.genres}, {'Free to Play': 12, 'Early Access': 12})
        self.assertEqual(data.release_years[0].months, [6] + [0]*11)
        self.assertEqual(data.coverage['release_month'].unknown, 6)
        self.assertEqual({x.label: x.count for x in data.words}, {'puzzle': 24, 'adventure': 12})
        self.assertEqual([x.count for x in data.free_paid], [4, 4, 4])
        self.assertEqual(data.platforms[2].unknown, 12)
        self.assertEqual(data.model_dump(), build_analytics(games, meta, 'fixture-v1').model_dump())

    def test_empty_and_all_unknown_are_not_zero_means(self):
        data = build_analytics([], [], 'empty')
        self.assertIsNone(data.avg_price_cents)
        self.assertIsNone(data.avg_discount_percent)
        self.assertEqual(data.total_games, 0)
        games, meta = pairs((None,))
        meta[0] = normalize_metadata(games[0].app_id, {}, games[0].evidence[0].source)
        data = build_analytics(games, meta, 'unknown')
        self.assertIsNone(data.avg_price_cents)
        self.assertIsNone(data.avg_discount_percent)
        self.assertEqual(data.reviews[0].label, 'Unknown')
        with self.assertRaises(ValueError):
            build_analytics(games, [], 'bad')

    def test_checksum_version_and_denominator_tampering_rejected(self):
        games, meta = pairs()
        doc = build_analytics(games, meta, 'v1').model_dump(mode='json')
        artifact = {'games_sha256': 'a'*64, 'metadata_sha256': 'b'*64}
        manifest = {**artifact, 'sha256': digest(doc), 'catalog_version': 'v1', 'format': 'catalog-analytics-v1', 'artifact_sha256': digest(artifact)}
        validate_analytics(doc, digest(doc), manifest, artifact, 'v1', len(games))
        for field, value in [('total_games', 99), ('catalog_version', 'v2')]:
            changed = {**doc, field: value}
            with self.assertRaises(ValueError):
                validate_analytics(changed, digest(doc), manifest, artifact, 'v1', len(games))
        changed = copy.deepcopy(doc)
        changed['free_paid'][0]['count'] += 1
        with self.assertRaises(ValueError):
            validate_analytics(changed, digest(changed), {**manifest, 'sha256': digest(changed)}, artifact, 'v1', len(games))
        for broken in (None, {}, {'games_sha256': None}):
            with self.assertRaises(ValueError):
                validate_analytics(doc, digest(doc), manifest, broken, 'v1', len(games))

    def test_readiness_rejects_missing_or_mismatched_enabled_analytics(self):
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        connection.execute.return_value.scalar_one.return_value = False
        for document in (None, {}):
            connection.execute.return_value.fetchone.return_value = ('v1', 1, None, None, {'format': 'catalog-analytics-v1'}, 'a'*64, document)
            self.assertEqual(probe_catalog(SecretStr('configured'), engine).error_code, 'analytics_integrity_error')

    def test_repository_reads_only_compact_active_snapshot_and_api_no_store(self):
        games, meta = pairs()
        data = build_analytics(games, meta, 'v1')
        response = AnalyticsResponse(catalog_version='v1', catalog_created_at=games[0].observed_at,
                                     analytics_sha256=digest(data.model_dump(mode='json')), data=data)
        repo = MagicMock(spec=CatalogRepository)
        repo.analytics.return_value = response
        with TestClient(create_app(Settings(), catalog_probe=lambda: CatalogReadiness(version='v1'), repository=repo)) as client:
            result = client.get('/api/v1/analytics')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.headers['cache-control'], 'no-store')
            self.assertEqual(result.json()['data']['total_games'], 12)
            repo.analytics.side_effect = CatalogFailure('analytics_unavailable')
            self.assertEqual(client.get('/api/v1/analytics').json()['code'], 'analytics_unavailable')

        class Repo(CatalogRepository):
            @contextmanager
            def snapshot(self):
                yield connection, 'v1'

        connection = MagicMock()
        connection.execute.return_value.one.return_value = (games[0].observed_at, 12, {}, None, None, None)
        with self.assertRaises(CatalogFailure):
            Repo(None).analytics()
        sql = str(connection.execute.call_args.args[0])
        self.assertIn('catalog_analytics', sql)
        self.assertNotIn('discovery.games', sql)
