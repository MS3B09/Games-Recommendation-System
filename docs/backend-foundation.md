# M1 backend foundation

Status: **M1 and M2 complete.** This document records the M1 foundation; [M2 operations](operations-m2.md) and [evidence](reports/m2-implementation.md) supersede its historical unpublished-catalog results. M2 hosted verification is owner-confirmed and the [approved clean-native replay](reports/m2-clean-replay.md) passed twice with CI/cleanup evidence. Stop before M3 until explicit approval. [Stack setup](setup.md) · [Deployment](deployment.md).

## Configure the runtime database role

The `m1_catalog_metadata_and_runtime_role` Supabase migration created `game_discovery_runtime`, with a five-connection limit and no superuser, database/role creation or RLS-bypass attributes. M1 granted only metadata SELECT; M2 adds SELECT on versioned catalog tables protected by active-version RLS. It cannot publish versions, read developer job logs or create schema objects.

**Owner setup was completed and verified on 2026-10-13.** To reproduce it on a new project, in **Supabase Dashboard → SQL Editor**, set a password locally:

```sql
alter role game_discovery_runtime password 'CHOOSE_A_PASSWORD_LOCALLY';
```

Do not paste the actual password in chat or add it to a migration file. Then update ignored `backend/.env`:

```dotenv
DATABASE_URL=postgresql://game_discovery_runtime.<PROJECT_REF>:<URL_ENCODED_RUNTIME_PASSWORD>@<SESSION_POOLER_HOST>:5432/postgres
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Use the **Session pooler** host from Dashboard → Connect. The pooler username is the runtime role plus the project suffix; that suffix is routing metadata, not a separate role. Keep `MIGRATION_DATABASE_URL` as the existing privileged developer connection. URL-encode the password; shared code also handles literal credential `@` characters in memory.

The configured runtime login succeeds and has no elevated attributes; the developer migration login remains separate and privileged. At M1 handoff status was uninitialized/readiness 503; after M2 catalog activation, real local status is ready/40 games and readiness 200. Owner-level runtime URLs remain deliberately rejected with `database_role_misconfigured`; no credentials or driver exception text appear in public responses.

`SET ROLE` impersonation was denied. Membership inspection confirmed that the creating `postgres` role has ADMIN option but not SET or INHERIT: it can administer the runtime password without inheriting/impersonating this role. No impersonation grants were added for a test. Permission introspection and the subsequent direct runtime login/catalog-metadata query passed.

## Run locally

From the repository root, using the C: environment workaround if E: installation stalls:

```powershell
$env:UV_PROJECT_ENVIRONMENT = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m0-venv'
uv sync --project backend --locked --extra dev --extra benchmark --link-mode copy
uv run --project backend --locked --extra dev --extra benchmark python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

The API reads ignored `backend/.env` in this editable local checkout. Explicit OS environment settings override file values. `GAME_DISCOVERY_ENV_FILE` can specify a different local file. Hosted deployments must set server secrets in the provider environment settings. Browser configuration will contain only the public API URL.

## M1 API baseline (M2 additions in its operations guide)

| Route | Behavior |
| --- | --- |
| `GET /health/live` | Process-only 200, without database or LLM calls |
| `GET /health/ready` | 503 for unconfigured/unavailable/privileged runtime access or missing active catalog; 200 only with an active catalog version |
| `GET /api/v1/catalog/status` | Typed version/count/US/USD/source-freshness metadata; a healthy database with no active catalog returns `state=uninitialized`; DB/configuration failures return structured 503 |
| `GET /docs`, `GET /openapi.json` | FastAPI documentation and client-contract source |

Errors contain `{code,message,request_id,retryable}`; `X-Request-ID` matches error request IDs. Missing source freshness remains null. M2 adds favorite-based discovery rankings and POST CORS; semantic-query matching/LLM capabilities remain disabled. CORS allows explicit origins, not wildcard credentials. At most two concurrent database operations run; connection and statement timeouts are bounded.

The metadata schema uses one active-version unique index and checks US/USD, 384 dimensions and positive game counts before an active row can exist. Publication remains developer-managed and is not exposed by an API endpoint. Schema changes are explicit migrations, never startup side effects.

## Checks and remaining gates

```powershell
uv run --project backend --locked --extra benchmark --extra api-spike python -m unittest discover -s backend/tests -v
uv run --project backend --locked python -m game_discovery.jobs environment-check --env-file backend/.env --project-url https://mmdmxjiawlbridvvhtrt.supabase.co --connect
```

M1's local behavior suite had 28 tests and 10 typed foundation files; M2 has **36 passing tests and 13 strictly typed serving modules**. Ruff covers all backend code. Historical M1 pooled checks reported uninitialized status; current M2 runtime/browser checks see the active catalog and useful discovery. [Detailed current evidence](reports/m2-implementation.md).

`.github/workflows/backend-checks.yml` uses pinned action commits and uv, bounded runtime, read-only repository permissions and lightweight extras. It needs no service secrets, browser installs, live scraping or model downloads. Backend and frontend workflows both passed on GitHub after publication of foundation commit `7c6767c`; [results](progress.md).

Alembic tracks revision `0002` after the explicitly applied M2 catalog migration; `0001` was the guarded M1 baseline adoption. Full initial migrations were verified twice on native PostgreSQL 17.10/pgvector 0.8.2 in GitHub Actions instead of installing local psql/Docker. M2 expects pgvector in `extensions`; see its operations guide. API startup never runs migrations. Runtime connections use SQLAlchemy's bounded two-connection pool with no overflow; developer migrations use NullPool and only the migration URL.

Hosted M1 verification passed with the then-uninitialized catalog. Owner confirmed Hobby/Free settings and one worker; no `WEB_CONCURRENCY` variable is required. **M1 is complete; M2 was subsequently authorized.** The shared database is now active, but new M2 routes/interface are not claimed hosted until publication and verification.
