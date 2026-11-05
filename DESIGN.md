---
name: Game Discovery — Current
description: The owner-selected Current visual system with guest discovery and the owner-authorized compact controls revision.
colors:
  ground: "#111525"
  surface: "#1b2137"
  blue: "#2538bb"
  surface-blue: "#1b2a94"
  tile: "#25378c"
  text: "#f5f6ef"
  muted: "#b8bed1"
  line: "#41485e"
  primary: "#e3fb76"
  primary-hover: "#efffae"
  soft-edge: "#7885e5"
  control-border: "#a0aaf0"
  status-text: "#e1e5ff"
  placeholder: "#c4cbf4"
  disabled-edge: "#78819a"
typography:
  display:
    fontFamily: "'Anton', sans-serif"
    fontSize: "clamp(54px, 7.5vw, 96px)"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-.025em"
  headline:
    fontFamily: "'Anton', sans-serif"
    fontSize: "clamp(36px, 4vw, 54px)"
    fontWeight: 400
    lineHeight: 1.15
    letterSpacing: "-.015em"
  title:
    fontFamily: "'Anton', sans-serif"
    fontSize: "clamp(30px, 3.3vw, 48px)"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-.015em"
  body:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  sentence:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "clamp(20px, 2.1vw, 28px)"
    fontWeight: 600
    lineHeight: 1.5
  favorite-chip:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 800
  action-label:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 800
    lineHeight: 1.6
  search-label:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 800
    lineHeight: 1.4
  input:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "16px"
  limits-lead:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.5
  control-label:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.6
  range-value:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: "18px"
  price:
    fontFamily: "'Manrope Variable', system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.2
rounded:
  flat: "0px"
  tile: "12px"
  slider-thumb: "50%"
spacing:
  sm: "8px"
  compact: "12px"
  md: "16px"
  inset: "20px"
  lg: "24px"
  row: "30px"
  xl: "32px"
  band: "38px"
  gutter: "clamp(20px, 4.5vw, 72px)"
components:
  button-discover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ground}"
    typography: "{typography.action-label}"
    rounded: "{rounded.flat}"
    padding: "15px 24px"
  button-discover-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.ground}"
  button-search:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ground}"
    typography: "{typography.search-label}"
    rounded: "{rounded.flat}"
    padding: "10px 16px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    padding: "8px 0"
  button-feedback:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    rounded: "{rounded.flat}"
    padding: "10px 14px"
  button-feedback-selected:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ground}"
  input:
    backgroundColor: "{colors.surface-blue}"
    textColor: "{colors.text}"
    typography: "{typography.input}"
    rounded: "{rounded.flat}"
    padding: "10px 12px"
  multi-choice:
    backgroundColor: "{colors.surface-blue}"
    textColor: "{colors.text}"
    typography: "{typography.input}"
    rounded: "{rounded.flat}"
    padding: "10px 12px"
  price-well:
    backgroundColor: "{colors.surface-blue}"
    textColor: "{colors.text}"
    typography: "{typography.range-value}"
    rounded: "{rounded.flat}"
    padding: "4px 12px"
    height: "48px"
  navigation:
    textColor: "{colors.text}"
  favorite-chip:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ground}"
    typography: "{typography.favorite-chip}"
    padding: "8px 16px"
  pick-tile:
    backgroundColor: "{colors.tile}"
    textColor: "{colors.text}"
    rounded: "{rounded.tile}"
  result-row:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.text}"
    padding: "30px 0"
---

# Design System: Game Discovery — Current

**Release hardening — 2026-11-05:** the2k shared-catalog release is explicitly authorized and in progress; local chat now uses the real archive/metered AI, superseding the older AI-disabled preview notes below. Clean frontend install/standard TypeScript+Vite build passed at125%. An initial full browser run found one320px error-state a11y issue: the scrolling assistant log lacked keyboard focus when it contained only the user message. It now has native `tabIndex=0` and an inset existing lime focus outline, without scale/layout/copy changes. Final confirmation is recorded in [release evidence](docs/reports/project-release-2026-11-05.md); no new independent/hosted verdict is implied.

The final clean-source confirmation passed **all80frontend tests in one run**; builder opened representative1440/390/320error captures, detector`[]`. This is verification of the focusability fix and regressions, not a new independent design verdict or physical-phone/hosted acceptance.

## Dashboard implementation and review — 2026-11-05

The owner-approved **`/dashboard` is implemented locally**, extending Current rather than replacing its world. Four pill navigation links follow **Your taste → Discover → Dashboard → Saved games**; discovery remains home. The dashboard contains the original Streamlit inventory of **four metrics, eight charts and a sixty-term description word cloud**, with versioned catalog freshness, native exact-value alternatives and read-only independence from taste, saved games and chat. See the component handoff below and [implementation report](docs/reports/dashboard-implementation.md).

**Owner dashboard review remains pending.** The supplied reviewer continuation opened all eight final captures and scored both original P1 findings **RESOLVED**, disposition **ship ONLY at the two-scored-fixes UI scope**, with no material regression attributable to the fix batch. This is not whole-product, owner or hosted acceptance. Owner-review preview **:4173 → isolated read-only :8002** displays the actual 2,000-game generation; the public active catalog remains 40. AI is disabled in that preview; no live LLM calls were made. Stop before separately approved Task 3 publication/activation. Historical design studies and evaluation gates do not add tasks; existing frontmatter, global tokens, palette, typography, asset provenance and `.impeccable/design.json` remain unchanged.

