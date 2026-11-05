# Official Current — source, operation and provenance

## Remaining frontend work — 2026-11-04

The [completion plan](../docs/project-completion-plan.md) calls for a **catalog-connected `/dashboard`** after catalog expansion, then publication of the latest application. Preserve Current's identity and existing discovery/saved/assistant contracts. The planned dashboard retains four summary metrics, eight charts and the description word cloud from the original Streamlit app, with clearer responsive/accessible presentation.

`/dashboard` is not implemented yet. Extend `GuestApp.tsx`'s existing routing/navigation/skip links and API client/types; use the same active catalog and refresh boundary. Confirm desired frontend skills before implementation. Update this source guide and the surface brief when the actual page exists. Older frozen/no-API status, R4 continuation and publication prohibitions below are historical, superseded as a remaining-work list by the completion plan.

**Friendly-error revision — 2026-10-28:** [Implementation/evidence](../docs/reports/friendly-errors-2026-10-28.md). Friendly reason-specific chat/catalog/storage messages, internal-only diagnostic IDs, localized reset times, persistent cooldowns, meaningful actions, edit/retry and confirmed New chat. Error prose16px and wrapping44px recovery actions retain Current.72frontend tests and nine error scans pass; manual narrow clipping finding fixed and corrected captures checked. Builder-reviewed UI revision only, not independent SHIP or R4 quality acceptance. Final build targets API:8001. Original v6 source is archived; earlier source-frozen resume instructions require a separately versioned decision.

**Backend quota update — 2026-10-27:** [Temporary100/1,500,000allowance](../docs/reports/r4-quota-increase-2026-10-27.md) applied preserving usage. No frontend implementation/build/visual change. Restart backend for runtime values; preserve authoritative C: evaluation journals. Current proposed development13/13passes, held-out32attempts with8retained prose failures; R4 not accepted. Today's95calls pause at provider-safe headroom, not the application ceiling. Historical UI evidence below retains its scope.

**Latest backend-only R4 — 2026-10-26:** [v6 checkpoint](../docs/reports/conversational-rag-r4-resume-2026-10-26.md). Played/undo/shortlist/journal fixes verified; frontend unchanged, no new UI test/verdict. Current9/26development attempts, full live/human/latency gates pending. Today's50calls exhausted; resume later UTC days under existing approval and preserve authoritative C: journal. Restart backend for current fixes; API:8001 build unchanged. October25 entries below are historical.

**RAG update — 2026-10-25:** [R4 fixes/current checkpoint](../docs/reports/conversational-rag-r4-continuation.md) remain backend-only; frontend unchanged. Current v3 core journey3/3 and runtime retrieval benchmark pass, full live/human/serving-latency gates pending. Additional free-tier inference is approved;49daily calls pauses two-call turns until later UTC day. R4 not accepted. R3's49frontend tests/6scans remain historical, not new UI checks/verdict. Final build API:8001; restart backend for strict generation/reference/metadata fixes. [Operations](../docs/operations-assistant.md).

**Latest implementation, 2026-10-22:** main favorites/limits/feedback discovery and an independent floating AI assistant replace main-form text/refinement. Main dismissals hide only their exact row; chat cards expand in-panel with Save/Steam only and own tab-session state. Current identity/provenance retained. [Current evidence](../docs/reports/independent-assistant.md) · [durable startup/AI setup](../docs/operations-assistant.md). 80 backend/29 frontend tests plus static/live checks passed; one mobile-focus fix RESOLVED, **SHIP at ONE-MOBILE-FOCUS-FIX UI verdict scope**. Live AI still needs configuration and quota initialization. Older summaries below describe superseded UI, not current startup instructions.

**Latest extension — M4 complete locally, unpublished (2026-10-19):** both official entry routes retain Current and now add approved text discovery, visible criteria/uncertainty/conflicts and bounded session refinement. Independent review reopened twelve refreshed captures and returned **SHIP at M4 Current UI surface scope**, no outstanding material UI findings. [Current implementation/evidence](../docs/reports/m4-implementation.md) · [startup/operations](../docs/operations-m4.md). Existing external catalog artwork and font provenance remain; no new raster asset or identity was introduced. Earlier M4-unstarted/unauthorized notes below are historical, superseded by owner approval. No M5, commit/push or publication authority.

