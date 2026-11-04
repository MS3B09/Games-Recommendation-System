# Conversational RAG — R0 architecture and measurement

**2026-10-24 · R0 complete locally. Stop here; R1 needs owner approval.**

The owner authorized starting the [implementation plan](../conversational-rag-plan.md), retaining its phase gates, and requested explicit notice of missing model/key configuration. R0 created isolated executable prototypes, measured the library choice, inspected actual configuration/catalog read-only, and froze design contracts/evaluation inputs. New retrieval, conversational behavior and session migration are **not serving yet**.

## Decision

**Use `langchain-core==1.7.0` for the finite chat pipeline in R2.** Its R0 gates pass and the prototype demonstrates useful named-stage graph inspection, local callback instrumentation, Document adaptation and replacement of one retrieval stage without rebuilding the other stages. Direct functions can also support injection; Core's advantage is a standard composition/testing vocabulary, not an otherwise impossible capability.

Only the isolated experiment depends on Core. Production `backend/pyproject.toml`, `backend/uv.lock`, application serving code, frontend, database and ignored environment configuration were not edited by R0. R1/R2 must not introduce ChatGroq, agents, LangGraph, automatic retries, parallel provider calls or external tracing. Reuse the existing `ChatModel.complete` transport and quota protections.

## Measured gates

[Raw three-pair measurements](conversational-rag-r0-benchmark.json) · [Compact derived decision evidence](conversational-rag-r0-summary.json)

| Gate | Measurement | Result |
| --- | --- | --- |
| Identical results/provider-call counts | Same output digest; same 2/2/1/1/1 synthetic call pattern for recommendation/title/social/clarify/empty scenarios; scripted provider failure executes once, no retry | Pass |
| 100 warm mocked repetitions | 100 per method in each of three fresh-process pairs; **300 per method** total, sequential, pair order alternated | Pass |
| Added orchestration p95 ≤25 ms | Paired differences **8.582 / 9.870 / 7.068 ms** | Pass |
| Added warm RSS ≤30 MiB | Worst paired increase across orchestration-only and API/encoder-resident checkpoints **23.973 MiB** | Pass |
| Representative API peak <400 MiB | Core interpreter peaks **259.625 / 256.367 / 255.695 MiB** | Pass |
| No hidden network/tracing | Socket connect/connect_ex forbidden during composition; tracing flags disabled, no keys/DSN inherited in workers, explicit local callbacks retain stage names only | Pass in prototype |
| Dependency compatibility | 83 installed distributions direct; 96 with Core; **13 added, zero changed baseline versions** between the two experiment environments | Pass |

**Costs that remain visible:** Core imports/builds took **7.695 / 2.822 / 2.386 seconds** in fresh interpreters. Filesystem caches varied, and this nearly-full-disk Windows laptop is not a hosted cold-start measurement. R0 specified measurement, not a startup pass/fail threshold. The extra packages include mandatory `langsmith==0.14.12` even though hosted tracing is disabled, plus jsonpatch/jsonpointer, langchain-protocol, orjson, requests-toolbelt, tenacity, uuid-utils, xxhash, zstandard, sniffio and distro. A dependency being present does not authorize its retry/tracing features.

The isolated Core experiment lock is **199,777 bytes**, versus **167,633 bytes** for a separately locked Core-free control (**+32,144 bytes**). Both consume the same local backend dependency specification. The control has a different project name/path depth; this is a measured isolated lock-size comparison, **not** a future production-lock diff. Both isolated environments share the same baseline dependency versions. Future production integration must preserve/recheck the production lock rather than replace it with an experimental lock.

### What the benchmark actually exercises

- Same five plain stage functions: interpretation → retrieval → evidence → generation → validation. Core composes RunnableLambda/RunnableSequence and adapts eight synthetic evidence records through Document; direct Python calls the functions in sequence.
- Synthetic provider/retrieval outcomes, up to eight bounded evidence candidates and four selected IDs, byte-budget enforcement and an explicit failure with no hidden retry. Social/clarification/empty scenarios use one simulated call, retrieval/generation scenarios two.
- A real existing FastAPI `/api/v1/chat` request via TestClient, one synthetic canonical card, mocked repository/provider, and real local pinned ONNX encoding. It preserves the real throttle: only one chat turn per API instance, no bypass. The new prototype chain is resident alongside the API, **not connected to its route** yet.
- Real encoding/load samples are recorded separately from mocked orchestration timings; they are not evidence of new retrieval performance.
- RSS is the measured interpreter's resident memory, using 10 ms sampling plus Windows process lifetime high-water working set. It excludes the thin venv launcher, is not a summed process-tree/container measurement and does not establish hosted feasibility. The eventual Linux serving process, larger evidence/memory workload and full R2/R3 integration must be measured again at the appropriate gates.

