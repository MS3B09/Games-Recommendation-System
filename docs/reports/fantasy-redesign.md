# Fantasy frontend replacement — local verification

> **Historical evidence only — superseded, not an active design (2026-10-18).** The owner approved the exact existing Current page without changes as the sole official design and requested deletion of other designs. See [DESIGN.md](../../DESIGN.md) and the [selected-source record](../../frontend/CURRENT_ORIGINAL.md). The Fantasy/integrated UI and its old frontend smoke commands were removed locally. Checks, assets, implementation descriptions and reproduction commands below record the 2026-10-15 state; they are not current frontend results or runnable acceptance instructions. Hosted M2/backend evidence remains valid history. Official-route verification is underway; live reconnection and M3 guest UI remain pending.

Date: 2026-10-15. **Implemented and locally verified; not published or deployed.** M3 remains in progress. The owner explicitly chose to redesign existing features first, keeping remaining persistence/saved-games/feedback UI pending.

## Reference and design outcome

The owner selected the installed [Fantasy guidance](../../.opencode/skills/fantasy/DESIGN.md) and supplied:

- https://fantasy-typeui-494377f0.vercel.app/marketing
- https://fantasy-typeui-494377f0.vercel.app/application
- https://fantasy-typeui-494377f0.vercel.app/ecommerce

All three pages were visited, captured and inspected with Playwright at desktop and 390px mobile. They are visual-language references rather than exact game-discovery layout comps. The application reference itself has mobile overflow; that behavior was not copied. The actual examples' dark surfaces take precedence over the generic skill's white-surface default, consistent with this project's dark image-rich requirement.

| Reference feature | Local implementation |
| --- | --- |
| Near-black canvas, navy panels, thin blue edges | Shared shell, criteria, catalog-context, cards, detail facts and service panels |
| Gold New Rocker display and blue primary actions | Headings, wordmark, primary discovery/retry/store actions |
| Readable sans-serif body beside expressive headings | Existing self-hosted Manrope retained; IBM Plex Mono reserved for measurements |
| Application work-area density and ecommerce image inventory | Existing favorite/filter workflow plus artwork-led shortlist and detail layout |
| Compact familiar controls | Native inputs, selects, checkboxes and evidence disclosures; no new component dependencies |

At that time this replaced the prior parchment-action identity, and DESIGN.md and its sidecar recorded that system. Those active documents now describe only the selected Current source. Brand title remained temporary. No npm dependency or architecture change was introduced by the historical Fantasy replacement.

## Functionality preserved

Search and bounded favorite selection; inclusive recorded-price/free-only/platform-any-all/mode/preferred-unwanted-genre filters; explicit exclusions and undo; capped ranked results; source evidence, tradeoffs, price dates and Early Access; Steam links; direct game details and reload; initial, busy, empty, failure and recovery states; request cancellation; connection/status/docs and unknown-route recovery.

Frontend generated contracts now reflect existing local M3 backend additions. Response validation accepts both hosted M2 `seed-v1` and local `seed-feedback-v1`, preserving compatibility without adding guest feature UI. Backend behavior, migrations, catalog and credentials were not changed by the redesign.

## Executed checks

| Check | Result |
| --- | --- |
| TypeScript + Vite production build | Pass |
| Generated OpenAPI frontend drift check | Pass |
| ESLint on all repository source, tests, scripts and config | Pass |
| Playwright browser suite | **13 passed**: previous 11 plus two targeted redesign/regression checks |
| Real browser → local FastAPI → restricted PostgreSQL | Pass: Hades seed, Windows, single-player, recorded price ≤1999 cents; ten recommendations |
| Real evidence and game-detail direct reload | Pass |
| Real desktop/mobile axe | **0 / 0 violations** |
| Real uncaught browser errors | **0** |
| Horizontal overflow | None at 320, 390, 760, 1024, 1440px in behavior checks; none in real final desktop/mobile discovery/detail/system captures |
| Keyboard / reduced motion | Enter submits and opens native evidence; skip link/focus retained; reduced motion removes authored press transition |
| Unavailable/malformed/stale responses, long titles and detail retry | Pass in controlled browser cases |
| Impeccable mechanical detector | `[]` |
| Independent read-only finish review | **ship**, local visual replacement scope; no required UI fixes |
| Documenter validation | Token/reference/JSON checks, ten current sidecar previews at desktop/mobile, no preview overflow and visible keyboard focus |

The initial missing-favicon 404 was corrected with an authored SVG. Final manual local navigation produced no console errors. Browser tests and axe are evidence, not exhaustive assistive-technology or physical-phone certification.

## Local evidence

Ignored captures in `.impeccable/review/`:

- `fantasy-{marketing,application,ecommerce}-reference.png` and corresponding `-mobile-reference.png`: supplied websites.
- `fantasy/desktop.png`, `mobile.png` and `desktop-viewport.png`, `mobile-viewport.png`: actual constrained results with first evidence disclosure expanded.
- `fantasy/empty-{desktop,mobile}.png`: initial discovery, not fabricated recommendations.
- `fantasy/detail-{desktop,mobile}.png`, `system-{desktop,mobile}.png`: real detail and connection screens.
- `fantasy/report.json`: actual existing real-stack smoke report, including version, result IDs/prices, filters and accessibility counts.

Artwork comes from the existing source-provided Steam header URLs. No raster asset was added to the application. New Rocker and IBM Plex Mono font distributions, origins and SIL OFL licenses are in `frontend/public/fonts`; the favicon and interface icons are authored SVGs.

## Reproduce

From a normally installed `frontend/` checkout:

```powershell
npm run lint
npm run check:api
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run build
npm test
# Stop any existing local processes on 8000/4173 before the owning smoke script.
$env:API_PYTHON = 'PATH_TO_YOUR_BACKEND_ENVIRONMENT\Scripts\python.exe'
$env:M2_CAPTURE_DIR = 'E:\Games-Recommendation-System\.impeccable\review\fantasy'
npm run smoke:discovery
```

On this machine E: has an incomplete frontend dependency installation. Verification used the documented C: execution copy at `C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m1\frontend`, synchronized with current source, assets, tests, config and adjacent non-secret backend OpenAPI. Its preexisting `check-hosted.mjs` and `verify-swagger.mjs` scratch files cause blanket `npm run lint` errors; the actual repository has neither file. The equivalent all-project-target check used was:

```powershell
npx --no-install eslint src tests scripts eslint.config.js vite.config.ts playwright.config.ts
```

For the real smoke, the earlier backend launcher issue was worked around with Python 3.13.12 at `D:\miniconda-installer\miniconda\python.exe` and `PYTHONPATH=E:\Games-Recommendation-System\backend\src;C:\Users\User\AppData\Local\Temp\opencode\game-discovery-cloud-venv\Lib\site-packages`. This does not establish a fresh locked install. `PLAYWRIGHT_BROWSERS_PATH` used the existing C: browser cache. Existing ignored backend configuration supplied the restricted connection; no secrets were displayed or copied into the frontend cache.

## Remaining limitations

- M3 browser persistence, saved page, bounded history, feedback controls and reset/storage-race verification remain pending by owner choice. Prior backend strict typing/fresh-install checks also remain open.
- Mobile criteria remain a long vertical flow, especially with all advanced controls expanded. The reviewer accepted this within the current preserved workflow.
- Source header artwork is soft when enlarged on a large detail page; its provenance/resolution was preserved.
- Physical-phone software keyboard, safe areas and touch feel require actual hardware. Browser resizing does not verify those effects.
- This report makes no hosted-redesign, full-product, M3-completion or recommendation-quality-improvement claim. No commit, push or deploy was performed.
