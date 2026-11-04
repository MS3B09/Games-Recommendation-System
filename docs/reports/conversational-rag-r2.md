# Conversational RAG R2 — finite backend composition and scoped memory

**2026-10-25 · Complete locally; stop before R3.** The owner explicitly approved R2. [Plan](../conversational-rag-plan.md) · [Frozen contracts](../conversational-rag-contracts.md) · [Integration/resource evidence](conversational-rag-r2-integration.json) · [R1 retrieval/parity](conversational-rag-r1.md)

## Implemented scope

- `ai/rag.py`: six named, replaceable synchronous Core stages: **interpret → remember → retrieve → evidence → generate → validate**. Uses pinned Core1.7.0 RunnableSequence/RunnableLambda through the existing metered `ChatModel.complete`. No agents, tool loops, parallel calls, batching, retries or second provider client.
- `ai/chat_contracts.py`: serving-domain `TurnPlan` and `ChatStateV2` schemas exactly match the frozen R0 schemas. The experiment is not imported. These are internal domain contracts in R2, not new public wire/session shapes.
- `ai/chat_memory.py`: neutral chat-only defaults, server-assigned user-turn provenance, conversation versus one-turn criteria, grouped budget/platform clears, free-only normalization, merged-range validation, replacement soft topics, explicit reset and legacy quarantine. Copy/validate/commit prevents failed/ambiguous operations or provider failures from partially changing request state.
- Canonical references/exclusions use R1 title resolution. Played/disliked games remain inspectable; undo removes only the resolved chat exclusion. Stored IDs are re-resolved; unknown exclusions do not enter active filters. Comparisons require two distinct targets from the same catalog version.
- Facts/existence bypass recommendation conditions/exclusions. Backend-derived mismatch notes distinguish **found** from **found_but_mismatch** without erasing preferences. Spider-Man resolves to **1817070**, records single-player versus retained multiplayer, and the next recommendation retains multiplayer and the relevant soft query.
- `ai/chat_evidence.py`: Core Document adapters for at most eight candidates, nonempty bounded description excerpts, requested-fact priority, canonical platforms/modes/Early Access, dated price and exact claimable references. Interpretation omits full state/provenance, raw client IDs and all main inputs. Recent text remains within last-eight/700-character policy.
- Both calls fit the existing **12,000 input JSON UTF-8 byte bound**, including the provider's nested JSON/role serialization. Older prose/soft detail yield first; hard criteria are never silently omitted. Unfit required packets fail before the affected call. At most four server-derived cards; omitted packet candidates cannot be selected/cited.
- Validators reject invented/duplicate selections, claims about unselected/omitted games, unsupplied evidence and changed JSON types. Numeric currency/URLs and obvious false-absence prose are rejected. Missing optional evidence does not fabricate reasons. Generation may select fewer/no candidates and clarify.
- Ambiguous/absent/no-match/unavailable outcomes are backend-derived. Only a completed title search establishes catalog absence. Provider failures remain errors, without successful fallback or retry.
- Request-local callbacks retain names/timings only. Explicit tracing-disabled context/local callback manager prevents inherited LangSmith switches from sending raw data; socket/create-run regressions cover this.

## API and R3 boundary

**`/api/v1/chat` now calls the R2 sequence; its wire schema is unchanged.** `ai/chat.py` adapts bounded legacy state into quarantined v2 domain state and returns the legacy-compatible shape. Title/fact lookup works through the actual API, including Spider-Man.

The current browser still stores/sends **legacy version1**. It cannot retain v2 provenance. Legacy criteria/query/exclusions are preserved as quarantine, not silently activated. Recommendations with relevant legacy context ask for reset/restate and explain that full memory requires the updated client. Explicit conversational reset clears quarantine. Legacy display positions and merged exclusion bounds are protected.

**Full v2 memory is implemented/backend-tested internally, not yet available end-to-end in the browser.** R3 must expose bounded legacy/v2 discrimination, regenerate OpenAPI/TypeScript/runtime guards together and implement protected session transition/reload/version skew. No undocumented v2 wire input or arbitrary dictionary was introduced. OpenAPI stays unchanged.

## Dependencies/configuration

- Added **`langchain-core==1.7.0`** to application dependencies and updated `backend/uv.lock`:12 new locked records/+205lines, no existing locked package upgrades. Benchmark/dev environment now has **96 compatible distributions**,13 more than the R0 direct control.
- Core1.7.0/LangSmith0.14.12/langchain-protocol0.0.20 match the chosen versions. Production resolves **jsonpatch1.37/jsonpointer3.5**, versus historical R0's1.36/3.4. R0 artifacts remain frozen; they are not measurements of this new serving build.
- First uv sync exceeded its120-second tool timeout after a hardlink-to-copy warning. Locked inexact sync with `--link-mode copy` then completed. Lock/install compatibility checks pass. No unrelated packages/model files removed.
- Preflight free space: about **2.938GiB C: /1.514GiB E:**. Earlier effectively-full-C: finding is historical. Machine reports four logical CPUs, Intel64 Family6 Model61,7.703GiB physical memory (owner hardware i5-5200U/8GB, CPU-only).
- **No new key, environment-file edit, model download or migration is needed.** Actual configured pinned encoder/hash/manifest load passes against **`m2-649714e8b26775165f105d02`**. Preserve model cache files. Sync the lock and restart an older backend; owner processes were not managed.

