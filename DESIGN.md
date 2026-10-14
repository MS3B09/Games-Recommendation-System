---
name: Game Discovery
description: Temporary M1 foundation system for a restrained dark service-status page.
colors:
  ground: "#101b26"
  text: "#e7eff5"
  muted: "#adbecb"
  line: "#334756"
  action: "#e9d7b6"
  action-hover: "#f4e6cc"
  action-ink: "#17232e"
  connected: "#93ccb4"
  failed: "#e9b69d"
  disabled-bg: "#2b3d4b"
  disabled-text: "#c0ced8"
  disabled-border: "#526878"
  scrollbar: "#61798c"
typography:
  headline:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "clamp(2.25rem, 4.4vw, 3.6rem)"
    fontWeight: 650
    lineHeight: 1.16
    letterSpacing: "-.035em"
  title:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "25px"
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: "-.025em"
  body:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.8
  body-mobile:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.8
  supporting:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.8
  status-label:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.8
  action-label:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "13px"
    fontWeight: 750
  link-label:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "13px"
    fontWeight: 600
  caption:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.8
  wordmark:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "20px"
    fontWeight: 750
    letterSpacing: "-.025em"
  wordmark-mobile:
    fontFamily: "'Manrope Variable', sans-serif"
    fontSize: "17px"
    fontWeight: 750
    letterSpacing: "-.025em"
rounded:
  control: "5px"
  state-dot: "50%"
spacing:
  compact: "12px"
  row: "16px"
  standard: "24px"
  action-offset: "28px"
  section: "32px"
  section-end: "40px"
  gutter: "48px"
  wide: "60px"
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.action-ink}"
    typography: "{typography.action-label}"
    rounded: "{rounded.control}"
    padding: "11px 18px"
  button-primary-hover:
    backgroundColor: "{colors.action-hover}"
    textColor: "{colors.action-ink}"
  button-primary-disabled:
    backgroundColor: "{colors.disabled-bg}"
    textColor: "{colors.disabled-text}"
    typography: "{typography.action-label}"
    rounded: "{rounded.control}"
    padding: "11px 18px"
  text-link:
    textColor: "{colors.text}"
    typography: "{typography.link-label}"
  text-link-hover:
    textColor: "{colors.action}"
  navigation:
    textColor: "{colors.muted}"
    padding: "12px 0"
  navigation-current:
    textColor: "{colors.text}"
  connection:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.text}"
    padding: "36px 0 40px"
  catalog-facts:
    textColor: "{colors.text}"
    padding: "4px 0 0"
  state-dot:
    rounded: "{rounded.state-dot}"
    width: "7px"
    height: "7px"
  state-dot-connected:
    backgroundColor: "{colors.connected}"
  state-dot-failed:
    backgroundColor: "{colors.failed}"
  skip-link:
    backgroundColor: "{colors.action}"
    textColor: "{colors.ground}"
    padding: "12px"
---

# Design System: Game Discovery

## Overview

This is the documented foundation system for the temporary M1 service-status surface, not a final release design. “Game Discovery” is the approved temporary title. No named creative metaphor or final brand identity has been approved. The confirmed direction is restrained, dark and minimal: compact sans typography, pale text, a quiet warm action color and flat sections separated by hairlines.

The implemented page makes a real connection state readable, distinguishes an unpublished catalog from a service failure, and provides manual retry and API documentation. Its generous spacing supports a small amount of operational information. These patterns describe the current foundation; they do not decide the identity or composition of later game-discovery surfaces.

Evidence: `PRODUCT.md`, `docs/design/foundation.md`, `frontend/src/styles.css` and `frontend/src/App.tsx`. Frontmatter is the normative extracted token layer; the source remains authoritative for application behavior. The schema-v2 sidecar holds component previews, focus, motion and breakpoint details. Its synthesized tonal ramps are panel-only previews, not additional approved application colors.

**Key Characteristics:**
- Restrained dark ground with pale readable text and warm action emphasis.
- Flat sections and hairline separators rather than elevated cards.
- Compact operational typography with a larger left-aligned introduction.
- Explicit connection states, manual retry and accessible focus feedback.
- Temporary M1 foundation, with final branding and discovery surfaces unresolved.

## Colors

Blue-tinted dark neutrals carry the page; parchment marks actions and focus, while mint and peach identify connection state.

