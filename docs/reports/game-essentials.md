# Essential game details and chat notices

Owner-requested local follow-up to the chatbot redesign.

## Changes

- Chat replies containing no games no longer render catalog notices. This also applies to restored tab-session messages. Notices remain in the underlying response/session data and remain visible for game-bearing replies; error/retry/storage guidance is unaffected.
- Main-result **Not For Me / Already Played** actions now align to the right of the same desktop row as Steam/Save. They wrap on smaller screens, retaining exact-title dismissal and existing feedback semantics.
- Main disclosure is now **Game details**: a description excerpt bounded to 280 characters plus ellipsis, supported platforms and one recorded-price date/current-price reminder. Genres and modes already appear above it.
- Chat uses the same essentials with genre, play style and conditional Early Access information. Save/Steam remain within the details. Repeated reasons, technical source lists and generic tradeoff paragraphs are removed from the presentation; underlying API evidence is unchanged.
- The 30-second per-peer message throttle was explained, not changed. Daily 50-call/500,000-reserved-token accounting and four-provider-calls-per-minute limit remain.

## Verification

- TypeScript, production build and targeted ESLint passed using the corrected C: harness against actual E: source; build targets API :8001.
- **32 frontend tests passed**, including right-side desktop alignment, concise details, no-game notices after reload and game-bearing notice retention.
- **4 visual scenarios passed**, at 1440, 1816, 390 and 320 widths: actions, expanded main details, expanded chat details and no-game chat. **16 axe scans with zero violations**, no horizontal page overflow or page errors.
- Mechanical detector: `[]`.
- Independent reviewer opened all 16 `.impeccable/review/game-essentials/{actions,main-details,chat-details,no-games}-{desktop,wide,mobile,narrow}.png` captures and returned **SHIP at this narrow UI revision scope**, with no material findings. Lower expanded chat content was source-inspected rather than fully visible in these captures.
- Documentation handoff updated DESIGN.md and the official surface brief, preserving tokens/sidecar and historical evidence.

UI checks use fixture catalog/chat/artwork. No live inference, database changes, backend changes, physical-phone/software-keyboard verification, commit, push or deployment. Earlier AI-quality limitations remain. E: dependencies remain incomplete; use the documented C: execution harness for preview/build. Hard-refresh an existing preview to load the rebuilt UI.
