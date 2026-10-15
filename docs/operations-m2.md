# M2 catalog and discovery operations

Run Python commands from the repository root. Keep the original legacy application/data intact. This pipeline never loads pickle files and never constructs an N-by-N matrix.

## Configuration

Use the existing ignored `backend/.env`:

- `DATABASE_URL`: restricted `game_discovery_runtime` connection, used by the API.
- `MIGRATION_DATABASE_URL`: privileged developer connection, used only by explicit migrations/imports.
- `ALLOWED_ORIGINS`: exact local frontend origins; the hosted value stays `https://steam-discovery.netlify.app`.

These credentials were already configured and worked during M2. No new secret or Groq key is needed. Configure secrets locally or in FastAPI Cloud environment settings, never in chat or Git. Netlify needs only public `VITE_API_BASE_URL=https://steam-discovery-api.fastapicloud.dev`.

## Install and migrate

```powershell
uv sync --project backend --locked --extra benchmark --extra dev --extra api-spike
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.db.migrate upgrade --env-file backend/.env
```

Alembic head is `0002`: versioned games, explicit platform states, normalized genre/tag/mode terms, US/USD price observations and 384-dimensional embeddings. Provenance/evidence is retained in each validated immutable game document rather than split across extra tables for this bounded M2 sample. Foreign keys, RLS and active-version policies protect serving access. All request transactions are read-only; migrations never run at API startup.

For a **new native database**, install PostgreSQL/pgvector and let the migration create `extensions` and install `vector` there. If installing manually, use `create schema if not exists extensions; create extension vector with schema extensions;`. Do not preinstall pgvector in `public`: this pipeline deliberately qualifies the `extensions` type/operator. Native clean-database replay remains unverified on this machine (no local PostgreSQL/Docker tooling).

## Collect, normalize, embed, stage and activate

```powershell
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.jobs collect --ids-file data/fixtures/m2-app-ids.json --run-dir data/raw/m2-catalog --resume
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.jobs normalize --run-dir data/raw/m2-catalog
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.jobs embed --run-dir data/raw/m2-catalog --cache-dir data/artifacts/model-cache --batch-size 8 --resume
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.jobs import --run-dir data/raw/m2-catalog --env-file backend/.env
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.jobs activate --run-dir data/raw/m2-catalog --env-file backend/.env
```

The fixed 40-ID list is a representative starting catalog, not a quality benchmark or an expansion target. Collection uses the already-selected structured Steam appdetails source, US region and English; it does not scrape HTML. Scrapling remains the only permitted scraping framework. Requests are sequential, 20-second bounded, at most 2 MiB per response and separated by two seconds. No retries or access-gate bypass. A run accepts at most 100 IDs.

- **Collect:** snapshot bytes, source URLs, real UTC collection times and SHA256 hashes; checkpoint after each request. `--resume` skips verified observations, retries failed ones and refuses a different ID set. Use a **new run directory** to refresh successful observations. A partial run exits nonzero and reports failure types without credentials.
- **Normalize:** verify raw hashes and app identity; quarantine non-games, unreleased/unknown/adult-only classifications, missing descriptions and failed observations. Preserve false versus unknown platform states. Prices require USD from the requested US source; explicit free-to-play can establish a zero-price observation. Zero-price promotions are not free-to-play. Unknown review/tag data is not fabricated. `normalized.json` contains counts and quarantine reasons.
- **Embed:** pinned MiniLM revision, float ONNX CPU, attention-mask mean pooling, L2 normalization, 384 dimensions, 256 tokens, one inference thread, batches 1–16. M0 established parity with Sentence Transformers; the same float representation is used offline here to avoid requiring PyTorch for this small pipeline. Semantic text is title → genres/tags/modes → short description; prices/review counts are excluded. Representation hashes guard resume checkpoints; matching content is reused. No weights download during API requests. The first developer job downloads public pinned files once; subsequent jobs reuse the local cache.
- **Import:** validate artifact hashes, identities, vector norms/content hashes; stage inside one transaction. A repeated immutable version is verified and reused, not duplicated. Database documents, model settings, embeddings, platform/term rows and prices must match the artifact. Inactive rows are hidden from the serving role. Imports on this small catalog are intentionally sequential; larger changed-only refresh operations belong to M5.
- **Activate:** repeat complete artifact/database checks, serialize publication with an advisory lock, atomically switch the one active version. Retain the previous version locally in `activation-report.json`; existing snapshots remain available for a later explicitly managed restore. A failure rolls the transaction back. The 350 MiB database budget is checked before commit.

Artifacts/reports live in the ignored run directory: `collection.json`, source snapshots, `games.json`, `normalized.json`, `embedding-settings.json`, `embeddings.json`, `artifact.json`, `import-report.json`, `activation-report.json`. Keep these locally for exact replay. The tracked [manifest](reports/m2-artifact-manifest.json) records the verified generation without redistributing raw responses or weights. Recollecting Steam later legitimately changes prices/timestamps and therefore the artifact version; it does not reproduce a historical price snapshot.

## API and UI

Start the backend as in [setup](setup.md), then `npm run dev` from `frontend/`. `/` is discovery when a catalog is active; `/system` retains the connection page; `/games/:id` supports direct details/reload. Browser selections are in memory only until M3.

New routes:

| Route | Behavior |
| --- | --- |
| `GET /api/v1/games?q=Hades&limit=12&offset=0` | Bounded title/full-text search; page size ≤50, offset ≤6000 |
| `GET /api/v1/games/{app_id}` | Typed metadata/evidence or 404 |
| `POST /api/v1/games/resolve` | At most 200 IDs; explicitly report unknown IDs |
| `GET /api/v1/facets` | Actual normalized genre/tag/mode/platform choices |
| `POST /api/v1/discover` | At most 50 favorites, bounded filters, at most 20 results; no LLM |

