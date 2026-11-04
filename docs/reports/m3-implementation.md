# M3 implementation and local acceptance — 2026-10-18

> **Historical completed M3 baseline.** The 49 Python/17 frontend counts, six live API cases, 12 scans and four-fix scoped ship verdict below describe M3 before the subsequent owner-authorized controls follow-up. See [current controls revision](discovery-controls.md): **complete locally, main confirmed**, with 51/21 checks, nine cases/18 refreshed clean scans and one metadata-failure fix **RESOLVED — ship at ONE-SCORED-FIX verdict-pass scope**, not blanket product/publication approval. Main restored final interactive build to :8001 after owned :8002 verification. Earlier control descriptions and :8001-only verification details below are historical. M3 stays complete/local/unpublished; M4 remains unstarted/unauthorized.

## Status and authority

**M0–M3 complete. M3 COMPLETE LOCALLY:** main agent confirms all five functional acceptance gates and final handoff. Independent reviewer marks all four material fixes **RESOLVED**, disposition **ship at the four-scored-fixes verdict-pass scope**. All 12 fresh captures were inspected with no material regression attributable to that fix batch. This is a scoped review pass, not blanket whole-product/UI release approval. No further implementation is needed for M3; M4 is unstarted and unauthorized.

The owner selected the exact Current visual, then explicitly authorized **“implement remaining M3 steps to complete it.”** This permitted a functional extension in that visual world. Both HTML entries load `current-original.tsx` → `GuestApp`; the earlier eight-game catalog, local genre-overlap sorter and frozen-page verifier/tests were removed. Earlier [exact-selection evidence](current-official-selection.md) remains historical.

Hosted M2 remains owner-confirmed and unchanged. M3 is local and unpublished. No commit, push, deployment or M4 work is authorized by these results.

## Implemented behavior

- Real API favorite search/resolution and explicitly submitted discovery; compact maximum-price/platform/required-genre controls, optional modes/terms/exclusions, source-backed genre-led rows, evidence and tradeoffs.
- `GuestApp`, `GuestDiscovery`, `GuestGameRow`, `GuestLibrary` and `guest-store.ts` preserve Current's cobalt/near-black/lime system with Anton/Manrope and the approved artwork picker.
- `/saved` caches minimal display metadata and correctly dated recorded prices; API failure does not erase saves. Artwork still depends on the image/network cache. Manual availability checks retain removed titles and cached observations.
- Version-2 validated browser storage: 50 favorites, 200 saves, 500 feedback entries and newest 20 history summaries. Defined ID-only v1 migration coalesces/revalidates latest feedback; corrupt/future/oversized storage is protected. Quota/blocked storage is truthfully temporary.
- Same-browser tab events plus read-before-edit/retry; clear removes owned local/session keys, restores defaults and invalidates pending work across tabs through epochs and a transient reset signal. No personal tombstone or full conversation archive.
- Save is separate from Interested. Already played excludes exactly that game without negative affinity; interested/not-for-me centroid contributions are bounded ±0.10. Explicit false/null/[] overrides saved preferences.
- Hard `required_genres` queries existing taxonomy; OpenAPI/generated types updated. No migration, database schema change or database mutation. No auth, new secrets, server-side guest profile or language-model processing.

## Recorded checks

These results were completed during implementation and supplied for this documentation handoff. This documentation-only pass did not rerun tests.

| Check | Recorded result and scope |
| --- | --- |
| Fresh backend environment | Standard-library venv at `C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv`; locked `uv sync --project backend --locked --extra dev --extra benchmark` installed 83 packages |
| Python behavior | Direct interpreter: **49 unit tests passed** |
| Backend static/contracts | Ruff, strict mypy **13 modules**, OpenAPI drift passed |
| Frontend compilation | Actual **E: source**, compiled using existing C: frontend tools with local-only Vite dedupe and TypeScript/test aliases; TypeScript and Vite production build passed |
| Frontend lint/contracts | Targeted ESLint over all E: source/tests/config and generated TypeScript schema `--check` passed |
| Normal frontend suite | **17 passed: 11 browser + 6 storage**; fixtures, live check excluded |
| Explicit live suite | **1 passed**, real browser → owned local FastAPI :8001 → restricted existing PostgreSQL/pgvector; actual POST CORS checked |
| Live UI scans | **12 states**: initial/favorites/results/evidence/saved/device-data × desktop 1440/mobile 390; axe **0**, no overflow, **0 page errors** |
| Mechanical source scan | Full targets before review `[]`; post-fix GuestGameRow/CSS `[]`; no new UI issues reported |
| Finish review | All four material fixes **RESOLVED**; **ship at the four-scored-fixes verdict-pass scope**. All 12 fresh captures inspected; no material regression attributable to the fix batch. Not blanket whole-product/UI release approval |

