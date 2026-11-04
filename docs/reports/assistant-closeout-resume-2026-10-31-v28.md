# Assistant continuation — current v28, 2026-10-31

> Superseded by the [v29 Ponytail simplification](assistant-ponytail-2026-10-31.md). The evidence below is historical; preserve its journals and use the new source-locked continuation.

**Live development progressed, but full quality acceptance remains INCOMPLETE. Current v28 has zero live attempts. Inference is paused at a conservative owned-token planning guard, not an application cap or a newly observed provider429.**

[Final source identities, immutable snapshots and usage](assistant-closeout-audit-2026-10-31-v28-final.json) · [Independent v27 budget checks](assistant-closeout-budget-v27.json) · [Current actual UI integration](assistant-closeout-ui-v28.json) · [UI archive cleanup](assistant-closeout-ui-v28-cleanup.json) · [Ten evaluation archives independently erased](assistant-closeout-cleanup-2026-10-31-v27-stopped.json) · [Protocol](../assistant-closeout-protocol.md).

## 1. What actually ran

At06:10UTC the existing observer API15196/11944and preview17652were still running. Source/config/fixture guards passed and fresh SQL showed27calls/310,453units. No restart or provider probe was needed before resuming the untouched Hades case.

This continuation made **25 actual model calls / 293,143 reserved units across11new attempted turns, all11delivered HTTP200**. HTTP success does not mean quality acceptance. No new provider429 occurred during this continuation. All versions/failures below remain visible; no attempted turn was replayed or hash replaced.

| Source | New work | Observations and retained failures |
| --- | --- | --- |
| v24 | D24P2turns, D24R3turns;5deliveries /8calls | Independent catalog read confirms Hades Windows/macOS, single-player,2499cents/dateOct14. Follow-up correctly qualifies catalog flags, but exposes an internal scope label. Recall correctly gives Thursday→Monday, tentative Dana/no budget. No preference edits or unsolicited catalog calls in recall; prose still inferred multiplayer casually. These are short-memory checks, not24turn memory acceptance. D24B's earlier429/two skips remain. |
| v25 | D25Bturn1;1delivery /3calls | Optional readiness was omitted. Four canonical cards delivered, but unsupported puzzle/sandbox/campaign/roguelike prose remained; requested normal13USD was incorrectly marked turn-only. Stopped this source for general fixes; archive erased. |
| v26 | D26Bturns1–2;2deliveries /5calls | Required readiness was emitted; first reply used2calls and correctly saved normal14USD. Unsupported description labels persisted. Temporary search found eligible records, but four- then three-record pages were refused by the full-context boundary, producing truthful incomplete retrieval and no cards. Source superseded, not passed. |
| v27 | D27B3turns;3deliveries /9calls | Compact writer/review delivered allfour normal records3893bytes and allfour temporary records4071bytes. Normal16USD was saved and retained; temporary1601–3200returned newly eligible records. First reply used literal source quotations, but clipped phrases/repeated notices remained awkward. Third reply recalled16USD but **did not execute the requested restored search**: applied_filtersnull/cards[]; two native patches competed on set/clear before finalization. Overall budget gate fails. |
| Current v28 |0live attempts | Offline completion/feedback/wording corrections below; fresh checkpoints prepared. No current-source live acceptance claim. |

Across all v22–v27 closeout versions there are **23attempts/21HTTPdeliveries**, including semantic failures, two earlier provider429s and retained skips. Current80planned turns are additional work, never a replacement that erases these outcomes. All discovery and original held-out live cases are still unattempted.

The independent v27 record check confirms all eight cards' Windows/single-player/recorded-price predicates and exact canonical price/platform/mode values. Temporary prices were1999/2999/2499/2499cents, above1600and at most3200. It explicitly records `overall_budget_gate: fail_restored_search_omitted`, with human scoresnull. Correct budget recall is not a substitute for executing a search.

## 2. What changed in the current engine

The existing native LLM-first architecture, public API/UI, catalog/ranking/model and accounting remain. No input classifier, game-specific serving rule, new service/dependency, migration or environment-file/limit change.

