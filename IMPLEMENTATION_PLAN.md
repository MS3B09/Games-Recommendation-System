# Technical Implementation Plan

## Current implementation authority — 2026-11-05

The owner replaced the remaining roadmap with **catalog expansion → dashboard → publication/deployment**. The detailed, actionable plan is [docs/project-completion-plan.md](docs/project-completion-plan.md); use it before any older instructions in this document.

| Task | Required outcome | Status |
| --- | --- | --- |
| 1. Catalog expansion | Capacity audit, owner-selected total size, diverse verified games, reproducible full-generation import/refresh | **Complete as verified staged handoff:** 2,000 games/vectors/metadata; public activation coordinated with Task 3 |
| 2. Dashboard | Original four metrics, eight charts and word cloud; improved Current design; same active catalog and refresh lifecycle | **Implemented locally, awaiting owner review**; Impeccable selected, real expanded preview at `/dashboard` |
| 3. Publish and deploy | Latest code on GitHub; verified Netlify + FastAPI Cloud release; owner confirms completion | Planned; follows dashboard acceptance |

After the capacity audit, the owner approved **2,000 total eligible games**. They are collected, embedded, staged and verified as `m2-cd9790b88f91370e69dae895`; [results and refresh commands](docs/reports/catalog-expansion.md). Keep the public 40-game snapshot and existing semantic artifact coordinated until Task 3. Dashboard data is not a separate historical CSV population.

The owner authorized Task 2 and selected Impeccable; [dashboard implementation and verification](docs/reports/dashboard-implementation.md) are ready for owner review. **Stop before Task 3**; no commit/push/deploy or public activation yet. Retain stop/report boundaries between tasks and frontend-skill confirmation for future UI work. Existing R4/assistant evaluation backlogs are historical limitations, not additional completion gates. Preserve frozen experiments and honest results. Free-only, one-database, Scrapling-only and existing product/identity constraints continue.

## Historical technical baseline and milestone record

The dated entries and M0–M5/R0–R4 sequences below are reference material. Their old next actions, targets and publication prohibitions do not override the three-task plan. Proposed technologies below are not proof they are installed; the completion plan records inspected implementation paths.

**Latest R4 — 2026-10-27:** [quota amendment/progress](docs/reports/r4-quota-increase-2026-10-27.md). Approved100/1,500,000temporary daily limits applied preserving usage; defaults50/500,000 retained. Same v6 source/outputs continue via documented operational wrapper.193backend tests and15scratch quota checks pass. Proposed development13/13passes; held-out32attempts/8prose failures,95calls today, paused by conservative provider-token headroom. Human/mandatory/latency gates remain, R4 not accepted. Resume only unattempted held-out work with a fresh receipt; restore runtime after R4, no counter reset or M5/publication authority. Older statuses below are historical.

**Latest R4 authority — 2026-10-26:** [v6 checkpoint](docs/reports/conversational-rag-r4-resume-2026-10-26.md) supersedes October25 status. Additional inference approved, today's50calls/393,494units exhaust daily calls.189backend tests/313integration assertions; explicit played/undo and durable journal fixes verified. Current9/26development attempts, baseline claim failure retained; full held-out live/human/representative latency gates pending. Preserve C: authoritative journal and resume only unattempted v6 work on later UTC days. No new setup or M5/publication authority.

## Current next-work authority — 2026-10-25

**Latest R4 continuation:** owner approved the additional inference needed within free-only limits. [Fixes/checkpoint](docs/reports/conversational-rag-r4-continuation.md): strict max-four generation, unsupported-platform metadata and continuation references verified; live proposed core journey3/3; runtime retrieve p95487ms/90warm samples.180backend tests and313integration assertions pass. Current live paired development13/26turns; today49/50calls/390,773reserved units pauses further two-call turns. Resume with a fresh later-UTC-day receipt under existing approval. Full held-out live/human/serving-total-latency gates remain; R4 is not accepted. No new key/config/model or M5/publication authority. The exhausted-pilot entry below is historical.

**R4 update: in progress, acceptance incomplete.** Owner approved R4 and a development pilot/fix-retest, not full held-out live generation. [R4 report](docs/reports/conversational-rag-evaluation.md) records conditional held-out title Hit@5 9/9 vs8/9 baseline, semantic miss/C06 metadata gap, retrieval p952.574s and live six-ID rejection after multiplayer/Spider-Man success. **Aggregate12calls/92,813reserved tokens used; further inference needs new explicit budget.**168backend tests/static/contracts pass; no frontend changes. [Architecture](docs/architecture-assistant.md) / [walkthrough](docs/walkthrough-assistant.md). Human/full live quality and R4 completion remain pending; M5/publication/commit/push unauthorized. The following R3 entry is historical.

**R0–R3 complete locally; stop before R4.** Owner approved R3/confirmed frontend skills. [RAG plan](docs/conversational-rag-plan.md), [visual guide](docs/design/conversational-rag-plan.html), [R3 evidence](docs/reports/conversational-rag-r3.md) and [frozen contracts](docs/conversational-rag-contracts.md) govern. Full v2 wire/browser memory now integrates the six Core stages; validated legacy migration/quarantine, exact pending reload/retry and protected version-skew recovery retain Current's assistant contracts.151backend/49frontend tests,1actual-network browser test,6clean responsive scans/static/contracts pass. No new configuration needed; restart older API/hard-refresh UI. Next: separately approved R4 evaluation/live budget. Chat remains independent from main inputs; no live-quality/M5/publication claim. Earlier dated entries are historical.

**Owner-approved follow-up (2026-10-22): independent assistant implemented locally.** Main favorites/limits/feedback recommendations are separate from the floating chat; main text/conflict UI removed, exact-row feedback dismissal added, chat cards expand in-panel with Save/Steam only and retain bounded tab-session state. [Follow-up evidence](docs/reports/independent-assistant.md) records 80 backend/29 frontend tests, strict/static checks, mocked-provider real-catalog integration and actual disabled-chat/browser verification. [Current startup and live-AI prerequisites](docs/operations-assistant.md) replace temporary interpreter instructions. Earlier main-text/refinement acceptance descriptions remain historical/backend-compatible. M0–M4 status and hosted M2 unchanged; no M5 or publication authorization.

