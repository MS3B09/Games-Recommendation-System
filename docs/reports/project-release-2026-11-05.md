# Shared 2,000-game release — in progress

## Authorization and current boundary

The owner requires the2,000-game catalog to be the default for recommendations, chat, dashboard and every other catalog service, and explicitly selected **Publish now** for Task3. Commit/push and deployment to the existing free GitHub/Netlify/FastAPI Cloud services are authorized. Owner-reported repo connection and Active Netlify builds do not establish a successful latest deployment. Final hosted acceptance is still required.

**20:06 UTC: compatible backend deployed and the shared 2,000-game generation is active.** FastAPI Cloud login is resolved. Deployment `782ae973-8bf6-4b23-b8c3-3fd102897f6e` serves the latest local source. Before activation, status proved `semantic_catalog_version=m2-cd9790b88f91370e69dae895` while the catalog still had40games. The existing validated `jobs activate` reused and atomically activated that generation; the previous40 remains retained. GitHub push and matching Netlify publication are next, not yet verified.

## Hosted backend and shared activation

- Existing Hobby team verified: directory `backend`, min0/max1, `nano`; startup logs show one server process. No paid resources/new app/second database.
- Preserved secret `DATABASE_URL`; added existing Groq key as secret, explicit `openai/gpt-oss-120b`, AI enabled, normal50/500,000 limits and exact Netlify CORS. No migration credentials/Windows query overrides deployed.
- Local commits `c50f5d4`/`bb93118`: release plus additive loaded-semantic-version diagnostic. After diagnostic: backend299checks(1historical skip)/Ruff/mypy30/OpenAPI and frontend APItypes/standard TS+Vite public-origin build passed.
- Post-activation hosted status2,000/semantic+AItrue; analytics digest `5116c42f8dc97f6e2556f8789aeb664e6c7ae02c070ec1466936d4fdf8472a83`/60words, expanded-only OuterWilds detail, last50of2,000page, facets, constrained favorite discovery, exact Netlify CORS and exact hosted/local OpenAPI equality pass. No inference in these probes.
- Preflight: Alembic0010,2,000games/vectors/metadata, original40document digest unchanged,3user archives/99,155logical bytes/0pending, Nov5usage3calls/30,886units. Activation report:50,460,339database bytes including temporary preview. No archive/accounting mutation by activation.
- Initial probe errors retained: wrong Alembic schema caused read-only rollback; wrong manual request keys/mode correctly returned422; wrong `recommendations` assertion corrected to actual `results`. Probe fixes only. Nonexistent `/api/v1/catalog/analytics` returned404; actual `/api/v1/analytics` correctly returned503for legacy generation and200after activation.
- Ignored local `.env`: matching2k artifact, normal50/500k caps and explicit dev/4173CORS; other values preserved. Exact owned preview25516/6324stopped after identity checks; tagged schema `catalog_preview_ca1e80e8e814` inspected/removed. Normal single-worker API8002started against shared DB; frontend4173unchanged.
- Rollback references: retained40version `m2-649714e8b26775165f105d02`, original full artifact, prior cloud deployment `59e1a472-abdc-447f-b5bd-bcb27e1b71ec`/source `c5a85499b7fe21ec1cf551cdb71e134c86840588`. Roll back compatible app/artifact/catalog together.

Ignored receipts: `cloud-postdeploy-initial.json`, `release-activation-preflight.json`, `release-hosted-api-activation.json`, `release-preview-cleanup.json`; C:run `activation-report.json`. Security advisories empty. Public Netlify history shows old `main@3453bfb` published; latest connected production build needs verification after push. No hosted generation/final owner acceptance yet. The preparation snapshots below are historical.

## Connected publication and CI

Published `d9796e4f291992794e7e53799e75eab78728541f` to existing `main` after scanning1,391tracked files:0configured-secret findings/0unsafe outgoing paths. Connected cloud deployment `aeffac70-9394-40f4-9557-ba97036aedbe` succeeded at that exact SHA. Netlify deploy `6aece2f9a3a978959a4e219f` is published at the same SHA; public JS includes the correct API origin/dashboard (not claimed byte-identical to the saved Windows build).

Backend CI [42101069716](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42101069716) passed. Frontend CI [42101068285](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42101068285) passed79/80; its saved-history test reloaded after request capture but before response persistence, aborting the second response. Added one explicit `aria-busy=false` completion assertion before reload; no app behavior/layout changed. The affected existing test passes3bounded local repetitions with lint. Full corrected CI and hosted journeys still pending. The temporary local reporter reused its normal JSON output for this3-run check; prior full80result remains dated terminal evidence, not the contents of that overwritten machine JSON. Historical failure reports/journals remain unchanged.

