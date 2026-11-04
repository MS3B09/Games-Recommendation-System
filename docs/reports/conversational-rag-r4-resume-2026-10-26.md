# R4 resumed — 2026-10-26 checkpoint

> **Historical checkpoint. Current allowance/resume/evidence is the [2026-10-27 quota-only amendment report](r4-quota-increase-2026-10-27.md).**100/1,500,000temporary limits are applied; v6 development completed and held-out began. Use `resume_chat_quota`, not the original50-call receipt parser. Preserve this report's historical failures and authoritative C: journals.

**R4 remains INCOMPLETE. Additional free-tier inference remains authorized.** Today's application allowance is exhausted at **50 calls /393,494 reserved units**, SQL-confirmed. Current source-frozen revision is **v6**, not v3. Resume only unattempted v6 work after a fresh later-UTC-day quota receipt. No new permission, key, model or configuration is needed. [Previous checkpoint](conversational-rag-r4-continuation.md) · [Current policy](../../data/evaluation/chat-rag-r4-continuation-v6.json) · [Reconciliation](conversational-rag-r4-audit-2026-10-26.json)

## What resumed and what failed

- Fresh UTC2026-10-26 preflight correctly observed effective zero usage even though the retained counter row still had the previous date. First approved reservation rolled the window normally; no reset.
- V3 source hashes matched, so the next unattempted S04/M05/C01/A01 work resumed without replaying old calls. V3 finished **24 attempted method-turns**,22 delivered, two transport failures, two dependent turns skipped. Proposed M05 additionally invented hard `Puzzle` genre filtering and returned no matches. Existing validators were not relaxed. [Retained v3](conversational-rag-r4-development-v3.json)
- V4 preserved a missing played-title exclusion, a misrouted undo, and an unsupported whole-catalog genre refusal. Slow E: checkpoint writes hit the420s tool timeout. SQL delta confirms **eight granted calls**; ninth attempt was started before reservation, with original JSON `not_attempted` and temporary JSON `pending`. No process remained; no ninth reservation was observed. Original JSON/tmp/lock remain untouched and **must not be resumed or replayed**. [Retained v4](conversational-rag-r4-development-v4.json)
- V5 verified played exclusion and fact lookup, then failed on model `clarify + title_mentions` for an explicit undo. Frozen generic TurnPlan validation correctly rejects that combination. The captured output became a regression; it was not rewritten or retried. [Retained v5 export](conversational-rag-r4-development-v5.json)
- V6's initial read-only catalog preflight encountered a transient local database connection failure, **before any turn/reservation/provider attempt**. A later TCP connectivity probe succeeded; only then was unattempted v6 work resumed. No host/credential/network configuration changed.

## Implemented fixes

1. `ai/chat_explicit.py` derives conservative **current-user-only** operations from anchored positive played statements and whole-message include/allow-again commands. Canonical IDs still come from the existing title resolver; ambiguity and failed validation remain atomic. Negated, quoted and question forms are not converted by this helper. Both proposed and baseline share this memory infrastructure.
2. Whole-message undo routing is normalized **before semantic TurnPlan validation**, then validated again through unchanged domain contracts. Unknown fields, malformed patches and model-invented IDs still fail. This repairs a specific unambiguous user operation rather than accepting arbitrary malformed model output.
3. Generic experience words remain soft semantic intent instead of becoming unconfirmed hard catalog-genre labels. Explicit genre requests and other hard criteria remain; existing confirmed preferences are retained. Generator guidance uses description evidence rather than exact genre-label equality and forbids whole-catalog absence assertions from a shortlist. A captured whole-catalog refusal is rejected by the prose guard. Fewer/no recommendations remain allowed when supplied evidence cannot establish fit.
4. Provider diagnostics retain only safe exception **class names**, never raw exception messages, credentials or response bodies. Existing public error behavior, three-second socket timeout, concurrency, accounting, two-call maximum,30-second throttle, quotas and no-provider-retry behavior remain.
5. Evaluation measures synchronous journal-write intervals with a request-local ContextVar. `serving_equivalent_domain_ms` subtracts only those observed writes from domain invocation time; real quota SQL and normal validation remain. No global profiling is needed for current evaluation, no serving source is replaced, and browser/HTTP time is not claimed.
6. **Before-call durable journals now live on approved local C: storage**, with atomic/fsynced E: exports after each whole turn and at pause/completion. Source/approval guards, before-reservation persistence, failed-turn retention and UTC-day preflight remain. This avoids rewriting the large catalog report to the slow workspace drive multiple times per call. The UTC date is checked again after a throttle wait.

