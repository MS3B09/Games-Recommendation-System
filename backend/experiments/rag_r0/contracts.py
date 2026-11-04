"""Frozen R0 design contracts; NOT imported by serving code or OpenAPI.

R2/R3 must move/adapt these deliberately with their compatibility tests. This
prototype validates shapes/bounds, not factual intent or truthful provenance.
"""

from typing import Literal

from pydantic import Field, model_validator

from game_discovery.catalog.contracts import AppId, Filters, StrictModel

CriterionKey = Literal["min_price_cents", "max_price_cents", "price_operator", "free_only",
    "platforms", "platform_match", "required_modes", "required_genres", "preferred_terms", "unwanted_terms"]
FactField = Literal["description", "platforms", "modes", "genres", "tags", "early_access", "recorded_price"]


class ChatCriteria(Filters):
    @model_validator(mode="after")
    def no_hidden_exclusions(self) -> "ChatCriteria":
        if self.excluded_ids:
            raise ValueError("Chat exclusions have their own bounded field")
        return self


class CriteriaPatch(StrictModel):
    scope: Literal["turn", "conversation"]
    set: ChatCriteria = Field(default_factory=ChatCriteria)
    clear: list[CriterionKey] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def unambiguous(self) -> "CriteriaPatch":
        supplied = self.set.model_fields_set
        if "excluded_ids" in supplied or supplied.intersection(self.clear) or len(self.clear) != len(set(self.clear)):
            raise ValueError("Conflicting or unsupported criteria operations")
        return self


class TitleTarget(StrictModel):
    title: str = Field(default="", max_length=200)
    shown_position: int | None = Field(default=None, ge=1, le=4, strict=True)

    @model_validator(mode="after")
    def one_target(self) -> "TitleTarget":
        if bool(self.title.strip()) == (self.shown_position is not None):
            raise ValueError("Provide exactly one title or recent shown position, never a model-generated ID")
        return self


class ExclusionPatch(StrictModel):
    action: Literal["add", "remove"]
    target: TitleTarget


class TurnPlan(StrictModel):
    kind: Literal["social", "clarify", "title_lookup", "game_facts", "compare", "recommend"]
    reply: str = Field(default="", max_length=2000)
    query: str = Field(default="", max_length=1000)
    title_mentions: list[str] = Field(default_factory=list, max_length=2)
    reference: Literal["none", "last_game", "last_pair"] = "none"
    requested_facts: list[FactField] = Field(default_factory=list, max_length=7)
    criteria_patch: list[CriteriaPatch] = Field(default_factory=list, max_length=2)
    evaluate_prior_requirements: bool = False
    exclusion_patch: list[ExclusionPatch] = Field(default_factory=list, max_length=8)
    reset_preferences: bool = False

    @model_validator(mode="after")
    def bounded_semantics(self) -> "TurnPlan":
        if any(not t.strip() or len(t) > 200 for t in self.title_mentions):
            raise ValueError("Invalid title mention")
        if self.reference != "none" and self.title_mentions:
            raise ValueError("Use explicit titles or a reference, not both")
        if self.kind in {"title_lookup", "game_facts"} and not (
                len(self.title_mentions) == 1 or self.reference == "last_game"):
            raise ValueError("Single-title lookup needs one target")
        if self.kind == "compare" and not (len(self.title_mentions) == 2 or self.reference == "last_pair"):
            raise ValueError("Comparison needs two targets")
        if self.kind in {"social", "clarify"} and (not self.reply.strip() or self.title_mentions or
                self.reference != "none" or self.requested_facts or self.evaluate_prior_requirements):
            raise ValueError("Nonretrieval reply cannot assert specific game facts")
        if self.evaluate_prior_requirements and self.kind not in {"title_lookup", "game_facts", "compare"}:
            raise ValueError("Suitability requires a resolved fact target")
        keys = []
        for change in self.criteria_patch:
            keys.extend(change.set.model_fields_set | set(change.clear))
        if len(keys) != len(set(keys)):
            raise ValueError("A criterion cannot have competing scopes in one turn")
        return self


class Origin(StrictModel):
    user_turn: int = Field(ge=1, le=1000000, strict=True)
    scope: Literal["conversation"] = "conversation"


class RememberedExclusion(StrictModel):
    app_id: AppId
    origin: Origin


class ChatStateV2(StrictModel):
    version: Literal[2] = 2
    user_turn: int = Field(default=0, ge=0, le=1000000, strict=True)
    criteria: ChatCriteria = Field(default_factory=ChatCriteria)
    provenance: dict[CriterionKey, Origin] = Field(default_factory=dict, max_length=10)
    query: str = Field(default="", max_length=1000)
    query_origin: Origin | None = None
    exclusions: list[RememberedExclusion] = Field(default_factory=list, max_length=100)
    shown_ids: list[AppId] = Field(default_factory=list, max_length=4)
    referenced_ids: list[AppId] = Field(default_factory=list, max_length=2)
    # Unknown-provenance legacy inputs are quarantined, not active criteria.
    legacy_criteria: ChatCriteria | None = None
    legacy_query: str = Field(default="", max_length=1000)
    legacy_excluded_ids: list[AppId] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def provenance_bounds(self) -> "ChatStateV2":
        defaults = ChatCriteria().model_dump()
        active = {k for k, value in self.criteria.model_dump().items() if value != defaults[k]}
        if active - self.provenance.keys() or bool(self.query.strip()) != (self.query_origin is not None):
            raise ValueError("Active preferences need chat-user provenance")
        origins = [*self.provenance.values(), *(e.origin for e in self.exclusions)]
        if self.query_origin:
            origins.append(self.query_origin)
        if any(o.user_turn > self.user_turn for o in origins):
            raise ValueError("Origin cannot refer to a future turn")
        for values in (self.shown_ids, self.referenced_ids, self.legacy_excluded_ids,
                       [e.app_id for e in self.exclusions]):
            if len(values) != len(set(values)):
                raise ValueError("Duplicate state IDs")
        return self


class RetrievalOutcome(StrictModel):
    kind: Literal["found", "found_but_mismatch", "ambiguous", "not_in_catalog", "no_recommendation_match",
                  "retrieval_unavailable"]
    channels: list[Literal["title", "lexical", "semantic"]] = Field(default_factory=list, max_length=3)
    semantic_available: bool = False
    degraded_reason: Literal["encoder_missing", "encoder_busy", "encoder_failed", "artifact_mismatch"] | None = None
    title_search_complete: bool = False
    evidence_ids: list[AppId] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def truthful_capabilities(self) -> "RetrievalOutcome":
        if self.kind == "not_in_catalog" and (not self.title_search_complete or "title" not in self.channels):
            raise ValueError("A shortlist miss cannot establish catalog absence")
        if ("semantic" in self.channels and not self.semantic_available) or (self.semantic_available and self.degraded_reason):
            raise ValueError("Conflicting semantic capability")
        if len(self.channels) != len(set(self.channels)) or len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("Duplicate retrieval metadata")
        return self
