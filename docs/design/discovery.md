# M2 discovery extension

## Overview

This records the implemented local M2 discovery surface, an ordinary extension of the M1 foundation. The owner approved preserving the dark Manrope/parchment system and the precise composition: favorite selection and filters beside image-rich results, stacked on mobile. Mode: Operate. The direction contract is [the discovery surface brief](../../.impeccable/surfaces/frontend-src-discovery-tsx.md).

This document describes component and presentation behavior; it does not certify public deployment or completion of M2. Browser-local persistence and feedback belong to M3, conversational discovery to M4, and final branding remains unresolved. Current selections are in component memory and disappear on navigation away or reload.

Implementation evidence: `frontend/src/Discovery.tsx`, `GameCard.tsx`, `GameDetail.tsx`, `discovery.css`, `App.tsx` and `styles.css`. [DESIGN.md](../../DESIGN.md) retains the incumbent token frontmatter; `.impeccable/design.json` remains the M1 preview sidecar.

## Colors

Discovery inherits the blue-dark ground, pale text, muted secondary text, hairline separators and parchment action/focus colors. Artwork supplies the strong color, rather than new decorative accents. Inputs use a darker blue field fill (`#14232f`); selected-game rows, artwork fallbacks and loading placeholders use a quiet blue fill (`#213747`). These are observed surface-local values, not additions to the normative global token registry.

## Typography

Manrope Variable remains the only family. The discovery headline is fluid (`clamp(2rem, 3.5vw, 3rem)`), inheriting the foundation heading weight, tracking and line-height. Criteria and results headings are compact (21px); card titles are (19px, weight 700, line-height 1.4). Inputs use (16px) text. Most controls, descriptions and status copy use (13px); supporting copy uses (12px), and price annotations and evidence use (11px). Recorded prices use (14px, weight 700). Counts, ranks and prices use tabular numerals where styled. These sizes describe this surface, not a replacement global type ramp.

## Layout

The shared shell remains bounded (1240px including gutters), with desktop gutters (48px) and mobile gutters (24px). The compact discovery introduction uses padding (44px above, 32px below), followed by catalog count, US/USD context and an observation date in UTC, or explicit unknown-date text.

The workspace has a criteria rail (310px), a flexible results region and a gap (40px), beginning below a hairline with top padding (28px). The rail contains favorite search and selected titles, then budget/platform requirements, an expandable play-mode/genre/exclusion area and the full-width discovery action. Results use two equal columns with gaps (32px vertically, 24px horizontally).

At maximum width (1100px), the rail becomes (280px), the workspace gap becomes (28px), and results become one column. At maximum width (760px), the workspace stacks criteria before results with a gap (36px); results receive a top hairline and padding (28px). Search results have a bounded scrolling area (270px desktop, 210px mobile). There is no sticky rail, mobile drawer or conversational panel.

Game details use an open reading region bounded to (790px), with artwork bounded to (690px). Long titles and evidence values wrap; flexible columns use zero minimum widths to accommodate narrow viewports.

## Elevation & Depth

The surface stays flat: open work areas, space and hairlines separate content. Cards have no enclosing raised panel, shadow, gradient or blur. Image-rich does not mean elevated. The inherited immediate button press scale is removed for reduced motion; loading placeholders are static and hidden from assistive technology.

## Shapes

Controls, selected rows, artwork and placeholder blocks use gentle corners (5px). Artwork reserves the Steam header ratio (460:215), uses cover fitting and fills the available card width. Cards end in a bottom hairline with padding (20px), rather than a rounded outer container. Keyboard focus retains the shared solid outline (2px, offset 5px).

## Components

### Routing and service boundary

The header now offers Discover (`/`) and Service status (`/system`), with the current route underlined and identified programmatically. A ready catalog enables discovery at `/`. During the initial catalog check, on failure, or for an unpublished catalog, `/` shows the foundation connection surface. `/system` retains that operational composition even when a catalog is ready. Numeric `/games/:id` routes load details directly; they are not gated on the catalog-status response. Unknown routes use the existing recovery surface.

### Favorite selection and requirements

Search is explicitly submitted, not issued on every keystroke. Empty search can browse catalog titles. Status text distinguishes initial guidance, searching, failure, no matches and available titles. Selected search rows are disabled; a maximum of 50 favorites is explained in text, and selections have named removal actions.