- Information tools expose a required native `finish` choice. The model chooses whether another information round is needed. Local parsing retains a default only for older scripted/private fixtures.
- A ready tool batch goes to a strict structured writer using **actual field evidence and original user messages**, omitting earlier generated prose. Original archived turns/cards/evidence are never rewritten or silently evicted; only provider working context is projected. Earlier originals remain available to the native planner through history tools before it closes tool use.
- A bounded compact grounding review remains when a call slot is available, **inside the same maximum three model calls**. Validated memory/preferences and selected card IDs are retained; wording review cannot introduce a different card. Second information rounds still work when the planner requests them.
- If the planning transcript cannot accompany a complete bounded tool page, the existing early-finalization policy now uses the compact evidence writer before refusing it. The6500tool-page/12000provider-input bounds remain unchanged; oversized/incomplete pages still fail explicitly and restore prior state.
- Evidence precedes prose in the internal passage schema. Instructions request complete short source phrases only when useful, avoid gratuitous clipped quotes, and keep platform/price statements catalog-qualified. **Instructions do not prove live compliance.**
- Native planning explicitly distinguishes executing a requested search from acknowledging conditions. Normal searches use retained filters; temporary read-only overrides expire automatically and need no restoration patch. Conflicting `set`/`clear` fields receive specific structural feedback instead of only generic validation feedback. Current v28 must still verify this fixes the omitted search live.
- Audit accounting counts missing usage with each original reservation as a conservative fallback instead of treating it as zero. Invalid/missing totals cannot establish a smaller planning debit. It reports an owned bound, not provider organization balance.

### Current checks

**278backend tests, Ruff, strict mypy30source files and OpenAPI drift check pass.** New meaningful regressions cover explicit readiness, second rounds, refused-page recovery, atomic price rejection, writer isolation from earlier assistant prose, retention of user originals/actions/card selections, structural preference-conflict feedback and conservative missing-usage accounting. Initial prompt-size/legacy-path test failures during development are retained in the terminal record; final full278passes include the compact early-finalization fix and shorter tool descriptions, with no relaxed limits.

## 3. Current-source browser/API verification — zero inference

Refreshed real browser→FastAPI→restricted catalog/archive integration: **10checks /6scans at1440/390/320**, axe0, no horizontal overflow or page errors. Builder opened all six captures. No frontend application code was changed, and no new independent UI SHIP/physical-phone/hosted verdict is claimed.

Verified full synthetic40turn archive paging, reload/card/draft persistence without generation, canonical details/Save/Steam, oversized-page uncertainty, independent NewChat and real server erasure, exact manual retry after a simulated provider wait, mobile close/focus restoration, clear-data erasure and unchanged main discovery results. The fixture was updated to read the compact writer's evidence projection.

This used **8scripted model exchanges,1simulated limit,0live provider calls/0actual reservations**. Both UI-owned archives were erased; port8002was stopped. The desktop artwork was still a placeholder in its first capture and loaded in later mobile captures; no blanket asset-load/visual-polish claim. Earlier74frontend-suite/TS/build evidence remains dated; current integration is fresh, not a full frontend-suite rerun. Real inference/naturalness/encoder performance are separate gates.

## 4. Provider receipts and exact stop condition

The safe response-header observer captured25real requests during this continuation:24providerHTTP200and oneHTTP400JSON-validation response. The last was handled by the existing typed local proposed-generation recovery, with no extra HTTP retry; its missing token usage is conservatively counted.

