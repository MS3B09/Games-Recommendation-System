# Independent conversational RAG — implementation plan

**Current authority — 2026-10-27:** [quota-only amendment and checkpoint](reports/r4-quota-increase-2026-10-27.md) supersedes older50/500,000ceiling/resume instructions. Approved temporary100calls/1,500,000reserved units/day applied preserving consumed usage; defaults remain50/500,000. Existing v6 source hashes/prompts/ranking/model/outputs unchanged; use **resume_chat_quota** wrapper, not the frozen original CLI for >50-call receipts. Proposed development13/13passes; held-out32attempts/8pricing-prose failures, human scores null. Today's95calls pause at conservative provider-token headroom despite5app calls left. Resume unattempted held-out work with fresh receipt; no held-out tuning or retries.193backend tests/15scratch checks/rollback probe pass. R4 not accepted; restore runtime after R4 without clearing counters, no M5/publication authority.

**Current authority — 2026-10-26:** [v6 checkpoint/resume](reports/conversational-rag-r4-resume-2026-10-26.md) supersedes October25v3 status below. Existing inference approval remains valid; today's50calls/393,494units exhaust daily calls. Source-frozen authoritative C: journal plus E: exports,9/26development attempts (8delivered/1baseline claim failure), proposedplayed→fact→undo3/3.189backend tests/313integration assertions; full held-out live/human/representative latency gates pending. Next resume proposedM01turn2/3 after a fresh later-UTC-day receipt. Preserve current C: journal and historical failures; no new setup or M5/publication authority.

**Revision:** 2026-10-25 · **Status: R0–R3 complete locally; R4 in progress, acceptance INCOMPLETE. Additional inference APPROVED; current run paused at daily quota.**

[Latest fixes/checkpoint/resume](reports/conversational-rag-r4-continuation.md) · [Original R4 results/failures](reports/conversational-rag-evaluation.md) · [R3 integration](reports/conversational-rag-r3.md) · [R2 composition](reports/conversational-rag-r2.md) · [R1 retrieval/parity](reports/conversational-rag-r1.md) · [R0 decision](reports/conversational-rag-r0.md) · [Frozen contracts](conversational-rag-contracts.md). Owner approved additional inference as needed within free-tier limits and directed completion of remaining issues. Strict max-four generation, metadata/references and reduced read-only round trips are verified; proposed live core journey3/3 and fixed runtime retrieve p95487ms/90warm samples.180backend tests/313actual-catalog scripted-provider assertions. Paired development13/26turns; UTC2026-10-25 usage49calls/390,773reserved units pauses another two-call turn. Resume on later UTC days under existing approval; no new configuration. Conditional33-case/44-turn retrieval comparison remains distinct from pending full held-out live/human/serving-total-latency gates. R4 not accepted; frontend unchanged; M5/publication unauthorized.

[Visual owner guide](design/conversational-rag-plan.html) · [Project milestones](../IMPLEMENTATION_PLAN.md) · [Current operations](operations-assistant.md)

## 1. Authority and intended outcome

The owner selected conversational RAG to demonstrate credible AI/ML engineering to recruiters and to provide natural game assistance. This document is the authoritative next-work specification for chat, superseding earlier planned chat retrieval/filter behavior where it conflicts. Phase reports distinguish locally implemented behavior from pending work. Dated implementation reports remain historical evidence. Main discovery, existing Current styling and completed M0–M4 work remain the baseline. This follow-up is not automatic authorization for M5, publication or catalog expansion.

**Goal:** an assistant that understands only its current conversation, retrieves real catalog evidence using embeddings plus title/keyword matching, and distinguishes a factual question from a constrained recommendation.

Success example: after asking for multiplayer games, “Does a spiderman game exist?” finds **Marvel’s Spider-Man Remastered**, explains its recorded single-player mode, and does not erase the multiplayer preference for the next recommendation. “Would it match my requirements?” explicitly evaluates that mismatch.

### Nonnegotiable boundaries