**Latest milestone status (2026-10-19): M0–M4 complete; M3/M4 complete locally, unpublished.** [M4 acceptance report](docs/reports/m4-implementation.md) records all five gates: constrained Hades discovery, retained refinement/conflict choices, bounded reload-safe session, validated claims/provider failure fallback, and atomic quota persistence verified across a new Python process in an isolated cleaned-up schema. Final checks: 68 backend tests in a fresh locked environment, Ruff/mypy17/contracts, 25 frontend tests, type/build/targeted lint, seven real API cases/twelve clean scans, seven SQL-budget checks. Independent UI review is **SHIP at M4 Current UI surface scope**, not blanket release approval. No live Groq, production quota migration, evaluated relevance improvement, physical-phone or hosted-M4 claim. Earlier unstarted/awaiting-layout notes are historical. **M5/publication remain unauthorized; stop after M4.**

**Active M4 coordination (2026-10-19):** the owner authorized “Start M4 Implementation” and confirmed installed frontend skills. M4 is now **in progress, incomplete**. The first backend slice adds bounded optional query/lexical ranking with explicit-filter preservation and safe encoder fallback; it does not complete interpretation, conversation, provider limits or the acceptance gates. Owner next requested an HTML plan before deciding on the application UI: `docs/design/m4-plan.html`. Await that decision before UI implementation. [Current evidence and remaining work](docs/reports/m4-in-progress.md). Earlier M4-unstarted/unauthorized statements are retained historical coordination, superseded by this authorization. M5/publication are not authorized.

**Current controls follow-up complete locally, main confirmed (2026-10-19):** owner-authorized after completed M3 in Current. Three multi-choice selectors (required modes → platform → catalog genre) and a two-handle min/max USD slider replace advanced/text-term UI; exclusions/undo remain. All modes/genres, any platform. The one material metadata-failure fix is **RESOLVED**; **ship at ONE-SCORED-FIX verdict-pass scope**, not blanket product/publication approval. Reviewer reopened all 18 refreshed captures with no regression attributable to the fix; earlier full review found no material visual/a11y regression. Full 21 frontend tests (15 browser/6 storage), TypeScript/build/lint and live nine-case/18-clean-scan verification passed again; backend 51/Ruff/strict mypy13/OpenAPI/generated drift and detector `[]` remain passed. Unavailable facets preserve stored null maximum/free-only false, with Any price / No maximum price; rendering fallback is never a budget. Main restored final interactive build to :8001 after owned :8002 verification; user must restart older :8001 backend and start/reuse :4173 preview, then refresh both entry routes. [Controls report](docs/reports/discovery-controls.md). M3 stays complete/local/unpublished; M4 stays unstarted/unauthorized. The following 49/17 counts and four-fix verdict describe the historical completed baseline separately.

Status: **M0–M3 complete; M3 complete locally and unpublished** as of 2026-10-18. Main agent confirms all five M3 acceptance gates and final handoff. Independent review: all four material fixes **RESOLVED**, disposition **ship at the four-scored-fixes verdict-pass scope**; all 12 fresh captures inspected with no material regression attributable to the fix batch. This is not blanket whole-product/UI release approval. Hosted M2 remains unchanged; the [clean PostgreSQL/pgvector replay](docs/reports/m2-clean-replay.md) remains historical evidence. Both entry routes load the same authorized Current guest application with real API search/discovery, compact controls, genre-led evidence, persistence, saves/history and feedback. [M3 evidence](docs/reports/m3-implementation.md) · [operations](docs/operations-m3.md) · [progress](docs/progress.md). Checks remain passed: 49 backend tests, 17 frontend tests, one separate live test, 12 clean scans and static/build/contract checks. Fresh frontend installation, remote M3 CI, real-phone and hosted M3 verification are not claimed. **M4 is unstarted and unauthorized. Stop after M3; no commit, push, deployment or redesign authorization.**

This plan implements [AGENTS.md](AGENTS.md) and records the decisions made during technical planning. The product brief governs scope; this document governs implementation order and proposed technical defaults. Items described as targets, candidates, or gates are not measured results. Keep both documents consistent when an approved requirement changes.

## 1. Build-agent instructions

1. Read both documents before coding. Inspect the current working tree and preserve existing user work.
2. For new work, start with Task 1A of [the completion plan](docs/project-completion-plan.md), not M0 or an old evaluation resume command. Complete catalog, dashboard and release in order; report and stop between tasks. Obtain the owner-selected catalog target after the capacity audit. The milestone chronology below is historical.
3. Build a thin, usable discovery flow early. Expand it incrementally rather than implementing every layer in isolation.
4. Record progress in `docs/progress.md`: milestone, completed work, checks run, measured results, blockers, and next action. Never describe a proposed check as passed.
5. Resolve routine choices within the current milestone autonomously using current official documentation. Ask the user for permission to advance after milestone completion, or when changing scope, requiring paid services, or encountering a product tradeoff this plan does not resolve.
6. Pin compatible stable dependency versions and commit lockfiles when implementation begins. Do not copy versions from the legacy application indiscriminately.
7. Keep the legacy application and data intact while establishing the new application. Do not load untrusted pickle artifacts. Rebuild recommendation artifacts through the new pipeline.
8. Each milestone handoff must identify changed files, runnable commands, acceptance evidence, and outstanding limitations. Commit only when requested; document any missing hosting access that blocks deployment verification.
9. When credentials, secret keys, or hosting access are needed, notify the user at that point. Name the service, required configuration variables, and local/provider settings where they belong. Have the user configure secrets there rather than paste values into chat. Never commit or log secret values; report credential-dependent checks as blocked until configured.
10. **Before any frontend implementation, including scaffolding in M1, notify the user and wait for confirmation that their desired frontend skills are installed.** Inspect available skill descriptions and load relevant skills before proceeding. Independent backend/data tasks can continue while waiting.

## 2. Agreed decisions and scope

