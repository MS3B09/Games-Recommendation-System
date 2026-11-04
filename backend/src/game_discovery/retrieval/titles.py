"""Bounded catalog-only title matching; fuzzy names are suggestions, never identities."""

import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal, Sequence

TITLE_CATALOG_LIMIT = 256
TITLE_OPTION_LIMIT = 4


@dataclass(frozen=True)
class CatalogTitle:
    app_id: int
    title: str


@dataclass(frozen=True)
class TitleMatch:
    kind: Literal["found", "ambiguous", "not_in_catalog"]
    matches: tuple[CatalogTitle, ...] = ()
    suggestions: tuple[CatalogTitle, ...] = ()
    total_matches: int = 0


def normalize_title(title: str) -> str:
    folded = unicodedata.normalize("NFKC", title).casefold()
    # Apostrophes are elided so Baldur's/Baldurs agree; hyphens become spaces.
    folded = "".join(character for character in folded if character not in "'’‘ʼ")
    return " ".join("".join(character if character.isalnum() else " " for character in folded).split())


# An alias is valid only while BOTH the canonical ID and title still agree.
# Broad aliases are combined with franchise matches, not allowed to hide sequels.
ALIASES = {"spiderman": CatalogTitle(1817070, "Marvel’s Spider-Man Remastered")}


def compact_phrase_matches(compact: str, tokens: list[str]) -> bool:
    """Join complete adjacent words, never accept ori as Original or 2 as 20."""
    for start in range(len(tokens)):
        joined = ""
        for token in tokens[start:]:
            joined += token
            if len(joined) >= len(compact):
                if joined == compact:
                    return True
                break
    return False


def match_title(query: str, titles: Sequence[CatalogTitle], reference_id: int | None = None) -> TitleMatch:
    if len(titles) > TITLE_CATALOG_LIMIT or len(query) > 200:
        raise ValueError("Title lookup exceeds its bounded input")
    if reference_id is not None and not 0 < reference_id <= 2147483647:
        raise ValueError("Invalid canonical reference")
    if len({item.app_id for item in titles}) != len(titles):
        raise ValueError("Duplicate catalog identities")
    ordered = sorted(titles, key=lambda item: item.app_id)
    needle = normalize_title(query)
    compact = needle.replace(" ", "")
    if reference_id is not None:
        matches = [item for item in ordered if item.app_id == reference_id]
    elif not needle:
        raise ValueError("A nonblank title is required")
    else:
        matches = [item for item in ordered if normalize_title(item.title) == needle]
        if not matches:
            matches = [item for item in ordered if normalize_title(item.title).replace(" ", "") == compact]
        if not matches:
            alias = ALIASES.get(compact)
            words = needle.split()
            prefix_matches = []
            for item in ordered:
                normalized = normalize_title(item.title)
                tokens = normalized.split()
                token_match = all(any(token == word if word.isdigit() else token.startswith(word)
                                      for token in tokens) for word in words)
                # Whole-token/compact phrases outrank partial token prefixes.
                # A broad prefix must not add Original Sin to exact Ori matches.
                compact_match = len(compact) >= 3 and compact_phrase_matches(compact, tokens)
                verified_alias = (alias is not None and item.app_id == alias.app_id
                                  and normalized == normalize_title(alias.title))
                if all(word in tokens for word in words) or compact_match or verified_alias:
                    matches.append(item)
                elif len(compact) >= 2 and token_match:
                    prefix_matches.append(item)
            if not matches:
                matches = prefix_matches
    if matches:
        return TitleMatch("found" if len(matches) == 1 else "ambiguous",
                          tuple(matches[:TITLE_OPTION_LIMIT]), total_matches=len(matches))
    suggestions = []
    if reference_id is None:
        for item in ordered:
            score = SequenceMatcher(None, compact, normalize_title(item.title).replace(" ", "")).ratio()
            if score >= 0.72:
                suggestions.append((score, item))
    suggestions.sort(key=lambda pair: (-pair[0], pair[1].app_id))
    return TitleMatch("not_in_catalog", suggestions=tuple(item for _, item in suggestions[:TITLE_OPTION_LIMIT]))
