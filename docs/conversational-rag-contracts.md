# Conversational RAG — frozen R0 contract and transition design

**Current native assistant — 2026-10-29:** the owner approved a new LLM-first `/api/v2/assistant` flow with backend-scoped archive memory, superseding the old no-database-memory restriction for current chat. [Current implementation and incomplete acceptance](reports/llm-first-assistant-2026-10-29.md). The frozen R0/v6 contracts and artifacts below remain historical and unchanged; v1 callers remain compatible. Do not edit their hashes or run their frozen evaluation on the new source. The current native v13 checkpoint has fresh v3 cases and must resume only unattempted work after a fresh applicable free-tier receipt.

**Owner-requested serving amendment — 2026-10-28:** [Context-aware chat follow-ups](reports/chat-context-2026-10-28.md) supersedes the serving-only restrictions in the frozen tables below: internal `TurnPlan` now accepts up to four title targets, `last_shown`, displayed subsets and multi-target fact inspection; both provider stages receive retained chronological messages when they fit. Canonical current/recent names accompany interpretation; LLM intent is no longer rewritten by the historical keyword overrides. Public wire/`ChatStateV2` remain compatible. The original frozen R0 artifacts and v6 evaluation outputs/hashes are unchanged and historical; this is not a silent schema/hash replacement or authorization to resume v6 against new source. New evidence is local bug-fix verification, not R4 acceptance.

**Quota-only amendment — 2026-10-27:** [Evidence/policy/resume](reports/r4-quota-increase-2026-10-27.md). Owner-approved temporary100/1,500,000daily allowance replaces the old operational ceilings only; original v6 source hashes, prompts, model, ranking, dataset, validators and pre-amendment output prefixes remain unchanged. No failed/attempted turn replay. Proposed development gate passes; held-out mandatory cases currently fail pricing-prose validation, human scores null. R4 is not accepted; frozen schemas/cases below remain intact.

**Latest R4 — 2026-10-26:** [v6 checkpoint](reports/conversational-rag-r4-resume-2026-10-26.md). Frozen domain schemas/cases and public wire are unchanged. Current-user explicit-operation routing normalizes whole-message undo before unchanged semantic validation; unknown fields/IDs/patches remain rejected. Current9/26development attempts, baseline unselected-game claim rejected; all failures retained. Additional inference approved, today's50calls exhausted. Full live/human acceptance pending; October25 statuses below are historical.

**R4 update — 2026-10-25:** [latest fixes/checkpoint](reports/conversational-rag-r4-continuation.md), [original failures](reports/conversational-rag-evaluation.md). Frozen domain schemas/40cases/53turns remain intact. Additional free-tier inference is approved; old12-call ledgers remain immutable. Strict generation enforces the existing max-four before backend validation; v3 core journey3/3. Metadata/reference/scoring fixes retain guards. Current paired development13/26turns,49calls/390,773reserved units today pauses two-call turns until later UTC day. Full held-out live/human/serving-latency gates remain incomplete. R0–R3 paragraphs below are historical.

**2026-10-24 · R0 design freeze; not a serving API/session change.** [R0 evidence](reports/conversational-rag-r0.md) · [Authoritative plan](conversational-rag-plan.md) · [Executable prototype](../backend/experiments/rag_r0/contracts.py) · [Frozen schemas](reports/conversational-rag-r0-contracts.json)

**R3 follow-up — 2026-10-25:** [integration complete locally](reports/conversational-rag-r3.md). Explicit unversioned legacy/v2 wire discrimination and matching responses, regenerated OpenAPI/TS, neutral runtime guards and same-key v1→v2 browser migration implement the transition matrix below. Old criteria/query/exclusions stay quarantined; transcript/cards/draft and canonical references are retained. Bounded pending request snapshots preserve exact pre-turn state/context through trimming/reload/retry.151backend/49frontend tests,1actual-network catalog/encoder browser test and6clean responsive scans pass. Frozen domain schemas/cases unchanged, not evaluated. Owner approved R3/confirmed skills; stop before R4. The R2 paragraph is historical phase evidence.

**R2 follow-up — 2026-10-25:** [backend composition complete locally](reports/conversational-rag-r2.md), after [R1 retrieval/parity](reports/conversational-rag-r1.md). Serving-domain TurnPlan/ChatStateV2 and internal outcome schemas match the freeze. Six Core stages now use verified retrieval, scoped memory and byte-bounded evidence through the existing metered provider. **Public wire/browser session remain legacy v1; full v2 integration is R3.** Legacy requirements are quarantined; facts work, recommendations may ask reset/restate.144backend tests/313real-catalog scripted-provider assertions pass. Frozen artifacts/40cases unchanged, not evaluated.

These are the R2/R3 implementation contracts. R0 prototypes live outside `src/` and are not imported by the application; serving domain copies and the required-version wire subclass are now exported in OpenAPI. Changes to the freeze require a recorded reason and refreshed schema/fixture hashes, never a silent adjustment to fit held-out failures.

