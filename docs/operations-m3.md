# M3 guest persistence and personalization

**2026-10-18: M0–M3 complete; M3 COMPLETE LOCALLY.** Main agent confirms all five functional acceptance gates and final handoff. Independent reviewer marks all four material fixes RESOLVED; **ship at the four-scored-fixes verdict-pass scope**, with all 12 fresh captures inspected and no material regression attributable to that batch. This is not blanket whole-product/UI release approval. The authorized M3 extension preserves Current; both HTML entries load `current-original.tsx` → `GuestApp`, and `/saved` uses that system. Hosted M2 remains unchanged; M3 is unpublished. M4 is unstarted and unauthorized; no further implementation or publication is authorized.

[Implementation/check evidence](reports/m3-implementation.md) · [retained live report](reports/m3-live-evidence.json) · [setup](setup.md) · [Current source/provenance](../frontend/CURRENT_ORIGINAL.md)

**Controls follow-up complete locally, main confirmed (2026-10-19):** the one material metadata-failure fix is **RESOLVED**; **ship at ONE-SCORED-FIX verdict-pass scope**, not blanket whole-product/publication approval. Reviewer reopened all 18 refreshed captures with no regression attributable to the fix; earlier full review found no material visual/a11y regression. Full 21 frontend tests (15 browser/6 storage), TypeScript/build/lint and nine live API cases/18 clean scans passed again; 51 Python/static/contracts and detector `[]` remain passed. [Final report](reports/discovery-controls.md) · [refreshed JSON](reports/discovery-controls-live.json). The four-fix verdict above belongs to the historical baseline. M3 stays complete/unpublished; M4 stays unauthorized.

## Guest journey

1. Start with Hades, Windows, single-player and maximum recorded $20 USD. Search the real catalog explicitly and toggle artwork to edit favorites.
2. Set **My limits** in modes → platform → genre → price order: three multi-choice native checkbox disclosures and a two-handle price slider. All selected modes/genres must match; any selected platform may match. Desktop stays one row, ≤900px two columns, ≤640px one column. One-cent, inclusive min/max; $0–$0 submits explicit free-only. The advanced/preferred/unwanted text UI is removed and legacy terms clear on submit; exact exclusions retain conditional Undo exclusions. Unknown required facts do not pass; filters are never silently relaxed.
3. Submit **Find my next game** for API-ranked results, genre-led rows and source evidence/tradeoffs. Editing taste invalidates the old shortlist; resubmit to apply changes. Search/discovery are abortable with bounded network timeouts and manual retry.
4. Save a game independently of **Interested**, **Not For Me** or **Already Played**. `/saved` retains cached title/artwork URL/store URL/recorded price and its original price observation date. This is cached metadata availability when the API is offline, not guaranteed offline image delivery or fresh pricing.
5. Manage feedback and clear recent summaries on `/saved`. A manual availability check sends saved IDs to the resolve endpoint; missing titles remain on the local list with a notice. It does not replace cached prices with an invented fresh observation.
6. **Your device data** explains local-only persistence and request forwarding; **Clear my saved data** resets the application.

## Storage contract and recovery

`frontend/src/guest-store.ts` owns `game-discovery:guest`, a validated version-2 envelope. It contains favorites, full explicit preferences, cached saves, latest feedback per game and recent discovery summaries. Limits: **50 favorites / 200 saves / 500 feedback / 20 history**; explicit additions at capacity show a notice rather than silently evict saves. History retains the newest 20 summaries, not full conversations.

- The defined v1 migration accepts ID-only `favorite_ids`/`saved_ids`, preferences and optional feedback. It creates placeholder metadata, clears required genres, starts empty history, coalesces latest feedback (last action wins ties) and revalidates the migrated envelope as v2. This is support for that defined format, not a claim that the frozen preview saved v1 data.
- Storage remains version 2. Older v2 preferences/history without optional `min_price_cents` normalize to zero; the defined v1 migration remains. History now displays the recorded range or free-to-play. No format bump or database migration.
- Invalid, oversized (>2,000,000 characters) or future-version data is protected from overwrite. The user can continue temporarily or explicitly clear it.
- Quota/blocked storage falls back to memory with **Temporary in this tab** and an explanation. Leaving/reloading can lose unsaved changes. **Try saving again** rereads current shared state before writing; it respects another tab's changes, clear or future format.
- Edits read shared storage first; storage events synchronize tabs. This reduces stale overwrites; local storage is not a transactional multi-writer database. Discovery is not automatically resubmitted by tab updates.
- Clear removes only `game-discovery:` local/session keys, increments the request epoch, remounts transient UI and sends/removes a transient cross-tab reset signal. It leaves no personal-data tombstone. Pre-clear responses cannot restore results/history. Defaults return to Hades/Windows/$20/single-player; unrelated keys remain.
- If removal is blocked, the notice distinguishes an in-tab reset from successfully erasing stored data and directs the user to browser settings.

