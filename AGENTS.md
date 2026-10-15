# Project Brief and Agreed Requirements

This document records the outcome of the 20-question project interview and subsequent approved scope revisions. It is the source of truth for the product vision and agreed scope before creating the implementation technical plan.

## 1. Task and Primary Goal

Transform the existing Steam games analytics and recommendation project into a full-stack, professional application.

The primary goal is a **portfolio-quality product that impresses recruiters and clients**, demonstrating both:

- Strong full-stack engineering.
- Strong, credible AI/ML engineering.

The application must also be genuinely useful to real gamers. Career and portfolio value are the primary motivation, supported by an authentic product experience.

The intended professional positioning is **full-stack engineer with strong AI/ML expertise**, rather than a project that only wraps an AI API.

## 2. Product Vision and Target User

### Primary user

A gamer looking for their next game.

### Core problem

Help players find games they will actually enjoy by expressing their taste through favorite games, natural-language preferences, and explicit constraints.

### Signature experience: hybrid discovery

The main discovery flow combines:

1. Favorite games selected by the user.
2. A natural-language description of the desired experience.
3. Optional explicit filters and exclusions.
4. A ranked shortlist of relevant games.
5. Grounded explanations of why each recommendation fits and relevant tradeoffs.
6. Conversational refinement of the results.

The conversational assistant should be integrated into discovery. Hybrid discovery is the product centerpiece.

### Initial acceptance scenario

The user accepted the following example as an initial product acceptance scenario:

> I loved Hades for its combat and sense of progression. I want another satisfying single-player game, but with less repetition, playable on Windows, under $20.

Use this scenario to assess whether ranking and explanations address the request. It is an agreed example, not a verified statement about the user's personal gaming history.

## 3. First Polished Release: User Features

### Guest-only discovery

- The first polished release is guest-only, with no sign-in or registration.
- The public demo should make the core experience immediately accessible to recruiters and gamers.

### Browser-local persistence

Preserve the following locally across visits in the same browser:

- Favorite games and preferences.
- Wishlists or saved games.
- A limited recent discovery history.
- Recommendation feedback.

Keep the active discovery conversation for the current session.

- Label persistent information clearly as **“Saved on this device.”**
- Explain that data does not sync between devices or browsers and is erased when browser storage is cleared.
- Provide a **“Clear my saved data”** action.
- Account profiles, Google sign-in, authentication flows, and guest-to-account migration are outside the first-release scope.

### Adaptive personalization

- Support explicit feedback such as interested, not for me, and already played.
- Feedback must influence future recommendations.
- The frontend sends relevant browser-local preferences and feedback with recommendation requests; the backend applies them to ranking without requiring a user account.
- Keep the personalization approach understandable and practical.
- Do not assume that feedback-driven personalization requires custom model training.

### Explicit discovery controls

Include the following controls in the first polished release:

1. **Budget:** free games or a maximum price.
2. **Platform:** Windows, macOS, or Linux.
3. **Genres and tags:** preferred and unwanted experiences.
4. **Play mode:** single-player, online co-op, local co-op, or multiplayer.
5. **Game exclusions:** already played, uninterested, or explicitly excluded titles.

Enforce hard constraints where the catalog contains reliable supporting data. Display price currency and freshness clearly. Recorded prices must not be presented as guaranteed current purchase prices.

### Natural-language experience preferences

Preferences such as difficulty, mood, session length, story emphasis, and less frustrating gameplay can influence ranking when supporting evidence exists.

- Distinguish source-supported facts from inferred attributes.
- Explain uncertainty when supporting information is missing.
- Do not invent game attributes to satisfy a request.

### Supporting analytics

Keep analytics as a **supporting feature**, not the main product experience.

Provide a focused catalog exploration and analytics page with useful genre, price, platform, and review insights, subject to available data. Exploration should help users discover games.

## 4. AI/ML Ambition

The agreed level is an **evaluated recommendation system**, with strong AI/ML depth but without unnecessary research or implementation complexity.

### Recommendation approach

- Reproducible data preparation and recommendation artifact generation.
- Candidate retrieval using game content and semantic embeddings.
- Hybrid ranking informed by favorite games, stated preferences, supported constraints, and saved feedback.
- Language-model assistance for interpreting requests and producing catalog-grounded explanations.
- Explicit checking of constraints and grounding rather than relying only on prompt instructions.

The exact embedding model, language model, retrieval storage, ranking formula, and inference provider remain technical planning decisions.

### Evaluation: simple and credible

The user chose a measured portfolio standard and explicitly requested simplicity. The agreed starting evaluation is:

- **30–50 curated discovery requests.**
- Manually judged recommendation relevance.
- Comparison against **one simple similarity-based baseline**.
- Checks for hard-constraint violations.
- Checks for unsupported claims in explanations.
- Response-time measurement.
- A straightforward, reproducible evaluation script.
- A concise, readable report describing results, tradeoffs, failures, and remaining weaknesses.

