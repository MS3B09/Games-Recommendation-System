# Catalog-wide chat grounding and tooltip position — 2026-11-07

## Owner-authorized publication

The owner subsequently approved commit, push and live deployment of the complete November7dashboard cleanup/hover refinements and general catalog chat fix. Final local frontend regression passed **81/81 in4.5minutes**; prior302backend checks (one existing skip), configured30-file mypy and focused dashboard/static checks remain applicable. A fresh Ruff check passed. A fresh OpenAPI export command hit a30-second local timeout; the remote backend CI must verify the unchanged contract. Configured-credential scan passed across1,404publication candidates; its initial broad key-name scan falsely identified a tokenizer file path, not a secret. No credentials, model files, private capabilities or ignored receipts are included.

CI, both connected production revisions and actual hosted browser/API checks must be verified after push. Their final SHA/deployment IDs and results are saved in ignored `data/reports/nov7-release-final.json` and `data/reports/nov7-release-hosted/verification.json`, avoiding a recursive documentation-only redeploy. No live inference is planned for this release verification; catalog recognition/scripted checks are not live-provider quality acceptance. Earlier local-only/no-publication snapshots below describe their dated state, not the subsequent authorization.

## Later owner follow-up: discount spacing and compact hover

Added20CSSpx above the discount legend, matching its existing20px row gap. Reduced the tooltip from180to160CSSpx, padding8×10to6×8px and line-height1.5to1.4; adjusted its horizontal clamp to the new width. Typography remains13px, placement remains above the strip and root scale stays125%. No other chart, backend or data change.

Five dashboard checks passed in47.8s, including1440/390/320equal-gap, compact-tooltip/above-strip/containment assertions, axe0 and no overflow. Lint and standard TypeScript/Vite build passed; the existing large Plotly chunk warning remains. Detector returned`[]`. Builder opened three discount-panel captures plus desktop/narrow hover captures and the actual local hover capture; no independent/physical-phone review is claimed.

Actual4173→8002browser verification passed:25physical-px legend gap;200×60.5physical-px tooltip above the strip;7plots/2,000games/unchanged analytics digest/125%/0page or API errors/0generation. Preview21228was updated without restarting either service; previous entries are backed up at `C:/Users/User/AppData/Local/Temp/opencode/dashboard-discount-compact-preview-backup-20261107/`, old assets retained. New ignored receipts: `data/reports/dashboard-discount-compact-tests-20261107.json`, `dashboard-discount-compact-local-20261107.json`; captures under `data/reports/dashboard-discount-compact-20261107/`. Earlier receipts were not overwritten. Local/uncommitted/undeployed; no full-suite/backend/live-provider rerun for this narrow UI follow-up.

## Implemented locally

The owner authorized fixing the assistant generally, not adding an eFootball exception, and moving discount hover values above the strip.

- **All active catalog names are available for recognition.** Each turn reads active eligible title identities in the restricted repeatable-read snapshot. A shared matcher recognizes whole names, case/Unicode/punctuation/spacing variants and optional trademark symbols. Longer overlapping names take precedence; ambiguous identities are not silently turned into a different title. Up to the existing four identities are placed in model context. Only compiled public title patterns are cached (one title set); no user message/conversation is cached. Matching is entity grounding, not an intent classifier or keyword router.
- **Canonical lookup is consistent.** `assistant_search` now also matches normalized compact title identities and ranks exact identities first, while retaining the complete paginated text/title search. LiteralTM and™ spellings no longer take incompatible paths. No stored keys, import artifacts, source aggregates or schema were rewritten.
- **Completed lookups use the structured writer.** A successful `lookup_titles` batch with `finish=true` now enters the existing strict-schema final writer. `finish=false` retains another information round. Malformed JSON and invalid citations/cards/filters still fail closed; no HTTP retries or extra repair/critique model calls were introduced.
- **Catalog-absence output is guarded.** The server checks common absence assertions before delivery. A contradictory/unsupported denial is replaced locally with verified canonical matches and cited cards, or with an honest unverified-name/search-criteria clarification. It is never treated as new catalog evidence. Existing canonical/filter validation runs before and after this deterministic status formatting; ordinary model text is otherwise retained. Metadata is not invented from the rejected denial.
- **Discount hover is above the colored strip.** Plotly emits hover/unhover events without drawing its inline tooltip. A native tooltip occupies reserved space above the strip, is horizontally clamped, clears on leave and retains the counted legend/failure alternative.125%scale is unchanged.

