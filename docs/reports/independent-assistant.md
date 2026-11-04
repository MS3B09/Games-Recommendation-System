# Independent floating assistant — implementation evidence

Owner-approved follow-up, 2026-10-22. [Local operation and AI setup](../operations-assistant.md).

## Delivered scope

The owner approved two separate discovery experiences and specified Save-only chat cards, details inside chat, and tab-session memory.

- Main discovery sends favorites, hard controls and relevant feedback; optional main text and conflict-resolution UI are removed. Existing ranking/filter behavior and legacy backend text API remain compatible.
- Main preference actions are Save Game, Not For Me and Already Played. The last two remove only the exact row immediately, retain the others in order, persist feedback and apply their existing negative-affinity / exact-exclusion semantics to later explicit discoveries. No automatic replacement/search occurs. Existing positive feedback and explicit exclusions are preserved and manageable, rather than silently erased.
- A Current-styled floating assistant has independent chat criteria, messages and exact-title rejection state. It never reads/forwards favorites, main controls, device feedback, saved lists or history. Shared Save is its only intentional device-list write. Spoken played/dislike instructions do not write global feedback.
- Compact image/title/recorded-price cards expand within chat to catalog facts, evidence, timestamps, Save and Steam. Natural conversation can answer/clarify without cards. Recommendations come only from retrieved, hard-checked catalog records; optional selected claims require exact evidence. Natural prose remains AI-generated and has no evaluated grounding-quality claim.
- Bounded tab-session persistence, close/reload/New chat/retry/clear, corrupt and blocked storage handling; no main-session text migration into chat. Main clear retains owned-key protection and cross-tab invalidation. Desktop nonmodal panel; mobile modal semantics, background inertness, Tab/Shift+Tab containment and focus restoration.
- New `/api/v1/chat` reuses the existing provider transport, atomic accounting and free-only limits; no new dependency, database schema, migration, service fleet or hosting resource.

## Verification

| Check | Result |
| --- | --- |
| Backend unittests | **80 passed** (12 new independent-chat tests). |
| Ruff | Passed. |
| Strict mypy | **18 source files passed**; E: cache timeout resolved with a C: cache, without relaxing import/type rules. |
| OpenAPI and generated TypeScript drift | Passed. |
| Frontend TypeScript, targeted ESLint, :8001 build | Passed, actual E: source through existing C: tools. |
| Frontend suite | **29 passed**; includes separation, card Save/Steam behavior, chat-local rejection, reload/reset/retry/corruption, cross-tab clear, stable main dismissal and mobile keyboard containment. |
| Real catalog / mocked provider integration | **Seven cases passed**, [report](independent-assistant-live.json). Groq HTTP, accounting reservation and interval are mocked/bypassed as explicitly documented; no real provider call. Actual database cards match resolved records. Invented selections fail closed; main results unchanged after chat. |
| Owned browser → real API → real catalog | **Eight API cases / twelve scans passed**, [report](independent-assistant-browser-live.json). Includes seven legacy API cases, new main seed case, actual disabled-chat response, no hidden main criteria changes, dismissal/reload/clear and both entry routes. Pinned encoder used for legacy semantic cases. All scans axe 0/no overflow/zero page errors. |
| Expanded chat fixture visual checks | Two desktop/mobile checks passed; component captures under `.impeccable/review/independent-assistant/`. Catalog artwork is mocked in these two captures, not evidence of live provider results. |
| Mechanical detector | Initial changed UI `[]`; after focus fix `FloatingAssistant.tsx` `[]`. |

Local browser checks use installed Chromium 1243 through local-only harness overrides; the current Playwright expected missing Chromium 1248. Normal E: frontend `npm run build` initially failed because its installation has no working tsc; targeted checks and production build used existing C: tools compiling actual E: source. No fresh dependency-installation, remote CI or physical-phone claim.

## UI review

Initial independent finish review reopened all eight supplied desktop/mobile captures and found one material issue: background keyboard focus could move behind the nearly full-screen mobile panel. The fix implements reactive mobile modal semantics, sibling inertness/restoration, Tab/Shift+Tab containment and launcher focus restoration. The final suite explicitly verifies that behavior; live and component captures were regenerated afterward. Two attempts to resume the reviewer timed out without a verdict; a fresh focused reviewer then reopened six regenerated shots and scored the finding **RESOLVED; SHIP at ONE-MOBILE-FOCUS-FIX UI verdict scope**. This is not blanket UI/product/backend/live-AI/publication approval. The documentation handoff source-inspected the extension and preserved tokens/sidecar; it did not rerun tests or independently review screenshots.

## Current operational boundary

- Final interactive build is restored to **API :8001**, preview :4173. Owned live verifier stopped its :8002 API; it did not stop or replace the owner's older backend. Restart the backend using `backend/.venv/Scripts/python.exe` for the new endpoint.
- Latest actual settings inspection: **Groq key absent, AI disabled**. The real disabled-chat endpoint is verified; natural provider success/quality remains unverified. Configure the key/model/enablement locally, never in chat or frontend variables.
- Existing application quota migration is authored and historically scratch-tested, **not applied to the application schema by this work**. It must be deliberately initialized before live inference. This follow-up did not mutate schema/catalog data or provision resources.
- 40-game active catalog and historical US/USD observations remain a coverage/freshness limitation. No evaluated relevance improvement or universal natural-language understanding is claimed.
- Local/unpublished. Public release remains M2; no M5, commit/push or publication.