User feedback can provide additional evidence as the app is used. Do not claim quality improvements before measuring them.

Custom training, fine-tuning, multiple experimental models, large labeled datasets, formal user studies, and complex statistical analysis are not required for the agreed first release.

## 5. Catalog and Data Pipeline

### Agreed strategy

Use an **expanded, refreshable catalog with selective enrichment**:

1. Audit and reuse the existing dataset.
2. Verify source availability and field coverage before committing to additional data.
3. Expand coverage and refresh supported fields.
4. Validate and normalize records.
5. Regenerate recommendation artifacts through reproducible, versioned jobs.

### Scraping constraint

**Scrapling is the only scraping tool permitted for this project.**

Do not introduce ScrapeGraphAI, Agent Reach, or another scraping framework into the agreed implementation.

Structured sources or APIs may be assessed where appropriate, but no additional data source or API has been selected. Scraping capabilities do not establish that a particular source is available or suitable.

### Data priorities

Prioritize data that directly improves discovery:

- Coverage of recognizable favorite games and relevant lesser-known titles.
- Clean titles, descriptions, genres, and tags.
- Platform support.
- Explicit single-player, multiplayer, and co-op information.
- Review summaries and counts, where available.
- Price, currency, region context, and freshness, where available.
- Game artwork and store links.

Audit duplicates, missing fields, coverage gaps, and non-game entries. During technical planning, the user approved released standalone games, including free-to-play and clearly labeled Early Access titles. Exclude DLC, soundtracks, software, demos, unreleased games, and adult-only sexual content from recommendations; ordinary mature-rated games remain eligible.

The first release uses the **United States Steam store region and USD**, with currency and observation timestamps displayed clearly.

### Provenance and reproducibility

- Record source URLs and collection timestamps.
- Retain raw snapshots where practical for reproducibility.
- Make cleaning, imports, indexing, and refresh workflows repeatable.
- Show useful catalog freshness information in the public interface.
- Do not assume historical CSV data represents live Steam information.

## 6. User Experience and Visual Direction

Build a **premium game-discovery platform**:

- Dark, image-rich presentation.
- Refined typography and restrained accent colors.
- Polished game cards.
- Game artwork used to create atmosphere.
- Clear, accessible, responsive interactions.
- Visible recommendation explanations, relevant tradeoffs, and refinement actions.
- Integrated conversational discovery.

The exact brand name, visual identity, and page layouts have not been selected. The technical plan proposes Tailwind CSS and shadcn/ui as the UI foundation.

## 7. Architecture Direction

The agreed technology direction is:

- **TypeScript frontend.**
- **Python backend.**
- **One database.**

Use a **lean, professional architecture**:

- One frontend application.
- One modular Python backend.
- Clear internal boundaries for catalog ingestion, retrieval, ranking, AI explanations, and feedback-driven personalization, with guest persistence managed in the browser.
- Standalone jobs for scraping, indexing, and evaluation.
- Run heavy jobs locally where practical to respect free-service constraints.

Avoid unnecessary distributed infrastructure. Separate AI services, dedicated worker fleets, elaborate job queues, and infrastructure-heavy orchestration are not part of the agreed baseline.

The technical planning baseline is recorded in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): React/TypeScript/Vite frontend on Netlify, a modular FastAPI backend on FastAPI Cloud Hobby (owner-selected replacement for Render on 2026-10-14), and Supabase PostgreSQL/pgvector without authentication. Netlify is published at https://steam-discovery.netlify.app/. Exact dependency versions, models, source availability, and hosting feasibility are implementation validation decisions. FastAPI Cloud's public-beta free allowances and actual account settings must be rechecked before deployment; no paid plan is authorized.

## 8. Budget, Hosting, and Availability

### Firm budget constraint

**Free only.**

This applies to hosting, database services, AI inference, scheduled collection, and required operation. Do not design required features around paid services or assume a paid budget is available.

Verify current free allowances and service suitability during technical planning.

### Public demo

The user chose **hosted, with graceful limits**:

- Provide a publicly accessible application.
- Occasional cold starts and limited AI usage are acceptable.
- Handle limitations clearly in the interface.
- Core discovery should remain useful when hosted language-model inference is unavailable or its quota is exhausted.
- Favorite-game recommendations, filters, and saved preferences should not depend on generating an LLM response.
- Bound AI usage to fit free allowances.
- Provide a reproducible local setup for the full application and its data/evaluation workflows.

Free hosting limitations are an accepted product tradeoff. The architecture must still support a credible, usable public demo.

## 9. Developer Operations

Use **developer-managed, clear workflows** for the first release:

- Importing and validating data.
- Scraping supported updates.
- Rebuilding recommendation indexes and artifacts.
- Running evaluation.

Provide documented commands, clear logs, and saved job reports. A protected web administration interface or full administration dashboard is not required for the first release.

The local development/data machine has **8 GB DDR3 RAM, an Intel Core i5-5200U CPU, and no GPU**. Heavy jobs must support bounded-memory CPU execution, small batches, checkpoints, and sequential operation.

