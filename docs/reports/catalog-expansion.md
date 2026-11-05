# Catalog expansion — Task 1 complete, verified staged handoff

**2026-11-05 10:35 UTC: Task 1 is complete at the documented staged-handoff scope.** Exactly **2,000 eligible games, 2,000 matching 384-dimensional vectors and 2,000 metadata documents** are staged in one generation, **`m2-cd9790b88f91370e69dae895`**, with all original 40 IDs retained. Import/idempotence/interruption, isolated expanded API/retrieval/RLS/rollback, resource and compatibility checks passed. **This generation is intentionally inactive:** the public catalog remains 40 games until the coordinated application/artifact/catalog release in Task 3. Dashboard and publication have not started; stop before Task 2.

## Task 1 completion — embeddings, staging and verification

### Artifact and import

- Exact original pinned MiniLM revision and cached tokenizer/float ONNX hashes verified; embedding ran CPU-only, batch 8, with `HF_HUB_OFFLINE=1`. No model download/provider inference. **2,000 embedded**, wall **230.972 s** (212.508 s encoding/checkpoint phase), peak working set **308,862,976 bytes**.
- Real resume with encoding prohibited reused **all 2,000 vectors**, keeping artifact/embedding/game/metadata file bytes identical. Resume peak **448,217,088 bytes** is a developer-job observation, not the API memory measurement; no new inference was needed.
- The full audit manifest measured **17,097 JSONB bytes before embedding**, above the existing 16,384-byte database manifest limit. `database_manifest()` now stores the bounded representation/checksums plus rejection count/hash and full artifact digest. Full local/public artifact bytes and version/hash semantics are unchanged; no schema relaxation or extra migration. Stored manifest: **1,846 bytes**.
- The measured 30-game row-at-a-time import took 23.490 s, projecting ~26 minutes at 2,000 (projection, not a measured full sequential baseline). Imports now use bounded **100-game batches**, still in one advisory-locked transaction with all existing validation and atomic activation guards.
- Actual full stage: **73.231 s**, 138 SQL statements, including 120 executemany batches; peak **228,634,624 bytes**. Repeated import: **29.430 s**, `reused=true`, no duplicated generation. All documents, vectors, identity keys, platform/term/price associations, metadata and manifest contents verified against local artifacts.
- Existing real-DB interruption check passed: partial write rolled back, incomplete vector artifact rejected before activation, original active version unchanged. Existing embedding-part interruption recovery remains covered by the focused checks.

### Expanded runtime, isolation and rollback

`backend/scripts/verify_expanded_catalog.py` copies the actual staged generation and original rollback generation into an exact tagged, private schema in the **same database**. It uses the actual restricted runtime login, recreates active-version RLS/read-only grants/FKs, translates only schema qualification in existing repository SQL, and exercises actual FastAPI handlers through TestClient. It does not grant runtime write access, activate the public catalog, run inference or copy chat/usage data.

Final expanded check passed:

- Active-only catalog/metadata reads; inactive version hidden; writes denied; all transaction-local two-second statement limits retained.
- Exact/reference title lookup beyond the old 256 cutoff (Outer Wilds, 753640), punctuation, ambiguity and honest absence.
- **19 ASGI requests**: actual readiness/version/semantic status, first/last catalog pages, all original saved IDs, full **200-ID** saved resolution, canonical detail/facets, ten hard-filter combinations and actual local semantic discovery. Price/mode/platform/genre/exclusion constraints and reason/card provenance checked.
- **12 real encoder + restricted-DB chat RRF retrieval samples**, plus direct native assistant title paging, details and filtered recommendation/exclusion tools. No model or archive access. Dashboard metadata does not leak into strict Game/assistant evidence.
- Isolated **2,000→40→2,000** committed switch/rollback; an uncommitted change remained invisible to the separate restricted reader. The actual public version/digest never changed.
- All exact owned schemas removed, including two initial fixture trials that correctly rejected activating a staged row without `activated_at`; the private fixture was corrected to use the real publication invariant. No production constraint was weakened.

Measured final bounded samples (not hosted performance/relevance acceptance):

