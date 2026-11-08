# Local setup

This guide is for the current React/FastAPI application. The [live demo](https://steam-discovery.netlify.app/) is the quickest way to try it without configuring services.

## Prerequisites

- Python 3.13 (the project records 3.13.12) and [uv](https://docs.astral.sh/uv/).
- Node.js 24 (the frontend requires 24.13.0 or newer within the 24.x series) and npm.
- A PostgreSQL database with pgvector, the project's migrations, and an **active catalog**. A separate restricted runtime role is required; an administrator connection is only for developer migrations and imports.
- A Groq API key only if you want to enable the assistant. Main discovery works without it.

**A clone is not a copy of production.** Database credentials, the full 2,000-game source snapshots, and generated vectors are not committed. An empty or unconfigured database cannot serve the catalog; dashboard analytics also need catalog metadata. Public app-ID lists and manifests are in [`data/fixtures/`](../data/fixtures/). See the [catalog workflow](catalog.md) for collection, normalization, embedding, import, and activation. Recollecting later can produce different records, timestamps, and artifact versions.

For a new database, review the [catalog workflow](catalog.md) before applying migrations or importing data. Migrations create the restricted role but do not populate a catalog. Only run migrations and activation against a database you own and intend to change; they never run automatically at API startup. The historical 40-game clean replay is separate from the current 2,000-game release.

## Backend

From the repository root. Only copy the example if you do not already have a `backend/.env` you want to keep:

```bash
uv sync --project backend --locked --extra dev --extra benchmark --extra api-spike
cp backend/.env.example backend/.env
```

On Windows PowerShell, use `Copy-Item backend/.env.example backend/.env` instead of `cp` if preferred. Edit the ignored `backend/.env` locally:

| Setting | Purpose |
| --- | --- |
| `DATABASE_URL` | Restricted runtime connection to your prepared catalog database. |
| `MIGRATION_DATABASE_URL` | Privileged developer connection for explicit migrations/imports only; not needed to serve an already-prepared database. |
| `ALLOWED_ORIGINS` | Exact local frontend origins; the example includes ports on `localhost` and `127.0.0.1` at 5173. |
| `AI_ENABLED`, `GROQ_API_KEY`, `GROQ_MODEL` | Optional assistant configuration. Leave `AI_ENABLED=false` without a key. |
| `QUERY_TOKENIZER_PATH`, `QUERY_MODEL_PATH`, `QUERY_ARTIFACT_PATH` | Optional semantic-runtime overrides; the example leaves them at the bundled defaults. |

Keep all credentials server-side and out of Git. The frontend's `VITE_API_BASE_URL` is public and must never contain secrets.

### Preparing an empty database

If you are setting up a new database, first set `MIGRATION_DATABASE_URL` to that intended database and review its existing state. Then, from the repository root, apply the migrations explicitly:

```bash
uv run --project backend --locked --extra dev --extra benchmark --extra api-spike python -m game_discovery.db.migrate current
uv run --project backend --locked --extra dev --extra benchmark --extra api-spike python -m game_discovery.db.migrate upgrade
```

Use your database administration tools to set a password for the newly created `game_discovery_runtime` role, then set `DATABASE_URL` to that restricted role's connection. Supabase's session pooler uses a username of the form `game_discovery_runtime.<PROJECT_REF>`; URL-encode special characters in passwords. Collect, normalize, embed, import, and activate a catalog using the [catalog workflow](catalog.md). These operations write to the database; inspect the target and artifacts before running them. The dashboard needs the corresponding metadata and analytics, and a different catalog requires a matching semantic artifact.

The semantic runtime uses pinned, hash-verified MiniLM assets. Packaging can download them; if the local assets are missing, run the following from the repository root (network access required):

```bash
uv run --project backend --no-sync python backend/build_semantic.py
```

For a newly generated catalog, point the query runtime at a matching artifact rather than assuming the bundled production manifest matches it. Without a compatible encoder, seed/filter discovery remains available, but semantic query matching falls back. [Catalog workflow and compatibility notes](catalog.md)

Start the API:

```bash
uv run --project backend --locked --extra dev --extra benchmark --extra api-spike python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Check **http://127.0.0.1:8000/health/ready**, **http://127.0.0.1:8000/api/v1/catalog/status**, and **http://127.0.0.1:8000/docs**. Readiness requires a usable active catalog; an unconfigured or empty database is not a successful setup.

## Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. Development defaults to `http://127.0.0.1:8000`. To use a different public API origin, copy `frontend/.env.example` to `frontend/.env.local` and set `VITE_API_BASE_URL`; also allow the frontend's exact origin in the backend's `ALLOWED_ORIGINS`. The hosted API is configured for the hosted site, so a local frontend should not assume it can use that API cross-origin.

## Checks

From the repository root:

```bash
uv run --project backend --locked --extra dev --extra benchmark --extra api-spike python -m unittest discover -s backend/tests -v
uv run --project backend --locked --extra dev --extra benchmark --extra api-spike ruff check backend
uv run --project backend --locked --extra dev --extra benchmark --extra api-spike python -m game_discovery.api.export_schema --check
```

From `frontend/` (set `VITE_API_BASE_URL` in `.env.local` before the production build):

```bash
npm run lint
npm run check:api
npm run build
npx playwright install chromium
npm test
```

Frontend tests start their own preview on port 4173, so that port must be free. The standard suites use fixtures or scripted providers; passing them does not establish live AI response quality. See [CI workflows](../.github/workflows/) for the exact release checks and [documentation](README.md) for architecture and historical evidence.
