"""Atomic scope/provenance operations. No transcript inference or main inputs."""

from dataclasses import dataclass
from typing import cast

from game_discovery.ai.chat_contracts import ChatCriteria, ChatStateV2, CriterionKey, Origin, TurnPlan
from game_discovery.catalog.contracts import Filters

BUDGET_KEYS = {"min_price_cents", "max_price_cents", "price_operator", "free_only"}


class MemoryClarification(ValueError):
    pass


@dataclass(frozen=True)
class MemoryUpdate:
    state: ChatStateV2
    effective: Filters
    query: str


def has_legacy(state: ChatStateV2) -> bool:
    return bool(state.legacy_query.strip() or state.legacy_excluded_ids or
                (state.legacy_criteria and state.legacy_criteria != ChatCriteria()))


def apply_plan(original: ChatStateV2, plan: TurnPlan) -> MemoryUpdate:
    """Build/validate a copy; caller commits it only after a successful turn."""
    if original.user_turn >= 1000000:
        raise MemoryClarification("This conversation has reached its turn limit. Please start a new chat.")
    state = ChatStateV2(user_turn=original.user_turn) if plan.reset_preferences else original.model_copy(deep=True)
    state.user_turn += 1
    origin = Origin(user_turn=state.user_turn)
    values = state.criteria.model_dump()
    effective = values.copy()
    defaults = ChatCriteria().model_dump()
    expanded: set[str] = set()
    for patch in plan.criteria_patch:
        clears: set[str] = set(patch.clear)
        if clears & BUDGET_KEYS:
            clears |= BUDGET_KEYS
        if "platforms" in clears:
            clears.add("platform_match")
        sets = patch.set.model_dump(exclude_unset=True)
        if sets.get("free_only") is True:
            sets.update(min_price_cents=0, max_price_cents=0, price_operator="lte")
        touched = clears | sets.keys()
        if expanded & touched:
            raise MemoryClarification("Please give one scope for each requirement, including the whole budget.")
        expanded |= touched
        destination = values if patch.scope == "conversation" else effective
        if (destination["free_only"] and sets.get("free_only") is False
                and not ({"min_price_cents", "max_price_cents"} <= touched)):
            raise MemoryClarification("Please explicitly clear or replace both old free-only price bounds when switching to paid games.")
        for key in clears:
            destination[key] = defaults[key]
        destination.update(sets)
        if patch.scope == "conversation":
            for key in touched:
                typed_key = cast(CriterionKey, key)
                if destination[key] == defaults[key]:
                    state.provenance.pop(typed_key, None)
                else:
                    state.provenance[typed_key] = origin
    # Turn and conversation patches cannot touch the same expanded key.
    turn_keys = {key for patch in plan.criteria_patch if patch.scope == "turn"
                 for key in (set(patch.clear) | patch.set.model_fields_set)}
    if any(p.scope == "turn" and (set(p.clear) & BUDGET_KEYS or p.set.free_only) for p in plan.criteria_patch):
        turn_keys |= BUDGET_KEYS
    if any(p.scope == "turn" and "platforms" in p.clear for p in plan.criteria_patch):
        turn_keys.add("platform_match")
    effective = {key: effective[key] if key in turn_keys else value for key, value in values.items()}
    try:
        state.criteria = ChatCriteria.model_validate(values)
        filters = Filters.model_validate(effective)
        if filters.free_only and (filters.min_price_cents != 0 or filters.max_price_cents != 0
                                  or filters.price_operator != "lte"):
            raise ValueError("Inconsistent free-only bounds")
    except ValueError:
        raise MemoryClarification("Those requirements conflict. Please clarify the budget or conditions; I kept your previous preferences.") from None
    # Facts never replace the retained soft recommendation topic.
    if plan.kind == "recommend" and plan.query.strip():
        state.query = plan.query.strip()
        state.query_origin = origin
    return MemoryUpdate(ChatStateV2.model_validate(state.model_dump()), filters, state.query)


def legacy_state(criteria: Filters, query: str, excluded_ids: list[int], shown_ids: list[int]) -> ChatStateV2:
    """Unknown-provenance legacy values are never active recommendation inputs."""
    exclusions = list(dict.fromkeys([*excluded_ids, *criteria.excluded_ids]))
    if len(exclusions) > 100:
        raise MemoryClarification("This older conversation exceeds the exclusion limit. Please start a new chat.")
    values = criteria.model_dump()
    values["excluded_ids"] = []
    return ChatStateV2(legacy_criteria=ChatCriteria.model_validate(values), legacy_query=query,
                       legacy_excluded_ids=exclusions, shown_ids=list(dict.fromkeys(shown_ids)))
