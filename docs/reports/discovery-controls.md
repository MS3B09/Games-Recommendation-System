# Discovery controls revision — 2026-10-18

Final documentation/handoff confirmed **2026-10-19** after the metadata-failure fix and refreshed verification.

## Authority and status

**Owner-authorized follow-up after completed M3, complete locally in Current; main-agent confirmation received.**
The owner requested one compact section, multi-choice required play
modes/platform/genre, a two-handle minimum/maximum price slider from free-to-play
through the catalog maximum, modes → platform → genre → price order on one
desktop line, and a small meaningful lead. The lead is **My limits**.

M0–M3 remain complete; M3 is local/unpublished. The completed M3 baseline's
five functional gates and four-fix scoped ship verdict remain historical
[baseline evidence](m3-implementation.md), not approval of this follow-up.
**Independent controls verdict: the one material metadata-failure fix is RESOLVED;
ship at ONE-SCORED-FIX verdict-pass scope.** The reviewer reopened all **18 refreshed
captures** and found no regression attributable to the fix. The earlier full
controls review found no material visual/accessibility regression. This scoped
verdict is not blanket whole-product or publication approval.
M4 is unstarted/unauthorized. No redesign, publication, commit, push or deployment
is authorized. Hosted M2 is unchanged.

## Implemented controls

- `frontend/src/DiscoveryControls.tsx`: native `details`/`summary` disclosures
  with native checkboxes, clear selection, outside-pointer close and Escape
  close/focus return. Selectors allow multiple required modes, platforms and
  catalog genres. Empty means Any; one/two selections show labels; larger sets
  show the first label plus a count, with the full selection available to
  assistive technology and the title tooltip.
- `GuestDiscovery.tsx`: compact ordered controls, request/metadata lifecycle and
  conditional exact-title exclusions/Undo exclusions. **All selected modes and
  genres** must match; **any selected platform** may match. The helper states
  these semantics and recorded-USD limitations.
- `current-original.css`: one four-field desktop row (three equal selector
  columns and 1.25fr price) beside the small 14px lead. Recorded at desktop
  widths **1000/1440/1777px**; **≤900px two columns**, **≤640px one column**,
  preserving modes → platform → genre → price order.
- Old advanced section and preferred/unwanted comma-separated text fields are
  removed. Submission explicitly sends `preferred_terms: []` and
  `unwanted_terms: []`, so legacy stored terms cannot silently influence a new
  discovery. The API retains compatible term support for future explicitly
  authorized work; this revision supersedes the earlier active UI only.
- Both official entry routes still load `current-original.tsx` → `GuestApp`.
  Genre-led result rows, artwork picker, favorite chips, saved games, feedback,
  history and device-data/clear features remain in the selected Current world.

## Price and API contract

`Filters.min_price_cents` is optional/null for compatible callers; supplied
bounds are integer **0..1,000,000 cents**, including zero. Minimum is inclusive;
the UI submits `price_operator: "lte"` for an inclusive maximum. The API retains
`"lt"` compatibility. Individual filters and the merged `DiscoverRequest`
validate minimum ≤ maximum; invalid ranges or free-only with a positive minimum
return **422**, including invalidity introduced by merging saved preferences
with explicit filters. Explicit null/false/[] continues to override saved state.

A supplied minimum, even zero, requires a known recorded US/USD price, as does
an upper bound. $0–$0 submits `free_only: true`, requiring explicit free-to-play
evidence rather than inferring eligibility from a zero-price promotion. Recorded
prices remain dated catalog observations, not guaranteed current purchase quotes.

`GET /api/v1/facets` adds optional `max_price_cents`: maximum recorded price among
eligible active US/USD games, null if unavailable. The UI rounds the cap upward
to a whole dollar, extends it to preserve higher stored min/max bounds, and caps
it at the API limit. The internal rail has a finite rendering scale with a minimum
$1 extent; it is not an available catalog maximum or an implied budget. If facets
are unavailable and stored criteria have `max_price_cents: null` and
`free_only: false`, the disabled slider displays **Any price**, with accessible
maximum text **No maximum price**. Submission and persistence retain null/false;
the finite rendering fallback is never saved or sent as a budget. Only when a
catalog maximum is available can a legacy null upper bound map to the derived
ceiling for slider submission. Minimum defaults to zero; initial/clear defaults remain Hades,
single-player, Windows, Any genre and **$0–$20 USD**.

`PriceRange` overlays two native range inputs, step **one cent**. Handles clamp
against one another and remain keyboard-operable, with distinct accessible
minimum/maximum names, value text and thumb focus. Missing/loading/error maximum
metadata disables the slider; request errors expose **Retry catalog controls**.
No-known-price metadata has its own notice. Favorite resolution precedes facets;
cached/in-flight facets deduplicate bootstrap work (two requests with defaults).

The implementation queries existing taxonomy and price data. OpenAPI and
frontend types were regenerated; there is **no migration, database mutation,
new dependency, authentication or language-model addition**.

## Storage compatibility

`guest-store.ts` retains the validated **version-2** envelope and defined v1
migration. Older v2 preferences and history without optional minimum normalize
to **zero**. Bounds and cross-bound validity are checked; no storage format bump.
`GuestLibrary.tsx` renders history ranges/free-to-play. Limits remain 50 favorites,
200 saves, 500 latest feedback entries and 20 recent summaries. Save is separate
from Interested; already played is exact exclusion only. Existing clear-data,
temporary-mode and cross-tab request invalidation behavior remains.