## Verification

| Check | Result |
| --- | --- |
| Full backend unittest suite | **144 passed**;41 added R2 tests (40 domain +1 API isolation),13 existing chat tests updated for approved typed intent/fact semantics |
| Ruff /strict mypy | Passed /25 source files |
| Public OpenAPI export | Passed, unchanged |
| R0 contract tests /frozen hashes | Six passed;40cases/53turns,10development/30held-out unchanged, not evaluated |
| Dependencies | `uv lock --check` and96-package `uv pip check` passed |
| Real-catalog/scripted-provider probe | **313 assertions passed**, actual encoder/restricted catalog, HTTP and budget mocked |

Tests cover scope/provenance after trimming, Spider-Man detours/suitability, topic replacement, turn-only bounds, budget/free-only/platform clears, conflicting ranges, comparisons/references/version changes, exclusion/undo/ambiguity/unknown IDs, reset/legacy quarantine, main isolation, missing/hostile/long evidence, UTF-8 overflow, selection/claim/type checks, irrelevant-pool rejection, malformed interpretation, first/second-call failures, denied quota, encoder busy/mismatch, turn bounds, callback privacy and named-stage replacement.

The actual-catalog probe uses the real GroqAssistant adapter with mocked urllib HTTP/budget. Every mock packet is byte-checked; reservation equals input bytes+1,280. It covers four Spider-Man variants, multiplayer retention, suitability, played inspection/undo, turn-only price/platform bounds, Ori ambiguity, catalog-only absence, comparison, legacy facts/confirmation, empty selection and quota denial. The real API returns canonical Spider-Man cards, then the unmodified throttle returns429/Retry-After30: **no throttle bypass**. Main discovery before/after is fully identical, IDs **107100,311690,237930,113200**.

## Resources and evidence limits

| Measurement | Local R2 probe |
| --- | ---: |
| Fresh-process Core/domain import | 6,972.466ms |
| Actual encoder hash/load | 7,903.255ms |
| Six-stage graph build | 0.486ms |
| Warm scripted-provider total median /p95 | **764.795 /844.970ms**,12samples |
| Outside-stage remainder p95 | 4.199ms |
| Probe interpreter peak RSS | **252.992MiB**, below400MiB |

Warm totals measure domain `invoke()` with actual encoding/remote retrieval and mocked HTTP/JSON/accounting; they exclude HTTP-server/frontend transport and the probe's extra canonical-card assertion queries. Outside-stage remainder is total minus stage timings, **not** an incremental direct-composition comparison. Startup includes filesystem/hash/import costs; contract/OpenAPI checks ran alongside the probe. Not uncached-OS startup, process-tree/container totals or hosted feasibility. RSS uses10ms sampling plus Windows lifetime high-water working set and includes a representative TestClient API request.

This is **not live-model latency/quality**. Scripted plans/answers establish behavior for validated interpretation, not live intent accuracy or prompt-injection immunity. Optional structured facts/cards are checked; unrestricted factual prose cannot be exhaustively proven by these validators. Hostile-source tests show bounded handling/no tool execution. No manually judged answer/relevance improvement is claimed.

No universal cosine cutoff or held-out tuning was added. Generation can reject unsupported candidates; control flow is tested. Freeze any later development-calibrated policy before R4 held-out evaluation. Catalog40/title-inventory256 remain limits.

## Reproduce

From repository root:

```powershell
uv sync --project backend --locked --inexact --extra benchmark --extra dev --link-mode copy
& .\backend\.venv\Scripts\python.exe -m unittest discover -s backend/tests
& .\backend\.venv\Scripts\python.exe -m ruff check backend
& .\backend\.venv\Scripts\python.exe -m game_discovery.api.export_schema --check
& .\backend\.venv\Scripts\python.exe backend/experiments/rag_r0/freeze.py
& .\backend\.venv\Scripts\python.exe -m unittest discover -s backend/experiments/rag_r0 -p test_contracts.py
& .\backend\.venv\Scripts\python.exe -m game_discovery.jobs.verify_chat_rag --output docs/reports/conversational-rag-r2-integration.json
```

From `backend/`: `& .\.venv\Scripts\python.exe -m mypy`, `uv lock --check`, `uv pip check --python .venv/Scripts/python.exe`. Probe repetitions1–30/default12; output parent must exist. Repeating replaces only the named report. `verify_assistant` is a compatibility entry point writing R2 evidence, preserving historical October22 JSON. R0 benchmark reproduction needs its historical pre-R2 protocol/dependency context, not the revised adapter.

## Handoff

**Stop before R3.** No frontend implementation/browser checks, live inference/actual reservation, application DB write/migration, model download, environment-file edit, commit/push/deploy/M5. Provider protections remain50calls/day,500,000tokens/day,four/minute,30-second peer throttle and existing concurrency/reservation/transport bounds. No persistent owned API/preview started.

Next: separately approved **R3 API/session integration**, with frontend-skill confirmation before frontend implementation. R4 and any live-call budget retain separate approval gates.