| Area | Decision |
| --- | --- |
| Goal | Portfolio-quality full-stack product with credible, evaluated AI/ML and genuine gamer usefulness |
| Main journey | Main favorites + My limits + feedback -> ranked shortlist; independent chat uses only its own conversation and catalog. Planned conversational RAG follows the 2026-10-24 addendum. |
| Persistence | Guest-only; browser-local preferences, saved games, feedback, limited recent history; active conversation retained for the current session |
| Accounts | No registration, Google sign-in, authentication flows, account profiles, or guest-to-account migration |
| Controls | Current UI: multi-choice required modes, Windows/macOS/Linux, required catalog genres, inclusive recorded-USD min/max slider/free-only and exact exclusions. Earlier preferred/unwanted text UI is superseded; API term support remains compatible for future authorized work. |
| Region | US Steam store region; USD prices, with collection timestamps and recorded-price wording |
| Eligibility | Released standalone games, including free-to-play and clearly labeled Early Access |
| Exclusions | DLC, soundtracks, software, demos, unreleased games, adult-only sexual content; ordinary mature-rated games remain eligible |
| Visual direction | Premium, dark, image-rich, restrained accents, polished responsive and accessible interactions |
| Analytics | Supporting catalog exploration, not the homepage centerpiece |
| Scraping | Scrapling only; additional structured APIs/sources require investigation before selection |
| Budget | Free only, including hosting, database, inference, and required jobs |
| Availability | Publicly hosted with cold starts and bounded AI usage; useful discovery without hosted LLM inference |
| Local machine | Intel Core i5-5200U, 8 GB DDR3 RAM, no GPU |
| Delivery | Quality-based milestones; no fixed deadline |
| Evaluation | 30–50 curated requests, manual relevance judgments, one similarity baseline, constraint/grounding checks, latency report |

The initial acceptance scenario is: “I loved Hades for its combat and sense of progression. I want another satisfying single-player game, but with less repetition, playable on Windows, under $20.” This is a test scenario, not a statement about the user's personal history. Less repetition must not be presented as a verified attribute without supporting evidence.

## 3. Stack and deployment baseline

| Concern | Selected planning baseline | Notes |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | Static SPA; no additional frontend server |
| UI | Tailwind CSS, shadcn/ui | Custom visual system; semantic HTML and accessible interactions |
| Navigation/data | React Router, TanStack Query | Routing, bounded caching, request cancellation and mutations |
| Charts | Recharts | Focused analytics only |
| Backend | FastAPI, Pydantic, Uvicorn | Modular Python API with OpenAPI contracts |
| Database access | SQLAlchemy, Alembic, PostgreSQL driver | Explicit schema migrations and bounded connection pool |
| Database | Supabase-hosted PostgreSQL + pgvector | One database; no Supabase Auth requirement |
| Retrieval | pgvector + PostgreSQL full-text search | No separate hosted vector database or retained legacy FAISS dependency |
| Offline embeddings | Sentence Transformers | Compact 384-dimensional model; MiniLM is the initial candidate, subject to evaluation |
| Online embeddings | Compact ONNX runtime candidate | Must pass memory/latency/parity gate; do not assume full PyTorch fits the free API host |
| Ranking/evaluation | Explicit Python/NumPy; scikit-learn where useful | Understandable, versioned ranking; one reproducible baseline |
| LLM | Groq Free via a small provider adapter | Exact supported model selected at implementation; optional enhancement with bounded usage |
| Data jobs | Scrapling, Pandas, Pydantic | Local, resumable, low concurrency |
| Frontend host | Netlify Free | User-selected; configure SPA rewrites and provider subdomain |
| API host | FastAPI Cloud Hobby | Owner-selected replacement for Render on 2026-10-14; verify actual account/build/runtime limits in M1 |
| Checks | pytest, Vitest, React Testing Library, Playwright | Meaningful behavior checks and a small end-to-end suite |
| Tooling | uv for Python; npm for frontend; Ruff, ESLint, TypeScript | Stable pinned dependencies and documented PowerShell-compatible commands |
| CI | GitHub Actions | Bounded lint/type/test/build checks within free allowances |

No Redis, worker fleet, queue broker, microservices, paid monitoring, or mandatory local LLM. Retain the existing metered provider adapter. For the planned RAG revision, prefer minimal LangChain Core composition if the R0 benefit/resource gate passes; no full agent framework or parallel provider transport.

### Free-service gates

The owner replaced Render with FastAPI Cloud on 2026-10-14. Current public-beta Hobby documentation reports $0, no credit card, 3 apps, 0.1 vCPU/512 MB shared and scale-to-zero. Configure minimum 0 / maximum 1 replica; future usage/build billing is not finalized and must be reviewed without assuming a paid budget. The pricing table and autoscaling guide disagree on the upper replica ceiling (2 versus 3); this app does not rely on that ceiling. Previously consulted Supabase Free documentation reported 500 MB database storage and pausing after one week of inactivity. Recheck actual account allowances before deployment. Verify Netlify's applicable plan, credits, transfer/request/build limits and exhaustion behavior; do not assume legacy quotas apply.

- Target API peak resident memory below 400 MB under representative low concurrency, preserving headroom. Measure startup as well as requests.
- Target hosted database use below 350 MB initially, including indexes and operational records. Measure a representative import and project catalog growth.
- Query embeddings must use the same model revision, normalization, and compatible representation as catalog embeddings. Validate ONNX conversion against the offline encoder.
- If ONNX inference cannot fit, record a decision before scaling: a verified free compatible inference service or a smaller evaluated model. Lexical fallback is useful degradation, not permission to silently drop semantic discovery from the completed product.
- Keep raw snapshots and large artifacts locally; keep operational database records bounded. Do not store game image binaries in the database.
- API cold starts and database pauses are different. Document database restoration; do not promise that a normal request resumes a paused Supabase project.
- Use free plans with paid auto-recharge/overage disabled where available; verify hard-stop behavior. Do not add artificial keep-alive traffic to evade provider limits.

## 4. Architecture and repository structure

```mermaid
flowchart TD
  Browser[React SPA on Netlify] --> API[FastAPI on FastAPI Cloud Hobby]
  Browser <--> Local[Local storage and session storage]
  API --> DB[(Supabase PostgreSQL + pgvector)]
  API --> Encoder[Optional in-process query encoder]
  API --> LLM[Groq: interpretation and grounded explanation]
  Jobs[Local Scrapling / cleaning / embeddings jobs] --> DB
  Jobs --> Snapshots[Local raw snapshots and manifests]
  Eval[Local evaluation runner] --> API
  Eval --> Report[Versioned evaluation report]
```

Proposed layout (create during implementation):

