# Temporary R4 quota increase — applied and verified

**Owner-approved change complete. R4 evaluation acceptance remains INCOMPLETE.** Approved on2026-10-26; application verified after UTC rollover on2026-10-27. [Operational amendment](../../data/evaluation/chat-rag-r4-quota-amendment.json) · [Prior v6 checkpoint](conversational-rag-r4-resume-2026-10-26.md)

## Applied allowance

| Layer | Normal default | Temporary R4 runtime / hard maximum |
| --- | ---: | ---: |
| Calls/day |50|**100**|
| Conservative reserved units/day |500,000|**1,500,000**|

`core/settings.py` accepts the approved maxima while retaining normal defaults. Only `AI_DAILY_CALLS` and `AI_DAILY_TOKENS` changed in ignored `backend/.env`; no secrets were read into documentation or changed. The example retains normal values with a temporary-R4 note. Restart an existing backend to load the runtime update; new evaluation processes already use it.

New application Alembic revision **0005**, SQL file `0006_r4_ai_budget_limits.sql`, expands the two table checks and the reservation function's admitted maxima. Four calls/minute,30-second peer throttle, one concurrent turn, maximum two calls/turn, per-call/input/output/socket-timeout bounds, UTC rollover, RLS and restricted grants remain. No paid plan, key rotation, model/catalog/prompt/ranking/frontend/public-wire change.

The applied migration locked the counter table and asserted its before/after JSON equality within the same transaction. It preserved the entire retained row: day2026-10-26, **50calls/393,494reserved units**, minute2026-10-26T17:33:00Z, minute_calls2. Application Alembic metadata advanced0004→0005 atomically. No counter reset/refund. The next day's rollover occurred only on the next normal committed reservation.

## Verification

- [Scratch database checks](r4-quota-increase-scratch-2026-10-26.json): **15 passed**, isolated scratch schema cleaned. Tests cover retaining all used counters, granting call51, concurrent stopping at100calls/1,500,000units, rejecting excessive/per-call-invalid limits, lower-runtime restoration without clearing counters, restart protection, four/minute, private counters and normal UTC rollover. Python validation tests also reject nonpositive configured limits.
- [Applied runtime probe](r4-quota-increase-live-verification.json): actual restricted runtime successfully reserved inside a transaction that was **rolled back**, with before/after retained row identical. **Zero provider calls or committed application reservations** in that probe. Runtime settings100/1,500,000 and normal defaults50/500,000 verified.
- Database postflight confirms RLS enabled, minute check≤4, runtime can execute the reservation function but cannot directly read/update counters, application Alembic0005 and zero leftover scratch schemas. Security advisor has no findings.
- **193 backend tests**, Ruff, strict mypy26, OpenAPI/generated/frozen checks. An initial parallel unit run timed out; the sequential full repeat passed193tests in12.105s. Historical successful checks are not substituted for the failed timed run.

## Same experiment, documented quota-only amendment

The source-frozen v6 runner/model/prompts/ranking/evidence/validators/dataset remain byte-identical. No original source hash was replaced. `jobs/resume_chat_quota.py` invokes that runner through an explicit operational wrapper; its SHA and amendment SHA are recorded separately in each journal. It validates the approved runtime settings, source identity and development gate, and accepts receipts up to the new daily maximum instead of the original CLI's50-call receipt ceiling.

The pre-amendment development checkpoint is preserved byte-exactly in the authoritative C: folder as `conversational-rag-r4-development-v6-before-quota-amendment.json`, SHA256 `f5b670b6bdd26bb5f3effce46f01dfb7f85f42f108ca7d6501cbf2bc1855e7de`. Its **9 records/18 attempts** remain an unchanged prefix of the continued journal. Original pilot ledger hashes also remain unchanged. Failed, started and dependent-skipped work is never replayed or reclassified as success. [Prefix/source/accounting audit](r4-quota-amendment-audit-2026-10-27.json)

## Provider free-tier controls are separate

