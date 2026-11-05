"""Versioned catalog contracts. Unknown source facts remain None."""

import hashlib
import json
import math
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

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


class ReleaseDate(StrictModel):
    raw: str = Field(max_length=100)
    precision: Literal['day', 'month', 'year', 'unknown']
    year: int | None = Field(default=None, ge=1, le=9999)
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)

    @model_validator(mode='after')
    def valid_precision(self) -> 'ReleaseDate':
        expected = {'day': (True, True, True), 'month': (True, True, False),
                    'year': (True, False, False), 'unknown': (False, False, False)}[self.precision]
        if tuple(value is not None for value in (self.year, self.month, self.day)) != expected:
            raise ValueError('Release date precision mismatch')
        if self.year is not None and self.month is not None and self.day is not None:
            date(self.year, self.month, self.day)
        return self


class ReviewSummary(StrictModel):
    label: str | None = Field(default=None, max_length=100)
    positive: int = Field(ge=0, strict=True)
    negative: int = Field(ge=0, strict=True)
    total: int = Field(ge=0, strict=True)
    scope: Literal['all-languages-all-purchases-offtopic-filtered-v1'] = 'all-languages-all-purchases-offtopic-filtered-v1'
    source: Source

    @model_validator(mode='after')
    def counts_agree(self) -> 'ReviewSummary':
        if self.positive + self.negative != self.total:
            raise ValueError('Review counts mismatch')
        return self


class DashboardMetadata(StrictModel):
    """Separate immutable document: never added to legacy Game/API/assistant payloads."""

    schema_version: Literal[1] = 1
    app_id: AppId
    developers: list[Annotated[str, Field(min_length=1, max_length=300)]] | None = Field(default=None, max_length=100)
    release_date: ReleaseDate | None = None
    original_price_cents: int | None = Field(default=None, ge=0, le=2147483647, strict=True)
    currency: Literal['USD'] = 'USD'
    region: Literal['US'] = 'US'
    # Preserve impossible recorded integers for the dashboard's invalid-data count.
    discount_percent: int | None = Field(default=None, strict=True)
    reviews: ReviewSummary | None = None
    evidence: list[Evidence] = Field(default_factory=list, max_length=10)

    @model_validator(mode='after')
    def field_evidence(self) -> 'DashboardMetadata':
        fields = {item.field: item for item in self.evidence}
        if len(fields) != len(self.evidence) or len({item.id for item in self.evidence}) != len(self.evidence):
            raise ValueError('Duplicate metadata evidence')
        for key in ('developers', 'original_price_cents', 'discount_percent'):
            value = getattr(self, key)
            if value is not None and (key not in fields or fields[key].value != value):
                raise ValueError('Missing or conflicting metadata evidence')
        if self.release_date is not None and ('release_date_raw' not in fields or fields['release_date_raw'].value != self.release_date.raw):
            raise ValueError('Missing release date evidence')
        return self


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
    min_price_cents: int | None = Field(default=None, ge=0, le=1000000)
    max_price_cents: int | None = Field(default=None, ge=0, le=1000000)
    price_operator: Literal["lte", "lt"] = "lte"
    free_only: bool = False
    platforms: list[Platform] = Field(default_factory=list, max_length=3)
    platform_match: Literal["any", "all"] = "any"
    required_modes: list[Mode] = Field(default_factory=list, max_length=4)
    required_genres: list[Term] = Field(default_factory=list, max_length=30)
    preferred_terms: list[Term] = Field(default_factory=list, max_length=30)
    unwanted_terms: list[Term] = Field(default_factory=list, max_length=30)
    excluded_ids: list[AppId] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def unique_controls(self) -> "Filters":
        supplied = self.model_fields_set.copy()
        self.platforms = list(dict.fromkeys(self.platforms))
        self.required_modes = list(dict.fromkeys(self.required_modes))
        self.required_genres = sorted({term.strip().casefold() for term in self.required_genres if term.strip()})
        self.preferred_terms = sorted({term.strip().casefold() for term in self.preferred_terms if term.strip()})
        self.unwanted_terms = sorted({term.strip().casefold() for term in self.unwanted_terms if term.strip()})
        if self.min_price_cents is not None and self.max_price_cents is not None and self.min_price_cents > self.max_price_cents:
            raise ValueError("Minimum recorded price must not exceed maximum recorded price")
        if self.free_only and self.min_price_cents is not None and self.min_price_cents > 0:
            raise ValueError("Free-only discovery cannot have a positive minimum price")
        # Normalization must not turn omitted controls into explicit overrides.
        self.model_fields_set.intersection_update(supplied)
        return self