```text
frontend/                 React SPA, generated API types, tests
backend/
  pyproject.toml
  uv.lock
  src/game_discovery/
    api/                  routes, dependencies, error mapping
    schemas/              request/response and normalized-data contracts
    catalog/              queries, eligibility, evidence, analytics
    retrieval/            vector and lexical retrieval, encoders
    ranking/              features, feedback adjustments, constraints
    ai/                   interpretation, explanation, provider adapter
    db/                   models, sessions, migrations integration
    jobs/                 audit, scrape, normalize, import, index
    evaluation/           runner, baseline, metrics
    core/                 configuration, logging, limits
  migrations/
  tests/
evaluation/               curated requests, judgments, report metadata
data/                     ignored raw/processed/artifact directories; small fixtures tracked
docs/                     architecture, operations, decisions, progress, reports
.github/workflows/        bounded CI
netlify.toml              frontend build and SPA rewrite configuration
IMPLEMENTATION_PLAN.md
AGENTS.md
```

Preserve root legacy files initially: `app.py`, both CSVs, `similarity_finale.pkl`, `faiss_index/`, and legacy dependencies. New environments must not depend on the legacy Streamlit application. Inspect `.streamlit/` for configuration without exposing secrets. Relocation or cleanup is a later explicit, documented change.

## 5. Catalog model and provenance

Use Steam app IDs as stable external identifiers. Titles are display/search fields, never primary identity keys. Deduplicate by verified identity rather than title alone. Quarantine ambiguous mappings instead of merging by guesswork.

Minimum schema:

| Entity | Key fields and purpose |
| --- | --- |
| `games` | app ID, title, normalized title, plain-text descriptions, type, release status/date, Early Access, eligibility status/reason, store URL, artwork URL, content hash, updated timestamp |
| `game_platforms` | game ID, platform, supported state; distinguish false from unknown |
| `taxonomy_terms` / `game_terms` | normalized genre/tag/play-mode identifiers and game associations; source labels retained |
| `game_prices` | game ID + US region + USD, amount in integer cents, free-to-play state, observed timestamp, source reference; current retained observation |
| `game_reviews` | positive/total counts and source summary where available, observed timestamp, source reference |
| `catalog_sources` / `game_evidence` | source URL, collection time, source field, supported value or excerpt, content hash; compact evidence for explanation validation |
| `game_embeddings` | game ID, artifact/model revision, content hash, vector, generated timestamp; one active model generation |
| `catalog_versions` / `job_runs` | active artifact manifest, counts, timestamps, status and bounded reports |
| `ai_usage_windows` | bounded global quota reservations for optional LLM use; no personal preference storage |

Store timestamps in UTC. Unknown values remain null/unknown, never false or zero by default. Historical imports with unknown observation dates must retain that uncertainty; import time is not collection time. Distinguish free-to-play from a temporary zero-price promotion.

Use ordinary indexes for identity/filter/join queries and a full-text index for descriptions/titles. Begin with exact vector search if measured fast enough. Add a pgvector approximate index only when justified by measured size and latency; validate filtered recall. An approximate search must not return disallowed games or silently underfill due to post-filtering.

Eligibility classifications require supporting source fields. Quarantine unclassified content from recommendations pending review. Keep recognizable but ineligible titles usable as favorite seeds only if clearly labeled and supported by usable metadata; never return them as eligible recommendations.

### Data workflow

1. Audit existing CSV headers, counts, duplicates, missingness, encoding, identifier coverage and provenance. Save a report; do not claim field coverage before inspection.
2. Probe a small sample of candidate structured sources and Scrapling pages. Document accessible fields, regional behavior, source terms, timestamps, failure modes and practical request rate. No additional source is selected by this plan.
3. Save raw snapshots with source, time, hash and run ID. Extract to a normalized schema and reject/quarantine invalid records with reasons.
4. Classify eligibility, normalize terms, validate region/currency and construct evidence records.
5. Generate embeddings from documented semantic text. Keep volatile prices/review counts out of semantic text so price refreshes do not trigger needless embedding work.
6. Batch-upsert validated records; generate embeddings only for changed semantic content/model revisions. Import staging data before promoting a complete artifact version.
7. Validate counts, foreign keys, vector dimensions, evidence references and constraints before atomic activation. Retain a rollback manifest locally.
8. Publish freshness summaries to the API. Refresh via documented manually invoked jobs initially; no guaranteed automated freshness schedule.

On the user's hardware: start with one browser session, conservative scraping concurrency, small embedding batches (initially 8–16, then measure), and sequential heavy jobs. Stream or chunk large files; never rebuild an N-by-N similarity matrix. Resume from checkpoints after interruption.

## 6. Recommendation behavior

### Request processing order

1. Validate bounded input, resolve seed game IDs, and load active catalog/artifact metadata.
2. Merge explicit request state with browser-local preferences. Current explicit controls override saved preferences.
3. If enabled, interpret natural language into a validated preference patch. An LLM may not silently override explicit controls. Conflicts require visible clarification; unambiguous additions appear as active filter chips.
4. Build the eligibility set using reliable hard constraints and exact exclusions.
5. Retrieve candidates using seed vectors, query vectors when available, and lexical matching. Filter during retrieval where possible and deterministically validate afterward.
6. Rank candidates using documented normalized features and feedback. Exclude seeds, explicitly excluded games, already-played games, and not-for-me titles from results by default.
7. Return a capped shortlist with rank features and catalog evidence available internally for debugging/evaluation.
8. Build template explanations immediately or use bounded LLM explanation generation. Validate claims and replace invalid output with templates.
9. Return applied constraints, unresolved preferences, evidence-backed reasons/tradeoffs, freshness, degradation state, and timing metadata.

### Hard-filter semantics