| Measurement | Result |
| --- | --- |
| ASGI/API samples | n=19, p50 468.685 ms, p95/max 1,354.137 ms; includes 200-card saved resolution |
| Chat encode + exact retrieval + RRF | n=12, p50 607.776 ms, p95/max 650.108 ms |
| API probe peak working set | **346,316,800 bytes**, below the 400 MiB engineering target |
| Actual database after scratch cleanup | **31,446,707 bytes**, below the 350 MiB engineering target |
| Public catalog relation/index total (both retained generations) | **18,694,144 bytes**; rest of database remains included in the database total above |

An earlier 18-request probe measured 667.202 ms API p95 / 473.122 ms chat p95; the final expanded 19-request results above are retained as the current result, not replaced with the faster round. No representative hosted SLA, broad relevance or live assistant-quality pass is claimed. No old evaluation campaign was resumed.

### Activation decision and current database

Hosted OpenAPI/readiness/catalog probes now return **HTTP 200**, superseding the earlier 403 limitation. Hosted **Game, Evidence, Source and Price schemas match exactly**, and every expanded Game document retains the same public keys. This establishes wire compatibility, **not** hosted 2,000-game semantic/runtime acceptance.

The existing configured semantic artifact is still **`m2-649714e8b26775165f105d02`**. Activating the new catalog alone would mismatch that running artifact and degrade current local semantic retrieval; the currently hosted M2 runtime also reports semantic/LLM disabled. Therefore use the completion plan's **staged-only/coordinated-release path**: preserve the current active version and switch the latest application, pinned full artifact and catalog together during Task 3. No user service or ignored configuration was changed merely to force activation. The staged data, normalized inputs and reproducible isolated runtime check are available for Task 2 development.

| Database relation/state | Verified count |
| --- | ---: |
| Staged games / embeddings / dashboard metadata | 2,000 each |
| Staged platform states | 6,000 |
| Staged normalized terms | 8,695 |
| Staged price records, including explicit unknowns | 2,000 |
| Retained generations | 2: original active 40; expanded inactive 2,000 |
| Restricted runtime visible staged games/metadata | 0 / 0, as required by RLS |
| Remaining owned scratch schemas | 0 |

Rollback reference remains original version **`m2-649714e8b26775165f105d02`**, document digest **`4417edbb322e9016bc465d17e36270237d8e044869b74125782adce8250bd244`** and its existing configured full artifact. No historical generation or archive was deleted. Before/after archive aggregates and usage counters were identical; zero actual LLM calls/reservations. Supabase security advisories `[]`; two pre-existing informational [unused-index advisories](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index) (`job_runs_started_at_idx`, `games_search_idx`) were retained, not removed to manufacture a clean report.

### Reproducibility and acceptance evidence

- New safe public inputs: [`catalog-expansion-2000-app-ids.json`](../../data/fixtures/catalog-expansion-2000-app-ids.json) and the full self-consistent [`catalog-expansion-2000-manifest.json`](../../data/fixtures/catalog-expansion-2000-manifest.json). They contain public app IDs/rejection reasons and artifact/model digests, not raw snapshots, models, secrets or private capabilities. The full manifest is byte/identity-compatible with the runtime artifact; the **database** stores its smaller hash-linked projection.
- Embeddings digest: `52955e42d1cc9970254a520f496f4b60b41a47f5bb9ae57f2798748495f51d63`; version **`m2-cd9790b88f91370e69dae895`**. The original game/metadata/source digests below remain unchanged.
- Full backend suite: **291 checks OK (1 skipped)**, 9.155 s; all-backend Ruff, strict mypy **30 configured modules**, and unchanged OpenAPI drift pass. The skipped external private journal remains a historical limitation. One focused compact-manifest test added; no dependency/model/API/UI change.
- Ignored machine evidence: `data/reports/catalog-expansion-task1-final.json` binds collection, embedding/reuse, interruption, stage/idempotence, runtime, hosted schema and final-database receipts by file hash. `catalog-expansion-2000-runtime.json` retains individual request/retrieval samples.
- Full staging/import commands below have run successfully. No pending collector, embedding or import job. No commit/push/deploy, frontend implementation or new live AI evaluation. **Task 1 done; Task 2 needs the owner's phase approval and frontend-skill confirmation.**

## Collection completion — 2026-11-05

