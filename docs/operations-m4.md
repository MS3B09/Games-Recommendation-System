# M4 local hybrid discovery

**Superseded UI/startup, 2026-10-22:** the current application separates favorites/limits/feedback discovery from an independent floating assistant. Use [current operations](operations-assistant.md) and durable `backend/.venv`; temporary interpreter paths below are historical and removed. This document retains compatible backend text/model/quota workflows, not the current frontend composition.

[Implementation and acceptance evidence](reports/m4-implementation.md) · [live report](reports/m4-live-evidence.json) · [budget verification](reports/m4-budget-evidence.json)

M4 is complete locally and unpublished. The public site remains hosted M2. The optional Groq path is implemented and failure-tested; live Groq has not been exercised because no key is configured.

## Normal setup and checks

From the repository root:

```powershell
uv sync --project backend --locked --extra dev --extra benchmark
uv run --project backend --locked --extra dev --extra benchmark python -m unittest discover -s backend/tests -v
uv run --project backend --locked --extra dev --extra benchmark ruff check backend
uv run --project backend --locked --extra dev --extra benchmark python -m game_discovery.api.export_schema --check
```

From `backend/`:

```powershell
uv run --locked --extra dev --extra benchmark mypy
```

From an installed `frontend/`:

```powershell
npm run lint
npm run check:api
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8001'
npm run build
npm test
```

Normal frontend tests mock the service and require the configured preview port to be available. The live M4 config expects preview already running.

## Query model files

Serving never downloads model weights. Acquire the two public files once through a developer command; no Hugging Face token is required:

```powershell
uv run --project backend --locked --extra benchmark python -c "from huggingface_hub import hf_hub_download; from game_discovery.catalog.contracts import MODEL_ID,MODEL_REVISION; cache='data/artifacts/model-cache'; print(hf_hub_download(MODEL_ID,'tokenizer.json',revision=MODEL_REVISION,cache_dir=cache,token=False)); print(hf_hub_download(MODEL_ID,'onnx/model.onnx',revision=MODEL_REVISION,cache_dir=cache,token=False))"
```

Set these **backend-only** environment variables or add them to ignored `backend/.env`:

| Variable | Value |
| --- | --- |
| `QUERY_TOKENIZER_PATH` | Absolute path printed for `tokenizer.json` |
| `QUERY_MODEL_PATH` | Absolute path printed for `onnx/model.onnx` |
| `QUERY_ARTIFACT_PATH` | Absolute path to the matching active catalog's `artifact.json`; the current 40-game catalog manifest is `docs/reports/m2-artifact-manifest.json` |

The loader verifies the manifest digest, pinned revision, dimensions and exact model/tokenizer hashes. A different active artifact disables semantic use and safely falls back; do not pair unrelated embedding generations. The `benchmark` extra supplies the compact ONNX runtime, tokenizer and NumPy dependencies.

Missing/invalid/busy encoder: the API discloses reduced semantic matching and retains lexical/seed discovery. Price/platform/mode/genre/exclusion controls remain authoritative.

## Current machine: interactive preview

The final local preview build targets **API :8001**. The live checker owns and stops **:8002**; it does not leave an API running or replace the owner's separate backend. Start a new terminal at `E:\Games-Recommendation-System`, or stop/restart your older :8001 process yourself if it is still running.

The freshly installed interpreter actually verified on this machine is:

`C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m4-venv\Scripts\python.exe`

To use the locally reacquired model files and current catalog:

```powershell
$python = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m4-venv\Scripts\python.exe'
$snapshot = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-models\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
$env:QUERY_TOKENIZER_PATH = "$snapshot\tokenizer.json"
$env:QUERY_MODEL_PATH = "$snapshot\onnx\model.onnx"
$env:QUERY_ARTIFACT_PATH = 'E:\Games-Recommendation-System\docs\reports\m2-artifact-manifest.json'
$env:ALLOWED_ORIGINS = 'http://127.0.0.1:4173'
& $python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8001 --workers 1
```

Keep that terminal open, reuse/start preview at :4173, then refresh both `/` and `/current-original.html`. Existing ignored restricted `DATABASE_URL` supplies catalog access. No Groq key is needed for this journey. If the temporary model directory is removed, reacquire pinned files and update the paths; the backend will not download them on demand.

The fresh environment was created with `UV_PROJECT_ENVIRONMENT` pointing to that temporary directory and `uv sync --project backend --locked --extra dev --extra benchmark`. Actual E: frontend source is compiled through existing C: tools; no fresh frontend installation is claimed.

## Request and criteria rules

`POST /api/v1/discover` accepts optional `query` (2,000 characters), `conversation.messages` and prior normalized `conversation.criteria`, plus current favorites/filters/preferences/feedback. At most 20 messages and 12,000 total characters are accepted. Assistant messages do not become ranking intent; recent user text is bounded to 2,000 characters for ranking.

