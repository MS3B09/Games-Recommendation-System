"""Exact nested timing accounting without provider, database, sleep or files."""

import sys
import unittest

from game_discovery.jobs.profile_chat_serving import ServingProfiler, summarize


class ServingProfileTests(unittest.TestCase):
    def test_nested_evaluation_time_is_removed_once_but_real_budget_time_is_retained(self):
        clock = [0.0]
        def advance(value):
            clock[0] += value
        def budget():
            advance(2)
        def capped():
            advance(3)
            budget()
            advance(4)
        def transport():
            advance(5)
            capped()
            advance(6)
        def journal():
            advance(7)
            transport()
            advance(8)
        def invoke():
            advance(9)
            journal()
            advance(10)
            return object()
        def turn(case, index, method):
            advance(100)  # pre-invocation checkpoint is not serving latency
            invoke()
            advance(100)
        codes = {turn.__code__: "turn", invoke.__code__: "invoke", journal.__code__: "journal",
                 transport.__code__: "transport", capped.__code__: "capped_budget", budget.__code__: "database_budget"}
        observer = ServingProfiler(codes, clock=lambda: clock[0])
        old = sys.getprofile()
        try:
            sys.setprofile(observer)
            turn({"id": "fixture"}, 0, "proposed")
            turn({"id": "fixture"}, 1, "proposed")
        finally:
            sys.setprofile(old)
        first, second = observer.records
        self.assertEqual(first["invocation_ms"], 54000)
        self.assertEqual(first["evaluation_wrapper_ms"], 22000)
        self.assertEqual(first["serving_equivalent_domain_ms"], 32000)
        self.assertFalse(first["warm"])
        self.assertTrue(second["warm"])
        self.assertTrue(second["invocation_returned_result"])
        self.assertEqual(summarize(observer.records)["proposed"]["warm_samples"], 1)
        self.assertFalse(observer.stack)

    def test_empty_observation_does_not_invent_a_latency_pass(self):
        result = summarize([])["proposed"]
        self.assertEqual(result["warm_samples"], 0)
        self.assertIsNone(result["serving_equivalent_domain_p95_ms"])


if __name__ == "__main__":
    unittest.main()
