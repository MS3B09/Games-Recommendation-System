# Deployment — Netlify + FastAPI Cloud Hobby

**M2 is complete. Hosted M2 verification is owner-confirmed** after publication of `3453bfb` and successful backend/frontend CI. Frontend: **https://steam-discovery.netlify.app/**. Backend: **https://steam-discovery-api.fastapicloud.dev/**. The final [clean-database replay](reports/m2-clean-replay.md) passed twice in approved Actions run `38680812079` on `3a62d1e`, including integrity/permissions/API/reproducibility checks and cleanup. Production hosting/database settings were not changed by replay verification. [M2 evidence](reports/m2-implementation.md) · [Historical M1 evidence](reports/m1-hosted-verification.md). Stop before M3 until explicit approval.

The M2 application was published in `3453bfb`; its unchanged frontend passed [CI with 11 browser tests](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38673824585). Replay support was published in `3a62d1e`, with passing [backend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680783914) and [clean replay](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680812079). Completion evidence and retained reports were published in `6264063`. Hosted M2 acceptance and private plan/scaling/worker settings are owner-confirmed; no provider dashboard changes were made during replay verification.

## M2 publication checklist — historical procedure; hosted verification now owner-confirmed

1. Publish the intended frontend/backend/contracts to the connected GitHub repository when authorized; allow the existing free hosting integrations to deploy the correct revision. M2 publication is complete (`3453bfb`); hosted verification is owner-confirmed.
2. Alembic `0002` and the active catalog are already applied to the configured Supabase project. Do not rerun initial SQL or put `MIGRATION_DATABASE_URL` in serving settings. Existing restricted `DATABASE_URL` and exact `ALLOWED_ORIGINS` remain sufficient; no Groq key is required.
3. Recheck applicable free-plan settings below, then confirm both providers built the intended revision. Netlify public `VITE_API_BASE_URL` stays the same.
4. Verify `/api/v1/games?q=Hades`, facets, details, a constrained POST `/api/v1/discover`, current contracts and POST CORS. Verify Netlify favorite selection → recorded-price/platform/mode filters → results → source evidence → direct details/reload on desktop/mobile. Readiness should now be 200 with the active version, not the historical M1 503.
5. Record hosted evidence and resolve the clean-native-database replay gate before marking M2 complete. Both are now satisfied; [retained completion evidence](reports/m2-clean-replay.md). M3 still requires explicit approval.

`npm run verify:hosted` below is the historical M1 verifier and assumes an unpublished catalog. It is not the M2 acceptance verifier. [M2 local verification commands](operations-m2.md).

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

The GitHub integration deploys the default branch when connected and on subsequent pushes. For an existing app, use **Settings → Source → Repository** to connect GitHub, and set **Application Directory** to `backend`. Confirm the correct commit/build logs in the dashboard. No Render build/start commands or `render.yaml` are needed; that superseded file was removed in the published migration.

### Environment variables

Under **App Details → Environment Variables**, add:

| Variable | Value | Secret? |
| --- | --- | --- |
| `DATABASE_URL` | Your restricted `game_discovery_runtime.<PROJECT_REF>` Supabase Session-pooler URI, using the rotated password | **Yes — enable Secret when creating it** |
| `ALLOWED_ORIGINS` | `https://steam-discovery.netlify.app` | No |

Use the actual URI from your local configuration; URL-encode special characters in the password. Do not paste secrets into chat. If a credential was shared, rotate it in Supabase first, then update both ignored `backend/.env` and the cloud secret. Credentials are never embedded in these docs or deployment files.

Choose **Save and Redeploy** to apply changes. Secret status must be chosen at creation; if a value was previously added as a regular variable, recreate it as a secret. Add the listed values individually rather than importing the entire local `.env`: **`MIGRATION_DATABASE_URL` stays developer-only**. No Groq key or Supabase service-role key is required. Do not connect a second database through an integration; the existing Supabase database remains the only one.

**Do not add `WEB_CONCURRENCY`:** the owner reported FastAPI Cloud rejecting that name with “Invalid environment variable name” and removed it. The reason for this platform validation is not verified; do not assume generic Uvicorn environment settings are configurable on this managed service or substitute an undocumented variable.

Keep maximum replicas at **1** using **Scaling**, and inspect startup logs/settings for worker count after relevant configuration changes. The owner confirmed minimum 0/maximum 1 replica and **one active serving worker** during M1 handoff. Each worker creates its own two-connection pool; replica count alone does not prove worker count. During rolling deploys old/new replicas can briefly overlap; the runtime role's five-connection limit remains in place. No grants or role limits were changed for hosting. Explicit local `--workers 1` commands remain valid for locally managed Uvicorn processes.

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