Example discovery body:

```json
{
  "favorite_ids": [1145360],
  "filters": {
    "max_price_cents": 2000,
    "price_operator": "lt",
    "platforms": ["windows"],
    "platform_match": "any",
    "required_modes": ["single-player"],
    "excluded_ids": []
  },
  "limit": 10
}
```

UI maximum is inclusive; API `lt` can express “under.” Unknown prices/platforms fail required constraints. Free-only requires explicit free-to-play evidence. Modes are all required. Preferred genre/tag terms boost; unwanted terms exclude recorded matches, without claiming unrecorded tags are absent. Seeds/excluded IDs never appear. No filters are silently relaxed. Unknown favorites produce 422. No-seed discovery uses preferred-term boosts then stable app-ID order, not a personalized-quality claim.

Ranking `seed-v1` uses cosine similarity to the normalized centroid of seed embeddings plus a bounded 0.15 preferred-term boost (fraction of preferred terms present), then app ID. Exact PostgreSQL vector retrieval applies hard filters **before** the limit and revalidates returned documents in Python. Template reasons cite real catalog fields; no numerical match confidence or inferred “less repetition” claim. Natural-language query interpretation and semantic query encoding remain M4.

## Verification

```powershell
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m unittest discover -s backend/tests -v
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike ruff check backend
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.jobs verify-catalog --output data/reports/m2-api-smoke.json
uv run --project backend --locked --extra benchmark --extra dev --extra api-spike python -m game_discovery.jobs verify-import --run-dir data/raw/m2-catalog --env-file backend/.env --output data/reports/m2-import-verification.json
```

`verify-catalog` explicitly uses the configured runtime connection; `verify-import` explicitly uses developer credentials and deliberately interrupts a real one-game subset import after its first game insert. That transaction rolls back; it checks the test version never persisted, incomplete embeddings cannot activate and the original active version is unchanged. Both commands are opt-in, not live-service CI requirements. Rerun normal import/embed to verify idempotence/checkpoint reuse.

From `frontend/`, after building with `VITE_API_BASE_URL=http://127.0.0.1:8000`:

```powershell
npm run lint
npm run check:api
npm run build
npm test
# Stop any existing servers on 8000/4173 first; set API_PYTHON to your installed backend Python.
npm run smoke:discovery
```

The real-stack smoke starts/stops only its own local API/preview processes, checks CORS-backed favorite search/discovery, constraints, evidence, direct-detail reload, desktop/mobile axe and overflow, and saves captures under `.impeccable/review/m2`. Local startup wait is bounded at 75 seconds for this slow filesystem. On this machine the frontend C: execution copy remains in use; set `API_PYTHON` to the new `game-discovery-m2-venv/Scripts/python.exe`. The earlier M0 environment lost its Python launcher and was not reused. Source remains on E:; no secrets/raw catalog are copied to the frontend cache.

M1's `verify:hosted` is historical and assumes an unpublished catalog; it is not the M2 acceptance verifier. M2 was subsequently published as `3453bfb`, passed both CI checks and is now hosted-verification owner-confirmed. The remaining replay preparation below makes no provider/database changes and requires separate approval before publication/execution.

## Clean-database replay in GitHub Actions

The owner has now confirmed M2 hosted verification. A local PostgreSQL installation is **not required** to close the remaining clean-database gate: `.github/workflows/m2-clean-replay.yml` prepares a native PostgreSQL 17/pgvector 0.8.2 service on a standard free GitHub-hosted runner. [Preparation/results record](reports/m2-clean-replay.md).

**Approval boundary:** the workflow and supporting files are currently local only. Do not commit, push or run it until the owner explicitly approves those actions. It is manual-only, so a later approved push does not automatically dispatch this replay. Keep the existing `main` branch; no new branch or production migration is needed.

After approval to publish **and** execute:

1. Commit/push the reviewed replay workflow, helper, source fixture, tests and docs to the existing repository/branch.
2. In GitHub → Actions → **M2 clean database replay**, choose **Run workflow** on `main`. Equivalent CLI (do not execute before approval):

   ```powershell
   gh workflow run m2-clean-replay.yml --repo MS3B09/Games-Recommendation-System --ref main
   ```

3. Wait for the entire job, including evidence retention/cleanup, to succeed. Inspect its summary and download the `m2-clean-replay-<run-id>-<attempt>` report within seven days. Preserve the concise result and run URL in the tracked [report](reports/m2-clean-replay.md), then update progress. Any failed/skipped/pending replay leaves the gate open.

The 40-game frozen source fixture avoids live Steam/network collection dependencies. Public pinned model files are downloaded once inside the disposable runner and used to compute embeddings independently twice. The helper runs the existing migrations, normalizer, embedding/import/activation and verification jobs, comparing manifests, database contents and recommendation results across two empty database builds. No precomputed vectors/database dump are used.

The fixture is a **field projection**, not a full original raw response. `original_source` retains the original HTTP SHA256 and collection time; materialized projection files carry their own SHA256. The replay's distinct provenance/version is expected. To regenerate the fixture deliberately from the retained verified local snapshots (no database access):

```powershell
uv run --project backend --no-sync python backend/scripts/export_replay_fixture.py --source-run data/raw/m2-catalog --output data/fixtures/m2-replay-sources.json
```

This exporter was used during preparation. Frozen public metadata fixtures are tracked; full raw HTTP snapshots, models and vectors remain ignored. No new credentials are required. Do not configure Supabase/Groq/Netlify/FastAPI Cloud secrets in this workflow. Its isolated test URLs are not accepted from user inputs or production `.env` files.
