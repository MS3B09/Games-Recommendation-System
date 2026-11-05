# Catalog-connected dashboard — Task 2

**2026-11-05: implemented locally; owner dashboard review pending.** `/dashboard` contains the four metrics, eight charts and description word cloud from the original Streamlit inventory. Main navigation is now **Your taste → Discover → Dashboard → Saved games**, with theme-matched pill outlines and a lime current state. No publication or public catalog activation was performed.

**Final explicit owner scale decision:125%.** The application now defaults to **125% display scale**, across all routes, with browser zoom kept independent. [Current setting, build/check evidence and memory limitation](default-scale-120.md). The earlier observation below that no scale change had been made was accurate before these subsequent requests; do not use it to override the owner's current default.

## Owner follow-up — apparent zoom and preview connection

The owner supplied discovery screenshots showing a larger-looking page and connection failures. Source comparison confirms Task 2 did **not** change discovery's root16px size, original responsive heading scale (96px desktop maximum), controls typography, viewport meta settings or introduce CSS zoom/global transforms. Screenshot sizes/browser settings alone do not establish the owner's actual zoom level; it was not changed programmatically by this task.

The investigation did find a genuine local-preview defect: the isolated API was constructed with default5173 CORS origins, while the frontend preview runs on4173. A real request returned HTTP200 **without** `Access-Control-Allow-Origin`, so browser requests were blocked. The two resulting error blocks made discovery taller. Earlier mocked browser tests plus separate direct HTTP checks did not exercise this cross-origin boundary; those checks must not be described as a successful real-network browser journey.

The isolated preview now explicitly allows only **http://127.0.0.1:4173** and **http://localhost:4173**. Only the identity-verified owned API was replaced, and its exact tagged old schema removed; frontend preview and unrelated user services remained running. No CSS/layout/zoom change, rebuild, public activation, source recollection or migration rerun was made for this correction. A focused `tests/live-dashboard.spec.ts` passed the **actual browser** catalog resolution, facets and dashboard flow with **no API mocking**, no API request failures, and unchanged computed root16px/heading96px/CSSzoom1/bodytransformnone at1440px. Both explicit origins also returned the correct CORS header. Targeted lint/Ruff pass. Evidence: ignored `dashboard-actual-browser.json` and `dashboard-cors-followup.json`.

## What is implemented

- Current's cobalt/navy/lime, Anton/Manrope, shared header/footer and independent assistant remain. Discovery is still the home page. Dashboard has its own skip target; discovery links on dashboard/saved/not-found pages point back to the home anchors. Direct loads/reloads use existing pathname routing and the existing Netlify SPA fallback; no routing dependency.
- A flat overview strip shows **2,000 eligible games, $19.29 mean original/list USD price, 7.04% mean valid discount and 1,968 normalized developers** for the expanded snapshot. Prices and discounts each have **1,608 known / 392 unknown** records. Developer coverage is **1,999 known / 1 unknown games**; co-developers count separately. Unknown is not zero.
- Eight chart articles: free versus paid, list-price ranges, discount ranges, monthly releases with year selection, top genres, supported platforms, review-type distribution and top developers. There are twelve populated genres, so the top-15 chart truthfully displays twelve, not fabricated categories. Long company/genre names remain intact.
- Price ranges have inclusive lower/exclusive upper edges, with **$100+** inclusive at $100. Discount bins distinguish exactly 100% and exclude invalid values while retaining the invalid-data count. Free-to-play is a source boolean, not inferred from a promotional zero price.
- Release precision is respected: unknown months are not fabricated; year-only records remain selectable and counted as unknown month for their year. The actual snapshot has **1,999 known months / 1 unknown**. Month columns and counts have a native table alternative.
- **Linux(SteamOS)** counts source-verified Linux support only, with explicit disclosure that independent SteamOS/Steam Deck compatibility is unverified. Each platform shows supported, unsupported and unknown counts.
- Steam sentiment labels are retained exactly. No invented score thresholds or grouping. Missing summaries, no reviews and unlabeled summaries are distinct. Scope: all languages, all purchase types, off-topic activity filtered.
- The description word cloud uses sixty actual occurrence-ranked terms, with alphabetical ties. All normalized descriptions are processed, each within the existing 16,000-character Game bound: no combined-text truncation. Unicode NFKC/case folding; 3–24-letter tokens; explicit English function-word and game/store boilerplate stopwords in `catalog/analytics.py`; no stemming. A counted list and method disclosure accompany the deterministic, collision-free wrapping layout.
- Native counted tables accompany all eight charts. Keyboard-focusable local scrolling preserves readable 12px release-chart labels on narrow screens without page overflow. Loading, empty, unavailable, invalid-response and retry states are distinct. A failed refresh explicitly retains and labels the previous snapshot; a successful refresh replaces it without a frontend rebuild.

