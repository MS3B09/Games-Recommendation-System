# M1 hosted walking-skeleton verification

Date: **2026-10-14**. Result: **PASS for M1; milestone complete**. At that time, M2 had not started and required explicit permission.

**Historical verification snapshot. Current status: M0–M2 are complete.** Hosted M2 is owner-confirmed and its [clean-database replay passed](m2-clean-replay.md). The M1 observations and unpublished-catalog verifier below are retained as historical evidence, not current M2 expectations. M3 requires explicit approval.

- Frontend: https://steam-discovery.netlify.app/
- Backend: https://steam-discovery-api.fastapicloud.dev/
- Published backend migration: `fe79842`; [backend CI passed](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38601010646).
- Last frontend-code CI: `7c6767c`; [frontend CI passed](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38497801731). Subsequent hosting changes did not alter frontend UI code; the actual rebuilt public artifact was exercised here.

## Public endpoint evidence

| Check | Observed result |
| --- | --- |
| `/health/live` | 200, `status=alive` |
| `/api/v1/catalog/status` | 200, `state=uninitialized`, `game_count=0`, no catalog version |
| Source scope/freshness | US/USD, null source observation timestamp |
| Capabilities | Semantic query matching=false; LLM enabled=false |
| `/health/ready` | **503**, `catalog_not_initialized`, retryable=false; response/header request IDs match |
| `/openapi.json` | 200; paths and component schemas match tracked contract |
| `/docs` | 200; actual Swagger UI renders the application title and catalog operation |
| CORS, success/error | Exact Netlify origin allowed; no credentialed wildcard |
| CORS preflight | OPTIONS for allowed-origin GET succeeds |
| Unrelated origin | No Access-Control-Allow-Origin grant; this is CORS behavior, not authentication |

The readiness 503 is **correct**: database connectivity and metadata reads work, but no catalog is published at M1. Do not fabricate/activate data to change it. No discovery endpoint or relevance quality is claimed.

## Actual public browser checks

Chromium used the deployed frontend and real cloud API; no local app server or mock successful catalog was used.

- `/` and direct `/system` both load with 200 and show **API connected / The catalog is being prepared**.
- Requests use the actual FastAPI Cloud origin embedded by the rebuilt Netlify artifact. The API documentation link points to that origin.
- One catalog request per page mount; manual retry succeeds. Reload reconnects.
- Desktop 1440×900 and mobile 390×844 axe scans report **zero violations**; mobile has no horizontal overflow. Keyboard entry reaches the skip link.
- **Zero uncaught JavaScript page errors** in the main frontend page during the checks.
- Delivered application JS includes the public API origin; the verifier found no tested DB-URI/key/private-key patterns. This is a targeted artifact check, not a claim to detect every possible secret.
- A **browser-only intercepted network failure** shows service-unavailable and unknown game-count/freshness rather than a fabricated zero/absent record. Removing interception and retrying recovers against the real API. No production outage or database mutation was induced.

## Owner-confirmed private settings

The owner explicitly confirmed through the structured question tool:

- FastAPI Cloud **Hobby ($0)**, Scaling **minimum 0 / maximum 1** replica.
- Netlify applicable **Free** plan, without paid upgrades/recharge.
- **One active serving worker**, verified by the owner in provider settings/logs.

These are **owner-confirmed**, not independently inspected through provider dashboard access. No deployment/billing credentials were requested. `WEB_CONCURRENCY` remains omitted because the provider rejected it. Existing two-connection per-worker pool and five-connection role limit remain unchanged; rolling deployments may temporarily overlap replicas.

## Timing and scope limitations

Two small endpoint spot-check rounds observed round trips from **761 to 2,415 ms**; catalog status was 797 ms in one round and 2,415 ms in the other. These include client/network/server time and are **not** p50/p95, a load test, or a measured cold start. Earlier requests had already contacted the service. Do not claim the future under-2-second discovery p95 target has passed. Measure actual discovery latency when that endpoint/catalog exists.

Hosted peak RSS, long-term stability/quota exhaustion, real-phone interaction and future encoder/ranking load were not measured here. Free/beta allowance changes require rechecking before later deployment. These do not prevent completion of the M1 walking-skeleton acceptance gates; they remain release/feature verification items.

No catalog import, indexing, recommendation implementation, feedback persistence or evaluation was started. M1 completion does not mean portfolio-ready product completion.

## Reproduce

From `frontend/`, with locked dependencies and Chromium installed:

```powershell
npm ci --no-audit --no-fund
npx playwright install chromium
npm run verify:hosted
```

Optional public-origin overrides: `HOSTED_FRONTEND_URL`, `HOSTED_API_URL`. On this machine, use the documented C: frontend execution copy and `PLAYWRIGHT_BROWSERS_PATH` workaround. The new script was linted and executed there against the same source file.

The verifier is an **explicit manual M1 smoke**, not a CI/uptime poller. It performs a bounded set of GET/OPTIONS requests and browser-only failure interception. It expects M1's unpublished catalog; update its assertions in a later approved milestone once that state intentionally changes. It reads the tracked public OpenAPI file and requires no credentials, database writes or model downloads. The script/report/status updates are local until separately requested publication.