Observed headers confirm **8000TPM and1000RPD**. These do not establish remaining TPD or the exact cause of historical429s. Source v25's three-call burst ended with only10TPM tokens remaining; v27's first burst ended with716. Current [Groq documentation](https://console.groq.com/docs/rate-limits) gives a200KTPD baseline for this model, states organization limits may differ and distinguishes request/day from token/minute headers. Cached tokens do not count toward rate limits; our reported-token sum may therefore overstate actual debit. No private limits/metrics/billing API was called, no account upgrade or paid resource enabled.

Fresh SQL at **2026-10-31T07:23:30.946973+00:00**:

| Receipt / planning value | Value |
| --- | --- |
| Application consumed | **52calls /603,596reserved units** |
| Application remaining under100/1.5M | **48calls /896,404units** |
| Known reported tokens |124,342 |
| Missing usage records / original reservation fallback |3 /36,638units |
| Conservative owned-token bound |**160,980** |
| Plus next three-call worst-case turn |**39,840** |
| Result |**200,820 >200,000** |

**Inference stopped before another call.** This is a conservative local free-tier planning stop, **not application exhaustion, a new provider429, an asserted provider remaining balance, or proof that the organization's TPD quota is exhausted**. Unknown usage/cached tokens/organization activity/window semantics prevent a more exact balance claim. Do not lower the guard or ignore missing usage merely to fit another turn. The next normal day is November1UTC, but fresh application/provider-window receipts are still required; UTC rollover alone does not prove provider recovery.

No inference occurred after D27Bturn3at06:58UTC. The later fixes, tests, UI integration, independent record reads, preparation, auditing and backup make no provider calls/reservations. Usage counters are preserved. Normal50/500krestoration remains after evaluation, not now.

## 5. Durable current checkpoint and next action

All four authoritative **C:/Users/User/AppData/Local/Temp/opencode/** v28journals are source/config/fixture/order matched at **zero attempted turns**:

| Journal | Fixture/order / planned turns |
| --- | --- |
| `assistant-closeout-capability-development-v28.json` | `dialogue-v18.json`, D28B/D28P/D28R /8 |
| `assistant-closeout-discovery-development-v28.json` | Original `assistant-discovery-v1.json`, D01–D10 /10 |
| `assistant-closeout-capability-held-out-v28.json` | Original `dialogue-v12.json`, H22L/H22C/H22F/H22N /32 |
| `assistant-closeout-discovery-held-out-v28.json` | Original `assistant-discovery-v1.json`, H01–H30 /30 |

The original held-out fixtures are unchanged and no held-out result was used for tuning. Older v24–v27 pending paths cannot resume on the changed engine. All23attempts and prior skips stay in the audit. Ten live-evaluation-owned archives independently return404/sessionmissing; current v28 has created no live archive/capability. Private capability files remain in C: and are never exported. Current public snapshots retain the exact earlier hashes, including v24`7ca86108…`, v25`a5f13b30…`, v26`3477c5d5…`, v27`d3249569…`; full hashes are in the machine audit.

After an applicable fresh provider/day headroom check **and** fresh SQL receipt, ensure the current observer API is ready, then run from the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m game_discovery.jobs.evaluate_dialogue_live --split development --cases data/evaluation/dialogue-v18.json --case-order D28B D28P D28R --max-new-turns 1 --output "C:/Users/User/AppData/Local/Temp/opencode/assistant-closeout-capability-development-v28.json"
```

This command was **not executed**. Audit each result before continuing. The runner retains61second pacing and per-turn3call/39,840unit application guard; the additional provider planning guard above must also pass. Stop on provider limits/ambiguous state. No new key, dependency, configuration or inference approval is needed for the already-authorized continuation. Do not run v20–v27 commands or replace stored hashes. Development must pass before discovery/held-out progression; recalling the normal budget without executing the requested search remains a failure.

Current-source observer API launcher **24672**, child **18832** on:8001; preview **17652** on:4173. Verified identity/catalogready/semantictrue/AIenabled; port8002stopped. Recheck identities before reuse/stop, because PIDs can be recycled. Existing C: helper `start-provider-receipt-api-v24.py --version v28` starts missing:8001with fresh logs. It uses the same observational `jobs.serve_provider_receipts`, whose code/request behavior is unchanged.

Current sidecar **C:`groq-rate-headers-v28-20261031T072427Z.jsonl`** contains observer startup only,0live requests. Older v24/v25/v26/v27 sidecars are preserved. No background evaluation is running. Open <http://127.0.0.1:4173/> for inspection; main discovery needs no AI inference.

## 6. Remaining acceptance

Current-source live verification of search completion, all preference scopes, source-qualified natural facts and short recall; then discovery development and original held-out including24real unseeded turns. Broader actual owner relevance/naturalness ratings and194retrieval judgments remain missing; aggregates staynull. Retrieval1second target remains missed, representative HTTP/API-memory/performance acceptance incomplete. Current mechanical/UI success is not assistant completion. Publication/M5/commit/push/deploy/paid resources remain unauthorized.

The current source/fixtures/tests/commands/public evidence and six UI captures are backed up in the approved C: directory by the v28snapshot helper; the [separate backup receipt](assistant-closeout-v28-backup.json) records its exact path, SHA256 and ZIP integrity. [Allowlisted provider-header snapshots](assistant-provider-rate-receipts-2026-10-31-v28.json) preserve the actual diagnostic receipts. Model weights, environments, logs with credentials and private capabilities are excluded.