## Discovery request and ranking

`POST /api/v1/discover` accepts current `favorite_ids`, optional saved `preferences`, explicit `filters`, up to 500 timestamped `feedback` actions and a bounded `limit`. Discovery sends relevant ranking inputs, **not saved lists or history**. Favorite resolution also sends favorite IDs; manual saved availability sends the saved IDs being checked. No language-model processing is enabled.

```json
{
  "favorite_ids": [1145360],
  "preferences": {"platforms": ["windows"], "max_price_cents": 1000, "free_only": true},
  "filters": {"min_price_cents": 0, "max_price_cents": 2000, "price_operator": "lte", "free_only": false, "platform_match": "any", "required_modes": ["single-player"], "required_genres": ["rpg"], "preferred_terms": [], "unwanted_terms": []},
  "feedback": [{"app_id": 620, "kind": "interested", "timestamp": "2026-10-18T18:00:00Z"}],
  "limit": 10
}
```

Omitted explicit fields inherit saved preferences. Explicit **`false`, `null` and `[]`** override saved values. `effective_criteria` reports the merged result. The UI submits its full current filter state, so clearing a control is explicit. `required_genres` is a hard subset constraint against the existing genre taxonomy, distinct from preferred terms. It adds no migration, database schema change or mutation. OpenAPI and frontend types are regenerated.

`min_price_cents` is optional/null for compatible API callers; defined bounds are integers in **0..1,000,000 cents**. Minimum is inclusive; UI maximum uses `lte` (API retains `lt`). Validate minimum ≤ maximum both within `Filters` and after explicit/saved merging; invalid ranges and free-only with positive minimum return **422**. A supplied bound, including minimum zero, requires known US/USD recorded price. Free-only requires explicit free-to-play evidence, not an inference from a temporary zero-price promotion. Current UI sends both term arrays empty on submit; compatible API term behavior remains for future explicitly authorized work.

`GET /api/v1/facets` returns optional `max_price_cents`: the active eligible US/USD recorded catalog maximum, null if none. The slider rounds the cap upward to whole dollars, extends it for stored higher bounds and caps it at 1,000,000 cents. With valid catalog maximum metadata, a stored null maximum can map to that ceiling for slider submission. **When facets are unavailable**, stored `max_price_cents: null` / `free_only: false` remains unbounded in both request filters/preferences and persistence. The disabled slider displays **Any price** / accessible **No maximum price**; its finite internal rendering fallback never becomes a budget. Missing/loading/error cap disables the slider; request errors expose **Retry catalog controls**. Favorite resolution precedes facets; in-flight/cached facets deduplicate default bootstrap to two requests. Existing taxonomy/price data only; no schema changes or writes.

Ranking **`seed-feedback-v1`**: seed cosine + 0.15 × preferred-term fraction + 0.10 × nonnegative cosine to the normalized interested centroid − 0.10 × nonnegative cosine to the normalized not-for-me centroid. Each affinity is clamped to [0,1]; missing/cancelled centroids contribute nothing. Ties use app ID. Latest timezone-aware feedback wins per game; equal timestamps use the last action. Unknown feedback IDs contribute no affinity; exact exclusions still apply.

Already played excludes only the exact title. Not for me excludes that title and modestly downweights similar content. Interested does not cancel explicit exclusions. Filters run before shortlist limiting and are revalidated afterward. The API stores no guest profile and remains read-only. No new secrets are needed; configure the existing restricted `DATABASE_URL` locally, never in frontend variables or chat.

## Verification commands

From repository root in an installed locked backend environment:

```powershell
uv run --project backend --locked --extra dev --extra benchmark python -m unittest discover -s backend/tests -v
uv run --project backend --locked --extra dev --extra benchmark ruff check backend
uv run --project backend --locked --extra dev --extra benchmark python -m game_discovery.api.export_schema --check
```

From `backend/`, `uv run --locked --extra dev --extra benchmark mypy` uses the configured 13-module strict scope. The direct-Python standard-library venv path actually verified on this machine is in [setup](setup.md).

From an installed `frontend/` working directory, with port 4173 free for normal tests:

```powershell
npm run lint
npm run check:api
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run build
npm test
```

