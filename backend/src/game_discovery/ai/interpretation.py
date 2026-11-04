"""Conservative local interpretation and explicit-control conflict resolution."""

import json
import re
from decimal import Decimal

from pydantic import ValidationError

from game_discovery.catalog.contracts import CriteriaConflict, DiscoverRequest, Filters


def experience_uncertainty(query: str) -> list[str]:
    unresolved = []
    if re.search(r"\b(?:less repetition|less repetitive|repetition|difficulty|easy|easier|harder|frustrat\w*|relax\w*|short sessions?|story|mood)\b", query.casefold()):
        unresolved.append("Experience preferences such as less repetition, difficulty, mood, story emphasis and session length are similarity signals, not verified catalog guarantees.")
    if query.strip():
        unresolved.append("Text matching is a soft relevance signal. Unsupported experience preferences remain uncertain; inspect each game's evidence and tradeoffs.")
    return unresolved


def local_patch(query: str) -> tuple[Filters, list[str]]:
    text = query.casefold()
    patch: dict[str, object] = {}
    unresolved = []
    budgets = re.findall(r"\b(under|below|less than|up to|at most|max(?:imum)?(?: of)?)\s*\$?\s*(\d{1,5}(?:\.\d{1,2})?)(?:\s*(?:usd|dollars?))?\b", text)
    if len(set(budgets)) == 1:
        operator, amount = budgets[0]
        cents = int(Decimal(amount) * 100)
        if cents <= 1000000:
            patch.update(max_price_cents=cents, price_operator="lt" if operator in ("under", "below", "less than") else "lte")
    elif budgets:
        unresolved.append("Your text includes multiple price limits. Choose one using My limits.")
    if re.search(r"\b(?:free[- ](?:to[- ]play|only)|only free|free games? only)\b", text):
        patch.update(free_only=True, min_price_cents=0, max_price_cents=0, price_operator="lte")
    for field, pattern, clear in (
        ("max_price_cents", r"\b(?:no budget|any price|remove (?:the )?(?:price|budget) limit)\b", None),
        ("platforms", r"\b(?:any platform|remove (?:the )?platform limit)\b", []),
        ("required_modes", r"\b(?:any (?:play )?mode|remove (?:the )?(?:play )?mode limit)\b", []),
    ):
        if re.search(pattern, text):
            patch[field] = clear
            if field == "max_price_cents":
                patch.update(free_only=False, min_price_cents=None)
    platforms = [(name, match) for name, pattern in (("windows", r"\bwindows\b"), ("mac", r"\b(?:macos|mac)\b"), ("linux", r"\blinux\b"))
                 for match in re.finditer(pattern, text)]
    modes = [(name, match) for name, pattern in (("single-player", r"\bsingle[- ]player\b"),
             ("online-co-op", r"\bonline co[- ]?op\b"), ("local-co-op", r"\blocal co[- ]?op\b"),
             ("multiplayer", r"\bmultiplayer\b")) for match in re.finditer(pattern, text)]
    for field, matches in (("platforms", platforms), ("required_modes", modes)):
        if matches and field not in patch:
            # Negation/alternatives are not safely reducible to required-all controls.
            ambiguous = any(re.search(r"\b(?:not|no|without|avoid|exclude)\s+(?:\w+\s+){0,2}$", text[max(0, match.start() - 30):match.start()]) for _, match in matches)
            if ambiguous or (field == "required_modes" and len(matches) > 1 and re.search(r"\bor\b", text)):
                unresolved.append(f"Your {field.replace('_', ' ')} wording needs an explicit choice in My limits.")
            else:
                patch[field] = list(dict.fromkeys(name for name, _ in matches))
    return Filters.model_validate(patch), unresolved + experience_uncertainty(query)


def resolve_criteria(request: DiscoverRequest, patch: Filters) -> tuple[Filters, list[CriteriaConflict], Filters | None, list[str]]:
    base = request.effective_filters()
    changes = patch.model_dump(exclude_unset=True)
    if not changes or request.resolution == "controls":
        return base, [], None, []
    # Only these hard controls can be proposed by language assistance. Seed IDs,
    # exclusions and taste-feedback cannot be fabricated or cleared by a model.
    allowed = {"min_price_cents", "max_price_cents", "price_operator", "free_only", "platforms", "platform_match", "required_modes"}
    if set(changes) - allowed:
        return base, [], None, ["AI proposed unsupported criteria. Existing controls were retained."]
    try:
        proposed = Filters.model_validate({**base.model_dump(), **changes})
    except ValidationError:
        return base, [], None, ["The text would create an invalid price range or incompatible free-only limit. Adjust My limits; existing criteria were retained."]
    explicit = request.filters.model_fields_set | request.preferences.model_fields_set | request.conversation.criteria.model_fields_set
    conflicts = []
    for field in changes:
        current_value, proposed_value = getattr(base, field), getattr(proposed, field)
        if current_value == proposed_value or field not in explicit:
            continue
        # An equal-dollar exclusive text bound only tightens the inclusive UI bound.
        if field == "price_operator" and proposed_value == "lt" and proposed.max_price_cents == base.max_price_cents:
            continue
        conflicts.append(CriteriaConflict(field=field, current=json.dumps(current_value), proposed=json.dumps(proposed_value)))
    if conflicts and request.resolution != "text":
        return base, conflicts, proposed, []
    return proposed, [], None, []
