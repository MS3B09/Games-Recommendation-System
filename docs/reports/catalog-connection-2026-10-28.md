# Catalog error layout and local connection recovery — 2026-10-28

Owner reported a vertically broken catalog-controls connection error. Fixed the UI first, then inspected the running services and restored a matching frontend/backend pair.

## Confirmed findings and fixes

- `.study-boundaries` has a68px label column and a flexible controls column on desktop. The shared `ErrorNotice` was a new direct grid child without explicit placement, so auto-placement put it in the68px column. Its text and retry button wrapped almost word by word. The notice now occupies column2 with the controls, changing to column1 with the existing ≤900px single-column layout. Error wording, timing and recovery behavior are retained.
- At inspection, neither API:8001 nor preview:4173 had a listener. The retained preview build targeted API:8001. The only local API listener was PID7792 on:8000, started October15 through the base Miniconda interpreter. Its facets response omitted the current required `max_price_cents`; its catalog status reported AI/semantic matching disabled. Its OpenAPI route also returned500. This was an older runtime, not the current application pair. The screenshot's original browser URL was not supplied; these are the directly observed local conditions, not a reconstruction of every earlier request.
- Rebuilt the actual E: frontend through the existing C: dependency harness, then started the current project environment's API on:8001 and preview on:4173. The fresh API reports semantic matching/AI enabled, includes `max_price_cents:5999`, and serves current OpenAPI/error metadata successfully. No live inference was used to establish readiness.
- Added ignored public-only `frontend/.env.local` and its C: harness counterpart with `VITE_API_BASE_URL=http://127.0.0.1:8001`. Verified a build **without** the shell override produced the same bundle. This persists the intended local API target. Per Vite's environment rules, this setting is baked into a build; changing it requires rebuilding, not just restarting preview. Explicit shell variables still override it.
- The local recovery helper waits for the current facets contract before starting preview, avoiding a first page load while Python is still importing. A transient refused connection during this recovery's initial cold startup cleared through the real retry controls after readiness.

## Verification

- TypeScript, Vite production build, targeted ESLint and whitespace checks pass; Impeccable CSS detector returns `[]`.
- [32 targeted browser tests](catalog-connection-browser-tests.json) pass: all error tests and discovery-controls tests. Five new tests at1440/1000/900/390/320px assert the error shares the controls' horizontal bounds, the retry button stays single-line, no horizontal overflow, axe zero violations, no automatic retry, and a successful explicit retry restores the slider without changing the stored$20 budget.
- Existing three-width chat-error scans and compact header/composer assertions also pass in this run. The earlier full72-test report remains dated evidence, not a new full-suite run.
- Opened the new error captures at1440/390/320 and confirmed readable copy and button placement. Captures remain in `C:/Users/User/AppData/Local/Temp/opencode/game-discovery-m1/frontend/test-results-catalog-connection/`.
- Actual browser → preview → current API → restricted catalog: favorite resolution/facets succeed; Portal search returns Portal and Portal2 with200; discovery returns200 and renders10 recommendations. After readiness: zero alerts, failed requests, page errors or horizontal overflow in the checked journey. Real retry of the initial connection failure also succeeds.
- Current API catalog status and OpenAPI both return200; preview CORS origin is allowed. No chat-generation request, live provider call, accounting reservation, schema change, counter reset or R4 continuation occurred.

## Inspection handoff

Open **http://127.0.0.1:4173/** and hard-refresh. Both `/` and `/current-original.html` serve the fixed source.

At handoff, current API launcher21428/serving child4728 listens on:8001; preview23676 listens on:4173. Their identities/listeners were checked. Recheck before stopping or duplicating them. The older:8000 process was preserved.

For later restarts, follow [the current startup commands](../operations-assistant.md#start-the-backend-using-a-durable-project-environment), using the project interpreter and API:8001 with preview:4173. Local recovery helper: `C:/Users/User/AppData/Local/Temp/opencode/start-catalog-connection-recovery.py`; logs: `catalog-connection-{api,preview}.{stdout,stderr}.log` in that same directory. It reuses existing listeners and checks catalog readiness. No new credentials are needed. No commit/push/deploy/M5; frozen R4 journals and prechange archive remain preserved.
