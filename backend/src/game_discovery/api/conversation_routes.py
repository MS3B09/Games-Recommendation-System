"""Versioned server-memory assistant API; old chat wire stays compatible."""
import threading
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import Field
from sqlalchemy.exc import SQLAlchemyError

from game_discovery.ai.conversation_store import Archive, ConversationKey, ConversationTurn
from game_discovery.ai.dialogue import Dialogue, DialogueModel
from game_discovery.ai.provider import AIFailure, ClientThrottle
from game_discovery.api.errors import ApiError, ai_error_code, error_response
from game_discovery.catalog.contracts import AppId, Filters, Recommendation, StrictModel
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.retrieval.query import QueryEncoder


class DialogueResponse(StrictModel):
    request_id: str
    message: str = Field(min_length=1, max_length=4000)
    games: list[Recommendation] = Field(default_factory=list, max_length=4)
    notices: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    applied_filters: Filters | None = None
    memory_changes: list[dict[str, Any]] = Field(default_factory=list)
    preference_changes: dict[str, Any] | None = None
    revision: int
    total_turns: int = 0


class HistoryRequest(ConversationKey):
    offset: int = Field(default=0, ge=0, strict=True)
    limit: int = Field(default=20, ge=1, le=50, strict=True)
    before: int | None = Field(default=None, ge=0, strict=True)


class HistoryResponse(StrictModel):
    revision: int
    total: int
    offset: int
    next_offset: int | None
    events: list[dict[str, Any]]


class ImportMessage(StrictModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)
    game_ids: list[AppId] = Field(default_factory=list, max_length=4)


class ConversationCreate(StrictModel):
    messages: list[ImportMessage] = Field(default_factory=list, max_length=20)
    key: ConversationKey | None = None


class ConversationCreated(ConversationKey):
    revision: int
    imported_messages: int = 0


def register_conversations(app: FastAPI, archive: Archive | None, model: DialogueModel | None,
                           repo: CatalogRepository | None, encoder: QueryEncoder | None,
                           slot: threading.BoundedSemaphore, throttle: ClientThrottle) -> None:
    create_throttle = ClientThrottle()

    def guarded(request: Request, action: Any) -> Any:
        try:
            if archive is None:
                raise AIFailure("chat_session_missing")
            return action(archive)
        except AIFailure as error:
            return error_response(request.state.request_id, ai_error_code(error.code), retry_at=error.retry_at)
        except (SQLAlchemyError, CatalogFailure):
            return error_response(request.state.request_id, "database_unavailable")
        except ValueError:
            return error_response(request.state.request_id, "chat_invalid_answer")

    @app.post('/api/v2/assistant/conversations', response_model=ConversationCreated, responses={503: {'model': ApiError}})
    def create(request: Request, body: ConversationCreate) -> Any:
        def action(store: Archive) -> ConversationCreated:
            if body.key is not None:
                try:
                    existing = store.read(body.key)
                except AIFailure as error:
                    if error.code != 'chat_session_missing':
                        raise
                else:
                    return ConversationCreated(**body.key.model_dump(), revision=existing['revision'])
            if not create_throttle.allow(request.client.host if request.client else 'unknown'):
                raise AIFailure('ai_minute_limit', retry_at=datetime.now(UTC) + timedelta(seconds=30))
            if sum(len(m.content) for m in body.messages) > 12000:
                raise ValueError('Import exceeds retained browser context')
            ids = list({i for message in body.messages for i in message.game_ids})
            if len(ids) > 12:
                raise ValueError('Import exceeds retained browser cards')
            canonical = {g.app_id: g for g in repo.resolve(ids).items} if repo is not None and ids else {}
            events: list[dict[str, Any]] = []
            for message in body.messages:
                if message.role == 'user':
                    events.append({'id': str(uuid4()), 'input': message.content, 'status': 'imported',
                                   'source': 'retained_browser_snapshot_not_full_original_history', 'attempts': []})
                else:
                    if not events or events[-1].get('output'):
                        events.append({'id': str(uuid4()), 'input': '', 'status': 'imported',
                                       'source': 'retained_browser_snapshot_not_full_original_history', 'attempts': []})
                    events[-1]['output'] = {'message': message.content, 'notices': [], 'evidence': [],
                        'games': [Recommendation(game=canonical[i], reasons=[], tradeoffs=[]).model_dump(mode='json')
                                  for i in message.game_ids if i in canonical]}
            key = store.create(events, body.key)
            return ConversationCreated(**key.model_dump(), revision=store.read(key)['revision'], imported_messages=len(body.messages))
        return guarded(request, action)

    @app.post('/api/v2/assistant/history', response_model=HistoryResponse)
    def history(request: Request, body: HistoryRequest) -> Any:
        def action(store: Archive) -> HistoryResponse:
            snapshot = store.read(body)
            # Failed/interrupted turns are part of the full original archive too.
            events = snapshot['document']['events']
            offset = body.offset if body.before is None else max(0, min(len(events), body.before) - body.limit)
            end = body.offset + body.limit if body.before is None else min(len(events), body.before)
            page = events[offset:end]
            return HistoryResponse(revision=snapshot['revision'], total=len(events), offset=offset,
                next_offset=offset + len(page) if offset + len(page) < len(events) else None, events=page)
        return guarded(request, action)

    @app.post('/api/v2/assistant/forget', response_model=bool)
    def forget(request: Request, body: ConversationKey) -> Any:
        return guarded(request, lambda store: store.delete(body))

    @app.post('/api/v2/assistant', response_model=DialogueResponse,
              responses={status: {'model': ApiError} for status in (404, 409, 422, 429, 502, 503, 504)})
    def converse(request: Request, body: ConversationTurn) -> Any:
        def action(store: Archive) -> DialogueResponse:
            if model is None or repo is None:
                raise AIFailure('ai_provider_configuration')
            if not body.message.strip():
                raise ValueError('Empty message')
            if not slot.acquire(blocking=False):
                raise AIFailure('ai_busy')
            try:
                snapshot = store.read(body)
                completed = next((e for e in snapshot['document']['events']
                    if e['id'] == str(body.turn_id) and e['status'] == 'done'), None)
                if completed:
                    if completed['input'] != body.message:
                        raise AIFailure('chat_session_conflict')
                    result = completed['output'] | {'revision': snapshot['revision']}
                else:
                    peer = request.client.host if request.client else 'unknown'
                    started = store.begin(body)
                    if 'cached' in started:
                        return DialogueResponse(request_id=request.state.request_id,
                                                **(started['cached'] | {'revision': started['revision']}))
                    if not throttle.allow(peer):
                        store.finish(body, None, started['document']['memory'], [{'failure': 'ai_minute_limit', 'stage': 'before_model'}])
                        raise AIFailure('ai_minute_limit', retry_at=datetime.now(UTC) + timedelta(seconds=throttle.remaining(peer)))
                    result = Dialogue(model, repo, store, encoder).run(body, started)
                return DialogueResponse(request_id=request.state.request_id, **result)
            finally:
                slot.release()
        return guarded(request, action)