- Price bounds use integer USD cents in 0..1,000,000. Optional `min_price_cents` is inclusive; UI maximum is inclusive (`price_operator: "lte"`), while the API retains exclusive `"lt"` support. A supplied minimum, including zero, requires a known recorded price. Unknown/non-USD/non-US prices fail a price constraint. Validate minimum ≤ maximum both in individual filters and after explicit/saved criteria merge; reject invalid ranges or free-only with a positive minimum as 422. Show recorded price and observation date; do not imply a live purchase quote.
- Free-only requires explicit supporting evidence of the chosen free eligibility policy.
- Platform controls expose whether the user means any selected platform or all selected platforms; default to any and document it. Unknown support does not pass a required platform.
- All selected required play modes and catalog genres must be explicitly supported. Current UI uses any-selected-platform matching and states it; API retains any/all support. Preferred terms remain ranking signals and unwanted terms exclusions for compatible API clients; the current UI removes their fields and clears both arrays on submit so old stored terms cannot silently influence discovery.
- Evidence absence is not evidence of absence: disclose incomplete tag coverage and use only supported fields for strong exclusion claims.
- Never silently relax filters when results are scarce. Return fewer/zero results and suggested changes that require user action.

### Initial ranking implementation

Use a configurable weighted sum of normalized seed similarity, query similarity, lexical relevance, preferred-term match, and bounded feedback affinity. Initial weights are engineering defaults, recorded in a versioned config and tuned on development cases. Renormalize for missing components rather than treating an absent query as a negative signal. Use a small review-confidence/popularity tie-breaker, not a dominant signal; stable app-ID tie-breaking makes runs reproducible.

Interested feedback can modestly boost similar content; not-for-me feedback can modestly downweight similar content while excluding the exact title. Already-played excludes the exact game without assuming dislike. Cap feedback influence so it cannot swamp the current request. Include controlled tests proving feedback changes order in a meaningful fixture while preserving hard constraints.

Avoid custom training in the first release. Do not claim the hybrid ranker improves over baseline until the evaluation shows it.

### LLM boundaries and grounding

- Provider interface: request interpretation and explanation generation; model name, prompt version, timeouts and token budgets are configuration.
- Send only bounded relevant preference/context data and shortlist evidence. Browser-local persistence does not mean discovery inputs never leave the device; explain API/provider processing concisely in the interface.
- Treat user text and catalog descriptions as untrusted data, not executable instructions.
- Prefer structured claims with allowlisted types, evidence IDs and game IDs. Validate exact numeric/platform/mode facts against the catalog; render validated facts using templates.
- An evidence citation alone does not prove a subjective statement. Present soft experience matches as qualified inferences and flag unsupported “less repetition” or difficulty assertions. Manual grounding review complements deterministic checks.
- Invalid JSON, invented IDs, unsupported facts, timeouts or quota errors fall back to evidence-derived templates. Ranking/filtering never waits indefinitely for explanations.
- Initially allow at most one interpretation and one batched shortlist explanation call per request; bounded context, output tokens and timeouts. Local per-client throttling plus database-backed atomic global usage reservations protect the overall allowance across restarts. If quota accounting fails, disable LLM calls and preserve core discovery.

### Graceful degradation

| Failure | User-visible behavior |
| --- | --- |
| LLM disabled/exhausted/unavailable | Core recommendations, explicit filters and feedback still work; template explanations; clearly identify reduced language interpretation |
| Query encoder unavailable | Seed-vector and lexical retrieval; disclose reduced semantic matching |
| API waking | Responsive frontend, truthful startup state, bounded retries and retry action |
| Database unavailable/paused | Clear temporary-unavailability state; saved local games remain visible from minimal cached display data; no fabricated recommendations |
| Browser storage blocked/full/corrupt | Continue in memory, explain persistence limitation, provide reset/recovery |
| Missing source facts | Display unknown/uncertain, exclude from constraints requiring those facts |

## 7. API contract baseline

Prefix routes with `/api/v1`. Generate frontend types from the OpenAPI schema. Use Pydantic validation, stable error codes and bounded pagination. All catalog application access goes through FastAPI; no database credentials in the browser.

| Route | Responsibility |
| --- | --- |
| `GET /health/live` | Process health without expensive dependencies |
| `GET /health/ready` | Bounded database/artifact readiness; do not require LLM availability |
| `GET /api/v1/catalog/status` | Catalog version, region, field freshness/coverage and service capability flags |
| `GET /api/v1/games` | Search/paginated catalog browsing and favorite selection |
| `GET /api/v1/games/{app_id}` | Detail and evidence-backed metadata |
| `POST /api/v1/games/resolve` | Resolve a bounded set of saved IDs; report removed/unknown entries |
| `GET /api/v1/facets` | Normalized genres, tags, platforms, modes and optional `max_price_cents` from eligible active US/USD catalog observations (null when unavailable) |
| `POST /api/v1/discover` | Initial and refined discovery using full current state; no server-side user profile |
| `GET /api/v1/analytics` | Bounded, cacheable catalog aggregates with missingness and freshness |

Discovery request groups:

- Current M3 request: `favorite_ids`, `filters` (`min_price_cents`, `max_price_cents`, `price_operator`, `free_only`, `platforms`, `platform_match`, `required_modes`, `required_genres`, compatible `preferred_terms`/`unwanted_terms`, `excluded_ids`). Optional minimum defaults to null at the API boundary; explicit null/false/[] overrides saved state. US/USD is the catalog price context. `query` remains a future hybrid-discovery field, not a current M3 capability.
- `preferences` and bounded `feedback` entries containing app ID, kind and timestamp; client data is untrusted and validated.
- `conversation`: bounded recent messages and normalized prior criteria; full active state is resubmitted, not fetched by user ID.
- `limit` (default 10, maximum 20) and an optional client request ID for stale-response handling.

Discovery response groups:

- `request_id`, `catalog_version`, `ranking_version`, `effective_criteria`, `unresolved_preferences`.
- `results`: game identity/display fields, recorded price and timestamp, supported reasons, qualified inferences, tradeoffs and evidence references.
- `capabilities`, `degraded_reasons`, `suggested_refinements`, `timings_ms`.
- No fake percentage “match confidence.” Raw rank features are available only in local evaluation/debug mode.

Return structured errors such as `{code, message, request_id, retryable}`. Distinguish malformed input, upstream unavailability, throttling and no matching games (a valid empty result). Configure CORS for explicit frontend origins; CORS is not abuse prevention. Bound query lengths, message count, feedback size, DB timeouts and concurrent inference. Redact provider keys, connection strings and raw conversation text from ordinary logs.

## 8. Frontend and browser persistence

Pages: discovery (`/`), saved games (`/saved`), catalog exploration (`/explore`), game details (`/games/:id`), and a concise about/methodology page. Brand name and detailed art direction remain design choices for the first UI review.

