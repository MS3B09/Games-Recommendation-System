# Local full-stack setup

**Current R4 quota — 2026-10-27:** [Applied100/1,500,000temporary allowance](reports/r4-quota-increase-2026-10-27.md), preserving usage; normal defaults50/500,000. Existing ignored `.env` updated; restart backend, no new keys/dependencies/models. Restore runtime after R4 without deleting counters. Use quota-aware `resume_chat_quota` for current v6 and preserve C: authoritative journals. Today's95calls pause at conservative provider-token headroom; R4 acceptance still incomplete. Older statuses below are historical.

**Current R4 checkpoint — 2026-10-26:** [v6 resume instructions](reports/conversational-rag-r4-resume-2026-10-26.md) supersede October25 status below. Existing configuration/key/model suffice; restart backend for explicit played/undo/shortlist fixes. Preserve the authoritative C: live journal directory in the report, distinct from model cache. Additional inference is approved but today's50daily calls are exhausted; resume with fresh later-UTC-day receipt. No frontend/API contract or deployment change; R4 acceptance remains incomplete.

**Latest R4 update — 2026-10-25:** [fixes/current checkpoint](reports/conversational-rag-r4-continuation.md), [architecture](architecture-assistant.md), [walkthrough](walkthrough-assistant.md). R4 is in progress, not accepted. Additional inference is approved within existing free-tier limits;49daily calls/390,773reserved units pauses two-call turns until a later UTC day. V3 core journey passes3/3; full paired live/human quality is pending. No new credential/configuration/dependency/model/cache setup needed; restart backend for strict generation/reference/metadata fixes. Frontend unchanged, final preview API:8001. R3 entry below is historical.

**RAG update (2026-10-25):** [R3 is complete locally](reports/conversational-rag-r3.md); [plan](conversational-rag-plan.md) / [visual roadmap](design/conversational-rag-plan.html). Full v2 browser/API memory now integrates six backend stages; valid v1 sessions retain transcript/cards/draft while old requirements are quarantined. Exact pending requests survive reload/retry, with protected service-version-skew recovery. Restart an older API and hard-refresh the rebuilt UI together. No new config/key/model/migration needed; preserve configured cache files and the R2 lock. Use [current operations](operations-assistant.md). Stop before separately approved R4/live budget; no live-quality/M5/publication claim.

**Current startup (2026-10-22):** use [independent-assistant operations](operations-assistant.md), including the working project-local `backend/.venv` interpreter, preview :4173 → API :8001, and explicit live-AI prerequisites. The old temporary M3/M4 environments were removed. Main discovery is now favorites/limits/feedback; floating chat is independent. Earlier main-text/refinement instructions below are historical.

**Latest local setup — M4 complete, unpublished (2026-10-19):** use [M4 operations](operations-m4.md) for the current working interpreter, optional pinned query-model files, preview :4173 → API :8001 startup and M4 verification commands. [M4 acceptance evidence](reports/m4-implementation.md) supersedes the historical M4-unstarted notes below. Core discovery needs only the existing restricted database configuration; actual optional Groq additionally needs a deliberate quota migration and server-only provider settings. Public M2 and deployment permissions are unchanged.

**2026-10-18: M0–M3 complete; M3 COMPLETE LOCALLY.** Main agent confirms all five functional gates and final handoff. Independent review marks all four fixes RESOLVED, with ship at the four-scored-fixes verdict-pass scope; all 12 fresh captures inspected with no material regression attributable to that batch. This is not blanket whole-product/UI release approval. Both entry routes load real-API discovery; `/saved` provides guest saves/history/feedback. Hosted M2 is unchanged and M3 unpublished. M4 is unstarted and unauthorized. [Evidence](reports/m3-implementation.md) · [operations](operations-m3.md). No commit/push/deploy authorization.

## Prerequisites and configuration

**Controls follow-up complete locally, main confirmed (2026-10-19):** [report](reports/discovery-controls.md) records the one metadata-failure fix **RESOLVED**, **ship at ONE-SCORED-FIX verdict-pass scope**, separate from the baseline four-fix verdict and not blanket product/publication approval. All 18 refreshed captures reopened with no regression attributable to the fix; earlier full review found no material visual/a11y regression. Full 21 frontend tests/static/build/lint and live nine cases/18 clean scans passed again; backend 51/static/contracts and detector `[]` remain passed. Unavailable facets preserve unbounded null maximum/free-only false and display Any price / No maximum price; finite rendering fallback never becomes budget. Main restored the final build to API :8001. Existing configuration suffices; no new credentials, dependency, migration or database mutation. M4/publication remain unauthorized.