**2026-10-18: M0–M3 complete; M3 COMPLETE LOCALLY.** The owner selected the exact Current page, then authorized **“implement remaining M3 steps to complete it.”** Main agent confirms all five functional gates and final handoff. The application extends that visual world with real discovery and guest persistence. Hosted M2 is unchanged; M3 remains unpublished. M4 is unstarted and unauthorized.

## Current source

The owner authorized a controls-only follow-up after completed M3. **Main confirms it complete locally (2026-10-19)**: the one material metadata-failure fix is **RESOLVED**, **ship at ONE-SCORED-FIX verdict-pass scope**, not blanket whole-product/publication approval. All 18 refreshed captures were reopened with no regression attributable to the fix; earlier full controls review found no material visual/a11y regression. [Revision report](../docs/reports/discovery-controls.md). This supersedes earlier active controls/text fields only, preserving Current and M3's completed baseline.

- `index.html` and `current-original.html` both load `/src/current-original.tsx` → `GuestApp`.
- `GuestDiscovery.tsx`: API search/resolution, sequenced/deduplicated facets bootstrap, explicit discovery, “My limits” modes → platform → genre → price controls and conditional exclusions/undo. Submission clears stored preferred/unwanted terms; the old advanced/text-term UI is removed. If facets are unavailable, stored `max_price_cents: null` / `free_only: false` stays unbounded in requests and persistence; the disabled slider displays Any price / accessible No maximum price. Its finite internal rendering scale never becomes a budget.
- `DiscoveryControls.tsx`: native checkbox disclosures for all three selectors and a two-handle one-cent native price slider. All modes/genres must match; any platform may match. Four desktop fields in one row, ≤900px two columns, ≤640px one column in the same order.
- `GuestGameRow.tsx`: genre-led artwork rows, dated evidence, tradeoffs, save, exclusion and feedback controls.
- `GuestLibrary.tsx`: `/saved`, cached metadata, manual availability check, history and feedback management.
- `guest-store.ts`: validated v2 persistence, defined v1 migration, bounds, tab updates, recovery and clear/request invalidation. Optional minimums in older v2 preferences/history normalize to zero without a format bump; `GuestLibrary.tsx` displays history ranges.
- `current-original.css`, `Icon.tsx`, self-hosted Anton and bundled Manrope preserve the selected identity. [DESIGN.md](../DESIGN.md) and the [single official surface brief](../.impeccable/surfaces/frontend-src-current-original-tsx.md) document it.

The frozen eight-game catalog and old `verify-current-original.mjs`/route tests are removed. The current application uses the real API and backend ranking, not automatic local genre-overlap ordering. Results appear on explicit submission; changing taste requires rediscovery. Initial/clear defaults remain Hades, Windows, single-player and maximum recorded $20 USD.

Saves are independent of Interested. Limits: 50 favorites, 200 saves, 500 latest-per-game feedback entries and 20 recent summaries. Storage is labeled **Saved on this device** or truthfully **Temporary in this tab**. Clear removes owned local/session data, resets defaults and invalidates stale work across tabs. Cached saved prices retain their original observation dates; remote artwork is not an offline guarantee. [Storage/ranking contract](../docs/operations-m3.md).

## Run locally

Install/configure the backend and frontend using [setup](../docs/setup.md). From installed `frontend/`:

```powershell
# Dev defaults to the local API on port 8000.
npm run dev
```

Both `http://127.0.0.1:5173/` and `/current-original.html` serve the same application; `/saved` is the saved library. Old local `/system` and `/games/:id` UI routes are not current surfaces.