- No main favorites, My limits, saved list, feedback or discovery history enters retrieval, prompts or chat memory. Shared Save remains an outbound bookmark action, never a personalization input.
- One React frontend, one modular FastAPI backend, one PostgreSQL/pgvector database. Free-only hosting/inference; CPU-only local work on 8 GB RAM. No vector service, agents fleet, queue or required paid tracing.
- Preserve existing 50 provider calls/day, 500,000 reserved tokens/day, four calls/minute, 30-second per-peer throttle, concurrency guard, reservation semantics and transport bounds. No quota reset or bypass for evaluation.
- No live web/Steam search in chat. Catalog prices are dated US/USD observations. Missing catalog information is not evidence that a game does not exist anywhere.
- Preserve bounded sessions, New chat, clear-data behavior, cancellation, error recovery, mobile focus and current card controls. No redesign.
- Current authorization includes remaining R4 fixes and additional inference as needed within existing free-tier limits. Original pilot ledgers remain immutable; current v3 source-frozen checkpoint resumes only unattempted work after a fresh shared-allowance receipt. Human ratings must come from the owner. No environment-file edit, model/catalog change, download, migration, paid resource, commit/push/deploy authority. R4 acceptance/full live/human/serving-latency quality remain incomplete. Preserve R2 Core/R3 public v2/browser baseline and configured cache files.

## 2. Verified baseline and gaps

Inspected source: `backend/src/game_discovery/ai/chat.py`, `catalog/repository.py`, `retrieval/query.py`, `catalog/contracts.py`, `frontend/src/FloatingAssistant.tsx`, `assistant-session.ts`, and legacy `app.py`.

| Existing behavior | Gap addressed by this plan |
| --- | --- |
| Chat already excludes main preferences | Retain and regression-test this boundary throughout orchestration. |
| R2 finite interpretation/memory/retrieval/evidence/generation/validation stages | At most two metered calls, no agent loops. |
| R1 aliases/partial-title resolver now used by R2 | Facts bypass recommendation conditions; mismatch notes preserve requirements. |
| Up to eight bounded evidence candidates and four cards | Canonical ID/claim/condition checks, fewer/no selections permitted. |
| Actual configured pinned MiniLM encoder | R1 hash/manifest/reference parity and R2 real semantic path pass on40games. |
| R3 scoped/provenanced v2 wire/browser memory, explicit legacy adapter | Validated v1 migration retains transcript/cards/draft and quarantines old requirements; no lossy downgrade on skew. |
| Canonical cards, exact claims and bounded UTF-8 evidence | Free prose remains incompletely fact-validated; R4 live/manual quality evidence is pending. |

Legacy Streamlit used MiniLM + FAISS + `ConversationalRetrievalChain` with top-five documents and prompt-only behavioral rules. Reuse the RAG principle, not its pickle/index artifacts or deprecated chain design.

## 3. Architecture and LangChain decision

```text
Offline: approved catalog → normalized game evidence → pinned MiniLM vectors → PostgreSQL/pgvector

Message + bounded chat-only context
  → typed turn interpretation (provider call 1)
  → resolve title/reference OR build recommendation query
  → title matching + lexical retrieval + query embedding/cosine retrieval
  → scope-appropriate filters + deterministic merge/ranking
  → bounded evidence packet
  → grounded answer (provider call 2 when needed)
  → ID/fact/card checks → existing chat UI + updated chat-local state
```

### Selected orchestration: minimal LangChain Core; R0 gate passed, R2 implemented

The owner prefers LangChain when it has a real advantage without material architecture or speed cost. R0 passed the measured adoption gates; R2 uses pinned **`langchain-core==1.7.0` Runnable composition and Document adapters** for six explicit testable stages. Typed domain contracts/repository logic stay in our modules. Local graph/stage replacement/timings are verified, not a decorative wrapper. R2 production transitive differences/resources are recorded in its evidence report.

- Wrap the existing `ChatModel.complete`/quota-controlled provider adapter; do not introduce a second direct ChatGroq transport that bypasses accounting or changes retries/timeouts.
- Wrap the existing restricted catalog repository in a retriever adapter. Do not let a vector-store integration create new tables or require privileged runtime access.
- Do not add LangGraph, autonomous agents, the legacy ConversationalRetrievalChain, hosted tracing or the whole community integrations bundle for this workflow. Imports and compatible versions must be checked and locked during R0, not guessed now.
- No automatic retries, parallel provider calls, hidden memory service or extra model calls from orchestration. Raw conversation/provider payload tracing is off by default.
- **R0 adoption gate:** same functional results and provider-call counts as direct Python stages; 100 warm mocked-provider repetitions with added orchestration p95 ≤25 ms; added warm RSS ≤30 MiB; total representative API peak RSS <400 MiB; measure startup/import time and lockfile size/dependency changes. These are proposed acceptance budgets, not measured claims. CPU-bound encoding and real provider latency are measured separately.
- If the gate passes, **use LangChain Core**. If it fails or yields no concrete maintainability/testing benefit, report evidence and obtain the owner's decision before switching to direct composition. Do not silently add a heavy framework or silently omit the preferred library.