- Recorded toolchain: Node **24.13.0**, npm **11.6.2**, Python **3.13.12**, uv **0.11.16**.
- Existing active PostgreSQL/pgvector catalog, either the configured Supabase Free project or an explicitly prepared local database. Runtime/developer roles are separate; [role setup](backend-foundation.md), [catalog workflow](operations-m2.md).
- For a new local setup, configure ignored `backend/.env` from its example. This machine's existing runtime configuration already passed the live check; **no new credentials are needed**. `DATABASE_URL` is the restricted runtime connection; `MIGRATION_DATABASE_URL` stays developer-only. Development `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`; allow `http://127.0.0.1:4173` for manual preview. Never paste credentials into chat or frontend settings. No Groq key is required.

Use a fast local filesystem for dependencies. This machine's removable FAT32 E: frontend `npm ci` still times out. Actual M3 frontend verification used existing C: dependencies against **actual E: source**, with local-only resolution wrappers, not a stale application mirror or a fresh install. Prefer a normal fast-disk checkout for ongoing work.

## Backend

From repository root on a normal working copy:

```powershell
uv sync --project backend --locked --extra dev --extra benchmark
uv run --project backend --locked --extra dev --extra benchmark python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Serving does not require Torch or model downloads. Run only one serving worker within the bounded pool settings.

### Verified machine-specific environment

The initial uv-created launcher disappeared; no cause is asserted. A fresh **standard-library venv** followed by locked sync installed **83 packages**, and direct interpreter checks passed. To use the recorded location, with the parent directory already present, from repository root:

```powershell
python -m venv 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv'
$env:UV_PROJECT_ENVIRONMENT = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv'
uv sync --project backend --locked --extra dev --extra benchmark
$python = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv\Scripts\python.exe'
& $python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

For an already-created environment, skip creation. The direct interpreter is the stable workflow used for recorded M3 checks; earlier `PYTHONPATH`/missing-shim workarounds are historical.

## Frontend

From `frontend/` on an installable filesystem:

```powershell
npm ci --no-audit --no-fund
npm run dev
```

Open **http://127.0.0.1:5173/** or `/current-original.html`; `/saved` supports direct navigation/reload. Unknown routes offer a home link. Former `/system` and `/games/:id` frontend pages are not current surfaces; corresponding backend health/detail APIs remain.

Development defaults to API **http://127.0.0.1:8000**. Set only public `VITE_API_BASE_URL` in ignored `frontend/.env.local` for another origin. Production builds require this variable at build time; no database/provider keys belong in frontend configuration.

Search/discovery use bounded 75-second network timeouts, cancellation and explicit user retries. No background keep-alive polling. Saved metadata stays readable when the API is unavailable; artwork is a remote URL, not an offline image guarantee. [Current behavior/provenance](../frontend/CURRENT_ORIGINAL.md).

### Interactive preview needs a terminal-run backend

**Main has restored the final :4173 interactive build to API :8001** after successful verification on owned :8002. Test stopped :8002 without changing the owner's :8001 server; no persistent owned background API remains. This documentation pass has not rebuilt or started services. Restart the older :8001 backend to load the new minimum/facet-maximum code, keeping it running in your terminal. Normal development uses :8000 above. For the final :8001 preview, from repository root:

```powershell
$python = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv\Scripts\python.exe'
$env:ALLOWED_ORIGINS = 'http://127.0.0.1:4173'
& $python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8001 --workers 1
```

Leave this terminal open. Start/reuse preview :4173 (`npm run preview` from installed `frontend/` if missing), then refresh both `http://127.0.0.1:4173/` and `http://127.0.0.1:4173/current-original.html`. Build-time `VITE_API_BASE_URL` must match the backend. The opt-in live helper permits only :8001/:8002, defaults :8001 and must own a free selected API port; a future :8002 check requires a matching build to leave an existing :8001 server alone.

## Checks

From repository root in the installed environment:

```powershell
uv run --project backend --locked --extra dev --extra benchmark ruff check backend
uv run --project backend --locked --extra dev --extra benchmark python -m unittest discover -s backend/tests -v
uv run --project backend --locked --extra dev --extra benchmark python -m game_discovery.api.export_schema --check
```

