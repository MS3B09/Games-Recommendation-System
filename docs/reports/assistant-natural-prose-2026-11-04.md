# Contextual recommendation wording — November 4

**Implemented locally; restart the user's backend terminal to load it. Live wording acceptance is pending.** The owner likes the conversations but asked that recommendations explain their relevance naturally, rather than duplicating the description/genres/modes/platforms/prices already in each card's **View details**. This is a small follow-up, not a reopening of the completed five-story evaluation.

## Change

- Native and final-writer prompts now request a short, evidence-grounded reason connected to the user's actual request. Removed the instruction requiring verbatim promotional description quotes. No copied-description or metadata checklist by default; details remain appropriate for a direct question, a relevant reason or an important tradeoff. Unsupported qualities and claims remain disallowed.
- The renderer no longer appends its automatic per-passage price/date paragraph when every cited price has a matching returned game card. Cards, recorded USD prices, observation dates, evidence and the existing non-live-price notice remain unchanged. A cited price without its matching card still retains visible provenance in the prose.
- No new inference stage, retry, classifier, UI change, model, dependency, API/schema/storage change or quota change. Saved/temporary requirements, retrieval, canonical cards, memory and atomic validation are unchanged.

## Verification

Updated two existing dialogue checks; no new test methods or fixtures. Coverage checks both prompt paths, preservation of a short contextual reason, canonical details retained in the card, an explicitly requested price still answered, no duplicate price paragraph with a matching card, and provenance retained with no card or the wrong card.

- **279 backend tests OK (1 skipped),10.890s**, including the60 dialogue checks.
- Ruff, strict mypy30 and unchanged OpenAPI pass.
- Zero live provider calls/reservations from this follow-up; no frontend/browser campaign or retrieval benchmark rerun. Scripted prose is not evidence of real-provider naturalness or descriptive entailment.
- Read-only SQL09:07 and09:11UTC remains18calls/198,579reserved units; this includes activity outside the earlier frozen4-call closeout receipt and is not added to its evaluation audit. No counters or limits changed.

## Load the change

The current user-started API is launcher4140/serving16168 on8001, without reload. It was deliberately left running, so it still has the pre-follow-up code loaded. In that backend terminal, press **Ctrl+C**, then rerun the same backend startup command from `E:\Games-Recommendation-System`:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn game_discovery.api.main:app --host 127.0.0.1 --port 8001 --workers 1
```

Keep the existing session's CORS/BLAS settings and `backend/.env`; no configuration edits are needed. Preview17652 on4173 is unchanged; no frontend rebuild is needed. New replies use the updated guidance after restart. Existing archived messages are not rewritten; use a fresh chat for the cleanest manual wording check. Manual sends consume the ordinary shared allowance.

## Preserved evidence

The completed v10 journal remains SHA256 `67e251d6c8853aa6dbd2882120f9c0c74d96b4abc701087641edced95fc50a2d`; earlier31 attempts, snapshots, failures and ratings remain untouched. Its source identity intentionally no longer matches this follow-up: **never resume/replay it or replace its hashes.** No new live checkpoint or scenario matrix was prepared.

Prechange source, tests and public completed journal are archived at `C:/Users/User/AppData/Local/Temp/opencode/assistant-natural-prose-prechange-20261104T090238Z.zip`, SHA256 `eaac6448a9272bbd341ee8faed5217a6b1f1bd9d0bf26c2af1b4d207bc3947c3`, byte-verified; no private capability was included. New `dialogue.py` SHA256 `53607223445502759ce8071d8c1936ad286def58fb2a068fa3f89b6759ec4dc1`,837lines.

The owner's positive conversational feedback is qualitative, not invented per-turn ratings or formal acceptance. No live post-change quality claim, commit/push/deploy/publication or M5.