## Versioned backend and refresh

`GET /api/v1/analytics` reads **one compact aggregate** through the repository's active-version, repeatable-read snapshot; it does not load Game documents on dashboard requests. The response includes the catalog version/creation date, observation interval, aggregate checksum and typed datasets. `Cache-Control: no-store` avoids reuse across activation; already-open pages identify their snapshot and offer explicit refresh.

New files: `catalog/analytics.py`, Alembic **0010** / SQL **0011**, focused aggregation tests, `GuestDashboard.tsx`, frontend analytics parser, dashboard browser checks and a safe public aggregate fixture. Existing importer/repository/readiness/API/OpenAPI/generated TypeScript contracts were extended; existing Game/evidence/assistant payloads were not widened.

The migration was first applied/tested in an exact owned private schema using the actual catalog table shape, then applied additively through the existing developer migration command. `catalog_analytics` has a 256KiB document bound, active-version RLS and restricted SELECT-only grants. `catalog_versions.analytics_manifest` is a separate bounded sidecar binding the aggregate checksum/format, original artifact digest and game/metadata hashes. Deferred constraint triggers reject missing or mismatched enabled analytics at commit. Runtime validation/readiness also reject corrupt checksums, missing input identity or invalid denominators. Legacy generations without the sidecar remain usable for discovery and return explicit `analytics_unavailable` for the dashboard.

The importer deterministically builds/verifies `analytics.json` and `analytics-manifest.json` and stores them in the same transaction as catalog staging/activation. Reimport validates existing aggregates instead of overwriting mismatches. These are additive sidecars: the completed Task 1 `artifact.json`, `games.json`, `metadata.json`, `embeddings.json`, version ID and historical receipts remain unchanged. The pre-analytics import report was preserved as `task1-import-report-before-analytics.json` in the authoritative C: run before the new import report was written.

Expanded catalog: **`m2-cd9790b88f91370e69dae895`**. Analytics digest: **`5116c42f8dc97f6e2556f8789aeb664e6c7ae02c070ec1466936d4fdf8472a83`**. Actual ASGI response **6,055 bytes**. Independent read-only SQL matched the list-price/discount means, denominators and free/paid totals. Repeat import passed with the same aggregate digest. Real interruption rollback/incomplete-artifact rejection passed on the analytics-enabled importer.

For subsequent refreshes, use Task 1's [new-run collection/normalization/embedding/import workflow](catalog-expansion.md#reproducibility-and-acceptance-evidence). Metadata-enabled import now generates analytics automatically. Publish catalog/artifact/analytics together only under the release approval; do not manually update aggregates or upload a historical CSV.

```powershell
$python = '.\backend\.venv\Scripts\python.exe'
& $python -m game_discovery.db.migrate upgrade --env-file backend/.env # already applied here; future fresh environments
& $python -m game_discovery.jobs import --run-dir $newRun --env-file backend/.env
# New import builds, hash-binds and validates the analytics sidecars before commit.
```

## Checks actually performed

| Check | Result / scope |
| --- | --- |
| Full backend suite before final boundary hardening | **295 tests OK, 1 skipped**, 14.262s; no inference. Historical skipped external private-journal check remains skipped. |
| Final analytics tests after defensive input/readiness hardening | **5 passed**, 0.338s; edges, means/unknowns, full names/deduplication, partial dates, word counts, empty data, tampering, readiness and compact API behavior. |
| Backend static/contracts | All-backend Ruff; configured strict mypy30 plus the new analytics module separately; OpenAPI drift passed. |
| Real database/ASGI integration | Owned-schema migration/RLS/grants, 2,000 source pairs/count parity, missing/mismatched activation rejection, read-only API and snapshot isolation passed. A distinct one-game refresh fixture switched version/metrics atomically. Exact test schema removed. |
| Import integration | Expanded existing generation reused with same analytics checksum; interruption rolled back; incomplete artifact refused; public active unchanged. |
| Full frontend regression suite | **79 passed**, 0 failed/0 flaky, 3.4min. Main controls, discovery, saved persistence/clear, independent assistant/history/Markdown and dashboard checks included. |
| Final mobile-fix browser round | **4 passed**, 36.3s; exact selected-year/table agreement, navigation/direct reload, refresh, storage isolation, recovery/empty/invalid response, long labels. |
| Three-width dashboard scans | **1440×1000 / 390×844 / 320×640**, axe0, no horizontal page overflow or page errors. Six full/top captures plus two final supporting detail captures opened by builder. |
| Frontend static/build | TypeScript and Vite build passed; actual E: source targeted ESLint passed with zero warnings; generated API types refreshed; Impeccable detector `[]`. |