Embedding model: reuse pinned `all-MiniLM-L6-v2`, 384-dimensional normalized vectors, existing hashes/artifact version and ONNX parity checks. Same representation for catalog and queries. No training or fine-tuning required. pgvector supports cosine similarity and PostgreSQL lexical search in the same database; no FAISS service is necessary.

## 4. Conversation semantics and contracts

Interpretation returns a validated internal `TurnPlan` (proposed fields):

- `kind`: `social`, `clarify`, `title_lookup`, `game_facts`, `compare`, `recommend`.
- `query`, `title_mentions` (maximum two for comparisons), resolved-reference intent, requested fact fields.
- `criteria_patch` and explicit clear operations; scope is `turn` or `conversation`.
- `evaluate_prior_requirements`: only for explicit suitability questions such as “Does it meet those requirements?”
- `exclusion_patch`: chat-only additions/removals; resolve IDs against catalog, never trust model-generated IDs.

Do not let the model write SQL or select arbitrary tools. The backend selects the finite retrieval path from this contract. Ambiguous titles, pronouns, negation or alternative constraints trigger a focused clarification.

### Memory rules

1. Start with no budget/platform/mode/genre defaults; context comes from user chat messages only. Assistant prose is not a source of new preferences.
2. “More like that” uses relevant prior intent. “Forget multiplayer” clears only that requirement. “Start over” resets chat preferences/references with explicit handling; New chat clears all chat state.
3. Title existence and fact questions bypass recommendation preferences and recommendation exclusions for lookup. Mention relevant mismatches separately; do not mutate preferences merely because a fact question was asked.
4. Recommendations enforce explicitly stated hard chat requirements. A one-turn constraint need not become a permanent preference. Preserve provenance (originating user turn and scope) in bounded validated state.
5. “I played X” excludes X from recommendations, not from answering facts about X. “Include X again” can remove that exclusion. “This one” requires a unique resolvable reference.
6. Topic changes replace the soft search query when appropriate. Do not blindly append every earlier topic. If whether to retain a hard criterion is unclear, ask rather than silently relax it.
7. Retain existing limits: 20 messages, 2,000 chars/message, 12,000 total; provider recent context stays within existing last-eight/700-char truncation and total byte budget. Provenance supports retained preferences after history trimming without an extra summarization model call.

### API/session compatibility

Keep `/api/v1/chat` and existing response essentials (`message`, `games`, `state`, `notices`, `catalog_version`, request ID). Add optional typed retrieval outcome/capability fields only when necessary; regenerate OpenAPI/TypeScript and runtime guards together. Do not break legacy text/discover endpoints.

Plan a versioned state/session transition if adding provenance: accept legacy request state through a documented bounded adapter. Legacy criteria have unknown provenance and must not be silently treated as newly explicit user requirements; preserve transcript/cards and ask to confirm relevant requirements before using them for recommendations. Title/fact lookup still works. Future/corrupt storage remains protected until user reset. New v2 state should default absent fields safely; test reload during transition and API/frontend version skew. No database conversation persistence.

## 5. Retrieval algorithm

### A. Title resolution

1. Exact catalog ID from a validated recent reference; otherwise exact normalized title.
2. Unicode-aware case folding; normalize punctuation/apostrophes/hyphens/whitespace. Preserve original titles for display. Do not strip numbers or sequel subtitles indiscriminately.
3. Small version-controlled alias map tied to verified catalog identities (e.g. `spiderman`), plus token/prefix matching. Multiple franchise matches return clarification options rather than an arbitrary winner.
4. Bounded fuzzy matching as suggestions only unless the score/margin has been validated; no model-invented IDs. Catalog-only existence lookup includes all eligible games even if they lack embeddings.
5. Use the same resolver for named exclusions and comparisons. Return `found`, `ambiguous` or `not_in_catalog`, not global nonexistence.

