import json
import math
import unittest

from game_discovery.jobs.database_sizing import fixture_vector, recorded_cents


class StorageFixtureTests(unittest.TestCase):
    def test_unknown_or_invalid_price_never_becomes_free(self):
        for value in ("", "Unknown", "NaN", "Infinity", "-1", "1.001", "999999999"):
            self.assertIsNone(recorded_cents(value))
        self.assertEqual(recorded_cents("19.99"), 1999)
        self.assertEqual(recorded_cents("0.00"), 0)

    def test_sizing_vectors_are_bounded_reproducible_nonzero_payloads(self):
        vector = json.loads(fixture_vector(620))
        self.assertEqual(len(vector), 384)
        self.assertTrue(all(math.isfinite(value) for value in vector))
        self.assertAlmostEqual(sum(value * value for value in vector), 1, places=6)
        self.assertEqual(fixture_vector(620), fixture_vector(620))
        self.assertNotEqual(fixture_vector(620), fixture_vector(440))
