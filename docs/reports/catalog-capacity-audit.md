# Catalog capacity audit — 2026-11-05

**Task 1A delivered; owner decisions pending. Recommend 2,000 total eligible games, including the existing 40.** No bulk expansion, staging, activation, dashboard implementation or publication has occurred. Account-specific free-plan receipts remain unavailable; the capacity recommendation is conditional on confirming them. Task 1 is not complete.

**Subsequent owner decision, 2026-11-05:** approved **2,000 total eligible games**, requested **Linux(SteamOS)** (source-verified Linux counts with an explicit no-independent-SteamOS/Deck-verification note), and confirmed the existing free plans. The pending-decision/no-implementation wording below is this original audit's dated disposition, not the current execution state. Continue with the [expansion report](catalog-expansion.md); the measurements below remain unchanged.

## Decisions requested

1. Select **500, 1,000 or the recommended 2,000 total eligible games**, or request another size. A 4,000-row sizing fixture worked, but its conservative lifecycle budget exceeds the retained 350 MB engineering target.
2. Approve retaining the dashboard's SteamOS category as **“independent support not recorded / unknown”**. No independent SteamOS field was found. Linux support and Steam Deck compatibility must not be relabeled SteamOS support. If verified SteamOS counts are essential, source feasibility remains a blocker rather than a fabricated zero.
3. Confirm the existing Supabase project remains **Free** and FastAPI Cloud team/app remains **Hobby/Nano**, without upgrading. Their browser dashboards required login; this audit could verify public documentation, not current account allowances or billing settings. Sign in through the providers; do not paste credentials into chat. Recheck Netlify/account usage during Task 3.

The next permitted implementation is Task 1B after the size/missing-field decisions. Stop before Task 2 after completing Task 1.

## Scope and reproducibility

Changes are limited to the developer audit helper `backend/scripts/catalog_capacity_audit.py`, its three focused safety tests, a fixed 32-ID pilot manifest, this report and current coordination documentation. Serving code, contracts, migrations, dependency locks, `.env`, quotas and existing services are unchanged. No subagents or HTML scraping were used. All Steam observations used public structured APIs; no Groq requests or application reservations were made. Local ONNX encoding **was** performed.

Local evidence is under ignored `data/reports/catalog-capacity-2026-11-05/`. It contains the deduplicated candidate manifest, restricted read snapshots, raw pilot responses/checkpoints, normalized documents, real embeddings, measurements, projections and postchecks. Raw responses, including public review text accidentally returned by the zero-page request described below, remain local and must not be published. No conversation documents, archive identifiers or private capabilities were read/exported.

```powershell
$python = '.\backend\.venv\Scripts\python.exe'
& $python -m game_discovery.jobs audit --input game_data_for_dashboard.csv --input games_data_recomendation.csv --output data/reports/catalog-capacity-2026-11-05/legacy-audit.json
& $python backend/scripts/catalog_capacity_audit.py snapshot
& $python backend/scripts/catalog_capacity_audit.py candidates
& $python backend/scripts/catalog_capacity_audit.py collect
& $python backend/scripts/catalog_capacity_audit.py reviews
& $python backend/scripts/catalog_capacity_audit.py measure
& $python backend/scripts/catalog_capacity_audit.py api-memory
& $python backend/scripts/catalog_capacity_audit.py snapshot --output data/reports/catalog-capacity-2026-11-05/postcheck
& $python backend/scripts/catalog_capacity_audit.py self-check
& $python -m unittest discover -s backend/tests -p test_catalog_capacity_audit.py -v
& $python -m unittest discover -s backend/tests -p test_catalog_m2.py -v
& $python -m ruff check backend/scripts/catalog_capacity_audit.py backend/tests/test_catalog_capacity_audit.py
```

These commands were run, not merely proposed. `collect` was resumed once to process only the last untouched ID after the invalid-ID stop. The audit never retries attempted IDs. The final helper's reviews phase requests one review, following the measured zero-page behavior below; existing observations keep their original request parameters. `measure` creates only transaction-local TEMP relations and unconditionally rolls them back. It does not call `publish()` or update catalog activation. Do not substitute any frozen assistant evaluation directory. To recollect successes, select a **new** output directory and rerun its snapshot/candidates preparation; do not overwrite historical evidence.

## 1. Current database and local capacity

Measured 02:28 UTC, with a restricted, read-only runtime connection for catalog inspection and a separate read-only developer connection for version/archive aggregates:

| Item | Actual observation |
| --- | --- |
| Active version | `m2-649714e8b26775165f105d02` |
| Active eligible games / embeddings | 40 / 40 |
| Retained generations | One active; no inactive/staging generations |
| Database size before sizing | 12,850,867 bytes (12.85 MB) |
| Games, including indexes/TOAST | 237,568 bytes |
| Embeddings, including index | 131,072 bytes |
| Platform / term / price relations | 65,536 / 122,880 / 32,768 bytes |
| Catalog metadata | 49,152 bytes |
| Archive count / logical document bytes | 3 / 99,155; largest 85,332; no pending turn |
| Archive physical relation, including index/TOAST | 385,024 bytes |
| Alembic head | `0008`, confirmed from `discovery_migrations.alembic_version` |
| Available RAM at snapshot | 1,054,330,880 bytes out of 8,271,118,336 |
| Free local C: / E: disk | 3,192,221,696 / 2,150,760,448 bytes |

The active source observation begins 2026-10-14. All 40 have titles/descriptions/genre/mode documents; 38 have recorded final prices. Platform states are known: Windows 40 true; macOS 22 true/18 false; Linux 17 true/23 false. Dashboard developer/release/list-price/discount/review metadata is not retained in current `Game` documents, regardless of its possible presence in older raw snapshots.

After sizing/API reads, the active documents and version were unchanged: document digest **`4417edbb322e9016bc465d17e36270237d8e044869b74125782adce8250bd244`** before and after. The three archive aggregates were unchanged. Postcheck database size was 12,809,907 bytes; normal allocation changes are not evidence of user-data deletion. No retained data was deleted to create headroom.

## 2. Candidates and fixed pilot

The existing streaming audit reconfirmed **17,370 dashboard rows / 3,000 recommendation rows**, with unchanged CSV SHA-256 values from the [legacy audit](data-audit.md). The deduplicated candidate universe has **17,433 Steam IDs**, including all 40 active identities, legacy leads and manually supplied gap leads. Entries retain origins, inclusion reasons and either current coverage or explicitly untrusted legacy hints. This is not 17,433 eligible games. The pilot IDs happened to have zero overlap with the legacy CSV identities; fresh validation of legacy leads remains expansion work.

The fixed manifest is `data/fixtures/catalog-capacity-pilot.json`, SHA-256 **`d569c13c0695e3b4ed2da33bb7b188dd71a4f9019b6c9714488fea4d27e9982d`**. It mixes eight retained anchors and 24 gap/edge leads across action, strategy, simulations, puzzles, lower-budget games, multiplayer and non-Windows coverage. Selection labels are hypotheses, not popularity evidence.

Actual outcomes:

- 32 appdetails requests; 31 verified identities; **30 eligible standalone games**.
- `1281930` is `tModLoader`, source type `mod`: excluded, not counted as a standalone game.
- `1493710` returned `success=false`: recorded collection failure. The “Unpacking” lead used the wrong ID; it was not silently substituted/retried.
- Lead `787430` was mislabeled “Coffee Talk”; the canonical result is **Steel Arena: Robot War**. Only its verified title/document was normalized. Do not count this as narrative/cozy coverage. Civilization VI's punctuation/trademark difference is also retained as a title-label difference.
- The normalized eligible sample has 10 full genre labels, 27 single-player, 17 multiplayer, 11 online-co-op and four local-co-op games. Windows/macOS/Linux positives: 30/23/14. Explicit free-to-play: two; Early Access: one. Known normalized final prices: 29/30.
- The Witness preserves developer **`Thekla, Inc.`** as one complete company name, demonstrating why comma splitting is invalid.

For the selected final size, retain all existing eligible IDs, then curate roughly half recognizable, source-validated anchors and half smaller/recent/less-exposed titles across the candidate pool, adjusting for coverage rather than enforcing a new product quota. Fill strategy, simulation, racing/driving, narrative/cozy, rhythm, puzzle and co-op gaps; include free/lower/mid/higher recorded budgets and macOS/Linux. Review volume can document exposure, **not certify popularity or recommendation quality**. The pilot review totals span 11–9,963,911; its small low-volume tail is not a representative lesser-known-games benchmark.

## 3. Dashboard field feasibility and source findings

