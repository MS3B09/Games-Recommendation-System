"""Deterministic M2 constraints and source-derived template reasons."""

from game_discovery.catalog.contracts import Filters, Game, Reason, Recommendation


def satisfies(game: Game, filters: Filters, excluded: set[int]) -> bool:
    if game.eligibility != "eligible" or game.app_id in excluded:
        return False
    if filters.free_only and game.free_to_play is not True:
        return False
    if filters.max_price_cents is not None:
        if game.price is None:
            return False
        if filters.price_operator == "lt" and game.price.amount_cents >= filters.max_price_cents:
            return False
        if filters.price_operator == "lte" and game.price.amount_cents > filters.max_price_cents:
            return False
    if filters.platforms:
        supported = [game.platforms.get(platform) is True for platform in filters.platforms]
        if not (all(supported) if filters.platform_match == "all" else any(supported)):
            return False
    if not set(filters.required_modes).issubset(game.modes):
        return False
    return not ({term.casefold() for term in filters.unwanted_terms} & set(game.genres + game.tags))


def recommendation(game: Game, seeds: list[Game], filters: Filters) -> Recommendation:
    evidence = {item.field: item.id for item in game.evidence}
    reasons = []
    shared = sorted(set(game.genres + game.tags) & {term for seed in seeds for term in seed.genres + seed.tags})
    preferred = sorted(set(game.genres + game.tags) & {term.casefold() for term in filters.preferred_terms})
    if shared:
        reasons.append(Reason(text=f"Shares catalog genres/tags with your favorites: {', '.join(shared)}.",
                              evidence_ids=[evidence[field] for field in ("genres", "tags") if field in evidence]))
    if preferred:
        reasons.append(Reason(text=f"Includes your preferred catalog terms: {', '.join(preferred)}.",
                              evidence_ids=[evidence[field] for field in ("genres", "tags") if field in evidence]))
    for platform in filters.platforms:
        if game.platforms.get(platform) is True:
            reasons.append(Reason(text=f"The catalog lists {platform} support.", evidence_ids=[evidence[f"platform:{platform}"]]))
    if filters.required_modes:
        reasons.append(Reason(text=f"Lists these play modes: {', '.join(filters.required_modes)}.", evidence_ids=[evidence["modes"]]))
    if game.price and (filters.max_price_cents is not None or filters.free_only):
        reasons.append(Reason(text=f"Recorded US price: ${game.price.amount_cents / 100:.2f} USD.",
                              evidence_ids=[game.price.evidence_id]))
    if not reasons:
        reasons.append(Reason(text=game.description, evidence_ids=[evidence["description"]]))
    tradeoffs = ["Recorded prices may differ from today's Steam store price.",
                 "Tag coverage is incomplete; missing tags do not establish that an experience is absent."]
    if seeds:
        tradeoffs.append("Content similarity is a discovery signal, not a guarantee of matching gameplay or enjoyment.")
    if game.early_access:
        tradeoffs.append("Early Access: features and content may change.")
    return Recommendation(game=game, reasons=reasons, tradeoffs=tradeoffs)