For build/preview, set the public API origin before compiling:

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run build
npm run preview
```

Preview uses port 4173. The commands above build for API :8000. **Main has restored the final interactive build to API :8001** after successful controls verification on owned :8002. The test stopped :8002 and did not change the owner's :8001 server; no persistent owned background API remains. Keep a matching backend running in your terminal. For this :8001 build, from repository root in a separate terminal:

```powershell
$python = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv\Scripts\python.exe'
$env:ALLOWED_ORIGINS = 'http://127.0.0.1:4173'
& $python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8001 --workers 1
```

Leave that terminal open for interactive preview. Restart the older :8001 backend, start/reuse preview :4173, then refresh both `/` and `/current-original.html` so minimum-price/facet-maximum code is loaded. Existing ignored `backend/.env` suffices; no new credentials or migrations. No database credentials belong in frontend settings. The live helper defaults to :8001 and also allows :8002 via `M3_API_ORIGIN`; preview must be built for the same origin and the selected API port must be free.

## Current local verification

**Final controls checks passed:** full 21 frontend tests (15 browser + 6 storage) passed again, including facets-503 legacy unbounded request/persistence, minimum normalization and term clearing; TypeScript/build/targeted lint pass. Backend 51/Ruff/strict mypy13/OpenAPI/generated drift and detector `[]` remain passed. Refreshed opt-in live test passed nine real API cases and 18 clean desktop/mobile scans after the fix, using owned :8002 and the existing restricted catalog. A transient search exceeded the old five-second assertion; the test now awaits the real response within the existing 75-second network budget without autoretry, and the final run passed. [Refreshed report](../docs/reports/discovery-controls-live.json). **Main-confirmed ship at ONE-SCORED-FIX verdict-pass scope.** Normal `npm test` starts its preview and excludes live tests; port 4173 must be free. Local-only wrappers start preview if missing/reuse it and stop owned processes; normal live config still expects preview running. [Procedure](../docs/operations-m3.md#explicit-live-m3-check).

Actual E: source was compiled/tested through the existing C: toolchain using local-only wrappers for dependency resolution, Vite dedupe and TypeScript/test aliases. This was **not** the old source-mirrored execution-copy verification. E: `npm ci` still times out; no fresh frontend installation or remote CI is claimed.

**Historical completed M3 baseline:** 49 Python/17 frontend tests, six live API cases and 12 clean desktop/mobile scans; independent reviewer marks all four material fixes **RESOLVED**, **ship at the four-scored-fixes verdict-pass scope**, with no material regression attributable to that batch in its 12 inspected captures. Main confirms M3's five gates and final handoff. [Baseline JSON](../docs/reports/m3-live-evidence.json) · [baseline completion](../docs/reports/m3-implementation.md). This remains separate from the controls one-fix verdict and is not blanket whole-product/UI release approval. Earlier exact-promotion **ship** applies only to that historical snapshot. Fresh frontend installation, remote M3 CI and real-phone checks remain unverified.

No new raster artwork is shipped: covers retain source Steam URLs, reserved aspect ratio and the unavailable fallback. Current controls captures are `.impeccable/review/discovery-controls/{initial,play-modes,platforms,genres,favorites,results,evidence,saved,device-data}-{desktop,mobile}.png`; baseline captures remain `.impeccable/review/m3/`. Viewport tests do not replace physical-phone testing.

## Restoration and selection provenance — historical

The original study's deleted source bytes were not recovered. On 2026-10-17 it was reconstructed against retained 1440px desktop and 390px mobile screenshots in `.impeccable/review/design-lab/current-*.png`. The reconstruction used a frozen catalog, compact controls, genre metadata and original composition; uncaptured picker/evidence/empty states were functional reconstructions.

The owner approved that restoration, then requested the artwork-card favorites picker: explicit Search, selected count, covers, Add/Selected actions and a double lime outline. On 2026-10-18 that exact page was selected as official and promoted unchanged to both HTML entries. [Historical selection report](../docs/reports/current-official-selection.md) retains hashes, screenshot comparisons and route-verifier results. Its byte-preservation claim applies to that promotion, not the subsequently authorized M3 functional extension.

M3 preserves this selected visual world. It authorizes neither a new design concept nor publication/M4; commit, push, deploy and next-milestone work require explicit owner permission.
