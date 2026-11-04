"""Durable guest archive. Capability tokens are hashed and never appear in URLs."""
import hashlib
import json
import secrets
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import Field
from sqlalchemy import Engine, text

from game_discovery.ai.provider import AIFailure
from game_discovery.catalog.contracts import StrictModel


class ConversationKey(StrictModel):
    conversation_id: UUID
    token: str = Field(min_length=43, max_length=43, pattern=r'^[A-Za-z0-9_-]{43}$', repr=False)


class ConversationTurn(ConversationKey):
    turn_id: UUID
    revision: int = Field(ge=0, strict=True)
    message: str = Field(min_length=1, max_length=2000)


class Archive(Protocol):
    def create(self, events: list[dict[str, Any]] | None = None, key: ConversationKey | None = None) -> ConversationKey: ...
    def read(self, key: ConversationKey) -> dict[str, Any]: ...
    def begin(self, turn: ConversationTurn) -> dict[str, Any]: ...
    def finish(self, turn: ConversationTurn, result: dict[str, Any] | None,
               memory: dict[str, Any], trace: list[dict[str, Any]]) -> None: ...
    def delete(self, key: ConversationKey) -> bool: ...


class ConversationStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def auth(key: ConversationKey) -> dict[str, Any]:
        return {"cid": key.conversation_id, "secret": hashlib.sha256(key.token.encode()).hexdigest()}

    def call(self, sql: str, params: dict[str, Any]) -> Any:
        with self.engine.begin() as connection:
            connection.execute(text("SET LOCAL statement_timeout='3s'"))
            connection.execute(text("SET LOCAL lock_timeout='1s'"))
            result = connection.execute(text(sql), params).scalar_one_or_none()
        if isinstance(result, dict) and result.get("error"):
            raise AIFailure(result["error"])
        return result

    def create(self, events: list[dict[str, Any]] | None = None, key: ConversationKey | None = None) -> ConversationKey:
        key = key or ConversationKey(conversation_id=uuid4(), token=secrets.token_urlsafe(32))
        if not self.call("select discovery.conversation_create(:cid,:secret,cast(:events as jsonb))",
                         self.auth(key) | {"events": json.dumps(events or [])}):
            raise AIFailure("chat_archive_full")
        return key

    def read(self, key: ConversationKey) -> dict[str, Any]:
        result = self.call("select discovery.conversation_read(:cid,:secret)", self.auth(key))
        if not isinstance(result, dict):
            raise AIFailure("chat_session_missing")
        return result

    def begin(self, turn: ConversationTurn) -> dict[str, Any]:
        result = self.call("select discovery.conversation_begin(:cid,:secret,:rid,:expected,:message)",
            self.auth(turn) | {"rid": turn.turn_id, "expected": turn.revision, "message": turn.message})
        if not isinstance(result, dict):
            raise AIFailure("chat_session_missing")
        return result

    def finish(self, turn: ConversationTurn, result: dict[str, Any] | None,
               memory: dict[str, Any], trace: list[dict[str, Any]]) -> None:
        ok = self.call("select discovery.conversation_finish(:cid,:secret,:rid,cast(:result as jsonb),cast(:memory as jsonb),cast(:trace as jsonb))",
            self.auth(turn) | {"rid": turn.turn_id, "result": json.dumps(result) if result is not None else None,
                              "memory": json.dumps(memory), "trace": json.dumps(trace)})
        if not ok:
            raise AIFailure("chat_archive_full")

    def delete(self, key: ConversationKey) -> bool:
        return self.call("select discovery.conversation_delete(:cid,:secret)", self.auth(key)) is True
