# M2 implementation evidence

Date: 2026-10-15 (source observations are recorded in UTC on 2026-10-14).

**Current status: M2 complete.** Hosted verification is owner-confirmed; the final [approved clean-database replay](m2-clean-replay.md) passed twice on PostgreSQL 17.10/pgvector 0.8.2 in GitHub Actions, with retained artifacts, CI evidence and cleanup confirmation. The following sections retain original implementation evidence. M3 has not started and requires explicit approval.

## Delivered

- Conservative normalized source/eligibility contracts, per-field evidence, real UTC observations, raw hashes, reproducible manifests and validated 384-dimensional vectors.
- Sequential resumable structured Steam collection, normalization, CPU embeddings, transactional staging/import, integrity checks and atomic activation.
- Search, detail, resolve, facets and non-LLM discovery APIs; generated OpenAPI/TypeScript contracts; POST CORS, bounded validated requests and credential-safe errors.
- Favorite selection, explicit budget/free/platform/mode/genre controls, result exclusions, image cards, recorded-price dates, Early Access labels, source-linked reasons and direct detail pages.
- User confirmed installed frontend skills and the precise extension layout. Impeccable/Emil guidance applied; detector returned `[]`; fresh independent reviewer disposition **ship**, with no material fixes, scoped to this narrow M2 extension. [Design record](../design/discovery.md).

## Real catalog and pipeline evidence

| Measurement/check | Observed result |
| --- | --- |
| Source | Selected Steam appdetails; US/English; 40 sequential requests |
| Collection UTC | 2026-10-14 18:52:47.736652 through 18:54:54.937875 |
| Eligible games | 40 of 40; none quarantined in this selected sample |
| Identity/provenance | Each response verified against requested Steam app ID; URLs, collection times and raw hashes retained locally |
| Artifact | `m2-649714e8b26775165f105d02`; [tracked manifest](m2-artifact-manifest.json) |
| Encoder | Pinned MiniLM float ONNX, 384 dimensions, normalized mean pooling, CPU, batch 8 |
| Embedding execution | Initial 40-vector compute: 6.447 s; later representation-guarded rebuild: 12.368 s; subsequent resume: 0 recomputed / 40 reused, 1.044 s job loop |
| Migration | Alembic `0001` → `0002`, explicitly applied through developer workflow |
| First import | 40 real games staged; no active catalog yet |
| Staging isolation | Restricted runtime API remained uninitialized; game endpoint returned `catalog_not_initialized` |
| Repeat import | Same generation reused, 40 games, no duplicate records |
| Activation | Complete artifact/database checks passed; generation atomically activated |
| Database size | 12,138,163 bytes after activation; comfortably below 350 MiB guard, not an expanded-catalog projection |
| Interrupted-write test | Real one-game subset insert interrupted after first game insert; complete rollback, no persisted test version, active catalog unchanged |
| Incomplete activation | Truncated embedding artifact rejected before database writes |

Public Steam responses, weights and full vectors stay local/ignored. Rerunning jobs on retained snapshots reproduces the manifest; collecting again produces a new historical observation/version. The test subset used real existing source records and never committed.

## Behavior and browser evidence

- **36 Python tests passed**: unknown price/platform/mode, inclusive/exclusive budget, free-to-play versus zero-price promotion, identity/eligibility, snapshot tampering, vector validity, stable semantic hashes, citation references, bounded requests, CORS and existing foundation checks.
- Ruff passes. Strict mypy covers API/core/database plus the three new serving catalog modules (13 files). Model-heavy development jobs stay outside strict serving typing.
- **11 Playwright checks passed**: original 7 foundation checks and 4 M2 checks covering favorites/outgoing constraints/exclusions/evidence, no-match versus failure/retry, canceled stale discovery, malformed citations, artwork fallback, mobile axe and direct detail reload.
- Frontend TypeScript/build and current-source ESLint pass. The existing C: execution cache contains unrelated old diagnostic scripts; lint was scoped to the synchronized project source/tests/scripts/configs rather than those extra cache files. No such scripts were removed from the user's cache.
- **Real local browser → FastAPI → restricted Supabase login passed**. Desktop 1440×900 and mobile 390×844: zero axe violations, no horizontal overflow, zero uncaught browser errors. Actual remote Steam artwork loaded; direct `/games/:id` and reload worked. Captures/report remain under ignored `.impeccable/review/m2/`.
- Nine real API/database cases passed: seed-only; Windows/single-player/under-$20; free-only; macOS+Linux all-match; online co-op; local co-op; impossible under-zero budget; unwanted action genre; exact title exclusions. Unknown favorite 422, unknown detail 404, saved-ID resolution and facets were checked. Nine observed request durations: 667.93–1,065.53 ms. This is a small local smoke sample, not hosted p95 or a quality evaluation.
- In the real UI Hades + Windows + single-player + maximum $19.99 returned Bastion, Enter the Gungeon, Transistor, The Binding of Isaac, Hollow Knight, Lethal Company, Cyberpunk 2077, Terraria, Risk of Rain 2 and Portal 2. Each passed the requested recorded-field constraints. This does **not** establish ranking quality, “less repetition,” current purchase prices or subjective suitability.
- Supabase security advisor after schema change: **no notices**. Performance advisor reported only new/unused-index INFO notices; [remediation reference](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index). No approximate vector index was added.

## Corrections during verification

- Removed unsolicited initial catalog browsing: a fast search could otherwise overlap the initial browse/facet requests and fill both backend admission slots. Search now runs only on explicit submission, preserving the bounded pool.
- Rebuilt a separate C: backend environment after the old M0 environment's Python launcher disappeared. Measured cold import on the slow filesystem took 19.19 s; the local smoke's startup allowance is now bounded at 75 s.
- Corrected smoke-runner browser-context setup for axe; failed attempts did not produce accepted captures. One successful desktop/mobile capture round was reviewed; no visual fix/rebuild was requested.

## Remaining gates and limitations

1. **Clean database replay — resolved:** approved [Actions run 38680812079](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680812079) on `3a62d1e` passed both fresh native builds, real CPU embeddings, migrations/import/activation, integrity/permission/rollback/API and reproducibility checks. Cleanup was confirmed. The exact report and verification metadata are retained in Git; no local PostgreSQL installation was required.
2. **Hosted M2 journey — resolved by owner confirmation:** M2 was published in commit `3453bfb` and both GitHub CI checks passed; the owner subsequently confirmed successful hosted deployment verification. This replay preparation task makes no production/provider changes and requires no hosting credentials.
3. Catalog size is deliberately 40 games, not the 6,000-game budget. Tags/reviews are not enriched yet; price/platform/mode facts come only from selected source fields. M5 covers expansion/refresh depth.
4. M2 has in-memory selection only. Browser persistence/feedback is M3; natural-language/conversation is M4. LLM/query-encoder capability flags remain false. Final brand/premium polish remains M6.
5. No relevance improvement, human evaluation, hosted latency/RSS, free-host load headroom, fresh-machine setup or physical-phone verification is claimed.

[Runnable operations](../operations-m2.md). All M2 gates are satisfied; [replay/CI/cleanup evidence](m2-clean-replay.md) and owner-confirmed hosted verification support completion. Stop and wait for explicit approval before M3.
