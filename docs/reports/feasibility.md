# M0 feasibility evidence

Status: **M0 complete for implementation feasibility**, updated 2026-10-13. Local CPU/encoder and representative database-sizing gates passed with the limits below. Actual hosted behavior and account settings remain M1/release checks. This is not a deployment or recommendation-quality report.

## 2026-10-13 measured outcomes

### Catalog storage and exact retrieval

An explicitly migrated private schema held 3,000 historical descriptions, 36,000 synthetic taxonomy associations, 18,000 compact evidence excerpts and 3,000 synthetic 384-dimensional unit vectors. All games stayed quarantined; unknown currency/region/platform/freshness stayed null. This was a storage experiment, not a recommendation catalog.

First successful relations occupied **42,278,912 bytes**. A later reused run measured **41,738,240 bytes**, or **13,912.75 bytes/game** including sample indexes. Vacuum/GIN maintenance can change allocations. The failed initial 60-second COPY committed zero runs/games/embeddings; a bounded 180-second COPY timeout then allowed success. Idempotent rerun kept the same counts; a deliberately rolled-back insertion left no surviving row.

| Projected games | One generation | Active + staging, 30% margin and 32 MiB reserve | Below 350 MB |
| --- | ---: | ---: | --- |
| 6,000 | 83,476,480 bytes | 250,593,280 bytes | Yes |
| 8,000 | 111,301,974 bytes | 322,939,563 bytes | Yes, less headroom |
| 10,000 | 139,127,467 bytes | 395,285,846 bytes | No |

**Decision:** target 6,000 quality games initially; remeasure before growth to 8,000. These are linear projections, not final catalog sizes. Failed-write allocation may be retained, making the estimate conservative. Real evidence cardinality, staging and indexes require fresh measurement. No approximate vector index was selected.

Exact cosine local-to-Supabase round-trip p95 was **120.01 ms** over the first 12-query run, then **100.33 ms** and **348.32 ms** over two 12-query reused runs. These include network variability and synthetic vectors; they are not production recommendation latency or filtered-recall measurements.

Browser-role schema access was denied and checked. After saving reports, guarded cleanup removed the agent-created experiment. Database size returned to **11,269,811 bytes** before M1 metadata creation; no sizing data remains active. Expected default-deny RLS/no-policy and unused-index INFO notices disappeared with cleanup.

### Offline/online encoder compatibility

Windows CIM verified **Intel Core i5-5200U, two cores/four logical processors**; the runner reported **7,888 MiB RAM**, matching the agreed local machine class.

CPU reference: Sentence Transformers **5.7.0**, Torch **2.14.1**, Transformers **5.19.0**, batch 8, max 256 tokens, normalized 384-dimensional output. Sixteen texts covered blank, Unicode and long/truncated inputs. Encoding the set took **2,082.15 ms**; peak reference RSS was **568.01 MiB**. First loading included model acquisition and took about 95 seconds.

Float ONNX/reference minimum cosine was **0.99999994**, maximum absolute component error **1.86e-7**: passed thresholds of minimum cosine 0.9999 and maximum error 1e-4. Quantized minimum cosine was **0.973724**, maximum component error **0.034886**. The earlier eight-short-text comparison was insufficient for selection. **Select float ONNX**, with the same pinned model revision for offline artifacts.

### One-worker HTTP resource spike

FastAPI validation, serialized vectors, float encoder and a real read-only DB probe measured **224,448,512 bytes / 214.05 MiB** peak process-tree RSS, below the **400,000,000-byte** target. Cached startup: **4,357.98 ms**. HTTP short-query p95: **42.17 ms** (24 samples); long-query p95: **246.46 ms** (12 samples). Single-slot saturation at two clients produced one 200 and seven 429 responses across eight requests; it did not queue unbounded inference.

A Windows virtual-environment launcher spawns the actual interpreter. An initial launcher-only 3.33 MiB result was discarded. The corrected monitor sums launcher/descendant RSS, and a regression test covers that error. Shared pages may be counted twice, so the sum is conservative. The spike's readiness correctly remained 503 (`catalog_not_initialized`); no active catalog/ranking/LLM was claimed. HTTP requests never download weights.

This supports local viability, not Render 0.1-CPU/Linux latency, complete ranker/provider memory or a load-test guarantee. Repeat profiling after adding substantial layers.

### Source and exclusion behavior

Two further sequential runs made 24 logical fetch calls. **Project Zomboid (108600)** and **BeamNG.drive (284160)** exposed Early Access genre ID 70 plus matching page banners. Valheim's current sample did not expose that designation; historical brand knowledge was not used to override the source.

**Cyberpunk 2077 (1091500)** reported descriptors `[1,2,5]` and passed the ordinary-mature-game policy, while page enrichment hit a redirect loop. **FreshWomen - Season 1 (1350650)** reported adult-content descriptors and was excluded; HTML redirected to login and failed canonical identity. No login or age gate was bypassed. Policy excludes descriptor IDs 3/4, retains ordinary mature/violence/nudity IDs 1/2/5 and quarantines missing/unknown IDs. Independent manual content review is not claimed.

