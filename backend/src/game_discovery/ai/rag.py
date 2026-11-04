"""Finite, synchronous conversational RAG over the existing metered transport.

No agents, batching, retries, parallel calls, hosted traces or database memory.
The sequence has replaceable named domain stages, not a second provider client.
"""

import time
import re
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler, CallbackManager
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langsmith import tracing_context
from pydantic import ValidationError

from game_discovery.ai.chat_contracts import ChatAnswer, ChatResult, ChatStateV2, ChatTurn, Origin, RememberedExclusion, TurnPlan
from game_discovery.ai.chat_evidence import (
    GENERATE, INTERPRET, EvidencePacket, evidence_packet, interpretation_packet, natural_message,
)
from game_discovery.ai.chat_memory import MemoryClarification, apply_plan, has_legacy
from game_discovery.ai.provider import AIFailure, validate_claims
from game_discovery.catalog.contracts import Filters, Game, Recommendation
from game_discovery.catalog.discovery import satisfies
from game_discovery.catalog.repository import CatalogFailure, CatalogRepository
from game_discovery.retrieval.chat import ChatRetriever
from game_discovery.retrieval.contracts import RetrievalOutcome, RetrievalResult
from game_discovery.retrieval.query import QueryEncoder

logger = logging.getLogger(__name__)
SAFE_FAILURE_CODES = {
    "ai_daily_calls", "ai_daily_units", "ai_minute_limit", "ai_busy", "ai_provider_limited", "ai_timeout",
    "ai_provider_configuration", "ai_provider_unavailable", "ai_accounting_unavailable", "ai_budget_unavailable",
    "ai_output_limit", "ai_invalid_answer", "chat_required_context_limit", "chat_required_evidence_limit",
    "chat_answer_context_limit", "chat_invalid_prose", "chat_candidate_integrity", "chat_invented_selection",
    "chat_incomplete_sequence", "chat_incomplete_stages",
}


class ChatModel(Protocol):
    def complete(self, instruction: str, data: object) -> object: ...


@dataclass
class TurnFrame:
    turn: ChatTurn
    plan: TurnPlan | None = None
    state: ChatStateV2 | None = None
    filters: Filters = field(default_factory=Filters)
    query: str = ""
    retrieval: RetrievalResult | None = None
    packet: EvidencePacket | None = None
    answer: ChatAnswer | None = None
    result: ChatResult | None = None
    mismatch_notes: list[str] = field(default_factory=list)


class StageTimings(BaseCallbackHandler):
    """Request-local names/timings only. Never retain callback inputs or errors."""

    run_inline = True

    def __init__(self) -> None:
        self.started: dict[UUID, tuple[str, float]] = {}
        self.timings_ms: dict[str, float] = {}
        self.failed_stage: str | None = None

    def on_chain_start(self, serialized: dict[str, Any] | None, inputs: Any,
                       *, run_id: UUID, name: str | None = None, **kwargs: Any) -> None:
        if name in {"interpret", "remember", "retrieve", "evidence", "generate", "validate"}:
            self.started[run_id] = (name, time.perf_counter())

    def on_chain_end(self, outputs: Any, *, run_id: UUID, **kwargs: Any) -> None:
        item = self.started.pop(run_id, None)
        if item:
            self.timings_ms[item[0]] = round((time.perf_counter() - item[1]) * 1000, 3)

    def on_chain_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        if run_id in self.started:
            self.failed_stage = self.started[run_id][0]
        self.on_chain_end(None, run_id=run_id)


def mismatch_notes(game: Game, filters: Filters) -> list[str]:
    """Backend facts, not a provider's suitability judgment."""
    notes = []
    if game.app_id in filters.excluded_ids:
        notes.append("It is excluded from recommendations in this chat, but can still be inspected.")
    if filters.required_modes and not set(filters.required_modes).issubset(game.modes):
        notes.append("Recorded play modes: " + (", ".join(game.modes) or "not recorded") +
                     ". It does not meet the required " + ", ".join(filters.required_modes) + " play modes.")
    if filters.platforms:
        flags = [game.platforms.get(p) is True for p in filters.platforms]
        if not (all(flags) if filters.platform_match == "all" else any(flags)):
            notes.append("The catalog does not confirm the required " + ", ".join(filters.platforms) + " platform support.")
    if filters.required_genres and not set(filters.required_genres).issubset(game.genres):
        notes.append("Its recorded genres do not include all your required genres.")
    price_filters = Filters(min_price_cents=filters.min_price_cents, max_price_cents=filters.max_price_cents,
                            price_operator=filters.price_operator, free_only=filters.free_only)
    if not satisfies(game, price_filters, set()):
        notes.append("Its recorded price/free-to-play facts do not satisfy your budget conditions; see the dated card.")
    if set(filters.unwanted_terms) & set(game.genres + game.tags):
        notes.append("Its recorded genres/tags include a term you asked to avoid.")
    return notes


