"""Missing provider usage cannot silently become zero planning consumption."""
import unittest

from game_discovery.jobs.audit_assistant_closeout import token_bound


class CloseoutTokenBoundTests(unittest.TestCase):
    def test_valid_reported_total_uses_actual_total_including_zero(self):
        for total in (0, 2147):
            self.assertEqual(token_bound({'reported_usage': {'total_tokens': total},
                                          'reserved_units': 12000}), (total, 0, False))

    def test_missing_or_invalid_total_falls_back_to_original_reservation(self):
        for usage in (None, {}, {'prompt_tokens': 2000}, {'total_tokens': True}, {'total_tokens': -1}):
            with self.subTest(usage=usage):
                self.assertEqual(token_bound({'reported_usage': usage, 'reserved_units': 12641}),
                                 (0, 12641, True))
        with self.assertRaises(ValueError):
            token_bound({'reported_usage': None, 'reserved_units': -1})


if __name__ == '__main__':
    unittest.main()