## Actual configuration and catalog

[Sanitized probe and bounded catalog inventory](conversational-rag-r0-config.json)

- Restricted runtime database configured; final read-only probe succeeded with **40 games**, active version **`m2-649714e8b26775165f105d02`**. No privileged migration credentials were used. Two earlier connection attempts returned `database_unavailable`; the later probe succeeded without configuration changes. Security advisory query returned no lints; queried recent PostgreSQL error logs returned no rows. This is not a claim of uninterrupted service.
- Groq key present, `AI_ENABLED=true`, selected model `openai/gpt-oss-120b`; **presence only**, no authentication/model inference performed in R0. Existing daily settings remain **50 calls / 500,000 reserved tokens**. No quota reservation or counter reset.
- All three query encoder settings were absent in the inspected application configuration. Do not claim semantic serving is configured from this explicit-path experiment.
- Existing local float ONNX and tokenizer files passed the actual loader's manifest digest, pinned revision, dimensions and exact SHA256 checks. Query vector length **384**, squared norm **1.0000000481**, matching active artifact. An existing parameterized read-only vector query succeeded. That compatibility probe is neither the new hybrid retriever nor a relevance evaluation.
- Verified Spider-Man identity **1817070**, recorded single-player; Ori and Isaac each have multiple catalog identities. Alias resolution must distinguish canonical exact titles from broad franchise queries.

### Owner configuration required before R1 semantic serving verification

Add the following **locally to ignored `backend/.env`**, not frontend configuration or chat. The owner was informed during R0; the agent did not edit `.env`:

```dotenv
QUERY_TOKENIZER_PATH=C:/Users/User/AppData/Local/Temp/opencode/game-discovery-models/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/tokenizer.json
QUERY_MODEL_PATH=C:/Users/User/AppData/Local/Temp/opencode/game-discovery-models/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/onnx/model.onnx
QUERY_ARTIFACT_PATH=E:/Games-Recommendation-System/docs/reports/m2-artifact-manifest.json
```

Keep these existing temporary-cache files in place or deliberately relocate them and adjust the paths together. Restart the backend after configuration; shell variables override `.env`. No new model key/download is currently needed. R1 must re-read the actual settings and assert semantic capability; it must stop/report if required configuration is still absent, not treat fallback as completion.

### Frozen representation/parity policy