| Field | Eligible pilot coverage | Decision / limitation |
| --- | ---: | --- |
| Developer arrays | 30/30 | Complete strings, deduplicated per game; no comma splitting |
| Released date | 30/30 | All sampled dates include day/month/year; retain raw text and precision for future partial dates |
| Original/list USD cents | 27/30 | Two explicit free games have no price overview; one paid game lacks price data. Do not infer a list price from final price or free status |
| Final USD price overview | 27/30 | Existing normalizer additionally represents explicit free games at zero, giving 29 known final prices |
| Discount percentage | 27/30 | Missing price overview means unknown discount, not 0%; sampled valid percentages remain source facts |
| Review summary/counts | 30/30 | Preserve source labels and counts, explicitly label collection scope |
| Windows/macOS/Linux | 30/30 states | Keep false separate from unknown |
| Independent SteamOS | **0/30** | No separate field; owner decision requested above |

**The old review source is no longer a dependable bulk path.** Current [Steam documentation](https://partner.steamgames.com/doc/store/getreviews) marks `/appreviews` deprecated. Its one attempted pilot request for Portal 2 returned non-JSON and stopped the review phase. The failure remains in `pilot/reviews.json`; that initial non-JSON body was not saved because parsing preceded snapshot writing in the first helper revision. Snapshot writing was corrected for subsequent probes. No old-endpoint retry or access bypass occurred.

The documented keyless replacement, [IUserReviewsService/GetAppReviews/v1](https://partner.steamgames.com/doc/webapi/IUserReviewsService), produced **31/31 valid summaries** for the verified identities, including the excluded mod. Counts satisfied positive + negative = total. Requested scope: all languages, all acquisition types, both sentiments, Helpful filter with no day limit, off-topic activity filtered, English labels. Anonymous responses may be cached for ten minutes and have a shared lower rate limit. This is not a measured sustained bulk quota or the Steam-purchase-only storefront score scope.

Important discovery: `num_per_page=0` defaults to 20 on this endpoint; **611 individual reviews** were returned across the 31 requests, although only summary data enters proposed documents. A separate bounded Portal 2 probe with `num_per_page=1` returned one review **and** the complete valid summary. The helper now requests one; production collection should discard review bodies and retain only validated summaries/provenance. That probe was a different documented page-size check, not a retry of a failed request.

All 30 source labels were present: 16 Overwhelmingly Positive, 13 Very Positive and one Negative. No sentiment thresholds were invented. No independent SteamOS/Deck compatibility fields were found in appdetails. [Valve's compatibility documentation](https://partner.steamgames.com/doc/steamhardware/compat) and Proton support are distinct from a Linux boolean; this audit does not select another compatibility source.

## 4. Real-document storage and filtered retrieval

The proposal envelope adds real developer/release/price/review metadata with source URLs, timestamps and hashes to immutable pilot documents, **only in local audit artifacts/TEMP rows**. It is named `capacity-proposal-v0`, not a production format. One small aggregate envelope holds actual pilot description frequencies and metadata groupings for sizing; it is **not** Task 2's final analytics implementation.

The original `games`, platforms, terms, prices and 384-dimensional embedding table definitions were copied with real generated full-text columns, checks and all indexes via `LIKE ... INCLUDING ALL`. TEMP analytics adds a primary-keyed JSONB row. Foreign keys and RLS policies are **not copied** by that operation; these measurements do not establish restricted-role staged access, full import validation cost or RLS overhead. Every write was rolled back; TEMP relation removal was confirmed.

Beyond the 30 actual games, rows replicate their real document/vector/association distribution under **fixture-only IDs**. They are not additional collected titles or a measured diverse full catalog. Repeated terms can understate full-text index vocabulary growth; aggregate dimensions are still the 30-game envelope. These limitations drive the conservative budget below.

| Rows | One generation including indexes/analytics | Unfiltered p95 | Windows + single-player + ≤$20 p95 | macOS + online co-op p95 |
| ---: | ---: | ---: | ---: | ---: |
| 30 actual | 581,632 B | 855.627 ms | 106.562 ms | 119.759 ms |
| 500 fixture | 4,251,648 B | 100.585 ms | 89.917 ms | 90.882 ms |
| 1,000 fixture | 8,142,848 B | 97.890 ms | 139.911 ms | 91.555 ms |
| 2,000 fixture | 15,925,248 B | 89.760 ms | 149.067 ms | 111.908 ms |
| 4,000 fixture | 31,547,392 B | 109.247 ms | 119.637 ms | 109.612 ms |

Six sequential observations per case, **90 total**, under the existing two-second statement timeout. Each exact vector query applied hard filters before ordering/LIMIT 20, returned IDs and included local-to-Supabase round-trip time. Separate EXPLAIN ANALYZE executions at 2,000 rows took 3.608/8.725/5.402 ms server time for the three cases; at 4,000, 11.440/22.217/15.296 ms. The slower 855.627 ms first-case observation is retained, not removed.

This is not complete main hybrid/feedback scoring, 20+20 assistant fusion, document serialization, hosted CPU performance, network tail latency, concurrency or quality evidence. Real expanded-generation queries and active-version RLS must be checked before activation. No approximate vector index or similarity matrix is justified by this pilot.

## 5. Lifecycle budgets and recommended size

Use decimal **350,000,000 bytes** as a conservative engineering target (the existing importer checks 350 MiB). Public Supabase Free docs currently specify a **500 MB database quota**, distinct from 1 GB provisioned disk; exceeding the database quota can trigger read-only operation. They do not establish this account's plan. [Database-size docs](https://supabase.com/docs/guides/platform/database-size) / [pricing](https://supabase.com/pricing) were rechecked.

Planning formula, **not measured final occupancy**:

`current entire DB + measured fixture generation × 2 uncertainty × 3 generations × 1.30 margin + 64 MiB archive reserve + 32 MiB operational reserve`

Three generations mean active + staging + one retained full rollback generation. The old 40-game generation is already counted in the current database and is not deleted/subtracted. The archive has a 32 MiB logical shared ceiling; 64 MiB is a physical planning reserve, not a proven worst-case bloat bound. The uncertainty factor covers richer evidence, diverse full-text vocabulary and nonfinal analytics layout; it is deliberately explicit rather than calling replicated rows final measurements. Unlimited retained generations are not supported: ask about retention if growth requires more space, never delete generations or chat history silently.

| Total eligible target | Conservative lifecycle projection | Successful collection estimate | Sequential import estimate |
| ---: | ---: | ---: | ---: |
| 500 | 146.7 MB | 0.91 h | 6.5 min |
| 1,000 | 177.0 MB | 1.81 h | 13.0 min |
| **2,000 recommended** | **237.7 MB** | **3.63 h** | **26.1 min** |
| 4,000 | 359.6 MB, above target | 7.25 h | 52.2 min |

The estimates use measured successful request times plus a two-second pause for **each** appdetails/reviews request: about 6.53 seconds/game. They exclude source throttling, quarantine replacement searches, enrichment and manual selection. Allow roughly **4–5 hours of collection** for 2,000 with modest candidate failures, not a promised runtime. The pilot is curated; its 30/32 yield is not a reliable yield estimate for mixed legacy rows.

The real sequential 30-game TEMP import took **23.490 seconds**. Indexes/checks were present, foreign-key/RLS and full production validation/commit were not; the import column is a lower-complexity extrapolation. The actual selected-size operation still needs measurement. No COPY/batch import optimization was implemented before that decision.

## 6. Encoder, local IO and API memory

- Exact pinned MiniLM float-ONNX/tokenizer hashes matched the existing manifest; no downloads/model changes. Model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; 384-dimensional unit vectors, sequential batches of eight.
- Encoder initialization: **1.091 seconds**. Thirty actual semantic documents plus incremental checkpoint writes: **2.192 seconds**. Audit artifact: `m2-dccb5063dfd974aa956dd134`, validated locally, **not imported/active**. No cross-run embedding-reuse optimization was added.
- Local files: normalized games 174,760 B; proposed enriched documents 236,737 B; embeddings 338,023 B; aggregate envelope 15,221 B. Appdetails snapshots total 775,591 B; replacement-review snapshots total 1,275,310 B before the minimal-page probe.
- Sizing-process peak working set including ONNX and the largest fixture: **280,576,000 B**. This is a developer job, not the API process.
- A separate **single application** ASGI TestClient process with AI disabled and the real encoder/restricted database peaked at **274,231,296 B**, below the retained 400,000,000 B API target. Readiness, 50-item catalog search, facets, favorite discovery and semantic-query discovery all returned 200. The catalog still had 40 games; no expanded-catalog/AI-generation/hosted memory acceptance is claimed. An earlier 375,730,176 B observation accidentally loaded two application/encoder instances and is retained as `api-memory-two-apps-discarded.json`, not used for capacity.
- Whole-file loading and whole-vector-checkpoint rewriting remain real constraints. At the pilot's ~11.3 KB/vector JSON representation, 2,000 vectors are about 22.5 MB on disk; rewriting every batch of eight implies roughly **2.8 GB cumulative writes**, not 2.8 GB simultaneously stored. Linear embedding extrapolation (~146 s for 2,000) is only a lower bound because it does not model this growing rewrite cost. Profile the approved complete run before introducing the smallest needed change.
- Roughly 100–250 MB of local snapshots/documents/vectors per 2,000-game generation is plausible from these observations, but long descriptions/raw responses vary. Existing E: free space supports the pilot-based estimate with retained runs; preserve at least operational working room and recheck disk before collection. Do not delete model caches or historical experiments.

FastAPI Cloud [instance sizes](https://fastapicloud.com/docs/advanced-features/instance-sizes/) currently list Hobby Nano as 0.1 CPU/500 MiB; [billing docs](https://fastapicloud.com/docs/team-management/billing/) describe Hobby as free, 0.1 vCPU/512 MB shared. Keep the stricter 400 MB working target. Local ASGI measurements do not validate Linux/Nano CPU latency, deployment packaging, account settings or cloud cold starts.

## 7. Compatibility work required before growth

- **256-title limit is live, not merely historical.** `CatalogRepository.chat_title()` → `ChatRetriever.lookup_title()` is used by `ai/rag.py` for compatible `/api/v1/chat` title/reference paths **and** by `ai/dialogue.py` to resolve named exclusions in the current `/api/v2/assistant`. Above 256 the current code fails unavailable; ordinary assistant paginated search does not fix exclusion lookup. Replace complete-scan identity resolution deliberately, preserve normalization/ambiguity/aliases, and test a real match beyond the old cutoff before activation.
- Main `/api/v1/games` caps pages at 50 and offset at 6,000. Both proposed 2,000 and tested 4,000 rows fit that navigation bound. Native `assistant_search()` has a separately validated ≤30 page size/10,000,000 offset. Discovery ≤20, resolution ≤200 and bounded evidence/tool pages must remain; no complete catalog should enter an LLM prompt.
- Collector total bound remains **100 IDs**. The approved full manifest must become one generation; activating separate 100-game chunks would replace, not extend, the catalog. The existing collector also continues after source errors, so bulk use requires stop/checkpoint behavior plus verified snapshot reuse, not just a higher count bound.
- New fields must not widen assistant packets or old responses accidentally. Current `Game` parsing forbids extra fields. Metadata-only changes must preserve semantic-text/model identity and historical artifact hashes while explicitly versioning the enriched format.
- Read-only hosted compatibility requests for OpenAPI, readiness and catalog status all returned **HTTP 403**. No access workaround was attempted; the audit cannot verify the hosted revision or exact parser remotely. Local M2 contracts are strict, so **stage-only/coordinated activation is the safe assumption** if enriched fields enter `Game` documents. Resolve live access and verify a compatible deployed API in Task 3 before activation. No hosted release acceptance is claimed.

## 8. Checks, limitations and handoff

Actual verification: three new audit safety checks, eight existing catalog checks, focused Ruff and the helper's assert-based self-check passed. Audit tests cover first-source-failure checkpoint/stop, immutable ID manifests, no retry of failures, percentile calculation and mismatched-project refusal. Five real restricted-database ASGI reads succeeded. The sizing transaction rolled back, and before/after restricted reads confirmed byte-equivalent active documents, the same one catalog version and unchanged archive aggregates.

Full backend/frontend suites, mypy/OpenAPI drift and browser UI regressions were not rerun because serving/frontend/contracts did not change. No new dependency was installed. The API probe is not network HTTP, an AI conversation or a quality evaluation. An optional Windows swap-counter inspection failed because performance counters were disabled; RAM/disk observations above succeeded. Initial helper syntax/schema-query mistakes were corrected before successful measurements and are not counted as source failures or passes.

Local evidence identities:

- Candidate manifest: `a82085c5b7b99741d79d52fe59fa19a5efda330a282987b15387bf7cfc071d32`.
- Pilot normalized document digest: `6f37b3f67792de6586f89abf2ee33efe1a237757ccceaf93a857c24138472d93`.
- Measurement JSON: `9b6b4add4c46ed4272cb2b844c38f26a5bc8945f5edd2f44efac3b940c5acadf`.
- Pilot replacement-review receipt: `a1bf5dd92e21760d204b24ee87af3453e508f0fa53eb51053b162dbd5125e657`.

**Await the owner's total-size and SteamOS decisions.** Confirm free account allowances before bulk import. Preserve all current/frozen user work; do not start the dashboard or publication during this pause.
