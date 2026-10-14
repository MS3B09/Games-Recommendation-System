# M1 deployment — GitHub publication and owner-managed hosting

The owner initially chose self-publication, then explicitly requested publication to [the GitHub repository](https://github.com/MS3B09/Games-Recommendation-System) on 2026-10-14. That request authorizes committing/pushing the verified foundation. Hosting configuration remains owner-managed; GitHub publication alone does not prove successful deployment. M1's live walking-skeleton gate remains open until the URLs below are verified. No M2 implementation has started.

## 1. Publish intended files

Publish the verified backend/frontend projects, lockfiles, generated API schema/types, workflows, `netlify.toml`, `render.yaml`, product/design and setup/progress documentation. Include `backend/alembic` and `backend/migrations` in the checkout. Keep environment secrets, node_modules, model caches/raw data/job reports and screenshots out of Git; `.gitignore` covers them. Existing personal OpenCode/MCP configuration was not changed for deployment.

CI workflows pin action revisions, uv and Node and use no live service secrets. Both passed on GitHub for foundation commit `7c6767c`: [Backend checks](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38497801838) and [Frontend checks](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38497801731). The source is published on `main`; configure hosting next.

## 2. Render API

In **Render Dashboard**, create/configure a **Python Web Service on Free** connected to the published repository. The root `render.yaml` describes one web service only; it creates no Render database, worker, cron or paid disk. Use it as a Blueprint or enter these settings manually for your existing service:

| Setting | Value |
| --- | --- |
| Root directory | `backend` |
| Python | `3.13.12` (`PYTHON_VERSION`) |
| Build | `pip install uv==0.11.16 && uv sync --locked --no-dev` |
| Start | `.venv/bin/uvicorn game_discovery.api.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health path | `/health/live` |
| Plan | **Free**, explicitly selected |
| Auto-deploy | Off initially; trigger the verified deployment manually |

Set in **Render → service → Environment**:

- `DATABASE_URL`: the existing restricted `game_discovery_runtime.<PROJECT_REF>` Session-pooler URI with its URL-encoded password, copied locally from your setup. **Never paste it in chat.**
- `ALLOWED_ORIGINS`: the exact public Netlify origin, e.g. `https://YOUR-SITE.netlify.app` (no path/trailing slash). Multiple explicit origins are comma-separated. No wildcard.
- `PYTHON_VERSION=3.13.12` when configuring manually.

Do not configure `MIGRATION_DATABASE_URL` on the serving service. Run reviewed migrations from your developer environment before a release. No Groq key, GPU, Torch, collection extras, encoder download or catalog activation is required for M1. Render's platform health must use **liveness**, since catalog readiness is intentionally 503 before M2 publication.

Record the public `https://YOUR-API.onrender.com` origin. Expected current responses:

- `/health/live`: 200 `alive`.
- `/api/v1/catalog/status`: 200 `uninitialized`, zero games.
- `/health/ready`: 503 `catalog_not_initialized`.
- `/openapi.json` and `/docs`: API contract/documentation.

Free cold starts are expected; do not add uptime polling to defeat sleep. Account allowances and hosted resource/latency behavior must be checked in the actual account; local measurements are not hosted guarantees. [Render Free limits](https://render.com/docs/free), [Blueprint specification](https://render.com/docs/blueprint-spec).

## 3. Netlify frontend

In the connected **Netlify project**, root `netlify.toml` supplies:

| Setting | Value |
| --- | --- |
| Base directory | `frontend` |
| Node | `24.13.0` |
| Install | lockfile-based npm install (`npm ci` in local/CI setup) |
| Build | `npm run lint && npm run check:api && npm run build` |
| Publish | `dist` relative to base |
| SPA fallback | `/*` → `/index.html`, 200; real assets retain precedence |

Set **Netlify → Project configuration → Environment variables**, build scope:

```dotenv
VITE_API_BASE_URL=https://YOUR-API.onrender.com
```

This is a **public** URL, not a secret. No database URI, migration password, service-role key or inference key belongs in Netlify/frontend variables. Rebuild after changing the API origin: Vite embeds it at build time. Missing production API configuration produces an explicit error page state; it never silently falls back to localhost. Set `ALLOWED_ORIGINS` on Render to the resulting exact Netlify origin.

Use the applicable **Free** plan and verify team/project allowances. Current credit-based Free documentation records a 300-credit hard limit; account-specific/legacy settings remain to inspect. Avoid unnecessary production/preview rebuilds. [Netlify configuration](https://docs.netlify.com/build/configure-builds/file-based-configuration/).

## 4. Verify the live M1 gate

Send **only the public Netlify and Render URLs** after publication/configuration. The agent can then check:

1. Public health and catalog responses match the current API contract.
2. Fresh browser visits to `/` and **direct `/system`** load static assets correctly.
3. The actual Netlify page calls the actual Render API with successful CORS.
4. Unpublished catalog remains distinct from failure; manual retry is usable.
5. Public client artifacts contain the API origin only, with no secret configuration.
6. Confirm CI results and actual Free-account limits/settings, recording any remaining access limitations.

Only then mark the relevant hosted acceptance gate passed. Report M1 completion and wait for explicit permission before M2. A blank initialized catalog is correct at this milestone; do not import synthetic or actual recommendation data just to make readiness green.

## Troubleshooting

- **Catalog status 200/uninitialized:** normal M1 state, not a database outage.
- **503 database role misconfigured:** runtime URL still uses a privileged role; configure the restricted login on Render.
- **API wakes slowly:** let the bounded 75-second check finish, then retry manually. No background polling.
- **CORS/network error:** compare the exact Netlify origin with Render's `ALLOWED_ORIGINS`, check both services' dashboards, and verify HTTPS API URL/build variables.
- **Nested route 404 or HTML instead of JS:** confirm the published `dist` assets and root Netlify fallback are deployed together.
- **Netlify paused:** inspect the actual Free-plan allowance; do not enable paid recharge as a workaround.
