# Ponytail simplification — 2026-10-31

> Superseded by the [November1live continuation](assistant-resume-2026-11-01.md). Preserve the v29journal; it must not resume on current source.

## Change

Installed only the requested Ponytail skill, project-local, using:

```powershell
npx --yes skills add https://github.com/dietrichgebert/ponytail --skill ponytail --agent opencode --copy --yes
```

The installed instructions are `.agents/skills/ponytail/SKILL.md`; `skills-lock.json` records its source/hash. No global skill or plugin configuration was installed.

Applied its smallest-complete-change rule: two conditions in `ai/dialogue.py` now distinguish an initial draft from an already-final evidence writer. A ready information batch needs one writer, not a second rewrite of the same evidence. Existing schema, citation, card, price, hard-filter and atomic preference validation still run. Initial native drafts still receive their grounding review; second information rounds remain available. The maximum remains three model calls, not a new two-call limit.

## Focused verification

**Eight existing tests passed in 1.060 seconds; targeted Ruff passed.** Three existing checks were adjusted to reflect the reduced call count/writer boundary; no tests were added.

Checked: two-call ready completion with saved preferences; writer isolation from earlier assistant prose; rejection of an unapproved review card; second information round; atomic invented-price rejection; conflicting preference feedback followed by search; normal → temporary → restored budget searches; and four-record payload fitting.

These use a scripted provider. They verify server mechanics, not whether the real model chooses the requested search. No broad suite, browser rerun or performance benchmark was necessary for this change.

The old API was absent. Started current v29 with the existing observer helper (adding v29 to its allowed version labels). API launcher20368/child22988 listens on8001; preview17652 remains on4173. Catalog ready with40games, semantic matching and AI enabled. No inference or reservation was made.

## Remaining live check

Fresh read-only SQL at `2026-10-31T17:34:22.621883+00:00`:52calls/603,596units used;48calls/896,404units remain. The existing owned-provider bound is still160,980; plus a three-call worst-case39,840 exceeds the200,000 planning ceiling. No quota reset, reduced guard or availability probe was used.

**The actual model's restored-search behavior remains unverified.** After applicable fresh provider/day headroom and SQL checks, run one turn at a time:

```powershell
.\backend\.venv\Scripts\python.exe -m game_discovery.jobs.evaluate_dialogue_live --split development --cases data/evaluation/dialogue-v18.json --case-order D28B D28P D28R --max-new-turns 1 --output "C:/Users/User/AppData/Local/Temp/opencode/assistant-closeout-capability-development-v29.json"
```

That fresh source-locked checkpoint is prepared at zero turns. The fixture is unchanged and its v28 cases were never attempted. All earlier journals/failures remain intact; do not resume them against changed source. Inspect all three budget-turn results, including an actual restored search rather than an acknowledgement. No background evaluation is running. Existing broader acceptance work remains incomplete; no product-quality completion claim is made.
