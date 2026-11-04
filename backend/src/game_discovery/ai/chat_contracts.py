"""Serving-domain contracts adapted from R0; exposed via the R3 wire boundary.

Shape validation does not authenticate client provenance or model intent.
"""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from game_discovery.catalog.contracts import AppId, ConversationMessage, Filters, Recommendation, StrictModel
from game_discovery.ai.provider import Claims
from game_discovery.retrieval.contracts import RetrievalOutcome

CriterionKey = Literal["min_price_cents", "max_price_cents", "price_operator", "free_only",
    "platforms", "platform_match", "required_modes", "required_genres", "preferred_terms", "unwanted_terms"]
FactField = Literal["description", "platforms", "modes", "genres", "tags", "early_access", "recorded_price"]


class ChatAnswer(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    game_ids: list[AppId] = Field(default_factory=list, max_length=4)
    claims: Claims = Field(default_factory=lambda: Claims(claims=[]))


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
    title_mentions: list[str] = Field(default_factory=list, max_length=4)
    reference: Literal["none", "last_game", "last_pair", "last_shown"] = "none"
    shown_positions: list[Annotated[int, Field(strict=True, ge=1, le=4)]] = Field(default_factory=list, max_length=4)
    requested_facts: list[FactField] = Field(default_factory=list, max_length=7)
    criteria_patch: list[CriteriaPatch] = Field(default_factory=list, max_length=2)
    evaluate_prior_requirements: bool = False
    exclusion_patch: list[ExclusionPatch] = Field(default_factory=list, max_length=8)
    reset_preferences: bool = False

    @model_validator(mode="after")
    def bounded_semantics(self) -> "TurnPlan":
        if any(not t.strip() or len(t) > 200 for t in self.title_mentions):
            raise ValueError("Invalid title mention")
        if (len(self.shown_positions) != len(set(self.shown_positions)) or
                any(type(p) is not int or not 1 <= p <= 4 for p in self.shown_positions)):
            raise ValueError("Use unique displayed positions from one through four")
        if sum((bool(self.title_mentions), self.reference != "none", bool(self.shown_positions))) > 1:
            raise ValueError("Use explicit titles, displayed positions or a reference, not a mixture")
        if self.kind in {"title_lookup", "game_facts", "compare"} and not (
                self.title_mentions or self.reference != "none" or self.shown_positions):
            raise ValueError("Catalog facts need a target")
        if self.kind in {"social", "clarify"} and (not self.reply.strip() or self.title_mentions or
                self.reference != "none" or self.shown_positions or self.requested_facts or self.evaluate_prior_requirements):
            raise ValueError("Nonretrieval reply cannot assert specific game facts")
        if self.evaluate_prior_requirements and self.kind not in {"title_lookup", "game_facts", "compare"}:
            raise ValueError("Suitability requires a resolved fact target")
        keys: list[str] = []
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


class ChatTurn(StrictModel):
    """Domain request behind the version-discriminating public wire boundary."""

    message: str = Field(min_length=1, max_length=2000)
    messages: list[ConversationMessage] = Field(default_factory=list, max_length=20)
    state: ChatStateV2 = Field(default_factory=ChatStateV2)

    @model_validator(mode="after")
    def bounded(self) -> "ChatTurn":
        if not self.message.strip() or sum(len(item.content) for item in self.messages) > 12000:
            raise ValueError("Chat needs a nonempty message and bounded context")
        return self


class ChatResult(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    games: list[Recommendation] = Field(default_factory=list, max_length=4)
    state: ChatStateV2
    notices: list[str] = Field(default_factory=list)
    catalog_version: str | None = None
    retrieval: RetrievalOutcome | None = None
