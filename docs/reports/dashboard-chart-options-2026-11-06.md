# Dashboard chart options — 2026-11-06

**Subsequent owner decision:** the owner supplied nine selection screenshots and requested implementation in Current: centered-total free/paid donut, price columns, discount share strip, retained release/genre section, retained platform stacks with Linux label, retained review donut, developer lollipops and retained cloud/header. Unknown/zero chart statistics and numeric low-review-count labels are hidden in presentation; donut percentages/bar counts must remain visible. The chooser below is retained as the selection artifact, not the current production implementation. [Selected implementation evidence](dashboard-selected-2026-11-06.md).

## Purpose and opening the file

An owner-choice review artifact in the established **Current** world, not a new design world or production dashboard change. The original three-task release is owner accepted per the latest coordination; stale November 5 pending statements in older context do not reopen it.

- Relative path: [`docs/design/dashboard-chart-options.html`](../design/dashboard-chart-options.html).
- Absolute path: `E:\Games-Recommendation-System\docs\design\dashboard-chart-options.html`.
- Double-click the HTML file, or open `file:///E:/Games-Recommendation-System/docs/design/dashboard-chart-options.html` in a browser. No server, install or live API is needed; JavaScript must be enabled.

Eight charts plus description themes each offer four alternatives: **36 working previews**. Option A restores the previous thin lime bars with full labels and right-aligned counts for the eight charts; description themes A retains the word cloud. These are native SVG/CSS design previews, **not Plotly zoom demonstrations**. The four headline metrics are untouched.

## Four alternatives per visualization

| Visualization | A | B | C | D |
| --- | --- | --- | --- | --- |
| Free vs paid games | Classic lime bars | Donut + counted legend | Proportional share strip | Vertical columns |
| Games by price range | Classic lime bars | Vertical columns | Lollipop ranking | Proportional share strip |
| Games by discount | Classic lime bars | Vertical columns | Lollipop ranking | Proportional share strip |
| Games released by month | Classic lime bars | Vertical columns | Filled monthly line | Month intensity tiles |
| Top 15 game genres (12 available) | Classic lime bars | Lollipop ranking | Vertical columns | Ranked count table |
| Supported platforms | Classic lime bars | Horizontal coverage stacks | Grouped support columns | Support count matrix |
| Review type distribution | Classic lime bars | Donut + counted legend | Lollipop ranking | Vertical columns |
| Top 10 developers by game count | Classic lime bars | Lollipop ranking | Vertical columns | Ranked count table |
| Description themes | Frequency word cloud | Ranked word bars | Counted word index | Word frequency tiles |

## Data, selection and visual boundaries

- Embedded recorded **2,000-game November 5, 2026 snapshot** from `frontend/tests/analytics-fixture.json`, catalog `m2-cd9790b88f91370e69dae895`, analytics SHA-256 `5116c42f8dc97f6e2556f8789aeb664e6c7ae02c070ec1466936d4fdf8472a83`. Saved final verification checks every embedded category/count, platform state, release year and all 60 words against that fixture. It is not live Steam data or pricing.
- Exact-value disclosures retain labels, counts and missing-data context. Genre/developer membership can overlap. Linux(SteamOS) means source-verified Linux support, not independently verified SteamOS/Steam Deck compatibility; word occurrences are not game counts or gameplay claims.
- Select one native radio per section, then use **Copy choices** or **Download choices** and share the list. No option is preselected. Clipboard denial selects the summary for manual copying; download produces `dashboard-chart-choices.txt`.
- Choices live only in page memory and are lost on reload/close. Clear affects only this page. No application storage, cookies, taste, saves or chat are read or written. Release-year selection updates all four release previews and the exact table while retaining the chart choice.
- Current's cobalt/navy/lime, flat hairlines and Anton heading character remain. Anton optionally loads from the repository-local `frontend/public/fonts/Anton-Regular.ttf`; moved files use sans-serif fallback. Body text declares Manrope Variable but uses system sans-serif unless that font is installed. No external font/CDN is required.
- This file uses normal browser scale; production's 125% root setting is unchanged. Plot colors and type sizes are prototype-local, not new global tokens. No shipping raster assets were introduced.

## Verification and finish review

**Saved builder evidence, not rerun by this documenter:** `data/reports/dashboard-chart-options/verification.json` records **12 checks PASS**, axe **0**, no page overflow at **1440/390/320**, no JavaScript page errors and no live API/CDN traffic. Checks cover fixture equality, zero/count scales, synchronized year updates, native keyboard selections, export, copy fallback, value reading, clear and reload behavior.

The initial failed run remains in `data/reports/dashboard-chart-options-initial/`: copied 2007 July/August data, the nested release-year label and duplicate landmark names failed. All eight review findings were then fixed in one batch; the final evidence above is separate and does not relabel the initial failure.

**Supplied reviewer result:** the reviewer examined final source, verification and **13 final captures**, scored **all eight findings RESOLVED, zero partial/unresolved**, and returned **“ship — scoped to eight fixes and chart-selection review artifact”**. This is not broad product or owner approval, nor production/deployment authorization. This documenter did not reopen captures or independently repeat that visual verdict.

**Supplied detector history:** one initial detector run warned about the Manrope family; the declaration was corrected and the actual fallback disclosed. Plot-type colors/type sizes remain prototype-local advisories. No second detector scan is claimed.

### Reusable focused check (not executed in this documentation pass)

From the repository root, using normally installed frontend Playwright/axe dependencies and an installed Chromium:

```powershell
node docs/design/dashboard-chart-options.check.mjs
```

An optional positional path resolves packages from an existing frontend installation:

```powershell
node docs/design/dashboard-chart-options.check.mjs 'C:\path\to\frontend\package.json'
```

Optionally set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to an installed browser executable before running. The saved run used the existing source-matched C: dependency harness/browser, **not a fresh install or the full application suite**. The script writes its report/captures under `data/reports/dashboard-chart-options/`; preserve initial evidence separately.

## Documentation audit and next action

This documenter read the final HTML, surface contract, reusable check, final and initial verification JSON, fixture header, `PRODUCT.md`, incumbent `DESIGN.md`, `docs/README.md` and Impeccable's document reference/context. Test execution and the reviewer/detector observations above are attributed evidence, not new checks performed here.

Only this report, a completed surface handoff and one index row were changed. No HTML/test/app/backend/data/environment/quota/dependency/inference/publication changes, commits, push or deployment; global design files and historical reports remain untouched.

**Historical next action at chooser completion:** await owner chart choices before production changes. Those choices were subsequently supplied as recorded above.