The first collector reached 2,000 at 06:39 UTC, but semantic eligibility review found software such as OBS Studio and Wallpaper Engine reported by Steam as `type="game"`. Initial source/hash checks therefore did **not** establish the required game-only population. Those initial documents, checkpoint, verification receipts and 25 unavailable-ID snapshots were preserved in the authoritative run's `pre-software-review-20261105T0642/` directory (31 files, hash-verified).

The shared classifier now conservatively quarantines Steam software-genre IDs 50–60 as `software_genre_requires_verification`, including mixed game/software classifications; this does not assert that every mixed-category title is software. No per-title serving exceptions or inferred facts were added. The collector refreshes cached classification decisions while preserving successful source snapshots. A single explicit resume revalidated the queue, retried the 25 unavailable candidates with originals preserved, and collected replacements from untouched candidates under the original sequential request limits. The original 34 software-tagged selections were removed; one additional software-tagged replacement candidate was quarantined before reviews. All **4,171 previously successful source-file hashes** remained unchanged.

Final checkpoint: **2,235 observed candidates → 2,000 eligible unique games + 235 rejected/quarantined/unavailable candidates**; 265 queue entries remain untouched. Rejection reasons:

| Reason | Count |
| --- | ---: |
| DLC | 153 |
| Software genres requiring verification | 35 |
| Unavailable/unverified identity | 25 |
| Music/soundtrack type | 11 |
| Mod type | 6 |
| Demo type | 2 |
| Missing description | 2 |
| Unreleased | 1 |

Both completed collector commands exited **1 / `partial`** because the CLI retains any failed candidate in its status. This is not a clean collector exit or erased failure history: independent final verification proves that **all 2,000 selected games have complete hash-verified appdetails/review source pairs**, and no source stop remains. No further collection/resume is needed.

Final verification checked all **4,269 recorded source-file hashes** (2,235 appdetails, 2,000 selected review projections and 34 retained review projections for subsequently quarantined records), canonical identities, US/English appdetails parameters, exact review scope/count arithmetic, released-game/content/software eligibility, all required IDs, metadata/document equality and unchanged checkpoint bytes. **No duplicate normalized titles** and no collector process remained. `normalize(..., metadata=True, target_count=2000, required_ids=...)` and subsequent `load_games`/`load_metadata` validation passed.

### Final collected coverage

| Field | Source-supported coverage |
| --- | --- |
| Required existing IDs retained | 40 / 40 |
| Review summaries | 2,000 / 2,000 |
| Developer names | 1,999 known; 1 unknown |
| Release-date strings | 2,000 known; 1,999 day precision, 1 unparsed/unknown precision |
| Original USD price / discount | 1,608 known; 392 unknown for each; no fabricated free/list prices |
| Final recorded USD price | 1,959 known; 41 unknown |
| Explicit free-to-play | 352 free, 1,648 paid |
| Platforms | Windows 2,000; macOS 496; Linux 331; all platform states recorded |
| Play modes | Single-player 1,860; multiplayer 665; online co-op 411; local co-op 111; overlapping counts |
| Early Access | 165 |

The Linux count is **not** independent SteamOS/Steam Deck verification. Twelve complete source genres remain, including action 919, adventure 819, RPG 483, strategy 349, simulation 489, casual 527, sports 94 and racing 72; multi-genre counts overlap. Selection origins: original 40, curated 347, Steam-chart leads 77 and legacy leads 1,536. Origins document selection, not a claim that every selected title is popular. Observation timestamps span 03:13:02–06:51:28 UTC on 2026-11-05; these are recorded US/USD observations, not live purchase guarantees.

### Completion receipts and checks

