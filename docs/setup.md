# Full-stack setup (M1 foundation + M2 discovery)

M1 and M2 are complete. M2 has an active 40-game real catalog, search, favorite-based discovery, hard filters and evidence-linked game cards; hosted verification is owner-confirmed. See [M2 operations](operations-m2.md) for commands and the [passed GitHub Actions replay](reports/m2-clean-replay.md) for clean-database evidence. No local PostgreSQL/pgvector installation was needed for this acceptance check. M3 requires explicit approval.

## Prerequisites

- Node **24.13.0**, npm **11.6.2** (Node 24 compatible).
- Python **3.13.12**, uv **0.11.16**.
- Existing Supabase Free PostgreSQL with the initial M1 schema; runtime and developer connections are separate. [Role setup](backend-foundation.md).

Use a normal fast local filesystem for dependency installation. This user's E: is a removable FAT32 volume; repeated dependency installs timed out there. Python environment, frontend execution copy and browser cache were verified on C:. No repair/reformat was attempted.

## Backend

From repository root:

```powershell
# Optional override used on this machine; omit on a normal local working copy.
$env:UV_PROJECT_ENVIRONMENT = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m2-venv'
uv sync --project backend --locked --extra dev --extra benchmark
uv run --project backend --locked --extra dev --extra benchmark python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Configure ignored `backend/.env` from its example: `DATABASE_URL` uses the restricted runtime role; `MIGRATION_DATABASE_URL` is developer-only; `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`. Never place DB credentials in frontend variables. No Groq key is needed for M1. Serving dependencies do not include Torch or model downloads.

## Frontend

Run these commands with `frontend/` as the terminal working directory:

```powershell
npm ci --no-audit --no-fund
npm run dev
```

Open **http://127.0.0.1:5173/system**. Development defaults to the local API. For another origin, configure `VITE_API_BASE_URL` in ignored `frontend/.env.local` (example provided). Only this public origin belongs in browser configuration.

`/` renders discovery when a catalog is active, `/system` retains the status page, and `/games/:id` supports details/direct reload. Unknown routes provide a home link. The UI requests metadata once, permits manual retry, aborts stale requests, times out at 75 seconds, and never polls to keep free services awake. A reachable unpublished catalog is distinct from an outage; unknown freshness stays unknown.

### Verified C: frontend execution copy

On this machine, the source remains `E:\Games-Recommendation-System\frontend`; the verified execution copy is `C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m1\frontend`. It contains the same application/config/test files and adjacent non-secret `backend/openapi.json`, without backend credentials or raw data. Generated lockfile and API types were copied back to the source. Run frontend commands from that copy while E: is slow; synchronize changed source/config/test files before rebuilding. Prefer a normal checkout on a fast local disk for ongoing development. Python uses the original checkout and reads its ignored backend environment.

## Checks

From repository root:

```powershell
uv run --project backend --locked --extra dev --extra benchmark ruff check backend
uv run --project backend --locked --extra dev --extra benchmark mypy --config-file backend/pyproject.toml backend/src/game_discovery/api backend/src/game_discovery/core backend/src/game_discovery/db
uv run --project backend --locked --extra dev --extra benchmark python -m unittest discover -s backend/tests -v
uv run --project backend --locked --extra dev --extra benchmark python -m game_discovery.api.export_schema --check
```

On the slow E: machine, use a C: mypy cache. Ruff covers all backend code; strict types cover serving/config/migration plus M2 catalog boundaries (13 files), not developer jobs. To include all configured modules, run `uv run --no-sync mypy` from `backend/` after installing the dev environment; CI explicitly includes the catalog modules too.

From `frontend/`:

```powershell
npm run lint
npm run check:api
# Test/local-preview origin; use the real HTTPS backend origin for hosted production.
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run build
npx playwright install chromium
npm test
```

This machine sets `PLAYWRIGHT_BROWSERS_PATH=C:\Users\User\AppData\Local\Temp\opencode\game-discovery-browsers`. CI installs Chromium with Linux dependencies. Eleven browser checks use mocked responses and no database secrets: seven foundation checks plus four discovery/evidence/constraint/stale-response/detail checks. [Real M2 smoke](operations-m2.md#verification) separately exercises the configured database through an actual browser.

For the **real** browser → API → PostgreSQL check, first stop local servers on ports 8000/4173, ensure backend setup is installed and frontend build targets the local API:

```powershell
$env:API_PYTHON = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m2-venv\Scripts\python.exe'
# Optional capture directory; default is ../.impeccable/review.
$env:M1_CAPTURE_DIR = 'E:\Games-Recommendation-System\.impeccable\review'
npm run smoke:stack
```

The script owns/terminates its server process trees and captures desktop/mobile after loading fonts. It temporarily sets its backend's CORS origin to the preview origin. It does not edit `.env`, publish a catalog, download a model or make LLM calls. Actual result: **200, uninitialized, 0 games, 0 browser errors**. Automated responsive checks do not replace real-phone testing.

## API-contract regeneration

After changing response models, from root:

```powershell
uv run --project backend --locked --extra dev --extra benchmark python -m game_discovery.api.export_schema
```

Then from frontend: `npm run generate:api`. Track `backend/openapi.json` and `frontend/src/api/schema.d.ts`; CI checks drift. Schema export never connects to the database or serializes configuration/secrets. Frontend validates responses at the network boundary; generated types alone do not validate JSON.

## Explicit migrations

From root:

```powershell
uv run --project backend --locked python -m game_discovery.db.migrate current
# Fresh database or explicit new release only; never an API startup operation.
uv run --project backend --locked python -m game_discovery.db.migrate upgrade
# Render migration SQL for review without connecting.
uv run --project backend --locked python -m game_discovery.db.migrate sql
```

These commands use **only `MIGRATION_DATABASE_URL`**, with NullPool. API serving uses a two-connection pool with no overflow, one-second pool wait, three-second connection and two-second statement bounds; request admission is separately capped at two probes. Prepared statements are disabled for pooler compatibility. Connections roll back read-only request transactions and are disposed on application shutdown.

The existing Supabase schema was already applied through MCP; a guarded migration adopted Alembic revision `0001` after schema/RLS/grant inspection. `discovery_migrations.alembic_version` is private, RLS-protected and inaccessible to runtime/browser roles. Do **not** run the fresh initial SQL over the existing schema or blindly stamp an unrelated database. The second SQL file records this one-time adoption, not a second Alembic revision. Future revisions must be reviewed and applied explicitly. Destructive downgrade of the initial schema is refused; use verified backups/manual recovery.

### Native, database-only alternative

Install PostgreSQL 17 and [pgvector](https://github.com/pgvector/pgvector#installation) locally; no full Supabase stack is required. Using a privileged local SQL client, create a dedicated `game_discovery` database. Let the catalog migration install `vector` in `extensions`, or preinstall using `create schema if not exists extensions; create extension vector with schema extensions;`. Set developer `MIGRATION_DATABASE_URL=postgresql://postgres:REPLACE_LOCALLY@localhost:5432/game_discovery`, then run the explicit `upgrade` command. The initial migration conditionally revokes Supabase browser roles only if those roles exist, so it is portable to native PostgreSQL. Configure the new runtime password in the local SQL client and set `DATABASE_URL=postgresql://game_discovery_runtime:REPLACE_LOCALLY@localhost:5432/game_discovery` (no pooler project suffix locally).

Native installation/fresh-database execution was not performed on this local machine; no psql/Docker was needed. The configured Supabase path, explicit M2 migration/import and real application connection were tested. Complete fresh native replay subsequently passed twice in the approved PostgreSQL 17.10/pgvector 0.8.2 Actions service; [retained results](reports/m2-clean-replay.md).

## Deployment and next gate

[Deployment guide](deployment.md). **M0–M2 are complete.** Hosted M2 verification is owner-confirmed and the clean-database Actions replay/cleanup passed. [M1 hosted evidence](reports/m1-hosted-verification.md) is historical; `npm run verify:hosted` assumes that old unpublished catalog and is not the M2 verifier. Use [M2 operations](operations-m2.md) for checks and the retained manual replay workflow. Stop; do not start M3 without explicit approval.
