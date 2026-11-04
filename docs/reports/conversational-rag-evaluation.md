# Conversational RAG R4 — retrieval comparison and bounded live development pilot

> **Latest2026-10-27 status:** [quota increase and v6 held-out checkpoint](r4-quota-increase-2026-10-27.md).100/1,500,000temporary limits applied preserving usage; source/output prefixes unchanged. Proposed development13/13passes;32held-out attempts with8prose failures remain, human scores null. R4 not accepted. Original pilot results below remain historical evidence.

> **Current status is the [2026-10-26 v6 checkpoint](conversational-rag-r4-resume-2026-10-26.md).** This document retains original pilot evidence; additional inference is now approved, today50daily calls are exhausted, and current source-frozen v6 resumes from its authoritative C: journal on later UTC days. Full live/human acceptance remains incomplete.

**Original R4 pilot evidence — 2026-10-25; acceptance INCOMPLETE.** This report retains the first retrieval comparison and original12-call development pilot/revision. **Later owner authorization and current status:** [R4 fixes/multi-day checkpoint](conversational-rag-r4-continuation.md). Additional free-tier inference is now approved; v3 proposed core journey3/3 and runtime retrieval target pass, current development13/26turns pauses at49daily calls. Full held-out live/human/serving-total-latency gates remain pending. Original failures and ledgers below stay intact. [Plan](../conversational-rag-plan.md) · [Frozen cases/manifest](../../data/evaluation/chat-rag-manifest.json) · [Comparison policy](../../data/evaluation/chat-rag-r4-policy.json)

## Main finding

The following results describe the **original pilot versions**, not the later v3 fixes. The original stop/no-further-inference restriction was superseded by the owner's additional free-tier authorization. See the linked continuation for current accounting and resume instructions.

Actual semantic/title retrieval and scoped memory work when supplied correct intent. On the held-out **retrieval-only** run, named-target Hit@5 is **9/9 proposed vs8/9 baseline**. Both methods cover4/5 nonexhaustive semantic anchor seeds, and both miss the interconnected-world example. This is **not measured end-to-end recommendation-quality improvement**.

The real provider pilot exposed failures masked by scripted integration tests. After a development-only prompt revision, the proposed method successfully answered multiplayer → Spider-Man mismatch, retaining origin user-turn1. The third answer selected **six IDs**, violating the four-card schema; it was rejected. **The complete live conversation does not pass.** Full held-out generation, human judgments, Recall@8 and the nonregression quality gate remain incomplete.

## Reproducible implementation and frozen comparison

- New `jobs/evaluate_chat.py`: sequential offline comparison, single fixed live approval ledger, explicitly approved revision ledger, checkpoint-before-reservation, independent expected-constraint checks, safe completed-ledger no-op, no automatic retries or refunds. Interrupted/failed turns are not automatically replayed. Initial and revision journals are retained separately; the revision inherits all initial attempts against the original cap.
- New `jobs/chat_evaluation.py`: evaluation-only oracle annotations and semantic-only baseline. No serving imports depend on these adapters. Baseline uses exact prefiltered cosine top-five SQL, **no lexical query/title boosts/RRF**, same versioned catalog/encoder, interpretation/memory, evidence byte budget, generator settings and canonical/prose/claim validation. Facts use neutral filters and the current question; recommendations use the interpreted relevant query. Exclusion identity resolution is shared memory infrastructure. Baseline recent targets derive from selected evidence, not five falsely exact references.
- Proposed method retains RRF60/equal weights/20+20/eight evidence; baseline receives five. Shared evidence packing may trim further to fit12,000UTF-8 JSON bytes. **Retrieval IDs and actual generation-packet IDs are recorded separately.** More candidates, routing/reference checks and lexical fusion are intentional differences; gains cannot all be attributed to embeddings.
- Policy was recorded before the first R4 result. No score cutoff, alias, ranking weight, held-out fixture or expectation was tuned. The original40-case/53-turn freeze and hashes remain intact. Two development prompt instructions changed only after the initial M01 live failure; they are not a held-out live result.
- Oracle offline plans use expected kinds/scopes/criteria and explicit extracted title strings. Named reference/exclusion annotations can supply known canonical names; semantic queries use the user text, never expected/anchor IDs. Scripted first-four selection exercises memory/card enforcement, **not live interpretation, answer relevance or factual prose**.

### Inventory and exclusions

