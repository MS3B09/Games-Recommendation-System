# Project-local design skills

Installed 2026-10-13 at the user's request. Scope: this repository only; no global OpenCode skill configuration was changed.

Upstream licenses and attribution for the published skill copies are retained in `third_party/`. Vendored skill text remains unchanged, including upstream whitespace; application-code whitespace checks exclude those vendor directories.

| Collection | Project path | Result |
| --- | --- | --- |
| [Impeccable](https://github.com/pbakaus/impeccable) | `.opencode/skills/impeccable/` | Skill version 4.5.2, 24 routed commands; project-local Windows engine v0.1.14 |
| [Emil Kowalski](https://github.com/emilkowalski/skills) | `.agents/skills/` | All 15 skills installed as project-local copies; hashes/source paths recorded in `skills-lock.json` |

Installation commands, run from the repository root:

```powershell
npx --yes impeccable@latest install --providers=opencode --scope=project --no-hooks
npx --yes skills@latest add emilkowalski/skills --agent opencode --skill '*' --copy --yes
npx --yes skills@latest list --agent opencode --json
```

Impeccable uses its own installer and is not listed in the Skills CLI lock/list; its installed `SKILL.md` and launcher were verified separately. Its downloadable binary directory is ignored; keep the skill text, references and launcher. Neither command used global scope. CLI package caches are ordinary tool caches, not global skill installs.

OpenCode officially discovers both project-local paths. Existing `.opencode` configuration and MCP settings were preserved. **Quit and restart OpenCode** to refresh its available skill list; the current session's startup list predates these installations.

Before database schema work, project instructions required installing Supabase's guidance. `supabase-postgres-best-practices` v1.1.1 was installed project-locally under `.agents/skills/` with its source/hash recorded in `skills-lock.json`, and consulted before the sizing/foundation migrations. No global skill configuration changed.

## Use in this product

All installed descriptions were inspected. Impeccable and `emil-design-eng` instructions were read for the future premium discovery UI. Apply other skills only where their descriptions fit: for example `mobile-native` for responsive touch behavior and `animate` for a justified motion implementation. Installing Swift/Expo skills does not change this project's React/TypeScript architecture.

Before frontend work, load applicable skills in the restarted session. Impeccable requires its session context command and relevant workflow references; perform those steps when starting UI work, not as a backend task. Reuse the already agreed product brief instead of restarting the requirements interview. The brief and free-only constraints govern over any skill's generic suggestions.
