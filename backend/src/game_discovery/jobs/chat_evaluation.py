"""R4 evaluation-only adapters. Never imported by serving code.

The baseline shares interpretation/memory/evidence/generation/validation policy,
but retrieves cosine top-five without title lookup, lexical matching or RRF.
Offline intent annotations are oracle inputs, not evaluated intent predictions.
"""

import hashlib
import json
import math
from pathlib import Path

from sqlalchemy import text

from game_discovery.ai.chat_contracts import ChatResult, ChatStateV2, TurnPlan
from game_discovery.ai.chat_evidence import INTERPRET, natural_message
from game_discovery.ai.provider import AIFailure, validate_claims
from game_discovery.ai.rag import ConversationalRAG, TurnFrame, mismatch_notes
from game_discovery.catalog.contracts import Filters, Recommendation
from game_discovery.catalog.discovery import satisfies
from game_discovery.catalog.repository import CatalogFailure, filter_sql
from game_discovery.retrieval.contracts import RankedCandidate, RetrievalOutcome, RetrievalResult

ROOT = Path(__file__).resolve().parents[4]
DATASET = ROOT / "data/evaluation/chat-rag.jsonl"
MANIFEST = ROOT / "data/evaluation/chat-rag-manifest.json"
POLICY = ROOT / "data/evaluation/chat-rag-r4-policy.json"
METHODS = ("proposed", "semantic_top5")
PILOT_CALLS = 12
PILOT_TOKENS = 159360


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(DATASET) != manifest["dataset_sha256"]:
        raise ValueError("frozen_dataset_hash_mismatch")
    cases = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    if (len(cases) != manifest["case_count"] or sum(len(c["turns"]) for c in cases) != manifest["turn_count"]
            or len({c["id"] for c in cases}) != len(cases)):
        raise ValueError("frozen_dataset_inventory_mismatch")
    return cases


def percentile(values, quantile=.95):
    return sorted(values)[max(0, math.ceil(len(values) * quantile) - 1)] if values else None


def oracle_plan(case, index, games, policy):
    """Explicit annotations derived from frozen expectations; no live prediction."""
    turn = case["turns"][index]
    expected = turn["expect"]
    key = f'{case["id"]}:{index + 1}'
    title = policy["title_queries"].get(key)
    kind = expected.get("kind", "recommend")
    if title:
        kind = "title_lookup" if kind == "clarify" else kind
    value = {"kind": kind}
    if kind == "clarify":
        value["reply"] = "The catalog cannot confirm the requested platform. Please choose Windows, macOS or Linux."
    elif kind in {"title_lookup", "game_facts"}:
        if expected.get("reference"):
            value["reference"] = expected["reference"]
        else:
            value["title_mentions"] = [title or games[expected["target_ids"][0]].title]
        value["requested_facts"] = ["modes", "platforms"]
        value["evaluate_prior_requirements"] = expected.get("evaluate_prior_requirements", False)
    else:
        value["query"] = turn["user"]
    if expected.get("constraints"):
        value["criteria_patch"] = [{"scope": expected.get("scope", "conversation"),
                                    "set": expected["constraints"]}]
    if expected.get("cleared_fields"):
        value["criteria_patch"] = [{"scope": "conversation", "clear": expected["cleared_fields"]}]
    if expected.get("reset_preferences"):
        value["reset_preferences"] = True
    operations = []
    if index == 0:
        operations.extend({"action": "add", "target": {"title": games[app_id].title}}
                          for app_id in expected.get("excluded_ids", []))
    operations.extend({"action": "remove", "target": {"title": games[app_id].title}}
                      for app_id in expected.get("removed_excluded_ids", []))
    if operations:
        value["exclusion_patch"] = operations
    return TurnPlan.model_validate(value)


class OracleModel:
    """Scripted output for retrieval/state evaluation, never a quality score."""

    def __init__(self, plan):
        self.plan = plan

    def complete(self, instruction, data):
        if instruction == INTERPRET:
            return self.plan.model_dump(exclude_unset=True)
        return {"message": "Scripted evaluation selection; this is not a generated answer-quality sample.",
                "game_ids": [game["app_id"] for game in data["games"][:4]], "claims": {"claims": []}}


