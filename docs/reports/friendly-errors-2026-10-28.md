# Friendly errors and recovery actions — complete locally

Owner approved the proposed error-message revision and confirmed installed frontend skills. This work covers chat, shared connection/catalog failures, input guidance and saved-device notices. It is a local error-interface revision, not R4 quality acceptance or publication.

## Owner follow-up — compact chat

Owner clarified that the marked header and composer should have reduced **height**. The header is now64px on desktop/60px on mobile; the composer uses a44px single-row textarea, shorter padding and the concise placeholder “Ask about games…”. Buttons retain44px touch targets. Short cooldown errors omit the “You can try again after…” timestamp sentence and keep the countdown button; daily allowance reset times remain available. TypeScript/build/targeted lint/detector pass; [eight focused browser tests](compact-chat-browser-tests.json) cover exact cooldown copy, preserved daily timing, retry/reload, keyboard/card behavior and nine axe-0/no-overflow/vertical-fit error scans at1440/390/320. Representative desktop/mobile/narrow captures were opened. The preview has been rebuilt for API:8001; hard-refresh to inspect. This follow-up made no backend changes or live AI calls.

## Implemented behavior

- Distinct chat failures identify daily call/usage exhaustion, the application minute limit, peer cooldown, concurrent work, accounting unavailability, provider throttling/configuration/outage, timeout, invalid generated answers, oversized input/context/evidence and incompatible versions.
- Known failures have short approved messages and specific recovery actions. Request IDs and internal codes remain in API diagnostics and safe server logs, not visible error text. Unknown failures retain an honest friendly fallback; they are not relabeled as quota exhaustion.
- Daily exhaustion offers **Use Your taste** and the confirmed UTC reset formatted in the visitor's local timezone. Short cooldowns disable retry and sending until the actual deadline. Provider deadlines come only from a valid, bounded `Retry-After`; an unknown reset is never invented.
- Confirmed timed availability is retained separately from the conversation in bounded tab-session storage. **New chat does not clear it.** Expired metadata is ignored/cleared. Recovered requests clear the old error; there is no automatic inference retry.
- **Retry message** preserves the exact pending request without duplicating the user message. **Edit message** restores failed text to the composer. **New chat** asks for confirmation before clearing an existing transcript/draft. Close/reload, pending-state protection, guest-data erasure and mobile focus containment remain covered.
- Search/filters/discovery use the same friendly classifier. Unavailable favorites can be explicitly removed; invalid prices direct the user to limits; no-result states explain how to broaden filters. Browser storage failures explain temporary operation and preservation of unreadable saved copies.
- Existing Current colors, typography, cards and general composition are retained. Error prose is16px; actions wrap and have44px touch height. A targeted recovery-height rule keeps long messages and their actions visible on narrow screens while retaining bounded overflow for unusual content.

## Backend and database contract

`ApiError` retains `code`, `message`, `request_id`, `retryable`, adding `recovery`, optional `retry_at` and optional `field`. OpenAPI and generated TypeScript are refreshed. Validation errors do not echo submitted input. Unexpected exceptions are handled without exposing raw driver/provider text in user responses or normal error logs.

Applied application **Alembic0006**, SQL `0007_ai_budget_error_reasons.sql`, adds `discovery.reserve_ai_usage_detailed(integer,integer,integer)`. The existing boolean function is unchanged. The new function calls it under the same atomic row-locking reservation and diagnoses a denial while retaining that lock. It distinguishes daily calls, daily reserved units, the minute limit, invalid limits and an unknown/accounting failure. It returns a reason/deadline, not private usage counts.

The applied migration asserted complete before/after row equality and advanced application Alembic0005→0006 atomically. It changed no ceilings or consumed counters. Runtime remains execute-only; anon/authenticated cannot execute the new function or read counters. Security advisor has no findings. Normal runtime defaults50/500,000, temporary R4 runtime100/1,500,000, four calls/minute,30-second peer throttle, one concurrent chat, two-call turns and existing per-call/model guards remain.

## Verification

