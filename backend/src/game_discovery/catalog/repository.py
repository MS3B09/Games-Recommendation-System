"""Bounded, parameterized PostgreSQL catalog access; active snapshot per transaction."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Connection, Engine, text

from game_discovery.catalog.contracts import DiscoverRequest, Filters, Game, Recommendation, StrictModel
from game_discovery.catalog.discovery import FEEDBACK_WEIGHT, centroid, recommendation, satisfies
from game_discovery.retrieval.query import lexical_query
from game_discovery.retrieval.query import validate_query_vector
from game_discovery.retrieval.contracts import CandidatePools, TitleLookup
from game_discovery.retrieval.titles import TITLE_CATALOG_LIMIT, CatalogTitle, match_title


class CatalogFailure(Exception):
    def __init__(self, code: str):
        self.code = code


class GamePage(StrictModel):
    catalog_version: str
    items: list[Game]
    total: int
    offset: int


class ResolvedGames(StrictModel):
    catalog_version: str
    items: list[Game]
    unknown_ids: list[int]


class Facets(StrictModel):
    catalog_version: str
    genres: list[str]
    tags: list[str]
    modes: list[str]
    platforms: list[str]
    max_price_cents: int | None = None


class CatalogRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    @contextmanager
    def snapshot(self) -> Iterator[tuple[Connection, str]]:
        with self.engine.connect().execution_options(
                isolation_level="REPEATABLE READ", postgresql_readonly=True) as connection, connection.begin():
            # Psycopg puts READ ONLY in BEGIN. One metadata round trip replaces
            # separate SET/role/version trips; timeout stays transaction-local.
            elevated, version, _ = connection.execute(text("""select
                rolsuper or rolcreatedb or rolcreaterole or rolbypassrls,
                (select version from discovery.catalog_versions where active),
                set_config('statement_timeout','2s',true)
                from pg_roles where rolname=current_user""")).one()
            if elevated:
                raise CatalogFailure("database_role_misconfigured")
            if version is None:
                raise CatalogFailure("catalog_not_initialized")
            yield connection, str(version)

    def search(self, query: str, limit: int, offset: int) -> GamePage:
        with self.snapshot() as (connection, version):
            params = {"v": version, "query": query, "needle": "%" + query.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%",
                      "limit": limit, "offset": offset}
            where = """version=:v and eligibility='eligible' and
                (:query='' or normalized_title like :needle escape '\\' or
                 search_text @@ websearch_to_tsquery('english',:query))"""
            count = connection.execute(text(f"select count(*) from discovery.games where {where}"), params).scalar_one()
            rows = connection.execute(text(f"""select document from discovery.games where {where}
                order by (normalized_title like :needle escape '\\') desc, normalized_title, app_id limit :limit offset :offset"""), params)
            return GamePage(catalog_version=version, items=[Game.model_validate(row[0]) for row in rows], total=count, offset=offset)

    def resolve(self, app_ids: list[int]) -> ResolvedGames:
        with self.snapshot() as (connection, version):
            rows = connection.execute(text("select document from discovery.games where version=:v and app_id=any(:ids) order by app_id"),
                                      {"v": version, "ids": app_ids})
            games = [Game.model_validate(row[0]) for row in rows]
            found = {game.app_id for game in games}
            return ResolvedGames(catalog_version=version, items=games, unknown_ids=sorted(set(app_ids) - found))

    def assistant_search(self, query: str, limit: int, offset: int) -> GamePage:
        """Complete paginated title/text search; never exact-title short-circuiting.

        Includes ineligible records for factual inspection, unlike discovery.
        Recommendation eligibility is enforced by the separate retrieval tool.
        """
        if len(query) > 200 or not 1 <= limit <= 30 or not 0 <= offset <= 10000000:
            raise ValueError("Invalid catalog page")
        with self.snapshot() as (connection, version):
            params = {"v": version, "q": query, "limit": limit, "offset": offset,
                      "needle": "%" + query.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"}
            where = "version=:v and (:q='' or normalized_title like :needle escape '\\' or search_text @@ websearch_to_tsquery('english',:q))"
            total = connection.execute(text(f"select count(*) from discovery.games where {where}"), params).scalar_one()
            rows = connection.execute(text(f"select document from discovery.games where {where} order by normalized_title,app_id limit :limit offset :offset"), params)
            return GamePage(catalog_version=version, items=[Game.model_validate(row[0]) for row in rows],
                            total=total, offset=offset)

    def facets(self) -> Facets:
        with self.snapshot() as (connection, version):
            rows = connection.execute(text("select distinct kind,term from discovery.game_terms where version=:v order by kind,term"), {"v": version})
            terms: dict[str, list[str]] = {"genre": [], "tag": [], "mode": []}
            for kind, term in rows:
                terms[kind].append(term)
            platforms = connection.execute(text("select distinct platform from discovery.game_platforms where version=:v and supported order by platform"), {"v": version})
            platform_names = [row[0] for row in platforms]
            maximum = connection.execute(text("""select max(p.amount_cents) from discovery.game_prices p
                join discovery.games g using(version,app_id)
                where p.version=:v and g.eligibility='eligible' and p.region='US' and p.currency='USD'"""), {"v": version}).scalar()
            return Facets(catalog_version=version, genres=terms["genre"], tags=terms["tag"], modes=terms["mode"],
                          platforms=platform_names, max_price_cents=maximum)

    def chat_title(self, query: str, reference_id: int | None = None) -> TitleLookup:
        """Complete small-catalog identity search, including games without vectors.

        Only compact identities cross the scan boundary. Fail closed above the
        measured cap: a partial catalog scan must never establish absence.
        """
        if len(query) > 200 or (not query.strip() and reference_id is None):
            raise ValueError("A bounded title is required")
        with self.snapshot() as (connection, version):
            rows = connection.execute(text("""select app_id,title from discovery.games
                where version=:v and eligibility='eligible' order by app_id limit :limit"""),
                {"v": version, "limit": TITLE_CATALOG_LIMIT + 1})
            titles = [CatalogTitle(int(row[0]), str(row[1])) for row in rows]
            if len(titles) > TITLE_CATALOG_LIMIT:
                raise CatalogFailure("title_catalog_bound_exceeded")
            match = match_title(query, titles, reference_id)
            ids = [item.app_id for item in match.matches]
            games: dict[int, Game] = {}
            if ids:
                documents = connection.execute(text("""select document from discovery.games
                    where version=:v and eligibility='eligible' and app_id=any(:ids) order by app_id"""),
                    {"v": version, "ids": ids})
                games = {game.app_id: game for game in (Game.model_validate(row[0]) for row in documents)}
                if set(ids) != set(games) or any(games[item.app_id].title != item.title for item in match.matches):
                    raise CatalogFailure("catalog_integrity_error")
            return TitleLookup(version, match, tuple(games[app_id] for app_id in ids))

    def chat_candidates(self, query: str, filters: Filters, query_vector: list[float] | None = None,
                        encoder_version: str | None = None) -> CandidatePools:
        """Chat-only 20+20 pools, with hard predicates BEFORE ranking/LIMIT.

        Main discover() weights, seed affinity and feedback are not involved.
        Every channel shares one restricted repeatable-read snapshot.
        """
        if not query.strip() or len(query) > 1000 or len(filters.excluded_ids) > 100:
            raise ValueError("A bounded chat query and exclusions are required")
        if query_vector is not None:
            validate_query_vector(query_vector)
        with self.snapshot() as (connection, version):
            mismatch = query_vector is not None and encoder_version != version
            clauses, params = filter_sql(filters)
            params.update(v=version, excluded=filters.excluded_ids, limit=20)
            where = ("g.version=:v and g.eligibility='eligible' and not (g.app_id=any(:excluded)) and "
                     + (" and ".join(clauses) if clauses else "true"))
            terms = lexical_query(query)
            statements = []
            if terms:
                params["terms"] = terms
                statements.append(f"""select 'lexical' as channel,document,score,app_id from (
                    select g.document,g.app_id,ts_rank_cd(g.search_text,to_tsquery('english',:terms),32) as score
                    from discovery.games g left join discovery.game_prices p using(version,app_id)
                    where {where} and g.search_text @@ to_tsquery('english',:terms)
                    order by score desc,g.app_id limit :limit) lexical_pool""")
            semantic_used = query_vector is not None and not mismatch
            if semantic_used:
                params["vector"] = json.dumps(query_vector)
                # Materialization ensures exact eligible-set ranking rather than
                # an approximate index scan that can lose rows to postfilters.
                statements.append(f"""select 'semantic' as channel,document,score,app_id from (
                    with eligible as materialized (
                    select g.document,g.app_id,e.embedding from discovery.games g
                    join discovery.game_embeddings e using(version,app_id)
                    left join discovery.game_prices p using(version,app_id) where {where})
                    select document,app_id,1 - (embedding OPERATOR(extensions.<=>)
                        cast(:vector as extensions.vector)) as score from eligible
                    order by score desc,app_id limit :limit) semantic_pool""")
            lexical = []
            semantic = []
            if statements:
                # Two independently capped/ranked channels, one DB round trip.
                # The outer order restores each channel's deterministic ranks.
                rows = connection.execute(text(" union all ".join(statements)
                                               + " order by channel,score desc,app_id"), params)
                for channel, document, score, _ in rows:
                    game = Game.model_validate(document)
                    if channel == "lexical":
                        lexical.append(game)
                    elif channel == "semantic":
                        semantic.append((game, float(score)))
                    else:
                        raise CatalogFailure("catalog_integrity_error")
            if any(not satisfies(game, filters, set(filters.excluded_ids))
                   for game in [*lexical, *(game for game, _ in semantic)]):
                raise CatalogFailure("catalog_integrity_error")
            return CandidatePools(version, tuple(lexical), tuple(semantic), bool(terms), semantic_used, mismatch)

    def discover(self, request: DiscoverRequest, query_vector: list[float] | None = None,
                 encoder_version: str | None = None) -> tuple[str, list[Recommendation]]:
        filters = request.effective_filters()
        feedback = request.latest_feedback()
        with self.snapshot() as (connection, version):
            if query_vector is not None and encoder_version != version:
                raise CatalogFailure("query_artifact_mismatch")
            seeds = []
            vectors = []
            feedback_vectors: dict[int, list[float]] = {}
            rows = connection.execute(text("""select g.document,cast(e.embedding as text) from discovery.games g
                join discovery.game_embeddings e using(version,app_id) where g.version=:v and g.app_id=any(:ids) order by g.app_id"""),
                {"v": version, "ids": sorted(set(request.favorite_ids) | {item.app_id for item in feedback})})
            for document, vector in rows:
                game = Game.model_validate(document)
                parsed_vector = json.loads(vector)
                feedback_vectors[game.app_id] = parsed_vector
                if game.app_id in request.favorite_ids:
                    seeds.append(game)
                    vectors.append(parsed_vector)
            if set(request.favorite_ids) - {game.app_id for game in seeds}:
                raise CatalogFailure("unknown_favorite")
            excluded = request.excluded_ids()
            clauses, params = filter_sql(filters)
            params.update(v=version, excluded=sorted(excluded), limit=request.limit)
            seed_score = "0.0"
            if vectors:
                average = centroid(vectors)
                if average is None:
                    raise CatalogFailure("invalid_seed_vector")
                params["vector"] = json.dumps(average)
                seed_score = "1 - (e.embedding OPERATOR(extensions.<=>) cast(:vector as extensions.vector))"
            params["preferred"] = [term.casefold() for term in filters.preferred_terms]
            # Versioned text-ranking defaults: seed .45, query .40, lexical .15.
            # Renormalize only present components; retain legacy ordering for
            # requests without text. These weights are not evaluated quality claims.
            if request.query.strip():
                components = []
                if vectors:
                    components.append((0.45, f"greatest(0.0,least(1.0,{seed_score}))"))
                if query_vector is not None:
                    params["query_vector"] = json.dumps(query_vector)
                    components.append((0.40, "greatest(0.0,least(1.0,1 - (e.embedding OPERATOR(extensions.<=>) cast(:query_vector as extensions.vector))))"))
                terms = lexical_query(request.query)
                if terms:
                    params["query_terms"] = terms
                    components.append((0.15, "ts_rank_cd(g.search_text,to_tsquery('english',:query_terms),32)"))
                total = sum(weight for weight, _ in components)
                seed_score = " + ".join(f"{weight / total} * ({expression})" for weight, expression in components) if total else "0.0"
            # Bounded preferred-term boost; stable ID breaks ties. No unsupported quality claims.
            score = f"({seed_score}) + 0.15 * (select count(distinct t.term)::float / greatest(cardinality(cast(:preferred as text[])),1) from discovery.game_terms t where t.version=g.version and t.app_id=g.app_id and t.kind in ('genre','tag') and t.term=any(:preferred))"
            # Already played excludes only the exact title; it never supplies negative taste.
            # Missing/removed feedback IDs are ignored for affinity, but exact exclusions remain.
            for kind, key, sign in (("interested", "positive", "+"), ("not-for-me", "negative", "-")):
                affinity = centroid([feedback_vectors[item.app_id] for item in feedback
                                     if item.kind == kind and item.app_id in feedback_vectors])
                if affinity is not None:
                    params[key] = json.dumps(affinity)
                    score += (f" {sign} {FEEDBACK_WEIGHT} * greatest(0.0,least(1.0,"
                              f"1 - (e.embedding OPERATOR(extensions.<=>) cast(:{key} as extensions.vector))))")
            rows = connection.execute(text(f"""select g.document from discovery.games g
                join discovery.game_embeddings e using(version,app_id)
                left join discovery.game_prices p using(version,app_id)
                where g.version=:v and g.eligibility='eligible' and not (g.app_id=any(:excluded))
                and {' and '.join(clauses) if clauses else 'true'}
                order by {score} desc,g.app_id limit :limit"""), params)
            results = []
            for row in rows:
                game = Game.model_validate(row[0])
                if not satisfies(game, filters, excluded):
                    raise CatalogFailure("catalog_integrity_error")
                results.append(recommendation(game, seeds, filters))
            return version, results


def filter_sql(filters: Filters) -> tuple[list[str], dict[str, Any]]:
    clauses = []
    params: dict[str, Any] = {}
    if filters.free_only:
        clauses.append("p.free_to_play is true")
    if filters.min_price_cents is not None:
        clauses.append("p.region='US' and p.currency='USD' and p.amount_cents >= :minimum_budget")
        params["minimum_budget"] = filters.min_price_cents
    if filters.max_price_cents is not None:
        operator = "<" if filters.price_operator == "lt" else "<="
        clauses.append(f"p.region='US' and p.currency='USD' and p.amount_cents {operator} :budget")
        params["budget"] = filters.max_price_cents
    if filters.platforms:
        params["platforms"] = filters.platforms
        if filters.platform_match == "all":
            clauses.append("""(select count(distinct platform) from discovery.game_platforms s
                where s.version=g.version and s.app_id=g.app_id and s.supported is true and s.platform=any(:platforms))
                = cardinality(cast(:platforms as text[]))""")
        else:
            clauses.append("""exists(select 1 from discovery.game_platforms s where s.version=g.version
                and s.app_id=g.app_id and s.supported is true and s.platform=any(:platforms))""")
    if filters.required_modes:
        params["modes"] = filters.required_modes
        clauses.append("""(select count(distinct term) from discovery.game_terms t where t.version=g.version and t.app_id=g.app_id
            and t.kind='mode' and t.term=any(:modes)) = cardinality(cast(:modes as text[]))""")
    if filters.unwanted_terms:
        params["unwanted"] = [term.casefold() for term in filters.unwanted_terms]
        clauses.append("""not exists(select 1 from discovery.game_terms t where t.version=g.version and t.app_id=g.app_id
            and t.kind in ('genre','tag') and t.term=any(:unwanted))""")
    if filters.required_genres:
        params["genres"] = filters.required_genres
        clauses.append("""(select count(distinct term) from discovery.game_terms t where t.version=g.version and t.app_id=g.app_id
            and t.kind='genre' and t.term=any(:genres)) = cardinality(cast(:genres as text[]))""")
    return clauses, params