[Groq's published limits](https://console.groq.com/docs/rate-limits) list GPT-OSS120b free limits of1,000requests/day,8,000tokens/minute and200,000tokens/day; exact organization limits may differ. Live response headers for this key confirm request limit**1,000** and token/minute limit**8,000**. Tokens/day are not exposed by those headers and are not claimed as account-verified. App reserved units are not actual provider tokens; cached tokens can make provider rate accounting lower than our conservative count.

The wrapper stores only whitelisted rate headers, not credentials or response bodies, in the approved local journal folder. Evaluation spacing is at least**60.1s after the preceding turn**, while the application's30-second peer throttle and four/minute protection remain unchanged. It conservatively accounts for owned-journal actual tokens, substitutes reservation bounds for missing usage, and requires26,560units of headroom for the next worst-case two-call turn under a200,000daily local guard. Other organization usage can cause an earlier provider limit.429/payment-required responses are retained and pause work; there is no automatic transport retry or paid escalation.

**Current pause is this local conservative provider-headroom guard, not an observed Groq429 or exhausted application ceiling.** On2026-10-27, owned reported token units are**174,975**. Adding the next worst-case turn26,560 would total**201,535**, above the guard. The app still has five calls and721,931reserved units available; the guard deliberately does not spend them speculatively. Do not describe this as confirmed exhaustion of the organization's actual token quota.

## Evaluation progress after the increase

### Development — complete with retained baseline failure

[Development journal/export](conversational-rag-r4-development-v6.json): **25 attempted of26planned method-turns**,49provider calls across both days. Proposed13/13delivered; target Hit@5 5/5, seed coverage2/2, annotated outcome checks4/4, observed hard-card/state failures0. Baseline11/12delivered, with its earlier claim for unselected620 rejected and dependent M05turn3 skipped. Its title hits4/4 are conditional on delivered turns, not a denominator hiding failure. The proposed same-version development gate passed before held-out calls began.

Proposed development warm delivered total p95**13,783.175ms**, minus exact journal IO domainp95**12,888.501ms**; baseline7,527.446/7,023.565ms. Earlier fast samples are not a general10-second pass. Human relevance and claim rates remain null.

### Held-out — underway, failures retained, no tuning

[Held-out journal/export](conversational-rag-r4-held_out-v6.json): **32 attempted of62planned method-turns**,64provider calls. Proposed12/16delivered; baseline12/16delivered. Both methods failed T02, S07, M02turn1 and M03turn1 with `chat_invalid_prose`, including numeric price/budget prose prohibited by the existing contract. M02/M03dependent turns remain skipped. Nothing was truncated, regenerated or tuned on held-out results. The mandatory all-pass gate is therefore not satisfied.

Both methods have5/5 conditional title hits and3/4 semantic seed coverage so far; not full quality/Recall metrics. Delivered-card hard violations0, observed state failures0. Twenty-six further method-turns remain unattempted; four dependent turns are skipped. Next case is M06. Human judgments remain unscored.

Current warm delivered held-out domain total p95**6,787.905ms proposed /15,401.564ms baseline**; minus exact journal IO**6,089.848/14,921.459ms**. Baseline has an encoder observation10,551.491ms. Slow samples and failures remain; no hosted/HTTP/full-latency pass or measured relevance improvement is claimed.

### Accounting reconciliation

| UTC day | Committed application calls | Reserved units |
| --- | ---: | ---: |
|2026-10-25|49|390,773|
|2026-10-26|50|393,494|
|**2026-10-27**|**95**|**778,069**|
|**Retained cumulative evidence**|**194**|**1,562,336**|

Today's95calls are31development continuation +64held-out. Raising the ceilings demonstrably allowed use beyond both former50calls and500,000reserved-unit limits without clearing counters. [Audit](r4-quota-amendment-audit-2026-10-27.json) matches read-only SQL; C: authoritative journals and E: exports match, frozen source identities match.

[Development replay](r4-quota-development-replay-2026-10-27.json) and [held-out replay](r4-quota-held-out-replay-2026-10-27.json) reproduce **all113current v6 packets byte-exactly**, including the recorded failures, with zero new provider calls/reservations. Method-masked owner worksheets are prepared for[25development outputs](r4-development-owner-review-2026-10-27.md) and[32held-out outputs](r4-held-out-owner-review-2026-10-27.md), all ratings null. Rejected generated prose is labeled explicitly as not delivered to the user. No agent judgment is represented as a human rating.

## Resume and restore

Preserve `C:/Users/User/AppData/Local/Temp/opencode/r4-evaluation-v5/` as authoritative durable data, including both v6 journals, the byte-exact pre-amendment backup and provider-rate sidecar. E: `docs/reports/` mirrors each completed turn. Never restore an older export over C: or edit source/amendment hashes. Original interrupted v4 remains abandoned evidence.

Use the **quota-aware wrapper**, not the original50-call CLI receipt parser. Obtain a fresh effective UTC-day SQL receipt as in the prior report, then use its actual values. If the receipt on October28 reports zero:

```powershell
& backend/.venv/Scripts/python.exe -m game_discovery.jobs.resume_chat_quota held_out --quota-day 2026-10-28 --used-calls 0 --used-tokens 0 --max-new-turns 6
```

Provider windows and other organization usage remain independent of the application's UTC rollover. No new approval or credentials are needed for remaining authorized R4 work. Current source is frozen; no owned persistent API/evaluation process is left running.

**After R4**, restore ignored runtime configuration to `AI_DAILY_CALLS=50` / `AI_DAILY_TOKENS=500000` and restart the backend. Keep consumed counters. If that day's usage exceeds the restored limits, subsequent inference is denied until normal rollover. Do not downgrade constraints over existing usage or delete/refund counters. Database maxima can remain at the approved ceiling while lower runtime values enforce normal operation.

**Remaining R4 gates:** finish unattempted frozen held-out work, obtain owner relevance/prose/retrieval labels, report the observed mandatory-case failures and latency misses honestly, and resolve the acceptance decision. Quota implementation is complete; R4 is not accepted. Publication/M5/commit/push remain unauthorized.