## TurnPlan

| Field | Meaning/bounds |
| --- | --- |
| `kind` | Exactly social / clarify / title_lookup / game_facts / compare / recommend |
| `reply` | ≤2,000 characters; used only for social/focused clarification, not ungrounded specific-game facts |
| `query` | Complete current relevant soft intent, ≤1,000 characters; replacement, not accumulated transcript |
| `title_mentions` | ≤2 nonblank titles, each ≤200 characters; one for lookup/facts, two for comparison |
| `reference` | none / last_game / last_pair; not mixed with explicit title mentions; unresolved/ambiguous reference becomes clarification |
| `requested_facts` | ≤7 known fields: description/platforms/modes/genres/tags/early_access/recorded_price |
| `criteria_patch` | ≤2 patches; each has turn/conversation scope, typed partial `set`, explicit `clear` keys; competing scopes/set-clear for the same key rejected |
| `evaluate_prior_requirements` | Only for explicit suitability of lookup/fact/compare targets, never inferred merely from a title question |
| `exclusion_patch` | ≤8 add/remove operations; target is one title or one recent displayed position 1–4, **never a model-generated app ID** |
| `reset_preferences` | Explicit conversational start-over. Reset first, then apply any clearly stated new patch in that same user message |

Criteria reuse existing bounded catalog filter types, but reject embedded `excluded_ids`. Conversation exclusions have one separate field. Hard keys: minimum/maximum cents, strict/inclusive upper operator, free-only, platforms/match mode, required modes/genres, unwanted exact terms. Preferred terms remain soft. Canonicalize/validate the merged criteria after clears/sets and before state mutation or retrieval; a valid partial patch need not form a valid merged range. Invalid/contradictory interpretation does not partially commit state.

Backend assigns current user-turn provenance; the interpreter cannot submit its own origin index. Applying clear restores the neutral default and removes provenance. “Forget the budget” clears min/max/free-only/operator as a group; clearing platform also resets its match policy. Free-only sets explicit zero bounds/inclusive operator; leaving free-only must explicitly clear/replace the old bounds. Multiple required modes/genres mean all; missing facts fail hard conditions. Unsupported platforms and unrepresentable alternatives/negation clarify rather than silently map to Windows or relax criteria.

Named-game facts/existence bypass recommendation conditions and exclusions. A retained known mismatch may be explained separately; it never removes the preference or prevents the title being retrieved. A factual turn may change preferences only when the same user explicitly instructs a separate preference edit. Subjective assistant prose never supplies a new preference. Topic changes replace unrelated soft query; ambiguous retention of a hard requirement asks the user.

## ChatStateV2

- `version: 2`, `user_turn: 0..1,000,000`; increment only on accepted new user turns, not retries. At bound, ask for New chat; no wraparound. Frontend retry reuses the pending-turn identity; R3 must preserve current no-duplicate/abort behavior.
- `criteria`: neutral defaults with no main-page inputs. Every nondefault active criterion needs `provenance[key] = {user_turn, scope: conversation}`. At most ten criterion origins; indexes cannot be in the future. Scope-turn patches are effective for the current response only, never persisted into these criteria.
- `query` ≤1,000 characters, with `query_origin` for a nonblank retained query. “More like that” can refer to relevant chat query/recent canonical references, not saved/main favorites.
- `exclusions`: ≤100 unique canonical app IDs, each with bounded conversation origin. Resolve/validate IDs against the active catalog when used; unknown catalog IDs never become instructions to SQL or prompts. Played/disliked titles remain accessible to fact lookup. Undo removes only the resolved title's exclusion.
- `shown_ids` ≤4 unique canonical IDs; `referenced_ids` ≤2 for latest unambiguously resolved fact/comparison targets. If pronoun target is not unique, clarify without mutation. Canonical references are re-resolved on active version changes.
- `legacy_criteria`, `legacy_query` ≤1,000 characters, `legacy_excluded_ids` ≤100: quarantined compatibility fields, **not active recommendation inputs** until the user confirms the relevant requirements. Merge legacy `state.criteria.excluded_ids` into this quarantine before validating ChatCriteria.
- These bounded structures remain untrusted client data. Shape/provenance validation does not authenticate intent, turn history or catalog facts. Do not introduce account/session database storage, signing-key requirements or user tracking for this feature.

Transcript/cards retain existing 20 messages/2,000 chars each/12,000 total/12 cached cards and 500,000-character envelope protection. New chat clears all chat state/transcript/draft and aborts old work. Conversational start-over clears preferences, query, exclusions, references and legacy quarantine, preserves visible transcript/cards, then applies any explicit new intent. Clear-device-data invalidates pending work and owned chat storage across tabs. No state recovery may import main preferences/history/saves.

### Provider projection and byte budget

