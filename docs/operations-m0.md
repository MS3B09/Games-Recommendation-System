# Run the M0 jobs

**Historical M0 workflow reference. M0–M2 are complete.** The original commands/results below describe feasibility work, not current blockers. Use [M2 operations](operations-m2.md) for the active pipeline and [replay results](reports/m2-clean-replay.md) for the passed clean-database gate. M3 is not authorized.

Run these PowerShell commands from the repository root. The legacy application has its own dependencies; the new job environment does not require them.

```powershell
uv sync --project backend --locked --extra collection --extra benchmark --extra configuration
uv run --project backend --locked --extra collection --extra benchmark --extra configuration python -m unittest discover -s backend/tests -v
uv run --project backend --locked --extra collection --extra benchmark python -m game_discovery.jobs audit --input game_data_for_dashboard.csv --input games_data_recomendation.csv --output data/reports/legacy-audit.json
uv run --project backend --locked --extra collection --extra benchmark python -m game_discovery.jobs probe --app-id 1145360 --app-id 620 --app-id 3611730 --output-dir data/raw/m0-source-probe
uv run --project backend --locked --extra collection --extra benchmark python -m game_discovery.jobs probe --app-id 440 --app-id 3736920 --output-dir data/raw/m0-source-edge-probe
uv run --project backend --locked --extra collection --extra benchmark python -m game_discovery.jobs encoder-benchmark --cache-dir data/artifacts/model-cache --output data/reports/encoder-benchmark.json
```

Audit can run without either extra (`uv run --project backend --locked python -m game_discovery.jobs audit ...`). A probe allows only 1–5 IDs; it is not the resumable collection job. HTTP errors and unverified canonical identities produce a saved partial report and nonzero exit. The demo edge sample is expected to exit 1 if it still redirects to its parent. Do not turn that into an identity mapping.

Model files are downloaded once to an ignored cache at the pinned revision; subsequent runs reuse them. The benchmark needs roughly 115 MB of model files plus environment/cache overhead, and internet access on the first run. A Hugging Face token was not needed for the public model.

## Workaround used on this machine

Installation to E: stalled. From `backend/`, the following succeeded:

```powershell
$env:UV_PROJECT_ENVIRONMENT = 'C:\Users\User\AppData\Local\Temp\opencode\game-discovery-m0-venv'
uv sync --locked --extra collection --extra benchmark --extra configuration --link-mode copy
uv run --locked --extra collection --extra benchmark --extra configuration python -m unittest discover -s tests -v
uv run --locked --extra collection --extra benchmark python -m game_discovery.jobs encoder-benchmark --cache-dir 'C:/Users/User/AppData/Local/Temp/opencode/game-discovery-models' --output ../data/reports/encoder-benchmark.json
```

The root commands assume root-relative inputs; commands from `backend/` need `../` on dataset/output paths. `UV_PROJECT_ENVIRONMENT` is a current-shell setting, not a committed absolute-path configuration.

## Access needed for the next gates

- **Database:** Supabase MCP access and both Python shared-pooler connections are verified. The user updated `MIGRATION_DATABASE_URL` to the Session pooler; the read-only check passed for both URLs. They identify the same underlying database role after removing the pooler's tenant suffix; the runtime role has elevated attributes. Separate least-privilege runtime access is a foundation gate. Database import/schema and sizing remain open. Never paste connection strings into chat.
- **Render/Netlify:** the user reports both services are connected to GitHub. Account-specific quotas and actual deployment access still need verification. No deploy token is required by the current jobs. Configure secrets through provider environment settings when deployment is implemented.
- **Groq:** optional later `GROQ_API_KEY` and verified `GROQ_MODEL`, in backend `.env` locally or Render environment settings. No key is needed for M0 or non-LLM discovery.
- **Frontend:** requested skills are installed project-locally and descriptions/instructions inspected. Restart OpenCode to refresh its skill loader before the next frontend session. See [project skills](project-skills.md).

M0 feasibility is complete. M1's restricted runtime role is now configured and its real login verified; the runtime URL no longer uses the owner role. [Backend foundation setup](backend-foundation.md) records the current status and reproduction steps. Earlier owner connections were valid for the M0 experiments, not the application's final runtime. Milestone completion now requires stopping for user permission before advancing.

Generated snapshots/models/reports are ignored; summarized evidence, code, lockfiles and curated case skeleton are tracked candidates. No commit has been created.

## Redacted environment and connection check

Run from the repository root, with the C: environment override above if needed:

```powershell
uv run --project backend --locked --extra configuration python -m game_discovery.jobs environment-check --env-file backend/.env --project-url https://mmdmxjiawlbridvvhtrt.supabase.co --connect
```

