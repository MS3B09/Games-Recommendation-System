# M4 — hybrid discovery and session refinement

**M4 is complete locally, unpublished (2026-10-19).** The owner approved [the HTML proposal](../design/m4-plan.html), then directed implementation. All five M4 acceptance gates have the evidence below. This does not authorize M5, commits, publication or deployment.

## Delivered

- Current's optional request field sits between favorites and My limits. Existing selectors, range slider, exclusions, genre-led rows, saving and feedback remain.
- Applied hard criteria, soft text context, unresolved preferences, reduced-AI status and explicit conflict choices appear before results. Conflicts compare human-readable USD amounts rather than API cents. Existing controls remain active until the user chooses a change.
- Refinement below the shortlist carries current favorites, controls and bounded user context forward. The normalized active criteria are resubmitted, not retrieved from a server-side profile.
- Session storage retains at most **20 messages / 2,000 characters per message / 12,000 total message characters**, plus bounded drafts and criteria. Reload restores conversation, not a cached claim of fresh results. A refinement refreshes the shortlist. Local recent history contains no full conversation or request text.
- New conversation clears context while retaining device preferences. Clear my saved data removes owned local/session keys, resets defaults, and invalidates pending work. Cross-tab reset also erases that tab's conversation before remounting.
- `hybrid-text-v1` combines seed, semantic query and lexical ranking, existing preferred-term support and bounded feedback. Empty query keeps `seed-feedback-v1` behavior. Initial weights are engineering defaults, not measured quality gains.
- Pinned float MiniLM query encoding checks model/tokenizer hashes, revision, dimensions and active catalog version. One nonblocking inference slot; unavailable, busy or mismatched encoders retain lexical/seed discovery. No request-time downloads.
- Conservative local interpretation supports clear numeric upper budgets, free-only, platform/mode requests and specified removal phrases. Ambiguous/unsupported wording stays visible. Optional Groq interpretation returns a partial, validated hard-control patch; it cannot fabricate favorites, exclusions or feedback.
- Optional Groq explanations select structured facts from bounded shortlist evidence. Exact game IDs, evidence IDs, fields, values and normalized facts are checked; server templates render accepted claims. Arbitrary generated prose is not displayed. Invalid claims/JSON, timeout, provider errors or exhausted accounting preserve catalog-derived explanations.
- AI calls have one interpretation and one batch explanation maximum, bounded input/output, one local network slot, no automatic provider retries, per-peer throttling and database-committed global reservations. The counter is a single private row, not a conversation archive.

## Acceptance gates

| Gate | Evidence | Outcome |
| --- | --- | --- |
| Hades scenario: constrained results and honest repetition handling | Real pinned-encoder/API/catalog request, ten results, recorded price strictly under $20, Windows and single-player supported; seed excluded; uncertainty explicitly includes repetition | Passed |
| Refinements retain criteria and expose contradictions | Real story refinement retained criteria; $30 proposal kept $20 until chosen; both explicit API choices and browser text-choice path verified | Passed |
| Reload keeps a bounded session without permanent chat history | Real desktop/mobile reloads, mocked browser persistence/local-history separation, storage bounds and cross-tab clear regression | Passed |
| Invented IDs/claims, malformed output, timeout and quota errors fall back safely | Direct grounding checks and API tests with mocked Groq transport/accounting; no provider request when reservation is denied | Passed, deterministic provider failure simulations |
| Global allowance survives process restart while core remains useful | Real isolated PostgreSQL function tests: concurrent reservations, token/minute ceilings and a separate Python process; live discovery with AI disabled | Passed |

## Actual checks

| Check | Result |
| --- | --- |
| Fresh locked backend environment | `uv sync --locked --extra dev --extra benchmark`: 83 packages in isolated C: virtualenv |
| Backend unittest suite | **68 passed** |
| Ruff | Passed |
| Strict mypy | **17 source files**, passed |
| OpenAPI and generated TypeScript drift | Both passed |
| TypeScript and Vite build | Passed, actual E: source through existing C: frontend tools |
| Targeted frontend lint | Passed with `--max-warnings 0`; actual changed source/tests |
| Full frontend suite | **25 passed**: 18 browser tests and seven storage/session tests |
| Separate live M4 test | **One passed**, seven real API cases and twelve desktop/mobile scans |
| Live accessibility/overflow/errors | All twelve scans axe violations `[]`, overflow false; page errors `[]` |
| Mechanical UI detector | `[]` |
| Real AI-budget SQL verification | **Seven checks passed**, scratch schema cleanup confirmed |

Retained generated reports:

- [Real API/browser results](m4-live-evidence.json)
- [Atomic allowance/restart results](m4-budget-evidence.json)

The live browser test uses owned API **:8002**, existing preview **:4173**, the real restricted active 40-game catalog, and the pinned local float encoder. The test forces AI disabled and stops its owned API afterward. Twelve full-page images are retained locally at `.impeccable/review/m4/{initial,hades-results,refined,session-reload,conflict,resolved}-{desktop,mobile}.png`.

The budget verifier applies the exact new allowance SQL to a uniquely named **scratch schema on the configured database**, using separate migration/runtime logins. It verifies atomic concurrent grants, restart persistence in another Python process, token exhaustion, the four-calls-per-minute ceiling, denied direct counter access and UTC window reuse. It drops the schema afterward. The application schema and active catalog were not migrated or changed by this verification.

### Verification interruptions and corrections

- The retained older C: backend environments had missing executables/package files. Preliminary fallback checks used system Python and existing package paths; final backend checks and live verification instead use the fresh locked M4 environment.
- Existing cached model paths were incomplete. The two public files were reacquired at the pinned model revision, then hash-checked against the active artifact before semantic matching passed. No inference-provider key or paid service was needed.
- An initial Node run failed under local memory pressure. Subsequent bounded single-worker runs used a 512 MB Node heap cap. A six-viewport serial axe test exceeded its old 45-second total budget; its bounded total budget is now 120 seconds, with all assertions retained and no automatic retry. Final full suite passed.
- The original scratch checker tried switching the migration connection to the runtime role, which this environment disallows. The final verifier uses the actual restricted runtime login. An interrupted run's owned scratch schema was explicitly removed; final scratch verification and cleanup passed.
- Historical user queries initially caused an obsolete price-ambiguity warning after refinement. Hard-language interpretation now reads only the current turn; historical context contributes subjective uncertainty and ranking context. A regression test covers the resolved-budget case.

## Independent UI review

Initial review required recapture after that uncertainty correction; it found no new material UI problem. Minor suggestions—USD conflict comparisons and retained-session results guidance—were applied in the same batch.

The reviewer reopened **all twelve refreshed captures** and inspected the current source, including cross-tab session erasure. Final disposition: **SHIP, M4 Current UI surface scope only; no outstanding material UI findings.** This is not a blanket product, backend, deployment, live-Groq or relevance-quality approval. The supplied automated checks above were run by the implementation workflow, not by the reviewer.

The documentation handoff compared the extension with Current: existing colors, Anton/Manrope, square controls, hairlines and original artwork sources are retained. `DESIGN.md` and the official surface brief record the actual extension; the design sidecar is preserved. No new raster asset was introduced.

## Honest limits

- **No live Groq call was made:** `GROQ_API_KEY` is unconfigured and AI is disabled. Success payloads and failure cases were tested with mocked transport. To enable actual Groq, deliberately apply Alembic revision `0003` and configure the server-only settings in [operations](../operations-m4.md). Accounting failure keeps AI disabled.
- The allowance migration is implemented and scratch-tested, **not applied to the application's hosted database**. Public deployment remains the earlier M2 release.
- A small 40-game catalog limits relevance. The Hades request can still rank roguelites highly; “less repetition” is unresolved, not an inferred absence of repetition. M4 does not establish better relevance than a baseline or finish the later evaluation milestone.
- Request timings are recorded for these smoke cases, not a p50/p95 benchmark or hosted latency promise.
- No new fresh frontend install, remote M4 CI, physical-phone, hosted-memory/load or hosted-M4 verification is claimed. Frontend checks use existing C: dependencies against actual E: source; the new backend environment is freshly locked.

## Main changed files

Backend: `catalog/contracts.py`, `catalog/repository.py`, `retrieval/query.py`, `core/settings.py`, `api/main.py`, new `ai/interpretation.py` and `ai/provider.py`, `migrations/0004_ai_budget.sql`, `alembic/versions/0003_ai_budget.py`, `jobs/verify_ai_budget.py`, tests, environment example and generated OpenAPI.

Frontend: `GuestDiscovery.tsx`, `GuestApp.tsx`, `guest-store.ts`, `api/discovery.ts`, generated API types and Current CSS; new `HybridSummary.tsx`, `discovery-session.ts`, hybrid tests, real live M4 test/config and `verify:m4` command. Existing controls/guest tests cover the expanded clearing contract and retain their functional assertions.

See [M4 operations](../operations-m4.md) for reproducible commands and interactive startup. **Stop after this local M4 handoff; M5 and publication require owner authorization.**
