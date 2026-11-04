"""Versioned R3 chat wire boundary with an explicit legacy compatibility path."""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from game_discovery.ai.chat_contracts import ChatCriteria, ChatStateV2, ChatTurn
from game_discovery.ai.chat_memory import MemoryClarification, legacy_state
from game_discovery.ai.rag import ChatModel as ChatModel, ConversationalRAG
from game_discovery.catalog.contracts import AppId, ConversationMessage, Filters, Recommendation, StrictModel
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.retrieval.query import QueryEncoder


class ChatState(StrictModel):
    criteria: Filters = Field(default_factory=Filters)
    query: str = Field(default="", max_length=1000)
    excluded_ids: list[AppId] = Field(default_factory=list, max_length=100)
    shown_ids: list[AppId] = Field(default_factory=list, max_length=4)


class ChatStateV2Wire(ChatStateV2):
    # The domain has a convenience default; a public v2 request must opt in.
    version: Literal[2]


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    messages: list[ConversationMessage] = Field(default_factory=list, max_length=20)
    state: ChatState | ChatStateV2Wire = Field(default_factory=ChatState)

    @field_validator("state", mode="before")
    @classmethod
    def versioned_state(cls, value: object) -> ChatState | ChatStateV2Wire:
        if isinstance(value, (ChatState, ChatStateV2Wire)):
            return value
        if isinstance(value, dict):
            if "version" not in value:
                return ChatState.model_validate(value)
            if type(value["version"]) is int and value["version"] == 2:
                return ChatStateV2Wire.model_validate(value)
        raise ValueError("Unsupported chat state version; use a compatible client or New chat")

    @model_validator(mode="after")
    def bounded(self) -> "ChatRequest":
        if not self.message.strip() or sum(len(item.content) for item in self.messages) > 12000:
            raise ValueError("Chat needs a nonempty message and bounded context")
        return self


class ChatResponse(StrictModel):
    request_id: str
    message: str = Field(min_length=1, max_length=2000)
    games: list[Recommendation] = Field(default_factory=list, max_length=4)
    state: ChatState | ChatStateV2Wire
    notices: list[str] = Field(default_factory=list)
    catalog_version: str | None = None


def respond(body: ChatRequest, model: ChatModel, repo: CatalogRepository,
             encoder: QueryEncoder | None, request_id: str) -> ChatResponse:
    if isinstance(body.state, ChatStateV2Wire):
        result = ConversationalRAG(model, repo, encoder).invoke(ChatTurn(
            message=body.message, messages=body.messages, state=body.state))
        return ChatResponse(request_id=request_id, message=result.message, games=result.games,
            state=ChatStateV2Wire.model_validate(result.state.model_dump()),
            notices=result.notices, catalog_version=result.catalog_version)
    try:
        state = legacy_state(body.state.criteria, body.state.query, body.state.excluded_ids, body.state.shown_ids)
    except MemoryClarification as error:
        return ChatResponse(request_id=request_id, message=str(error), state=body.state)
    result = ConversationalRAG(model, repo, encoder).invoke(ChatTurn(
        message=body.message, messages=body.messages, state=state))
    # Preserve quarantined fields for old tabs, rather than silently erasing them
    # or inventing provenance that their envelope cannot retain. Reset clears both.
    updated = result.state
    legacy = updated.legacy_criteria
    criteria = legacy if legacy is not None and legacy != ChatCriteria() else updated.criteria
    legacy_exclusions = list(dict.fromkeys([*updated.legacy_excluded_ids, *(e.app_id for e in updated.exclusions)]))
    if len(legacy_exclusions) > 100:
        return ChatResponse(request_id=request_id, message="This older client cannot retain more chat exclusions. Start a new chat or use the updated session client.", state=body.state)
    return ChatResponse(request_id=request_id, message=result.message, games=result.games,
        state=ChatState(criteria=criteria, query=updated.legacy_query or updated.query,
                        excluded_ids=legacy_exclusions,
                        shown_ids=updated.shown_ids if result.games else updated.referenced_ids or updated.shown_ids),
        notices=result.notices, catalog_version=result.catalog_version)
