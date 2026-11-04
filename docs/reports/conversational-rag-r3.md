# Conversational RAG R3 — public v2 state and browser integration

**2026-10-25 · Complete locally; stop before R4.** Owner explicitly approved R3 and confirmed frontend skills available. [Plan](../conversational-rag-plan.md) · [Frozen design](../conversational-rag-contracts.md) · [Browser checks](conversational-rag-r3-browser.json) · [Actual-catalog browser/API evidence](conversational-rag-r3-live.json)

## Implemented

- `ai/chat.py`: `/api/v1/chat` accepts bounded legacy state (no version) or an explicitly declared `version:2`. Omitted state retains the legacy default for old callers. `ChatStateV2Wire` requires the discriminator while inheriting the unchanged frozen domain state. Future/invalid versions, hidden main inputs and invalid provenance fail before inference. V2 callers receive full v2 state; old callers receive the legacy-compatible shape and quarantine behavior.
- Regenerated `backend/openapi.json` and `frontend/src/api/schema.d.ts` together. No permissive arbitrary state dictionary, database conversation persistence, new secret, dependency or migration.
- `frontend/src/chat-state.ts`: dedicated chat-neutral defaults (including **null minimum**, no main Windows/budget/mode defaults), bounded runtime validation, provenance/origin relationships, canonical-ID bounds/uniqueness, separate exclusions and legacy quarantine. Missing optional fields use neutral defaults. Unknown v2 fields/versions are rejected; no automatic downgrade.
- `assistant-session.ts`: the **same** `game-discovery:assistant` key now stores envelope version2. Fully validate v1 transcript/cards/draft/state before conversion; retain them, merge legacy exclusion fields into quarantine, preserve re-resolvable shown IDs and never invent origins. Successful conversion is validated before writing. Failed/blocked/corrupt/future/oversized data keeps its original stored copy and offers memory-only/reset guidance.
- Exact bounded `pending` request snapshots retain pre-turn state and context through trimming/reload. Retry reuses that snapshot, preserves any newer draft and does not append a duplicate visible user message. Success commits the returned state and clears pending. The API is stateless: this is **not server-side request deduplication**, and a retried inference can consume another normal reservation.
- 20 messages /2,000 characters each /12,000 total,12 cached cards,2,000-character draft,100 exclusions and500,000-character envelope remain enforced. Provenance survives transcript trimming without model summarization. New chat clears only chat; clear-device-data across tabs aborts/remounts and rejects obsolete responses.
- `FloatingAssistant.tsx` retains the approved curved interface, Save/Steam cards, plain-text answers, game-bearing notices, desktop nonmodal/mobile modal behavior and focus restoration. Only pending-request lifecycle changed. API validation/version-skew errors explain recovery while preserving the v2 session and pending turn.

## Acceptance evidence

| Check | Result |
| --- | --- |
| Backend tests | **151 passed**,7 new public-v2/legacy boundary tests beyond R2's144 |
| Frontend suite | **49 passed**,17 new R3 tests beyond the prior32; includes6 storage-domain cases and11 browser cases |
| Separate actual-network browser test | **1 passed**,6 successful v2 turns through real API/CORS/catalog/encoder |
| Ruff / strict mypy | Passed /25 source files |
| TypeScript / production build / targeted ESLint | Passed using existing C: dependencies against actual E: source; initial lint invocation ignored outside-base files, corrected E: cwd invocation checked them successfully |
| OpenAPI / generated TypeScript drift | Both checks passed after regeneration |
| Frozen R0 contracts/cases | Six tests and frozen hashes pass;40cases/53turns remain unevaluated |
| R3 UI scans | **6 axe scans:0 violations**, no horizontal overflow/page errors at1440×1000,390×844,320×844 |
| Mechanical detector | `[]` |

Browser tests cover full v1 migration and reload, protected/blocked storage, retained origins after trimming, malformed pending snapshots, overflowing legacy exclusion unions, multiplayer→Spider-Man facts/suitability→reload→more, played/undo state, exact retry after trimming/reload, drafts,422/old-response/invalid-provenance version skew, cross-tab clear during a pending reply, stale-response rejection, main isolation, cards/Save and keyboard focus.

The first suite run passed47/48 tests. Its single failure incorrectly expected main result objects to survive a full-page reload. Main intentionally does not cache that shortlist. The corrected test verifies no automatic discovery, identical main request/criteria, and identical results after explicit rediscovery; final49/49 pass. No UI change was made to satisfy that assertion. Type-check/test-message expectation corrections are reflected in the final checks.

### Actual browser → API → catalog/encoder

`serve_chat_r3_probe` is a developer-only loopback job, not a production endpoint/configuration. It serves the actual application on owned `127.0.0.1:8002` with the existing restricted repository and hash-verified pinned encoder. All Groq HTTP and budget reservations are mocked for its lifetime; only six exact scripted messages are accepted. Main AI is disabled. Its diagnostic endpoint exists only in this probe process.

