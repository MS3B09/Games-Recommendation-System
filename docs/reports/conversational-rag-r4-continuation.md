# R4 reliability fixes and multi-day evaluation checkpoint

> **Historical October25 checkpoint. Current authority is the [October26 resume/v6 report](conversational-rag-r4-resume-2026-10-26.md).** V3 is now completed with retained failures; resume the v6 authoritative C: journal, not this report's old v3 commands. UTC2026-10-26 usage50calls/393,494units; additional inference remains approved for later UTC days.

**2026-10-25 · Engineering fixes verified; R4 acceptance remains INCOMPLETE.** Owner approved additional inference as needed within existing free-tier limits and directed completion of all remaining R4 issues. That authorization supersedes the exhausted original pilot allowance. The current blocker is the **daily application ceiling**, not missing approval or credentials. [Initial report/failures](conversational-rag-evaluation.md) · [Plan](../conversational-rag-plan.md) · [Continuation policy](../../data/evaluation/chat-rag-r4-continuation.json)

## Verified changes

1. **Bound generation before decoding.** The existing metered Groq transport now sends a strict JSON Schema for chat answers, including `game_ids.maxItems:4`. The configured `openai/gpt-oss-120b` supports constrained decoding. Canonical ID, distinctness, supplied-evidence, hard-condition and exact-claim validators remain intact. Six IDs are still rejected by the backend regression; outputs are not truncated or regenerated. Interpretation and legacy discovery retain JSON-object mode. No model/dependency/configuration change.
2. **Count schema bytes.** The strict response format is included in the conservative 12,000-byte input accounting and evidence packing, as well as the existing +1,280 reservation allowance. Redundant, nonclaimable description citation metadata was removed to retain useful evidence capacity. Requested facts, canonical facts and excerpts remain. Retrieval IDs and actual generation-packet IDs remain distinct.
3. **Correct unsupported-platform metadata.** Unsupported-platform clarifications now carry `retrieval_unavailable`, no invented platform support, no encoder-failure reason, no catalog query and no state commit. Generic clarifications retain their previous metadata. The frozen C06 offline expectation now passes for both methods.
4. **Reduce transaction round trips.** SQLAlchemy/Psycopg establishes READ ONLY in BEGIN; role/version/transaction-local timeout are checked together. Repeatable-read, the elevated-role refusal and active-version requirement remain. Main ranking SQL/weights are unchanged. Actual probe confirms read-only **on**, repeatable read and 2s statement timeout, then pooled read-only **off** and original 5s timeout restored. Successful subsequent live reservations also exercise that pool boundary.
5. **Fix follow-up reference interpretation.** A first strict-output development run exposed an invented `last_pair` for “more multiplayer options.” The revised prompt distinguishes generic continuation from explicit demonstrative references and acknowledges a found canonical fact target before mismatch notes. The failed behavior is preserved in the v2 ledger, not rewritten as success.
6. **Tighten the evaluator.** A delivered clarification is not automatically a successful recommendation: expected recommendation turns must actually perform retrieval. Expected hard constraints are checked even when the interpreted kind is wrong. Human scores remain null. Continuation journals freeze serving/evaluator/policy hashes, alternate method order per case, checkpoint before reservations, refuse source drift, preserve failed/started turns and pause before a turn without two worst-case calls of observed daily allowance.

`ChatAnswer` moved to internal chat contracts for schema reuse; frozen `TurnPlan`, v2 state and retrieval-outcome schemas, public OpenAPI and generated TypeScript remain unchanged. The HTTP response schema is not a database migration or a relaxation of the public card limit.

## Latency: runtime target now measured separately from journal overhead

The development SQL plan executes in **0.676 ms**; earlier profile **0.806 ms**. Network/transaction overhead dominates. Fixed development-query warm p95 was 740.920ms before and 452.495ms in the final guarded profile. These are separate small measurements, not controlled proof that all improvement came from the code change. [Before](conversational-rag-r4-latency-before.json) · [After](conversational-rag-r4-latency-after.json) · [Guard/pool verification](conversational-rag-r4-latency-guards-v2.json)

The normal journaled offline repeat still had slow samples: proposed held-out retrieve p95 **1,644.813 ms**, baseline **2,689.634 ms**, including individual multi-second observations. Those results remain retained, alongside the original 2,574.066ms proposed finding. They are not replaced with the faster development number. [Development repeat](conversational-rag-r4-development-verified-v2.json) · [Held-out repeat](conversational-rag-r4-held-out-verified-v2.json)