### Primary
- **Parchment action** (`action`): retry button, wordmark punctuation, keyboard outline, focused skip link, text selection and fine-pointer link hover. `--action` and `--focus` share this same value in the source.
- **Light parchment** (`action-hover`): enabled button hover only.
- **Dark action ink** (`action-ink`): text on the primary button.

### Neutral
- **Dark blue ground** (`ground`): page background, with no separate raised surface color; also selection and skip-link text.
- **Pale blue-white** (`text`): headings, current navigation, fact values and ordinary link text.
- **Muted blue-gray** (`muted`): supporting copy, fact labels, inactive navigation and the unfilled loading indicator border.
- **Blue-gray hairline** (`line`): header, connection section and fact-row separators.
- **Disabled blue-gray** (`disabled-bg`, `disabled-text`, `disabled-border`): the checking button's fill, text and border; a readable distinct state, not opacity applied to the enabled button.
- **Scrollbar blue-gray** (`scrollbar`): thumb against the dark ground.

Mint (`connected`) and peach (`failed`) are semantic status colors, not additional brand accents. The dot is always accompanied by visible text; an unpublished catalog can still have a healthy API connection.

**The State Is Written Rule.** Keep loading, connected and failed states explicit in text; color alone never communicates the service state.

## Typography

**Font:** Manrope Variable with a sans-serif fallback throughout. There is no separate display, serif or monospace family in this surface. Text is sentence case, with compact labels and tightly tracked headings.

### Hierarchy
- **Headline** (`headline`): the introductory h1; fluid size, balanced wrapping and a desktop-only explicit line break.
- **Title** (`title`): the live connection h2, including loading and failure headings.
- **Body** (`body`, `body-mobile`): introductory purpose copy; muted, with a narrower measure (54ch).
- **Supporting** (`supporting`): foundation notice and connection explanation. Paragraphs use the established generous line-height and default measure (65ch).
- **Labels** (`status-label`, `action-label`, `link-label`): connection label, retry and documentation link. Fact rows share the compact label size, with tabular numerals on values.
- **Caption** (`caption`): footer and optional request ID. Long request IDs wrap rather than overflow.
- **Wordmark** (`wordmark`, `wordmark-mobile`): the temporary home-link title with parchment punctuation; not a final logo asset.

Navigation uses the supporting size on desktop and caption size at the mobile breakpoint. Button line-height is inherited; no separate explicit button line-height token has been established.

## Layout

The current page uses a centered, bounded shell (maximum 1240px, including horizontal padding), a minimum viewport height (100svh) and a flexible main region that lets the footer follow short content. The body supports a minimum width (320px). Desktop shell gutters are (48px); the header is at least (100px) tall, with a hairline bottom edge and a (20px) gap between its home link and navigation.

The introduction is left-aligned, bounded to (790px), with vertical padding (76px above, 60px below). The connection section has top and bottom hairlines, padding (36px above, 40px below), and two columns (1.8fr / 1fr) separated by (60px). Explanation and actions occupy the wider column; the three-row definition list occupies the other. This is a service-status composition, not a reusable game-card grid.

Actions wrap with a (24px) gap and sit (28px) below the explanation. Fact rows use equal columns, a (24px) gap and vertical padding (16px), except that the first row has no top padding. Values align right, permit anywhere wrapping and use tabular numerals. The footer wraps, has a (16px) gap and vertical padding (32px).

At **maximum width (760px)**, gutters become (24px), header minimum height becomes (84px), the wordmark and navigation shrink, and the introduction uses padding (48px above, 40px below). Its body copy uses `body-mobile`, and the forced headline break disappears. The status grid becomes one column with a (32px) gap and top padding (28px); the fact list is bounded to (480px). Footer padding becomes (28px) with an (8px) gap. There is no mobile drawer or collapsed navigation control in M1.

## Elevation & Depth

The implementation has no shadows, gradients, blur or raised cards. Depth comes from the dark ground, text hierarchy, space and thin dividing lines. Both status columns belong to the same flat surface.

**The Flat Foundation Rule.** For this M1 surface, separate regions with spacing and hairlines rather than elevated containers.

Motion is limited to an immediate enabled-button press scale (.98), removed under `prefers-reduced-motion: reduce`, and the skip link's focus reveal. There are no authored animation durations, easing tokens, spinners or transition sequences. The existing live region changes in place.