Do **not** send the entire v2 state/envelope or provenance to each call. Interpretation uses a compact projection: active criteria/query, relevant bounded references and exclusions, current message and existing last-eight/700-character recent text policy. Legacy criteria are only projected when asking for explicit confirmation. Reserve space for required active hard conditions. Truncate older prose/soft detail first; if the required projection cannot fit the existing 12,000 input-JSON-byte limit, return a clear bounded-context failure instead of silently dropping a hard criterion. This includes UTF-8 byte, not character, accounting.

Evidence generation gets at most eight relevance-prioritized catalog packets and four display selections. Description excerpts are bounded/truncated, not omitted just for exceeding the old per-value length check. Preserve requested fact evidence before unrelated metadata. Card names/IDs/links/dated prices remain canonical. Existing no-generated-URLs/numeric-currency prose rules and factual claim validation remain in force.

## RetrievalOutcome

`kind`: found / found_but_mismatch / ambiguous / not_in_catalog / no_recommendation_match / retrieval_unavailable. `channels` is a unique subset of title/lexical/semantic. `semantic_available` describes compatible encoder capability; a channel is listed only when actually used. `degraded_reason` is absent or encoder_missing / encoder_busy / encoder_failed / artifact_mismatch. `evidence_ids` contains at most eight unique canonical catalog IDs.

`not_in_catalog` requires a completed eligible-catalog title search (`title_search_complete=true`, title channel present). A semantic/keyword shortlist miss may only establish no matching recommendations, not catalog absence. An unavailable database cannot establish absence either. The frozen shape validator checks the prerequisite flags; R1/R2 must derive them from actual repository execution, never let the model choose them. Ambiguous franchise options are grounded canonical identities; aliases are small, verified and version-controlled.

Social/clarify with no retrieval may omit retrieval metadata entirely. Unsupported platform facts may return clarification with retrieval_unavailable semantics, but cannot be labeled an encoder degradation. Provider failures remain explicit retryable errors as appropriate, not a fabricated successful deterministic model answer. Known title/no-match outcomes can use clearly backend-derived response text. No automatic retry or extra model call is authorized.

## Wire/session compatibility — implemented in R3

Keep `/api/v1/chat` and response essentials message/games/state/notices/catalog_version/request_id. Request-state discrimination: an omitted `version` means existing legacy state; explicit `version:2` means v2. Unknown future versions fail safely. Export both bounded accepted request shapes and regenerate TS/runtime validation at the integration phase; do not use permissive arbitrary dictionaries to swallow extra fields.

| Combination | Required behavior |
| --- | --- |
| Legacy tab envelope → new frontend | Validate the existing v1 envelope before conversion; retain transcript/cards/draft, quarantine preferences/query/exclusions, preserve references only as canonical re-resolvable IDs. Write version2 only after successful complete validation. Never activate unknown-provenance requirements automatically. |
| Old frontend → new backend | Accept legacy state and return the **legacy-compatible state shape**. Facts/title lookup work; recommendations ask confirmation when old retained requirements are relevant. Do not silently reactivate legacy requirements or pretend the old client preserves v2 provenance. If it cannot retain the confirmed state, explain that a refreshed client is needed for the revised memory behavior. |
| New frontend → old backend | Existing bounded 422/unavailable response is handled without overwriting v2 storage, automatic lossy downgrade or discarding the pending user turn. Preserve retry/reset guidance and state until the backend is updated. |
| v2 frontend/backend | Full validated v2 memory; additive typed outcome metadata only where needed. Missing optional fields use neutral defaults; missing provenance for nondefault active requirements is invalid. |
| Corrupt/future/oversized envelope | Protect original storage, continue in-memory only with existing guidance until explicit New chat. No overwrite/migration of unknown data. |
| In-flight reload/New chat/clear | Retain current pending-turn retry contract; discard responses for obsolete session epochs. Clear in another tab cannot be undone by a late response. |

The session envelope is version2 while retaining the same owned session key. New chats send explicit neutral v2 state. An omitted API state retains the legacy server default for old callers; it never guesses v2. `pending` is an optional bounded request snapshot (neutral default null), validated against the retained pre-turn state and final visible user message. This preserves exact retry context even after transcript trimming; it is not server-side deduplication or free retry accounting. The R3 approval/skills gate was explicitly satisfied. Domain schemas and frozen fixtures were not changed.

## Evaluation freeze and remaining implementation tests

`data/evaluation/chat-rag.jsonl` and its manifest contain 40 curated scenarios, 53 turns, deterministic 10/30 development/held-out split, real/synthetic labels, expected scope/constraints and judgment rubric. They are inputs, not passing results. R1/R2 tests must cover ambiguity, normalization, actual lexical matches/no zero-score fill, filters, no embeddings, artifact mismatch, reference/exclusion undo, hostile evidence and the multiplayer → Spider-Man → multiplayer case. R3 adds the transition matrix, main-state isolation, reload/clear/retry and relevant responsive/focus regressions. R4 adds manual relevance/grounding judgments and separately approved live-call accounting.
