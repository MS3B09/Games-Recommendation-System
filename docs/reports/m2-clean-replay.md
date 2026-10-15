# M2 clean-database replay verification

Status: **owner authorized commit/push/manual execution on 2026-10-15; execution/results pending. M2 remains in progress until the replay passes.**

The owner confirmed successful M2 hosted deployment verification on 2026-10-15. That is owner-reported acceptance; this task does not re-run or modify the live Netlify/FastAPI Cloud/Supabase deployment. The only remaining M2 acceptance gate is clean-database replay.

## Prepared verification

- Workflow: `.github/workflows/m2-clean-replay.yml`, **manual `workflow_dispatch` only**, on the existing repository/default `main` branch. No new branch, push trigger, pull-request trigger, schedule or deployment step.
- Service: PostgreSQL **17** with pgvector **0.8.2**, `pgvector/pgvector:0.8.2-pg17-bookworm` pinned to multiarch digest `sha256:feb68f4f15446397d8cac7f4fe48fe4586de83160d1fc48b46283312d1a33966`. Registry metadata was checked while preparing the workflow; no container was run locally.
- CPU-only runtime, locked Python dependencies, pinned MiniLM model revision and byte hashes; no PyTorch or hosted inference requirement.
- Frozen projections of the same **40 real source observations** used for M2. No Steam traffic or scraping during CI. The fixture contains only the public fields needed by normalization; the exporter verifies equivalence against the retained original response before writing each projection. Original source URLs, UTC collection timestamps and original HTTP hashes are retained. Temporary projection files receive their own verified hashes, explicitly distinguished from original HTTP-body hashes.
- Two independent source materializations, normalization and **fresh embedding computations**, each followed by migrations from empty native schemas, staging, validation and activation. The temporary database and runtime role are dropped between passes, so the second pass cannot reuse schema or imported rows. Only pinned model files are reused within the runner; embedding artifacts are rebuilt.

## Checks required before recording a pass

| Check | Expected evidence after the approved run |
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

These checks prepare the replay; they do **not** close the clean-database gate.

## Results to retain after approval

The workflow writes its code revision/run URL, lockfile hash, actual server/runtime versions, fixture/model/artifact/table hashes, row counts, API case outputs, timings and permission/rollback checks into a small `replay.json` report. It also writes a GitHub job summary. Only that JSON is uploaded as `m2-clean-replay-<run-id>-<attempt>`, retained for **7 days**. Credentials, raw/projection snapshots, embeddings, model files, environments and database dumps are never uploaded.

After a successful approved run, download the report, add its non-secret results to this tracked report (and retain the compact JSON under `docs/reports/` if desired), record the exact Actions URL and commit SHA, then check M2's remaining acceptance box. Do not mark M2 complete based only on preparation tests, an artifact with `status=running`, a skipped run or a failed job.

| Execution result | Current value |
| --- | --- |
| Approved workflow run | **Not run — approval pending** |
| Actions URL / tested commit | Pending |
| Clean pass 1 / pass 2 | Pending / pending |
| Database/API/permissions reproducibility | Pending |
| Cleanup observed in Actions | Pending |
| M2 clean-database gate | **Open** |

## Isolation, cost and cleanup

No repository secrets, production URLs, hosting APIs, Supabase tools or provider credentials are used. DB endpoints/passwords are fixed disposable CI-only values pointing at `127.0.0.1` and the service's dynamically assigned port. The replay script refuses non-GitHub-hosted contexts, other repositories and unexpected scratch roots; it checks PostgreSQL major version and the service's database inventory before any destructive teardown. Existing production scripts/migrations are exercised without changing their serving behavior.

The existing public repository uses a standard `ubuntu-24.04` runner, a 20-minute timeout, sequential work, no persisted dependency/model caches and read-only repository permissions. Standard public-repository runner usage is [free according to GitHub](https://docs.github.com/en/actions/concepts/billing-and-usage); only one small report is retained briefly. No paid runner/plan, scheduled keep-alive, external hosted test database or paid inference is introduced.

An `always()` step removes the dedicated runner-temp directory after evidence upload. The script also drops its test database/role in `finally`; even if a crash/timeout prevents that step, GitHub removes the service container/network and discards the hosted VM/volumes. No test database is hosted after the job.

M3 remains unstarted and unauthorized. See [M2 operations](../operations-m2.md#clean-database-replay-in-github-actions) for the approval-gated run procedure.