Explicit current filters override saved/prior criteria. Local interpretation reads the **current** turn only for hard changes; earlier user text contributes ranking context and experience uncertainty. Clear numeric upper budgets, supported platforms/modes and selected removal/free-only phrases are recognized conservatively. Other wording may remain unresolved without AI.

Language changes conflicting with explicit controls return `conflicts`, unchanged `effective_criteria`, and `proposed_criteria`. **Keep my controls** rejects that patch. **Apply text changes** explicitly resubmits approved criteria. Equal-dollar “under” text may tighten an inclusive upper bound to exclusive; this is visible in applied criteria. Moving the price slider returns its normal inclusive semantics.

The response reports `hybrid-text-v1`, `interpret-claims-v1`, effective text/criteria, uncertainty, capabilities and separate core/interpretation/explanation/total timings. No percentage match confidence is invented.

## Session and clearing

**Owner revision, 2026-10-22:** the after-results conversation/refinement UI is removed. Edit the existing request text and/or My limits in **Your taste**, then select **Find my next game**. The existing **Rework your request** link returns there.

`game-discovery:conversation` retains its validated version-1 **session-storage** envelope for compatibility, separate from version-2 device data. The current UI retains request text and normalized criteria, writes empty messages/draft after discovery, and sends no previous messages. It stores no result archive. Reload retains the request and asks users to submit Find my next game for fresh results. The backend conversation API and its bounded validation remain compatible.

Corrupt/future/oversized session data is protected from overwrite; the UI offers **Reset request storage**. Blocked/full storage keeps the current request in memory and explains possible reload loss. Clear my saved data removes all owned local/session keys, and cross-tab reset removes each receiving tab's session before remounting and invalidates pending responses. Unrelated keys are retained. Earlier M4 live evidence and captures describe the pre-removal UI; the browser live-check source now uses the single request form but was not rerun for this removal.

## Optional Groq configuration

Use only a verified free Groq account/model. Set the following in ignored `backend/.env` or server environment settings, **never in frontend variables or chat**:

```dotenv
GROQ_API_KEY=REPLACE_LOCALLY
GROQ_MODEL=llama-3.3-70b-versatile
AI_ENABLED=true
AI_DAILY_CALLS=20
AI_DAILY_TOKENS=100000
```

Before deliberately enabling AI against an application database, apply the explicit allowance migration using developer-only `MIGRATION_DATABASE_URL`:

```powershell
uv run --project backend --locked python -m game_discovery.db.migrate upgrade
```

**This command writes the configured application database. It was not run against the application's schema during M4 verification.** The new Alembic revision `0003` creates one private counter row/table and a restricted security-definer reservation function. No guest text or identifiers are stored there. The API never runs migrations at startup; if accounting is absent/unavailable, AI calls fail closed and core discovery remains useful.

Global hard ceilings: 20 calls/day, 100,000 conservatively reserved tokens/day, four calls/minute, 16,000 maximum reservation per call. Settings may lower the daily limits. Reserve before contacting Groq, commit before the call, and do not refund failures/crashes. The local peer-address throttle is one AI-assisted request per 30 seconds, bounded to 1,024 remembered peers; clients sharing a proxy address can share that local limit. There is one network slot and at most one interpretation plus one batched explanation per discovery. Input/output sizes, output tokens and network timeout are bounded; there is no automatic provider retry.

Only source-selected, exact validated claims are rendered through templates. Invalid output, invented IDs, unsupported facts, provider errors, timeouts and exhausted allowances use source-derived templates. Live Groq success, account allowance verification and hosted behavior remain unverified.

## Reproduce real verification

Atomic SQL verification uses unique scratch schema names and separate migration/runtime logins:

```powershell
uv run --project backend --locked --extra benchmark python -m game_discovery.jobs.verify_ai_budget
```

It applies the exact SQL in the scratch schema, checks concurrency and restart behavior in another Python process, and removes the schema. It does not apply the application's migration. After an interrupted run, inspect the report and explicitly clean only its named owned scratch schema:

```powershell
uv run --project backend --locked python -m game_discovery.jobs.verify_ai_budget --cleanup-schema m4_budget_verify_REPLACE_WITH_REPORTED_SUFFIX
```

For browser → owned API → real catalog verification, build preview for the same dedicated API origin, leave preview running, and run from `frontend/`:

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8002'
npm run build
# Run npm run preview in another terminal.
$env:API_PYTHON = 'ABSOLUTE_PATH_TO_INSTALLED_BACKEND_PYTHON'
$env:M4_API_ORIGIN = 'http://127.0.0.1:8002'
# Also set QUERY_TOKENIZER_PATH, QUERY_MODEL_PATH, QUERY_ARTIFACT_PATH as above.
npm run verify:m4
```

The developer-only checker refuses an occupied API port and CI, permits only loopback :8001/:8002, forces AI disabled, and stops only its owned API. It overwrites `docs/reports/m4-live-evidence.json` and twelve local screenshots. Rebuild preview for :8001 afterward for the normal interactive setup.

No commit, push, hosted deployment or M5 work is authorized by these commands or local acceptance.