From `backend/`, `uv run --locked --extra dev --extra benchmark mypy` uses all configured serving/config/database/catalog modules. On this machine the same checks passed through direct Python, e.g. from repository root:

```powershell
$python = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv\Scripts\python.exe'
& $python -m unittest discover -s backend/tests -v
& $python -m ruff check backend
& $python -m game_discovery.api.export_schema --check
```

For direct mypy, run `& $python -m mypy` with `backend/` as working directory so configured relative module paths resolve. Ruff covers all backend code; strict mypy covers **13 modules**, not developer jobs. Current recorded controls result: **51 tests**, lint/type/OpenAPI drift pass; baseline 49 remains historical.

From installed `frontend/`, port 4173 free:

```powershell
npm run lint
npm run check:api
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run build
npx playwright install chromium
npm test
```

Current recorded controls result: **21 tests (15 browser + 6 storage)**, TypeScript/build, targeted ESLint over actual E: source/tests/config and generated types, using existing C: tools. Baseline 17 remains historical. This machine uses `PLAYWRIGHT_BROWSERS_PATH=C:\Users\User\AppData\Local\Temp\opencode\game-discovery-browsers`. Normal suite uses fixtures and starts its preview; it excludes live tests. Fresh frontend installation, remote M3 CI and real-phone checks remain unverified. No verification was rerun in this documentation pass.

The separate **`npm run verify:m3`** requires `API_PYTHON` and preview already running, built for the selected API. `M3_API_ORIGIN` defaults to `http://127.0.0.1:8001` and permits only that origin or `http://127.0.0.1:8002`. It owns/stops its API, refuses CI/occupied healthy API and reads the existing restricted catalog with preview CORS. Local-only C: execution wrappers start a missing preview/reuse an existing one and stop owned processes; normal live config still expects preview running. [Procedure](operations-m3.md#explicit-live-m3-check). Controls result: one passing live test on owned :8002, nine API cases, 18 clean scans; [retained JSON](reports/discovery-controls-live.json). Old frozen-page/smoke verifiers are removed.

## API contract regeneration

From root, after deliberate API-contract changes:

```powershell
uv run --project backend --locked --extra dev --extra benchmark python -m game_discovery.api.export_schema
```

Then from `frontend/`: `npm run generate:api`. Track `backend/openapi.json` and `frontend/src/api/schema.d.ts`; schema export does not connect to the database. Network-boundary validation remains necessary in addition to generated types.

## Explicit database setup and migrations

M3 adds **no migration/schema change**; the configured M2 catalog is already active. For a separately prepared fresh database or deliberately authorized future release, from repository root:

```powershell
uv run --project backend --locked python -m game_discovery.db.migrate current
uv run --project backend --locked python -m game_discovery.db.migrate sql
# Fresh database or explicitly approved release only; never on API startup.
uv run --project backend --locked python -m game_discovery.db.migrate upgrade
```

These use only `MIGRATION_DATABASE_URL`, with NullPool. Serving uses restricted `DATABASE_URL`, a two-connection pool/no overflow, one-second wait, three-second connection and two-second statement bounds; prepared statements are disabled for pooler compatibility. Do not reapply initial SQL or blindly stamp an unrelated database. The initial existing-schema adoption and private Alembic revision table are documented in [backend foundation](backend-foundation.md).

### Native database-only alternative

Use PostgreSQL 17 with pgvector, a dedicated database, privileged developer connection and separate restricted runtime connection. No full Supabase stack is required. The catalog migration can install `vector` in `extensions`; native runtime URLs use the local role name without a pooler project suffix. Follow [M2 operations](operations-m2.md) for reproducible collection/artifacts/import/activation; migrations alone do not create a usable catalog.

Fresh native installation was not performed on this machine. Two complete fresh PostgreSQL 17.10/pgvector 0.8.2 builds passed in the earlier approved [M2 Actions replay](reports/m2-clean-replay.md). M3 live checks read the existing catalog, not a newly replayed database.

## Handoff boundary

[Deployment settings](deployment.md) record hosted M2, not M3 publication. Final handoff is confirmed and M3 complete locally; stop here. Commit/push/deploy and starting the unstarted M4 require explicit owner authorization.
