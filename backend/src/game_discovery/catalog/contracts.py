"""Versioned catalog contracts. Unknown source facts remain None."""

import hashlib
import json
import math
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
Platform = Literal["windows", "mac", "linux"]
Mode = Literal["single-player", "multiplayer", "online-co-op", "local-co-op"]
AppId = Annotated[int, Field(gt=0, le=2147483647)]
Term = Annotated[str, Field(min_length=1, max_length=100)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(StrictModel):
    url: str = Field(max_length=2048)
    collected_at: datetime
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class Evidence(StrictModel):
    id: str
    field: str
    value: str | int | bool | list[str]
    source: Source


class Price(StrictModel):
    amount_cents: int = Field(ge=0)
    currency: Literal["USD"] = "USD"
    region: Literal["US"] = "US"
    observed_at: datetime
    evidence_id: str


class Game(StrictModel):
    app_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(max_length=16000)
    store_url: str
    artwork_url: str | None = None
    eligibility: Literal["eligible", "excluded", "quarantined"]
    eligibility_reason: str
    early_access: bool | None = None
    platforms: dict[Platform, bool | None]
    genres: list[str] = Field(default_factory=list, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=100)
    modes: list[Mode] = Field(default_factory=list)
    free_to_play: bool | None = None
    price: Price | None = None
    observed_at: datetime
    evidence: list[Evidence] = Field(max_length=100)
    semantic_hash: str

    @model_validator(mode="after")
    def evidence_integrity(self) -> "Game":
        ids = [item.id for item in self.evidence]
        if len(ids) != len(set(ids)) or (self.price and self.price.evidence_id not in ids):
            raise ValueError("Duplicate or missing evidence reference")
        if self.semantic_hash != semantic_hash(self):
            raise ValueError("Semantic content hash mismatch")
        if self.observed_at.utcoffset() is None:
            raise ValueError("Observation timestamp must include timezone")
        return self


def semantic_text(game: Game) -> str:
    # Title and terms precede prose to survive the encoder's 256-token bound.
    return (f"{game.title}. Genres: {', '.join(game.genres)}. Tags: {', '.join(game.tags)}. "
            f"Play modes: {', '.join(game.modes)}. {game.description}")[:16000]


def semantic_hash(game: Game) -> str:
    return hashlib.sha256(semantic_text(game).encode()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Embedding(StrictModel):
    app_id: int = Field(gt=0)
    semantic_hash: str
    vector: list[float] = Field(min_length=384, max_length=384)

    @model_validator(mode="after")
    def normalized(self) -> "Embedding":
        if not all(math.isfinite(value) for value in self.vector):
            raise ValueError("Nonfinite embedding")
        if abs(sum(value * value for value in self.vector) - 1) > 0.001:
            raise ValueError("Embedding must have unit norm")
        return self


class Filters(StrictModel):
    max_price_cents: int | None = Field(default=None, ge=0, le=1000000)
    price_operator: Literal["lte", "lt"] = "lte"
    free_only: bool = False
    platforms: list[Platform] = Field(default_factory=list, max_length=3)
    platform_match: Literal["any", "all"] = "any"
    required_modes: list[Mode] = Field(default_factory=list, max_length=4)
    preferred_terms: list[Term] = Field(default_factory=list, max_length=30)
    unwanted_terms: list[Term] = Field(default_factory=list, max_length=30)
    excluded_ids: list[AppId] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def unique_controls(self) -> "Filters":
        self.platforms = list(dict.fromkeys(self.platforms))
        self.required_modes = list(dict.fromkeys(self.required_modes))
        self.preferred_terms = sorted({term.strip().casefold() for term in self.preferred_terms if term.strip()})
        self.unwanted_terms = sorted({term.strip().casefold() for term in self.unwanted_terms if term.strip()})
        return self


class DiscoverRequest(StrictModel):
    favorite_ids: list[AppId] = Field(default_factory=list, max_length=50)
    filters: Filters = Field(default_factory=Filters)
    limit: int = Field(default=10, ge=1, le=20)


class Reason(StrictModel):
    text: str
    evidence_ids: list[str]


class Recommendation(StrictModel):
    game: Game
    reasons: list[Reason]
    tradeoffs: list[str]


class DiscoverResponse(StrictModel):
    request_id: str
    catalog_version: str
    ranking_version: Literal["seed-v1"] = "seed-v1"
    effective_criteria: Filters
    results: list[Recommendation]
    degraded_reasons: list[str] = Field(default_factory=lambda: ["Natural-language discovery is not enabled in M2."])
    suggested_refinements: list[str]
    timings_ms: dict[str, float]