## 10. Delivery Approach

- Work through **quality-based milestones**.
- There is no fixed delivery deadline.
- Make a usable discovery experience available early.
- Build toward the complete portfolio standard through evaluation, engineering, and UX polish.
- Preserve a manageable scope and understandable implementation.

When scope tradeoffs arise, prioritize **trustworthy discovery and a polished core experience**.

## 11. Portfolio Deliverables

The user chose a **balanced showcase** covering product, full-stack engineering, and AI/ML evidence.

The finished project should include:

1. A live guest demo demonstrating hybrid discovery.
2. A concise README explaining the problem, features, and setup.
3. An architecture diagram.
4. Documented APIs.
5. A short, reproducible AI evaluation report.
6. Meaningful automated checks for important application behavior.
7. A brief walkthrough of the main user journey.
8. Reproducible local operation and documented developer workflows.

A recruiter or client should be able to experience the product within a few minutes, then inspect credible evidence behind its engineering claims.

## 12. Definition of Portfolio-Ready

The project is ready to showcase when:

- The primary discovery journey is polished, responsive, and accessible without registration.
- Hybrid discovery combines favorite games, natural-language preferences, and explicit controls coherently.
- Recommendations are relevant, enforce supported hard constraints, and provide grounded explanations and tradeoffs.
- Conversational refinement is integrated into the discovery experience.
- Browser-local storage preserves preferences, saved games, limited recent history, and feedback across visits in the same browser.
- The active conversation is retained for the current session; local persistence limits are clearly explained, and users can clear their saved data.
- Feedback influences subsequent recommendations.
- Supporting analytics is useful and visually consistent with the product.
- Catalog expansion and refresh have documented, reproducible workflows using Scrapling as the sole scraping tool.
- The simple evaluation and baseline comparison can be reproduced, with results and weaknesses documented.
- The public application operates within free-only limits and handles service limitations gracefully.
- The repository includes the agreed engineering documentation, meaningful checks, and walkthrough.

## 13. Existing Project Context

The current repository contains a Streamlit application with dashboard, similar-game recommendation, and chatbot sections.

Observed implementation details:

- Similar-game recommendations load a precomputed similarity matrix from `similarity_finale.pkl`.
- The README describes cosine similarity, but the matrix-generation code was not present in the inspected repository.
- The chatbot uses pretrained MiniLM embeddings, a saved FAISS index, and a Groq-hosted language model.
- Chat history is held in Streamlit session state.
- Dataset files and saved recommendation artifacts are present.
- No training, index-building, or evaluation scripts were found in the inspected repository.

Treat this implementation and its data as the starting point to audit and improve. Do not assume the existing artifacts establish quality, reproducibility, or current catalog freshness.

## 14. Status and Next Step

### Required build coordination

- **Milestone approval gate:** after completing a milestone, report its results and stop. Do not start implementation, scaffolding, migrations, or setup for the next milestone until the user explicitly grants permission. Routine work within the current milestone may continue. M1 was already in progress when this rule was added; completion of M1 does not authorize M2.
- Tell the user whenever credentials, secret keys, or hosting access are needed. Specify which service, the required configuration variable(s), and where to set them. Ask the user to configure secrets locally or in the hosting provider's environment settings, not paste secret values into chat. Never commit secrets.
- **Before starting any frontend implementation, including scaffolding, notify the user and wait for confirmation that they have installed the frontend skills they want the coding agent to use.** Then inspect the available skill descriptions and load applicable skills before proceeding. Independent backend or data work may continue while waiting.

The user approved the complete vision at the end of the 20-question interview.

During technical planning, the user approved replacing accounts and sign-in with a **guest-only experience with browser-local persistence**. This revision supersedes earlier account and Google sign-in agreements. Feedback-driven personalization remains required. Supabase remains the proposed PostgreSQL/pgvector host; its authentication service is no longer required.

The technical implementation plan is saved in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). **M0 and M1 are complete; M2 is in progress, explicitly authorized on 2026-10-15.** M2 now has an active 40-game real catalog, reproducible jobs, non-LLM APIs and a locally verified discovery interface. The owner confirmed installed frontend skills and the precise M2 layout before frontend work. See [M2 evidence](docs/reports/m2-implementation.md), [operations](docs/operations-m2.md) and [progress](docs/progress.md). Clean-native-database replay and hosted M2 verification remain open; do not mark M2 complete or start M3. The last verified live Netlify https://steam-discovery.netlify.app/ → FastAPI Cloud https://steam-discovery-api.fastapicloud.dev/ → PostgreSQL deployment was M1 code; the shared database now has the M2 catalog. Free plans, min 0/max 1 replica and one worker were owner-confirmed in M1. The owner explicitly requested committing and pushing M2 on 2026-10-15; publication does not by itself establish provider deployment or hosted acceptance.

During planning, resolve the remaining technical choices without silently expanding scope or weakening the free-only, Scrapling-only, lean-architecture, and simple-evaluation requirements.