The budget is an inclusive maximum recorded USD price. Free-to-play disables the price input and removes the maximum from the request. Platform checkboxes support Windows, macOS and Linux with any/all matching. Native expandable controls reveal required play modes, preferred genres (a boost), unwanted genres (exclusion) and excluded titles with Undo actions. Genre choices load independently and offer retry on failure. Copy explicitly distinguishes the sample's genre evidence from missing enriched tags and explains that unknown required facts do not pass filters.

Adding/removing favorites, changing filters or excluding/undoing a title invalidates the current shortlist and aborts pending discovery. The visitor submits Discover games again to obtain results for the changed criteria. Search and discovery requests are aborted on unmount to avoid stale updates.

### Shortlist and result states

Discovery requests up to ten games. Results carry a count and a polite status region; the section exposes its busy state. Loading disables the submit action, changes its label and explains a possible free-service wake-up. Errors show their message and an optional request ID. The unchanged action can be submitted again after failure. No-match results display server-provided suggested refinements and explicitly state that filters were not relaxed. Before submission, an explanatory empty area describes the favorite/constraint workflow.

Each ranked card links its artwork and title to details, then presents recorded price, US observation date (UTC), supported platforms, optional Early Access labeling and description. Missing price or platform information is written as unknown. “View on Steam” opens the recorded store URL in a new tab with an accessible announcement. Exclude adds the title to the current criteria and clears the old shortlist; it is not persistent feedback.

### Inline reasons and provenance

The native “Why this game?” disclosure reveals returned reasons, evidence and tradeoffs in place. The evidence list is filtered to the deduplicated evidence IDs referenced by those reasons. It displays field/value, a source link and collection date (UTC). Copy states that content similarity is a candidate signal, not a guarantee of the same experience. There is no invented match percentage or claim of measured recommendation improvement.

Details reuse artwork, facts and the evidence list, add genres and play modes, and offer a full “Catalog evidence & provenance” disclosure. Loading and failure have written status, with Try again on failure. Details remind visitors that recorded US/USD prices must be checked on Steam for current availability.

### Remote artwork provenance

`Artwork` reads each game's remote `artwork_url` directly. The catalog normalizer takes this HTTPS URL from Steam appdetails' source-provided `header_image`; it does not construct a guessed CDN image path. `backend/src/game_discovery/jobs/catalog.py` records the appdetails source URL, `collected_at` timestamp and response SHA-256 in the collection manifest alongside the raw JSON snapshot. Normalized games retain `artwork_url`, `observed_at` and field evidence carrying the source URL and collection timestamp. Artwork lineage therefore follows the source response and record observation; there is no separate artwork evidence row or image-byte hash in the UI contract.

Images are lazy-loaded with reserved dimensions and empty alternative text because adjacent/link labels identify the game. Missing or failed remote images become a written “Artwork unavailable” fallback. No local raster is shipped as game artwork, and no generated or fabricated asset/provenance artifact is needed. The review PNGs below are verification captures, not application assets.

## Local verification

The existing [local browser report](../../.impeccable/review/m2/report.json) identifies catalog version `m2-649714e8b26775165f105d02`, ten real results, a maximum recorded price of (1999 cents), Windows and single-player requirements. It records zero desktop/mobile accessibility violations, zero browser errors and a passed direct-detail reload. The [desktop capture](../../.impeccable/review/m2/desktop.png) and [mobile capture](../../.impeccable/review/m2/mobile.png) show Hades selected, those controls, artwork-backed results and Bastion's expanded evidence. Desktop shows the side-by-side workspace and two-card result grid; mobile stacks criteria and single-column results.

For this documentation pass, the report and both captures were inspected against the component/CSS source and catalog provenance code. The supplied review handoff reports detector `[]`, desktop/mobile axe zero, no overflow, and a ship disposition with no material fixes for this narrow scope. Detector output and numeric overflow measurements are not fields in `report.json`; those claims are attributed to that handoff, not represented as newly executed checks. This docs-only pass did not rerun the application or browser checks. These are local observations, not hosted-release evidence, an exhaustive accessibility certification or an evaluation of relevance.

## Existing drift retained

The historical M1 foundation document still lists `/` and describes discovery as future work; it now describes `/system` and the fallback at `/`, rather than ready-catalog discovery. `PRODUCT.md` and the sidecar also retain M1-era scope/status language and previews. They are not refreshed by this ordinary extension. Unknown-route recovery still says to return to the foundation page although its home action targets discovery when ready; this minor copy mismatch is reported, not promoted as a rule. The root extension note clarifies route scope without changing incumbent tokens, historical prose, sidecar or implementation. No material mismatch with the approved narrow M2 layout/evidence contract was found.
