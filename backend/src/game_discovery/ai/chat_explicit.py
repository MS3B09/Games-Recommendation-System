"""Historical v6 keyword overrides; NOT used by the current serving chat path.

Retained for historical regression/replay reference. Current ConversationalRAG
validates the LLM's plan directly and does not call these overrides.

No inferred IDs, main state, catalog facts, model calls, or broad language parser.
Only anchored positive played statements and whole-message undo commands override
model omissions; ambiguous titles still go through the existing catalog resolver.
"""

import re

from game_discovery.ai.chat_contracts import ChatTurn, TurnPlan

PLAYED = re.compile(r"^\s*I(?:\s+have|['’]ve)?\s+(?:already\s+)?played\s+([^.!?;\n]{1,200})(?:[.!;]|$)", re.I)
UNDO = re.compile(r"^\s*(?:please\s+)?(?:include|allow)\s+([^.!?;\n]{1,200}?)\s+again(?:\s+in\s+(?:the\s+)?recommendations)?[.!]?\s*$", re.I)


def explicit_plan(turn: ChatTurn, plan: TurnPlan) -> TurnPlan:
    value = plan.model_dump(exclude_unset=True)
    # Catalog genre labels are a separate hard control. Generic experience words
    # stay in the semantic query; existing confirmed genre requirements remain.
    if not re.search(r"\bgenres?\b", turn.message, re.I):
        changes = []
        for change in value.get("criteria_patch", []):
            change.get("set", {}).pop("required_genres", None)
            if change.get("set") or change.get("clear"):
                changes.append(change)
        value["criteria_patch"] = changes
    undo = UNDO.fullmatch(turn.message)
    played = PLAYED.match(turn.message)
    match = undo or played
    if match:
        target = match.group(1).strip()
        action = "remove" if undo else "add"
        operations = [op for op in value.get("exclusion_patch", [])
                      if op["target"].get("title", "").casefold() != target.casefold()]
        operations.append({"action": action, "target": {"title": target}})
        value["exclusion_patch"] = operations
        if undo:
            value.update(kind="recommend", reply="", query=turn.state.query, title_mentions=[target],
                         reference="none", requested_facts=[], evaluate_prior_requirements=False)
    return TurnPlan.model_validate(value)


def interpreted_plan(turn: ChatTurn, raw: object) -> TurnPlan:
    # A whole-message explicit undo determines the operation before semantic
    # validation. Some providers return clarify+title for this command, which
    # the frozen generic TurnPlan correctly rejects. Normalize only these known
    # routing fields; unknown fields, malformed patches/IDs still fail validation.
    if isinstance(raw, dict) and UNDO.fullmatch(turn.message):
        raw = raw | {"kind": "recommend", "reply": "", "title_mentions": [], "reference": "none",
                     "requested_facts": [], "evaluate_prior_requirements": False}
    return explicit_plan(turn, TurnPlan.model_validate(raw))
