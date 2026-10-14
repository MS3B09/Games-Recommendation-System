# Full-stack foundation setup (M1)

M1 implements a real service-status page, typed catalog metadata API, bounded PostgreSQL access and explicit migrations. No catalog is published yet. Search, imports, recommendations and game cards belong to M2 and have not started.

## Prerequisites

- Node **24.13.0**, npm **11.6.2** (Node 24 compatible).
- Python **3.13.12**, uv **0.11.16**.
- Existing Supabase Free PostgreSQL with the initial M1 schema; runtime and developer connections are separate. [Role setup](backend-foundation.md).

Use a normal fast local filesystem for dependency installation. This user's E: is a removable FAT32 volume; repeated dependency installs timed out there. Python environment, frontend execution copy and browser cache were verified on C:. No repair/reformat was attempted.

## Backend

From repository root:

```powershell
# Optional override used on this machine; omit on a normal local working copy.
$env:UV_PROJECT_ENVIRONMENT = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m0-venv'
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

Both `/` and `/system` render the foundation. Unknown routes provide a home link. The UI requests metadata once, permits manual retry, aborts on unmount, times out at 75 seconds, and never polls to keep free services awake. A reachable unpublished catalog is distinct from an outage; unknown freshness stays unknown.

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

On the slow E: machine, add `--cache-dir C:/Users/User/AppData/Local/Temp/opencode/game-discovery-mypy` to mypy. Ruff covers all backend code; strict types cover serving/config/migration boundaries (10 files), not the disposable M0 job implementations.

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

This machine sets `PLAYWRIGHT_BROWSERS_PATH=C:\Users\User\AppData\Local\Temp\opencode\game-discovery-browsers`. CI installs Chromium with Linux dependencies. Seven browser checks use mocked provider responses and no database secrets. They cover uninitialized versus unavailable state, malformed/HTML responses, retry, a 75-second timeout, nested navigation, mobile layout, keyboard and axe accessibility checks.

For the **real** browser → API → PostgreSQL check, first stop local servers on ports 8000/4173, ensure backend setup is installed and frontend build targets the local API:

```powershell
$env:API_PYTHON = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m0-venv\Scripts\python.exe'
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

Install PostgreSQL 17 and [pgvector](https://github.com/pgvector/pgvector#installation) locally; no full Supabase stack is required. Using a privileged local SQL client, create a dedicated `game_discovery` database. In it, install `create extension vector;` after pgvector is available. Set developer `MIGRATION_DATABASE_URL=postgresql://postgres:REPLACE_LOCALLY@localhost:5432/game_discovery`, then run the explicit `upgrade` command. The initial migration conditionally revokes Supabase browser roles only if those roles exist, so it is portable to native PostgreSQL. Configure the new runtime password in the local SQL client and set `DATABASE_URL=postgresql://game_discovery_runtime:REPLACE_LOCALLY@localhost:5432/game_discovery` (no pooler project suffix locally).

Native installation/fresh-database execution has **not** been performed on this machine; no psql/Docker was available. The configured Supabase path, real application connection and baseline revision were tested; offline SQL generation was checked, including PostgreSQL format placeholders. Extension setup/indexes for the full catalog are M2 work.

## Deployment and next gate

[Deployment guide](deployment.md). Local foundation verification is complete; hosted page/API/CORS/rewrite and actual Free-account allowances remain unverified until the owner publishes/configures the services and supplies public URLs. M1 is not marked fully complete while that gate is open. M2 requires explicit permission **after M1 completion**.