Normal tests exclude `live-*.spec.ts` and use fixtures, not database secrets. Current recorded result: **21 passed (15 browser + 6 storage)**, plus **51 Python tests**, Ruff, strict mypy (13 modules), OpenAPI drift, TypeScript/build, targeted ESLint and generated-type drift. The old 17/49 counts are completed-baseline evidence. The frozen-catalog verifier and route tests were removed.

### Explicit live M3 check

Requires the existing active catalog, ignored backend runtime configuration and a locked environment interpreter. The helper defaults to **8001**; `M3_API_ORIGIN` permits only **http://127.0.0.1:8001** or **http://127.0.0.1:8002**. Preview must be built for the selected origin. From `frontend/`, for the default :8001 path, build then keep preview running in a separate terminal:

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8001'
npm run build
npm run preview
```

In the test terminal, also with `frontend/` as working directory:

```powershell
$env:API_PYTHON = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv\Scripts\python.exe'
$env:M3_API_ORIGIN = 'http://127.0.0.1:8001'
npm run verify:m3
```

`playwright.live.config.ts` expects preview already running at 4173. The test refuses CI and an occupied healthy API at the selected origin; startup fails if it cannot bind. It starts/stops only its owned API process tree, sets its CORS origin to preview and reads the existing restricted PostgreSQL/pgvector catalog. The normal config does not manage preview. The **local-only execution wrappers** used with the existing C: tools now start a missing preview or reuse one, and stop processes they own; this is not a fresh install or a change to normal live-config behavior. No migration/import/publication. Normal dev still defaults to API **8000**.

The controls verification deliberately built for **8002** and set `M3_API_ORIGIN=http://127.0.0.1:8002` to avoid the owner's :8001 backend. For a future :8002 check, set the same origin in **both** build and test terminals; the selected API port must be free. **Main has already restored the final interactive build to :8001** after successful verification; test stopped owned :8002 without changing owner's :8001. Do not stop an unrelated backend to reclaim the test port.

Optional `M3_CAPTURE_DIR` changes captures (default `.impeccable/review/m3/`); optional `M3_REPORT_PATH` writes an additional report. Controls evidence is retained in [discovery-controls-live.json](reports/discovery-controls-live.json), with captures `.impeccable/review/discovery-controls/`. The baseline [m3-live-evidence.json](reports/m3-live-evidence.json) stays historical. Both JSON files are generated evidence, not hand-edited documentation.

Final retained controls results after the metadata fix: one live test, **nine API cases** (previous six plus range/multi-choice/free-only), real desktop/mobile guest journey with CORS; **18 refreshed scans**, axe 0/no overflow/zero page errors. Full 21 frontend tests passed again, including forced facets 503 with unbounded filters/preferences/persisted-null checks, zero normalization and legacy-term clearing. A transient search exceeded the old five-second assertion; the test now awaits its real response within the existing 75-second network budget, without autoretry; final run passed. Backend 51/Ruff/mypy13/OpenAPI/generated drift and detector `[]` remain passed. **One metadata-failure fix RESOLVED; ship at ONE-SCORED-FIX verdict-pass scope, main confirmed**. Historical baseline four-fix verdict stays separate. Actual E: source uses existing C: tools; fresh frontend install/remote M3 CI/real-phone remain unverified. This documentation pass did not rerun checks.

### Interactive preview after verification

The live check **stopped owned :8002** after successful controls verification; the owner's :8001 server was not changed. No persistent owned background API remains. **Main has restored the final interactive frontend build to API :8001**. This documentation pass has not rebuilt or started any service.

Normal dev uses API **:8000**; use the [setup backend command](setup.md#backend) and allow its frontend origin. The final :4173 preview build already targets **:8001**. Restart the older :8001 backend so it loads optional minimum/facet-maximum support. From repository root in a separate terminal:

```powershell
$python = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv\Scripts\python.exe'
$env:ALLOWED_ORIGINS = 'http://127.0.0.1:4173'
& $python -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8001 --workers 1
```

Leave that terminal open. Start/reuse preview **:4173** (`npm run preview` from installed `frontend/` if missing), then refresh both **http://127.0.0.1:4173/** and **http://127.0.0.1:4173/current-original.html**. Old API processes cannot serve the revised contract. Existing ignored `backend/.env` suffices; **no new credentials or migrations**. Local-only wrappers start missing preview/reuse existing and stop owned processes; normal source live config expects owner preview running. Future live checks need a free allowed API port and matching build. This is local operation, not deployment.