### Backend environment evidence limits

The initial uv-created launcher disappeared. No cause is asserted. A fresh standard-library venv plus locked sync and direct interpreter execution subsequently passed the checks above. This closes the earlier local backend install/typing blockers; it does not establish hosted runtime resource measurements.

E: frontend `npm ci` still times out. Compilation/testing used actual E: source through an existing C: toolchain, **not a stale mirrored application copy**. Local wrappers were execution aids, not committed setup or a fresh frontend install. No remote CI result is claimed for M3.

### Live evidence

[Retained generated JSON](m3-live-evidence.json), observed **2026-10-18T19:47:27.370Z**, records catalog `m2-649714e8b26775165f105d02`, ranking `seed-feedback-v1` and these six passing cases:

1. Hades baseline with Windows/single-player/≤$20 constraints.
2. Interested in Portal 2 changes order while constraints hold.
3. Already-played Bastion removes the exact game and preserves relative order of common remaining results.
4. Not-for-me Bastion excludes it and changes order beyond the already-played case.
5. Required RPG returns only games with the catalog genre.
6. Explicit current filters override saved preferences, including `free_only: false`.

The browser journey covers real search, ten discovery results, source evidence, save and feedback, rediscovery, saved navigation/reload and clear on desktop/mobile. Local captures and matching report are under `.impeccable/review/m3/`. It reads the existing catalog; it does not replay a fresh database. The live check starts and stops its owned API :8001; passing it does not leave an interactive backend running. The brief background-start attempt is not persistent in this harness. For interactive use, run the backend in a local terminal: normal development uses :8000; the current :4173 preview build targets :8001. [Commands](../operations-m3.md#interactive-preview-after-verification). Existing ignored `backend/.env` runtime configuration suffices; no new credentials are needed.

### Regression coverage and repaired findings

Normal browser/storage checks cover reload persistence, no-auth requests, hard filters and explicit clears, save/Interested separation, exact exclusions, removed IDs, offline saved metadata, bounded lists, v1 migration, corrupt/future/quota states, same-/other-tab clear races and unrelated-key preservation.

The independent review's four scored fixes are all **RESOLVED**:

- Retry rereads current shared device state before writing.
- Aborted discovery releases loading by request identity when criteria change and are restored.
- Saved availability releases its checking state independently of a ranking-ticket change.
- Migrated feedback is coalesced and revalidated through the v2 invariants.

The reviewer inspected all 12 fresh captures and found no material regression attributable to this fix batch. Its **ship** disposition applies to these four scored fixes at verdict-pass scope; it is not a blanket approval of the whole UI, product or release. Main agent separately confirms all five M3 functional gates and declares M3 complete locally. The recorded test/build/static/contract results remain passed; this documentation finalization did not rerun them.

## Functional acceptance evidence

- [x] Same-browser reload retains favorites/preferences/saves/history/feedback.
- [x] Controlled ranking cases prove bounded feedback changes and exact exclusions.
- [x] Already played does not imply dislike; explicit controls override saved values.
- [x] Local-persistence disclosure and clear behavior, including pending requests and other tabs, are checked.
- [x] No accounts/authentication introduced.
- [x] Main agent confirms final handoff review/verdict and declares M3 complete locally, with the review scope recorded above.

## Remaining limits and handoff

This is behavior/engineering evidence, not measured relevance improvement or a baseline evaluation. Natural-language/conversational discovery is M4 and unauthorized. Automated mobile viewport/axe checks do not establish physical-phone behavior. Hosted M3, fresh frontend installation and remote M3 CI are unverified.

[Operations and runnable verification](../operations-m3.md) · [setup](../setup.md) · [design](../../DESIGN.md). Final handoff is checked and M3 complete locally; stop here. Hosted M2 remains unchanged and M3 unpublished. Commit/push/deploy and starting M4 require explicit owner authorization.