Run reviewed schema migrations explicitly from the developer environment, never on cloud/API startup. If a health-check path is configurable, use **`/health/live`** for process liveness; catalog readiness describes database/artifact availability and is a separate check. The active M2 catalog now makes readiness return 200 when its dependencies are available.

## 2. Connect the Netlify frontend

After the backend deploys, copy its **public HTTPS app origin** from FastAPI Cloud, normally on `fastapicloud.dev`.

In **Netlify → steam-discovery → Project configuration → Environment variables**, build scope, set:

```dotenv
VITE_API_BASE_URL=https://steam-discovery-api.fastapicloud.dev
```

Use the real app URL with **no `/docs` or `/api` suffix**. This is public configuration. No database password/URI, migration credential, provider key or service-role key belongs in Netlify/frontend variables.

**Trigger a new Netlify deploy** after changing the variable: Vite embeds it at build time. The owner completed this rebuild; the live JS artifact now contains the correct public API origin and connects successfully.

Root `netlify.toml` retains base `frontend`, Node 24.13.0, build `npm run lint && npm run check:api && npm run build`, publish `dist`, and a 200 SPA fallback to `/index.html`. The public `/system` route is already verified. Avoid unnecessary rebuilds on the Free plan.

## 3. Free-only validation

Official FastAPI Cloud [pricing](https://fastapicloud.com/pricing), checked 2026-10-14, lists Hobby at **$0 / no credit card**, 3 apps, 0.1 vCPU / 512 MB shared, scale-to-zero and one-day logs/metrics. The service is in **public beta**; usage billing/build-minute limits are still being developed. These are current allowances, not permanent free guarantees. Recheck account settings and billing notices before deployment; do not upgrade to Pro or paid resources.

The pricing page is internally inconsistent about maximum replicas (summary 3 versus table 2); the [autoscaling guide](https://fastapicloud.com/docs/advanced-features/autoscaling) documents Hobby min 0 / max selectable 1–3. Configure max **1**, which avoids relying on that discrepancy. Owner confirmed Hobby/$0, min 0/max 1 and one worker. Hosted peak memory, actual cold starts and quota exhaustion remain unmeasured; local encoder measurements are not cloud guarantees.

The owner confirmed the applicable Netlify **Free** plan without paid upgrades/recharge. Current credit-based Free documentation lists a 300-credit hard stop; recheck changing account limits before later releases. Scale-to-zero/cold starts are accepted; do not add background uptime polling.

## 4. Hosted M1 gate — passed

The owner supplied both public URLs and the following checks passed at M1 handoff. They are historical observations; `npm run verify:hosted` encodes that old unpublished state:

1. `/health/live`: 200 `alive`.
2. `/api/v1/catalog/status`: 200 `uninitialized`, zero games.
3. `/health/ready`: 503 `catalog_not_initialized` — expected until M2 catalog publication.
4. `/docs` and `/openapi.json` render the actual API contract.
5. The rebuilt Netlify `/` and `/system` page calls the cloud API successfully with CORS, distinguishes empty from failure and permits manual retry.
6. Free-account/scaling/worker settings are owner-confirmed and CI is checked; memory/cold-start/load limitations are recorded in the report rather than claimed as measured.

Hosted M1 acceptance passed under the historical conditions above. M2 is now published and complete: its real catalog is active, hosted verification is owner-confirmed, and the final clean replay/cleanup passed. Do not use the historical unpublished-catalog assertions as current M2 expectations.

## Troubleshooting

- **API address not configured:** add `VITE_API_BASE_URL` in Netlify build variables and redeploy.
- **Module/app not found:** application directory must be `backend`; publish `[tool.fastapi]`, `src/`, `pyproject.toml` and `uv.lock` together.
- **503 database role misconfigured:** cloud `DATABASE_URL` uses an elevated role; use the restricted runtime login.
- **503 database unavailable:** verify the rotated secret, Supabase availability and cloud outbound connection; inspect provider logs locally without sharing credentials.
- **CORS/network failure:** backend `ALLOWED_ORIGINS` must exactly match `https://steam-discovery.netlify.app`, without trailing slash; save/redeploy the backend.
- **Cold start:** let the bounded 75-second check finish, then retry manually. No background polling.

References: [existing-project migration](https://fastapicloud.com/docs/getting-started/existing-project), [GitHub integration](https://fastapicloud.com/docs/source-control/github-integration), [application directory](https://fastapicloud.com/docs/builds-and-deployments/application-directory), [environment variables](https://fastapicloud.com/docs/builds-and-deployments/environment-variables), [dependency installation](https://fastapicloud.com/docs/builds-and-deployments/install-dependencies), [ignore rules](https://fastapicloud.com/docs/builds-and-deployments/fastapicloudignore).
