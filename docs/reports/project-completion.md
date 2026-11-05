# Hosted release — published; acceptance incomplete

**2026-11-05:** the requested source is published and the expanded catalog/dashboard are live. **Do not mark the project complete:** the one fresh hosted assistant smoke failed answer validation, and final owner acceptance has not occurred.

## Live destinations

- [Application](https://steam-discovery.netlify.app/) · [Dashboard](https://steam-discovery.netlify.app/dashboard)
- [API documentation](https://steam-discovery-api.fastapicloud.dev/docs)
- [Source](https://github.com/MS3B09/Games-Recommendation-System)

## Release identity

- Shared active catalog: **`m2-cd9790b88f91370e69dae895`**,2,000eligible games/all original40,2,000384D vectors/metadata documents. Discovery/chat catalog tools/dashboard use this same active database generation.
- Analytics: four metrics/eight charts/60-word cloud; digest `5116c42f8dc97f6e2556f8789aeb664e6c7ae02c070ec1466936d4fdf8472a83`. Linux(SteamOS) describes verified Linux support, not independently verified Deck compatibility.
- Source release `c50f5d4`, loaded-artifact diagnostic `bb93118`, activation handoff `d9796e4`, CI race correction `a76fc58`. Later handoff-only commits do not change the runtime.
- Backend was deployed and the exact expanded semantic artifact verified **before** shared activation. First manual deployment `782ae973-8bf6-4b23-b8c3-3fd102897f6e`; connected deployment `63d01067-e4c9-46dc-be09-4fd1d56ab121` succeeded at `a76fc589beb76f3974f37793af06c2a235a1c983`.
- Matching Netlify production deployment [`6aece40f87f179a62545bc26`](https://app.netlify.com/projects/steam-discovery/deploys/6aece40f87f179a62545bc26) published from that SHA. Final handoff-only push/deployment receipt is retained locally rather than recursively committing its own SHA.
- Existing FastAPI Cloud Hobby/min0-max1/nano, one startup server process; normal **50calls/500,000reserved units/day**. No paid resources, second database, quota resets or request-time model download. Netlify account plan/settings are owner-confirmed Free, not independently authenticated; public deployment receipts were inspected.

## Verification

| Area | Actual result |
| --- | --- |
| Backend CI | [42101069716](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42101069716) passed:299checks OK/1historical skip, Ruff, mypy, OpenAPI. Backend tree unchanged by subsequent test/docs commits. |
| Frontend CI | [42101815353](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42101815353):80/80passed, clean npmci/lint/generated types/TS+Vite/fresh Linux Chromium. Earlier79/80run retained; test now awaits response persistence before reload. |
| Hosted API | Ready2k/semantic+AItrue/exact loaded version; analytics digest, facets, expanded-only OuterWilds detail, last50games, constrained favorite recommendations and exact local/hosted OpenAPI match. Netlify-origin CORS passes. |
| Hosted browser | Real network/no mocks/no inference: explicit discovery, canonical saved card, direct saved reload/persistence; all13dashboard items, release-year selector/exact values, all4direct routes/reloads/favicon.125%scale preserved. |
| Hosted responsive/a11y |1440/390/320dashboard:0axe violations/no horizontal overflow; mobile assistant bounds pass;0page/API errors in the no-inference journey. Four captures inspected, plus actual chat-error capture. Chromium automation, not physical-phone/other-engine acceptance. |
| Portable artifacts | Independent89-package backend install/actual384Dencoder; licensed83,279,503Bwheel and original pinned model/tokenizer hashes; fresh build-time downloads verified. Models/secrets/private capabilities not published in Git. |
| Safety |1,391tracked-file configured-secret scan clean before release; runtime role/readiness/RLS maintained.3existing archives/99,155logical bytes remain;0pending; owned preview schema removed. Security advisories empty;2pre-existing informational [unused-index notices](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index) retained. |

## Hosted assistant smoke — failed, not retried

One new browser conversation asked for the OuterWilds catalog card and a short recorded description. Actual HTTP**502 `chat_invalid_answer`**,6,897.868ms; UI displayed the friendly edit-message recovery. **No assistant answer/card was delivered.** This does not pass hosted assistant integration, reload/history or Newchat acceptance.

- Two actual metered calls/22,232new reserved units; no automatic/manual retry, refund, reset or guard relaxation. Nov5total is **5calls/53,118units** including the earlier local3-call successful smoke.
- Owned test archive erased; independent history404confirmed. Original user archives and usage retained. No pending/background evaluation.
- Runtime logs establish guarded rejection, not the precise internal validation cause. The probe erased its archive before exporting its private attempt trace; that diagnostic detail is unavailable. Do not invent a root cause or replay the failed turn to obtain it.
- Earlier local OuterWilds success (HTTP200/3calls) remains evidence of local integration only, not a substitute hosted pass or broad AI-quality claim.

Ignored receipts: `data/reports/release-hosted-api-activation.json`, `release-connected-cloud-ci-fix.json`, `release-netlify-ci-fix.json`, `hosted-release-20261105/browser.json`, `release-hosted-chat-{preflight,after}.json`, `release-hosted-chat-20261105.json`. Private cleanup capability remains only in approved local temp storage, never Git.

## Remaining boundary

Publication and catalog/dashboard deployment are verified. Hosted assistant successful delivery remains unverified because its bounded smoke failed. Preserve that failure; any follow-up should be targeted diagnosis with explicit bounded fresh work, not an old evaluation replay or an expanding campaign. Owner must review the live application and provide final acceptance after the open limitation is resolved or explicitly accepted.

Rollback references remain original40generation `m2-649714e8b26775165f105d02`, original full manifest and cloud deployment `59e1a472-abdc-447f-b5bd-bcb27e1b71ec`. Switch compatible application/artifact/catalog together if rollback is required; never delete chats or usage to make verification pass. [Detailed release history](project-release-2026-11-05.md).
