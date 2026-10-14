# M0 legacy data audit

Measured 2026-10-12 with `game_discovery.jobs audit`. Raw machine-readable output is generated locally at `data/reports/legacy-audit.json`; the command and hashes below reproduce the audit against the retained files.

| Measure | Dashboard CSV | Recommendation CSV |
| --- | ---: | ---: |
| Data rows | 17,370 | 3,000 |
| File bytes | 42,025,048 | 5,903,233 |
| Columns, including legacy index | 27 | 26 |
| Structurally malformed rows | 0 | 0 |
| Unique valid store app IDs | 17,369 | 3,000 |
| Missing/invalid store app IDs | 1 | 0 |
| Duplicate app-ID excess rows | 0 | 0 |
| Duplicate normalized-title excess rows | 3 | 0 |
| Duplicate content rows (ignoring dataframe index) | 0 | 0 |
| Missing/unknown original price | 16,202 | 0 |
| Missing/unknown discounted price | 43 | 0 |
| Missing/unknown genre | 868 | 162 |
| Missing/unknown review label | 12,059 | 2,256 |
| Missing/unknown description | 14 | 0 |
| Missing/unknown tags | No tags column | 153 |
| Suspicious non-game title heuristic | 2,931 | 591 |
| Audit elapsed seconds (successful run) | 10.4227 | 2.1039 |

UTF-8/BOM-aware strict decoding succeeded. No replacement decoding was used. Missingness counts recognize empty values, `Unknown`, `N/A`, `null`, empty list strings, and the nested empty-tag representation. They are not semantic correctness measurements. Numeric review counts of zero are retained as source values, not certified zero-review facts.

## Identity and reproducibility

- Dashboard SHA-256: `56196baa240c027f7071b1fba14ff6f7066417442f99fdf8c96b3859f2004db2`.
- Recommendation SHA-256: `73847c26b6bfb55a570f26f10cc18ef826e1cf2e73233a1a483e2da9cf4f97d4`.
- IDs were extracted only from `store.steampowered.com/app/{positive integer}` links. Titles and artwork are not identity evidence.
- Both datasets contain zero exact-title matches for Hades, Stardew Valley, Portal 2, Hollow Knight, Dead Cells, and Celeste. This six-title sample establishes a serious seed-coverage gap, not overall catalog recall.
- Titles such as “Tirsy's Tale Soundtrack,” “Bus Flipper Simulator Demo,” and Trainz DLC establish mixed content. The heuristic count is a review queue, not a safe eligibility classifier.

## Field trust and reuse decision

All dashboard rows report Windows=true; 3,394 report macOS=true. All Linux and SteamOS values are zero. Recommendation rows have the same all-Windows/all-zero-Linux pattern, with 592 macOS positives. Fresh source probes report Linux=true for Portal 2, Team Fortress 2, and the sampled soundtrack. Do not treat legacy zeros as reliable platform exclusions.

No collection timestamp, region, explicit currency, authoritative app type, coming-soon flag, adult-only classification, or explicit play-mode columns are present. Release dates and artwork query timestamps do not establish price observation time. All legacy prices therefore have unknown currency/region/freshness, even when numerically populated.

Dashboard descriptions are stemmed/tokenized; recommendation descriptions retain readable prose. Recommendation tags use nested list-string representations; space-joined genre strings must not be split into invented terms (for example, Early Access). Maximum `about_game` lengths are 126,588 and 10,460 characters respectively; production semantic text must be bounded.

**Decision:** retain both files as historical discovery/enrichment leads. Quarantine recommendation eligibility until source-supported type/release/content checks are available. Refresh regional prices, platforms, modes, and descriptions; add recognizable seeds. Do not bulk activate the CSV as trustworthy recommendations.

## Repository/configuration audit

Git inspection succeeded using a command-local safe-directory override; global Git configuration was not changed. `AGENTS.md` and `IMPLEMENTATION_PLAN.md` were existing untracked user files. Legacy application/data/artifacts were preserved.

`.streamlit/` contained only a light-theme configuration, not a secrets file. The inspected legacy application reads `GROQ_API_KEY` from Streamlit secrets. New ignore rules cover environment variants, Streamlit secrets, virtual environments, local outputs and model artifacts. This is a current-workspace inspection, not a full historical secret scan.

Legacy pickle/FAISS artifacts were never loaded. The old app's deserialization, fabricated fallback description and unverified “real-time” wording are not adopted by the new implementation.

## Implementation checks

The audit streams CSV rows and uses a temporary SQLite counter with a 2 MiB page-cache setting for distinct identities, titles, and hashes. It does not allocate an N×N matrix or retain all descriptions. This temporary job-local counter is not an additional application database. Tests cover BOM/multiline CSVs, duplicate content with different dataframe indices, unknown values, malformed rows, duplicate headers and lookalike URL hosts.
