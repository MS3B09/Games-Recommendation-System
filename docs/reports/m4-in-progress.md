# M4 — initial implementation record (historical)

**Superseded:** the owner approved the HTML proposal and M4 is now complete locally. See [final implementation/acceptance evidence](m4-implementation.md) and [operations](../operations-m4.md). The initial slice and proposal-review record below are historical, not current blockers or final test counts.

Owner authorization: **2026-10-19**, “Start M4 Implementation.” Frontend skills were confirmed installed. The owner then requested “give me your plan in a html file to see it and decide.”

## Layout decision

Open [`../design/m4-plan.html`](../design/m4-plan.html) in a browser. It illustrates:

- Optional natural-language input between favorite chips and My limits.
- Applied criteria and unresolved preferences before the existing genre-led rows.
- A refinement conversation after the shortlist.
- Explicit conflicting-budget resolution and reduced-AI states.
- Proposed implementation order and acceptance checks.

The standalone page sends no API/provider requests. Its example game is not a ranked or budget-verified result; the Steam artwork source is linked. Scenario buttons illustrate different states. Existing app UI, owner API :8001 and preview :4173 were not replaced. **Await owner approval or adjustments before implementing the application UI.**

Local review URL: **http://127.0.0.1:4184/**. A separate local-only Python server serves just the proposal and its existing font, using an allowlisted temporary script outside the repository. It is independent of :4173 and :8001. The HTML file can also be opened directly if that temporary server is stopped.

### Proposal verification and finish review

- Browser checks: five states at 1440px and 390px, **no horizontal overflow or page errors**. Both budget choices, new-conversation reset and empty-feedback handling passed.
- Six full-page captures retained at `.impeccable/review/m4-plan-{1440,390}-{request,refine,conflict}.png`, all opened and verified.
- Independent finish reviewer: **SHIP at standalone-proposal scope**, no material findings. This is permission to present the proposal for a decision, not application approval or M4 completion.
- Documentation handoff confirmed preserving the existing design system. The proposal uses local Anton headings and system prose, approximating rather than replacing the app's Manrope. Externally loaded Dead Cells artwork comes from Steam's CDN with visible Steam attribution; no new shipping raster asset was created.
- Preview text inputs drive scripted examples, not interpretation. Optionality is explained in the plan rather than beside the field. Detector's logical-padding warnings did not correspond to cramped rendering in inspected captures; its system-font warning reflects the documented prose-font approximation.
- No application UI/CSS was modified. Existing `DESIGN.md`, design sidecar and official app surface brief are preserved. Owner layout approval or adjustments remain the next step.

## Initial backend slice

- `DiscoverRequest.query`: optional, maximum 2,000 characters; legacy requests remain supported.
- `hybrid-text-v1` ranking for nonblank text. Seed/query/lexical weights start at .45/.40/.15, renormalized over available components; preferred-term and bounded feedback adjustments remain. These are engineering defaults, not measured relevance gains.
- Parameterized OR-token full-text ranking against existing PostgreSQL search vectors. This is ranking over the hard-filtered eligible set, not permission to relax constraints.
- Optional local float ONNX query encoding, one nonblocking inference slot. Local model/tokenizer hashes and pinned model revision/dimensions must match the catalog artifact manifest; active catalog version mismatch falls back to lexical/seed retrieval.
- Missing, invalid, busy or failed encoders retain lexical/seed discovery. No request-time downloads. Capability reporting checks active catalog version.
- Unknown prices are no longer excluded solely by an inner price-table join when there is no price constraint; constrained unknown prices still fail.
- Responses disclose unresolved subjective preferences and that natural-language limits are not yet interpreted. No generated explanation, AI provider call or conversation feature is claimed.
- Updated generated OpenAPI and frontend types. The application has no text-query control yet.

Optional server settings: `QUERY_TOKENIZER_PATH`, `QUERY_MODEL_PATH`, `QUERY_ARTIFACT_PATH`. Point these to the same pinned float files and `artifact.json` used by the active catalog. They are developer paths, not secrets. Empty settings disable semantic query encoding. Existing `benchmark` extra supplies ONNX/NumPy/tokenizers; production encoder packaging and resource checks remain pending.

## Checks actually run

- **57 backend unittest tests passed**, including six new query/fallback cases.
- **Ruff passed** across backend.
- Strict mypy passed **14 modules**, including the newly added query module.
- OpenAPI and TypeScript types regenerated through existing tools; **both drift checks passed**.

Execution uses installed Python 3.13.12 with the existing M3 site's installed packages on `PYTHONPATH`, because the retained M3 virtualenv's `Scripts/python.exe` is absent. No fresh environment installation is claimed. No live database mutation, import, provider call or deployment was performed.

Reproduce the backend checks in a working locked environment using documented `uv run --project backend --locked --extra dev --extra benchmark` commands. The local fallback actually used:

```powershell
$env:PYTHONPATH = 'E:\Games-Recommendation-System\backend\src;C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m3-standard-venv\Lib\site-packages'
python -m unittest discover -s backend/tests -v
python -m ruff check backend
python -m game_discovery.api.export_schema --check
```

Run `python -m mypy` from `backend/` with the same environment. Frontend schema generation uses the existing C: `openapi-typescript` CLI against actual E: source.

## Remaining M4 work

All five M4 acceptance gates remain open. Remaining work includes structured interpretation and explicit conflicts, bounded session context and browser storage/reload/reset behavior, provider adapter and grounded claim validation, database-backed atomic usage reservations, per-client throttling, frontend integration after layout approval, and real acceptance/failure-mode checks. Live Groq checks will require server-only `GROQ_API_KEY` and a verified free-tier model configured locally; do not paste keys into chat. Provider configuration and quota schema are not implemented by this slice.

No claim of Hades-scenario acceptance, session refinement, AI quota enforcement, hosted operation, completed M4 or improved relevance is made.