No catalog, embedding, model, dependency, environment file, database/public/frozen-domain schema, ranking weights/aliases, frontend or deployment change. No held-out tuning or output reuse across versions. V4–V6 policies explicitly record their revision reasons; original two pilot ledger hashes remain unchanged.

## Current v6 live evidence

[Workspace export](conversational-rag-r4-development-v6.json) · [No-call replay](conversational-rag-r4-development-v6-replay.json)

- **9 attempted /26 expected development method-turns**: proposed4/4 delivered; baseline4/5 delivered. One baseline dependent turn is skipped, not a pass. Sixteen other method-turns remain unattempted. Full held-out live evaluation has **not started**.
- **Proposed M05 passes3/3**: already played Portal2 → factual online-co-op lookup remains possible → include-again removes the exclusion and resumes recommendation routing. Correct user-turn provenance is retained. Its first response safely declined unsupported fit rather than inventing a puzzle-genre match; this is not a human relevance score.
- Proposed M01 turn1 passes; its fact/continuation turns are still unattempted in v6. Do not reuse v3's3/3 core result as a complete v6 result.
- Baseline M05 turn2 was rejected: it returned `game_ids:[]` but attached a modes claim for620. The ID/value were supplied, but claims must belong to **selected** games. This is a structured-selection contract failure, not an invented title or fabricated modes value. It remains a delivery failure; no truncation, repair call or retry. Its third dependent turn is skipped.
- All18v6 provider attempts returned JSON and were reserved. **18 input packets replay byte-exactly with zero inference/reservations**; replay reproduces the baseline rejection. Other observed v6 canonical/card/state checks pass; human relevance, prose claim rates and Recall@8 remain null.
- Current v6 source identities match; authoritative C: journal and E: export hashes match. No normal v6 lock remains after quota pause. V4's abandoned artifacts are separate.

## Timing evidence and scope

Initial global-profile sidecars exposed synchronous evaluation-write cost, but also retained slow real accounting/network samples. Corrected observations included19.358s proposed and11.954s failed baseline outliers; these are not filtered out or passed off as ≤10s. [First sidecar](conversational-rag-r4-serving-development-2026-10-26-a.json) · [Second sidecar](conversational-rag-r4-serving-development-2026-10-26-b.json)

Current lightweight v6 measurements, excluding first successful method turn as in the recorded summary:

| Current successful live observation | Proposed | Baseline |
| --- | ---: | ---: |
| Warm delivered samples |3|3|
| Journaled domain total p95 |4,931.196ms|4,027.340ms|
| Domain p95 minus exact journal-write intervals |3,985.186ms|3,186.786ms|
| Retrieve+encode p95 |999.759ms|558.965ms|

These are **small, development-only successful-sample timings**; the failed baseline turn is retained separately. They are not a completed live held-out p95 or actual browser/HTTP end-to-end test, and do not erase previous spikes. Current v6 sampled process peak239.535MiB.