Normal local API8002verified against shared2k/semantic+AItrue: listener25788/parent10792; frontend21228/24344unchanged. Recheck identities before actions.

## Local services restored (earlier preparation)

-4173 still targets8002; the125% presentation is unchanged.
-Discovery, exact/semantic/chat catalog tools and dashboard share version`m2-cd9790b88f91370e69dae895` and2,000games.
-The preview now uses the real restricted conversation store and original metered Groq adapter. Archive/usage data are not copied into the catalog schema or reset. Process caps are the normal50calls/500,000reserved units; the database's preserved ceilings/counters are unchanged.
-Acceptance queries run with AI detached. Only the subsequent interactive server attaches configured AI, so verifying the catalog cannot inadvertently spend inference quota. Interactive usage remains tracked by the existing shared ledger, not reported as zero by the catalog verifier.
-Missing archive configuration now produces503`chat_service_configuration`, not a misleading404/Newchat loop. Real missing/wrong-capability archive reads still retain404semantics.
-Actual cross-origin browser verification passed catalog/facets/resolution, an explicit main discovery, dashboard version/totals/eightcharts and real chat create/history/erasure. No API mocking, no generation request. Only owned empty probe archives were created/erased; existing user archives remain.

The exact old preview was identity-checked; child9176was stopped and parent22072exited automatically. The initial stop script correctly stopped on the already-exited parent, so its remaining cleanup was completed separately after rechecking exact schema ownership. Old tagged schema`catalog_preview_d459f68ee4da` was removed; unrelated8000/8001/frontend services were untouched. The running replacement retains exact schema`catalog_preview_ca1e80e8e814`, owner tag`game-discovery-owned-expanded-acceptance-v1`; graceful verifier exit removes it. Recheck actual listener/parent identities before process actions.

## Reproducible deployment runtime

-Promoted already-locked NumPy2.5.4, ONNXRuntime1.31.0 and tokenizers0.23.3 into required serving dependencies. The lockfile changed only dependency metadata, not existing package versions.
-Standard setuptools `build_py` provisions the pinned tokenizer and floatONNX weights using`build_semantic.py`: exact model/revision and manifest identity, streaming SHA256/byte bounds, atomic temporary files, no retries or request-time network. Cached mismatches fail rather than being silently replaced.
-The full existing safe catalog manifest was copied unchanged into package assets. Model/tokenizer cache files remain ignored by Git; Apache2license/notice accompany packaged assets. No Steam raw snapshots, vectors, private chat capabilities or credentials are packaged.
-`Settings.from_environment()` defaults to portable installed-package paths; explicit paths still override, including an explicitly empty process override. Cloud settings must not keep Windows paths.
-Fresh network download of both original pinned files passed:90.565s,466,247-byte tokenizer and90,405,214-byte model, original hashes unchanged.
-An initial wheel build on E: timed out while copying data. The same source built successfully from a C: copy:83,275,359-byte initial wheel. The final wheel including Apache2license is83,279,503bytes; original model/tokenizer hashes and catalog version match, secrets/private capabilities absent. CLI ignore rules also exclude local weights/build outputs, so CLI and GitHub builds use the same provisioning hook.
-A new independent backend environment installed89locked production packages with `uv sync --locked --offline --no-dev` from the clean C: source copy and existing verified assets. Actual query loading from its default package paths passed:384dimensions, norm1.0000000275, matching2k catalog, full license present, no network/provider/SQL call during the encoder probe. No dependency from the private application execution harness was required.

## Checks completed

