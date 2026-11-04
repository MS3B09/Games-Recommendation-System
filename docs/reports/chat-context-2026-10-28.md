# Context-aware chat follow-ups — 2026-10-28

Owner requested a real LLM conversation with catalog access and memory after a zombie-game recommendation followed by “Which one support Local Co Op play style ?” returned the friendly 502 validation error. Implemented and verified locally.

## Findings

The prior chatbot had scoped preference memory and recent canonical IDs, but the LLM did not receive sufficient conversational context:

- Interpretation projected only the last eight messages, taking the last 700 characters of each. It received reference counts, not canonical game titles.
- Answer generation received the latest question, soft intent and retrieved evidence, **without the conversation transcript**.
- The internal `TurnPlan` required a single target for `game_facts` and exactly two for comparison. A reasonable model output such as `game_facts` + `last_pair` was rejected before retrieval.
- Serving also rewrote some LLM interpretations using current-message played/undo and genre keyword rules.

The original owner's failed request is not in the retained local API logs, so its precise rejection cannot be reconstructed. These are confirmed implementation limitations, not a claim to have recovered that original model output.

## Changes

- Both LLM stages now receive the retained conversation messages, complete and chronological when they fit. The old eight-message/700-character projection is removed.
- Interpretation resolves the current shown/referenced catalog IDs to canonical titles before calling the model. Display positions and recent fact targets are distinguished.
- Internal fact/compare plans accept up to four explicit titles, all currently shown games, or a validated positional subset. Single-game and pair references remain supported. The public v2 state and API response shapes stay compatible.
- Instructions tell the LLM to resolve ellipsis, pronouns, older titles and feature questions by meaning. When canonical names are known, explicit title targets are preferred. A question about features of prior recommendations does not itself establish a new recommendation requirement.
- `ConversationalRAG` validates the LLM's plan directly. The former `chat_explicit.py` overrides remain labeled historical and are not invoked by serving. Hard-filter enforcement, canonical identity checks and evidence validation remain backend responsibilities.
- Generation receives the relevant catalog facts for every resolved target, including recorded modes. It distinguishes local co-op from online co-op and does not treat missing support evidence as proof of real-world absence.
- Named recommendation operations with no new soft query retain an existing chat topic before falling back to a named-game anchor.
- Added safe local failure diagnostics: stage and validation issue types / allowlisted failure codes only. No raw prompts, outputs, arbitrary unknown keys or exception messages are logged.

### Context bounds

“Conversation context” means the existing retained tab conversation: at most 20 messages / 12,000 text characters, plus scoped preferences, exclusions and canonical references. Each provider request still has a 12,000-UTF-8-byte bound including instructions and answer schema. Complete messages are retained when possible; older whole messages yield under pressure, with `context_truncated` passed to the model. Required hard criteria and fact evidence are preserved. Large history does not force recommendation evidence down to one game: four candidate packets are preserved before dropping old conversation text, when the required evidence fits.

This is not unlimited history or cross-chat memory. Main favorites/limits/saves/history remain outside chat context. New chat and existing storage/retry behavior remain compatible.

## Verification

- **210 backend tests pass**, including nine new context regressions: the exact reported question; single/pair/four-game and positional facts; full older messages in both LLM stages; UTF-8 overflow and retained modes; older-title resolution after a one-card answer; transcript/evidence balance; no keyword override in serving; safe diagnostic redaction.
- Ruff passes for `src` and `tests`; strict mypy passes all 27 configured source files.
- `python -m game_discovery.api.export_schema --output openapi.json --check` passes with configuration-independent startup. Public OpenAPI and browser session schemas do not change.
- [Final actual-catalog/encoder scripted probe](chat-context-catalog-final-2026-10-28.json): **203 checks pass**, zero live calls/reservations/database writes. Retained [earlier successful probe](chat-context-catalog-2026-10-28.json). These are integration checks, not model-quality or latency acceptance.
- Real browser → preview:4173 → API:8001 → restricted catalog + configured Groq verified these delivered turns:

| Turn | User request | Actual answer | Evidence |
| --- | --- | --- | --- |
| 1 | Recommend two zombie games. | Dying Light and Project Zomboid | [200 response](chat-context-live-2026-10-28-turn1.json) |
| 2 | Which one support Local Co Op play style ? | “Project Zomboid supports Local Co‑Op.” | [200 response](chat-context-live-2026-10-28-turn2.json) |
| 3 | And the other one—can we play it together online? | “Yes, Dying Light supports online co‑op play.” | [200 response after correction](chat-context-live-2026-10-28-turn3.json) |
| 4 | Between the original two you recommended, which could my friend and I play together on the same couch? | Project Zomboid, with recorded local co-op | [200 response](chat-context-live-2026-10-28-turn4.json) |

After the final backend restart, reloaded the browser and reopened the assistant: all four delivered exchanges were restored, including the original local-co-op question, the other-game answer and the older-pair couch question/answer. No alert was shown. This reload check made no new chat-generation request.

### Retained failures and development diagnostics

This was not an all-green first live attempt. Before the final reference-instruction correction, turn 3 first returned [database 503](chat-context-live-2026-10-28-turn3-failure.json), then its explicit visible retry returned [validation 502](chat-context-live-2026-10-28-turn3-validation-failure.json). A separately recorded, single-call [planner diagnostic](chat-context-planner-diagnostic-2026-10-28.json) reproduced an invalid combination of `reference:last_shown` and `shown_positions:[2]` after the latest response displayed one card. The LLM needed clearer distinction between the prior pair and current card positions. The revised prompt prioritizes canonical title names and exclusive target mechanisms. The identical follow-up then succeeded through the visible Edit message/resubmit action. No automatic provider retry was added; the earlier failures remain saved.

The diagnostic initially could not open an additional runtime database connection while the API was running: the runtime role reported too many connections. Stopping only the identity-verified API owned by this session freed its slots; the diagnostic then completed. This did not alter database limits or terminate remote sessions. Its final console print encountered Windows character encoding after the JSON evidence had already been saved; it was not re-executed.

The first concurrent actual-encoder probe exited with an OpenBLAS allocation failure. Subsequent probes ran with `OPENBLAS_NUM_THREADS=1`; the final one ran sequentially while this session's API was stopped, then the API was restored. No model files were changed/downloaded.

### Live accounting

Read-only SQL before testing: **17 calls / 125,215 reserved units** for UTC October 28 at 17:37:20. After testing: **27 calls / 203,889 units** at 17:53:27. Delta: **10 calls / 78,674 units**: eight for the four delivered turns, one failed interpretation, one standalone interpretation diagnostic. The database-failed turn made no provider reservation. These are new bug-fix checks, not continuation/replay of the frozen R4 experiment. Runtime quota values, counters and throttles were not reset or modified.

## Preservation and operation

Before source edits, archived the AI source directory and the two changed pre-existing tests at `C:/Users/User/AppData/Local/Temp/opencode/chat-context-prechange-2026-10-28.zip`, SHA-256 `6b8f80a4f11f02f1d5a9dddd08af4c4466d5340a52d26699d055f4d406ebabb5`.

This owner-requested serving revision intentionally expands the **internal** planner schema and changes prompts/memory projection. The old frozen R0 `TurnPlan` schema, R4 journals, original source hashes, backups and held-out cases were not edited. The frozen `ChatStateV2` schema still matches serving. The regression now explicitly checks the internal planner amendment rather than claiming it remains identical to R0. **Do not resume frozen v6 evaluation against this new serving source or replace its stored hashes.** R4 quality/human/latency acceptance is still incomplete; later live evaluation requires a separately versioned continuation.

At handoff the final source is loaded by API launcher **18372**, serving child **8880** on :8001; preview **19676** on :4173 is reused. Parent/command-line/listener identities verified. Recheck identities before stopping. Open **http://127.0.0.1:4173/** and refresh. Existing v2 chats can continue; no new credentials or environment changes are required.

No frontend implementation, migration/schema update, dependency/model change, commit, push, deployment or M5 work.
