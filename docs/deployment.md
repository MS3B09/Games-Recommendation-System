# Deployment — Netlify + FastAPI Cloud Hobby

> **Current quota boundary — 2026-10-27:** [Temporary R4 quota migration applied](reports/r4-quota-increase-2026-10-27.md):100calls/1,500,000reserved units, old usage preserved, runtime defaults50/500,000. This is authorized accounting/configuration work, not publication. Restore lower runtime after R4 without clearing usage. Development proposed13/13passes; held-out pricing-prose failures/latency/human gates remain. Hosted M2, frontend and deployment settings unchanged; no M5/commit/push/deploy authority.

> **Current R4 boundary — 2026-10-26:** [v6 checkpoint](reports/conversational-rag-r4-resume-2026-10-26.md). Backend-only explicit-operation/shortlist/diagnostic/journal changes verified locally. Current9/26development attempts; full live/human/representative latency gates pending. Additional inference approved; today's50calls exhausted. Preserve authoritative C: journals; resume on later UTC days. Hosted M2 remains; no M5/commit/push/deploy authority. October25 statuses below are historical.

> **Latest R4 boundary — 2026-10-25:** [verified fixes/current checkpoint](reports/conversational-rag-r4-continuation.md). Strict generation and v3 proposed core journey3/3 work locally; fixed runtime retrieval p95487ms does not prove hosted quality. Full paired live/human/serving-total-latency gates remain. Additional free-tier inference approved, current49daily calls pause further two-call turns until a later UTC day. Frontend/config/hosting unchanged. Public M2 remains; M5/commit/push/deploy unauthorized. [Architecture](architecture-assistant.md) / [walkthrough](walkthrough-assistant.md). Earlier entries are historical.

> **Current boundary (2026-10-25):** [RAG R0–R3 complete locally](reports/conversational-rag-r3.md); full v2 wire/browser memory now integrates six pinned Core stages, with protected legacy migration/retry/skew handling. Any later authorized release must publish compatible API/generated contracts/frontend together; old frontend→new API retains legacy behavior, new frontend→old API preserves state and reports recovery. Hosted M2 remains public. Local scripted-provider/browser measurements do not prove hosted memory/latency/free allowances or live quality. October22 quota migrations remain as recorded in [revision evidence](reports/assistant-redesign.md). R4/live budgets and cloud/deployment/M5/commit/push need separate approval.

> **Latest boundary (2026-10-19): M0–M4 complete; M3/M4 local and unpublished.** [M4 evidence](reports/m4-implementation.md) and [operations](operations-m4.md) supersede the historical M4-unstarted notes below. No M4 deployment, hosting setting change or application quota migration was performed. The public release remains M2. Publication, commit/push and M5 require explicit owner permission; the scoped M4 UI SHIP verdict is not deployment approval.

> **Current local/hosted boundary (2026-10-18): M0–M3 complete; M3 COMPLETE LOCALLY**, with all five functional gates and final handoff confirmed by main agent. Hosted M2 remains unchanged; M3 is **unpublished**. Independent review: all four material fixes RESOLVED, ship at the four-scored-fixes verdict-pass scope; all 12 fresh captures inspected with no material regression attributable to the fix batch. Not blanket whole-product/UI release approval. M4 is unstarted and unauthorized; no commit/push/deploy authorization. [M3 evidence](reports/m3-implementation.md) · [current routes/checks](../frontend/CURRENT_ORIGINAL.md). Removed verifier references below remain historical, not current runnable instructions.

**M2 is complete. Hosted M2 verification is owner-confirmed** after publication of `3453bfb` and successful backend/frontend CI. Frontend: **https://steam-discovery.netlify.app/**. Backend: **https://steam-discovery-api.fastapicloud.dev/**. The final [clean-database replay](reports/m2-clean-replay.md) passed twice in approved Actions run `38680812079` on `3a62d1e`, including integrity/permissions/API/reproducibility checks and cleanup. Production hosting/database settings were not changed by replay verification. [M2 evidence](reports/m2-implementation.md) · [Historical M1 evidence](reports/m1-hosted-verification.md). Subsequent M3 implementation authorization does not authorize publication or M4.