Frontend execution used the existing source-matched **C: dependency harness** and installed Chromium1243; no dependency/browser installation or fresh E: install is claimed. Initial attempts correctly exposed missing E: executables, an ignored-path lint invocation and missing default Chromium1248; corrected to existing tools and actual-source lint. An initial axe definition-list finding was fixed semantically; an ambiguous test locator was narrowed. These initial failures are not final passes. The harness restart interrupted a browser run, but identity checks found the same API/preview alive; no duplicate servers or replayed data jobs were started.

## Visual review

Impeccable was explicitly selected by the owner; its context/direction/craft-floor workflow and two bounded capture rounds were used. The available general subagent applied the shipped degraded finish-review contract because no named shipped reviewer agent is exposed. The first full review required readable mobile month labels and a denser proportional mobile word cloud; both were fixed in one batch. The reviewer opened **all eight final captures**, scored **both P1 fixes resolved**, and returned **`ship` at the two-scored-fixes UI scope only**, with no regression attributable to that batch observed. This is not whole-product, backend, hosted or owner acceptance. The established dismissible assistant greeting was retained, not redesigned to conceal its existing overlay behavior.

No new shipping raster artwork was created. Existing owner favicon, fonts and Steam artwork/provenance are unchanged. Pre-existing design-sidecar narrative drift is not repaired as part of dashboard work.

## Inspection runtime and release boundary

Open **http://127.0.0.1:4173/dashboard** and hard-refresh if already open. The current preview build explicitly targets **127.0.0.1:8002** through a process-local build override, not an ignored `.env` edit. API8002 serves the actual expanded generation from an owned private schema in the **same database**, using restricted read-only transactions/RLS and the matching pinned local encoder. Its discovery and dashboard version/count agree. AI is intentionally disabled in this isolated preview; source assistant behavior and its regressions remain preserved, but no live inference was spent.

The read-only preview intentionally retains **`catalog_preview_d459f68ee4da`**, tagged `game-discovery-owned-expanded-acceptance-v1`, while it is running for owner inspection. This is not an unexplained leftover: graceful exit of the verifier removes that exact owned schema. Current identities after the CORS follow-up: API launcher22072/child9176, existing preview3548. Prior launcher1492/child5532 and schema`catalog_preview_49beda1b2193` were identity-verified, stopped/removed only for this correction. Always recheck listener/parent identity before stopping, never use stale PIDs blindly. No unrelated user service was stopped/restarted.

Reproducible isolated preview (only if8002 is free; do not duplicate the running one):

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& .\backend\.venv\Scripts\python.exe backend/scripts/verify_expanded_catalog.py `
  --run-dir C:/Users/User/AppData/Local/Temp/opencode/catalog-expansion-2000-20261105 `
  --env-file backend/.env --output data/reports/dashboard-expanded-runtime.json --serve-port 8002
# Separate frontend terminal: process-local VITE_API_BASE_URL=http://127.0.0.1:8002, build then preview.
```

The analytics-only migration/activation verifier can run separately without leaving a schema:

```powershell
& .\backend\.venv\Scripts\python.exe backend/scripts/verify_analytics.py `
  --run-dir C:/Users/User/AppData/Local/Temp/opencode/catalog-expansion-2000-20261105 `
  --env-file backend/.env --output data/reports/dashboard-backend-verification.json
```

Measured while the owner-review preview is retained: DB **50,386,611 bytes including the private copy**, production analytics relation **49,152 bytes**, preview API peak **346,279,936 bytes**. These are bounded local observations, not a hosted SLA. Security advisor `[]`; performance advisor has the two pre-existing production unused-index INFOs and two private-preview unused-index INFOs, retained rather than removed to manufacture a clean report ([explanation](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index)).

Public active catalog remains **40**, version **`m2-649714e8b26775165f105d02`**, original document digest unchanged. Public 2,000-game/analytics activation, semantic cloud provisioning and latest-source deployment remain **Task 3**. No commit/push/deploy, paid resources, new dependency/model/quota/env-file changes, live LLM calls or historical evaluation replay. Physical-phone and hosted dashboard acceptance remain unverified.

**Next: owner reviews the dashboard. Stop before Task 3 until its explicit approval.** Machine receipts are ignored under `data/reports/dashboard-*.json`; the small public test fixture intentionally contains aggregate counts only, not credentials/raw snapshots/private capabilities.