A dedicated runtime benchmark was therefore fixed **before its first timed observation**: three full passes of all 31 real held-out turns per method, alternating method order by case/pass, actual encoder/restricted remote database, oracle interpretation/scripted output, no per-turn journal writes inside the measured sequence, no inference/retries or ranking changes. All 186 observations completed; first method turn of each pass is cold, leaving **90 warm observations per method**. Slow observations are retained, not filtered by threshold.

| Runtime-only warm retrieval + encoding | Proposed | Cosine-only baseline |
| --- | ---: | ---: |
| p95, all 90 warm observations | **487.187 ms** | **415.599 ms** |
| Pass 1 p95, 30 warm observations |494.355 ms|413.019 ms|
| Pass 2 p95, 30 warm observations |487.187 ms|417.694 ms|
| Pass 3 p95, 30 warm observations |474.376 ms|415.599 ms|

Sampled process peak **221.223 MiB**. This meets the local runtime retrieval target under this declared benchmark protocol. It does not erase the journaled spikes or establish hosted feasibility. [All observations/protocol](conversational-rag-r4-runtime-latency-v3.json)

**Total live answer latency is still not accepted.** Current v3 proposed journaled warm total p95 is **12,772.578 ms** on six samples; baseline **12,320.529 ms** on five. These include repeated durable diagnostic writes/reservation bookkeeping and are not clean serving-only timings. Current live retrieval p95 is809.129/514.598ms. No claim of live total p95 ≤10s follows. A serving-vs-journal timing separation must be measured before clearing that gate; no extra calls were made after today's pause.

## Real provider observations and retained development failure

### Version 2 — six attempted turns, eleven calls

Strict schema was accepted; all attempted transport outputs delivered. Proposed M01 turn3, however, invented `reference:last_pair` and returned “Which games do you mean?” instead of retrieving more multiplayer games. This is a **behavior failure**, despite its successful HTTP/shape delivery. Its original summary predates the stronger retrieval-performed check; the [read-only audit](conversational-rag-r4-continuation-audit.json) explicitly identifies `M01:3`. No all-green journey or functional 3/3 claim is made for v2. [Retained v2 ledger](conversational-rag-r4-development-v2.json)

### Version 3 — current frozen checkpoint

The revised proposed **M01 passes all three mandatory turns**: four canonical multiplayer cards; correct Spider-Man title/single-player mismatch with multiplayer provenance retained; then three eligible multiplayer cards, no Spider-Man, and actual recommendation retrieval. No six-ID format error. Baseline delivered all three too, but its no-selected-card fact answer has `found` rather than expected `found_but_mismatch` metadata; that miss remains visible.

Current v3 records: **13/26 development method-turns** — proposed7/13, baseline6/13. All13 attempted turns delivered; proposed observed state/constraint/outcome checks pass, target Hit@5 is3/3 for each method. S04 has only proposed output so far; there is no complete paired quality comparison or human relevance score. Next unattempted work is baseline S04, then M05, C01 and A01 for both methods. Full held-out live generation has **not started**: it requires the full same-version proposed development gate first. [Current v3 ledger](conversational-rag-r4-development-v3.json)

No-call recorded-output replay reproduced all **26 v3 input packets byte-for-byte**, with no unsupplied selections/claims or replay errors. The replay tool now groups by case as well as method/turn and resets state across cases. [Replay](conversational-rag-r4-development-v3-replay.json)

## Accounting and checkpoint

| Disjoint accounting phase | Calls | Reserved units | Provider-reported actual tokens |
| --- | ---: | ---: | ---: |
| Original pilot + revision (count aggregate once) |12|92,813|not captured by that adapter version|
| New v2 continuation |11|85,620|19,038|
| Current v3 continuation to pause |26|212,340|47,311|
| **SQL-confirmed UTC 2026-10-25 total** |**49**|**390,773**|unknown for all phases combined|

All37 new reservations were granted; all37 new provider attempts returned JSON. Actual tokens for those new calls total66,349; they do not refund conservative reserved units. Both original ledger SHA-256 values are unchanged. [Reconciliation/hashes](conversational-rag-r4-continuation-audit.json)

