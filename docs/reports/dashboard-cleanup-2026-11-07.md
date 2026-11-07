# Dashboard cleanup — 2026-11-07

Implemented the owner's requested copy removals, wider genre plot, compact developer list and removal of the observed/About-this-snapshot panel. Impeccable was explicitly reconfirmed.

## Subsequent request — discount hover and coverage wording

The owner subsequently requested hover values on the discount chart and removal of all dashboard “known/unknown” coverage text. The proportional strip now uses the same lazy Plotly engine as the other interactive plots, showing the discount range, count and percentage on actual pointer hover; its native counted legend still works if the chart chunk fails. Seven plots now load Plotly; developers remain native. Removed the obsolete CSS strip rules and the coverage-rendering helper. Header metric values and underlying coverage/analytics remain unchanged; unavailable averages use an accessible em dash rather than invented zero values. The word-cloud method option remains.

Final-source lint/APItypes/TypeScript/Vite and five focused dashboard checks pass (43.8seconds). The focused checks exercise hover across all six positive discount buckets. The extended full-source suite then passed **81/81 in one4.0-minute run** (shell `sh_1b704934b001q2ou6GcpPmzWFm`), including pointer-hover values at1440/390/320, axe0/no overflow and retained label containment. The earlier81/81below remains the preceding cleanup's separate evidence. No backend changes or generation were made.

Initial simultaneous shell attempts exited before useful output under low machine-memory headroom; subsequent checks ran sequentially. A final capture-only extension scrolls to the plot before hover and captures the plot rather than the whole article, preventing screenshot scrolling from dismissing narrow-width tooltips; it also explicitly asserts hover text visibility. Its first combined foreground confirmation exceeded the120-second command limit, without a reported assertion failure. A separate responsive confirmation then passed **1/1 in49.8seconds** with a process-only150-second test timeout; the builder opened all three actual visible-tooltip captures. This test-only capture/assertion extension followed the full81run; UI runtime source is identical. The timeout remains retained, not relabeled. The manual detector returned `[]` for the follow-up implementation.

Final local confirmation passed against the actual API with no mocks/generation: seven ready plots, hover values, no known/unknown wording, retained cloud method option,125%scale,2,000games and unchanged analytics digest; zero page/API errors. Receipt: ignored `data/reports/dashboard-hover-final-20261107.json`. The existing4173preview is updated against the unchanged8002API, without a service restart. Previous HTML entries are backed up at `C:/Users/User/AppData/Local/Temp/opencode/dashboard-hover-preview-backup-20261107/`; old hashed assets remain. Neither this cleanup nor the hover follow-up is committed, pushed or deployed. No physical-phone, other-engine or live chat-fix acceptance is claimed.

The owner's eFootball screenshot was investigated read-only using its saved trace and independent catalog reads. Lookup actually found the game; malformed post-tool prose was rejected, while a later evidence-free reply bypassed retrieval and falsely denied catalog presence. A separate literalTM-versus-™search discrepancy was also confirmed. [Diagnosis and proposed general correction](efootball-catalog-diagnosis-2026-11-07.md). That backend correction is proposed, not implemented.

- Removed the specified recorded-price paragraph, developer-normalization sentence, description-theme caveat and both donut denominator sentences. Calculations and visible percentage/count labels are unchanged.
- Removed all chart value/coverage disclosure controls. **View word counts and method** remains, with the same 60 terms and method.
- Screen-reader data remains available in visually hidden tables. If a Plotly chunk fails, those tables become plain visible fallback data without disclosure controls; native discount/developer lists remain usable.
- Genre X-axis automargin is disabled to extend the drawing toward the right, retaining Y-axis label margins and count clearance. Three-width checks bound the right margin to54px and retain value/month/platform-label containment.
- Developer rows use aligned label/track/count columns on desktop; mobile labels wrap above tracks. The ten-row desktop list fits within480px without reducing text size.
- Deleted the removed panel's dead CSS. Current's header/metrics,125%scale, catalog data, saves/chat, backend, dependencies and accounting are unchanged.

## Verification

- Standard lint and generated API checks passed. TypeScript/Vite build passed after correcting an unsupported flaglist type in the pinned Plotly typings; no dependency/type-guard workaround was introduced. An initial foreground build timed out and is not counted as a pass.
- A later lint rerun also picked up the separate local-preview build directory and failed on generated bundles. That exact generated directory was moved outside the source harness (preserved, not deleted); final ordinary `npm run lint` and `npm run check:api` both pass without ignore/config changes.
- **5/5 focused dashboard checks passed in one1.2-minute run**, including download-failure fallback, requested removals, word-count disclosure, real hover/zoom/reset/keyboard legends, year changes, refresh/storage isolation and long-name wrapping.
-1440/390/320: axe0, no page overflow/page errors, contained plot values and visible month/platform/price labels; month labels remain nonoverlapping. Captures: ignored `data/reports/dashboard-cleanup-20261107/`. Builder opened the changed genre/developer views at all three widths, desktop/narrow headers, both desktop donuts and the narrow cloud; no independent reviewer or physical-phone claim.
- Mechanical detector returned `[]` before the one-line typing correction. Source/tests/packages matched the existing C: harness across40files. No fresh dependency install was attempted. The existing Plotly bundle-size warning remains.
- Actual-network **local** browser check passed with no API mocks/generation: six ready plots,2,000games, unchanged analytics digest `5116c42f8dc97f6e2556f8789aeb664e6c7ae02c070ec1466936d4fdf8472a83`, retained125%scale, removed panel, word-cloud disclosure and zero page/API errors. Receipt: ignored `data/reports/dashboard-cleanup-local-network-20261107.json`.
- Final-source **81/81 frontend tests passed in one3.0-minute run**, confirmed by the completion notification for shell `sh_1b4c197b6001uy17G4unyoa7l5`; no failures/skips or earlier-release substitution. The five-check JSON remains separate and was not overwritten.

## Inspection and release boundary

Open **http://127.0.0.1:4173/dashboard** and hard-refresh. The identity-verified existing preview now serves this generated build against the existing local API:8002; neither service was restarted. Previous HTML entries were backed up to `C:/Users/User/AppData/Local/Temp/opencode/dashboard-cleanup-preview-backup-20261107/`, and all old hashed assets remain untouched.

No commit, push, deployment, database/configuration/dependency change, AI call or evaluation replay. The public site remains the November6 release. Physical phones, other engines and hosted checks were not run for this local-only cleanup. Pre-existing design-sidecar drift remains unrepaired.
