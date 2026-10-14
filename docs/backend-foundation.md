# M1 backend foundation

Status: **local foundation verified; hosted M1 gate pending owner deployment**. Frontend, generated contracts, SQLAlchemy/Alembic integration and lint/type tooling are implemented. Full catalog tables/import/discovery are M2 work. The M0 resource spike is separate from this application. [Complete stack setup](setup.md) · [Owner deployment steps](deployment.md).

## Configure the runtime database role

The `m1_catalog_metadata_and_runtime_role` Supabase migration created `game_discovery_runtime`, with a five-connection limit and no superuser, database/role creation or RLS-bypass attributes. Its only table grant is SELECT on catalog-version metadata. It cannot publish versions, read developer job logs or create schema objects. Grants were verified through `has_table_privilege`/`has_schema_privilege`.

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

The configured runtime login now succeeds and has no elevated attributes; the developer migration login remains separate and privileged. Real checks return `/health/live` 200, catalog-status 200 with `state=uninitialized`, and readiness 503 with `catalog_not_initialized`. No active catalog is published yet. Owner-level runtime URLs remain deliberately rejected with `database_role_misconfigured`; no credentials or driver exception text appear in public responses.

`SET ROLE` impersonation was denied. Membership inspection confirmed that the creating `postgres` role has ADMIN option but not SET or INHERIT: it can administer the runtime password without inheriting/impersonating this role. No impersonation grants were added for a test. Permission introspection and the subsequent direct runtime login/catalog-metadata query passed.

## Run locally

From the repository root, using the C: environment workaround if E: installation stalls:

```powershell
$env:UV_PROJECT_ENVIRONMENT = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m0-venv'
uv sync --project backend --locked --extra dev --extra benchmark --link-mode copy
uv run --project backend --locked --extra dev --extra benchmark python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

The API reads ignored `backend/.env` in this editable local checkout. Explicit OS environment settings override file values. `GAME_DISCOVERY_ENV_FILE` can specify a different local file. Hosted deployments must set server secrets in the provider environment settings. Browser configuration will contain only the public API URL.

## Current API

| Route | Behavior |
| --- | --- |
| `GET /health/live` | Process-only 200, without database or LLM calls |
| `GET /health/ready` | 503 for unconfigured/unavailable/privileged runtime access or missing active catalog; 200 only with an active catalog version |
| `GET /api/v1/catalog/status` | Typed version/count/US/USD/source-freshness metadata; a healthy database with no active catalog returns `state=uninitialized`; DB/configuration failures return structured 503 |
| `GET /docs`, `GET /openapi.json` | FastAPI documentation and client-contract source |

Errors contain `{code,message,request_id,retryable}`; `X-Request-ID` matches error request IDs. Missing source freshness remains null. No discovery rankings, semantic-query matching, or LLM capability is claimed yet. CORS allows explicit origins, not wildcard credentials. At most two concurrent database probes run; connection and statement timeouts are bounded.

The metadata schema uses one active-version unique index and checks US/USD, 384 dimensions and positive game counts before an active row can exist. Publication remains developer-managed and is not exposed by an API endpoint. Schema changes are explicit migrations, never startup side effects.

## Checks and remaining gates

```powershell
uv run --project backend --locked --extra benchmark --extra api-spike python -m unittest discover -s backend/tests -v
uv run --project backend --locked python -m game_discovery.jobs environment-check --env-file backend/.env --project-url https://mmdmxjiawlbridvvhtrt.supabase.co --connect
```

Current local behavior suite: **28 tests passed**, Ruff passes across backend code, strict mypy passes on 10 foundation files, generated OpenAPI drift check passes. Actual pooled runtime checks and the browser → API → PostgreSQL smoke confirmed process health 200, catalog-status 200/uninitialized and readiness `catalog_not_initialized`. Mocked checks distinguish empty catalogs from outages, verify CORS, malformed configuration, structured errors/request IDs and dependency-independent liveness.

`.github/workflows/backend-checks.yml` uses pinned action commits and uv, bounded runtime, read-only repository permissions and lightweight extras. It needs no service secrets, browser installs, live scraping or model downloads. It has not run on GitHub because changes have not been committed/pushed.

Alembic now tracks revision `0001` in private `discovery_migrations.alembic_version`; the already-applied metadata baseline was adopted through a guarded migration. Offline SQL is portable to native PostgreSQL without Supabase's browser roles. Native fresh-database execution remains untested on this machine; no psql/Docker was available. API startup never runs migrations. Runtime connections use SQLAlchemy's bounded two-connection pool with no overflow; developer migrations use NullPool and only the migration URL.

Next: the owner authorized GitHub publication on 2026-10-14; hosting configuration remains owner-managed. Verify public Netlify/Render page/API/CORS/rewrite, remote CI and applicable Free-plan settings after publication and receiving public URLs. **Do not mark the hosted gate complete or start M2; after full M1 completion, stop for permission.**
