# Exact Current selection — local verification, 2026-10-18

> **Later scope note:** this report preserves the exact-selection snapshot before the owner subsequently authorized completing remaining M3. Its byte hashes, frozen catalog and verifier results are historical, not current-source guarantees. M3 is complete locally; see [M3 implementation](m3-implementation.md) and the subsequent owner-authorized [controls revision](discovery-controls.md). Hosted M2 remains unchanged.

## Outcome

The owner approved the exact existing `/current-original.html` without any
changes as the sole official design. Both `frontend/index.html` and
`frontend/current-original.html` now load the same selected implementation.
The superseded integrated UI, its styles/tests/scripts and active surface
briefs were removed. Backend/API clients and dated engineering evidence remain.

The selected page intentionally remains a frozen eight-game local demonstration,
with exact copy, initial Hades/Windows/$20, automatic shared-genre ordering,
compact dropdowns, artwork picker, genre metadata and reload-reset behavior.
Live integration and remaining M3 guest features are follow-up work.

## Unchanged source evidence

`git hash-object` returned the same hashes before and after promotion:

| Selected file | Before and after Git object hash |
| --- | --- |
| `frontend/src/current-original.tsx` | `50a89680eda502a56071cd1f163c15cf8c989e1c` |
| `frontend/src/current-original.css` | `04d1364f0609b5ebbdcf735c22735ca6d7ac2709` |
| `frontend/src/current-original-catalog.ts` | `08381306df413305cd63b00be601b6efd8a95465` |
| `frontend/src/Icon.tsx` | `7f748c65e4a03f7242a80757f847ed3656d0588e` |
| `frontend/current-original.html` | `dbb6de935233ed3210dc74784fd7e0d42ebc8c0b` |

`frontend/index.html` now has the same hash as `current-original.html`.
Selected source, entries, verifier, tests, Vite configuration and retained API
source hashes matched the C: execution copy used for verification.

## Executed checks

- `npm run build`: TypeScript and production Vite build pass; the build produces
  both HTML entries and one shared selected-page JS/CSS implementation.
- `node node_modules/eslint/bin/eslint.js src scripts/verify-current-original.mjs tests/current.spec.js vite.config.ts playwright.config.ts eslint.config.js`:
  passes. An initial `npx eslint ...` invocation timed out; the direct local
  executable succeeded without installation or dependency changes.
- Existing `verify-current-original.mjs`, before promotion: passed against the
  exact approved URL to record fresh comparison evidence.
- Same verifier after promotion with `STUDY_PATH=/` and then
  `/current-original.html`: both pass with real source artwork and baseline
  comparisons enabled. Each run covers initial ordering, explicit search,
  keyboard toggles, selected counts/chips, search alignment, reduced motion,
  budget/platform/genre constraints, empty/reset, exclusion/undo, evidence,
  results focus and reload reset.
- Per real-artwork route: **13 axe scans with zero violations**, no horizontal
  overflow at 320/390/768/1000/1440px, zero page errors and zero application API
  requests.
- For both routes: initial desktop/mobile geometry matches exactly; initial
  full-page, expanded-favorites full-page and cropped-picker PNGs are
  **byte-identical** to their matching approved baseline PNGs.
- Frontend browser suite: **2 passed**, one complete verifier journey per route,
  using mocked artwork and blocked external HTTPS traffic. Executed using a
  temporary local Playwright configuration against the existing preview server;
  that temporary file was removed. The committed configuration retains its
  normal managed-preview startup.
- Mechanical detector: `[]`.
- Independent read-only preservation review inspected all 18 required baseline
  and after screenshots: **ship**, no material fixes for this exact request.
- `git diff --check`: passes; Git emitted only existing LF/CRLF conversion notices.

## Local evidence

Ignored review files are retained locally, not shipped as application artwork:

- `.impeccable/review/current-official-before/`: approved baseline report and PNGs.
- `.impeccable/review/current-official-root/`: `/` report and PNGs.
- `.impeccable/review/current-official-original/`: original URL report and PNGs.

Each after directory includes `report.json`, desktop/mobile full pages,
expanded-favorites full pages and picker crops. The verifier asserts equality
before writing its successful report. Two-route test outputs are local to the
execution copy's Playwright results directory.

## Scope

Verification used the documented source-matched C: execution copy because the
E: dependency installation is incomplete. This is not a fresh locked-install,
remote CI, real-phone, live API integration, relevance or deployment result.
The original study restoration was reconstructed earlier; unchanged source here
means the exact existing page approved on 18 October, not recovered deleted bytes.
Hosted M2 and provider/database settings were not changed. M3 remains incomplete;
M4 is unauthorized. No commit, push or deployment was performed.