- **201 backend tests pass**, including eight new failure-contract/privacy/transport/input/cooldown tests. Ruff and strict mypy27 pass.
- **72 frontend tests pass**, including23new error tests. [Final test report](error-handling-browser-tests.json). A subsequent focused expiry check also confirms that, after clearing a chat and waiting out its deadline, sending becomes available without displaying a nonexistent message to retry or making an automatic request. TypeScript, production build and targeted ESLint pass through the existing C: dependency harness against actual E: source. An earlier wrong-cwd ESLint invocation ignored files; the corrected E: invocation actually checked them and passed.
- [Ten isolated database checks](error-handling-budget-verification.json) pass: reasons/resets, unchanged denied rows, per-call bounds, concurrent last-two reservations, lower-limit restoration, UTC rollover, shared legacy usage and private counters. Scratch schema cleanup confirmed.
- [Applied runtime probe](error-handling-applied-verification.json) exercised the real restricted function in a **rolled-back** transaction. Before/after accounting is identical; no committed reservation or inference.
- [223 actual-catalog/encoder checks](error-handling-chat-integration.json) pass with scripted provider HTTP/budget and three warm samples. This is pipeline verification, not live-model answer quality.
- The real running API returns200for Portal search, facets, catalog status, readiness and seed/filter discovery. Actual chat validation of a2001-character message returns422with `chat_message_too_long` / `edit`, before any inference. Semantic encoder readiness is true; main core remains usable.
- Nine dedicated error scans cover three states at1440×1000,390×844 and320×640: axe0, no horizontal overflow or page errors, and recovery actions fit without scrolling. Existing R3/card/control accessibility regressions also pass.
- Builder opened the initial/refreshed nine-state captures. Manual review found that the old140px status cap could clip actions despite axe passing. The recovery-specific height correction and a vertical-fit regression resolved it; the corrected320px quota/context captures were reopened and their actions are fully visible. This is a builder review at error-interface scope, not independent product/SHIP approval.
- Mechanical detector returned `[]` before the final narrow-height correction. It was not rerun in a polishing loop. An initial concurrent build hit Node memory pressure; sequential bounded-heap builds passed. Initial stale-copy assertions were corrected; the final full72-test run passes without retries.

No live provider calls or committed application reservations were made. SQL still retains the October27 row at **100calls/813,332reserved units**. A fresh October28 receipt reports **0effective calls** before any new normal reservation; old usage is retained rather than manually cleared. Provider windows remain independent.

## Frozen R4 preservation

Before modifying serving code, both authoritative v6 checkpoints matched their source identities. Archived112files plus checkpoints at:

`C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5/error-interface-prechange-v6.zip`

Archive SHA256: `de89eb7970cec56173b1b1c7473365ac209d43657514d5d6f59630a4a126abac`. [Prechange manifest](error-handling-prechange-manifest.json) · [Archive/checkpoint verification](error-handling-checkpoint-verification.json).

Development and held-out journal bytes and E: mirrors are unchanged. No stored source hash, failure, score or output was rewritten. The new serving error interface deliberately fails the old v6 source guard. **Do not resume v6 against this new source or edit its stored hashes.** Future evaluation continuation needs an explicit versioned operational/experimental decision; earlier generic resume instructions are superseded at that boundary. R4 mandatory failures, remaining turns, latency gates and owner judgments remain incomplete.

Final screenshot evidence is also archived in the same durable folder as `error-interface-ui-evidence.zip`; preserve that folder.

## Owner operation

The build targets API:8001. At handoff, newly started inspection services are API launcher7288 with serving child9208 listening on8001, and preview17372 on4173. The child/parent relationship and Uvicorn startup log were verified; recheck current identity before stopping them. Logs: `C:/Users/User/AppData/Local/Temp/opencode/friendly-errors-{api,preview}.{stdout,stderr}.log`. They are left running for owner inspection.

Open **http://127.0.0.1:4173/** and **Ctrl+F5**. No new keys, dependency install or manual migration is needed for this configured database. Future manual startup commands remain in [operations](../operations-assistant.md); stop existing listeners before starting duplicates. No commit, push, deployment or M5 work occurred.