## Shapes

Sections are open, square-edged regions with thin borders (1px), not rounded panels. Buttons alone use the gentle `control` corner radius. The decorative state dot is circular, using `state-dot`, with equal width and height. Focus is a solid outline (2px) offset from the control (5px); it is not a shadow or glow.

## Components

### Buttons

A single restrained primary treatment serves retry and the unknown-route home action.

- **Shape and size:** `button-primary`, matching action-colored border (1px), minimum height (44px). The frontmatter owns padding, color, label weight and radius.
- **Hover:** light parchment fill on enabled controls only, and only for `(hover: hover) and (pointer: fine)`.
- **Focus and press:** shared visible outline; immediate press scale on enabled buttons, with no scale under reduced motion.
- **Checking:** native disabled button using `button-primary-disabled`, its own border color and a wait cursor. Visible text changes to “Checking…”.
- **Recovery:** “Check connection again” replaces the checking label after completion. There is no secondary button variant in the current page.

### Documentation Link

A compact, underlined text action accompanies retry, using `text-link` and its warm hover variant. Underlines are offset (.3em). The API documentation opens in a new tab, announced in screen-reader text. It is rendered only when the API origin can form a valid documentation URL.

### Navigation

The header pairs the temporary title/home link with a single “Service status” link. Navigation is muted by default; the current route uses pale text, an underline and `aria-current="page"`. Fine-pointer hover uses parchment. Mobile retains the same two-link header at smaller text sizes. The colored title punctuation is decorative and hidden from assistive technology.

### Connection Section

A titled flat section contains the status copy, actions and facts. Its copy uses a polite, atomic live region so the heading, state label and explanation update together. The indicator is a small circle with a muted outline while loading, a mint fill when connected and a peach fill when failed; it is hidden from assistive technology because the text carries the meaning.

**The One Check Rule.** Check on entry, then let the visitor retry manually; do not poll or animate a continuing activity after the request completes.

Loading explains the free demo's possible cold start. A failed request supplies recovery copy and, when present, a wrapping request ID. A reachable service with no published catalog is shown as connected with “The catalog is being prepared”, not as an outage. The current request has a timeout (75 seconds). No recommendation interface is implied by the connected state.

### Catalog Facts

A semantic definition list reports catalog publication/version, game count and source freshness. Rows use bottom hairlines rather than cards. Waiting or failure shows “Not available yet” or “Unknown”; an uninitialized catalog reports “Not published”; missing recorded freshness reports “Not recorded yet”. Values come from the real service response, with localized counts and timestamps. Do not replace unknown values with fabricated measurements.

### Keyboard Entry and Route Recovery

The skip link is positioned above the initial viewport using a translate transform, then revealed on focus. It targets the focusable main region. All links and buttons use the common visible outline and manipulation touch behavior. An unknown route reuses the introductory typography and primary link-button for “Go home”; it does not add a separate visual system.

The sidecar includes only implemented patterns: primary button, checking button, documentation link, navigation, connection copy, catalog facts and skip link. Previews are static HTML/CSS documentation, not working API controls. They require no frontend runtime; custom-property references include the source values as fallbacks. The preview frame uses the existing dark ground for legibility. Manrope is inherited from the host when available; the snippets do not fetch fonts.

## Do's and Don'ts

### Do:
- **Do** preserve the restrained dark, flat foundation and its hairline separators.
- **Do** pair each status color with explicit loading, connected or failed text.
- **Do** keep manual retry, readable disabled controls, visible keyboard focus and reduced-motion press feedback.
- **Do** stack the status columns at the existing mobile breakpoint and allow long values to wrap.
- **Do** distinguish unpublished, unknown and unavailable catalog data using real service evidence.
- **Do** treat this document as the temporary M1 foundation, with later visual decisions requiring their own approved scope.

### Don't:
- **Don't** present “Game Discovery” or this foundation as a final approved brand identity.
- **Don't** add game cards, images, synthetic catalog metrics or M2 discovery controls to this M1 surface.
- **Don't** treat a reachable but unpublished catalog as a failed connection.
- **Don't** introduce automatic polling or animated loading ceremonies into the manual-check pattern.
- **Don't** promote the sidecar's synthesized tonal ramps into application tokens or owner-approved palette decisions.
