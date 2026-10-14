import unittest

import numpy as np

from game_discovery.retrieval.encoder import normalized_mean_pool


class PoolingTests(unittest.TestCase):
    def test_padding_does_not_change_the_sentence_embedding(self):
        hidden = np.zeros((1, 3, 384), dtype=np.float32)
        hidden[0, 0, 0] = 2
        hidden[0, 1, 1] = 2
        hidden[0, 2, 2] = 1000
        vector = normalized_mean_pool(hidden, np.array([[1, 1, 0]]))
        self.assertAlmostEqual(float(vector[0, 0]), 2**-0.5, places=6)
        self.assertEqual(float(vector[0, 2]), 0)
        np.testing.assert_allclose(np.linalg.norm(vector, axis=1), [1], atol=1e-6)

    def test_nan_model_output_is_rejected(self):
        with self.assertRaises(ValueError):
            normalized_mean_pool(np.full((1, 1, 384), np.nan), np.array([[1]]))