Current owner-authorized layout: favorite picker, small “My limits” lead, required modes → platform → catalog genre multi-choice selectors → two-handle price slider, ranked genre-led rows, evidence/tradeoffs and feedback. Four desktop fields stay on one row; ≤900px two columns; ≤640px one column in the same order. The former advanced/soft-term text UI is superseded only for the active UI. Native checkbox disclosures support clearing/Escape/outside close; one-cent native range handles cannot cross. Slider cap uses facets' eligible recorded maximum, rounded up to a whole dollar, extended for stored bounds and capped at 1,000,000 cents; absent/error cap disables it, with request-error retry. Stored unbounded `max_price_cents: null` / `free_only: false` is preserved when facets are unavailable, including submission/persistence; disabled labels read Any price / No maximum price. The finite internal rendering fallback never becomes a budget. Bounded $0–$0 submits explicit free-only. Natural-language input, active refinement chips and integrated conversation remain later unauthorized work. Keep loading/empty/error states, image fallbacks, keyboard navigation and visible focus.

Persistence defaults (technical defaults, adjustable with documentation):

- A versioned local-storage envelope stores favorites/preferences, saved IDs, minimal cached saved-game display metadata, feedback and at most 20 recent discovery summaries.
- Start with bounded limits of 50 favorites, 200 saved games and 500 feedback entries. Explain limits rather than silently discarding saves. Coalesce feedback to the latest action per game.
- Session storage retains at most 20 recent active conversation messages and normalized criteria for the current tab session, including reloads. Persistent history summaries do not contain full conversations.
- Validate and migrate storage schemas; catch quota and parsing errors. Handle same-browser tab updates without silently replacing an in-progress conversation.
- The controls follow-up retains storage version 2 and the defined v1 migration: older v2 preferences/history without `min_price_cents` normalize to zero. History summaries display ranges; no format bump or database migration is needed.
- “Clear my saved data” removes application-owned local and session keys, resets in-memory state and personalized query caches. Ignore outstanding responses that would restore cleared state.
- Show “Saved on this device,” explain no sync and storage-clearing loss. Keep data forwarding to the API limited to relevant ranking inputs.
- Saving a game does not implicitly mean “interested” unless clearly communicated; make feedback behavior explicit.

Analytics use the same eligible catalog and normalization as discovery. Display denominators, unknown-field counts, US/USD context and freshness; do not label snapshots as live Steam statistics.

## 9. Developer workflows and operations

Implement a single Python module entry point (`python -m game_discovery.jobs`) with the following subcommands. These are target interfaces, not commands that exist today:

| Subcommand | Output |
| --- | --- |
| `audit --input ...` | Dataset/coverage/resource report |
| `collect --source ... --limit ... --resume` | Raw snapshots and collection manifest |
| `normalize --run-id ...` | Validated records and quarantine report |
| `embed --run-id ... --batch-size 8 --resume` | Versioned embeddings, hashes, checkpoints |
| `import --run-id ...` | Idempotent staging import and validation report |
| `activate --run-id ...` | Validated catalog/artifact activation |
| `evaluate --cases ... --catalog-version ...` | Baseline/hybrid outputs, judgment template and metrics |

Each job supports useful help, structured logs, clear exit status and a summary report. Interrupted jobs resume safely; rerunning imports must not duplicate records. Keep raw snapshots, models, secrets, local outputs and large artifacts out of Git. Track small fixtures, schemas, manifests and summarized reports. Where source redistribution is restricted, document how to regenerate data rather than publishing it.

Document frontend install/dev/build, backend environment setup/dev/test, migrations, local PostgreSQL/pgvector setup, artifact generation, database import/restore, deployment and troubleshooting. Offer a native/local PostgreSQL path or a lightweight database-only container; do not require the entire Supabase stack on an 8 GB machine.

Configuration: server-only database URL, Groq key/model, feature flags, allowed origins, limits, artifact version and log level; public frontend API URL only. Track `.env.example` with placeholders. Use least-privilege runtime DB access and separate migration/import credentials. Serving the demo must not expose collection or import endpoints.

Netlify builds `frontend/` using its lockfile and publishes `dist`; SPA fallback must support direct navigation to nested routes. FastAPI Cloud uses application directory `backend`, the locked Python package and its explicit `[tool.fastapi]` entrypoint. Configure minimum 0 / maximum 1 replica and verify a single serving worker so the pool/request bounds remain meaningful; transient old/new replicas can overlap during rollout. Build artifacts must include needed encoder files or use a documented reproducible acquisition step; do not download large models on each first request. Run schema migrations explicitly as part of the release workflow, not on every API startup.

## 10. Evaluation and testing

Curate 30–50 cases spanning seeds, text-only requests, combined discovery, contradictory constraints, missing facts, feedback, refinements and empty results. Include the Hades scenario. Record query, seed IDs, expected hard constraints, qualitative relevance rubric and evidence notes. Separate development cases from final report cases before tuning; document small-sample limitations.

One baseline: cosine similarity using a reproducible TF-IDF representation of the same eligible catalog, combining seed text and request text. Apply the same hard-filter/exclusion policy to both systems for a fair relevance comparison. Report cold-start/no-query behavior separately. The legacy unexplained similarity matrix is not the reproducible baseline.

Manual judgments: use a simple 0/1/2 relevance scale on the union of each system's top five results, with system labels hidden where practical. Report mean relevance@5 and case-level wins/ties/losses; report fewer-result cases explicitly. Have the project owner review judgments; never present model-generated judgments as independent human labels.

Report hard-constraint violation count/rate, unsupported-claim count/rate from automated factual checks plus manual review, and latency p50/p95. Separate warm core, AI-assisted and cold-start measurements and record sample sizes. Pin catalog, model, ranking, prompt, code revision and provider settings; hosted LLM outputs are not bit-for-bit reproducible, so retain evaluation outputs where appropriate.

Required checks include constraint edge cases (unknown price/platform, exclusions), feedback effects, interpretation conflicts, invalid claims, unavailable AI, interrupted/idempotent import, storage migrations/clearing and core navigation. CI uses small fixtures and mocked providers, never required live scraping or paid inference. A small browser suite covers the main guest journey, reload persistence, session refinement, clear-data behavior and empty/error states.