At the current small catalog size, bounded normalized lookup can avoid new extensions/schema. Do not load an unbounded future catalog into every request. R1 records measured bounds and chooses a parameterized database lookup if growth requires it. Any schema/alias-table/index change requires a reviewed migration and local verification before a separately authorized remote application.

### B. Semantic + keyword recommendations

- Build a concise search query from current intent and relevant chat-only context.
- Apply explicit recommendation eligibility/price/platform/mode/genre/exclusion conditions before candidate selection. Missing required facts do not count as a match.
- Encode with the pinned local query encoder; compare to catalog vectors using cosine similarity.
- Retrieve up to 20 semantic and 20 lexical candidates, bounded by available catalog rows. Lexical candidates must actually match query terms; zero-score rows must not silently fill the pool.
- Merge by stable game ID, using **reciprocal rank fusion (initial constant 60, equal channel weights)** as a simple versioned starting point. Title resolution outranks approximate discovery for named-game questions. Scores/weights are tuning defaults, not quality claims.
- Build evidence for at most eight candidates; select at most four display cards. Preserve retrieval IDs/ranks in local evaluation traces. If relevant evidence does not support fit, clarify or return fewer/no recommendations.
- Calibrate semantic-only relevance cutoffs on development cases; cosine is not a probability and no universal threshold is assumed. Freeze policy before held-out evaluation.
- Busy/missing/mismatched encoder → lexical/title fallback with truthful capability/outcome metadata. This is graceful degradation, not a passing semantic-RAG completion result.

### C. Evidence and natural answers

Pack canonical ID/title, relevant description excerpts, genres/tags, modes/platform facts, Early Access, recorded price/date and evidence references. Fit the **existing 12,000 input JSON byte limit** by relevance-prioritized truncation; avoid the current accidental omission of long descriptions. Prefer the requested fact over unrelated tags. No full-catalog prompts.

Model returns natural text plus selected IDs and bounded optional evidence claims. Validate IDs against the retrieved set and recommendation constraints against canonical records. Cards/links/prices are server-derived. Preserve the current no-generated-URLs/numeric-currency prose contract unless explicitly revised; price questions may be answered by directing to a dated card. Subjective fit must be qualified when unsupported.

Backend-grounded outcomes distinguish `found`, `found_but_mismatch`, `ambiguous`, `not_in_catalog`, `no_recommendation_match`, and `retrieval_unavailable`. The model must not convert a shortlist miss into a catalog-absence claim. Deterministic fallback text is acceptable for known outcomes; it must not impersonate a successful model response after provider failure. Greeting/clarification can use one call and no catalog query. No-match can end after interpretation/retrieval without a second call.

## 6. Implementation sequence and approval gates

**R0–R3 are complete locally** with [R0](reports/conversational-rag-r0.md), [R1](reports/conversational-rag-r1.md), [R2](reports/conversational-rag-r2.md) and [R3 exit evidence](reports/conversational-rag-r3.md). R4 remains **incomplete**; [current continuation evidence](reports/conversational-rag-r4-continuation.md) supersedes the original capped pilot restriction. Further inference is approved within daily limits, using multi-day checkpoints; full live/human/serving-total-latency gates remain. Report and stop after each phase; no M5 authority. The table retains implementation/exit specifications.

| Phase | Implementation tasks after approval | Exit evidence |
| --- | --- | --- |
| **R0 — architecture/measurement** | Inspect real catalog/version/config without exposing secrets; lock model parity plan; prototype minimal Core vs direct composition in an isolated local environment; fix TurnPlan/outcome/session contracts and evaluation cases. | LangChain decision record with benefit, dependencies, call counts, cold/warm RSS and latency; frozen contracts, explicit blockers. No live AI required. |
| **R1 — retrieval foundation** | Configure/verify compatible query encoder; implement chat-scoped title resolver, actual lexical matches, bounded semantic retrieval and rank fusion. Keep main ranking unchanged. | Spider-Man variants, ambiguous franchises, no-match, no-embedding title, filters, version mismatch and encoder fallback tests; real-catalog read-only retrieval evidence. |
| **R2 — conversational RAG** | Compose finite stages; apply intent-scoped memory, references/exclusions, bounded evidence, grounded outcomes and existing provider accounting. | Multi-turn backend tests, hostile/untrusted inputs, missing evidence and quota/provider failure coverage; contract/type checks. |
| **R3 — integration** | Implement compatible session transition and any additive API handling; preserve existing chat visual, cards, Save, focus/retry/clear contracts. | Browser isolation/reload/version-skew tests, main-discovery regression, responsive/accessibility checks if rendered behavior changes; no visual redesign. Confirm frontend skills before frontend implementation. |
| **R4 — evaluation/handoff** | Run frozen comparison, manually judge answers/relevance, report failures and resource costs; update README/diagram/operations/demo walkthrough. | Reproducible report with retrieval vs generation metrics, actual encoder capability, latency/RSS and known limitations. Live provider runs require separate budget approval. This narrow RAG evaluation does not claim whole-product M5 completion. |

