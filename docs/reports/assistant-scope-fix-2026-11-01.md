# v36 — budget scope corrected; live continuation needs provider headroom

> Superseded by [November2 continuation and memory stop](assistant-resume-2026-11-02.md). V36's pending follow-up was attempted and failed; its remaining paths are closed. Do not use the old continuation command against changed source.

## Latest read-only check — November2 02:03UTC

SQL02:02:44UTC confirms the application's new-day allowance is100calls/1,500,000units, with0effective use. Source identity still matches v36; D36Pfollow-up remains untouched. However, all63owned model calls are still within the preceding24hours:160,302+39,840=200,142>200Kplanning ceiling. The first completed-turn usage ages out at **November2 12:54:41UTC**; **12:55UTC** is the earliest useful conservative-owned-window recheck, not a claim about Groq's actual reset. An earlier restart still requires actual organization allowance/reset evidence. No inference, reservations, tests, source/config changes or API restart. API8001is absent; preview17652remains on4173. Earlier SQL/process snapshots below are historical.

## Implemented

Discovery now makes one native, typed `requirements_action` decision:

- `save_normal`: propose the requested normal filter changes.
- `temporary`: apply overrides to this search without persisting them.
- `use_saved`: use saved requirements, requiring empty overrides. Conflicting arguments return bounded correction feedback instead of running the wrong query.

The proposal commits only after the existing final answer/card/evidence validation succeeds. The final writer no longer chooses preference scope a second time; it can still add ordinary sourced memory. No search or refused page can commit a proposal on its own. Non-search corrections still use the existing typed preferences object. Public API/UI/storage contracts, model, limits, services and dependencies are unchanged; no classifier or title-specific serving rule was added.

The initial v35 attempt chose the wrong native action, then leaked internal IDs in its draft. It was rejected without committing preferences; its failure/two dependent skips remain preserved. V36 removes the contradictory “normal searches use saved filters” instruction for requests that are actually saving NEW requirements, and clarifies correction feedback. No failed turn was replayed or identity hash edited.

## Verification evidence

Current source:

```text
python -m unittest test_dialogue
Ran 59 tests in 1.821s — OK
python -m ruff check .../ai/dialogue.py .../tests/test_dialogue.py
All checks passed!
python -m mypy --config-file backend/pyproject.toml --cache-dir C:/Users/User/AppData/Local/Temp/opencode/mypy-assistant-v35 backend/src/game_discovery/ai/dialogue.py
Success: no issues found in 1 source file
```

These are the existing affected-module tests, not new test methods or a broad suite. They cover saved→temporary→restored searches, conflicting saved arguments, retained preference/memory operations, invented-price rejection, refused-page rollback and request-size bounds. The first type-check attempt stalled on the project-drive cache; its owned process was stopped and the same check succeeded with a C: cache.

**Actual v36 budget scenario: three searches / six model calls, all HTTP200.** Independent read-only catalog comparison verified all nine displayed card snapshots and hard predicates:

| Turn | Native action | Actual filters | Persistent update |
| --- | --- | --- | --- |
| Normal | `save_normal` | Windows/single-player/max2050cents inclusive | Conversation-scoped2050 saved |
| Exception | `temporary` | Windows/single-player/min2051/max4100 | None |
| Restored | `use_saved` | Windows/single-player/max2050 | None; saved2050 retained and stated |

Actual Dead Cells lookup also passed its independent record comparison: Windows/macOS/Linux, single-player,2499cents observed2026-10-14. Its compatibility follow-up has not yet run. No broad relevance, full naturalness, long-memory or representative performance acceptance is claimed. UI/public wire did not change; browser/full-backend/full-frontend suites were not rerun.

## Exact stop and what only the owner can verify

SQL `2026-11-01T15:27:44.405629+00:00`: **63calls/697,062reserved units used;37calls/802,938units remain** under100/1.5M. All63owned calls have usage:160,302reported tokens. Another allowed three-call worst-case turn reserves39,840:

**160,302 +39,840 =200,142 >200,000 provider planning ceiling.**

No new429 or actual provider exhaustion is asserted. Increasing the application's cap does not establish more Groq free-tier headroom. Current Groq documentation still lists200KTPD for `openai/gpt-oss-120b`; response headers expose request/day and token/minute balances, not token/day balance. Cached tokens are exempt, so reported totals can overestimate actual debit. Do not lower the guard or infer a reset from app UTC rollover.

**Owner action:** check the signed-in [Groq organization Limits page](https://console.groq.com/settings/limits) and current usage/reset information for this model. Evidence of enough remaining free-tier allowance for a full turn, or an applicable fresh reset, is needed before more inference. No secret key, paid upgrade, model switch or application-cap increase is requested.

## Durable continuation

Authoritative checkpoint: `C:/Users/User/AppData/Local/Temp/opencode/assistant-closeout-capability-development-v36.json`, source/config matched and explicitly paused before another call. Next untouched turn is **D36Pturn2**, then D36Rthree turns. D36B is finished/erased; the failed v35archive independently404. D36P's one completed-turn archive is deliberately retained for its dependent follow-up; its capability stays private in C:. No generation is pending or running in the background.

After verifying applicable provider headroom and a fresh SQL receipt, continue one turn at a time:

```powershell
.\backend\.venv\Scripts\python.exe -m game_discovery.jobs.evaluate_dialogue_live --split development --cases data/evaluation/dialogue-v25.json --case-order D36B D36P D36R --max-new-turns 1 --output "C:/Users/User/AppData/Local/Temp/opencode/assistant-closeout-capability-development-v36.json"
```

API5012/child22376on8001and preview17652on4173were verified; catalog/semantic/AI ready. Recheck identities; a missing API uses the existing C: helper with `--version v36`. Memory improved to about1.9GiBphysical/3.4GiBvirtual free; it is not the current blocker. No config, dependency, migration, quota, commit/push/deploy/paid-resource/M5 change.

Development must finish before discovery development and unchanged held-out work. Four capability-development turns plus discovery10/held-out62 remain; existing owner relevance judgments are also pending. **This is not yet the final owner-quality acceptance stage.**

Evidence: [paused audit/source hashes/SQL](assistant-closeout-audit-2026-11-01-v36-paused.json), [budget predicate/canonical check](assistant-closeout-budget-v36.json), [fact record check](assistant-closeout-facts-v36.json), [63allowlisted provider receipts](assistant-provider-rate-receipts-2026-11-01-v36.json). All older failures, original owner judgments and held-out fixtures remain intact.