Quality gates: zero known hard-constraint violations and zero known unsupported factual claims in release cases; fix and rerun failures, or narrow unsupported behavior transparently. Hybrid relevance must be compared honestly: investigate regressions and document limitations rather than claiming automatic improvement. Proposed warm core target: p95 under 2 seconds on representative demo requests; AI-assisted target under 10 seconds. These are targets to measure and review, excluding documented cold starts, not guarantees.

## 11. Build milestones

M0–M3 are **complete**; M3 is **complete locally and unpublished**, with all five functional gates and final handoff confirmed by main agent. The independent review's ship verdict covers the four scored fixes, not a blanket release approval. M4–M8 are **not started**; M4 is **unauthorized**. Stop after M3 and wait for explicit owner permission before M4 or publication.

### M0 — Audit and feasibility decisions

Dependencies: none.

Tasks: audit legacy data/source coverage; inspect repository and secrets handling; confirm free allowances; probe sources with Scrapling/structured API candidates; benchmark a representative import and compact encoder on available resources; create the initial evaluation case skeleton.

Deliverables: `docs/reports/data-audit.md`, `docs/reports/feasibility.md`, and decision records for sources/model/hosting with measured counts, memory, storage and latency.

- [x] No assumed legacy price freshness or unverified source field becomes a promised fact.
- [x] A viable free deployment path and CPU-only local pipeline are documented; hosting experiments may use a minimal disposable spike.
- [x] Catalog sizing, query encoder feasibility and any unresolved blockers have explicit outcomes.
- [x] Later milestones have enough verified data to implement real constraints.

Evidence: [M0 feasibility](docs/reports/feasibility.md), [engineering defaults](docs/decisions/0002-m0-feasibility-selection.md). These establish local implementation viability; hosted memory/latency, account allowances and deployment remain M1/release checks. Initial budget: 6,000 games, float ONNX; private sizing data removed after measurement.

### M1 — Application foundation and deployed walking skeleton

Dependencies: M0 feasibility decisions.

Tasks: create frontend/backend projects, pin dependencies, configure typed API contracts, migrations and environment examples; establish local DB; build health endpoints and minimal page; configure CI, Netlify and FastAPI Cloud deployment.

Coordination gate: before scaffolding or implementing the frontend, notify the user and wait for their frontend-skill installation confirmation. Request database/hosting configuration when needed, with explicit setup locations and variable names.

Deliverables: runnable local stack, initial schema, deployment configs, setup guide and live health-connected page when account access is available.

- [x] Frontend build, Python checks and initial API tests pass from documented setup.
- [x] User was notified before frontend implementation, confirmed their desired skills were installed, and applicable skills were consulted.
- [x] Frontend can call the hosted API; direct SPA routes work; secrets remain server-side.
- [x] API/database unavailability is distinguishable from empty results.
- [x] Deployment access blockers are recorded rather than marked complete.

Evidence: [setup/checks](docs/setup.md), 28 Python tests, Ruff, strict mypy, generated-contract checks, frontend lint/type/build and 7 browser checks; GitHub CI and real local browser/CORS/API/PostgreSQL smoke passed. [Hosted M1 report](docs/reports/m1-hosted-verification.md): deployed Netlify → FastAPI Cloud → PostgreSQL verified, direct SPA routes, contracts/docs, explicit CORS, manual retry, mobile/keyboard/axe and controlled browser-only outage recovery pass. Owner confirmed both Free plans, min 0/max 1 replica and one worker. **M1 is complete; owner subsequently authorized M2 on 2026-10-15.** Hosted RSS, cold-start/load/relevance evaluation are not claimed.

### M2 — Reproducible catalog and useful non-LLM discovery

Dependencies: M1.

Tasks: implement normalized imports/provenance/eligibility, compact embeddings, seed retrieval and hard filters; add search, details, facets/status and initial discovery endpoints; build favorite selection, filters, cards and template reasons.

Deliverables: a representative real catalog, reproducible artifact manifest, thin public discovery journey.

- [x] From a clean database, documented jobs reproduce a usable catalog and embeddings (two PostgreSQL 17/pgvector Actions builds; retained evidence).
- [x] Favorite selection and recorded US/USD/platform/mode/exclusion filters work end to end (real local browser/API/Supabase).
- [x] Missing data fails required constraints; no-match results do not relax filters.
- [x] Useful recommendations work with no Groq key configured.
- [x] Output cites real catalog fields; freshness and Early Access labels are visible.

Evidence: [M2 implementation report](docs/reports/m2-implementation.md), [operations](docs/operations-m2.md), [production artifact manifest](docs/reports/m2-artifact-manifest.json), [clean replay report and retained JSON](docs/reports/m2-clean-replay.md). All five gates pass: owner-confirmed hosted journey; 40 real games; two independent clean PostgreSQL 17.10/pgvector 0.8.2 builds in [run 38680812079](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680812079), identical fresh artifacts/database fingerprints/recommendation results, integrity/permissions/rollback checks and confirmed cleanup. Backend CI passed on replay commit `3a62d1e` with 41 tests; the unchanged frontend has passing lint/contract/type/build and 11 browser tests from `3453bfb`. **M2 is complete; these are historical M2 checks. M3 is now complete locally under the latest status above.** This is not a full-product or evaluated-relevance release claim.

### M3 — Guest persistence and feedback personalization

Owner-authorized post-completion follow-up is **complete locally, main confirmed**: compact multi-choice/range controls, compatible minimum/facets API fields and the resolved unbounded-price metadata-failure fix. [Controls evidence](docs/reports/discovery-controls.md) records final passing checks and **ship at ONE-SCORED-FIX verdict-pass scope**, separate from the historical baseline four-fix verdict below. Completed acceptance gates stay complete; no M4 or publication authority.

Current status (2026-10-18): **M3 COMPLETE LOCALLY.** Main agent confirms all five functional acceptance gates and final handoff. Real search/discovery, versioned guest storage, saved page, bounded history, feedback and required-genre filtering are implemented and verified. [Recorded evidence](docs/reports/m3-implementation.md): 49 backend tests, 17 frontend tests, one separate live test, 12 clean scans and static/build/contract checks remain passed. Independent reviewer: all four material fixes RESOLVED; ship at the four-scored-fixes verdict-pass scope, with no material regression attributable to the fix batch in all 12 inspected fresh captures. This is not blanket whole-product/UI release approval. M3 is unpublished; hosted M2 remains unchanged. M4 is unstarted and unauthorized; no further implementation, commit/push/deploy or next-milestone work is authorized.