- Authoritative artifacts: `games.json`, `metadata.json`, `normalized.json` and `collection-verification.json` inside the C: run below. The verification file includes the per-source hash manifest; ignored summary receipt: `data/reports/catalog-expansion-2000-collection-verification.json`. Software-review/backup receipt: `data/reports/catalog-expansion-software-review-20261105.json`.
- Canonical games digest: `8fd37a0d4d700000cd97c098db18ca7cc0465fd148fea35474913bf1e053140a`.
- Canonical metadata digest: `ad2edf1351a4247de8f587ac0985ed21c8465e4165765d2a15b927622690707e`.
- Final collection-file SHA256: `b90e269fe5145e2636e393d0b775791a04afba0ffdf62f49439dd9d9d2d36711`.
- Normalized files: games 11,760,678 bytes; metadata 5,305,709 bytes; manifest 20,301 bytes. These are local file sizes, not measured expanded-database occupancy.
- Five eligibility and seven affected collector checks passed with the software/mixed-genre and cached-reclassification assertions added to existing tests. Full backend suite rerun: **290 tests OK, one skipped**, 14.553 s. Ruff across backend passed; strict mypy **30 modules** passed; repository-root OpenAPI `--check` passed without regeneration. An initial OpenAPI check from `backend/` used its root-relative default output path incorrectly; rerunning from the repository root resolved the command-context error without a contract change.
- No live AI inference/reservations, database writes, user-service changes, dependency/config/model changes, frontend work or publication in this collection continuation. Old source/evaluation evidence remains preserved. No expanded activation was performed; this work did not replace the existing public 40-game generation.

**Historical collection-only boundary:** this 06:53 UTC checkpoint preceded embedding/staging. The completed Task 1 results and explicit staged-only activation decision are recorded above; dashboard/release acceptance remain separate.

## Owner decisions

- 2,000 eligible games approved after the [capacity audit](catalog-capacity-audit.md).
- Existing free plans confirmed by the owner; no paid resource or allowance change.
- Requested dashboard label: **Linux(SteamOS)**. Its count will represent source-verified Linux support, with an explicit note that independent SteamOS/Steam Deck compatibility is not verified. No invented separate compatibility flag/count.

## Implemented so far

1. **Bounded collector:** at most 2,500 candidate IDs, with a 1–2,000 eligible completion target, immutable identity/settings checks, hash-verified successful-source reuse, per-ID progress and stop-on-source-error. Unavailable individual identities remain visible; no source-access bypass or automatic HTTP retry. Cached successful IDs do not trigger no-op checkpoint rewrites.
2. **Reviews:** current keyless Steam reviews API, one requested review, validated aggregate counts/scope, and a hashed summary projection. Public author IDs/review text are not retained by the collector. The original response hash remains provenance; the projection has its own independently verified snapshot hash.
3. **Versioned metadata:** developers as whole names, partial/raw release dates, original USD cents separately from final price, discount integers including invalid-value visibility, review scope/counts/label and source evidence. Metadata is stored in a separate immutable document/checksum, not inserted into public `Game` or assistant evidence. Legacy schema-v1 normalization/artifact hashes retain their meaning.
4. **Exact size and retention checks:** normalization requires the selected eligible count and all required existing identities. A target-enabled interrupted collection cannot be normalized as a completed generation.
5. **Embedding checkpoint IO:** measured full 2,000-vector JSON write at 11.212 s and load at 0.799 s on E:. Rewriting it every eight records implies substantial avoidable cumulative IO. New atomic per-app embedding parts preserve validated model/content identity and resume interrupted work; the final combined JSON/digest remains compatible. Existing combined checkpoints are still reused. A test verifies interrupted-part recovery and zero new encoding when only metadata format changes.
6. **Complete title matching:** parameterized database matching of normalized/compact identities, canonical references, whole-token/compact phrases, verified aliases and bounded prefix ambiguity. Only returned options and fuzzy suggestions are capped; a match beyond app 256 is not lost to a truncated scan. Missing identity keys fail unavailable, not false absence. Fuzzy suggestions use an explicitly bounded prefix pool and never establish identity.
7. **Additive schema:** Alembic **`0009` / SQL `0010_catalog_expansion.sql` applied** using the developer migration CLI. It adds title keys/indexes, an optional generation manifest and active-version-RLS dashboard metadata relation. Existing 40 titles were backfilled with the same Python NFKC/casefold rules. Game documents, vectors, prices, archive/usage tables and public activation were not changed.

The separate metadata relation deliberately avoids widening old strict Game serializers. Hosted compatibility still needs actual verification before expanded activation; prior public probes returned 403. Keep the staged-only/coordinated-activation option from the completion plan.

## Fixed candidate queue and source status