| Check | Result |
| --- | --- |
| Full backend suite after changes |299tests OK,1historical skip;68.782s. No live provider calls. |
| Backend Ruff, strict mypy, OpenAPI |Pass; mypy30source files. One foreground mypy/OpenAPI attempt timed out on local slow IO; subsequent bounded/background runs passed. |
| New focused behavior |Build download/hash/cache/tamper/portable-default checks and missing-archive recovery regression pass. |
| Clean frontend installation |Initial npmci failed on2missing transitive lock slots; normal package-lock-only regeneration did not repair them. Added only registry-integrity-verified root entries for`@emnapi/wasi-threads1.2.3` and`tslib2.9.1`; no previously locked version changed. Fresh npmci then installed283packages successfully. |
| Standard frontend lint/APItypes/TypeScript+Vite |All passed from the clean C: source copy and new dependencies, not the private execution harness. Built with public FastAPI Cloud origin and process-local384MiB/4MiB Node settings. This resolves the prior125% TypeScript blocker. |
| Actual local network/browser services |1passed,15.2s; matching discovery/dashboard version,2,000games,semantic+AIenabled,real archive lifecycle,CORS,no API failures. Existing installed Chromium1243used; no fresh browser install. |
| Initial full clean browser suite |79/80passed; the320px error-state scan found a real scrollable chat-log keyboard-focus violation. Initial JSON and failure evidence retained. The log now has native `tabIndex=0` and an inset existing lime focus ring; the existing error scan explicitly verifies focus. No scale/layout/copy change. Final confirmation run is separate. |
| Final clean frontend confirmation |**80/80passed in one run**,2.6min, after final standard lint/APItypes/TypeScript+Vite build. Actual clean-source/dependency execution on4174, existing Chromium1243; no private dependency harness. The rebuilt local8002-target artifact also replaces the inspection preview's old build. |
| Clean backend install and encoder |89locked production packages installed into a new environment; actual384Dquery encoder loaded using only portable package defaults. Final licensed wheel hashes/version verified. |
| Fresh live chat integration |One new OuterWilds request, HTTP200in8,037.024ms; canonical753640card (outside original40),revision1. **3actual metered calls/30,886reserved units**,no retries. Owned archive erased and independently404afterwards. This is local integration, not hosted/general relevance/naturalness/grounding acceptance. |
| Secret/private-file scan |1,390tracked/candidate files scanned against actual configured database/Groq secrets and private-file names;no findings. Repeat on final staged files before publication. |

The final full browser confirmation completed successfully. A preliminary final-source lint found four useless test initializers in the newly expanded live-network check; removed those initializers before the passing standard checks. Detector`[]`; builder opened representative final1440daily-limit/390invalid-answer/320context-limit captures, with no regression attributable to the focusability fix. No fresh independent UI review, physical-phone/other-engine check or hosted release acceptance is claimed.

The former4173preview was found absent during final HTTP verification (cause unproven). A free-port check preceded starting the exact freshly built clean-source preview; no occupied port was taken over. API8002listener25516/parent6324serves the current all-service preview; recheck identities before any process action. The clean full-suite preview used its own4174and stopped on completion.

The first final-source actual-network browser recheck immediately after the live smoke hit the existing30-second conversation-create throttle (429); the guard was not disabled and no inference retried. The failure is preserved in`data/reports/release-actual-browser-create429.json`. A later explicit no-inference verification **passed1/1in13.7s**, independently recorded in`release-actual-browser-final.json`: real cross-origin discovery/dashboard/empty chat lifecycle all agree on the2k generation; no API mocking or request failures. The live-smoke usage remained3calls/30,886units afterward.

The current inspection frontend is the verified clean-source Vite preview:listener21228/parent24344on4173, with matching local8002API. No app/env file or user browser profile was edited to change browser zoom. Recheck these process identities before any future stop.

Read-only database checks: Alembic0010; original40active/expanded2,000inactive; matching analytics digest retained. Three user archives existed before probe creation (38,890logical document bytes), and three remained after owned archive probes. Fresh19:38UTCusage check showed0effective Nov5calls/units and last reservation Nov4at10:13UTC(over33hours earlier), establishing fresh owned-window headroom for one bounded smoke, not an organization-wide balance guarantee. The smoke used the ordinary reservation function's normal UTC rollover: Nov5now3calls/30,886units. No manual reset/refund/quota increase. The terminal's CP1252printing failed on a nonbreaking hyphen **after** the completed smoke report/cleanup had been written; the saved report was read, not replayed. Supabase security advisories empty; existing informational unused-index findings retained, not deleted.

## Resolved access blocker and next action

The owner completed FastAPI Cloud login privately; `cloud whoami` and deployment now succeed. The earlier private-login request was:

```powershell
.\backend\.venv\Scripts\fastapi.exe cloud login
```

Next: publish reviewed source, verify CI and connected Netlify/FastAPI Cloud revisions, then hosted journeys and bounded fresh chat when headroom permits. Public build variable remains`VITE_API_BASE_URL=https://steam-discovery-api.fastapicloud.dev`. Never paste secrets. No paid service, second database, old evaluation replay or blanket quality claim is needed.