A fresh fixed three-pass full real held-out **runtime-only** benchmark completed all186 observations without inference:90warm samples/method, actual encoder/database, oracle intent/scripted generation, alternate method ordering, no per-turn disk writes. Proposed retrieve+encode p95 **717.448ms**; baseline **669.008ms**. Proposed per-pass p95 589.228/847.340/841.420ms; baseline1,007.422/698.775/502.777ms. All passes and slow samples remain visible. Combined runtime target passes; one baseline pass slightly misses1second. Peak220.109MiB. [All runtime observations](conversational-rag-r4-runtime-latency-v6.json)

## Accounting

| UTC2026-10-26 disjoint work | Charged calls | Reserved units |
| --- | ---: | ---: |
| Resumed v3 |19|140,675|
| V4, including interrupted checkpoint |8|60,295|
| V5 |5|36,578|
| Current v6 |18|155,946|
| **SQL-confirmed daily total** |**50**|**393,494**|

Previous UTC2026-10-25 remains49calls/390,773units. Cumulative retained evidence: **99calls/784,267reserved units across two days**. Current v6 provider-reported actual tokens35,719 are distinct from155,946reserved units; two earlier v3 transport failures have unknown actual tokens. No refunds/resets. All new live phases use original free-tier safeguards. No further reservation or provider call is permitted today by the application call ceiling, despite106,506token-unit headroom. [Daily/phase reconciliation, identities and mirror hashes](conversational-rag-r4-audit-2026-10-26.json)

## Verification and owner review

- **189 backend tests**, Ruff, strict mypy26, public OpenAPI/generated drift and frozen schema/dataset checks; no new frontend test or visual verdict claimed.
- Current actual catalog/encoder/API probe: **313 assertions**, mocked HTTP/accounting only; main results identical, real429/Retry-After30 retained, max-two/bounded schema bytes/canonical cards checked. Twelve warm mocked samples p95534.632ms, outside-stage p955.343ms, peak252.762MiB. [Probe](conversational-rag-r4-integration-v6.json)
- [Current nine-output owner worksheet](conversational-rag-r4-owner-review-development-v6.md), companion JSON and separate keys are prepared with **zero human ratings**. Older worksheets remain historical. Full paired held-out judgments and exhaustive relevance labels must come from the owner before quality/nonregression/Recall claims.

## Resume next UTC day — preserve both journal copies

**Authoritative journal:**
`C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5/conversational-rag-r4-development-v6.json`

**Workspace export:** `docs/reports/conversational-rag-r4-development-v6.json`.

The directory name containsv5 for storage lineage; the authoritative current filename is **v6**. Preserve this C: directory until handoff; do not clean it as disposable cache. In a crash it may contain newer started/granted attempts than E:, and it governs resume. Never restore an older export over it, delete a ledger to retry, edit its hashes, or resume v4. Source changes require a documented new revision, not hash replacement.

At/after **2026-10-27 00:00UTC**, obtain a fresh effective receipt:

```sql
select (clock_timestamp() at time zone 'UTC')::date as utc_day,
       case when day=(clock_timestamp() at time zone 'UTC')::date then calls else 0 end as used_calls,
       case when day=(clock_timestamp() at time zone 'UTC')::date then reserved_tokens else 0 end as used_tokens
from discovery.ai_usage_windows;
```

If that receipt actually reports October27 and zero usage, from repository root:

```powershell
& backend/.venv/Scripts/python.exe -m game_discovery.jobs.continue_chat_evaluation development --quota-day 2026-10-27 --used-calls 0 --used-tokens 0 --max-new-turns 6
```

Next work is proposed M01 turn2/3, C01/A01 and remaining title/semantic development cases for both methods. Baseline M05 turn3 remains skipped because turn2 failed. After full same-version proposed development gate passes, take another fresh receipt and run `held_out` through the same CLI, using actual counters. No new approval is required. No owned persistent evaluation/API process is left running.

**Acceptance remains open:** remaining development, full paired held-out live generation, representative live/HTTP total-latency evidence, mandatory/nonregression checks and owner relevance/grounding judgments. No M5, publication or measured end-to-end quality improvement claim.