Frozen40cases =10development/30held-out,53turns. **33 real-catalog cases /44turns** =8development cases/13turns +25held-out cases/31turns. Seven synthetic cases/nine turns are separate regressions, not generation scores. Both methods ran all44real turns: **88 method-turn observations**.

The frozen manifest's judgment-status text is its original R0 snapshot, not a mutable current-results index. R4 executions live in the linked reports; human judgments still do not exist. Likewise `freeze.py` reports `evaluation_executed:false` for its own hash-check operation, not as a statement that this separate R4 evaluator never ran.

Synthetic coverage remains explicitly separate: A04 ambiguity/atomic exclusion, I01 isolation, I02 legacy quarantine, I03 browser reload/trim/clear, F01 encoder fallback, F02 invalid IDs/JSON/quota/timeout, F03 hostile/long evidence/claims. Relevant `test_chat*.py`/retrieval tests pass again in the backend suite; I03's actual browser lifecycle evidence remains the dated R3 suite, **not a new R4 browser rerun or seven newly scored evaluation cases**.

## Offline results

[Development JSON](conversational-rag-r4-development.json) · [Completed bounded held-out JSON](conversational-rag-r4-held-out-bounded.json)

| Conditional retrieval/state measure | Proposed development | Baseline development | Proposed held-out | Baseline held-out |
| --- | ---: | ---: | ---: | ---: |
| Completed method turns |13/13|13/13|31/31|31/31|
| Named-target Hit@5 |5/5|5/5|**9/9**|8/9|
| Nonexhaustive anchor seed present in evidence |2/2|2/2|4/5|4/5|
| Expected outcome metadata |4/4|3/4|9/10|7/10|
| Returned-card hard-condition violations |0|0|0|0|
| Forbidden-card violations /failed state checks |0/0|0/0|0/0|0/0|

These denominators include only turns with the relevant annotated targets/seeds/outcomes. They are not40 independent answer-quality judgments. No human mean relevance, unsupported-prose claim rate or Recall@8 is reported; anchors are not exhaustive relevance labels. Failed live executions are never removed from the live delivery counts below.

### Remaining retrieval/contract findings

1. **S05**, interconnected-world/ability-route exploration: neither method retrieved Hollow Knight/Ori anchor IDs within its evidence pool. Proposed first four are Monster Hunter: World, Portal, Horizon Zero Dawn and Terraria. This is a meaningful relevance warning; no post-hoc held-out tuning was performed.
2. **M07 turn2**, “Does this one support Linux?” after Hades: baseline embeds the pronoun question and misses Hades; proposed canonical recent-reference lookup succeeds. This tests routing/reference behavior, not a new embedding model.
3. **C06**, unsupported PlayStation platform: both methods safely clarify with no invented cards, but omit retrieval metadata rather than returning the frozen expected `retrieval_unavailable`. Counted as an outcome mismatch; not silently waived or rewritten as an encoder failure.
4. Baseline cannot establish catalog absence or grounded franchise ambiguity from a cosine shortlist; A01/A02/A03 outcome misses are retained. No-match never proves global nonexistence.

## Live development pilot, failures and revision

Provider **Groq `openai/gpt-oss-120b`**, existing zero-temperature/low-reasoning/bounded transport, no model/config change. Initial method order proposed then baseline; failed methods stop dependent turns. [Initial ledger](conversational-rag-r4-pilot.json) · [Exact-byte replay diagnosis](conversational-rag-r4-pilot-diagnosis.json)

| Initial M01 attempt | Result |
| --- | --- |
| Proposed turn1 | Rejected: multiplayer appeared only in query, not criteria patch; generator used unsupplied `440:price_cents`. TF2's zero-price record actually cites `440:free_to_play`; the value being zero does not authorize a different source ID. All selected game IDs were supplied. |
| Baseline turn1 | Delivered three real multiplayer/free games, but explicit multiplayer was not persisted as a hard condition. |
| Baseline turn2 | Spider-Man retrieved, but full-description claim rejected: description excerpts/source IDs are not claimable full-source values. |

Initial: **1/3 attempted turns delivered**,6calls/46,533reserved tokens. No third baseline turn or later proposed turn was attempted after its dependency failed. Replay reproduced all six input packets byte-for-byte using recorded provider JSON, with **zero new inference/reservations**.

### Focused development revision