class Feedback(StrictModel):
    app_id: AppId
    kind: Literal["interested", "not-for-me", "already-played"]
    timestamp: AwareDatetime


class ConversationMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class Conversation(StrictModel):
    messages: list[ConversationMessage] = Field(default_factory=list, max_length=20)
    criteria: Filters = Field(default_factory=Filters)

    @model_validator(mode="after")
    def bounded_context(self) -> "Conversation":
        if sum(len(message.content) for message in self.messages) > 12000:
            raise ValueError("Conversation context is too large")
        return self


class DiscoverRequest(StrictModel):
    query: str = Field(default="", max_length=2000)
    favorite_ids: list[AppId] = Field(default_factory=list, max_length=50)
    filters: Filters = Field(default_factory=Filters)
    preferences: Filters = Field(default_factory=Filters)
    feedback: list[Feedback] = Field(default_factory=list, max_length=500)
    conversation: Conversation = Field(default_factory=Conversation)
    resolution: Literal["controls", "text"] | None = None
    limit: int = Field(default=10, ge=1, le=20)

    @model_validator(mode="after")
    def valid_effective_price_range(self) -> "DiscoverRequest":
        # Validate after merging too: each partial filter may be valid on its own.
        self.effective_filters()
        return self

    def effective_filters(self) -> Filters:
        # Explicit defaults (false, [], null) clear a saved value. Omitted fields inherit it.
        return Filters.model_validate({**self.conversation.criteria.model_dump(),
                                      **self.preferences.model_dump(exclude_unset=True),
                                      **self.filters.model_dump(exclude_unset=True)})

    def ranking_text(self) -> str:
        # Recent user intent only: assistant prose is never treated as a request.
        previous = [item.content for item in self.conversation.messages if item.role == "user"]
        return " ".join([*previous, self.query.strip()])[-2000:].strip()

    def latest_feedback(self) -> list[Feedback]:
        latest: dict[int, Feedback] = {}
        for item in self.feedback:
            if item.app_id not in latest or item.timestamp >= latest[item.app_id].timestamp:
                latest[item.app_id] = item
        return [latest[app_id] for app_id in sorted(latest)]

    def excluded_ids(self) -> set[int]:
        return (set(self.favorite_ids + self.effective_filters().excluded_ids)
                | {item.app_id for item in self.latest_feedback() if item.kind != "interested"})


class Reason(StrictModel):
    text: str
    evidence_ids: list[str]


class Recommendation(StrictModel):
    game: Game
    reasons: list[Reason]
    tradeoffs: list[str]


class CriteriaConflict(StrictModel):
    field: str
    current: str
    proposed: str


class DiscoveryCapabilities(StrictModel):
    semantic_query_matching: bool = False
    ai_interpretation: bool = False
    ai_explanations: bool = False


class DiscoverResponse(StrictModel):
    request_id: str
    catalog_version: str
    ranking_version: Literal["seed-feedback-v1", "hybrid-text-v1"] = "seed-feedback-v1"
    effective_criteria: Filters
    unresolved_preferences: list[str] = Field(default_factory=list)
    conflicts: list[CriteriaConflict] = Field(default_factory=list)
    proposed_criteria: Filters | None = None
    effective_query: str = ""
    assistant_message: str = ""
    prompt_version: str = "interpret-claims-v1"
    capabilities: DiscoveryCapabilities = Field(default_factory=DiscoveryCapabilities)
    results: list[Recommendation]
    degraded_reasons: list[str] = Field(default_factory=lambda: ["Natural-language discovery is not enabled yet."])
    suggested_refinements: list[str]
    timings_ms: dict[str, float]