The immutable queue has **2,500 leads**: 40 required active IDs, 349 curated gap leads, 83 additional Steam most-played identity leads and 2,028 legacy CSV leads. Category/title/review hints are leads, not validated facts or popularity claims. Steam-chart source bytes/time/URL/hash are recorded locally; the list includes non-games, so appdetails eligibility checks remain mandatory. The legacy queue uses a deterministic rotation over untrusted genre hints and a title prefilter to avoid obvious non-game/adult collection leads; that prefilter is not the eligibility classifier.

Initial source collection stopped on an actual **HTTP 502 from Valheim's reviews**, after 25 complete game/source pairs and 26 appdetails observations. The failure is preserved in `collection-stop-1.json`; Valheim's successful appdetails was not refetched. One explicit resume attempt stopped while revalidating cached IDs because of an **E: PermissionError during atomic checkpoint replacement**, before reaching the failed review. Subsequent source reads and an isolated atomic IO probe passed, so the exact transient lock/root cause is unproven; the failed `.tmp` and original run remain preserved.

The run was copied to the approved C: working location, verifying **59 files byte-for-byte** and rechecking every retained appdetails/review projection hash. **C: is now authoritative**:

`C:/Users/User/AppData/Local/Temp/opencode/catalog-expansion-2000-20261105/`

The original `data/raw/catalog-expansion-2000-2026-11-05/` is a retained, older copy. Never copy it over the newer C: checkpoint. Relocation receipt: `data/reports/catalog-expansion-run-relocation.json`. The C: collector was explicitly resumed; it is a sequential source job, not an assistant evaluation. Any later source error must stop/checkpoint again, not trigger a hidden retry loop.

**Historical progress snapshot, 2026-11-05 03:48:14 UTC:** 108 observed IDs / **108 eligible complete source pairs**, including all **40 required retained identities**; no source stop at that checkpoint. Valheim's failed review succeeded on the explicit C: resume. Receipt: `data/reports/catalog-expansion-progress-2026-11-05.json`. The collector has now finished; use the completion section above.

**Owner continuation, 2026-11-05 05:39 UTC:** owner requested continuing collection through all 2,000 eligible games without another next-step question. The existing C: collector was still running (launcher 10832 / serving child 22440, one sequential job; no duplicate started). A fixed in-progress checkpoint independently verified **1,340 eligible complete source pairs**, all **40 required IDs**, **2,769 source-file hashes**, US/English appdetails identity, review request scope/count arithmetic, and all 1,340 metadata documents. No duplicate normalized titles were found. Of 1,429 observations, 72 were noneligible/missing-description records and 17 were unavailable identities; none counted toward the target. Known developers: 1,339; release-date source strings: 1,340; original-price/discount fields: 1,109; review summaries: 1,340. This is partial coverage, not final acceptance. Receipt: `data/reports/catalog-expansion-inprogress-integrity-20261105T0537.json`, checkpoint SHA256 `a4d5d7c7171c76bcad606ecefb142fb1b389b3f099becf20c36aef7491a6cf1b`. No new source request, source edit, database write or service change was needed for this verification. Wait for the existing collector's completion/error notification, then validate the complete checkpoint and normalize exact 2,000/all required IDs; preserve source-error stops and do not duplicate the running job.

## Earlier pipeline checkpoint — before expanded staging

- Full existing/new backend suite: **290 checks OK, one skipped** (retained external private journal absent), before the final cached-success no-op-write refinement; **all seven affected collector/metadata/embedding checks passed again afterward**, including no writes/network for cached successes.
- Ruff across backend passed; strict mypy passed for the three affected contract/retrieval files and then **all 30 configured modules**. Full mypy must run from `backend/`; invoking its relative configured file list from the repository root produced a command-context error, not a serving-code failure. C: cache avoids the earlier E: timeout.
- OpenAPI drift check passed unchanged. No generated frontend contract change is needed: metadata is not in existing wire responses.
- Real **341-row private-schema** checks passed before and after applying the migration: beyond-256 Unicode/title/reference/alias/ambiguity behavior, fail-closed missing keys and active/inactive metadata RLS/write denial. Initial `SET ROLE` trials were denied and rolled back. The final check used separate actual developer/restricted connections, briefly committed isolated fixtures so the restricted connection could see them, then verified and removed only its exact tagged owned schema. No role privileges were elevated or public catalog activated.
- Post-migration restricted reads returned Hades=1145360, Portal-2=620, Spider-Man=1817070 and both Ori IDs. All 40 identity-key rows are populated. No metadata rows exist for the old generation, rather than fabricated old dashboard coverage.
- Current active version remains **`m2-649714e8b26775165f105d02`**, one retained generation, 40 games; document digest **`4417edbb322e9016bc465d17e36270237d8e044869b74125782adce8250bd244`** unchanged. Database measured **13,096,627 bytes** after the additive migration. No owned scratch schema remains. Supabase security advisories returned `[]` after the schema change.