`ai/chat_evidence.py` now explicitly requires hard conditions in `criteria_patch`, with the multiplayer example and platform/budget rule. Ordinary answers default to empty optional claims; explicit citation requests may use only supplied claimable entries, not price objects or description excerpts. Runtime validation remains intact, not relaxed. Main discovery's legacy provider prompt is unchanged.

Owner explicitly chose **Fix and retest**, authorizing only the remaining six calls for proposed M01. [Revision ledger](conversational-rag-r4-pilot-revision.json) · [Exact-byte revision diagnosis](conversational-rag-r4-revision-diagnosis.json)

1. **PASS turn1:** four supplied multiplayer cards, conversation-mode provenance origin1, empty optional claims.
2. **PASS turn2:** canonical Spider-Man1817070, recorded single-player mismatch, original multiplayer requirement/provenance retained. Model chose no display cards; authoritative appended text names the canonical game.
3. **FAIL turn3:** interpretation retained multiplayer and every selected ID was supplied/eligible, but `game_ids` contained six entries. `ChatAnswer` max-length validation rejected it before commit. Prior successful state remains usable. No truncation, hidden regeneration or extra call was used to turn failure into a pass.

Revision: **2/3 delivered**,six more calls/46,280reserved tokens. This is a development repair check, **not a new paired baseline comparison**. The baseline was not rerun under revised prompts. Captured six-ID failure has a regression asserting rejection, unchanged input state and exactly two calls. Source-ID/free-without-price and aggregate-cap/completed-ledger regressions also pass.

### Qualitative inspection, not human evaluation

[Per-output builder review and human-rating worksheet](conversational-rag-r4-review.json) inspects all six attempted outputs, including rejected outputs and structured claims. Two revised delivered answers have no unsupported factual prose observed in this short builder inspection. The initial delivered baseline's collective “all support online multiplayer” exceeds the explicit generic-multiplayer facts for TF2/Dota. This is one builder-identified collective prose unit, **not a measured human unsupported-claim rate**. Review is not independent/blinded/human; frozen human metrics remain null.

### Accounting and stop

- Database read-only preflight showed a previous UTC-day row:2026-10-23,4calls/19,516reserved units;2026-10-25 had no observed use yet. Normal reservation-function day rollover occurred on the first approved call; no manual reset.
- Post-initial actual row:2026-10-25,6calls/46,533reserved tokens. Post-revision: **12calls/92,813reserved tokens**. All12provider attempts returned JSON; all12reservations were granted. Maximum input packet11,827bytes. Existing concurrency, two-call turn cap, four/minute and30-second peer throttle remain. Starts are spaced beyond30seconds after preceding completion, including revision startup.
- **Approval consumed:12/12calls;66,547 reserved-token headroom does not authorize more calls.** Application allowance observed remaining:38calls/407,187reserved tokens, absent other use. Shared application headroom is distinct from this exhausted agent approval.
- Reserved units are the existing conservative input-byte+1,280 allowance; actual provider usage tokens are not exposed by the current adapter and are not invented in this report.
- No further live run, quota reset, provider retry, schema/migration/data mutation or environment-file edit. Only the expressly approved accounting writes occurred. No new key/config/dependency/download, commit/push/deploy/M5.

## Performance and machine limits

Local owner machine: Intel Core i5-5200U, CPU-only,4logical CPUs,7,888MiB observed RAM; Windows10/Python3.13.12. Actual40-game catalog `m2-649714e8b26775165f105d02`, pinned384-D MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, hash-verified local encoder. Database is remote, so retrieval includes network/snapshot cost. No hosted feasibility claim.

| Observation | Proposed | Semantic baseline |
| --- | ---: | ---: |
| Development warm total median /p95,12successful samples per method |752.661/1,622.172ms|648.743/1,681.018ms|
| Development warm retrieve p95 |839.835ms|653.310ms|
| Held-out warm total median /p95,30successful samples per method |889.653/2,686.778ms|719.560/2,548.586ms|
| Held-out warm retrieve p95 |**2,574.066ms**|**2,524.511ms**|
| Held-out encoding p95, includes each method's initial encode |65.693ms|295.465ms|

Warm means excluding the first successful method turn, not controlled repeated identical requests. Diverse queries, fixed proposed-first ordering and host contention limit paired latency interpretation. These offline totals use oracle/scripted provider output; they are **not live answer latency**. The1-second retrieval target is **not met on the held-out run**. Do not substitute the earlier R1 development benchmark to claim a pass.