## Resolved metadata-failure finding and review scope

The one material finding was that submitting a stored unbounded price while
facets failed could turn a finite internal slider scale into a real budget.
`GuestDiscovery` now preserves `max_price_cents: null` / `free_only: false` when
the catalog maximum is unavailable. The disabled native slider truthfully says
Any price / No maximum price instead of presenting the rendering fallback as a
selected maximum. No other UI/CSS change beyond the unbounded-label conditional
is reported; detector `[]` remains unchanged.

The updated legacy regression forces a facets **503**, checks both request
`filters` and `preferences` plus persisted `max_price_cents: null`, and verifies
missing minimum normalization to zero and clearing of old preferred/unwanted
terms. The full **21-test frontend suite passed again** (15 browser/6 storage),
with TypeScript/build/targeted lint passing. Refreshed live verification passed
all nine API cases and 18 clean state scans after the fix.

A transient live catalog search exceeded the old five-second assertion. The
test now waits for the real response within the existing **75-second network
budget**, with no automatic retry; the final run passed. This is test waiting
alignment, not a new application timeout or a response-time guarantee.

Main confirms local completion. The independent reviewer marks this finding
**RESOLVED**, disposition **ship at ONE-SCORED-FIX verdict-pass scope**, after
reopening all 18 refreshed captures with no regression attributable to the fix.
The earlier full controls review found no material visual/a11y regression.
Keep this separate from the historical M3 four-fix verdict and from any future
whole-product/publication approval.

## Recorded verification — final passed checks and scoped verdict

These results were completed during implementation and supplied for this
documentation handoff. **This documentation-only pass did not rerun tests.**

| Check | Recorded result |
| --- | --- |
| Python behavior | **51 tests passed**; unchanged backend result |
| Backend static/contracts | Ruff; strict mypy **13 modules**; OpenAPI drift remain passed, unchanged |
| Frontend compilation | **Actual E: source** through existing C: tools/local-only resolution wrappers; TypeScript/production build passed |
| Frontend lint/contracts | Targeted ESLint passed again; generated TypeScript drift remains passed |
| Normal frontend suite | **21 passed again: 15 browser + 6 storage**, including the facets-503 unbounded-price regression; live check excluded |
| Mechanical detector | `[]`, unchanged |
| Opt-in live test | **1 passed after the fix**, nine real API cases using owned local API :8002 and the existing restricted PostgreSQL/pgvector catalog |
| Browser scans | **18 refreshed**, axe **0**, no horizontal overflow, **0 page errors** |
| Independent controls review | One material metadata-failure fix **RESOLVED**; **ship at ONE-SCORED-FIX verdict-pass scope**, main confirmed |

The test-refreshed [generated live report](discovery-controls-live.json), observed
**2026-10-19T00:06:46.858Z**, records catalog
`m2-649714e8b26775165f105d02`, ranking `seed-feedback-v1`, and nine cases:
baseline, interested, already played, not for me, required RPG, explicit
overrides, recorded price range, multiple required choices and free-only range.
Scans cover initial/play-modes/platforms/genres/favorites/results/evidence/saved/
device-data × desktop (1440) and mobile (390).

The test also refreshed the local captures:
`.impeccable/review/discovery-controls/{initial,play-modes,platforms,genres,favorites,results,evidence,saved,device-data}-{desktop,mobile}.png`.
The historical [m3-live-evidence.json](m3-live-evidence.json) remains unchanged,
with its six cases/12 scans and baseline 49 Python/17 frontend checks.

## Local operation and confirmed handoff

- Verification built preview :4173 for **http://127.0.0.1:8002** and set
  `M3_API_ORIGIN` to that origin, avoiding the owner's existing :8001 server.
  The live helper permits **only** loopback :8001 or :8002, defaults :8001 and
  stops its owned API process tree. Normal live config expects preview running;
  local-only wrappers used with C: tools start preview if missing/reuse it and
  stop processes they own. No owned background API persists.
- **Main has restored the final interactive build to API :8001** after successful
  :8002 verification. The test stopped owned :8002; the owner's :8001 server was
  not changed. This documentation pass has not rebuilt or started any service.
- Restart the older :8001 backend, start/reuse preview :4173 and refresh **both**
  `/` and `/current-original.html` for minimum-price/facets-maximum
  support; an already-running older API cannot serve new code. Existing ignored
  `backend/.env` runtime configuration suffices; **no new credentials/migrations**.
  Normal development still uses :8000. [Run instructions](../operations-m3.md).
- **Main-agent review confirmation received:** controls revision complete locally,
  with the one-fix scoped disposition above. The baseline four-fix verdict remains
  separate; neither grants blanket product or publication approval.
- Fresh frontend installation, remote M3 CI and physical-phone behavior remain
  unverified. Existing C: tools compile actual E: source; no fresh-install claim.
  These are behavior/engineering checks, not measured relevance improvement.

Stop at this owner-authorized follow-up: M3 complete/local/unpublished;
M4 unstarted/unauthorized; no commit/push/deploy.
