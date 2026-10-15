# M2 clean-database replay verification

Status: **PASSED on 2026-10-15. M2 is complete.** The owner authorized publication/execution; the workflow passed on its first attempt, all required replay checks passed, cleanup was confirmed, and the already verified hosted deployment is owner-confirmed. **Stop before M3; explicit approval is required.**

The owner confirmed successful M2 hosted deployment verification on 2026-10-15. That is owner-reported acceptance; this task did not re-run or modify the live Netlify/FastAPI Cloud/Supabase deployment. Clean-database replay was the last remaining M2 acceptance gate and is now satisfied by the results below.

## Verification design

- Workflow: `.github/workflows/m2-clean-replay.yml`, **manual `workflow_dispatch` only**, on the existing repository/default `main` branch. No new branch, push trigger, pull-request trigger, schedule or deployment step.
- Service: PostgreSQL **17** with pgvector **0.8.2**, `pgvector/pgvector:0.8.2-pg17-bookworm` pinned to multiarch digest `sha256:feb68f4f15446397d8cac7f4fe48fe4586de83160d1fc48b46283312d1a33966`. Registry metadata was checked while preparing the workflow; no container was run locally.
- CPU-only runtime, locked Python dependencies, pinned MiniLM model revision and byte hashes; no PyTorch or hosted inference requirement.
- Frozen projections of the same **40 real source observations** used for M2. No Steam traffic or scraping during CI. The fixture contains only the public fields needed by normalization; the exporter verifies equivalence against the retained original response before writing each projection. Original source URLs, UTC collection timestamps and original HTTP hashes are retained. Temporary projection files receive their own verified hashes, explicitly distinguished from original HTTP-body hashes.
- Two independent source materializations, normalization and **fresh embedding computations**, each followed by migrations from empty native schemas, staging, validation and activation. The temporary database and runtime role are dropped between passes, so the second pass cannot reuse schema or imported rows. Only pinned model files are reused within the runner; embedding artifacts are rebuilt.

## Acceptance checks — all passed in the approved run

| Check | Verified evidence from the approved run |
| --- | --- |
| Clean migrations | No `discovery`, `discovery_migrations`, `extensions`, pgvector extension or runtime role before each migration; actual PostgreSQL 17 and pgvector 0.8.2; Alembic head `0002` |
| Migration rerun | Reapplying `upgrade` succeeds without duplicating schema |
| Source and artifacts | Exactly 40 identities, no quarantine, valid snapshots/content hashes, normalized 384-dimensional vectors, pinned tokenizer/model file hashes |
| CPU embeddings | Each independent pass computes 40; checkpoint resume computes 0 and reuses 40 |
| Import/activation | Staged rows hidden from runtime; identical import reused; only one active generation; repeat activation leaves data fingerprint unchanged |
| Integrity | Published documents/platforms/terms/prices/vectors match artifacts; correct dimensions/norms; duplicate identity, orphan platform FK and wrong model-dimension writes rejected |
| Least privilege | Runtime has no elevated attributes/memberships; all catalog tables use RLS; no PUBLIC schema usage; writes, DDL, job logs and migration metadata denied |
| APIs | Real FastAPI TestClient → restricted PostgreSQL login: health/readiness, search/details/resolve/facets, nine discovery filter/exclusion cases, empty results, unknown IDs, evidence references and POST CORS |
| API role protection | Serving with privileged developer login is rejected |
| Interrupted imports | Existing real-write interruption check rolls back; incomplete activation rejected; active generation/data fingerprint unchanged |
| Reproducibility | Both fresh artifact manifests, all table fingerprints and ordered recommendation-case results agree exactly **on the same runner** |
| Teardown | Test DB/runtime role explicitly dropped; scratch files removed; service container/network and hosted VM discarded by Actions |

Created/activated operational timestamps are intentionally omitted from database fingerprint comparison; immutable source observation timestamps are retained. This does not claim bit-for-bit embedding parity across operating systems/CPU builds, an exact match to production's historical manifest, or independently evaluated recommendation relevance. Projection provenance creates a deliberately separate replay artifact version.

## Local preparation results — actually executed

- **41 offline Python tests passed**, including the original 36 and five replay preparation/isolation/fixture/workflow checks. No database connections, model inference or GitHub workflow execution occurred in the new offline tests.
- Ruff passed for all backend source/scripts/tests.
- **actionlint 1.7.12 passed** for the new workflow; its downloaded Windows binary matched the published SHA256. External shellcheck/pyflakes integrations were disabled; this was static validation, not workflow emulation/execution.
- Existing generated OpenAPI check passed; no serving API contract change is required.
- Repository metadata was read to confirm this is the existing **public** repository with default branch `main`. No GitHub settings, branches, workflow runs or deployments were changed.

These preparation checks alone did not close the gate. The actual GitHub execution below now does.

## Actual execution results