**Header badge/favicon — 2026-11-04:** Owner changed only the small header badge from **Current** to **Steam** and supplied `frontend/public/favicon.png` for the browser tab. The header compass, main wordmark, typography and layout remain unchanged. Both HTML entries now use the32×32 PNG derivative `favicon-32.png` (1,243bytes); original1,254×1,254 PNG is untouched. [Asset provenance](.impeccable/assets/favicon-32.json) records both hashes and deterministic resizing, not AI generation. Existing focused browser regression verifies the badge, both entry links and the served PNG type/dimensions, with1440/390/320 header captures opened. TypeScript/build, actual-source lint and detector`[]` pass. No backend/full-suite/live-AI rerun; hard-refresh4173, and reopen the tab if its favicon remains cached.

**Launch helper removal — 2026-11-04:** Owner requested removal of the catalog/no-sign-in and saved-taste helper paragraph beside **Find my next game**, including its temporary-tab variant. The button, controls and footer device-data disclosure remain. Removed its two unused CSS rules. Updated existing focused browser check passes at1440/390/320 with no horizontal overflow; all three launch-row captures opened. TypeScript/build, actual-target lint and detector`[]` pass; no backend/full-suite/live-AI rerun. Preview rebuilt for8001; hard-refresh4173.

**Assistant Markdown — 2026-11-04:** [Verified implementation](docs/reports/assistant-identity-markdown-2026-11-04.md). Assistant prose now renders safe standard Markdown inside the existing curved chat, while user input remains literal. Preserve14px/1.75 Manrope body copy; compact18px/16px title/subtitle roles and14px minor headings use semantic h3 under the dialog h2. Native lists, bold/italic, lime underlined links, quotes and bounded keyboard-scrollable code replace raw markers; HTML/images/unsafe links are blocked. Current palette, panel/card/composer layout, fonts, storage/history and actions are unchanged.75frontend tests,TypeScript/build/real lint/detector[] pass; two bounded1440/390/320 rounds have clean scoped axe/no-overflow/page-error checks and all captures opened. Builder Markdown-scope review found no material issue, not independent product SHIP or physical-phone acceptance. Frontend skills reconfirmed; tokens/frontmatter/sidecar and prior evidence remain untouched.

**Server-memory assistant integration — 2026-10-29:** [Current evidence and incomplete AI acceptance](docs/reports/llm-first-assistant-2026-10-29.md). Existing Current identity, curved panel, compact header/composer, canonical essentials and Save/Steam actions are retained. A44px text action loads earlier server messages; history failures have a manual read-only retry, successful recovery clears its error, and async restoration preserves drafts. Device-data disclosure now accurately distinguishes server history from the private tab capability/reload cache; New chat confirms actual server erasure and independent empty memory.72full frontend tests and5targeted recovery checks pass. Actual80-turn synthetic archive restoration/paging and expanded cards were inspected at1440/390/320:axe0/nooverflow/pageerrors,0generation; builder opened all3captures. This is a builder integration review, not independent SHIP or blanket AI acceptance. No new artwork/tokens/palette/motion system; earlier phase handoffs remain historical.

**Catalog error-placement fix — 2026-10-28:** the shared catalog-controls error now occupies the flexible controls column instead of the68px desktop label column, resetting to the single column at≤900px. Copy and retry remain readable.32targeted browser tests pass, including five width/axe0/recovery regressions; representative desktop/mobile captures opened. [Evidence](docs/reports/catalog-connection-2026-10-28.md). Existing identity and compact-chat design retained.

