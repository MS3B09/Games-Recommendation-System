import unittest

from game_discovery.jobs.score_assistant_retrieval import score, template


class RetrievalReviewTests(unittest.TestCase):
    def report(self, empty=False):
        return {'results': [{'id': 'H1', 'split': 'held_out',
            'rankings': {'hybrid_rrf': [] if empty else [1, 2], 'cosine_only': [] if empty else [2, 1]},
            'masked_methods': {'A': 'cosine_only', 'B': 'hybrid_rrf'}}]}

    def test_null_ratings_cannot_create_an_aggregate_or_a_quality_pass(self):
        report = self.report()
        result = score(report, template(report))
        self.assertEqual(result['status'], 'owner_judgments_incomplete')
        self.assertIsNone(result['splits']['held_out']['aggregate'])

    def test_shared_candidate_ratings_and_missing_slots_are_applied_consistently(self):
        report = self.report()
        ratings = template(report)
        ratings['cases']['H1']['relevance'] = {'1': 2, '2': 0}
        metrics = score(report, ratings)['cases'][0]['metrics']
        self.assertEqual(metrics['hybrid_rrf']['mean_gain_at_4'], .5)
        self.assertEqual(metrics['cosine_only']['mean_gain_at_4'], .5)
        self.assertGreater(metrics['hybrid_rrf']['ndcg_at_4_judged_union'], metrics['cosine_only']['ndcg_at_4_judged_union'])

    def test_wrong_source_unknown_candidates_and_boolean_scores_are_rejected(self):
        report = self.report()
        for error in ('source', 'candidate', 'bool'):
            ratings = template(report)
            if error == 'source':
                ratings['source_report_sha256'] = 'wrong'
            elif error == 'candidate':
                ratings['cases']['H1']['relevance']['999'] = 2
            else:
                ratings['cases']['H1']['relevance']['1'] = True
            with self.assertRaises(ValueError):
                score(report, ratings)

    def test_empty_rankings_require_actual_adequacy_judgment(self):
        report = self.report(empty=True)
        ratings = template(report)
        self.assertIsNone(score(report, ratings)['splits']['held_out']['aggregate'])
        ratings['cases']['H1']['empty_ranking_adequacy'] = {'A': 'partial', 'B': 'fail'}
        result = score(report, ratings)
        self.assertEqual(result['cases'][0]['empty_ranking_adequacy']['B'], 'fail')
        self.assertEqual(result['splits']['held_out']['aggregate']['hybrid_rrf']['mean_gain_at_4'], 0)