- **Replay:** [GitHub Actions run 38680812079](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680812079), attempt **1**, completed successfully. Tested commit: [`3a62d1ef2f07eb5d2b7f080ab5edb35f4ea2db70`](https://github.com/MS3B09/Games-Recommendation-System/commit/3a62d1ef2f07eb5d2b7f080ab5edb35f4ea2db70).
- Job: **04:18:58–04:19:41 UTC, 43 seconds**. Replay helper: **04:19:25.939917–04:19:35.812219 UTC**. Native server: **PostgreSQL 17.10 (Debian)**, pgvector **0.8.2**, Python **3.13.13**, x86_64.
- **Two independent clean passes**, each applying original migrations to head `0002`, normalizing 40 real-source fixture games with no quarantine, computing all 40 embeddings from scratch, importing and activating successfully. The second database/role was freshly created after the first was discarded.
- Each resume computed **0** vectors and reused **40**. Fresh embedding loop times were **0.981 / 0.966 seconds**; these exclude model acquisition and are not hosted latency measurements.
- Both passes produced artifact **`m2-10190ee67b2b13af7840bb0a`**, identical table fingerprint **`78f266b635b7087605e73453e3a2d9c1573c408fc720650114a7e44f0fa16b4c`**, identical embedding hashes and identical ordered outputs for all **nine API cases per pass**.
- Each database contained **40 games, 120 platform rows, 186 term associations, 40 prices and 40 embeddings**. FK/unique/dimension constraints, vector norms, staging isolation, RLS/least-privilege and privileged-serving rejection passed. Repeat migrations/import/activation and interrupted/incomplete-import checks passed.
- Nine request observations per pass ranged **5.19–9.40 ms** through TestClient and the same-runner database. This is only a small local CI smoke sample, not public-demo latency, p95 or relevance evidence.
- **No failures, fixes or reruns were needed.** The one nonblocking Actions annotation concerned the pinned upload action's Node 20 metadata; GitHub executed it on Node 24 and artifact upload succeeded. No unrelated action upgrade was introduced.

### GitHub CI

- [Backend CI 38680783914](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680783914) on replay commit `3a62d1e`: **success**, **41 tests**, Ruff, strict mypy (13 modules) and generated OpenAPI checks passed.
- [Frontend CI 38673824585](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38673824585) on M2 application commit `3453bfb`: **success**, lint/contract/type/build and **11 browser tests**. Git diff confirmed frontend source, API contract, frontend workflow and Netlify configuration are unchanged since that run. Existing path filters therefore correctly did not rerun frontend CI for the replay-only commit.

### Retained evidence and cleanup

- The exact downloaded [machine-readable replay report](m2-clean-replay-38680812079/replay.json) is retained in Git alongside [verification/cleanup/CI metadata](m2-clean-replay-38680812079/verification.json), so evidence survives artifact expiration.
- GitHub artifact `m2-clean-replay-38680812079-1`: **2,783 bytes compressed**, archive digest `sha256:86b706521d369d356ad29a27130c36e697775439d9b0dcc712278a1a8b433006`, expiration **2026-10-22 04:19:36 UTC**. It contains only the non-secret report.
- The replay report records **`test_database_and_runtime_role_discarded=true`** after successful teardown. Scratch cleanup step completed successfully. Actions logs explicitly show **`docker rm --force`** and **`docker network rm`**, both successful, at **04:19:39 UTC**. Service-container/network removal is observed; hosted VM/anonymous-volume disposal follows GitHub's standard ephemeral-runner lifecycle, not a separately inspected VM API.
- No production database connection, Supabase mutation, hosting configuration change or manual provider deployment operation was used. The workflow remains manual-only for future regression checks on the existing branch.

## Future result retention

The workflow writes its code revision/run URL, lockfile hash, actual server/runtime versions, fixture/model/artifact/table hashes, row counts, API case outputs, timings and permission/rollback checks into a small `replay.json` report. It also writes a GitHub job summary. Only that JSON is uploaded as `m2-clean-replay-<run-id>-<attempt>`, retained for **7 days**. Credentials, raw/projection snapshots, embeddings, model files, environments and database dumps are never uploaded.

For future runs, download the report and retain its non-secret results/run URL/tested SHA in Git before the artifact expires. A running/skipped/failed report is never a pass.

| Execution result | Current value |
| --- | --- |
| Approved workflow run | **38680812079 — success, attempt 1** |
| Actions URL / tested commit | [Run](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680812079) / `3a62d1ef2f07eb5d2b7f080ab5edb35f4ea2db70` |
| Clean pass 1 / pass 2 | Passed / passed |
| Database/API/permissions reproducibility | Passed |
| Cleanup observed in Actions | DB/role teardown, scratch cleanup, container/network removal passed |
| M2 clean-database gate | **Closed — M2 complete** |

## Isolation, cost and cleanup

No repository secrets, production URLs, hosting APIs, Supabase tools or provider credentials are used. DB endpoints/passwords are fixed disposable CI-only values pointing at `127.0.0.1` and the service's dynamically assigned port. The replay script refuses non-GitHub-hosted contexts, other repositories and unexpected scratch roots; it checks PostgreSQL major version and the service's database inventory before any destructive teardown. Existing production scripts/migrations are exercised without changing their serving behavior.

The existing public repository uses a standard `ubuntu-24.04` runner, a 20-minute timeout, sequential work, no persisted dependency/model caches and read-only repository permissions. Standard public-repository runner usage is [free according to GitHub](https://docs.github.com/en/actions/concepts/billing-and-usage); only one small report is retained briefly. No paid runner/plan, scheduled keep-alive, external hosted test database or paid inference is introduced.

An `always()` step removes the dedicated runner-temp directory after evidence upload. The script also drops its test database/role in `finally`; even if a crash/timeout prevents that step, GitHub removes the service container/network and discards the hosted VM/volumes. No test database is hosted after the job.

M3 remains unstarted and unauthorized. See [M2 operations](../operations-m2.md#clean-database-replay-in-github-actions) for the approval-gated run procedure.
