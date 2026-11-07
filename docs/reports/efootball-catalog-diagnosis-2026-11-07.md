# eFootball catalog/chat mismatch — read-only diagnosis, 2026-11-07

**Subsequent owner authorization:** the owner requested a general fix. [The local implementation and verification](catalog-chat-fix-2026-11-07.md) now supersede the proposed-only status below; the recorded diagnosis/failed attempts remain historical evidence, not relabeled passes. No new live-provider or hosted acceptance is implied.

## Confirmed cause in the reported conversation

The catalog is not missing the game. Both the saved lookup result and an independent read-only query identify **eFootball™**, Steam app **1665460**.

The relevant archived events show two separate failures:

1. At06:37:59UTC, `lookup_titles(query="efootball")` returned the game and its factual preview successfully. The next model response was ordinary prose rather than the required JSON reply. The server rejected it with `JSONDecodeError`; that attempt was **not delivered**.
2. At06:39:50UTC, another lookup for `eFootball` again returned the correct game. Its next response was also unstructured prose and rejected with `JSONDecodeError`.
3. The screenshot's successful turn, at06:40:10UTC, first encountered the normal minute limit; its later successful attempt used **one model call and no catalog tool**. The model claimed there was no catalog entry without evidence. This is a delivered false-absence claim, not a database lookup returning no game.

No old evaluation was resumed, no failed turn was retried by this investigation, and no model calls were made. Existing owner attempts remain intact.

## Why the code allowed it

- `backend/src/game_discovery/ai/dialogue.py`, `Dialogue.run`: native tool selection is optional. Before any catalog tool has been used in the current turn, non-JSON prose is packaged as an evidence-free reply for ordinary conversation. After a catalog tool, the same unstructured reply is rejected instead. This explains the successful unsupported denial versus the failed factual drafts.
- `Dialogue.validate_answer` validates supplied citations, canonical card IDs, filters and certain numeric observations, but does **not** require evidence for every game-related prose statement when there are no citations/cards. An absence claim can therefore use the ordinary-conversation path.
- `lookup_titles` is explicitly excluded from the normal `finish=true` early-finalization condition. After the successful lookup, the next planner call still had optional tools and no strict reply schema; it returned prose. The guard correctly rejected that format, but the flow did not reliably produce a deliverable structured answer.

The screenshot turn performed no retrieval, so trademark matching is **not its immediate cause**. There is a separate confirmed search inconsistency: the literal title/text search returns one match for `efootball` and `eFootball™`, but zero for the user's literal spelling `eFootballTM`. The stored canonical identity key is `efootballtm`. The existing normalized `chat_title` resolver is separate from `lookup_titles`, which currently calls `assistant_search` directly.

## Smallest general fix to implement next

1. Require a sourced lookup outcome for catalog-existence assertions; an evidence-free conversation reply must not assert game presence/absence or recommend uncited alternatives. Enforce this at the structured output boundary, not solely with another prompt or an eFootball-specific keyword rule.
2. When an explicitly completed name lookup has supplied the requested evidence, use the existing structured final-writer path within the current call ceiling. Preserve a second information round for genuinely incomplete lookups. Do not accept malformed JSON, weaken the existing guards or add automatic repair/retry calls.
3. Reuse normalized canonical name resolution for specific-title lookup, with explicit ambiguity/related-title suggestions. Do not label a spelling/version mismatch as whole-catalog absence. Keep broad paginated browsing separate.
4. Reuse focused tests for an exact title, literal trademark suffix, absent title, ambiguous/year variant, successful lookup followed by prose, and unsupported evidence-free denial. Start with scripted/offline checks, then only a separately bounded live check if authorized and quota-safe. Do not restart a historical evaluation campaign.

This is a proposed backend correction, **not an implemented fix**: the user requested investigation. No backend, database schema/data, model, prompts, quotas, chat history or hosting configuration changed.

## Evidence and limits

Read only the four events whose user messages mention eFootball, excluding capability hashes and unrelated conversation contents. Remote queries were explicit read-only transactions. Recent PostgreSQL logs contain checkpoint activity and one client-reset entry, not a catalog lookup/database error for the reported event. Security advisories are empty; two existing unused-index INFO notices are unrelated ([Supabase guidance](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index)).

No fresh live generation or quality acceptance is claimed. A separate attempted local Python diagnostic exited before producing a receipt; it is not counted as a passing replay/test. The saved server trace and independent database reads establish the findings above without additional inference.
