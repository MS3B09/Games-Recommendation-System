# Project history and release status

Current is [live](https://steam-discovery.netlify.app/) with a shared catalog of 2,000 games. The original three-task completion scope was owner-accepted on November 6, 2026; subsequent dashboard and assistant improvements were published on November 7.

| Phase | Work completed |
| --- | --- |
| Original application | A Streamlit app provided analytics, recommendations, and a chatbot. |
| M0 | Audited the existing data and assessed sources, hosting, and CPU embedding feasibility. |
| M1–M2 | Built the API, database and hosting foundation, catalog pipeline, and initial 40-game discovery experience. |
| M3–M4 | Added guest persistence, feedback, controls, and AI-assisted discovery. |
| Assistant follow-up | Built catalog retrieval, conversation state, validation, and browser integration; later simplified the engine and added catalog-wide title grounding. |
| Revised completion plan | Expanded the shared catalog to 2,000 games, added the dashboard, and published the app. This replaced the original remaining M5–M8 roadmap, rather than completing every original gate. |
| November 6–7 follow-ups | Published interactive dashboard charts, layout and hover refinements, and the general assistant title-lookup fix. |

The November 7 application release was built from [`cd615c2`](https://github.com/MS3B09/Games-Recommendation-System/commit/cd615c2fa49cfe811ee20ecf04aa1bb85867cc26). [Backend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42409600236) passed 302 tests (one skipped); [frontend CI](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/42409600180) passed 81 tests. Hosted discovery, saves, dashboard interactions, and responsive Chromium checks passed without new live AI calls.

The owner-reviewed original release does not establish comprehensive recommendation relevance or assistant quality. Earlier failures, incomplete human judgments, and the absence of a fresh live-provider quality check remain documented in the [evaluation summary](evaluation.md).
