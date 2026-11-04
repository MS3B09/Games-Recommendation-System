# Conversational RAG R1 — retrieval foundation

**2026-10-25 · Complete locally; stop before R2.** Owner explicitly authorized R1. [Plan](../conversational-rag-plan.md) · [Frozen contracts](../conversational-rag-contracts.md) · [Final read-only evidence](conversational-rag-r1-retrieval.json) · [Pre-optimization measurement](conversational-rag-r1-before-roundtrip-optimization.json)

## Implemented scope

- `retrieval/titles.py`: Unicode NFKC/casefold, apostrophe/hyphen/space normalization, exact and compact whole-title matching, verified Spider-Man alias, complete-token/phrase matching, then bounded token-prefix matches. Numeric sequel tokens are retained. Multiple matches return canonical ambiguity options; fuzzy names are suggestions only, never automatically accepted identities.
- `catalog/repository.py`: additive `chat_title()` and `chat_candidates()` methods. Existing `discover()` ranking/filter/feedback logic is untouched by R1. Operations reuse restricted-role checks, read-only repeatable-read transactions, active-version RLS and the two-second statement timeout.
- Title lookup scans at most **257 compact `(app_id,title)` rows**, accepts a complete catalog of **at most 256 eligible titles**, and fetches at most four canonical documents. Above the cap it returns retrieval unavailable, never a false absence. Measured catalog: **40 games**, version **`m2-649714e8b26775165f105d02`**. Larger-catalog parameterized matching is required before expanding the bound. No new extension, table, index or migration.
- Title lookup has no embedding join, recommendation filters or exclusions. Unembedded games remain inspectable. Recent canonical references are re-resolved against the active catalog. Criteria mutation, suitability and conversational reference handling belong to R2.
- Recommendation eligibility, explicit recorded-price bounds, platform any/all, all requested modes/genres, unwanted terms and chat exclusions are applied **before each channel's ranking/LIMIT**. Lexical candidates require an actual `search_text @@ to_tsquery` match, not zero-rank fillers, and do not need embeddings. This reuses existing English title/description search; it does not invent tag coverage.
- Semantic candidates use exact pgvector cosine ordering over a materialized eligible set, avoiding ANN postfilter loss if an approximate index is later introduced. Both channels share one snapshot. Their independently ranked/capped queries use **one database round trip**, retaining stable app-ID tie breaks.
- `retrieval/chat.py`: chat-only query/explicit-filter interface; no favorites, feedback, saved list, main preferences or history. **20 lexical + 20 semantic** pools, equal-weight RRF constant **60**, canonical-ID deduplication, at most **eight evidence candidates**, bounded ID/rank traces. R2 will select at most four cards and pack evidence within the existing provider-byte budget.
- `retrieval/contracts.py`: internal types; `RetrievalOutcome` exactly matches the frozen R0 JSON schema. Only a completed title search establishes `not_in_catalog`. Shortlist misses mean `no_recommendation_match`; database failure cannot establish absence. Missing/busy/failed encoder and artifact-version mismatch produce truthful fallback metadata without retry.
- `retrieval/query.py`: shared existing vector validation and a `ValueError`-compatible typed busy exception. Existing main fallback behavior retained. Strict mypy adds the three new modules. No dependency/lockfile changes.

**Integration boundary:** the foundation is callable and verified, but `/api/v1/chat` still uses its existing workflow. Connecting the new resolver/RRF and finite Core stages is R2; API/session/frontend compatibility is R3. No application UI, wire contract, session version or serving dependency changed in R1.

## Actual configuration and fresh parity

The owner added all three query paths. R1 used **`Settings.from_environment()` / `load_query_encoder()` with those actual values**, not explicit replacement paths. Configured tokenizer/model SHA256 and content-addressed manifest checks passed, and the active catalog matches the artifact. No environment edit, new key, installation or model download was needed.