[Retained evidence](conversational-rag-r3-live.json), catalog **`m2-649714e8b26775165f105d02`**:

1. Multiplayer returns canonical **105600 /548430**.
2. Immediate duplicate request returns actual **429 /Retry-After30**. Subsequent turns wait at least30.1seconds after the preceding response, without clock/throttle resets.
3. `spiderman` resolves to **1817070**, recorded single-player, with multiplayer mismatch and original criterion provenance retained.
4. Suitability uses the canonical recent reference and explains the mismatch.
5. Full-page reload restores transcript/v2 memory; more options still enforce multiplayer and origin user-turn1.
6. Played Spider-Man adds its canonical chat exclusion; include-again removes it. Final user-turn6, pending cleared after every success.

All **12 scripted provider HTTP calls** matched their **12 mocked reservations**, input packets≤12,000UTF-8 JSON bytes, existing transport timeout retained. **Four real semantic candidate queries** executed. Full main recommendations/effective criteria were identical before/after (ten canonical IDs retained in JSON). External artwork/web requests were blocked. Owned API was stopped and verified no longer responding; the final frontend build was restored to API **:8001**.

Six observed browser turns took **911–2,329ms** after the explicit throttle waits. These are small-sample scripted-provider UI observations, **not a live-model latency benchmark**, isolated orchestration overhead/RSS measurement or hosted proof. R2's historical resource measurements retain their original scope.

### Visual review and provenance

Builder opened all six final `.impeccable/review/conversational-rag-r3/{cards,recovery}-{1440,390,320}.png` captures. **PASS at R3 state-integration/recovery UI scope:** no material attributable visual regression observed; wrapping recovery text, reachable retry/composer, canonical card layout and desktop/mobile containment remain coherent. Lower card essentials/actions are visible in the recovery captures. This is builder review, **not a new independent reviewer SHIP verdict** or blanket product approval. Prior independent UI verdicts remain historical and scoped.

No palette/type/layout/CSS changes or new shipping raster assets. Captures use explicitly synthetic game/artwork fixtures; existing catalog artwork/font provenance is retained. Physical-phone/software-keyboard behavior was not tested.

## Reproduce

From repository root with the durable backend interpreter:

```powershell
& .\backend\.venv\Scripts\python.exe -m unittest discover -s backend/tests
& .\backend\.venv\Scripts\python.exe -m ruff check backend
& .\backend\.venv\Scripts\python.exe -m game_discovery.api.export_schema --check
& .\backend\.venv\Scripts\python.exe backend/experiments/rag_r0/freeze.py
& .\backend\.venv\Scripts\python.exe -m unittest discover -s backend/experiments/rag_r0 -p test_contracts.py
```

From `backend/`: strict `mypy` (existing C: cache if necessary). Normally from installed `frontend/`: `npm run check:api`, `npm run build`, `npm test`; targeted lint the changed source/tests. This machine used the documented C: source harness, local-only `playwright.r3-source.config.ts` and already installed Chromium1243, not a fresh E: dependency install or remote CI. The retained browser JSON records all49 final results.

For the actual-network probe, build preview for API:8002, keep preview:4173 running, ensure:8002 is free, then from `frontend/`:

```powershell
$env:API_PYTHON = 'E:/Games-Recommendation-System/backend/.venv/Scripts/python.exe'
npx playwright test --config playwright.r3-live.config.ts
```

Existing local C: equivalent uses its same-named local config with source/runtime resolution and Chromium1243. The test owns/stops only its probe process, waits the real throttle and writes the R3 live JSON. It requires the already configured actual catalog/encoder. Restore the preview build to API:8001 afterward. The helper is deliberately **not** a general-purpose fake AI service or live evaluation runner. R2 `verify_chat_rag` retains its legacy-API/historical evidence scope; its source's R2 boundary label is now explicitly dated.

## Handoff and limits

**R0–R3 complete locally; stop before R4.** Restart an older API and hard-refresh the rebuilt frontend together. Existing valid v1 sessions migrate in place; reset/restate old requirements with **Start over** or **New chat** before using them as active requirements. A new frontend against an old API preserves session/pending data and reports a compatible-service error; it does not lose provenance by downgrading.

No new key/configuration/model download/migration is needed. Preserve model cache files. No live inference, actual quota reservation, database write, environment-file edit, commit/push/deploy/M5. Daily50calls/500,000reserved tokens/four-per-minute,30-second peer throttle and existing concurrency/accounting/transport bounds remain.

Scripted interpretation/generation prove integration for validated plans, not live intent accuracy, relevance improvement, prompt-injection immunity or comprehensive factual-prose grounding. **R4 and any live-call budget need separate explicit approval.** Frozen held-out evaluation, manual answer judgments and hosted feasibility remain pending.
