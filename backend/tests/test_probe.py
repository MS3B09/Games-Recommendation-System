import unittest

from game_discovery.jobs.probe import identity_matches, verified_review_summary


class ProbeIdentityTests(unittest.TestCase):
    def test_zero_review_success_does_not_establish_game_existence(self):
        payload = {"success": 1, "query_summary": {"total_positive": 0, "total_negative": 0, "total_reviews": 0}}
        self.assertIsNone(verified_review_summary(payload, app_identity_verified=False))
        self.assertEqual(verified_review_summary(payload, app_identity_verified=True), payload["query_summary"])
        payload["query_summary"]["total_positive"] = 3
        self.assertIsNone(verified_review_summary(payload, app_identity_verified=True))

    def test_demo_redirect_must_not_inherit_parent_game_tags(self):
        self.assertFalse(identity_matches(3736920, "https://store.steampowered.com/app/2174560/Bus_Flipper/"))
        self.assertTrue(identity_matches(440, "https://store.steampowered.com/app/440/Team_Fortress_2/"))
        self.assertFalse(identity_matches(440, None))
