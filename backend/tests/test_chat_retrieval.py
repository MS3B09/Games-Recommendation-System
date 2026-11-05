"""R1 deterministic tests; no provider or application database access."""

import json
import math
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from game_discovery.catalog.contracts import Filters, Game, semantic_hash
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.retrieval.chat import ChatRetriever, fuse
from game_discovery.retrieval.contracts import CandidatePools, RetrievalOutcome, TitleLookup
from game_discovery.retrieval.query import BoundedQueryEncoder
from game_discovery.retrieval.titles import TITLE_OPTION_LIMIT, CatalogTitle, match_title, normalize_title
from test_catalog_m2 import fixture

VECTOR = [1.0] + [0.0] * 383


def game(app_id=10, title="Fixture", **changes):
    result = fixture().model_copy(update={"app_id": app_id, "title": title, **changes})
    result.semantic_hash = semantic_hash(result)
    return Game.model_validate(result.model_dump())


class ConnectionRepository(CatalogRepository):
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def snapshot(self):
        yield self.connection, "fixture"


class TitleTests(unittest.TestCase):
    def test_unicode_punctuation_and_verified_spiderman_aliases(self):
        title = CatalogTitle(1817070, "Marvel’s Spider-Man Remastered")
        for query in ("spiderman", "Spider-Man", "spider man remastered", "MARVEL'S SPIDER-MAN REMASTERED",
                      "Marvel’s Spider Man Remastered", "Ｍａｒｖｅｌｓ Spider-Man Remastered"):
            with self.subTest(query=query):
                self.assertEqual(match_title(query, [title]).matches, (title,))
        self.assertEqual(normalize_title("Café — Adventure"), "café adventure")

    def test_ambiguous_franchise_is_not_resolved_by_broad_alias(self):
        titles = [CatalogTitle(1817070, "Marvel’s Spider-Man Remastered"),
                  CatalogTitle(200, "Marvel’s Spider-Man 2")]
        result = match_title("spiderman", titles)
        self.assertEqual(result.kind, "ambiguous")
        self.assertEqual(result.total_matches, 2)
        self.assertEqual(match_title("spiderman 2", titles).matches, (titles[1],))
        self.assertEqual(match_title("spiderman 3", titles).kind, "not_in_catalog")

    def test_exact_titles_win_and_sequel_numbers_are_not_dropped(self):
        titles = [CatalogTitle(1, "Portal"), CatalogTitle(2, "Portal 2"), CatalogTitle(20, "Portal 20")]
        self.assertEqual(match_title("Portal", titles).matches, (titles[0],))
        self.assertEqual(match_title("PORTAL-2", titles).matches, (titles[1],))
        self.assertEqual(match_title("portal 3", titles).kind, "not_in_catalog")
        self.assertEqual(match_title("port", titles).kind, "ambiguous")

    def test_whole_franchise_words_outrank_unrelated_partial_tokens(self):
        titles = [CatalogTitle(1, "Ori and the Blind Forest"), CatalogTitle(2, "Ori: Definitive Edition"),
                  CatalogTitle(3, "Divinity Original Sin 2")]
        self.assertEqual(match_title("ori", titles).matches, tuple(titles[:2]))

    def test_alias_requires_verified_identity_and_original_title(self):
        self.assertEqual(match_title("spiderman", [CatalogTitle(1817070, "Unrelated game")]).kind, "not_in_catalog")

    def test_fuzzy_names_are_suggestions_only_and_recent_ids_are_exact(self):
        titles = [CatalogTitle(10, "Stardew Valley"), CatalogTitle(11, "Valley Adventure")]
        result = match_title("Stardew Vally", titles)
        self.assertEqual(result.kind, "not_in_catalog")
        self.assertEqual(result.matches, ())
        self.assertEqual(result.suggestions, (titles[0],))
        self.assertEqual(match_title("", titles, 11).matches, (titles[1],))
        self.assertEqual(match_title("Stardew Valley", titles, 999).kind, "not_in_catalog")

    def test_bound_and_options_cap_are_explicit(self):
        titles = [CatalogTitle(i + 1, f"Adventure Chapter {i}") for i in range(10)]
        result = match_title("adventure", titles)
        self.assertEqual(len(result.matches), 4)
        self.assertEqual(result.total_matches, 10)
        with self.assertRaises(ValueError):
            match_title("adventure", titles * 30)
        for query in ("", "x" * 201):
            with self.assertRaises(ValueError):
                match_title(query, titles)