## M3 publication handoff — not authorized or performed

Local baseline completion/four-fix review are recorded in [M3 implementation](reports/m3-implementation.md). The owner-authorized [controls follow-up](reports/discovery-controls.md) is **complete locally, main confirmed (2026-10-19)**: one metadata-failure fix **RESOLVED**, **ship at ONE-SCORED-FIX verdict-pass scope**, not blanket product/publication approval. Reviewer reopened all 18 refreshed captures with no regression attributable to the fix; earlier full review found no material visual/a11y regression. Full 21 frontend/static/build/lint and live nine cases/18 clean scans passed again; backend 51/static/contracts and detector `[]` remain passed. Unavailable facets preserve null maximum/free-only false without persisting rendering fallback as budget. No hosted follow-up is claimed. Future authorized publication needs matching backend/frontend/generated contracts for minimum price, facets maximum, required genres and feedback. Existing ignored runtime configuration suffices; no new secrets/migration. Restricted `DATABASE_URL`, exact `ALLOWED_ORIGINS` and public `VITE_API_BASE_URL` remain the boundary; secrets stay local/provider-side. Fresh frontend install/remote M3 CI/real-phone remain unverified.

The live helper permits only loopback :8001/:8002 (default :8001). Controls verification used owned :8002 to avoid the owner's :8001; test stopped :8002 without changing :8001. **Main restored the final interactive :4173 build to API :8001**. User must restart older :8001 backend, start/reuse preview :4173 and refresh both entry URLs for minimum/facet support. No persistent owned background API. Local-only wrappers start missing preview/reuse existing and stop owned processes; normal source live config still expects owner preview running. Normal dev uses :8000. [Local commands](operations-m3.md#interactive-preview-after-verification). No deployment was verified. Neither local checks nor historical M2 evidence establishes hosted M3 behavior; free-plan rechecks and explicit publication authorization remain required. Procedures below are reference only.

The M2 application was published in `3453bfb`; its unchanged frontend passed [CI with 11 browser tests](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38673824585). Replay support was published in `3a62d1e`, with passing [backend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680783914) and [clean replay](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680812079). Completion evidence and retained reports were published in `6264063`. Hosted M2 acceptance and private plan/scaling/worker settings are owner-confirmed; no provider dashboard changes were made during replay verification.

## M2 publication checklist — historical procedure; hosted verification now owner-confirmed

1. Publish the intended frontend/backend/contracts to the connected GitHub repository when authorized; allow the existing free hosting integrations to deploy the correct revision. M2 publication is complete (`3453bfb`); hosted verification is owner-confirmed.
2. Alembic `0002` and the active catalog are already applied to the configured Supabase project. Do not rerun initial SQL or put `MIGRATION_DATABASE_URL` in serving settings. Existing restricted `DATABASE_URL` and exact `ALLOWED_ORIGINS` remain sufficient; no Groq key is required.
3. Recheck applicable free-plan settings below, then confirm both providers built the intended revision. Netlify public `VITE_API_BASE_URL` stays the same.
4. Verify `/api/v1/games?q=Hades`, facets, details, a constrained POST `/api/v1/discover`, current contracts and POST CORS. Verify Netlify favorite selection → recorded-price/platform/mode filters → results → source evidence → direct details/reload on desktop/mobile. Readiness should now be 200 with the active version, not the historical M1 503.
5. Record hosted evidence and resolve the clean-native-database replay gate before marking M2 complete. Both are now satisfied; [retained completion evidence](reports/m2-clean-replay.md). This checklist is historical; the current M3 boundary is above.

The removed `verify:hosted` command was the historical M1 verifier and assumed an unpublished catalog. It is not a current acceptance command. Use [current M3 operations](operations-m3.md) for local verification; retain M2 reports as historical evidence.

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

Root `netlify.toml` retains base `frontend`, Node 24.13.0, build `npm run lint && npm run check:api && npm run build`, publish `dist`, and a 200 SPA fallback to `/index.html`. Historical hosted `/system` verification describes M1/M2. Current local routes are `/`, `/current-original.html` and `/saved`; a future authorized M3 publication must verify direct saved navigation/reload. Avoid unnecessary rebuilds on the Free plan.

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