Dependencies: M2.

Tasks: implement versioned browser storage, saved page, bounded history, feedback controls, preference forwarding and ranking adjustments; handle storage failure and reset races.

Deliverables: persistent guest experience and personalization checks.

- [x] Reload preserves favorites/preferences/saves/history/feedback in the same browser.
- [x] Controlled examples prove feedback changes ranking and exact exclusions hold.
- [x] Already played is not treated as negative taste; current request overrides stored preferences.
- [x] “Saved on this device” and clear-data behavior are verified, including in-flight requests.
- [x] No accounts/authentication have been introduced.

### M4 — Hybrid text discovery and conversational refinement

**Complete locally (2026-10-19), unpublished.** [Acceptance evidence and limits](docs/reports/m4-implementation.md) · [operations](docs/operations-m4.md). Provider failure-mode coverage uses mocked Groq transport; real atomic quota behavior uses a scratch schema, not an application-schema migration. Live Groq remains optional and unverified.

Dependencies: M2 and M3; query encoder feasibility resolved.

Tasks: integrate query/lexical retrieval, configured hybrid ranker, structured interpretation, session context, validated explanations and provider limits/fallbacks. Build active criteria chips and clarification states.

Deliverables: complete signature discovery flow, ranking/prompt versions and failure-mode tests.

- [x] Hades acceptance scenario produces constrained results and honestly handles “less repetition.”
- [x] Refinements retain prior criteria unless explicitly changed; contradictions are visible.
- [x] Session conversation survives reload without becoming an indefinite persistent chat archive.
- [x] Invented IDs/claims, malformed outputs, timeout and quota exhaustion fall back safely.
- [x] Global AI budget enforcement survives process restart; core discovery remains usable.

### M5 — Catalog expansion and refresh operations

Dependencies: M2; may proceed after M3 before M4 if data gaps block quality.

Tasks: expand recognizable seeds and useful lesser-known games from verified sources; complete selective enrichment, resumable collection, changed-only embeddings, staged activation/rollback and developer reports.

Deliverables: documented expanded catalog, refresh runbook, source/coverage/freshness report and measured local resource profile.

- [ ] Scrapling is the sole scraping tool; jobs run CPU-only within available RAM.
- [ ] Interrupted jobs resume; identical reruns do not duplicate data or recompute unchanged vectors.
- [ ] Failed validation cannot activate incomplete catalog/artifact generations.
- [ ] Catalog growth remains within measured free storage headroom.

### M6 — Premium UX and supporting analytics

Dependencies: M3 and M4; use M5 catalog for final presentation.

Tasks: establish visual tokens, polish discovery/cards/detail/saved pages, responsive behavior, accessible controls, artwork fallbacks and restrained motion; add exploration charts from normalized data.

Deliverables: coherent responsive interface, focused analytics and interface walkthrough draft.

- [ ] Main journey works by keyboard and at mobile/desktop widths with readable contrast and visible focus.
- [ ] Loading, cold-start, reduced-AI, empty and error states are truthful and actionable.
- [ ] Charts show coverage, denominators and freshness, and lead back to discovery.
- [ ] Browser tests cover the guest journey and persistence/reset behavior.

### M7 — Measured recommendation evaluation

Dependencies: M4 and M5; evaluation fixtures begin in M0 and evolve throughout.

Tasks: freeze 30–50 cases and catalog version, implement baseline runner, collect manual judgments, run factual/constraint checks and latency measurement, inspect failures and make bounded corrections.

Deliverables: runnable evaluation commands, versioned outputs/judgments, concise report with baseline comparison and weaknesses.

- [ ] Report is reproducible from recorded inputs/artifacts, with hosted-generation variability disclosed.
- [ ] No known release-case hard-constraint violation or unsupported factual claim remains.
- [ ] Results include relevance comparison and warm/cold/AI latency, not unsupported quality claims.
- [ ] Manual-review dependencies are explicit; do not mark human judgment complete without it.

### M8 — Release, operations and portfolio handoff

Dependencies: M6 and M7; all deployment gates resolved.

Tasks: recheck free allowances and load/resource headroom, verify provider-outage behavior, finalize setup/operations/API/architecture docs, record walkthrough and exercise fresh-machine setup and restore workflows.

Deliverables: live guest demo, concise README, architecture diagram, API docs, evaluation report, meaningful CI, walkthrough and completed progress record.

- [ ] Public demo is accessible without registration and functions with LLM disabled.
- [ ] Netlify, API and database failure/limit states have been exercised and documented.
- [ ] Clean local setup, import/index/evaluation and database restoration commands are verified.
- [ ] Dependencies/artifacts/configuration are reproducible; credentials are absent from tracked files.
- [ ] Every portfolio-ready criterion in AGENTS.md has linked evidence; remaining limitations are clearly stated.

## 12. Scope boundaries and change control

Do not add accounts, Steam account integration, custom model training, multiple databases, distributed job infrastructure, a web admin dashboard, multiple store regions, paid requirements, or research-heavy evaluation without user approval. Do not weaken supported constraints to make example outputs look better.

Open engineering decisions to settle in M0/M1: exact dependency versions, selected collection sources, final embedding model/runtime, Groq model, measured catalog capacity and free-host suitability. Open design decisions to settle in M6: brand name, detailed typography, artwork treatments and final layouts. None require restarting the product interview.

## 13. Documentation references

Consult current documentation again when implementing; free limits and model availability can change.

- [Vite deployment](https://vite.dev/guide/static-deploy.html)
- [Netlify Vite deployment](https://docs.netlify.com/build/frameworks/framework-setup-guides/vite/)
- [Netlify pricing](https://www.netlify.com/pricing/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Supabase pgvector search](https://supabase.com/docs/guides/ai/semantic-search)
- [Supabase pricing](https://supabase.com/pricing)
- [FastAPI Cloud pricing](https://fastapicloud.com/pricing) and [autoscaling](https://fastapicloud.com/docs/advanced-features/autoscaling)
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
- [Scrapling](https://github.com/D4Vinci/Scrapling)
