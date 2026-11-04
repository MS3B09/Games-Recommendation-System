"""Internal R1 retrieval contracts. These do not change the chat wire API."""

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from game_discovery.catalog.contracts import AppId, Game, StrictModel
from game_discovery.retrieval.titles import CatalogTitle, TitleMatch

Channel = Literal["title", "lexical", "semantic"]
DegradedReason = Literal["encoder_missing", "encoder_busy", "encoder_failed", "artifact_mismatch"]


class RetrievalOutcome(StrictModel):
    kind: Literal["found", "found_but_mismatch", "ambiguous", "not_in_catalog",
                  "no_recommendation_match", "retrieval_unavailable"]
    channels: list[Channel] = Field(default_factory=list, max_length=3)
    semantic_available: bool = False
    degraded_reason: DegradedReason | None = None
    title_search_complete: bool = False
    evidence_ids: list[AppId] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def honest_outcome(self) -> "RetrievalOutcome":
        if len(self.channels) != len(set(self.channels)) or len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("Duplicate retrieval channel or identity")
        if self.kind == "not_in_catalog" and (not self.title_search_complete or "title" not in self.channels):
            raise ValueError("Catalog absence requires a completed title search")
        if (("semantic" in self.channels and not self.semantic_available)
                or (self.semantic_available and self.degraded_reason)):
            raise ValueError("Semantic channel requires a compatible encoder")
        return self


@dataclass(frozen=True)
class TitleLookup:
    catalog_version: str
    match: TitleMatch
    games: tuple[Game, ...]


@dataclass(frozen=True)
class CandidatePools:
    catalog_version: str
    lexical: tuple[Game, ...]
    semantic: tuple[tuple[Game, float], ...]
    lexical_used: bool
    semantic_used: bool
    artifact_mismatch: bool = False


@dataclass(frozen=True)
class RankedCandidate:
    game: Game
    rrf_score: float
    lexical_rank: int | None = None
    semantic_rank: int | None = None
    cosine_similarity: float | None = None


@dataclass(frozen=True)
class RetrievalResult:
    catalog_version: str | None
    outcome: RetrievalOutcome
    candidates: tuple[RankedCandidate, ...] = ()
    suggestions: tuple[CatalogTitle, ...] = ()
    lexical_ids: tuple[int, ...] = ()
    semantic_ids: tuple[int, ...] = ()
    # Bounded local evaluation trace, not a public probability/confidence score.
    fused_ranks: tuple[tuple[int, float], ...] = ()
