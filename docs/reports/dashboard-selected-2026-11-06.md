# Owner-selected dashboard charts — 2026-11-06

## Selected implementation

The owner supplied nine screenshots after reviewing the [36-option chooser](dashboard-chart-options-2026-11-06.md). This is the implementation of those choices in Current, not another design proposal.

| Area | Selected treatment |
| --- | --- |
| Header metrics and section navigation | Preserved, including the existing coverage in the four metrics |
| Free vs paid | Donut with centered displayed total, side-by-side counted legend and visible percentages; stacks on mobile |
| Price ranges | Periwinkle columns with visible counts |
| Discounts | Proportional share strip and counted percentage legend |
| Releases and genres | Existing filled monthly line/year selector and lime ranked genre bars; visible bar counts |
| Platforms | Existing supported/unsupported stacked columns, visible counts and readable **Linux** display label |
| Reviews | Existing donut/keyboard legend, visible percentages; sentiment categories only |
| Developers | Full-label native lollipops with visible counts |
| Description themes | Existing weighted cloud and counted alternative preserved |

Unknown and zero-value statistics are omitted from chart/table presentation. Numeric `x user reviews` labels are omitted from the review distribution. Source aggregates, the API response and header metrics are not rewritten. Review percentages use the **1,995 displayed sentiment summaries**, not all 2,000 raw summaries; the displayed-category denominator is disclosed. Discount percentages use the 1,608 displayed valid discounts. Browser legend toggles retain the stated original displayed-category denominator.

The monthly line retains all twelve calendar positions and the actual zero baseline, preventing an invented connection between nonadjacent months. Zero-value points and table statistics are not presented. Axis zero baselines remain valid scales, not extra data categories. Linux is a display-only label for recorded Linux support; independent SteamOS/Steam Deck compatibility remains unverified.

## Boundaries

- Current palette, Anton/Manrope, header, navigation, **125% root scale**, shared catalog and independent assistant remain intact.
- Native strip/lollipop need no Plotly download; six remaining plots retain lazy Plotly, actual hover/zoom/reset and keyboard donut controls. Exact-value tables remain available if the chart chunk fails.
- No dependency, backend, API schema, database/catalog, model, quota or environment-file change; no LLM calls or accounting resets.
- Plotly's existing approximately385kB gzip dashboard-only bundle and ordinary Vite chunk warning remain. The upstream public MIT notice is unchanged.

## Verification and retained failures

Standard lint, generated API checks and TypeScript/Vite production build passed. Existing frontend tests were extended rather than adding another suite. They check selected types, visible numbers, hidden unknown/zero/low-review labels, truthful percentage denominators, nonzero-unknown refresh, preserved header/cloud, year changes, real hover/box zoom/reset, native keyboard legends, download failure and device-data isolation.

The first full run passed80/81: the new percentage assertion counted both a Plotly SVG group and its nested text. The test now selects `text.slicetext`. An added number-containment check then found the largest genre count clipped on narrow layouts; reserved right space fixes it. These failures remain in managed logs and separate reports, not relabeled passes.

A later full local run passed **81/81 in3.7minutes**, saved at `data/reports/dashboard-selected-release-tests-20261106.json`, before the final monthly-axis refinement. A fresh reviewer inspected17captures and found final X-axis labels disappearing, including Linux and Oct–Dec. Explicit tick-label overflow restores them; the reviewer then marked320px monthly crowding partial. Monthly X-axis automatic margin growth is now disabled while Y-axis automargin remains, with explicit scaled32px-left/14px-right margins. No typography shrinking or month hiding was used. Intermediate overlap/December-clipping diagnostics remain in managed terminal history.

**Final-source focused confirmation:** all **five dashboard checks pass in one53-second run**, after standard lint/APItypes/TypeScript/Vite pass. At1440/390/320: axe0, no page overflow, every platform/positive price bin/month label visibly present and contained, adjacent month labels nonoverlapping, and donut/bar numbers contained. Native long developer names remain readable. Final captures are under `data/reports/dashboard-selected-axis-confirmed-20261106/`; the reviewer opened all three final monthly captures and scored the original axis issue **RESOLVED**, disposition **ship — ONE-axis-fix scope only**. This is not whole-product, owner or hosting acceptance. Unaffected selected-chart captures remain valid in the preceding `dashboard-selected-final-20261106/` and `dashboard-selected-release-20261106/` directories.

Detector `[]` ran once before final margin/axis fixes; it is not claimed as a post-fix scan. A configured-secret scan of10changed/candidate files found0secrets before these final documentation writes. No backend/dependency/generated-schema diff. Execution reused the existing C: dependency/Chromium harness, not a fresh installation. Physical phones and other browser engines were not checked; no new backend suite or live assistant evaluation was run.

## Documentation and publication

The delegated documenter hit its usage limit without writing files, so the builder completed this narrow documentation audit inline using Impeccable's documenter guidance. Source components, CSS, tests, contract and incumbent DESIGN.md were compared; no new tokens/world or raster assets were introduced. Existing historical/sidecar drift was not repaired or canonized. The chooser is retained as decision evidence.

The original owner workflow authorizes implementation and deployment after selections. **Commit/push/final CI and connected Netlify/FastAPI Cloud publication are pending at this local snapshot.** Do not treat the earlier full81run as a fresh final-source full-suite run. Final source CI, both deployment revisions, actual hosted chart interactions, unchanged analytics digest and public license verification will be recorded in ignored `data/reports/dashboard-selected-final-release.json` and `data/reports/dashboard-selected-hosted-20261106/verification.json`, avoiding recursive commits solely to add their own SHA.