class ChatRepositoryTests(unittest.TestCase):
    def test_title_lookup_has_no_embedding_join_or_recommendation_predicates(self):
        connection = MagicMock()
        target = game(title="An unembedded game")
        connection.execute.side_effect = [[(10, target.title, 2, 1)], [(target.model_dump(mode="json"),)]]
        lookup = ConnectionRepository(connection).chat_title("unembedded")
        self.assertEqual(lookup.games, (target,))
        statements = " ".join(str(call.args[0]) for call in connection.execute.call_args_list)
        self.assertNotIn("embedding", statements)
        self.assertNotIn("game_prices", statements)
        self.assertNotIn("excluded", statements)
        self.assertEqual(connection.execute.call_args_list[0].args[1]['limit'], TITLE_OPTION_LIMIT + 1)
        self.assertIn('count(*) over(partition by priority)', statements)

    def test_missing_identity_keys_fail_instead_of_claiming_absence(self):
        connection = MagicMock()
        connection.execute.return_value = [(None, None, -1, 1)]
        result = ChatRetriever(ConnectionRepository(connection), None).lookup_title("missing")
        self.assertEqual(result.outcome.kind, "retrieval_unavailable")
        self.assertFalse(result.outcome.title_search_complete)

    def test_complete_database_match_beyond_old_256_cutoff_and_bounded_ambiguity(self):
        connection = MagicMock()
        target = game(900, 'Beyond the old cutoff')
        connection.execute.side_effect = [[(900, target.title, 0, 1)], [(target.model_dump(mode='json'),)]]
        result = ConnectionRepository(connection).chat_title(target.title)
        self.assertEqual(result.games, (target,))
        statement, params = connection.execute.call_args_list[0].args
        self.assertEqual(params['needle'], 'beyond the old cutoff')
        self.assertNotIn('257', str(statement))
        connection = MagicMock()
        targets = [game(i, f'Adventure {i}') for i in range(1, 6)]
        connection.execute.side_effect = [[(g.app_id, g.title, 2, 500) for g in targets],
                                          [(g.model_dump(mode='json'),) for g in targets[:4]]]
        result = ConnectionRepository(connection).chat_title('adventure')
        self.assertEqual(result.match.total_matches, 500)
        self.assertEqual(len(result.games), 4)

    def test_lexical_sql_requires_matching_rows_not_zero_rank_fillers(self):
        connection = MagicMock()
        connection.execute.return_value = []
        pools = ConnectionRepository(connection).chat_candidates("unmatched'); DROP TABLE games --", Filters())
        statement, params = connection.execute.call_args.args
        self.assertIn("g.search_text @@ to_tsquery", str(statement))
        self.assertNotIn("DROP", str(statement))
        self.assertEqual(params["limit"], 20)
        self.assertEqual(pools.lexical, ())
        self.assertFalse(pools.semantic_used)
        connection.execute.reset_mock()
        ConnectionRepository(connection).chat_candidates("12345 !", Filters())
        connection.execute.assert_not_called()

    def test_each_channel_applies_all_filters_before_limit(self):
        connection = MagicMock()
        connection.execute.return_value = []
        filters = Filters(min_price_cents=0, max_price_cents=1999, price_operator="lt", free_only=True,
                          platforms=["windows", "linux"], platform_match="all", required_modes=["single-player", "online-co-op"],
                          required_genres=["action", "adventure"], unwanted_terms=["horror"], excluded_ids=[10])
        ConnectionRepository(connection).chat_candidates("combat", filters, VECTOR, "fixture")
        self.assertEqual(connection.execute.call_count, 1)
        for call in connection.execute.call_args_list:
            sql, params = call.args
            for statement in str(sql).split(" union all "):
                self.assertLess(statement.index("amount_cents < :budget"), statement.index("limit :limit"))
                self.assertIn("p.free_to_play is true", statement)
                self.assertIn("g.app_id=any(:excluded)", statement)
            self.assertEqual(params["excluded"], [10])
            self.assertEqual(params["platforms"], ["windows", "linux"])
            self.assertEqual(params["modes"], ["single-player", "online-co-op"])
        self.assertIn("eligible as materialized", str(connection.execute.call_args.args[0]))

    def test_artifact_mismatch_runs_only_lexical_in_same_snapshot(self):
        connection = MagicMock()
        connection.execute.return_value = []
        pools = ConnectionRepository(connection).chat_candidates("combat", Filters(), VECTOR, "old")
        self.assertTrue(pools.artifact_mismatch)
        self.assertFalse(pools.semantic_used)
        self.assertEqual(connection.execute.call_count, 1)
        self.assertNotIn("game_embeddings", str(connection.execute.call_args.args[0]))

    def test_corrupt_or_ineligible_rows_are_not_allowed_to_cross_boundary(self):
        connection = MagicMock()
        connection.execute.return_value = [("lexical", game().model_dump(mode="json"), 0.1, 10)]
        with self.assertRaises(CatalogFailure):
            ConnectionRepository(connection).chat_candidates("combat", Filters(max_price_cents=100))
        for vector in ([0.0] * 384, [math.nan] * 384, [1.0]):
            with self.assertRaises(ValueError):
                ConnectionRepository(connection).chat_candidates("combat", Filters(), vector, "fixture")


class ChatRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock(spec=CatalogRepository)
        self.target = game()
        self.repo.chat_candidates.return_value = CandidatePools("fixture", (self.target,), (), True, False)

    def test_rrf_equal_weights_stable_id_ties_and_eight_evidence_bound(self):
        games = [game(i) for i in range(1, 31)]
        pools = CandidatePools("fixture", tuple(games[:20]), tuple((item, 0.5) for item in games[10:30]), True, True)
        result = fuse(pools)
        self.assertEqual(len(result), 30)
        self.assertEqual(result[0].game.app_id, 11)
        self.assertAlmostEqual(result[0].rrf_score, 1 / 71 + 1 / 61)
        self.assertEqual(len({item.game.app_id for item in result}), 30)
        self.repo.chat_candidates.return_value = pools
        reply = ChatRetriever(self.repo, BoundedQueryEncoder(lambda _: VECTOR, "fixture")).recommend("combat")
        self.assertEqual(len(reply.candidates), 8)
        self.assertEqual(len(reply.fused_ranks), 30)
        tie = fuse(CandidatePools("fixture", (games[0],), ((games[1], 0.9),), True, True))
        self.assertEqual([item.game.app_id for item in tie], [1, 2])

    def test_duplicate_channel_ids_and_conflicting_canonical_evidence_fail(self):
        for pools in (CandidatePools("fixture", (self.target,) * 2, (), True, False),
                      CandidatePools("fixture", (self.target,), ((game(title="Different"), 0.1),), True, True)):
            with self.assertRaises(ValueError):
                fuse(pools)

    def test_missing_busy_failed_and_invalid_encoders_have_truthful_fallback(self):
        busy = BoundedQueryEncoder(lambda _: VECTOR, "fixture")
        busy.slot.acquire()
        failed = MagicMock(catalog_version="fixture", side_effect=RuntimeError("private native details"))
        invalid = MagicMock(catalog_version="fixture", return_value=[0.0] * 384)
        try:
            for encoder, reason in ((None, "encoder_missing"), (busy, "encoder_busy"),
                                    (failed, "encoder_failed"), (invalid, "encoder_failed")):
                with self.subTest(reason=reason):
                    self.repo.reset_mock()
                    result = ChatRetriever(self.repo, encoder).recommend("combat", Filters(max_price_cents=2000))
                    self.assertEqual(result.outcome.degraded_reason, reason)
                    self.assertFalse(result.outcome.semantic_available)
                    self.assertEqual(result.outcome.channels, ["lexical"])
                    self.assertIsNone(self.repo.chat_candidates.call_args.args[2])
                    self.assertEqual(self.repo.chat_candidates.call_count, 1)
        finally:
            busy.slot.release()

    def test_mismatch_is_not_semantic_success_and_no_match_is_not_absence(self):
        self.repo.chat_candidates.return_value = CandidatePools("new", (), (), True, False, True)
        result = ChatRetriever(self.repo, BoundedQueryEncoder(lambda _: VECTOR, "old")).recommend("combat")
        self.assertEqual(result.outcome.degraded_reason, "artifact_mismatch")
        self.assertEqual(result.outcome.kind, "no_recommendation_match")
        self.assertFalse(result.outcome.title_search_complete)

    def test_database_failure_never_establishes_catalog_absence(self):
        for error in (CatalogFailure("database_unavailable"), OperationalError("private", {}, Exception("private"))):
            self.repo.chat_candidates.side_effect = error
            self.repo.chat_title.side_effect = error
            retriever = ChatRetriever(self.repo, None)
            for result in (retriever.lookup_title("missing"), retriever.recommend("combat")):
                self.assertEqual(result.outcome.kind, "retrieval_unavailable")
                self.assertEqual(result.outcome.evidence_ids, [])
                self.assertFalse(result.outcome.title_search_complete)

    def test_facts_ignore_recommendation_exclusions_and_all_filters_by_interface(self):
        title = CatalogTitle(10, self.target.title)
        self.repo.chat_title.return_value = TitleLookup("fixture", match_title("Fixture", [title]), (self.target,))
        result = ChatRetriever(self.repo, None).lookup_title("Fixture")
        self.assertEqual(result.outcome.kind, "found")
        self.assertEqual(result.outcome.channels, ["title"])
        self.repo.chat_title.assert_called_once_with("Fixture", None)
        self.repo.chat_candidates.assert_not_called()

    def test_bounded_inputs_fail_before_catalog_access(self):
        retriever = ChatRetriever(self.repo, None)
        for query in ("", "x" * 1001):
            with self.assertRaises(ValueError):
                retriever.recommend(query)
        with self.assertRaises(ValueError):
            retriever.recommend("combat", Filters(excluded_ids=list(range(1, 102))))
        with self.assertRaises(ValueError):
            retriever.lookup_title("x" * 201)
        self.repo.chat_candidates.assert_not_called()
        self.repo.chat_title.assert_not_called()

    def test_outcome_matches_frozen_r0_schema_and_rejects_conflicting_metadata(self):
        path = Path(__file__).resolve().parents[2] / "docs/reports/conversational-rag-r0-contracts.json"
        self.assertEqual(RetrievalOutcome.model_json_schema(), json.loads(path.read_text(encoding="utf-8"))["RetrievalOutcome"])
        for values in ({"kind": "not_in_catalog"},
                       {"kind": "found", "channels": ["semantic"]},
                       {"kind": "found", "semantic_available": True, "degraded_reason": "encoder_missing"}):
            with self.assertRaises(ValidationError):
                RetrievalOutcome(**values)