class RecordedRAG(ConversationalRAG):
    last_frame: TurnFrame | None = None

    def generate(self, frame):
        try:
            return super().generate(frame)
        finally:
            self.last_frame = frame

    def validate(self, frame):
        self.last_frame = frame
        return super().validate(frame)


class SemanticBaseline(RecordedRAG):
    def retrieve(self, frame):
        if frame.result or frame.plan is None or frame.state is None:
            return frame
        if frame.plan.kind == "social":
            return super().retrieve(frame)
        # No named-title/recent-ID lookup or lexical fallback on this path.
        query = (frame.plan.query or frame.query or frame.turn.message) if frame.plan.kind == "recommend" else frame.turn.message
        if self.retriever.encoder is None:
            raise AIFailure("evaluation_encoder_required")
        vector = self.retriever.encoder(query)
        filters = frame.filters if frame.plan.kind == "recommend" else Filters()
        clauses, params = filter_sql(filters)
        with self.repository.snapshot() as (connection, version):
            if version != self.retriever.encoder.catalog_version:
                raise CatalogFailure("evaluation_catalog_changed")
            params.update(v=version, excluded=filters.excluded_ids, vector=json.dumps(vector))
            where = " and ".join(clauses) if clauses else "true"
            rows = connection.execute(text(f"""with eligible as materialized (
                select g.document,g.app_id,e.embedding from discovery.games g
                join discovery.game_embeddings e using(version,app_id)
                left join discovery.game_prices p using(version,app_id)
                where g.version=:v and g.eligibility='eligible' and not (g.app_id=any(:excluded)) and {where})
                select document,1 - (embedding OPERATOR(extensions.<=>) cast(:vector as extensions.vector)) as score
                from eligible order by score desc,app_id limit 5"""), params)
            from game_discovery.catalog.contracts import Game
            candidates = tuple(RankedCandidate(Game.model_validate(row[0]), float(row[1]),
                               semantic_rank=rank, cosine_similarity=float(row[1]))
                               for rank, row in enumerate(rows, 1))
        if any(not satisfies(item.game, filters, set(filters.excluded_ids)) for item in candidates):
            raise AIFailure("chat_candidate_integrity")
        found = RetrievalResult(version, RetrievalOutcome(kind="found" if candidates else "no_recommendation_match",
            channels=["semantic"], semantic_available=True, evidence_ids=[item.game.app_id for item in candidates]),
            candidates=candidates, semantic_ids=tuple(item.game.app_id for item in candidates))
        if not candidates:
            return self.known_outcome(frame, found)
        frame.retrieval = found
        return frame

    def validate(self, frame):
        """Same canonical-selection/prose/claim gates; no top-five-as-five-references."""
        self.last_frame = frame
        if frame.result:
            return frame
        if (frame.answer is None or frame.packet is None or frame.retrieval is None
                or frame.state is None or frame.plan is None):
            raise AIFailure("chat_incomplete_stages")
        answer, state, plan = frame.answer, frame.state, frame.plan
        packet_ids = {d.metadata["app_id"] for d in frame.packet.documents}
        available = {item.game.app_id: item.game for item in frame.retrieval.candidates if item.game.app_id in packet_ids}
        if (len(set(answer.game_ids)) != len(answer.game_ids) or set(answer.game_ids) - available.keys()
                or any(c.app_id not in answer.game_ids or (c.app_id, c.evidence_id, c.field) not in frame.packet.claimable
                       for c in answer.claims.claims)
                or any(sum(c.app_id == app_id for c in answer.claims.claims) > 2 for app_id in answer.game_ids)):
            raise AIFailure("chat_invented_selection")
        cards = validate_claims(answer.claims, [Recommendation(game=available[i], reasons=[], tradeoffs=[
            "Recorded prices may differ from today's Steam store price.",
            "Missing catalog evidence does not establish that an experience is absent."]) for i in answer.game_ids])
        message = natural_message(answer.message)
        notes = []
        if plan.kind != "recommend":
            for app_id in answer.game_ids:
                mismatch = mismatch_notes(available[app_id], frame.filters)
                if mismatch:
                    notes.append(available[app_id].title + ": " + " ".join(mismatch))
        if notes:
            message += "\n\n" + "\n".join(notes)
        elif plan.evaluate_prior_requirements:
            active = frame.filters.model_dump(exclude_defaults=True, exclude={"preferred_terms"})
            message += ("\n\nThe recorded facts satisfy your confirmed hard chat conditions; subjective fit remains unverified."
                        if active else "\n\nThere are no confirmed hard chat requirements to evaluate yet.")
        if len(message) > 2000:
            raise AIFailure("chat_answer_context_limit")
        if answer.game_ids:
            state.shown_ids = answer.game_ids
        if plan.kind != "recommend":
            # Only selected evidence can establish an explicit recent target.
            state.referenced_ids = answer.game_ids[:2]
        else:
            state.referenced_ids = []
        outcome = frame.retrieval.outcome
        if notes:
            outcome = outcome.model_copy(update={"kind": "found_but_mismatch"})
        elif plan.kind == "recommend" and not answer.game_ids:
            outcome = outcome.model_copy(update={"kind": "no_recommendation_match"})
        frame.result = ChatResult(message=message, games=cards, state=ChatStateV2.model_validate(state.model_dump()),
            catalog_version=frame.retrieval.catalog_version, retrieval=outcome, notices=self.notices(frame.retrieval))
        return frame