Use `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 384 normalized float components; existing title/terms/description representation, 256-token truncation, masked mean pooling and one-thread CPU runtime. No silent quantized model switch or regenerated catalog activation.

The existing ignored local artifacts **`data/reports/offline-reference.json`** and **`data/reports/encoder-parity.json`** are present. The historical 2026-10-13 float comparison reports minimum cosine `0.9999999404` and maximum component error `1.8626451492e-7`; that is historical evidence, not a fresh R0 parity run. Their SHA256 values are retained in the derived R0 summary. R1 should compare the current ONNX outputs on the existing fixed 16 `PARITY_TEXTS` to the retained CPU reference, requiring minimum cosine ≥0.9999 and maximum component error ≤0.0001, and record versions/input/reference hashes. If the ignored reference is unavailable on another machine, explicitly regenerate it using the existing bounded CPU offline workflow; do not install PyTorch into serving or download at request time.

## Frozen contracts and evaluation inputs

[Contract/transition specification](../conversational-rag-contracts.md) · [Executable non-serving contract prototype](../../backend/experiments/rag_r0/contracts.py) · [JSON schemas](conversational-rag-r0-contracts.json)

- Typed finite TurnPlan, separate turn/conversation changes, explicit clears/reset, named/reference targets, bounded chat-user provenance and quarantined legacy preferences/exclusions.
- Grounded retrieval outcomes and truthful encoder capability; a shortlist miss cannot become `not_in_catalog`.
- Legacy/new API and tab-session transition is specified for R2/R3. Existing serving schema/session version remains unchanged in R0. No frontend implementation occurred.

[40 cases / 53 user turns](../../data/evaluation/chat-rag.jsonl) · [Frozen split, hashes and rubric](../../data/evaluation/chat-rag-manifest.json)

Exactly **10 development / 30 held-out**, categories **8 title + 8 semantic + 8 scope/reference + 6 constraints + 4 ambiguity/absence + 3 independence/session + 3 failure/grounding**. **33 real-catalog / 7 synthetic** fixtures; synthetic injection/browser cases are mandatory regressions, not fabricated live quality results. All curated anchor/target IDs resolve in the actual inventory. Semantic anchor IDs are curation seeds, **not complete manually judged relevance labels**. No dataset case was run through either proposed method or the live generator during R0.

The 53 turns alone would imply up to **212 provider calls** if both methods used two calls per turn, before synthetic case separation, injected variants or repeats. This is a conservative illustration, not a final live budget: R4 must itemize actual eligible turns and calls and obtain separate approval, respecting all daily/minute/token/throttle protections. Freeze development-derived ranking/cutoff policy before held-out runs; manually judge relevance/claims and record the actual evidence labels before reporting Recall@8 or quality changes.

## Verification and reproduction

R0 checks passed: **6 experimental contract tests**, frozen fixture/schema/hash check, Ruff across backend, unchanged OpenAPI export check, and **82 existing backend tests**. Benchmarks passed their own parity/call-count/no-retry/stage-replacement assertions. No browser/UI, physical-phone, live answer-quality or hosted test is claimed.

From the repository root, using the existing durable interpreter:

```powershell
$python = 'E:\Games-Recommendation-System\backend\.venv\Scripts\python.exe'
& $python -m unittest discover -s backend/experiments/rag_r0 -p 'test_*.py' -v
& $python backend/experiments/rag_r0/freeze.py
& $python backend/experiments/rag_r0/summarize.py
& $python -m unittest discover -s backend/tests -v
& $python -m game_discovery.api.export_schema --check
```

From `backend/`, `& .\.venv\Scripts\python.exe -m ruff check .` uses the existing project lint settings. `freeze.py --freeze` is an intentional artifact revision command, not the normal check; do not use it to hide drift.

To reproduce benchmarks **after freeing sufficient disk space**, create two isolated environments with the experiment's own lock. For example, from the root, use ignored local artifact paths (not the application's `.venv`):

```powershell
$env:UV_PROJECT_ENVIRONMENT = 'E:\Games-Recommendation-System\data\artifacts\rag-r0\direct'
uv sync --project backend/experiments/rag_r0 --locked
$env:UV_PROJECT_ENVIRONMENT = 'E:\Games-Recommendation-System\data\artifacts\rag-r0\core'
uv sync --project backend/experiments/rag_r0 --locked --extra core
```

Run `backend/experiments/rag_r0/benchmark.py` with `--direct-python` and `--core-python` pointing to those interpreters, `--tokenizer`, `--model`, `--artifact` using the verified paths above, and `--output` to a new report. It starts six sequential fresh workers and performs no downloads, DB connections or live provider calls. `probe.py` takes the same three model-path flags plus `--output`; it uses actual restricted read-only database access and sanitized settings. `uv lock --project backend/experiments/rag_r0/direct-lock --offline` reproduces the Core-free control lock from available cache. Restore/remove shell `UV_PROJECT_ENVIRONMENT` before unrelated uv work.

### Local disk constraint and cleanup

C: became effectively full during a follow-up uv cache write (Windows error 112). The two owned temporary experiment environments were removed as far as Windows allowed; **only locked native-library remnants remain** beneath `C:\Users\User\AppData\Local\Temp\opencode\rag-r0-direct\Lib` and `rag-r0-core\Lib`. They are not usable environments. No unrelated processes, caches, application environment or model files were removed. All benchmark workers finished; no persistent API/preview was started by R0. At the check C: had roughly **0.01 GiB free** (D: 0.67 / E: 1.47 GiB); the owner should free working space before further installation/download work. The offline follow-up lock and all final source checks succeeded. Do not disguise this as a working retained benchmark environment.

## Handoff gate

R0's architecture/measurement/design exits are complete. **Pending:** owner adds/confirms query settings and authorizes **R1 retrieval foundation**. R1 adds bounded title/alias, actual matching lexical candidates, chat-only semantic retrieval/RRF and real-catalog verification while leaving main ranking unchanged. R2/R3/R4, live evaluation budget, remote changes, M5 and publication retain separate approval gates. No commit/push/deployment was performed.