### File map (R1–R3 implemented; R4 evaluator implemented, acceptance incomplete)

- `ai/chat.py`: orchestration entry and request/response compatibility.
- `ai/chat_contracts.py`, `ai/chat_memory.py`, `ai/chat_evidence.py`, `ai/rag.py`: typed plans/memory, UTF-8 Document evidence and finite runnable stages; `ai/chat.py` exposes the explicit v2/legacy boundary.
- `retrieval/titles.py`, `retrieval/chat.py`: reusable title resolution and chat-only hybrid retrieval. `retrieval/query.py`: retain pinned bounded encoder/fallback.
- `catalog/repository.py`: parameterized retrieval methods; reuse snapshot/RLS boundaries. Do not silently alter `discover()` main ranking.
- `ai/provider.py`: existing transport/accounting is reused; no parallel unmetered client.
- `frontend/src/api/discovery.ts`, `chat-state.ts`, `assistant-session.ts`, `FloatingAssistant.tsx`: R3 runtime guards/neutral defaults, validated migration, exact pending replay and preserved assistant integration. `tests/live-r3.spec.ts`/`jobs/serve_chat_r3_probe.py` provide the owned actual-network/catalog/encoder check with mocked provider/accounting.
- `backend/tests/test_chat.py` plus focused retrieval/memory tests; `frontend/tests/hybrid.spec.ts` and relevant storage tests.
- `jobs/evaluate_chat.py`, `chat_evaluation.py`, `review_chat_pilot.py`: oracle-intent offline comparison, fixed/capped live pilot/revision ledgers, no-call completed-ledger recovery and recorded-output diagnostics. Frozen `data/evaluation/chat-rag.jsonl` remains unchanged; additive `chat-rag-r4-policy.json` records the comparison. [R4 report](reports/conversational-rag-evaluation.md) contains measured results, failures and runnable offline/replay commands, not full live acceptance. [Architecture](architecture-assistant.md) / [walkthrough](walkthrough-assistant.md).

## 7. Tests and evaluation specification

### Mandatory regression scenarios

- Multiplayer recommendation → “exist a spiderman game?” → correct title and single-player mismatch → “more multiplayer options” retains multiplayer.
- Same title with curly/straight apostrophe, hyphen/no hyphen, short name; ambiguous franchise asks which game; nonexistent title says absent from this catalog only.
- “Would it meet those requirements?” checks prior criteria; “forget the budget” clears only budget; topic change does not carry unrelated soft intent.
- Played/disliked title excluded from recommendations but inspectable; undo works; ambiguous pronoun clarified.
- Different main favorites/limits/feedback/saves with identical chat inputs produces identical retrieval inputs; main changes never leak into prompts.
- Price boundary/free-only/unknown price, unsupported platform, all requested modes; no silent constraint relaxation.
- Catalog version changes, missing vectors, encoder failure/busy, irrelevant matches, long evidence, malicious catalog instructions, fabricated IDs/claims, invalid provider JSON and exhausted quota.
- Reload, legacy session, trimming, New chat, clear across tabs, abort/retry and stale-response rejection.

### Simple measured comparison

Use **40 curated cases**: 8 title/alias, 8 semantic discovery, 8 multi-turn scope/reference, 6 hard-constraint, 4 ambiguity/absence, 3 independence/session, 3 failure/grounding. Cases may be multi-turn. Split 10 development and 30 held-out before tuning. Synthetic test fixtures must be distinguished from the real catalog; inventory coverage explicitly (last known 40 games).

**One baseline:** semantic-only cosine top-five RAG over the same versioned catalog, same encoder, generator, evidence budget and model settings. No title boosts or lexical fusion. The proposed method adds routing/title lookup/hybrid retrieval/checks. Record these differences honestly; do not attribute all gains to embeddings. Historical Streamlit output and current keyword fallback are context, not an additional formal baseline.