Fresh-process evaluator import observation:4,935.856ms/75.211MiB import high-water RSS; not API startup. Encoder loads:initial pilot2,510.992ms/revision1,440.035ms; imports are explicitly null in per-run JSON rather than guessed. Offline development/bounded held-out sampled peaks230.152/224.512MiB; live initial/revision239.832/239.398MiB. Sampling is10ms, not guaranteed native transient peak or host capacity proof.

Initial held-out attempt hit `MemoryError` after retaining partial results ([original interruption](conversational-rag-r4-held-out.json)); host diagnostic showed about489.6MiB available. Evaluator changed to streaming JSON, compact per-turn selections with one catalog evidence inventory, and collection of bound-method cycles outside timed turns. No user processes/model caches were removed. The completed repeat retains unchanged ranking/fixtures; the initial partial run is not pooled into scores or hidden. Sampling/repeat/query order cannot prove the exact OOM cause or isolated effect of the retention fix.

Six live attempted turns took5.18–7.05seconds including failed deliveries and diagnostic journal/accounting overhead, excluding intentional waits. Only three delivered. No general live p95≤10seconds pass is inferred from this tiny, failure-heavy development sample. No standalone orchestration-overhead rebenchmark was performed; historical R0/R2 evidence retains its scope.

## Verification and reproduction

From repository root, existing durable interpreter and configured local model paths:

```powershell
& .\backend\.venv\Scripts\python.exe -m game_discovery.jobs.evaluate_chat offline --split development --output docs/reports/my-r4-development.json
& .\backend\.venv\Scripts\python.exe -m game_discovery.jobs.evaluate_chat offline --split held_out --output docs/reports/my-r4-held-out.json
& .\backend\.venv\Scripts\python.exe -m unittest discover -s backend/tests
& .\backend\.venv\Scripts\python.exe -m ruff check backend
& .\backend\.venv\Scripts\python.exe -m game_discovery.api.export_schema --check
& .\backend\.venv\Scripts\python.exe backend/experiments/rag_r0/freeze.py
& .\backend\.venv\Scripts\python.exe -m unittest discover -s backend/experiments/rag_r0 -p test_contracts.py
```

Output parents must exist; offline output paths must be new. No inference in `offline`. Use existing model/cache files, never download serving weights. To replay already recorded revised outputs locally:

```powershell
& .\backend\.venv\Scripts\python.exe -m game_discovery.jobs.review_chat_pilot --source docs/reports/conversational-rag-r4-pilot-revision.json --output docs/reports/my-r4-revision-diagnosis.json
```

`pilot` and `retest` commands use fixed completed approval ledgers and now return a **no-call completed status**. Preserve both ledgers; deleting/renaming them is not a new approval or valid way to reproduce live results. A new live phase needs an explicitly scoped approval and ledger revision. Diagnostics under later prompt revisions may lose byte parity; both retained diagnostic runs matched their recorded input bytes before later changes.

Final backend suite: **168 tests** (17 new evaluator/failure regressions beyond R3's151); Ruff, strict mypy25, OpenAPI/generated drift and six frozen tests/hashes checked. Frontend code/build/assets unchanged in R4; R3's49frontend tests/6scans remain dated evidence, not new R4 checks. An initial mypy cache run timed out; the later run with the same cache completed cleanly.

## Acceptance disposition and next decision

**R4 remains in progress, not complete/portfolio-ready.** Delivered: reproducible offline baseline comparison, real encoder traces, explicit failures/performance report, durable capped live pilot/revision, qualitative review worksheet, [architecture](../architecture-assistant.md), [walkthrough](../walkthrough-assistant.md) and updated operations.

Remaining gates:
1. Original six-ID failure is preserved; strict schema generation and the current proposed3/3core journey verify its repair without relaxing guards. Complete remaining same-version development/live verification under the already granted additional approval.
2. C06 metadata now passes offline/regression checks and the declared runtime retrieval benchmark meets1second; retain earlier spikes and S05 miss. Serving-only total live latency still needs measurement; do not tune rankings on this held-out set.
3. Finish the approved real-generation comparison with fresh shared-quota receipts and sequential multi-day checkpoints, then obtain owner relevance/prose/per-candidate judgments. Current v3 remaining upper bound150calls/1,992,000reserved units after26same-version calls; earlier versions are not silently reused as held-out evidence. Today pauses at49/50calls, not an approval limit.
4. Apply the frozen quality gate only when evidence exists. No whole-product M5, hosted deployment, publication or measured relevance-improvement approval follows from this partial phase.
