# Floating chatbot and daily quota revision — 2026-10-22

Owner requested a circular floating launcher like the supplied speech-bubble reference, a changed icon, removal of two explanatory blocks, a more sculpted chatbot window, and application limits of 50 calls / 500,000 reserved tokens per day. Owner confirmed the installed frontend skills and implementation.

## Delivered UI

- Circular lime controller-icon launcher: 72px desktop / 64px mobile. An off-white speech invitation opens chat and has its own dismiss control. Opening or dismissing hides it for the mounted page; retained chats do not show an unsolicited greeting.
- Curved panel, cobalt header sweep, asymmetric user bubbles and game cards, pill controls, inset rounded composer and circular send. Existing Current palette/type and main discovery are retained.
- Three conversation starters prepare and focus a draft, with **no automatic AI call**.
- Removed both requested in-chat explanatory paragraphs and their obsolete `aria-describedby`. The existing device-data disclosure retains the processing/session explanation; game details retain recorded-price/source dates.
- Independent chat state, close/reload/New chat/clear/retry, shared Save, in-panel evidence and Steam links remain. Mobile keeps inert background, bidirectional focus containment and launcher focus restoration.
- The first batched inspection found a narrow welcome heading/initial-scroll problem. A single batch fixed the line wrapping and starts an empty welcome at the top while retaining conversation auto-scroll. Final captures are refreshed.

## Daily limits and database

Updated Python defaults/validation, `.env.example` and the owner's ignored `backend/.env` to:

```dotenv
AI_DAILY_CALLS=50
AI_DAILY_TOKENS=500000
```

Added immutable follow-on migration **Alembic `0004` / `backend/migrations/0005_ai_budget_limits.sql`** and applied it to the configured application database. It expands both table constraints and the atomic reservation function. The original applied migration is unchanged.

- Runtime/migration database target identity checked; existing tables, RLS and constraints inspected before application.
- Consumed usage preserved exactly: **20 calls / 87,822 reserved tokens for 2026-10-22 UTC** before and after the upgrade.
- Thus the observed remaining application allowance is **30 calls / 412,178 reserved tokens**, absent other usage.
- Existing four-calls/minute, 16,000 reserved tokens/call, 30-second chat interval, single concurrent turn, UTC rollover and no-refund accounting remain.
- Runtime execute privilege retained; direct quota-table read denied; RLS enabled. Supabase security advisor returned no findings after migration.
- `.env` changes require backend restart. Groq account/model limits are independent; this does not change the provider's quota or enable a paid plan.

### Meaningful SQL verification

The upgraded scratch-schema verifier passed **10 checks**, including preserved usage above the old ceiling, concurrent reservations ending at exactly 50 calls / 500,000 tokens, invalid oversized caps/per-call bounds, lower configured limits, new-process persistence, minute bounds, denied direct runtime access and UTC rollover. [Machine-readable evidence](assistant-redesign-budget.json).

An initial local connection failure interrupted a scratch run; its named scratch schema was explicitly cleaned before the successful rerun. Final database inspection found **no remaining `m4_budget_verify_*` schemas**.

The actual application runtime role also successfully called the upgraded reservation function inside an explicitly rolled-back transaction. **No inference followed this probe and no consumed usage was reset or added.** A freshly constructed app returned catalog status 200 (`llm_enabled=true`) and main discovery 200 with ten real catalog results.

## Checks and finish review

- **82 backend tests**, Ruff, strict mypy (18 files), OpenAPI drift: passed.
- TypeScript and production build: passed, actual E: application source through the existing C: execution harness, targeting API :8001.
- Targeted ESLint: passed. The first lint attempt from C: ignored outside-base files; it was rerun correctly from E: and checked the changed TSX/icon/test files.
- Full frontend suite: **30 passed**. After the narrow fix, **9 assistant tests** passed again.
- Final visual scenarios: **3 passed**, covering four states at **1440×1000, 390×844 and 320×640**. All **12 axe scans found zero violations**, with no document overflow or page errors. Viewport containment and Escape focus restoration checked. Existing assistant tests also verify mobile forward/reverse Tab containment, inert restoration, separate inputs, session/retry/clear/save and starter no-call behavior.
- Mechanical detector returned `[]` before the final small heading/scroll adjustment; no second detector claim.
- A fresh independent finish reviewer opened **all twelve final captures** and returned **SHIP, no material UI findings at this chatbot revision scope**. The documentation handoff inspected source and updated DESIGN.md/the official surface brief, preserving global tokens/sidecar and attributing evidence.

Final captures: `.impeccable/review/assistant-redesign/{launcher,welcome,expanded,unavailable}-{desktop,mobile,narrow}.png`. These are full-page captures: fixed mobile dialogs occupy the viewport while offscreen document content remains visible further down the capture.

## Limits and local operation

- Chat/prose/artwork in UI tests are mocked fixtures. **No live Groq inference was consumed by this revision.** Earlier live relevance/structured-response limitations and the unconfigured semantic encoder remain; this is not a recommendation-quality pass.
- Physical phone, software keyboard and hosted deployment were not verified. SHIP is UI-revision scope only, not whole-product/backend/provider/publication approval.
- The C: harness uses complete local dependencies; the E: dependency installation remains incomplete. Its corrected `npm run build` uses the source-aware TypeScript/Vite configs.
- Final local HTTP probes found neither :8001 nor :4173 running. Tests stopped their owned preview processes. Start the backend and preview using [assistant operations](../operations-assistant.md), then hard-refresh the browser.
- No commit, push, deployment or M5 work.
