"""Meaningful rejection tests for the frozen, not-yet-serving contract design."""

import unittest

from pydantic import ValidationError

from contracts import ChatStateV2, RetrievalOutcome, TurnPlan


class ContractTests(unittest.TestCase):
    def test_main_inputs_and_model_ids_cannot_be_smuggled_into_plan(self):
        for extra in ({"favorite_ids": [400]}, {"feedback": []},
                      {"exclusion_patch": [{"action": "add", "target": {"app_id": 400}}]},
                      {"criteria_patch": [{"scope": "conversation", "set": {"excluded_ids": [400]}}]}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                TurnPlan.model_validate({"kind": "recommend", **extra})

    def test_ambiguous_reference_and_competing_scopes_are_rejected(self):
        for values in ({"kind": "compare", "title_mentions": ["Portal"]},
                       {"kind": "game_facts", "reference": "last_pair"},
                       {"kind": "title_lookup", "title_mentions": ["Hades"], "reference": "last_game"},
                       {"kind": "recommend", "criteria_patch": [
                           {"scope": "turn", "set": {"max_price_cents": 2000}},
                           {"scope": "conversation", "clear": ["max_price_cents"]}]}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                TurnPlan.model_validate(values)

    def test_retained_criteria_require_bounded_user_provenance(self):
        for values in ({"user_turn": 1, "criteria": {"required_modes": ["multiplayer"]}},
                       {"user_turn": 1, "query": "combat"},
                       {"user_turn": 1, "provenance": {"platforms": {"user_turn": 2}}},
                       {"version": 3}, {"shown_ids": [400, 400]}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                ChatStateV2.model_validate(values)

    def test_legacy_preferences_remain_quarantined_not_active(self):
        state = ChatStateV2(legacy_criteria={"required_modes": ["multiplayer"]},
                            legacy_query="old intent", legacy_excluded_ids=[400])
        self.assertFalse(state.criteria.required_modes)
        self.assertFalse(state.query)
        self.assertFalse(state.exclusions)

    def test_turn_scope_and_explicit_suitability_are_expressible(self):
        plan = TurnPlan(kind="game_facts", title_mentions=["spiderman"], evaluate_prior_requirements=True)
        self.assertEqual(plan.criteria_patch, [])
        one_turn = TurnPlan(kind="recommend", criteria_patch=[{"scope": "turn", "set": {"platforms": ["linux"]}}])
        self.assertEqual(one_turn.criteria_patch[0].scope, "turn")
        restart = TurnPlan(kind="recommend", reset_preferences=True,
                           criteria_patch=[{"scope": "conversation", "set": {"required_modes": ["single-player"]}}])
        self.assertTrue(restart.reset_preferences)

    def test_catalog_absence_and_semantic_capabilities_cannot_be_overclaimed(self):
        for values in ({"kind": "not_in_catalog", "channels": ["lexical"]},
                       {"kind": "found", "channels": ["semantic"]},
                       {"kind": "found", "semantic_available": True, "degraded_reason": "encoder_missing"}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                RetrievalOutcome.model_validate(values)


if __name__ == "__main__":
    unittest.main()