def metrics(expected, result, frame, plan):
    ranked = [c.game.app_id for c in frame.retrieval.candidates] if frame and frame.retrieval else (
        result.retrieval.evidence_ids if result.retrieval else [])
    selected = [card.game.app_id for card in result.games]
    targets = expected.get("target_ids", [])
    anchors = expected.get("anchor_ids", [])
    conditions = []
    if frame and expected.get("kind") == "recommend":
        expected_filters = Filters.model_validate({**expected.get("retained_constraints", {}), **expected.get("constraints", {})})
        conditions = [i for i in selected if not satisfies(next(c.game for c in result.games if c.game.app_id == i),
                      frame.filters, set(frame.filters.excluded_ids)) or not satisfies(
                      next(c.game for c in result.games if c.game.app_id == i), expected_filters, set())]
    state_checks = {}
    state = result.state
    if frame and expected.get("kind") == "recommend":
        state_checks["recommendation_retrieval_performed"] = result.retrieval is not None
        for field, value in expected.get("constraints", {}).items():
            state_checks["effective_" + field] = getattr(frame.filters, field) == value
        if expected.get("scope") == "turn":
            state_checks["turn_scope_not_persisted"] = state.criteria == frame.turn.state.criteria
    if expected.get("soft_query_replaces"):
        state_checks["old_soft_intent_removed"] = expected["soft_query_replaces"].casefold() not in state.query.casefold()
    for field, value in expected.get("retained_constraints", {}).items():
        state_checks["retained_" + field] = getattr(state.criteria, field) == value
    for field, value in expected.get("must_not_retain", {}).items():
        state_checks["cleared_" + field] = getattr(state.criteria, field) != value
    for app_id in expected.get("excluded_ids", []):
        state_checks["excluded_" + str(app_id)] = app_id in [e.app_id for e in state.exclusions]
    for app_id in expected.get("removed_excluded_ids", []):
        state_checks["removed_" + str(app_id)] = app_id not in [e.app_id for e in state.exclusions]
    for field in expected.get("cleared_fields", []):
        state_checks["neutral_" + field] = getattr(state.criteria, field) == getattr(Filters(), field)
    return {"target_hit_at_5": bool(set(targets) & set(ranked[:5])) if targets else None,
        "anchor_seed_hit_in_evidence": bool(set(anchors) & set(ranked)) if anchors else None,
        "hard_card_violation_ids": conditions,
        "forbidden_card_ids_returned": sorted(set(selected) & set(expected.get("forbidden_card_ids", []))),
        "expected_outcome_match": result.retrieval.kind == expected["outcome"] if expected.get("outcome") and result.retrieval else (
            False if expected.get("outcome") else None), "state_checks": state_checks,
        "human_relevance": None, "unsupported_prose_claims": None, "recall_at_8": None}