Tradeoff: name recognition adds a compact read-only catalog-title scan per turn, plus matching records when found. Ordinary conversation still uses one model call and the same optional native tools; it is no longer a zero-catalog-read path. Main preferences, saves and feedback never enter this check. Public wire, model, dependencies, quotas and archive schema are unchanged.

## Verification

| Check | Result |
| --- | --- |
| Focused dialogue/retrieval mechanics |86tests passed |
| Full backend suite |302tests OK, one existing skip |
| Standard Ruff / configured strict mypy |PASS / PASS30serving files |
| Actual active catalog recognition |**2,000/2,000 titles;4,602 exact/case/normalized/trademark variants;0misses**,36.467s total |
| Actual restricted SQL lookups |eFootball/eFootballTM/™ all resolve1665460; Counter Strike2→730; Baldurs Gate3 ranks1086940first; absent test query0matches |
| Actual repository + scripted denial |Canonical eFootball card/title returned; one scripted exchange,0provider calls |
| Actual repository + ASGI route + in-memory archive |HTTP200/Counter-Strike2canonical730card;0shared archive writes/0provider calls |
| Frontend standard lint/APItypes/TypeScript/Vite |PASS |
| Final five dashboard checks |5/5PASS in1.1min, including all six discount hover values and1440/390/320tooltip-above-bar geometry, axe0/nooverflow/contained axis/value labels |
| Visual confirmation |Builder opened all three tooltip captures; tooltip is separated above the bar, including320px; no independent-review/physical-phone verdict |
| Actual local browser/API |7readyplots/2k/unchanged analytics digest/tooltip above/clears on leave/125%/0page or API errors/0generation |
| Impeccable detector |`[]` on changed tooltip component/CSS |

The current frontend scope has focused five-check coverage; the preceding81/81run predates this tooltip-position change. Initial overly broad mypy invocation included untyped historical jobs and timed out; a cold configured-scope foreground invocation also timed out. The subsequent normal configured30-file check passed; no historical jobs were changed or errors hidden with new ignores. All failed commands remain in managed logs.

Receipts are ignored: `data/reports/catalog-chat-name-verification-20261107.json`, `catalog-chat-asgi-fix-20261107.json`, `catalog-chat-tooltip-ui-20261107.json`, `catalog-chat-tooltip-local-20261107.json`; captures under `data/reports/catalog-chat-tooltip-20261107/`.

## Runtime and limits

Open **http://127.0.0.1:4173/dashboard** and hard-refresh. The existing preview21228was updated without restarting it; previous entries are backed up at `C:/Users/User/AppData/Local/Temp/opencode/catalog-chat-fix-preview-backup-20261107/`, with old assets retained. The idle, identity-verified8002API was restarted once after a read-only preflight found0active generation leases. Its old launcher exited with its child before the stop command reached it; startup then followed a verified free-port check. New launcher11104/serving child20484has2k/semantic/AI readiness. Recheck identities before any future process action.

Pre-change backend/test source backup: `C:/Users/User/AppData/Local/Temp/opencode/catalog-chat-before-fix-20261107.zip`, SHA256 `f034d381a9adee9b9c94b17775adef4b7f858f7015dcf695bf7b05df0442b923`. Original user archives, historical failures, frozen journals and hashes remain untouched. New serving source intentionally differs from old locked evaluations; never resume them or replace their hashes.

**No commit/push/deploy, schema/data/configuration/dependency/model/quota change or new live LLM call.** No claim that an LLM can be error-free for arbitrary wording, facts, typos, ambiguous editions or provider outages. The exhaustive result establishes catalog-name recognition, not2,000live generated answers or a broad recommendation-quality/latency pass. The output status guard is conservative English-language validation, not proof of arbitrary prose entailment. A fresh bounded live-provider check remains pending current applicable free-tier headroom; it must not replay failed turns or restart an old evaluation campaign.