The project URL is public; never put credential URLs in CLI arguments. The job reports allowlisted key-presence flags, project matching, role-name separation, connection modes, and sanitized failure codes. It does not display DSNs, usernames, passwords, or exception messages. Without `--connect`, it only validates configuration presence/identity. Connection checks are read-only and use a 10-second connect timeout plus a 5-second statement timeout. Pooler usernames' project suffixes are removed when comparing role identity.

`partial`/exit 1 means a missing/mismatched URL or failed connection. `ok` without `--connect` is not a connectivity pass. Role separation alone does not prove least-privilege grants. The latest `--connect` check returned `ok`/exit 0 and established authentication and read-only query access for both configured URLs; it did not execute a schema migration.

Both configured URLs contained literal credential `@` characters. The job now performs a targeted, idempotent `%40` correction **in memory** before parsing/connecting, without changing `backend/.env`. This made the runtime check succeed. Correct saved password URL encoding locally for compatibility with other tools; already encoded `%40` is preserved by the job. This helper does not claim to repair every possible malformed URI.

For IPv4-only environments, Supabase's free shared **Session pooler** (port 5432) is the documented alternative to the IPv6 direct endpoint; do not select the paid IPv4 add-on. Get the exact host and role-specific username from **Supabase Dashboard → Connect → Session pooler**. Review DNS/network behavior and update URLs locally as needed; both connections must pass before API/database integration. [Connection documentation](https://supabase.com/docs/guides/database/connecting-to-postgres).

## Reproduce the completed resource/source gates

From the repository root. Use the C: environment override above on this machine; these examples keep generated model files/reports in ignored project folders on a normal local filesystem.

```powershell
# Larger local-only environment; CPU reference is never required by the hosted API.
uv sync --project backend --locked --extra benchmark --extra offline --extra collection --extra api-spike
uv run --project backend --locked --extra benchmark --extra offline python -m game_discovery.jobs encoder-parity --cache-dir data/artifacts/model-cache --output data/reports/encoder-parity.json
uv run --project backend --locked --extra benchmark --extra api-spike python -m game_discovery.jobs api-benchmark --cache-dir data/artifacts/model-cache --env-file backend/.env --output data/reports/api-benchmark.json
uv run --project backend --locked --extra collection python -m game_discovery.jobs probe --app-id 108600 --app-id 284160 --app-id 999999999 --reviews --output-dir data/raw/m0-source-early-access-probe
```

The invalid-ID probe intentionally returns `partial`/exit 1. Review success alone does not prove game existence; the aggregate requires preceding verified appdetails identity. Tests cover its zero-count ambiguity. Aggregate scope is all languages/all purchase types and must stay labeled.

The API benchmark starts **127.0.0.1 only**, with one worker and one inference slot, and terminates its own process tree afterward. It samples startup and request memory, including Windows launcher descendants. It loads pre-acquired local float ONNX files, never downloads them in an HTTP request. Its `/spike/encode` is a disposable local experiment, not a public discovery API. Readiness intentionally remains 503 because no catalog is activated.

### Database sizing reproduction

The agent-created `discovery_m0` schema was removed after measurement. To reproduce from a clean state, explicitly apply `backend/migrations/spikes/0001_m0_sizing.sql` through a migration workflow/MCP before running:

```powershell
uv run --project backend --locked python -m game_discovery.jobs database-sizing --input games_data_recomendation.csv --limit 3000 --env-file backend/.env --project-url https://mmdmxjiawlbridvvhtrt.supabase.co --output data/reports/database-sizing.json
```

Rerun with the same input hash/limit to verify reuse and stable row counts. Changed input is refused rather than overwriting a different experiment. COPY is streamed from the client, with bounded statement timeouts and one atomic import; no database-server files or OS commands are used. Records are quarantined, vectors/taxonomy labeled synthetic, browser access denied, and no artifact activated.

After saving measurements, explicitly apply `0002_cleanup_m0_sizing.sql`. It checks the schema marker and expected objects before removing only the experiment. Initial 60-second COPY timeout caused a complete rollback; successful measured run used 180 seconds for its small local/network import. This timeout is for developer jobs, not public API requests.

Lightweight checks without live providers/model downloads:

```powershell
uv sync --project backend --locked --extra benchmark --extra api-spike
uv run --project backend --locked --extra benchmark --extra api-spike python -m unittest discover -s backend/tests -v
```

Historical M0 result: **26 tests passed**. Offline installation was tested on the user's Windows CPU machine. M2 subsequently passed backend CI with 41 tests and two native Linux PostgreSQL/pgvector builds with real CPU embeddings. Hosted serving still omits `offline`/collection extras: completed M2 uses stored seed vectors and does not load a hosted query encoder. Natural-language/query encoding remains M4 work, not an unfinished M2 gate.
