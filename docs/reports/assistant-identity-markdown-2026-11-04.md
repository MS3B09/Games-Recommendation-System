# Assistant identity, contextual replies and Markdown — November 4

**Implemented and checked locally; no live AI evaluation was run.** The owner confirmed installed frontend skills before UI changes. Existing Current colors, Manrope typography, curved panel, card details, session/history, recovery and main-discovery isolation are retained.

## Changes

- Both model entry paths now identify the assistant as **Current's game-discovery assistant**. Instructions prohibit claiming ChatGPT or guessing/disclosing the underlying provider, model, GPT version or architecture. When asked, the assistant should describe its app role and explain that implementation details are not shared, rather than inventing a GPT-4 claim.
- General questions should be answered first, then end with a brief, context-relevant bridge to game discovery or an offer to help. This is model guidance, not a repetitive deterministic footer or an extra model call. The previous natural, evidence-grounded recommendation guidance remains.
- Assistant replies now render standard Markdown: headings, bold/italic, ordered/unordered lists, links, quotes and code. User messages remain escaped plain text. Raw HTML and embedded Markdown images are disabled; default safe URL filtering is retained, blocked links become text, external links use `noopener noreferrer` and disclose the new tab. No unsafe HTML injection API or raw-HTML plugin.
- Headings stay below the dialog's h2, with compact visual title/subtitle styles. Existing14px/1.75 chat prose remains, with18px/16px heading roles. Long code scrolls inside a focusable, labeled code region rather than widening the conversation. Links, lists, wrapping and spacing use Current's existing palette.

`react-markdown@10.1.0` is the one added runtime dependency. Its83 new locked packages were added without changing any existing locked package version. The existing C: execution harness also installs the renderer and resolves the actual E: source through its existing Vite/TypeScript mappings. This is not a fresh E: dependency-install/CI claim. No backend model, ranking, public API, storage, schema, environment file or quota change.

## Verification — completed, not queued

- **279 backend checks OK (1 skipped),15.824s**, including60 existing dialogue checks; Ruff, strict mypy30 and unchanged OpenAPI pass. Scripted cases cover the name/architecture questions, a contextual general reply, preserved Markdown text, both prompt paths and unchanged model-call behavior. They are not real-provider compliance or naturalness ratings.
- **75 frontend tests passed,0failed/0flaky,3.5minutes**, including one new focused Markdown regression; source-matched TypeScript and production build pass.
- The new regression checks formatting, unsafe links/HTML/images, preserved user text/cards, reload/history rendering without another inference request, bounded keyboard-scrollable code and no page errors at1440/390/320.
- Two bounded browser rounds (focused test, then full suite) each produced three clean scoped axe/no-horizontal-overflow scans. All three captures were opened in each round; final captures are [desktop](../../.impeccable/review/assistant-identity-markdown/markdown-1440.png), [mobile](../../.impeccable/review/assistant-identity-markdown/markdown-390.png), [narrow](../../.impeccable/review/assistant-identity-markdown/markdown-320.png). Builder review only: no material finding at this Markdown UI scope, not an independent SHIP/product or physical-phone verdict.
- Mechanical detector returned `[]`. Real-source targeted ESLint passes with zero warnings using E: cwd and the external C: configuration. Initial lint attempts were invalid/timed out or ignored the E: files; these were not treated as passes.
- Full frontend output is retained at `C:/Users/User/AppData/Local/Temp/opencode/assistant-identity-markdown-browser-20261104.json`. No completed tests, inference cases or visual-polish rounds need repeating after the reported server restart.

## Load and inspect

The frontend preview was rebuilt for API8001. **Hard-refresh http://127.0.0.1:4173/** to load the new renderer; existing stored replies render as Markdown without rewriting their original content.

Backend prompt changes require a backend restart. Last confirmed process inspection saw the user's API15684/9624 started09:15UTC, before the09:39UTC prompt edit; it was left untouched. The owner subsequently reported a server restart. If that restarted the backend after these edits, no further restart is needed; if it restarted only OpenCode, restart the backend terminal once. New chat is optional for a clean identity check and retains its existing confirmation/real-erasure semantics.

After the restart report, read-only HTTP checks at09:58UTC confirmed API catalog ready/semantic matching true/AI enabled and preview HTTP200. A fresh Windows process inspection timed out, so current PID/source-load ownership is not newly claimed. No process was stopped or started by this task.

No actual provider calls/reservations were made by this work. The09:48UTC SQL snapshot37calls/406,779units includes activity outside the frozen evaluation and is not a new agent quality-pass count or provider remaining-token receipt. Human live checks still consume shared free allowance.

## Preservation and limits

Prechange11-file archive: `C:/Users/User/AppData/Local/Temp/opencode/assistant-identity-markdown-prechange-20261104T093756Z.zip`, SHA256 `b7ab638253dad11e2a0bcda1d980974313bedbfe8951b7a5153e74dfb3aa9211`, byte-verified with no private capabilities. An earlier incomplete archive from the missing harness root lock is not the authoritative backup.

New `dialogue.py` SHA256 `f2b6cbf867cf7cc068e97f6a0757a5bc300c4f93f7105f46f80acd224be7c726`. Completed v10 journal SHA256 `67e251d6c8853aa6dbd2882120f9c0c74d96b4abc701087641edced95fc50a2d` and all original31 attempts/snapshots remain unchanged; never resume them on this changed source or replace hashes. No new live fixture/checkpoint/campaign was prepared.

Prompt guidance is not a guarantee against every adversarial model response. Live identity/bridge naturalness and physical-phone behavior remain for manual review. No paid resources, commit/push/deploy/publication or M5.