- Retrieval: expected-title Hit@5, relevant-evidence Recall@8 where judged, failed title resolution and empty/irrelevant pools.
- Answers: human relevance 0/1/2 (irrelevant/partial/good), unsupported factual claims, false-absence claims and correctly resolved scope. Review all factual prose, not just structured claims. Record rubric and judgments per case; blind method labels where practical.
- Constraints/isolation: zero returned-card hard-condition violations, zero main-state leakage, zero invented catalog IDs on mandatory tests.
- Performance: cold/warm startup, encoding/retrieval/orchestration/provider stages, total median/p95, peak RSS, actual and reserved usage where available. Target warm retrieval+encoding p95 ≤1 second locally and total warm answer p95 ≤10 seconds; these are proposed targets requiring measured reporting, not guarantees. Record hardware, provider/model version and sample size.
- Quality gate: all mandatory title/scope cases pass; proposed held-out mean relevance does not regress against baseline and unsupported-claim rate does not worsen. Report ties, remaining failures and limited sample size; do not promise a statistical improvement. If targets fail, fix within approved phase or present the tradeoff before advancing.
- Retrieval-only and mocked-provider tests consume no live allowance. Real-generation comparison needs explicit approval and a preflight budget: cases × actual turns × model calls × methods. Forty cases are not forty calls. Check shared remaining allowance, run sequentially over multiple UTC days if necessary, honor 30 seconds and all token/minute limits; checkpoint without resets/retries that hide failures. Report incomplete live evidence as incomplete.

## 8. Operational controls, rollback and remaining work

Reuse restricted runtime credentials and current local startup. Configure compatible encoder paths only during authorized implementation; never print secrets. Serving must not download weights. Measure deployed-environment feasibility before any later publication; do not assume local memory results prove hosted capacity. Store only bounded nonsensitive operational timings/outcomes by default; keep evaluation transcripts as curated fixtures, never real user chats in public reports.

Prefer additive repository/contract changes and minimal dependency surface. Validate any required migrations in scratch/local database first. Remote migrations/catalog activation need explicit permission. Retain prior artifact identifiers and a compatibility path for session data; rollback means reverting the approved implementation slice and restoring compatible configuration/lockfiles, not destructive database cleanup or quota resets. A degraded lexical runtime cannot be marketed as fully functioning semantic RAG.

**Next action:** preserve all historical ledgers and current source-frozen v3 checkpoint. Resume remaining development turns on a later UTC day with a fresh effective shared-quota receipt, then same-version paired held-out live evaluation. No new inference approval needed. Serving-only total latency and owner relevance/grounding/Recall labels remain; runtime retrieval target passes the declared90warm-sample benchmark, while earlier journaled spikes remain reported. No held-out S05 ranking tuning. Restart backend for strict generation/reference/metadata fixes; no new config/key/model/migration. Preserve cache. Larger catalogs need a parameterized strategy before256title identities. Broader catalog/portfolio/M5/publication work remains separately gated.

## 9. Documentation handoff and sources

Keep this Markdown authoritative and the HTML consistent. Update current entry points (`README`, `AGENTS`, `PRODUCT`, `IMPLEMENTATION_PLAN`, `DESIGN`, progress/setup/assistant operations and deployment guidance) to distinguish **implemented baseline** from **planned next work**. Preserve dated reports and historical milestone operations; link them as evidence, not current implementation orders.

Documentation consulted during planning:
- [LangChain retrieval and custom runnable retrievers](https://docs.langchain.com/oss/python/langchain/knowledge-base): custom retrieval can use Core runnables without a full agent framework.
- [pgvector querying and hybrid search](https://github.com/pgvector/pgvector#querying): PostgreSQL supports cosine vector search and full-text hybrid retrieval.
- Existing project reports: [live AI limitations](reports/ai-live-configuration.md), [chatbot/quota revision](reports/assistant-redesign.md), [essential-details UI](reports/game-essentials.md).

The original specification did not claim implementation results. R0 records dependency/orchestration gates; R1 retrieval/parity/filters; R2 scoped composition/grounding/resources; R3 browser/API/session integration. R4 now records oracle-intent held-out retrieval and a failure-bearing live development pilot/revision. Full held-out generation and human relevance/prose judgments remain pending. No measured end-to-end relevance improvement or hosted feasibility is claimed.
