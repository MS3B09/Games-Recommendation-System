# M1 deployment — Netlify + FastAPI Cloud Hobby

The owner selected **FastAPI Cloud instead of Render on 2026-10-14**. The frontend is published at **https://steam-discovery.netlify.app/**. Browser checks of `/` and direct `/system` return 200 and render without JavaScript errors; both currently say **“The API address has not been configured for this deployment.”** Backend deployment and cross-origin integration are still pending. M1 is not fully complete; M2 has not started.

The original foundation is published on GitHub; [backend](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38497801838) and [frontend](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38497801731) CI passed for `7c6767c`. The owner has explicitly authorized publishing the FastAPI Cloud migration and latest project changes. No hosting credentials are available to the agent; successful GitHub publication does not by itself verify the backend deployment.

## 1. FastAPI Cloud settings

Use the **Hobby ($0) team plan**. In [FastAPI Cloud Dashboard](https://dashboard.fastapicloud.com), create an app using **GitHub Repo**, connect `MS3B09/Games-Recommendation-System`, and set:

| Setting | Value |
| --- | --- |
| Root Directory when creating / Settings → Application Directory | `backend` |
| Python version | `3.13.12`, recorded in `backend/.python-version` |
| Dependencies | `backend/pyproject.toml` and `backend/uv.lock` |
| App entrypoint | `game_discovery.api.main:app`, recorded in `[tool.fastapi]` |
| Scaling → Replicas | **minimum 0 / maximum 1** |

`fastapi[standard]` is pinned to the existing FastAPI version, with its CLI dependencies locked. The installable `src` layout means the entrypoint **does not** start with `src.`. Keep the application directory at `backend` so the legacy root Streamlit `requirements.txt` is not chosen.

The GitHub integration deploys the default branch when connected and on subsequent pushes. Publish the new configuration before relying on that deployment. For an existing app, use **Settings → Source → Repository** to connect GitHub, and set **Application Directory** to `backend`. Confirm the correct commit/build logs in the dashboard. No Render build/start commands or `render.yaml` are needed; that superseded file has been removed locally.

### Environment variables

Under **App Details → Environment Variables**, add:

| Variable | Value | Secret? |
| --- | --- | --- |
| `DATABASE_URL` | Your restricted `game_discovery_runtime.<PROJECT_REF>` Supabase Session-pooler URI, using the rotated password | **Yes — enable Secret when creating it** |
| `ALLOWED_ORIGINS` | `https://steam-discovery.netlify.app` | No |

Use the actual URI from your local configuration; URL-encode special characters in the password. Do not paste secrets into chat. If a credential was shared, rotate it in Supabase first, then update both ignored `backend/.env` and the cloud secret. Credentials are never embedded in these docs or deployment files.

Choose **Save and Redeploy** to apply changes. Secret status must be chosen at creation; if a value was previously added as a regular variable, recreate it as a secret. Add the listed values individually rather than importing the entire local `.env`: **`MIGRATION_DATABASE_URL` stays developer-only**. No Groq key or Supabase service-role key is required. Do not connect a second database through an integration; the existing Supabase database remains the only one.

**Do not add `WEB_CONCURRENCY`:** the owner reported FastAPI Cloud rejecting that name with “Invalid environment variable name” and removed it. The reason for this platform validation is not verified; do not assume generic Uvicorn environment settings are configurable on this managed service or substitute an undocumented variable.

Keep maximum replicas at **1** using **Scaling**, and inspect the provider's startup logs/settings for the actual worker count. Each worker creates its own two-connection pool, so one replica alone does not prove a single worker. One worker remains the desired serving configuration, not a confirmed cloud setting. During rolling deploys old/new replicas can briefly overlap; the runtime role's five-connection limit remains in place. No database grants or role limits were changed for the hosting switch. The explicit local `--workers 1` commands remain valid for locally managed Uvicorn processes.

### Optional CLI deployment

Use a terminal whose working directory is **`backend/`**:

```powershell
# On this machine, avoid installing the venv on the slow removable E: drive.
$env:UV_PROJECT_ENVIRONMENT = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-cloud-venv'
uv sync --locked
uv run --locked fastapi login
uv run --locked fastapi deploy
```

Complete login in your own browser, select the **Hobby** team, and link the intended app. These commands upload/deploy; they were not executed by the agent. The local `.fastapicloud/` link state is ignored. `.fastapicloudignore` excludes secret files, environments, caches and unrelated frontend/legacy data from uploads. Review the CLI upload list before confirming. For GitHub deployment, keep the application directory `backend`; for a direct backend-folder upload, use the application root corresponding to that upload, rather than nesting `backend` twice.

Run reviewed schema migrations explicitly from the developer environment, never on cloud/API startup. If a health-check path is configurable, use **`/health/live`**. Do not use catalog readiness as platform liveness while the M1 catalog is unpublished.

## 2. Connect the Netlify frontend

After the backend deploys, copy its **public HTTPS app origin** from FastAPI Cloud, normally on `fastapicloud.dev`.

In **Netlify → steam-discovery → Project configuration → Environment variables**, build scope, set:

```dotenv
VITE_API_BASE_URL=https://YOUR-APP.fastapicloud.dev
```

Use the real app URL with **no `/docs` or `/api` suffix**. This is public configuration. No database password/URI, migration credential, provider key or service-role key belongs in Netlify/frontend variables.

**Trigger a new Netlify deploy** after saving the variable: Vite embeds it at build time. The existing deployed page has no configured API origin; changing a variable without rebuilding will not fix that artifact.

Root `netlify.toml` retains base `frontend`, Node 24.13.0, build `npm run lint && npm run check:api && npm run build`, publish `dist`, and a 200 SPA fallback to `/index.html`. The public `/system` route is already verified. Avoid unnecessary rebuilds on the Free plan.

## 3. Free-only validation

Official FastAPI Cloud [pricing](https://fastapicloud.com/pricing), checked 2026-10-14, lists Hobby at **$0 / no credit card**, 3 apps, 0.1 vCPU / 512 MB shared, scale-to-zero and one-day logs/metrics. The service is in **public beta**; usage billing/build-minute limits are still being developed. These are current allowances, not permanent free guarantees. Recheck account settings and billing notices before deployment; do not upgrade to Pro or paid resources.

The pricing page is internally inconsistent about maximum replicas (summary 3 versus table 2); the [autoscaling guide](https://fastapicloud.com/docs/advanced-features/autoscaling) documents Hobby min 0 / max selectable 1–3. Configure max **1**, which avoids relying on that discrepancy. Actual hosted memory, cold starts, worker count and account limits are not verified yet; local encoder measurements are not cloud guarantees.

Netlify's actual Free/legacy account limits still need owner verification. Current credit-based Free documentation lists a 300-credit hard stop. No paid recharge is authorized. Scale-to-zero/cold starts are accepted; do not add background uptime polling.

## 4. Close the hosted M1 gate

Send **only the public FastAPI Cloud URL** once it is deployed; the Netlify URL is already known. Verify:

1. `/health/live`: 200 `alive`.
2. `/api/v1/catalog/status`: 200 `uninitialized`, zero games.
3. `/health/ready`: 503 `catalog_not_initialized` — expected until M2 catalog publication.
4. `/docs` and `/openapi.json` render the actual API contract.
5. The rebuilt Netlify `/` and `/system` page calls the cloud API successfully with CORS, distinguishes empty from failure and permits manual retry.
6. Check applicable Free-account settings, startup workers, memory/cold start and current CI; record limitations honestly.

Only then mark hosted acceptance passed. Report M1 completion and wait for explicit permission before M2. Do not import data to make readiness green at this milestone.

## Troubleshooting

- **API address not configured:** add `VITE_API_BASE_URL` in Netlify build variables and redeploy.
- **Module/app not found:** application directory must be `backend`; publish `[tool.fastapi]`, `src/`, `pyproject.toml` and `uv.lock` together.
- **503 database role misconfigured:** cloud `DATABASE_URL` uses an elevated role; use the restricted runtime login.
- **503 database unavailable:** verify the rotated secret, Supabase availability and cloud outbound connection; inspect provider logs locally without sharing credentials.
- **CORS/network failure:** backend `ALLOWED_ORIGINS` must exactly match `https://steam-discovery.netlify.app`, without trailing slash; save/redeploy the backend.
- **Cold start:** let the bounded 75-second check finish, then retry manually. No background polling.

References: [existing-project migration](https://fastapicloud.com/docs/getting-started/existing-project), [GitHub integration](https://fastapicloud.com/docs/source-control/github-integration), [application directory](https://fastapicloud.com/docs/builds-and-deployments/application-directory), [environment variables](https://fastapicloud.com/docs/builds-and-deployments/environment-variables), [dependency installation](https://fastapicloud.com/docs/builds-and-deployments/install-dependencies), [ignore rules](https://fastapicloud.com/docs/builds-and-deployments/fastapicloudignore).
