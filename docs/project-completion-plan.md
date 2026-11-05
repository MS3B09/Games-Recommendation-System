# Project completion plan

**Owner direction: 2026-11-04; implementation requested 2026-11-05. Status: [Task 1 complete as a verified staged handoff](reports/catalog-expansion.md); [Task 2 dashboard implemented locally, awaiting owner review](reports/dashboard-implementation.md).** The owner approved Task 2 and selected Impeccable, including `/dashboard` and clearer four-item header navigation. Expanded games/vectors/metadata/analytics share `m2-cd9790b88f91370e69dae895`; public activation remains deferred to coordinated Task 3. Inspect the actual expanded read-only local preview at http://127.0.0.1:4173/dashboard. Public 40 unchanged. Stop before Task 3; no publication authority from this dashboard request.

**Superseding owner authorization — 2026-11-05:** the owner explicitly selected **Publish now**, authorizing Task 3's commit/push and existing free-host deployment. The 2,000-game generation must be the shared default for discovery, chat, dashboard and other catalog reads. Task 3 is now **in progress**; the earlier stop/await-publication-permission statements are historical. The local preview now includes real archive/metered AI services. Public activation still requires the compatible hosted backend and matching semantic artifact first; final hosted acceptance remains outstanding. [Current release work and access blocker](reports/project-release-2026-11-05.md).

This is the authoritative remaining-work plan. It supersedes earlier M5, R4, assistant-closeout and evaluation continuation instructions as a future task list. There are exactly three remaining tasks:

1. Expand the current 40-game catalog.
2. Add a better-designed dashboard with the same analytics as the [original Streamlit dashboard](https://steam-recommender-system.streamlit.app/).
3. Publish the latest application to GitHub and deploy it to Netlify and FastAPI Cloud, verify the release, then mark the project complete.

Existing evaluation results, failures, missing judgments and limitations remain truthful historical evidence. They are not a fourth workstream, and unfinished experiments are not reclassified as passes. Do not resume old evaluation journals or change their hashes.

## 1. Confirmed decisions and execution boundary

| Decision | Owner-confirmed requirement |
| --- | --- |
| Final catalog size | **2,000 total eligible games**, approved after the audit on 2026-11-05, including retained existing identities. |
| Selection | Recognizable popular games plus lesser-known titles across genres, budgets, platforms and play modes. Existing database/data may supply candidates. |
| Dashboard population | The same active catalog used by recommendations. When that catalog is expanded or refreshed, dashboard data updates with it. |
| Platform presentation | Owner requested **Linux(SteamOS)** on 2026-11-05. Count source-verified Linux support under that label and disclose that this is not independent SteamOS/Steam Deck compatibility verification; no separate inferred SteamOS count. |
| Dashboard feature scope | Preserve the original analytics inventory; improve its organization, readability and usability. |
| Publication | GitHub, existing Netlify frontend and existing FastAPI Cloud backend form the final task. |
| Current request | Owner authorized Task 3 with **Publish now** on 2026-11-05 and requires the 2,000-game catalog across all app services. Deployment/access verification and final acceptance remain. |

When implementation is requested, start with Task 1's audit. Present its measured capacity and recommended target for the owner's decision before bulk expansion. Retain the existing stop-and-report boundary between the three tasks. Confirm installed frontend skills before dashboard implementation. Ask about unresolved product decisions rather than inventing them.

Existing constraints continue: free only; one PostgreSQL/pgvector database; React/TypeScript frontend and modular Python backend; guest use; US/USD recorded prices; Scrapling as the only HTML scraping framework; sequential CPU-only jobs suitable for the owner's 8 GB machine. Preserve Current's identity, main discovery, saved data and independent assistant.

## 2. Verified starting point

Repository inspection and a read-only visit to the live Streamlit dashboard on 2026-11-04 established:

- The active catalog is documented as 40 games. Recount it during the audit; this documentation pass did not query the database.
- `backend/src/game_discovery/jobs/catalog.py` already collects, normalizes, embeds, stages and atomically activates versioned catalogs. `jobs/__main__.py` exposes the commands.
- Collection accepts **1–100 IDs per run**. Normalization and embedding currently load whole JSON collections; checkpoint rewrites and per-record database work need measurement at the selected size.
- `CatalogRepository.chat_title()` scans a complete compact title list and fails above `TITLE_CATALOG_LIMIT` (256). Trace its actual callers, including compatible older chat endpoints, before changing it. The native assistant also has a separately bounded, paginated `assistant_search()`.
- The normalized `Game` document has descriptions, genres, three platform states, play modes, explicit free-to-play and recorded final USD prices. It does **not** yet retain developers, release dates, original/list prices, discount percentages, review summaries or independent SteamOS support.
- Existing selected sources are Steam Store appdetails and aggregate appreviews, with selective Scrapling enrichment where necessary. Bulk collection currently uses appdetails; review probing exists in `jobs/probe.py`.
- The [legacy audit](reports/data-audit.md) found 17,370 dashboard rows and 3,000 recommendation rows, with unreliable platform zeros, missing eligibility/provenance and many missing prices/review labels. These are candidate leads, not ready-to-activate catalog records.
- The old [capacity experiment](reports/feasibility.md) used synthetic vectors/associations and projected 6,000 games. That historical estimate is **not** the new target or evidence that today's full catalog/archive fits.
- `GuestApp.tsx` uses simple pathname routing; no router or chart package is currently installed. Official routes are `/`, `/current-original.html` and `/saved`. There is no implemented dashboard route.
- The latest local assistant/UI is ahead of the last documented hosted M2 release. Actual deployed revisions and current provider settings must be checked in Task 3.

## 3. Task 1 — expand the catalog

### 1A. Audit capacity and agree the target

1. Read the existing catalog manifest, import/activation code, source audit and current database schema. Record active version/count, field coverage, table/index/database sizes, archived-chat storage, retained catalog generations and local disk/RAM availability. Use restricted read access for inspection; scratch measurements must not activate or replace the public catalog.
2. Build a deduplicated candidate manifest keyed by Steam app ID. Retain current eligible games and source candidate leads from the existing database/CSVs; supplement recognizable gaps. Record why a candidate is included and its known coverage categories. Do not infer popularity from app ID or call an unverified title popular.
3. Use a bounded pilot within the current 100-ID collection limit, covering the requested variety and the dashboard's required fields. Record collection success, quarantines, field coverage, bytes/game, embedding time/memory, import time and filtered retrieval latency. Keep a fixed pilot manifest and record actual failures.
4. Measure storage with the **real proposed documents and indexes**, including dashboard aggregates, active + staging + retained rollback data, conversation storage and operational headroom. Recheck actual Supabase/hosting free allowances. Retain the existing 350 MB database and 400 MB API working targets unless measurements require an owner decision; these are engineering targets, not current measurements.
5. Compare a few feasible catalog sizes using the measured costs, selection coverage, source reliability and collection time. Account for exact retrieval, title resolution, search offsets, response limits and the two-second database read timeout. A storage-only projection is insufficient.
6. Deliver `docs/reports/catalog-capacity-audit.md` with measurements, proposed target, candidate mix, missing-field decisions and estimated collection time. **Ask the owner to select the final total eligible-game target.** If reliable SteamOS or another required dashboard field cannot be sourced, present that gap here; do not silently remove it or invent values.

### 1B. Extend the existing pipeline for the approved size and fields

**Change locations:** `jobs/catalog.py`, `jobs/__main__.py`, `catalog/contracts.py`, `catalog/repository.py`, relevant retrieval callers, `backend/alembic/versions/`, `backend/migrations/`, and existing catalog/import/retrieval tests. Add files only for a concrete responsibility missing from those modules.

- Retain one sequential collector. Replace the hardcoded 100-ID total ceiling with a documented, validated bound appropriate to the approved target, preserving per-request byte/time limits, immutable run identity, saved snapshots and per-ID checkpoints. Do not just remove all bounds. Keep failed IDs visible; explicit resume may retry collection failures, while verified successes are reused. Stop/checkpoint on source throttling or access failures; no bypass or tight retry loop.
- Carry the full selected catalog in **one generation**. Repeatedly activating individual 100-game batches would replace the active catalog with the last batch. If batching becomes necessary for memory, merge validated batches into one complete manifest before staging/activation.
- Add optional, validated dashboard metadata to the immutable catalog documents, with source URL, observed time, hash and field evidence. Preserve old documents with missing new fields as unknown. Keep legacy artifact/hash semantics compatible; version the new normalization/analytics format explicitly where necessary rather than replacing historical manifest hashes.
- Retain Steam app ID identity, eligibility checks and stable saved-game references. Exclude unsupported content according to the existing released-standalone policy; keep Early Access labeling. Preserve unknown versus false/zero.
- Dashboard metadata: developer names as complete strings/arrays; release date with precision/raw source retained; original/list USD cents separately from final USD cents; discount percentage; review label/counts and documented review scope. Do not split company names at commas. Never infer SteamOS/Deck compatibility from Linux support.
- Keep the pinned 384-dimensional float ONNX representation and semantic-text rules. Price/review/developer analytics changes alone should not force new embeddings when semantic text/model bytes match. Reuse existing checkpoints by verified content/model identity; measure whether cross-run reuse is needed before adding it.
- Profile whole-file JSON loads/checkpoint rewrites and sequential import at the approved size. Make the smallest bounded-memory changes needed; do not introduce worker infrastructure or an N×N similarity matrix.
- Resolve the 256-title limit for affected public paths before activating a larger catalog. Prefer complete parameterized database matching for exact/normalized identities plus explicitly bounded ambiguity/suggestion handling. Do not claim absence from a truncated title scan. Preserve existing title/reference semantics and test a match beyond the old cutoff.
- Preserve strict old API parsing: new internal dashboard fields must not accidentally widen assistant evidence payloads or break frozen legacy responses. Update affected serializers, generated contracts and actual callers deliberately.

### 1C. Stage, verify and activate

1. Collect/normalize the approved candidate set in a new versioned run directory. Count **eligible unique games**, not requests or successful HTTP responses, toward the approved target. Report quarantines and replacement candidates; ask if the agreed coverage/target cannot be met.
2. Build embeddings and deterministic analytics inputs; verify every eligible app has matching document/vector/provenance. Stage one complete generation with the existing privileged developer import path, never serving credentials.
3. Use focused existing checks for identity, missing data, eligibility, hard filters, idempotence and rollback. Add only checks needed for new fields/limits and failed or interrupted operations. Measure actual expanded-catalog storage, memory and retrieval once; report limitations honestly.
4. Review compatibility with the currently deployed M2 API **before activation**. It may strictly reject new document fields. If incompatible, retain the current active version and stage the expanded generation for coordinated activation with Task 3; verify it in an isolated local/scratch environment for Task 2. Do not break the live site by activating first.
5. When compatible, atomically activate the validated generation. Preserve the prior manifest/version and verify rollback using the existing validation path. Do not delete old generations or archive usage to manufacture capacity; propose an explicit retention decision if space requires it.
6. Update catalog operations and write `docs/reports/catalog-expansion.md`: target/actual count, coverage, missing fields, provenance, model/artifact identity, resource measurements, activation or staged-only state, rollback reference and runnable refresh commands.

**Task 1 done:** owner-selected target met; variety and eligibility documented; artifacts/staging checks pass; expanded catalog available for dashboard development; activation state explicit; current discovery/chat/saved-ID contracts supported at the selected size. Report and stop before Task 2.

### Existing command family to reuse

From the repository root, after implementation is authorized, with the existing working backend environment:

```powershell
$python = '.\backend\.venv\Scripts\python.exe'
& $python -m game_discovery.jobs audit --input game_data_for_dashboard.csv --input games_data_recomendation.csv --output data/reports/catalog-expansion-audit.json
# Set $idsFile, $runDir and $cacheDir to the approved manifest, NEW run and existing pinned model cache.
& $python -m game_discovery.jobs collect --ids-file $idsFile --run-dir $runDir --resume
& $python -m game_discovery.jobs normalize --run-dir $runDir
& $python -m game_discovery.jobs embed --run-dir $runDir --cache-dir $cacheDir --batch-size 8 --resume
# Developer database writes: use only the reviewed target and approved migration/activation sequence.
& $python -m game_discovery.jobs import --run-dir $runDir --env-file backend/.env
& $python -m game_discovery.jobs activate --run-dir $runDir --env-file backend/.env
```

These are existing command names, not evidence that an expanded run exists. Today `collect` still rejects more than 100 IDs. `$idsFile`, `$runDir` and `$cacheDir` must be set explicitly; never substitute old frozen evaluation paths. Any newly needed flags must be implemented and documented before use.

## 4. Task 2 — catalog-connected dashboard

### Exact feature inventory

Confirmed against both live Streamlit and `app.py` lines 98–343 on 2026-11-04. Preserve the **analytical questions**, with accurate data and clearer presentation. Historical values such as 17,370 games, $11.10 average price and 2.05% discount are not target values for the new catalog.

| Original item | Required new-catalog definition and presentation |
| --- | --- |
| Total Games | Unique eligible games in the displayed active catalog version. |
| Avg. Price | Mean known recorded **original/list** USD price, matching the original metric's meaning; show priced-game denominator and unknown count. Do not silently replace it with mean discounted price. |
| Avg. Discount | Mean valid recorded discount percentage, with known/unknown denominator. Unknown is not 0%. |
| Total Developers | Count distinct normalized developer identities/names with source-supported data. Explain that co-developed games can count for multiple developers. |
| Games Released by Month | January–December counts with release-year breakdown; retain month/year exploration. Exclude unknown month from monthly totals and show its count. Do not fabricate a month for year-only dates. |
| Free vs Paid Games | Explicit free-to-play versus explicitly paid; separate unknown. A temporary zero-price promotion is not free-to-play. |
| Games by Price Range | Original/list USD price buckets: [0,5), [5,10), [10,20), [20,50), [50,100), [100,+∞). Label the last **$100+**, correcting the old `>100` label at its boundary. |
| Games by Discount % | [0,10), [10,25), [25,50), [50,75), [75,90), [90,100), exactly 100%; preserve an explicit invalid/over-100 data-quality count rather than presenting impossible discounts as valid offers. |
| Top 15 Game Genres | Count each distinct full genre once per game; sort descending with deterministic name ties. Multi-genre totals can exceed total games. Never split “Free to Play” or “Early Access” into stray words. |
| Supported Platforms | Owner's 2026-11-05 revision: Windows, macOS and **Linux(SteamOS)**. The latter counts source-verified Linux support, with a clear scope note that independent SteamOS/Steam Deck compatibility is not verified. Show unknown Linux states; do not create an inferred separate SteamOS count. |
| Top 10 Developers by Game Count | One count per game/developer; deduplicate names within a game; retain complete company names. Show long labels legibly. |
| Review Type Distribution | Source-supported sentiment labels, with missing/no-reviews distinguished and the review collection scope shown. If grouping source labels into Positive/Mixed/Negative, define the mapping explicitly; do not invent score thresholds. |
| Word Cloud from Game Descriptions | Actual cleaned catalog description terms, deterministic frequencies/layout, visible count/list alternative; document stopwords, case folding and any per-description bound. No silent first-million-character truncation. |

The original source contains no separate top-publishers chart or numeric review-count distribution chart; a comment/README mention is not another required visualization.

### Backend and refresh contract

1. Add a typed `GET /api/v1/analytics` endpoint under the existing API, with a repository read using the same active-version snapshot as discovery. Proposed response: `catalog_version`, generation/observation dates, eligible total, field coverage, the four metrics, eight chart datasets and bounded word frequencies. This is a **planned endpoint**, not currently implemented.
2. Build one compact deterministic analytics artifact per complete catalog generation during normalization/import, validate it against the documents, and store it alongside that version in the same database. Bind its checksum/version to the generation manifest. Select the smallest schema addition after inspecting current tables; use an additive migration, active-version RLS and restricted read grants if a new relation is needed.
3. Publish catalog and analytics together through the existing atomic activation boundary. Missing/mismatched aggregates must fail readiness/activation for new dashboard-enabled generations, not silently display another version's totals. Older catalog generations without analytics return an explicit unavailable response.
4. Read only compact aggregate data per dashboard request, not every full game document. Keep request timeouts/bounds and empty/error semantics. Include the version in cache identity; never cache independently of catalog activation. A reload or explicit refresh fetches the current generation; an already-open page identifies its snapshot. No rebuild or manual CSV upload is required after catalog refresh.
5. Extend `backend/openapi.json`, generated `frontend/src/api/schema.d.ts`, client parsing and existing contract checks. Keep discovery/assistant contracts compatible.

### Frontend implementation

**Change locations:** `frontend/src/GuestApp.tsx`, a new focused `GuestDashboard.tsx`, `frontend/src/api/`, `current-original.css`, existing browser checks, `DESIGN.md` and the official surface brief.

- Add `/dashboard` and a clear **Dashboard** navigation link using the existing pathname-routing pattern. Update skip-link targets, active navigation and discovery anchors on non-discovery pages. Direct loads/reloads must work through the existing Netlify SPA fallback.
- Reuse Current's cobalt/navy/lime palette, Anton/Manrope typography, header, footer and responsive spacing. Keep discovery the main landing page.
- Organize the same inventory into an overview metric row, pricing/free-paid, release/genre/platform coverage, developers/reviews, then description themes. Use readable horizontal bars for long ranked labels and a full-width word cloud; preserve year exploration with a labeled control. This is an implementation layout proposal within the approved visual system, not a completed design review.
- Use semantic HTML/CSS/SVG for straightforward bounded charts; no chart library is installed today. Add a library only if the actual interactions justify it, after checking current docs and bundle/accessibility cost. Do not install React Router merely for one route.
- Provide exact text values and an accessible table/list equivalent. Do not rely on color, hover-only values or tiny legends. Support keyboard access, long labels, zero/one categories, unknown fields and narrow screens.
- Distinguish loading, empty catalog, missing-field coverage and failed-request states; use the existing error/retry conventions. Display recorded-data dates and catalog scope, not “real-time Steam stats” or fixed legacy counts.
- Keep dashboard viewing read-only, without changing saved preferences or injecting dashboard filters into chat/discovery. The shared assistant remains independent.

### Verification and completion

Reuse existing test infrastructure. Add focused aggregation checks for denominators, bucket edges, duplicates, partial dates, unknown data and catalog-version consistency; verify refreshed activation produces updated metrics. One integration path should compare aggregate counts against its actual catalog snapshot.

Check all thirteen inventory items, dashboard navigation/direct reload/back links, keyboard/table equivalents, loading/error/retry and empty/long-label states. Inspect desktop/mobile at the existing 1440/390/320 widths for readable charts, no horizontal page overflow and accessibility issues. Run affected API/static/build checks and existing discovery/saved/chat regressions.

**Task 2 done:** all four metrics, eight charts and word cloud implemented against the expanded catalog; truthful missing-field handling agreed; catalog refresh updates analytics; responsive/accessible behavior verified; owner reviews the dashboard; record `docs/reports/dashboard-implementation.md`. Report and stop before Task 3.

## 5. Task 3 — publish, deploy and complete

### Release preparation

1. Confirm Task 1/2 evidence and the intended release revision. Review the working tree, remote and `main` branch. Include the complete latest local application, not only dashboard files. Reuse existing backend/frontend CI; do not create another evaluation program.
2. Run the existing locked backend tests, Ruff, mypy, OpenAPI drift, frontend lint/type/build/API-type checks and browser suite for the release candidate. Fix release regressions; document actual results and limitations. Confirm a clean install/build works without the private C: execution harness.
3. Inspect repository contents to exclude `.env`, credentials, private chat capabilities, raw archives, local model caches and generated private journals. Retain intended public evidence and lockfiles. Raw Steam snapshots stay local; publish safe manifests and reproducible commands.
4. Recheck current free plans/access for GitHub, Netlify, FastAPI Cloud, Supabase and Groq. Use existing connected projects and one database. Ask for missing access through the provider's login/settings; never request secret values in chat.
5. Confirm hosted migration level with the developer migration tool. Task 1B added/applied Alembic `0009` for title identities and separate dashboard metadata; inspect the actual source/database head again rather than assuming `0002` or blindly rerunning initialization. Apply only reviewed pending migrations, including dashboard changes, preserving all catalog, chat and quota data. Runtime `DATABASE_URL` stays restricted; `MIGRATION_DATABASE_URL` stays developer-only.
6. Prepare the full hosted semantic runtime: current `pyproject.toml` places ONNX/tokenizer/NumPy in optional extras, and local `QUERY_*_PATH` settings point to machine-local files. Package/install only the needed serving dependencies and provision the exact pinned tokenizer, ONNX file and matching artifact manifest through a verified build/deploy path. Validate hashes, host paths and memory. No downloads during user requests, no C: paths in cloud configuration, and no silent keyword-only substitute for a working semantic release. If the free host cannot support this, present the measured blocker to the owner.
7. Restore normal release runtime allowances **50 calls/day and 500,000 reserved units/day** under the previously documented post-evaluation policy, preserving consumed counters and database ceilings. Verify effective settings and friendly exhaustion handling; a lower runtime cap may remain exhausted until normal rollover. Never reset/refund counters to get a green release check. Any owner-requested different public quota needs an explicit decision.

### Deployment targets and configuration

| Target | Existing destination / required configuration |
| --- | --- |
| GitHub | `MS3B09/Games-Recommendation-System`, existing `main`; verify remote before publication. |
| Netlify | `https://steam-discovery.netlify.app/`; base `frontend`, existing locked build command from `netlify.toml`, publish `dist`, SPA fallback. |
| Public frontend setting | `VITE_API_BASE_URL=https://steam-discovery-api.fastapicloud.dev`, build scope; never use localhost in production. |
| FastAPI Cloud | Existing `steam-discovery-api` app; application directory `backend`, `game_discovery.api.main:app`, locked Python/dependencies. |
| API connection/CORS | Secret restricted `DATABASE_URL`; `ALLOWED_ORIGINS=https://steam-discovery.netlify.app`. |
| Assistant runtime | Secret `GROQ_API_KEY`; explicit verified existing `GROQ_MODEL` (currently documented `openai/gpt-oss-120b`), `AI_ENABLED=true`, release allowance settings. Do not rely on a different code default. |
| Semantic runtime | `QUERY_TOKENIZER_PATH`, `QUERY_MODEL_PATH`, `QUERY_ARTIFACT_PATH` resolving to verified files inside the hosted runtime. |
| Scale | Free/Hobby settings; preserve min 0/max 1 replica and verify one serving worker where supported. |

### Publish and verify

1. Once Task 3 is started by the owner, commit the reviewed release and push to the existing GitHub branch. This documents publication as the final task; it does not execute it now. Account for connected auto-deploys: finish compatible migrations/runtime preparation first, and coordinate frontend activation so it does not depend on an API still building. Do not assume the two hosts deploy sequentially.
2. Verify GitHub CI and both provider builds target the intended commit. Confirm FastAPI health/readiness, migration compatibility, restricted DB access, semantic availability and the active catalog/analytics version. If Task 1 was staged-only, activate the expanded generation only after the compatible backend is ready.
3. Publish/confirm the matching Netlify artifact. Verify `/`, `/current-original.html`, `/saved`, `/dashboard`, direct reloads, cross-origin API calls and favicon/assets. Confirm built JavaScript uses the public API origin.
4. Exercise the hosted main journey: favorite search, constraints, recommendations, Save, Not For Me/Already Played, persistence and clear-data behavior. Confirm dashboard totals match the hosted active catalog and every visualization is present.
5. Verify assistant opening, reload/New chat and availability/error handling. Use a bounded fresh smoke conversation to verify the deployed integration only when current free provider/application headroom permits; record its actual calls, result and cleanup. Do not resume historical experiments or claim a smoke check establishes broad recommendation quality. If blocked, record the blocker and finish that release check when available.
6. Check cold-start recovery and representative hosted resource/latency behavior. Record observed values and accepted limitations without inventing SLA or quality improvements. Confirm useful core discovery/dashboard when AI is unavailable.
7. Keep prior deploy IDs and the prior compatible catalog/analytics manifest as rollback references. Roll back compatible app/data versions together if release verification fails; no destructive database downgrade or usage reset.
8. Update README, documentation index, product/implementation/progress/deployment docs and walkthrough with actual commit, catalog count/version, public URLs, checks and remaining limitations. Write `docs/reports/project-completion.md` and obtain the owner's final completion confirmation.

**Task 3 done / project complete:** the agreed expanded catalog and full dashboard are live; the latest source is on GitHub; both deployed revisions are verified; existing core journeys work; free-only operation/configuration and recovery are documented; the owner confirms the released result. Historical incomplete evaluation remains disclosed, not an extra completion task or a claimed pass.

## 6. Documentation and handoff rules

- Use this file for remaining scope/sequence; `AGENTS.md` for retained constraints and latest owner direction; `docs/progress.md` for actual task status.
- `docs/README.md` identifies current operational references and historical material. Older plans, design studies, reports and frozen fixtures never override this plan's task list.
- Preserve dated reports, source-locked experiments, owner ratings and frozen hashes. Do not rewrite measurements to match a new catalog or call old results expanded-catalog evidence.
- Each task handoff reports changed files, commands/checks actually run, measurements, blockers and the next permitted action. Tests should verify the new behavior and release compatibility, not expand into another long-running assistant campaign.
- Unresolved decisions are explicit: final count after audit; owner choice if a required field is unavailable or capacity/hosting is inadequate; dashboard acceptance; final release acceptance. No additional product features are implied.

## 7. Documentation consulted

Source inspection: `app.py`, catalog contracts/repository/jobs/CLI, frontend routing/package scripts, runtime settings, deployment config and retained source/capacity reports. Live dashboard inventory inspected read-only on 2026-11-04; no game recommendations or AI calls were submitted.

Current official documentation was consulted through Context7 for [FastAPI Cloud application directories](https://fastapicloud.com/docs/builds-and-deployments/application-directory/) and [GitHub integration](https://fastapicloud.com/docs/source-control/github-integration/), plus [Netlify build configuration](https://docs.netlify.com/build/configure-builds/overview/) and [SPA rewrites](https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/). Recheck actual account allowances and supported artifact/build configuration during Task 3; historical free-plan numbers are not a current account receipt.