Observed shared remainder: **one call /109,227 reserved units**. A normal recommendation turn requires two calls; the runner paused **before attempting it**, with no denied reservation or failed partial turn. No reset, bypass, hidden provider retry, paid service, catalog/model/environment/dependency/schema change, commit/push/deploy/M5. Approval for future free-tier days remains valid. SQL receipts are read-only; only approved application accounting writes occurred.

The v3 ledger is `paused_daily_quota`, its normal process lock was removed, and no owned persistent API/evaluation process remains. It can resume after a fresh UTC-day receipt without replaying earlier turns. Source identity must remain frozen; docs/review changes do not affect it. Do not delete a ledger or change its source hashes to bypass the guard.

Two new offline interruptions are also retained: combined v2 run stopped at a tool timeout, and first development repeat stopped on a Windows checkpoint sharing `PermissionError`. Separate bounded repeats completed. Checkpoint writes now flush/fsync and retry only the atomic **filesystem rename** up to five times for transient Windows sharing locks. This never retries inference or reservations. Partial JSON, temporary/lock artifacts remain visible; they are not scored as completed runs or used as live checkpoints.

## Verification and human handoff

- Backend suite **180 tests**; Ruff; strict mypy25; public OpenAPI/generated drift; six R0 contract tests and frozen hashes.
- Actual catalog/encoder + existing API integration probe: **313 assertions**, mocked HTTP/accounting only, canonical cards/constraints/exclusion/undo/main results unchanged, actual429/Retry-After30 retained. Twelve warm mocked samples total p95 **496.723ms**, outside-stage p95 **5.479ms**, peak **252.699MiB**. Not live quality/hosted proof. [Probe](conversational-rag-r4-integration-v3.json)
- Security advisory scan has no findings. Performance advisory had only informational unused-index notices; indexes were retained. [Advisory explanation](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index)
- Frontend implementation/assets unchanged; R3 browser/49tests/6scans remain dated evidence, not new R4 UI checks. Final frontend build targets API:8001. Restart backend to use these fixes; no new setup or credential needed.
- [Owner review worksheet](conversational-rag-r4-owner-review-development-v3.md) and companion JSON contain13 current development outputs with per-case masked method labels, canonical evidence and **null ratings**. Mapping is separate in `.keys.json`. This is preparation, not independent/human review. The scoring helper refuses a human nonregression pass without all62 held-out method-turn judgments and explicit owner confirmation. Recall@8 needs paired exhaustive human relevance labels; anchor seeds never become Recall labels. Full held-out worksheet comes after its outputs exist.

## Resume within existing authorization

Read-only SQL preflight (MCP or trusted developer connection), with effective current-day counters:

```sql
select (clock_timestamp() at time zone 'UTC')::date as utc_day,
       case when day=(clock_timestamp() at time zone 'UTC')::date then calls else 0 end as used_calls,
       case when day=(clock_timestamp() at time zone 'UTC')::date then reserved_tokens else 0 end as used_tokens
from discovery.ai_usage_windows;
```

From repository root, use the receipt's actual date/counters; zero counters below apply only if that fresh receipt actually reports zero:

```powershell
& backend/.venv/Scripts/python.exe -m game_discovery.jobs.continue_chat_evaluation development --quota-day 2026-10-26 --used-calls 0 --used-tokens 0 --max-new-turns 6
# After same-version development completes and passes, take another fresh receipt:
& backend/.venv/Scripts/python.exe -m game_discovery.jobs.continue_chat_evaluation held_out --quota-day 2026-10-26 --used-calls <receipt-calls> --used-tokens <receipt-tokens> --max-new-turns 6
```

The placeholder second command is illustrative, not executable as written. No fresh phase approval is needed. Before spending held-out calls, finish development, separate serving latency from journal instrumentation, and freeze any approved development-only fixes under an explicit new revision if necessary; never silently mix versions. Current remaining full-run conservative bound is150calls/1,992,000reserved units (26development +124held-out calls), so multiple UTC days remain necessary. A later source revision can require further development verification.

**Acceptance still pending:** remaining development/live comparison, serving-only total latency, owner relevance/grounding/Recall labels and the frozen nonregression/mandatory gates. No measured end-to-end improvement, whole-product acceptance, M5 or publication claim.
