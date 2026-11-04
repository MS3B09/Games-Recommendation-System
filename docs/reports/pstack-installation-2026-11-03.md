# Project-local pstack skills

## Installation

- Original source only: [cursor/plugins/pstack at ae5650f](https://github.com/cursor/plugins/tree/ae5650febf4320793844c12c4adaa937f417f8da/pstack).
- Pinned commit: `ae5650febf4320793844c12c4adaa937f417f8da`; upstream plugin metadata reports version `0.15.36`.
- Location: `.agents/skills/pstack/skills/<skill-id>/SKILL.md`.
- Copied 558 original files, including all 58 skills and their supporting files, original documentation, agent definitions, artwork, README, and MIT license. Content is unmodified, including frontmatter and relative directory layout.
- Cursor plugin manifests and the Cursor-only automation pack were not installed. Agent definitions are reference files, not registered OpenCode agents.
- No forks, ports, third-party packages, configuration edits, existing skill edits, lockfile edits, setup execution, or automatic updates.

## OpenCode v2 verification

Verified against installed OpenCode `v2.2.5` and the [V2 skills documentation](https://opencode.ai/v2/docs/skills).

- The live project-scoped `/api/skill` registry contains all 58 original skill IDs, with paths inside this installation. Nested grouping directories are discovered without configuration changes.
- All 558 installed files match the SHA-256 values taken from the pinned Git archive. No missing or changed files after the interrupted installation and server restart.
- All 58 registered skill bodies match the originals after normalizing registry line endings. The verifier captures raw UTF-8 CLI output; an earlier PowerShell text capture corrupted Unicode in the verification output, not in the installed files.
- All 124 protected pre-existing files under project skills, commands, and OpenCode JSON configuration retain their pre-installation hashes. All 28 previous registered skills retain their IDs, names, paths, and invocation settings. No skill ID collisions.
- Original `disable-model-invocation: true` remains effective for 57 skills, including `poteto-mode` and `poteto-help`. `setup-pstack` is the only auto-discoverable pstack skill. It was not invoked.

Use explicit OpenCode skill mentions, for example `@poteto-help` or `@poteto-mode`, rather than assuming Cursor's slash commands were installed. Installing these files does not activate poteto mode or replace Ponytail.

Local verification receipts remain in `C:/Users/User/AppData/Local/Temp/opencode/pstack-installation-state.json` and `pstack-verification.json`, alongside the pinned upstream checkout. The state receipt contains per-file hashes; no credentials were copied into this report.

## Compatibility limits

**Skill loading is verified; full pstack workflow compatibility is not.** The original source includes a Claude Code adapter, but no OpenCode adapter. Preserving that source means the following features are not wired up by this installation:

| Feature | OpenCode limitation |
| --- | --- |
| Cursor plugin installation, slash-menu/custom-mode behavior, and plugin updates | This is a local skill snapshot, not a registered native OpenCode plugin. Use OpenCode skill mentions. |
| `Task`, `AskQuestion`, todo tools, `subagent_type: poteto-agent` and `comment-sicko` | Cursor tool names and agent registrations do not transfer automatically. The agent files are retained only as references. |
| Default model slugs, reasoning budgets, and per-role routing | Cursor model identifiers are not verified OpenCode model IDs. No models were selected, mapped, or called. |
| `setup-pstack` | The unchanged skill writes `~/.cursor/rules/pstack-models.mdc`, not OpenCode configuration. Do not treat it as an OpenCode setup wizard. Running it would require separate approval for configuration changes. |
| Cursor rules, transcript paths, cloud agents, Bugbot, automations, webhook/bot setup, and `/loop` integration | Not supplied by copying skills. Cursor-specific history and paths do not become OpenCode history or paths. |
| External skills such as `deslop`, `control-ui`, `control-cli`, and Cursor's built-in `create-skill` | Not bundled in pstack and not installed here. |
| Bundled scripts and external tools | Preserved but not executed, dependency-installed, or verified on Windows. Review their prerequisites before use. |

General engineering and writing instructions can be read as skills. A workflow that requires one of the integrations above cannot be claimed to work unchanged. No adapter or workaround was added.

Existing project approval gates, free-only constraints, inference pause, and commit/push/deployment restrictions remain in force. Installing skills does not authorize their external actions, parallel model calls, publication, or configuration changes. No application code, database, evaluation journal, or runtime service was changed for this task.
