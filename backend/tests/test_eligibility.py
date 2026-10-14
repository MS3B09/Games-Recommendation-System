import unittest

from game_discovery.catalog.eligibility import classify_appdetails


class EligibilityTests(unittest.TestCase):
    def base(self):
        return {"type": "game", "release_date": {"coming_soon": False},
                "genres": [], "content_descriptors": {"ids": []}}

    def test_mature_or_nudity_is_not_an_adult_only_exclusion(self):
        data = self.base()
        data["content_descriptors"]["ids"] = [1, 2, 5]
        self.assertEqual(classify_appdetails(data)["status"], "eligible")

    def test_adult_only_content_is_excluded(self):
        for descriptor in (3, 4):
            data = self.base()
            data["content_descriptors"]["ids"] = [1, descriptor, 5]
            self.assertEqual(classify_appdetails(data)["status"], "excluded")

    def test_missing_or_new_descriptors_are_quarantined(self):
        data = self.base()
        del data["content_descriptors"]
        self.assertEqual(classify_appdetails(data)["status"], "quarantined")
        data["content_descriptors"] = {"ids": [99]}
        self.assertEqual(classify_appdetails(data)["status"], "quarantined")

    def test_non_games_and_unreleased_games_fail_closed(self):
        for app_type in ("demo", "music", "dlc", "software"):
            self.assertEqual(classify_appdetails({"type": app_type})["status"], "excluded")
        data = self.base()
        data["release_date"]["coming_soon"] = True
        self.assertEqual(classify_appdetails(data)["reason"], "unreleased")
        data["release_date"]["coming_soon"] = 0
        self.assertEqual(classify_appdetails(data)["status"], "quarantined")

    def test_early_access_uses_source_genre_identity_not_title_guess(self):
        data = self.base()
        data["genres"] = [{"id": "70", "description": "Early Access"}]
        self.assertTrue(classify_appdetails(data)["early_access"])
        self.assertEqual(classify_appdetails(data)["status"], "eligible")
