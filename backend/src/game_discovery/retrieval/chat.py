"""Chat-only retrieval foundation; no provider, memory or main-discovery inputs."""

from typing import Protocol

from sqlalchemy.exc import SQLAlchemyError

from game_discovery.catalog.contracts import Filters
from game_discovery.catalog.repository import CatalogFailure
from game_discovery.retrieval.contracts import (
    CandidatePools, Channel, DegradedReason, RankedCandidate, RetrievalOutcome, RetrievalResult, TitleLookup,
)
from game_discovery.retrieval.query import QueryEncoder, QueryEncoderBusy, validate_query_vector

RRF_CONSTANT = 60
EVIDENCE_LIMIT = 8
RANKING_VERSION = "chat-rrf-v1"


class ChatRepository(Protocol):
    def chat_title(self, query: str, reference_id: int | None = None) -> TitleLookup: ...

    def chat_candidates(self, query: str, filters: Filters, query_vector: list[float] | None = None,
                        encoder_version: str | None = None) -> CandidatePools: ...


def fuse(pools: CandidatePools) -> tuple[RankedCandidate, ...]:
    if len(pools.lexical) > 20 or len(pools.semantic) > 20:
        raise ValueError("Retrieval channel exceeds its bound")
    if (len({game.app_id for game in pools.lexical}) != len(pools.lexical)
            or len({game.app_id for game, _ in pools.semantic}) != len(pools.semantic)):
        raise ValueError("Duplicate channel identities")
    lexical = {game.app_id: (rank, game) for rank, game in enumerate(pools.lexical, 1)}
    semantic = {game.app_id: (rank, game, score) for rank, (game, score) in enumerate(pools.semantic, 1)}
    result = []
    for app_id in lexical.keys() | semantic.keys():
        left, right = lexical.get(app_id), semantic.get(app_id)
        if left and right and left[1] != right[1]:
            raise ValueError("Conflicting canonical channel evidence")
        result.append(RankedCandidate(
            game=left[1] if left else semantic[app_id][1],
            rrf_score=(1 / (RRF_CONSTANT + left[0]) if left else 0)
                      + (1 / (RRF_CONSTANT + right[0]) if right else 0),
            lexical_rank=left[0] if left else None, semantic_rank=right[0] if right else None,
            cosine_similarity=right[2] if right else None,
        ))
    return tuple(sorted(result, key=lambda item: (-item.rrf_score, item.game.app_id)))


class ChatRetriever:
    def __init__(self, repository: ChatRepository, encoder: QueryEncoder | None):
        self.repository = repository
        self.encoder = encoder

    def lookup_title(self, query: str, reference_id: int | None = None) -> RetrievalResult:
        if len(query) > 200 or (not query.strip() and reference_id is None):
            raise ValueError("A bounded title or canonical reference is required")
        try:
            lookup = self.repository.chat_title(query, reference_id)
        except (CatalogFailure, SQLAlchemyError):
            return self.unavailable()
        compatible = self.encoder is not None and self.encoder.catalog_version == lookup.catalog_version
        candidates = tuple(RankedCandidate(game, 0.0) for game in lookup.games)
        return RetrievalResult(lookup.catalog_version, RetrievalOutcome(
            kind=lookup.match.kind, channels=["title"], semantic_available=compatible,
            title_search_complete=True, evidence_ids=[item.game.app_id for item in candidates]),
            candidates=candidates, suggestions=lookup.match.suggestions)

    def recommend(self, query: str, filters: Filters | None = None) -> RetrievalResult:
        if not query.strip() or len(query) > 1000:
            raise ValueError("A bounded nonblank chat query is required")
        filters = filters or Filters()
        if len(filters.excluded_ids) > 100:
            raise ValueError("Too many chat exclusions")
        reason: DegradedReason | None = None
        vector = None
        if self.encoder is None:
            reason = "encoder_missing"
        else:
            try:
                vector = self.encoder(query)
                validate_query_vector(vector)
            except QueryEncoderBusy:
                reason = "encoder_busy"
                vector = None
            except Exception:
                # No raw query, native exception/path or provider details logged.
                reason = "encoder_failed"
                vector = None
        try:
            pools = self.repository.chat_candidates(query, filters, vector,
                                                    self.encoder.catalog_version if self.encoder else None)
        except (CatalogFailure, SQLAlchemyError):
            return self.unavailable()
        if pools.artifact_mismatch:
            reason = "artifact_mismatch"
        ranked = fuse(pools)
        channels: list[Channel] = []
        if pools.lexical_used:
            channels.append("lexical")
        if pools.semantic_used:
            channels.append("semantic")
        candidates = ranked[:EVIDENCE_LIMIT]
        return RetrievalResult(pools.catalog_version, RetrievalOutcome(
            kind="found" if candidates else "no_recommendation_match", channels=channels,
            semantic_available=pools.semantic_used, degraded_reason=reason,
            evidence_ids=[item.game.app_id for item in candidates]), candidates=candidates,
            lexical_ids=tuple(game.app_id for game in pools.lexical),
            semantic_ids=tuple(game.app_id for game, _ in pools.semantic),
            fused_ranks=tuple((item.game.app_id, item.rrf_score) for item in ranked))

    @staticmethod
    def unavailable() -> RetrievalResult:
        return RetrievalResult(None, RetrievalOutcome(kind="retrieval_unavailable"))
