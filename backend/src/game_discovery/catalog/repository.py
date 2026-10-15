"""Bounded, parameterized PostgreSQL catalog access; active snapshot per transaction."""

import json
import math
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Connection, Engine, text

from game_discovery.catalog.contracts import DiscoverRequest, Filters, Game, Recommendation, StrictModel
from game_discovery.catalog.discovery import recommendation, satisfies


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


class CatalogRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    @contextmanager
    def snapshot(self) -> Iterator[tuple[Connection, str]]:
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout = '2s'"))
            elevated = connection.execute(text(
                "select rolsuper or rolcreatedb or rolcreaterole or rolbypassrls from pg_roles where rolname=current_user"
            )).scalar_one()
            if elevated:
                raise CatalogFailure("database_role_misconfigured")
            version = connection.execute(text("select version from discovery.catalog_versions where active")).scalar()
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

    def facets(self) -> Facets:
        with self.snapshot() as (connection, version):
            rows = connection.execute(text("select distinct kind,term from discovery.game_terms where version=:v order by kind,term"), {"v": version})
            terms: dict[str, list[str]] = {"genre": [], "tag": [], "mode": []}
            for kind, term in rows:
                terms[kind].append(term)
            platforms = connection.execute(text("select distinct platform from discovery.game_platforms where version=:v and supported order by platform"), {"v": version})
            return Facets(catalog_version=version, genres=terms["genre"], tags=terms["tag"], modes=terms["mode"], platforms=[row[0] for row in platforms])

    def discover(self, request: DiscoverRequest) -> tuple[str, list[Recommendation]]:
        with self.snapshot() as (connection, version):
            seeds = []
            vectors = []
            rows = connection.execute(text("""select g.document,cast(e.embedding as text) from discovery.games g
                join discovery.game_embeddings e using(version,app_id) where g.version=:v and g.app_id=any(:ids) order by g.app_id"""),
                {"v": version, "ids": request.favorite_ids})
            for document, vector in rows:
                seeds.append(Game.model_validate(document))
                vectors.append(json.loads(vector))
            if set(request.favorite_ids) - {game.app_id for game in seeds}:
                raise CatalogFailure("unknown_favorite")
            excluded = set(request.favorite_ids + request.filters.excluded_ids)
            clauses, params = filter_sql(request.filters)
            params.update(v=version, excluded=sorted(excluded), limit=request.limit)
            seed_score = "0.0"
            if vectors:
                average = [sum(values) / len(vectors) for values in zip(*vectors, strict=True)]
                norm = math.sqrt(sum(value * value for value in average))
                if norm < 1e-9:
                    raise CatalogFailure("invalid_seed_vector")
                params["vector"] = json.dumps([value / norm for value in average])
                seed_score = "1 - (e.embedding OPERATOR(extensions.<=>) cast(:vector as extensions.vector))"
            params["preferred"] = [term.casefold() for term in request.filters.preferred_terms]
            # Bounded preferred-term boost; stable ID breaks ties. No unsupported quality claims.
            score = f"({seed_score}) + 0.15 * (select count(distinct t.term)::float / greatest(cardinality(cast(:preferred as text[])),1) from discovery.game_terms t where t.version=g.version and t.app_id=g.app_id and t.kind in ('genre','tag') and t.term=any(:preferred))"
            rows = connection.execute(text(f"""select g.document from discovery.games g
                join discovery.game_embeddings e using(version,app_id)
                join discovery.game_prices p using(version,app_id)
                where g.version=:v and g.eligibility='eligible' and not (g.app_id=any(:excluded))
                and {' and '.join(clauses) if clauses else 'true'}
                order by {score} desc,g.app_id limit :limit"""), params)
            results = []
            for row in rows:
                game = Game.model_validate(row[0])
                if not satisfies(game, request.filters, excluded):
                    raise CatalogFailure("catalog_integrity_error")
                results.append(recommendation(game, seeds, request.filters))
            return version, results


def filter_sql(filters: Filters) -> tuple[list[str], dict[str, Any]]:
    clauses = []
    params: dict[str, Any] = {}
    if filters.free_only:
        clauses.append("p.free_to_play is true")
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
    return clauses, params
