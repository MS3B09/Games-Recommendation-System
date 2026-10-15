# Game Discovery

<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
Approved: React/TypeScript/Vite, Tailwind CSS, modular Python/FastAPI, one PostgreSQL/pgvector database. Netlify frontend, FastAPI Cloud Hobby backend (owner-selected replacement for Render), Supabase Free database. No accounts.

## Users
Gamers looking for their next game; recruiters and clients assessing full-stack and AI/ML engineering.

## Product Purpose
Help players find games through favorite titles, natural-language taste and explicit constraints. Demonstrate measured, grounded recommendation engineering in an immediately accessible guest experience.

## Operating Context
Desktop and mobile browsers; free hosting can cold-start or pause. Developer collection/indexing/evaluation jobs run sequentially on an 8 GB CPU-only machine.

## Capabilities and Constraints
AGENTS.md governs product scope; IMPLEMENTATION_PLAN.md governs milestones. M1 is complete; M2 has real catalog import, search and favorite-based non-LLM discovery, with hosted verification owner-confirmed. Only clean-database replay remains open; the prepared temporary PostgreSQL/pgvector Actions workflow requires approval before commit/push/execution. Browser persistence/feedback is M3; conversational discovery M4. US store region/USD, recorded freshness, no promised live prices. Scrapling is the sole scraping framework. No next milestone without explicit owner permission.

## Brand Commitments
User-approved dark, refined presentation with restrained accents. “Game Discovery” remains a temporary title, not a final brand decision. User confirmed M2 extends the existing dark Manrope/parchment foundation with favorites/filters beside image-rich results, stacked on mobile, with evidence and price dates visible. Final branding remains M6.

## Evidence on Hand
docs/progress.md and docs/reports/feasibility.md record measured resource results. docs/reports/m2-implementation.md records an active 40-game source-backed catalog, local real browser/API/database discovery and an independently reviewed M2 interface. Hosted M2 is now owner-confirmed; docs/reports/m2-clean-replay.md records the prepared but unexecuted final replay gate. Evaluated relevance improvement is not claimed.

## Product Principles
- Ground claims in source evidence.
- Show empty, unavailable and loading states distinctly.
- Keep the core useful without hosted language-model inference.
- Preserve the free-only, lean architecture.

## Accessibility & Inclusion
Responsive layouts, semantic controls, keyboard navigation, visible focus, readable contrast and reduced-motion support.