- Model: `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; normalized 384-dimensional float vectors, 256-token masked mean pooling, single-thread CPU execution.
- Fresh serving-encoder comparison with the **retained 16-text CPU reference** (empty/Unicode/long inputs): minimum cosine **0.9999999404**, maximum component error **1.8626451492e-7**. Gates: ≥0.9999 and ≤0.0001 respectively.
- CPU reference SHA256 `238406a24e756aa17578f3584e0cd4b20f2839447a1d6071e2e0dbd432a29530`; fixed-input digest recorded in JSON. Reference not regenerated; quantization not substituted; no weights downloaded.
- Preserve configured temporary-cache files or deliberately relocate the paths together. Restart an existing owner-run API to load edited settings. This task did not manage the owner's running processes.

## Acceptance evidence

**21 focused retrieval tests; 103 total backend tests.** Coverage: Spider-Man spellings, broad-alias ambiguity, numeric sequels, references, fuzzy suggestions, scan overflow, synthetic unembedded title, hard-filter predicates, invalid vectors, RRF bounds/ties, encoder failures/contention/missing configuration, version mismatch, SQL parameterization, unavailable database and frozen outcome-schema parity. Existing main-discovery, provider/quota and chat-isolation regressions pass.

The real restricted database probe passed **76 assertions**, with no writes or provider calls:

- Five Spider-Man variants find **1817070** and its canonical **single-player** facts.
- `ori` returns real ambiguity options **261570 / 387290**. An intentionally absent title produces catalog-scoped absence only.
- Twelve filter configurations compare actual semantic top-20 IDs against an **independent Python cosine oracle over bounded stored vectors**, filtering canonical records first: neutral, inclusive/strict budget, min/max, free-only, platform any/all, all modes, all genres, unwanted terms, exclusions and impossible bounds. Every lexical ID independently satisfies canonical hard conditions.
- Lexical no-match has no filler rows. A stale artifact uses lexical only and marks semantic unavailable. Impossible criteria do not become catalog absence.
- One development farm/town query includes **Stardew Valley (413150)** in evidence. This is a development sanity check, **not held-out relevance scoring or answer evaluation**.
- Existing main discovery returns identical full results before/after chat reads: IDs **107100, 311690, 237930, 113200** for the fixed Hades/Windows/≤$20 request.

### Findings corrected

1. Initial real-catalog ambiguity check failed: partial `ori` also matched **Original** Sin. Whole-word/phrase matching now precedes prefixes. A regression test retains both actual Ori options without the unrelated partial match; final checks pass.
2. Initial warm remote-retrieval p95 **1,015.863 ms** exceeded the 1,000 ms target. Combining the independently ranked channel queries into one round trip reduced final p95 to **766.725 ms**. Complete oracle/filter checks were rerun after the source change; the [earlier successful functional/slower timing run](conversational-rag-r1-before-roundtrip-optimization.json) is retained. Network variability means this is not an isolated causal benchmark.
3. An initial OpenAPI invocation from `backend/` used the exporter’s repository-root default output path and reported missing/stale schema. Correct root invocation passes; public API files were not regenerated or changed.

## Resources

Final run, **12 warm samples**, local CPU encoding and the existing remote restricted database:

| Measurement | Result |
| --- | ---: |
| Configured encoder hash/load | 2,415.898 ms |
| Encoding-only median / p95 | 8.122 / 9.831 ms |
| Encoding + remote retrieval median / p95 | 670.980 / **766.725 ms** |
| Warm retrieval target | ≤1,000 ms — met in this run |
| Sampled verification interpreter peak RSS | **215.371 MiB** |

Hash/load timing is not an uncached-OS startup guarantee. RSS includes this probe/model/inventory, not a running API/container/process tree or Core; it is not a new hosted/R2 resource gate. Timings include network/snapshot overhead, have a small sample and are not guarantees. No generation latency measured.

## Reproduce

From `E:\Games-Recommendation-System`, with the durable environment and actual ignored configuration:

```powershell
$python = 'E:\Games-Recommendation-System\backend\.venv\Scripts\python.exe'
& $python -m unittest discover -s backend/tests
& $python -m ruff check backend
& $python -m game_discovery.api.export_schema --check
& $python backend/experiments/rag_r0/freeze.py
& $python -m game_discovery.jobs.verify_chat_retrieval --output docs/reports/conversational-rag-r1-retrieval.json
```

From `backend/`, `& .\.venv\Scripts\python.exe -m mypy` checks **21 source files**. Six R0 experimental contract tests and frozen 40-case/53-turn schema/fixture hashes still pass.

The new probe accepts `--reference` for the retained CPU-reference artifact and `--repetitions` (1–30, default12). The reference hash must match R0. Missing configuration/reference/parity fails explicitly; no silent replacement download or keyword-only semantic completion. Other machines need deliberately provisioned documented artifacts. Output parent must exist; failures emit sanitized phase/error type, never driver credentials. Rerunning replaces only the named local report.

## Limits and next gate

- Candidates are not calibrated answer relevance. **No universal cosine cutoff**, confidence/probability claim, held-out quality tuning or live-answer quality claim. R2 must allow fewer/no selections or clarification when evidence lacks support. Calibrate any semantic-only rejection policy on development inputs and freeze before R4 held-out evaluation.
- Unembedded titles and some failure cases are synthetic fixtures. The live bounded inventory currently has vectors; no application row was altered to manufacture failures.
- Multiplayer → title facts → multiplayer memory, exclusions/undo, provenance, prompt packing, grounding and session transitions remain R2/R3. No full frozen-suite, physical-phone or hosted-feasibility claim.
- Existing 50 calls/day, 500,000 reserved tokens/day, per-minute/concurrency bounds, 30-second throttle and metered transport remain unchanged. **Zero provider calls/reservations, database writes/migrations, model downloads, frontend implementation, commits, pushes or deployments.** No new config currently missing. Nearly full C: remains a constraint before future installation work.

**Stop before R2; explicit owner approval required.** Then compose finite Core stages around existing metered transport and these retrieval methods, using frozen intent-scoped memory/evidence contracts. No automatic R3/frontend, live evaluation, M5 or publication authority.

Reference: [pgvector exact cosine, filtering and hybrid search](https://github.com/pgvector/pgvector#querying), consulted through Context7. Restricted snapshots, existing RLS and bound SQL parameters retained; no schema change necessary.
