# Live Groq configuration verification — 2026-10-22

Owner requested a live check after configuring `backend/.env`, then explicitly approved applying the existing AI accounting migration and consuming live requests. Checks used the durable `backend/.venv/Scripts/python.exe` and the configured application database. No secret values are retained here.

## Result

**Groq authentication, the selected model, application accounting and individual chat paths work after the fixes below. This is a staged smoke test, not a full recommendation-quality or browser acceptance pass.** Live output exposed weak relevance and invalid structured responses; successful transport does not establish consistent recommendation quality.

### Configuration observed

- `AI_ENABLED=true`; Groq key present, never printed.
- `GROQ_MODEL=openai/gpt-oss-120b`; authenticated Groq model-list request succeeded and reported the model active.
- `AI_DAILY_CALLS=20`, `AI_DAILY_TOKENS=100000`; no inherited overrides for these settings.
- Query encoder paths are unconfigured. API status reports `semantic_query_matching=false`; chat falls back to keyword matching.
- Catalog ready: 40 games, version `m2-649714e8b26775165f105d02`.

## Blockers found and addressed

1. **Accounting migration missing.** Both `discovery.ai_usage_windows` and `discovery.reserve_ai_usage(integer,integer,integer)` were absent. Chat returned 503 before contacting Groq, as designed.
   - Verified runtime and migration URLs target the same database/project, inspected discovery tables and current revision `0002`.
   - With explicit owner approval, ran `python -m game_discovery.db.migrate upgrade`.
   - Database is now at Alembic revision `0003`, applying `backend/migrations/0004_ai_budget.sql`.
   - Verified quota-table RLS enabled, runtime has no direct table-read privilege, and reservations persist across separate test processes.
2. **Groq HTTP 403 / edge error 1010.** The default Python HTTP identity was rejected. Adding `User-Agent: game-discovery/0.1` made chat requests succeed. The adapter now sends this header.
3. **GPT-OSS response compatibility.** GPT-OSS used substantial completion tokens for reasoning. The adapter now requests `reasoning_effort=low` for the two supported GPT-OSS IDs only, retaining the existing 1,024 completion-token cap and three-second transport timeout.
4. **Prompt-contract mismatches.** Earlier responses repeated a numeric budget in prose, serialized an evidence array into a string, or placed `exclude_ids` inside `filters`. Existing validation rejected those responses with 503. Prompts now prohibit repeating budgets, demonstrate top-level exclusions, prefer empty optional claims and explain exact JSON types. Unsupported subjective comparisons are more explicitly discouraged. Prompt changes do not guarantee future compliance.

## Live observations

Provider calls were real Groq HTTPS requests with real database accounting. FastAPI `TestClient` exercised the actual app. Diagnostic observation wrapped the real transport to inspect HTTP status and generated test responses; it did not supply fake output, bypass quota, increase limits or bypass throttling.

| Check | Observed result |
| --- | --- |
| Backend readiness | 200, real catalog ready |
| Main favorites/limits discovery | 200, ten results; no AI interpretation/explanation calls |
| Chat greeting | 200, natural answer without cards; final uninstrumented greeting took 1.45 seconds |
| Immediate repeated message | 429, `Retry-After: 30`, no extra provider call |
| Windows, single-player, recorded price below USD 20 | 200 after transport/prompt fixes; final uninstrumented search took 3.44 seconds |
| Returned game card | Exact equality with `/api/v1/games/{app_id}`; recorded price, Windows and single-player checked |
| Played-title follow-up | Initially 503 due to wrong exclusion location; after explicit top-level example, 200 with Portal (`400`) excluded and all criteria retained |
| Follow-up recommendations | Empty cards with a message that supplied evidence did not establish the requested combat preference; excluded title not returned |

**Quality limitation:** the successful recommendation selected Portal and described it as matching combat. That combat claim is not established by this smoke test; the follow-up declined to recommend from remaining evidence. The catalog is small and semantic matching is unavailable. This does not establish strong relevance or fully grounded natural prose.

The final follow-up took 8.14 seconds overall. The urllib timeout is not a strict end-to-end deadline. There was no complete all-green rerun of the same three-turn conversation after the last prompt edit: individual successful cases were observed at successive fix stages, and calls stopped to preserve the remaining allowance.

## Accounting after testing

Persisted usage for **2026-10-22 UTC**:

- **16 of 20 call reservations consumed**, including failed attempts.
- **71,835 of 100,000 reserved tokens consumed**.
- **4 calls and 28,165 reserved tokens remain**, assuming no other client consumes them.
- Reserved-token accounting is conservative and differs from Groq actual usage. No failures were refunded or counters reset. The daily window rolls over on the next reservation after UTC midnight.
- Recommendation turns can use two calls. Groq limits remain independent.

## Automated checks

- Backend unit suite: **81 passed**, including transport/GPT-OSS compatibility regression.
- Ruff: passed.
- Strict mypy: passed, 18 source files.
- OpenAPI drift: passed.

## Local operation and scope

Neither :8001 API nor :4173 preview was running at preflight. Tests used temporary in-process app lifecycles and left no persistent server. Default CORS origins are :5173; use documented `ALLOWED_ORIGINS=http://127.0.0.1:4173` for the existing preview.

See [assistant operations](../operations-assistant.md) for startup and optional query-model setup. No frontend changes, browser acceptance run, deployment, commit, push or M5 work. The accounting migration was applied to the configured application database with owner approval; hosted application process/environment deployment remains unchanged.