Evidence: ignored `data/reports/catalog-expansion-2000-migration-check*.json`, `catalog-expansion-2000-migration-applied.json`, `catalog-checkpoint-profile-2026-11-05/report.json` and relocation receipt. These measurements do **not** establish final 2,000-game storage, performance, field coverage, review quality or hosted acceptance.

## Commands and continuation

```powershell
$python = '.\backend\.venv\Scripts\python.exe'
$runDir = 'C:/Users/User/AppData/Local/Temp/opencode/catalog-expansion-2000-20261105'
# Already applied and verified:
& $python -m game_discovery.db.migrate current --env-file backend/.env
# Historical command only: this run has completed 2,000; do not resume it again.
& $python -m game_discovery.jobs collect --ids-file "$runDir/candidate-ids.json" --run-dir $runDir --reviews --eligible-target 2000 --resume
```

These Task 1 commands are **completed**, retained for verification/reproducibility. Do not rerun collection or activate publicly as part of this handoff:

```powershell
# Already completed and verified; retained here for reproducible normalization:
# & $python -m game_discovery.jobs normalize --run-dir $runDir --metadata --target-count 2000 --required-ids-file "$runDir/required-ids.json"
& $python -m game_discovery.jobs embed --run-dir $runDir --cache-dir C:/Users/User/AppData/Local/Temp/opencode/game-discovery-models --batch-size 8 --resume
& $python -m game_discovery.jobs verify-import --run-dir $runDir --env-file backend/.env --output data/reports/catalog-expansion-import-verification.json
# Idempotent stage only; public activation is deferred to coordinated Task 3.
& $python -m game_discovery.jobs import --run-dir $runDir --env-file backend/.env
& $python backend/scripts/verify_expanded_catalog.py --run-dir $runDir --env-file backend/.env --output data/reports/catalog-expansion-2000-runtime.json
```

For a future refresh, use a **new** run directory; never overwrite the completed source snapshots, manifests or frozen evaluation runs. The fixed eligible IDs are starting identities, not permission to assume future source eligibility. A newly unavailable/ineligible title must not count toward 2,000; use an explicitly reviewed replacement decision if needed.

```powershell
$refresh = 'C:/Users/User/AppData/Local/Temp/opencode/catalog-refresh-YYYYMMDD' # NEW directory
& $python -m game_discovery.jobs collect --ids-file data/fixtures/catalog-expansion-2000-app-ids.json --run-dir $refresh --reviews --eligible-target 2000
# Explicit --resume only after inspecting a source stop; no hidden retry loop.
& $python -m game_discovery.jobs normalize --run-dir $refresh --metadata --target-count 2000 --required-ids-file data/fixtures/m2-app-ids.json
$env:HF_HUB_OFFLINE = '1' # This terminal/process only; verified existing pinned cache.
& $python -m game_discovery.jobs embed --run-dir $refresh --cache-dir C:/Users/User/AppData/Local/Temp/opencode/game-discovery-models --batch-size 8 --resume
& $python -m game_discovery.jobs verify-import --run-dir $refresh --env-file backend/.env --output "$refresh/import-verification.json"
& $python -m game_discovery.jobs import --run-dir $refresh --env-file backend/.env
# Activation needs coordinated runtime/artifact compatibility and the applicable release approval.
```

No user service was stopped/restarted; no ignored environment file, dependency/model version, quota, archive or accounting data was changed. The expanded generation was written through the privileged developer import only; runtime access remains read-only/RLS-restricted. No live LLM calls/reservations, frozen evaluation continuation, frontend implementation, commit, push or deployment. Dashboard skill confirmation remains a Task 2 gate.