**Owner compact-chat follow-up — 2026-10-28:** owner clarified height reduction for the header and composer. Header64px desktop/60px mobile;44px single-row textarea and shorter composer padding, with44px button targets. Placeholder “Ask about games…” fits the compact narrow input. Short cooldown copy relies on the countdown instead of appending an absolute retry timestamp; daily reset information remains. Eight targeted browser tests/nine error scans, TS/build/lint/detector pass; representative captures inspected. [Follow-up evidence](docs/reports/friendly-errors-2026-10-28.md#owner-follow-up--compact-chat).

**Owner-approved friendly errors — 2026-10-28:** [Revision evidence](docs/reports/friendly-errors-2026-10-28.md). Shared error prose uses16px Manrope, bounded wrapping and existing muted/lime colors. Recovery actions use existing pill/outline buttons or44px-height text links. Confirmed deadlines are localized; no request IDs/internal codes appear in user messages. Known waits persist through New chat/reload; reset requires explicit confirmation. The chat status area expands within a viewport-relative cap so action controls remain visible at320px.72frontend tests and nine error scans pass; builder inspected captures and resolved narrow clipping. This is an error-interface scope review, not independent product SHIP; tokens/frontmatter/artwork identity remain authoritative below.

**Current R4 quota — 2026-10-27:** [Applied allowance/checkpoint](docs/reports/r4-quota-increase-2026-10-27.md).100calls/1,500,000units temporary, usage preserved; no frontend/CSS/layout/asset change or new visual verdict. Proposed development13/13passes; held-out8pricing-prose failures remain, R4 not accepted. Today's95calls pause at conservative provider headroom. Restart backend for runtime values; normal defaults50/500,000 and UI/hosted M2 baseline retained.

**Current R4 boundary — 2026-10-26:** [v6 checkpoint](docs/reports/conversational-rag-r4-resume-2026-10-26.md). Backend-only explicit-operation/shortlist/journal fixes; frontend/CSS/tokens/assets/layout unchanged, no new visual verdict.189backend tests/313integration assertions; current9/26development attempts, full live/human/latency gates pending. Additional inference approved, today's50calls exhausted. Preserve authoritative C: journal and resume on later UTC days. R4 not accepted; October25/R3 evidence below is historical.

**Latest R4 boundary — 2026-10-25:** [fixes/current checkpoint](docs/reports/conversational-rag-r4-continuation.md). Backend-only structured-output/metadata/reference/transaction/evaluation changes; frontend/CSS/tokens/layout/assets unchanged, no new UI verdict. Live proposed core journey3/3; full quality/serving-latency gates pending. Additional free-tier inference approved;49calls/390,773reserved units today pauses two-call turns until a later UTC day. R4 acceptance incomplete. R3 browser/scans below remain historical; publication remains separately gated.

**RAG update — 2026-10-25:** [R0–R3 complete locally](docs/reports/conversational-rag-r3.md). Owner approved R3/confirmed skills; v2 browser/API state now integrates the six Core stages. Validated legacy migration/quarantine and exact pending reload/retry preserve transcript/cards/draft. Recovery copy explains compatible-service errors without losing state. Current's curved assistant, essential cards, game-bearing notices, Save/Steam and focus contracts retained; no CSS/palette/type/layout or shipping raster changes.49frontend tests/6axe-0/no-overflow/page-error scans at1440/390/320; builder opened all6 R3 cards/recovery captures, PASS at R3 integration/recovery UI scope (not independent SHIP).151backend tests and actual-catalog/encoder browser flow pass. [Roadmap](docs/conversational-rag-plan.md) / [visual guide](docs/design/conversational-rag-plan.html) govern; stop before separately approved R4. Earlier visual verdicts retain their scopes; no live-quality/publication claim.

**Latest essential-details handoff (2026-10-22):** main and chat now share compact game essentials; zero-game chat replies suppress catalog notices at render time, including retained sessions. This supersedes the older evidence-list/card-content descriptions below, while preserving Current's identity, frontmatter/tokens, sidecar and historical evidence. See the component handoff below; main will write `docs/reports/game-essentials.md`.

**Latest implementation/handoff (2026-10-22):** the owner-directed chatbot revision adds a controller-icon orb, dismissible off-white speech greeting and curved panel within Current, not a new visual world. Main discovery uses favorites, My limits and feedback with **no main text input**; chat owns its conversation, criteria and exclusions. This supersedes earlier assistant-shape, single-form text and post-results refinement descriptions below. See the current component handoff, [revision report](docs/reports/assistant-redesign.md) and [official surface brief](.impeccable/surfaces/frontend-src-current-original-tsx.md). Existing identity, tokens/frontmatter and sidecar are preserved; pre-existing sidecar drift is not repaired.

**Historical owner revision (2026-10-22, before the independent assistant):** remove the complete “Closer to your next.” section after the game rows: heading, assistant transcript, refinement field, session note and new-conversation action. The existing **Rework your request** / **Your taste** links lead back to the single request text and My limits controls. This supersedes the earlier M4 session-refinement composition documented below. No conversation history is forwarded by the frontend; request text still reloads in the tab, with updated recovery/device-data guidance. Dedicated conversation styles are removed; Current's tokens and remaining layout are preserved. Verification: 25 existing frontend tests passed after adapting them to the single-form flow, plus TypeScript, targeted lint and rebuilt :8001 preview. Two 1440px/390px fixture-backed captures were reopened and checked; axe 0, no overflow/page errors; detector `[]`. This is a self-checked removal, not a new independent-review verdict. Historical M4 review/captures describe the earlier UI.

## Overview

**Creative North Star: "Taste as the query"**

The approved Current page composes taste in a cobalt band above an artwork-led, near-black result stream. Acid-lime marks selected favorites, actions and recorded prices; condensed Anton headings contrast with Manrope controls and prose. “Current” identifies the selected design; “Game Discovery” remains the temporary product title.

**Historical coordination — M4 extension verified locally (2026-10-19):** owner approval of `docs/design/m4-plan.html` supersedes earlier M4-unstarted/unauthorized and await-layout stop notes. The implemented extension adds optional request text, applied criteria/uncertainty and explicit conflict choices, then session refinement within this same Current world. The UI reviewer gives **SHIP, UI scope only**, after reopening all 12 refreshed desktop/mobile captures, with no outstanding material UI findings. This is not whole-product approval or publication authority; supplied engineering evidence is attributed separately below. M5 remains unauthorized.

On 2026-10-18 the owner selected the exact Current page, then authorized completing M3 and subsequently consolidating discovery controls. Both HTML entries load `current-original.tsx` → `GuestApp`. The same world contains real API discovery, save/feedback actions, device-data disclosure and a matching saved library. The owner-authorized follow-up replaces the advanced section with three compact multi-choice selectors and a two-handle price range. Main confirms the controls revision complete locally on 2026-10-19: the one material metadata-failure fix is RESOLVED, with ship at ONE-SCORED-FIX verdict-pass scope. The reviewer reopened all 18 refreshed captures and found no regression attributable to that fix; the earlier full controls review found no material visual/accessibility regression. The baseline four-fix verdict remains separate. Neither verdict is blanket whole-product or publication approval. M0–M3 remain complete; M3 is local/unpublished and hosted M2 is unchanged. These controls and baseline verdicts are historical evidence, distinct from the latest M4 UI verdict.

**Key Characteristics:**
- Cobalt header and composer above a near-black result stream.
- Lime favorite chips and artwork toggles with a double lime selection outline.
- Compact native checkbox disclosures for modes, platform and catalog genre, followed by a dual-native-range price control.
- Artwork-led result rows with catalog genres, recorded USD prices and native evidence disclosures.
- Flat hairline structure, Anton headings and Manrope controls and prose.

Extracted from `frontend/src/DiscoveryControls.tsx`, `GuestApp.tsx`, `GuestDiscovery.tsx`, `GuestDashboard.tsx`, `api/analytics.ts`, `HybridSummary.tsx`, `discovery-session.ts`, `GuestGameRow.tsx`, `GuestLibrary.tsx`, `guest-store.ts`, `current-original.css`, `Icon.tsx` and both HTML entries. Source is authoritative; frontmatter records actual CSS values, not newly introduced application variables. Synthesized sidecar ramps are panel illustrations, not application colors. The [official surface brief](.impeccable/surfaces/frontend-src-current-original-tsx.md), [source/provenance](frontend/CURRENT_ORIGINAL.md), [controls revision](docs/reports/discovery-controls.md) and [historical M3 baseline](docs/reports/m3-implementation.md) distinguish current work from prior checks.

## Colors

### Primary
- **Acid lime** (`primary`): selected favorite chips, primary/search fills, selection outline, keyboard focus, prices, checked controls, range fill/thumbs, evidence/store links and compass accent. Filled controls use ground-colored ink.
- **Lime bright** (`primary-hover`): fine-pointer hover fill on discover, favorite and store actions, and the search button.

### Secondary
- **Brand cobalt** (`blue`): header/composer region and browser theme color.
- **Royal-blue inset** (`surface-blue`): native fields and expanded favorite picker.
- **Picker blue** (`tile`): artwork-tile background.
- **Soft periwinkle** (`soft-edge`): request hairlines, picker/tile boundaries and scrollbar thumb.
- **Control edge** (`control-border`), **on-blue helper** (`status-text`) and **placeholder ink** (`placeholder`): readable field boundaries and helper text within the blue region.

### Neutral
- **Near-black ground** (`ground`): page/results and ink on lime.
- **Panel navy** (`surface`): expanded evidence and failed-artwork fallback.
- **Off-white** (`text`), **muted blue-gray** (`muted`) and **slate hairline** (`line`): primary copy, secondary copy and structural separators. Quiet exclusion/undo controls are muted at rest, not lime-filled.
- **Disabled edge** (`disabled-edge`): unavailable discover and at-capacity favorite boundaries. Selected feedback reuses lime fill/ground ink; unselected feedback remains outlined with off-white text.

**The Region and Action Rule.** Use cobalt for the request region and lime for selection, actions and price emphasis; retain the source's muted quiet actions.

## Typography

Anton is self-hosted from `/fonts/Anton-Regular.ttf`, preloaded by both HTML entries with swap rendering. Manrope Variable is locally bundled through the existing font import. Headings use CSS uppercase transformation; the underlying heading copy stays exactly as authored.

The frontmatter records desktop fluid scales. At the mobile breakpoint the opening uses `clamp(52px, 14vw, 76px)` capped to (9ch), results heading (38px), result titles (34px), favorite labels (16px) and prices (20px). The taste sentence becomes (22px). “My limits” uses the small limits-lead role; selector legends use control-label and range endpoints use range-value. Search and selector summaries remain (16px); checkbox labels are (14px), the matching helper (12px), and the USD legend suffix (11px). Supporting metadata is (13px), (12px) on mobile; price captions are (11px). Evidence paragraphs use (14px) with line-height (1.75). The wordmark is Manrope 700, with its small lime label now reading “Steam” at the owner's request. Prices use tabular numerals.

**The Display Has a Job Rule.** Keep Anton for headings and Manrope for controls, prose, prices and the wordmark.

## Layout

**Owner-requested final default display scale — 2026-11-05:125%.** The application renders at **125%** through the root `--study-scale`/CSS `zoom` setting recorded in the sidecar's `extensions.displayScale`. Existing typography, spacing and color primitives remain unchanged; browser zoom stays independent and accessible. Keep browser zoom at100% and hard-refresh the preview. Page minimum and floating-panel viewport caps account for magnification. At≤360px, narrower assistant header/composer gutters preserve the complete title and placeholder without shrinking16px input text or44px CSS targets. The125% setting passed the four-route/six-width bounds check, actual-network browser check, production Vite build and detector`[]`. The usual TypeScript check was blocked by local memory pressure; prior scale results retain their historical scope. [Current setting and evidence](docs/reports/default-scale-120.md); physical-phone/other-engine/hosted acceptance is unverified.

The page has a (320px) minimum width and a fluid shared gutter from the frontmatter; it has no fixed maximum-width shell. Header, composer, results and footer follow normal document flow. Navigation exposes **Your taste → Discover → Dashboard → Saved games**, the last with a count; saved and dashboard use the same frame. The four links are periwinkle-outlined pills with a lime-filled current state and (44px) minimum targets. Navigation wraps at ≤1000px and becomes two columns at ≤640px. Discovery anchors on other pages lead home. The opening pairs the large headline with its introduction. A periwinkle hairline request band contains favorite chips, their disclosure and the boundaries form. The launch row contains only the lime discovery action; its former catalog/device-persistence helper copy was removed at the owner's request.

Desktop boundaries pair a (68px) “My limits” lead column with one four-field row: **modes → platform → genre → price**. The first three fields share equal space; price uses (1.25fr), with (16px) gaps. The lead/control grid uses (12px / 20px) row/column gaps. Dropdown summaries and the price well are (48px) tall. Dropdown panels sit (6px) below their summary, with (8px 12px) padding and a scrollable maximum height of `min(320px, 50svh)`. The matching helper and conditional exclusion/undo sit below the controls. The picker has a (540px) maximum-width search area, (24px) panel padding and four artwork columns with (20px) gaps. Results/library start with (38px) top padding; rows pair art and copy at (.92fr / 1.08fr) with `clamp(24px, 3.5vw, 52px)` gaps and hairline separators. Feedback wraps with (8px) gaps; library sections use a (48px) top margin and (24px) block padding. Device disclosure is capped at (540px).

At **1000px**, picker tiles become three columns and the introduction narrows; controls still occupy one desktop row (recorded at widths 1000/1440/1777). At **900px and below**, the lead moves above a two-column controls grid. At **640px and below**, all four controls stack in the same order, the header places its two-column pill navigation on a second row, the opening stacks, and picker tiles become two columns with (14px) gaps. The discover button remains start-aligned rather than full-width. Result/saved rows stack art over copy with (22px) gaps and the footer becomes a grid. There is no separate 760px breakpoint.

## Elevation & Depth

Page depth is tonal: cobalt, inset royal blue, near-black and navy, divided by thin rules. The page remains flat; the floating assistant is the owner-approved local shadow exception: launcher (`0 8px 24px #070b1b55`), greeting (`0 8px 24px #070b1b44`) and panel (`0 16px 48px #070b1b66`). No gradients or backdrop blur are introduced.

**The Flat Request Rule.** Preserve region color, hairlines and spacing instead of introducing lifted cards or decorative effects.

Search, artwork toggles, discover and favorite chips have (120ms) transform transitions with `cubic-bezier(.23, 1, .32, 1)` and active scale (.98), only under `prefers-reduced-motion: no-preference` and outside keyboard focus. Quiet exclusions and new utility/feedback controls do not share this motion. Focus, disclosure and skip-link reveal are immediate; discovery submission focuses and instantly scrolls to results. Loading placeholders use flat navy blocks without shimmer.

## Shapes

Control wells, fields and result rows are square. Artwork picker tiles have rounded corners (12px), with a (2px) periwinkle border. Selected tiles change that border to lime and add a (1px) lime outline offset (3px); `aria-pressed`, a check and “Selected” restate the state. Slider thumbs are circular (50%) with a (2px) ground border: WebKit (24px) and Firefox (20px) source dimensions. Keyboard focus is a (3px) lime outline offset (5px), off-white on picker tiles; focused slider thumbs use an off-white (3px) outline offset (2px). Inline SVG icons come from `Icon.tsx`.

The shared header navigation uses pill links; the assistant uses a circular launcher/send control, asymmetric speech corners and pill actions. Desktop panel corners are (32px 32px 12px 32px), greeting/cards (24px 24px 8px 24px), user bubbles (22px 22px 6px 22px) and inset composer (28px). Its cobalt header has a curved lower-right corner (44px); mobile panel corners are (28px). These instance shapes do not replace the page's square controls or global radius tokens.

## Components

### Catalog dashboard — implementation and finish handoff (2026-11-05)
- **Established-world comparison:** `GuestDashboard.tsx`, `GuestApp.tsx`, `api/analytics.ts` and `current-original.css` retain cobalt heading/header, near-black ground, navy tracks, lime data/focus, periwinkle accents and flat hairline structure. Anton serves dashboard headings and metric values; Manrope serves chart titles, counts, notes and controls. The owner-pinned pill navigation is a scoped shared-header extension, not a global radius/token redesign. No new raster assets, fonts or palette; existing discovery, library and independent assistant remain.
- **Inventory and layout:** the flat four-column metric strip shows total eligible games, mean known original/list USD price, mean valid discount and distinct normalized developers, with known/unknown coverage rather than zero-filled gaps. The supplied actual expanded-backend display is **2,000 / $19.29 / 7.04% / 1,968**, not fixed UI values. Eight charts cover **free vs paid; original/list price ranges; discount ranges; monthly releases; top 15 genres; supported platforms; review types; top 10 developers**. Grouping proceeds prices → releases/genres → platforms/people → description themes. Long names remain intact; Linux(SteamOS) explicitly means verified Linux support, not independently verified SteamOS/Steam Deck compatibility. These are recorded catalog observations, not live offers or all-Steam totals.
- **Exact values and mobile fixes:** all eight charts have native `details`/counted-table equivalents with captions and row/column headers. A labeled native release-year select filters the twelve month columns and their table together; year-only dates remain unknown-month counts, never fabricated months. At ≤640px metrics use two columns and chart grids stack. The keyboard-focusable monthly-chart region alone scrolls horizontally over a (480px) minimum plot, retaining (12px) month/count labels and a visible scroll/table hint without page overflow. The sixty-term cloud is deterministic, frequency-weighted wrapping text, with a counted-list/method disclosure; its mobile font sizes scale proportionally by (.62), preserving relative weights rather than flattening them. All descriptions are processed within the existing per-game (16,000-character) bound, without combined-text truncation; description themes are not verified gameplay attributes.
- **Snapshot and independence:** the validated `/api/v1/analytics` response identifies the active catalog version, creation date and observed interval. Reload or **Refresh snapshot** fetches the current version without a frontend rebuild; an already-open page remains an identified snapshot. Loading, empty, unavailable and malformed responses remain distinct. Failed refresh retains the prior data with an explicit warning that it may no longer be active. Browsing, year selection and refresh neither write device taste/saves nor inject criteria into discovery/chat. The shared assistant stays independent. The supplied owner-review preview is **:4173 → isolated restricted read-only :8002**, with the actual matching 2,000-game generation; public active **40** is unchanged. Preview AI is disabled; no live LLM calls.
- **Attributed finish evidence:** the original full review found **two P1s** (mobile month-label legibility and disproportionate cloud density). Its continuation reportedly opened **all eight final captures**, scored **BOTH RESOLVED**, and returned **ship ONLY at the two-scored-fixes UI scope**, finding no material regression attributable to that fix batch. Builder reports **79 frontend regression tests before the final visual batch**, then **four final dashboard tests**, clean **1440×1000 / 390×844 / 320×640** axe-0/no-page-overflow/no-page-error scans, plus TypeScript/build/actual E: source lint passing. Detector `[]` ran **once before the final fix batch**, not afterward. Execution used the existing source-matched **C: dependency harness**, not a fresh E: install. This documenter compared source/docs only; tests, browser scans and screenshot review were not rerun here.
- **Acceptance boundary:** owner dashboard review, physical-phone and hosted acceptance remain pending; this scoped verdict is not whole-product, backend, owner or deployment approval. [Main's implementation report](docs/reports/dashboard-implementation.md) owns backend/operational evidence. Task 3 publication and coordinated activation remain separate. Frontmatter/global tokens and `.impeccable/design.json` are preserved; unrelated pre-existing narrative/sidecar drift is not repaired or canonized.

### Favorites and artwork picker
The “I’m into” sentence contains removable lime chips, initially Hades. With no favorites it reads “a fresh start.” “Change favorites” opens guidance, a labeled search field, lime Search button, request/selected-count status and cover toggles. Explicit search calls the API with a trimmed query; empty submission browses a bounded catalog page. Favorite capacity is 50; unselected tiles disable at capacity. Artwork retains source URLs, a reserved (460:215) ratio and the written “Artwork unavailable” fallback. Removed favorite IDs are identified without silently deleting their chips.

### Boundaries and discovery action
“My limits” introduces **Required play modes**, **Required platform**, **Required catalog genre**, then **Price range · USD**. Defaults remain single-player, Windows, Any genre and $0–$20. Each selector is a native `details`/`summary` with native checkboxes and Clear selection; empty means Any, one/two selections show their labels, larger sets show the first plus a count. Escape closes and returns focus to the summary; an outside pointer closes it. All selected modes and genres are required; any selected platform may match. The helper states this and that USD prices are recorded, not live quotes.

The square price well holds endpoint labels and two overlaid native range inputs over a periwinkle rail with lime selected span. Step is one cent; handles cannot cross and remain keyboard-operable. The lower zero label is “Free to play”; a bounded upper zero is “Free only” and submits explicit free-to-play filtering. The cap comes from eligible US/USD catalog facets, rounded up to a whole dollar, extended for stored bounds and capped at the API limit. Missing/loading/error price metadata disables the slider; request failure exposes Retry catalog controls. If stored price is unbounded (`max_price_cents: null`, `free_only: false`) and facets are unavailable, the disabled well says **Any price**, with accessible maximum text **No maximum price**. Its finite internal rendering scale never becomes a persisted or submitted budget; null/false is preserved. Source details are in the controls report.

The old advanced section and preferred/unwanted text fields are removed. Submission explicitly clears those legacy terms so stored hidden criteria cannot affect new discovery. Exact-title exclusions retain conditional Undo exclusions. “Find my next game” explicitly submits discovery, focuses/scrolls to results and disables with truthful loading text while that request runs. Changed criteria invalidate old results and prompt rediscovery.

### Result rows and evidence
Rows render the API's bounded ranked results, not a frozen initial list. Each shows source artwork linking to Steam, an unlinked title, recorded USD price, **catalog genres** followed by recorded play modes/Early Access when applicable, and one source-backed reason. The native **Game details** disclosure uses shared essentials: a whitespace-normalized description excerpt bounded at 280 characters before an ellipsis, supported platforms and a recorded-price date (or explicit missing-data wording), with a reminder to check Steam for current pricing. Redundant evidence/source lists, repeated reasons and generic tradeoff lists are removed from these disclosures; underlying API data remains intact. “View on Steam” is outlined lime; Save is quiet. **Not For Me** and **Already Played** share that desktop action row, pushed right, with wrapping at narrow widths. Each immediately hides only that exact row, preserving the other rows and their order; stored feedback affects the next explicit discovery. Saving remains independent of feedback. Earlier evidence-dump, “Not this one” and three-toggle descriptions belong to historical implementations.

### Essential-details revision — latest finish handoff (2026-10-22)
- **Source inspected:** `GuestGameRow.tsx`, `FloatingAssistant.tsx` and `current-original.css`. Both disclosures use `GameEssentials`; chat adds Genre, Play style and a conditional Early Access note, retaining **Save / Steam only** inside the disclosure. Main retains its single lead reason and genre-led metadata. Compact fact pairs and muted price dates inherit Current's palette/type; no new global tokens or visual world.
- **No-game replies:** notices render only when a message has games and notices. This applies equally to newly received and retained-session messages without deleting their stored notices. Conversation prose, loading, errors and storage/recovery status remain visible. Throttle and quota behavior are unchanged.
- **Attributed finish evidence:** reviewer reportedly opened all **16** game-essentials captures: **actions / main-details / chat-details / no-games**, each at **desktop / wide / mobile / narrow**, and returned **SHIP at this narrow UI scope, no material findings**. Builder reports **32 frontend tests**, **4 visual scenarios / 16 axe-0 scans with no overflow or page errors**, TypeScript/build/targeted lint and detector `[]` passing. This documenter inspected source/docs only; checks and screenshot review were not rerun here.
- **Limits and handoff:** no live AI, real-phone verification or publication claim; the verdict is not whole-product/backend approval. Main will write `docs/reports/game-essentials.md`. Frontmatter/tokens and `.impeccable/design.json` are preserved; pre-existing sidecar drift remains unrepaired, and earlier evidence retains its historical scope.

### Saved library, device data and states
`/saved` reuses artwork rows and Anton section headings for cached titles, feedback and recent summaries. History displays minimum–maximum USD ranges or free-to-play; legacy missing minimums normalize to zero. Cached prices are labeled and keep original observation dates; missing images have the same fallback. Manual catalog availability does not erase removed saves. Feedback can be removed; recent history can be cleared. Device disclosure uses the existing footer and lime summary with square outlined utility buttons. It explains no sync, data loss when storage is cleared and bounded API forwarding. Persistent mode says **Saved on this device**; storage failure says **Temporary in this tab** and exposes retry. Clear resets owned data/defaults and invalidates pending requests across tabs.

No-match copy says filters were not relaxed. Reset restores default boundaries while retaining favorites; unavailable service, stale criteria and empty results remain distinct. No detail/service-status frontend is part of the current implementation; unknown routes show a home link. The schema-v2 sidecar supplies self-contained static previews of actual primitives, not a second running application.

### Historical chatbot revision handoff (2026-10-22; details content superseded)
- **Source inspected for this handoff:** `FloatingAssistant.tsx`, `Icon.tsx`, `current-original.css` and `GuestApp.tsx`. The bottom-right lime controller-icon orb is (72px) desktop / (64px) at ≤640px. The off-white speech invitation appears only while closed with no messages; opening or explicitly dismissing it hides it for the mounted page. Dismissal is not persisted across remounts.
- **Composition and behavior:** desktop width is capped at (440px), height at `min(700px, calc(100dvh - 136px))`. The curved cobalt header, near-black log, navy inset composer, pill actions and circular (44px) send inherit Current's palette/type. The Anton welcome uses `clamp(36px, 4vw, 44px)` desktop / `clamp(32px, 10vw, 40px)` mobile; control/card titles use Manrope. Three starters fill the draft and focus the composer without making an AI call. Empty welcome opens at the beginning of the log, including narrow screens; messages/loading/errors still scroll to the end. Press feedback reuses the existing (120ms) curve at scale (.97), gated by reduced-motion preference.
- **Content and retained contracts:** the two requested in-panel independence and session/provider/price paragraphs and their `aria-describedby` wiring are removed. `GuestApp.tsx` retains the footer device-data explanation. Cards still expand in-panel with recorded USD, original observation dates, source links, reasons/tradeoffs and **Save / Steam only**. Independent chat, shared device Save, session/recovery and desktop-nonmodal / ≤640px mobile-modal behavior remain; source retains sibling inertness, bidirectional focus containment and launcher focus restoration. No new shipping raster asset or artwork-provenance change.
- **Attributed finish evidence:** the independent fresh reviewer reportedly opened **all 12** `.impeccable/review/assistant-redesign/{launcher,welcome,expanded,unavailable}-{desktop,mobile,narrow}.png` captures at **1440×1000 / 390×844 / 320×640** and returned **SHIP, no material UI findings at this chatbot revision scope only**. Builder reports **30 frontend tests** passed; after the narrow initial-log fix, **9 targeted assistant tests / 3 visual scenarios** passed, with **12 final axe-0/no-overflow/no-page-error scans**. TypeScript/build/targeted ESLint passed; detector `[]` predates the minor final heading/scroll fix. These results are supplied evidence, not tests or screenshot review performed by this documenter.
- **Limits and drift:** test cards/prose are mocked; no live Groq call in this revision, physical-phone/software-keyboard verification, backend/product/provider/publication approval or fresh E: installation claim. The C: execution harness builds actual E: source using complete C: dependencies. Main owns backend/operational evidence in the [revision report](docs/reports/assistant-redesign.md). Frontmatter/tokens and `.impeccable/design.json` remain intact; its pre-existing older milestone narrative, three-toggle feedback preview and missing assistant coverage are not repaired or promoted into current rules. Earlier evidence below remains historical.

### Historical independent-assistant implementation/handoff (2026-10-22; shape superseded)
- **Source-inspected behavior:** `FloatingAssistant.tsx`, `assistant-session.ts`, `GuestDiscovery.tsx`, `GuestGameRow.tsx` and `current-original.css` confirm separate page/chat paths. Main sends favorites, limits and feedback; chat sends only its own conversation and state. Shared Save updates the same device library without forwarding the saved list or main preferences to chat. Chat-local criteria/exclusions do not change main discovery.
- **Local composition:** lime bottom-right launcher, cobalt header with New chat/Close, near-black scrollable transcript, navy composer and compact image/title/recorded-USD-price cards reuse Current's materials. Native details expand inside the panel with facts, reasons, tradeoffs, source links and observation dates; game actions are **Save and Steam only**. There is no chat-card feedback row. No new shipping raster asset; real external Steam artwork, provenance links and “Artwork unavailable” fallback remain.
- **Session/recovery:** bounded tab-session context keeps 20 messages, 2,000 characters each, 12,000 total, up to 12 recent cards and 100 chat-local exclusions. Close preserves chat; reload restores retained context/cards/draft. New chat resets chat and cancels pending work. Unreadable storage is protected from overwrite; temporary continuation and blocked-erasure guidance are explicit. Clear my saved data resets owned local/session data and invalidates pending work across tabs. `GuestApp.tsx` and chat-state validation were also inspected for reset wiring and the exclusion bound.
- **Responsive/focus contract:** desktop is nonmodal; at ≤640px the nearly full-height panel is modal and the launcher is hidden while open. Mobile siblings become inert with their prior states restored on close, resize out of mobile or unmount. Tab/Shift+Tab stay within visible panel controls; Escape/Close returns focus to the launcher. These mechanisms were inspected in source, not exercised in this documentation pass.
- **Supplied evidence, not rerun here:** main reports 80 backend tests, Ruff, strict mypy (18 modules) after C-cache relocation, API/generated-type drift, TypeScript/build/targeted ESLint and final 29 frontend tests; seven real-catalog integration cases with Groq HTTP/accounting mocked; owned live checker eight API cases and twelve axe-0/no-overflow/no-page-error scans including the actual disabled-chat response; two expanded-card fixture visual checks. Initial independent review opened eight screenshots and found one mobile focus defect. After the fix/recapture, the focused fresh reviewer reopened six shots: **RESOLVED; SHIP at ONE-MOBILE-FOCUS-FIX UI verdict scope**. This is not blanket UI/product/backend/live-AI/publication approval. This pass inspected source/docs only, not screenshots or test execution.
- **Handoff limits:** Groq key absent/AI disabled, no live provider call; existing quota migration not applied to the application database. Main's [report](docs/reports/independent-assistant.md) and [operations](docs/operations-assistant.md) carry engineering/operational detail. Final preview :4173 build targets API :8001. Local/unpublished; no deployment or M5 authority. Historical evidence below remains attributable to its earlier UI.

### Historical M4 — ordinary extension of Current (2026-10-19; composition superseded)
- **Request and applied criteria:** “What are you looking for? Optional” sits between favorites and My limits. Above the unchanged genre-led rows, the summary separates applied **Hard criteria** from **Soft text preference**, names “What we cannot verify”, and exposes degraded-service wording. Conflicts keep existing controls until an explicit **Keep my controls** or **Apply text changes** choice; the latter applies all proposed changes. Current/proposed values use readable labels and dollars such as “Under $20.00 USD” rather than raw cents. Another refinement is disabled while a conflict awaits resolution.
- **Session refinement:** “Closer to your next.” follows the shortlist. Initial text and refinement drafts each allow 2,000 characters; conversation context keeps at most 20 recent messages, at most 2,000 characters each and 12,000 characters total, dropping oldest messages to fit. Session storage retains text, active criteria and conversation across reloads, **not result objects**: reload asks for a refinement to refresh the shortlist using current controls and feedback. This is separate from the 20 browser-local discovery summaries. A new conversation clears text/context/results and pending discovery while retaining favorites and preferences.
- **Truthful recovery and disclosure:** unreadable/corrupt conversation storage is not silently overwritten; the UI offers reset or temporary continuation. Blocked reads/writes/removal show memory-only or incomplete-erasure notices, with browser site-data guidance when needed. Clear my saved data erases owned local/session data, signals other tabs to erase their tab-local context, restores defaults and invalidates pending work; blocked removal is disclosed rather than claiming erasure. Relevant inputs go to the API and may go to **Groq when enabled**; AI assistance is disabled by default and an actual live provider key is not configured in the verified setup.
- **Actual design-system comparison:** request fields reuse royal-blue insets, off-white Manrope (16px), square periwinkle borders and existing lime focus. Criteria are wrapping lime-text/slate-outline labels, not new filled favorite chips. Conflict content uses panel navy, Anton headings and the existing outlined/filled lime action hierarchy; conversation uses slate rules, Manrope messages and a navy textarea. The conversation width is capped at (860px); mobile conflict padding becomes (18px) and the initial textarea minimum height (132px). Existing responsive controls, genre-led rows and reduced-motion behavior remain. No new palette, fonts, identity, motion system or shipping raster assets were introduced. Artwork remains real catalog external URLs with source links and the existing fallback. Frontmatter tokens and `.impeccable/design.json` are preserved.
- **Evidence and scope:** the UI review reopened all 12 refreshed `.impeccable/review/m4/{initial,hades-results,refined,session-reload,conflict,resolved}-{desktop,mobile}.png` captures and returned **SHIP, UI only**, with no outstanding material UI findings. Supplied final engineering evidence: **25 frontend tests; 68 backend tests in the locked 83-package venv; seven real API cases; 12 scans with axe 0/no overflow and zero page errors; seven scratch-database budget checks including a new-process restart and cleanup**. The reviewer did not run those tests; this documentation pass did not rerun them. Live Groq/provider-success, publication, real-phone verification and measured relevance improvement are not claimed. Earlier M3 evidence remains historical; none of these scoped verdicts is whole-product approval.

## Do's and Don'ts

### Do:
- Do preserve the owner-selected Current identity, defaults, compact multi-choice/range controls, artwork picker and result genres when extending guest behavior.
- Do keep cobalt regions, lime selections, flat hairlines, Anton headings and Manrope controls.
- Do retain source artwork provenance, recorded USD wording, original observation dates and truthful device-storage status.
- Do preserve native keyboard interactions, visible focus and reduced-motion behavior.
- Do distinguish locally complete, unpublished M3 from unchanged hosted M2 and keep the baseline four-fix verdict separate from the controls ONE-SCORED-FIX verdict-pass scope.

### Don't:
- Don't retain superseded designs as active alternatives or restore deleted UI through documentation.
- Don't replace result genres with platforms/play modes or introduce composition changes beyond the owner-authorized controls revision, approved M4 extension, subsequent independent-assistant/chatbot revisions and catalog dashboard extension.
- Don't describe the current guest application as a frozen preview or imply that saving automatically means Interested.
- Don't present recorded or cached prices as live quotes or feedback behavior as evaluated recommendation quality.
- Don't treat scoped review approval or local milestone completion as blanket whole-product/UI release approval or deployment authorization.