class ConversationalRAG:
    def __init__(self, model: ChatModel, repository: CatalogRepository, encoder: QueryEncoder | None):
        self.model, self.repository = model, repository
        self.retriever = ChatRetriever(repository, encoder)
        self.chain: RunnableSequence[TurnFrame, TurnFrame] = RunnableSequence(*[
            RunnableLambda(stage, name=stage.__name__)
            for stage in (self.interpret, self.remember, self.retrieve, self.evidence, self.generate, self.validate)])

    def invoke(self, turn: ChatTurn, observer: StageTimings | None = None) -> ChatResult:
        observer = observer or StageTimings()
        # Explicit local callback manager + disabled tracing defeats inherited env
        # switches without editing process-wide environment or retaining raw data.
        callbacks = CallbackManager(handlers=[observer], inheritable_handlers=[observer])
        try:
            with tracing_context(enabled=False, parent=False):
                frame = self.chain.invoke(TurnFrame(turn), config={"callbacks": callbacks, "max_concurrency": 1})
        except ValidationError as error:
            # Structure diagnostics only: no raw output, transcript or catalog text.
            issues = [item["type"] for item in error.errors(include_input=False, include_context=False)]
            logger.warning("chat_validation_failed stage=%s issues=%s", observer.failed_stage, issues)
            raise
        except AIFailure as error:
            logger.warning("chat_generation_failed stage=%s code=%s", observer.failed_stage,
                           error.code if error.code in SAFE_FAILURE_CODES else "unexpected_error")
            raise
        if frame.result is None:
            raise AIFailure("chat_incomplete_sequence")
        return frame.result

    @staticmethod
    def clarify(frame: TurnFrame, message: str, retrieval: RetrievalResult | None = None) -> TurnFrame:
        # An ambiguous or invalid operation never partially commits preferences.
        frame.result = ChatResult(message=message, state=frame.turn.state,
                                  catalog_version=retrieval.catalog_version if retrieval else None,
                                  retrieval=retrieval.outcome if retrieval else None)
        return frame

    def interpret(self, frame: TurnFrame) -> TurnFrame:
        if frame.turn.state.user_turn >= 1000000:
            return self.clarify(frame, "This conversation has reached its turn limit. Please start a new chat.")
        # The LLM resolves language and intent. Catalog identity and state changes
        # are validated below, never overridden by a keyword/regex language router.
        references = None
        ids = list(dict.fromkeys([*frame.turn.state.shown_ids, *frame.turn.state.referenced_ids]))
        if ids:
            try:
                references = self.repository.resolve(ids)
            except CatalogFailure:
                return self.known_outcome(frame, self.retriever.unavailable())
        frame.plan = TurnPlan.model_validate(self.model.complete(
            INTERPRET, interpretation_packet(frame.turn, references)))
        return frame

    def remember(self, frame: TurnFrame) -> TurnFrame:
        if frame.result or frame.plan is None:
            return frame
        plan = frame.plan
        if plan.kind == "clarify":
            # An unsupported requested platform is a capability boundary, not
            # missing encoder data, catalog absence, or an empty recommendation.
            unsupported = re.search(r"\b(?:playstation(?:\s*[345])?|ps[345]|xbox|nintendo\s+switch)\b",
                                    frame.turn.message, re.I)
            return self.clarify(frame, natural_message(plan.reply), self.retriever.unavailable() if unsupported else None)
        if plan.kind == "recommend" and has_legacy(frame.turn.state) and not plan.reset_preferences:
            return self.clarify(frame, "This older chat has preferences without confirmed origins. Please restate your requirements in a new chat, or say ‘start over’. Title and fact questions still work. Full preference memory requires the updated chat client.")
        try:
            memory = apply_plan(frame.turn.state, plan)
        except MemoryClarification as error:
            return self.clarify(frame, str(error))
        frame.state, frame.filters, frame.query = memory.state, memory.effective, memory.query
        if plan.exclusion_patch:
            remembered = {e.app_id: e for e in memory.state.exclusions}
            for operation in plan.exclusion_patch:
                target = operation.target
                reference = None
                if target.shown_position is not None:
                    shown = memory.state.shown_ids
                    if target.shown_position > len(shown):
                        return self.clarify(frame, "Which recently displayed game do you mean? Please use its title.")
                    reference = shown[target.shown_position - 1]
                found = self.retriever.lookup_title(target.title, reference)
                if found.outcome.kind != "found":
                    return self.known_outcome(frame, found, exclusion=True)
                app_id = found.candidates[0].game.app_id
                if operation.action == "add":
                    remembered[app_id] = RememberedExclusion(app_id=app_id, origin=Origin(user_turn=memory.state.user_turn))
                else:
                    remembered.pop(app_id, None)
            if len(remembered) > 100:
                return self.clarify(frame, "This chat has reached its exclusion limit. Remove a title or start a new chat.")
            memory.state.exclusions = list(remembered.values())
        # Resolve stored exclusions against the current active catalog in one
        # bounded read. Unknown IDs never enter SQL filters or provider packets.
        if memory.state.exclusions:
            resolved = self.repository.resolve([e.app_id for e in memory.state.exclusions])
            canonical = {game.app_id for game in resolved.items if game.eligibility == "eligible"}
            frame.filters.excluded_ids = sorted(canonical)
        return frame

    def known_outcome(self, frame: TurnFrame, result: RetrievalResult, exclusion: bool = False) -> TurnFrame:
        kind = result.outcome.kind
        if kind == "ambiguous":
            names = "; ".join(item.game.title for item in result.candidates[:4])
            message = "Which catalog title do you mean: " + names + "?"
        elif kind == "not_in_catalog":
            suggestions = "; ".join(item.title for item in result.suggestions[:4])
            message = "I couldn't find that title in this catalog. That does not mean it doesn't exist elsewhere."
            if suggestions:
                message += " Did you mean: " + suggestions + "?"
        elif kind == "retrieval_unavailable":
            message = "The catalog lookup is unavailable right now. I can't establish whether a title is present. Please try again later."
        else:
            message = "I couldn't find a catalog recommendation matching those conditions. I haven't relaxed your requirements. Would you like to change the type of game or a limit?"
        self.clarify(frame, message, result)
        if kind == "no_recommendation_match" and not exclusion and frame.state:
            frame.result = ChatResult(message=message, state=frame.state, catalog_version=result.catalog_version,
                                      retrieval=result.outcome, notices=self.notices(result))
        return frame

    def retrieve(self, frame: TurnFrame) -> TurnFrame:
        if frame.result or frame.plan is None or frame.state is None:
            return frame
        plan, state = frame.plan, frame.state
        if plan.kind == "social":
            frame.result = ChatResult(message=natural_message(plan.reply), state=state)
            return frame
        targets: list[tuple[str, int | None]] = []
        if plan.title_mentions:
            targets = [(title, None) for title in plan.title_mentions]
        elif plan.shown_positions:
            if any(position > len(state.shown_ids) for position in plan.shown_positions):
                return self.clarify(frame, "Which displayed games do you mean? Please use their titles.")
            targets = [("", state.shown_ids[position - 1]) for position in plan.shown_positions]
        elif plan.reference != "none":
            ids = state.shown_ids if plan.reference == "last_shown" else state.referenced_ids or state.shown_ids
            count = len(ids) if plan.reference == "last_shown" else 2 if plan.reference == "last_pair" else 1
            if not ids or len(ids) != count:
                return self.clarify(frame, "Which game" + ("s" if count == 2 else "") + " do you mean? Please use the title" + ("s." if count == 2 else "."))
            targets = [("", app_id) for app_id in ids]
        found = []
        for title, reference in targets:
            result = self.retriever.lookup_title(title, reference)
            if result.outcome.kind != "found":
                return self.known_outcome(frame, result)
            found.append(result)
        if found:
            if len({r.catalog_version for r in found}) != 1:
                return self.known_outcome(frame, self.retriever.unavailable())
            games = tuple(item for r in found for item in r.candidates)
            if len({item.game.app_id for item in games}) != len(games):
                return self.clarify(frame, "Please name two different catalog games for a comparison.")
            if plan.kind == "recommend":
                anchor = " ".join(item.game.title + ". " + item.game.description[:300] for item in games)
                frame.query = (plan.query.strip() or frame.query or anchor)[:1000]
            else:
                for item in games:
                    notes = mismatch_notes(item.game, frame.filters)
                    if notes:
                        frame.mismatch_notes.append(item.game.title + ": " + " ".join(notes))
                frame.retrieval = RetrievalResult(found[0].catalog_version, RetrievalOutcome(
                    kind="found_but_mismatch" if frame.mismatch_notes else "found", channels=["title"],
                    title_search_complete=True, semantic_available=all(r.outcome.semantic_available for r in found),
                    evidence_ids=[item.game.app_id for item in games]), candidates=games)
                return frame
        if plan.kind != "recommend":
            return self.clarify(frame, "Which catalog game would you like me to inspect?")
        if not frame.query.strip():
            return self.clarify(frame, "What kind of game would you like? Describe the experience or name a game to use as a reference.")
        result = self.retriever.recommend(frame.query, frame.filters)
        if result.outcome.kind != "found":
            return self.known_outcome(frame, result)
        # Repository defense in depth, including every hard predicate.
        valid = tuple(item for item in result.candidates if satisfies(item.game, frame.filters, set(frame.filters.excluded_ids)))
        if len(valid) != len(result.candidates):
            raise AIFailure("chat_candidate_integrity")
        frame.retrieval = result
        return frame

    def evidence(self, frame: TurnFrame) -> TurnFrame:
        if frame.result or frame.plan is None or frame.retrieval is None:
            return frame
        frame.packet = evidence_packet(frame.turn, frame.plan, frame.retrieval,
            frame.filters.model_dump(exclude_defaults=True), frame.mismatch_notes)
        return frame

    def generate(self, frame: TurnFrame) -> TurnFrame:
        if frame.result or frame.packet is None:
            return frame
        frame.answer = ChatAnswer.model_validate(self.model.complete(GENERATE, frame.packet.data))
        return frame

    def validate(self, frame: TurnFrame) -> TurnFrame:
        if frame.result:
            return frame
        if (frame.answer is None or frame.packet is None or frame.retrieval is None
                or frame.state is None or frame.plan is None):
            raise AIFailure("chat_incomplete_stages")
        answer, state, plan = frame.answer, frame.state, frame.plan
        packet_ids = {document.metadata["app_id"] for document in frame.packet.documents}
        available = {item.game.app_id: item.game for item in frame.retrieval.candidates if item.game.app_id in packet_ids}
        if (len(set(answer.game_ids)) != len(answer.game_ids) or set(answer.game_ids) - available.keys()
                or any(c.app_id not in answer.game_ids or (c.app_id, c.evidence_id, c.field) not in frame.packet.claimable
                       for c in answer.claims.claims)
                or any(sum(c.app_id == app_id for c in answer.claims.claims) > 2 for app_id in answer.game_ids)):
            raise AIFailure("chat_invented_selection")
        # Fact cards describe the title even when it is excluded/over budget.
        cards = [Recommendation(game=available[app_id], reasons=[], tradeoffs=[
            "Recorded prices may differ from today's Steam store price.",
            "Missing catalog evidence does not establish that an experience is absent."])
            for app_id in answer.game_ids]
        cards = validate_claims(answer.claims, cards)
        message = natural_message(answer.message)
        if frame.mismatch_notes:
            message += "\n\n" + "\n".join(frame.mismatch_notes)
        elif plan.evaluate_prior_requirements:
            active = frame.filters.model_dump(exclude_defaults=True, exclude={"preferred_terms"})
            message += ("\n\nThe recorded facts satisfy your confirmed hard chat conditions; subjective fit remains unverified."
                        if active else "\n\nThere are no confirmed hard chat requirements to evaluate yet.")
        if len(message) > 2000:
            # Never truncate away authoritative mismatch notes to fit prose.
            raise AIFailure("chat_answer_context_limit")
        if answer.game_ids:
            state.shown_ids = answer.game_ids
        if plan.kind != "recommend":
            resolved_ids = [item.game.app_id for item in frame.retrieval.candidates]
            # Keep the public v2 session contract; larger groups stay in shown_ids.
            state.referenced_ids = resolved_ids if len(resolved_ids) <= 2 else []
        else:
            # Most recent recommendation replaces stale fact references.
            state.referenced_ids = []
            if frame.query and frame.query != state.query:
                state.query = frame.query
                state.query_origin = Origin(user_turn=state.user_turn)
        outcome = frame.retrieval.outcome
        if plan.kind == "recommend" and not answer.game_ids:
            outcome = outcome.model_copy(update={"kind": "no_recommendation_match"})
        frame.result = ChatResult(message=message, games=cards, state=ChatStateV2.model_validate(state.model_dump()),
            notices=self.notices(frame.retrieval), catalog_version=frame.retrieval.catalog_version, retrieval=outcome)
        return frame

    @staticmethod
    def notices(result: RetrievalResult) -> list[str]:
        notices = ["US/USD recorded prices, not live quotes. Experience preferences are not catalog guarantees."]
        if result.outcome.degraded_reason:
            notices.append("Semantic matching is unavailable (" + result.outcome.degraded_reason.replace("_", " ") +
                           "); only the reported title/keyword channels were used.")
        return notices