Aggregate reviews returned positive/negative/total counts with `language=all`, `purchase_type=all`, `filter=all`; zero-page requests returned no individual reviews. Counts must satisfy positive + negative = total. This scope differs from Steam-purchase-only storefront scoring and must remain labeled.

Nonexistent ID 999999999 returned appdetails success=false but reviews success=1 with zero counts. The first extended probe revealed that ambiguity. Corrected collection requires preceding appdetails identity before accepting reviews; the later Early Access/invalid-ID run confirms rejection. Older raw reports are retained as experiment evidence, not blindly reused as normalized facts.

**Selected sources:** best-effort Steam Store appdetails and aggregate appreviews; selective Scrapling-only static store-page enrichment with verified canonical identity. Unknown/gated data remains unavailable or quarantined. Public reachability does not establish an SLA, a bulk quota or redistribution rights. Keep snapshots local, preserve URLs/times/hashes and attribute/link Steam facts/artwork. Use one sequential process, conservative pauses, backoff and checkpoints. [Reviews documentation](https://partner.steamgames.com/doc/store/reviews) explains score scope and links its API; [Early Access documentation](https://partner.steamgames.com/doc/store/earlyaccess) explains the labeling requirement.

### Free hosting documentation resolved

The earlier Netlify 404s were stale guessed routes. Its sitemap identified [How credits work](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/how-credits-work/) and [Billing FAQ](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/billing-faq-for-credit-based-plans/). Credit-based Free has **300 credits/cycle, a hard limit, no auto-recharge**, and pauses all projects on the team at exhaustion until the next cycle. Production deploys cost 15 credits, transfer 20/GB and requests 2/10,000. Preview/branch deploys consume zero deploy credits, but traffic still counts. Pre-September-4-2025 accounts may retain legacy plans: verify the actual account before deployment.

Retain Netlify Free / Render Free / Supabase Free. Local memory and projected storage support that implementation path; hosted measurements/settings remain open. GitHub CLI access to the public `MS3B09/Games-Recommendation-System` repo is verified through a process-local Git safe-directory override. No global Git settings, commits, pushes or account-plan changes occurred. Netlify/Render connections are user-reported, not deployment-verified.

### Verification and reproducibility

M0 plus initial M1 checks total **26 passing tests**. Security advisor is empty after M1 migration. One expected new-table unused-index INFO notice exists for `job_runs_started_at_idx`; [remediation guidance](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index). Reassess that chronological-history index after usage, not while its table is empty.

Local reports under ignored `data/reports/`: `database-sizing.json`, `database-sizing-rerun.json`, `database-sizing-projections.json`, `encoder-parity.json`, `offline-reference.json`, `api-benchmark.json`. Code, model revision, input hash and summarized evidence reproduce the checks. Installing offline dependencies initially timed out mid-copy; a locked scikit-learn reinstall repaired the incomplete environment before parity passed.

## Earlier 2026-10-12 exploratory evidence

The sections below preserve initial results/blockers as history. The dated outcomes above supersede them.

## Sources

Ten requests sampled five app IDs: Hades (1145360), Portal 2 (620), Tirsy's Tale Soundtrack (3611730), Team Fortress 2 (440), and Bus Flipper demo (3736920). Five structured `appdetails` requests and five static Scrapling requests returned HTTP 200. Final identity checks accepted nine responses; the demo HTML redirected to parent app 2174560 and was rejected for enrichment of 3736920. The edge probe correctly exits 1 with `partial`, despite HTTP success.

Raw snapshots and SHA-256/source/time manifests are local under `data/raw/m0-source-probe/` and `data/raw/m0-source-edge-probe/`. This is a small feasibility experiment, not an expanded catalog or a reliability guarantee.

| Required evidence | Observed |
| --- | --- |
| Identity/type/release | `steam_appid`, `type`, `release_date.coming_soon`; soundtrack=`music`, demo=`demo` |
| Platforms | Explicit Windows/mac/Linux booleans; Linux positives observed |
| Modes | Category IDs: 2 single-player, 1 multiplayer, 38 online co-op, 39 shared/split-screen co-op in the sample |
| Regional price | Paid samples returned USD integer cents for `cc=us`; no live-price guarantee |
| Free status | TF2 returned `is_free=true` and no price overview; missing price alone is not free evidence |
| Semantic content | Readable descriptions and genre labels in structured data; user tags via Scrapling CSS selectors |
| Artwork | Header/capsule image URLs in structured data |
| Reviews | Structured recommendation totals available for some games; positive/total review coverage not yet verified |
| Adult-only/Early Access | Not sufficiently verified by this sample; remain normalization gates |

Use source categories rather than user tags for hard play-mode support: TF2's scraped “Online Co-Op” tag is not an equivalent authoritative category. Canonical identity checks must precede page enrichment. Region query parameters and USD responses support this sampled price interpretation; they do not prove every response will honor regional settings.

Probes were sequential within each run with 2-second pauses, 20-second request timeouts, and no retries. Final two small runs overlapped; these measurements establish accessibility only, not an acceptable sustained production request rate. Bulk collection must use one sequential process, backoff and checkpoints.

Steam store `robots.txt` did not disallow sampled app paths. [Steam Web API terms](https://steamcommunity.com/dev/apiterms) were inspected: availability can change and use must not degrade Steam. The documented Web API allowance must **not** be assumed to apply to the undocumented Store appdetails endpoint. Endpoint support, redistribution applicability, mature/age-gated pages and long-run rate behavior remain unresolved. Retain raw snapshots locally and publish only summarized evidence for now.

## Compact encoder experiment

Pinned candidate: `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (Apache-2.0 model metadata). ONNX Runtime CPU, one inference thread, max 256 tokens, attention-mask mean pooling, L2 normalization, 384 dimensions. No PyTorch or GPU was installed for this spike.

| Metric | Float ONNX | AVX2 unsigned-int8 ONNX |
| --- | ---: | ---: |
| Model bytes | 90,405,214 | 23,046,789 |
| Session initialization ms | 540.97 | 437.21 |
| Warm short-query p50 ms | 9.01 | 6.59 |
| Warm short-query p95 ms | 15.52 | 13.64 |
| RSS after requests MiB | 197.69 | 137.37 |

24 warm queries per representation; eight example texts compared. Overall sampled peak process RSS was **217.79 MiB** across sequential float/quantized runs. Corresponding float-versus-quantized vector cosine similarities ranged **0.990823–0.995252**. This is representation similarity, not retrieval accuracy or a passed production parity gate.

Runner reported four logical CPUs and 7,888 MiB RAM. CPU model and parity with the agreed target hardware were not verified. Download/cache time is excluded from inference timings. Full FastAPI startup/low-concurrency memory, long inputs, offline Sentence Transformers parity, seed retrieval recall and hosted 0.1-CPU latency remain unmeasured. Keep float as the initial reference; quantization is a candidate, not an approved active generation.

## Catalog storage

A 384-dimensional float32 vector payload alone uses 1,536 bytes per record: about 4.39 MiB for 3,000 games and 25.44 MiB for 17,369 games. These are arithmetic lower bounds, **not measured PostgreSQL storage**. Rows, text, taxonomy/evidence, TOAST, full-text indexes and active/staging generations add storage. No approximate index has been selected.

PostgreSQL/pgvector import sizing is blocked: neither `psql` nor Docker is available on PATH, and no configured database was used. A representative actual schema import, `pg_database_size`/`pg_total_relation_size`, and growth projection must pass the 350 MB target before M0 completion. No CSV has been imported into an application database.

## Free hosting checks

| Service | Current public documentation | Remaining gate |
| --- | --- | --- |
| [Render Free](https://render.com/docs/free) | 0.1 CPU / 512 MB RAM; 750 instance hours/workspace/month; 15-minute idle spin-down; roughly minute-long wakeup; ephemeral filesystem | Full API memory below 400 MB and account-specific bandwidth/build limits. Documentation says bandwidth overage suspends services without a payment method; with one it can bill. Verify free-only account settings before deployment. |
| [Supabase Free](https://supabase.com/pricing) | 500 MB DB, 5 GB egress, two active projects; pausing after a week of inactivity; no included automatic backups | Actual import/index storage, pooler/network compatibility and manual restoration; no claimed request-triggered unpause. |
| [Netlify Free](https://www.netlify.com/pricing/) | 300 credit limit; production deploy 15 credits, bandwidth 20/GB, requests 2/10k | Applicable account plan, exhaustion/hard-stop behavior and credit reset terms. Linked billing-document routes returned 404 during this check; pricing alone does not verify exhaustion behavior. |
| [Groq limits](https://console.groq.com/docs/rate-limits) | Free table includes `openai/gpt-oss-20b`: 30 RPM, 1,000 RPD, 8,000 TPM, 200,000 TPD; exact org limits can differ | Authenticated model availability, account plan, structured outputs and global reservations. No model or inference provider call has been activated. |

**Outcome:** the proposed free path remains plausible, conditionally. It is not deployment-validated. Render's temporary Free Postgres is not chosen (expires after 30 days); Supabase remains the sole proposed application database. Core discovery must work with AI disabled.

## Environment and installation

Python 3.13.12, uv 0.11.16, Node 24.13.0 and npm 11.6.2 were available. Python 3.13 is the pinned initial job environment, subject to compatibility testing when the API/offline stack is added. Optional dependencies and transitive hashes are in `backend/uv.lock`.

Installing on E: timed out three times and left an incomplete ignored `.venv`. A clean environment in the approved C: temporary directory installed the locked collection stack in 5.42 seconds; benchmark dependencies installed successfully. This local filesystem issue was bypassed without changing global configuration. Use the documented C: environment override here; a normal local filesystem can use `backend/.venv`.
