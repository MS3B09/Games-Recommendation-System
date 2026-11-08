# Catalog workflow

Discovery, chat, and dashboard analytics use one active, versioned catalog. The deployed generation contains 2,000 eligible games with US/USD source observations. Prices are snapshots, not live Steam offers. Raw source snapshots and embeddings are not in this repository; [public app IDs and manifests](../data/fixtures/) document the selected population.

Collection uses Steam's structured app-details and review-summary endpoints. Jobs record source identity and timestamps, reject unsupported or ineligible records, generate CPU MiniLM embeddings, and stage a validated generation before activation. Scrapling is the only permitted HTML scraping framework; the catalog jobs use structured API responses.

## Build a new generation

Start with the configured environment and your own migrated database from [local setup](setup.md). Choose a **new** run directory; do not overwrite existing snapshots or activate against a shared database without a reviewed plan. The selected IDs are leads, not a guarantee that every title will remain eligible or available later.

From the repository root, after installing the setup guide's locked dependencies:

```bash
RUN_DIR=data/raw/catalog-refresh
CACHE_DIR=data/artifacts/model-cache
uv run --project backend --no-sync python -m game_discovery.jobs collect --ids-file data/fixtures/catalog-expansion-2000-app-ids.json --run-dir "$RUN_DIR" --reviews --eligible-target 2000
uv run --project backend --no-sync python -m game_discovery.jobs normalize --run-dir "$RUN_DIR" --metadata --target-count 2000 --required-ids-file data/fixtures/m2-app-ids.json
uv run --project backend --no-sync python -m game_discovery.jobs embed --run-dir "$RUN_DIR" --cache-dir "$CACHE_DIR" --batch-size 8 --resume
```

The first embedding run downloads pinned model assets if absent. Collection stops on source failures and can return a partial result; inspect it before using `--resume`. Because the example list has exactly 2,000 identities, an unavailable or newly ineligible game requires a reviewed replacement rather than silently counting it. Prepare a reviewed candidate list with replacements in a **new** run: an existing checkpoint rejects changes to its IDs or settings. Fresh observations may produce a different catalog version and cannot reproduce the exact production snapshot.

After reviewing the target database, normalized records, generated artifact, and analytics metadata, stage the generation using the developer-only migration connection in `backend/.env`:

```bash
uv run --project backend --no-sync python -m game_discovery.jobs import --run-dir "$RUN_DIR" --env-file backend/.env
```

Import stages data and builds version-bound analytics. Before activation, configure the serving runtime with the matching `artifact.json` and compatible pinned tokenizer/model, and plan rollback. Only then, explicitly activate the reviewed generation:

```bash
uv run --project backend --no-sync python -m game_discovery.jobs activate --run-dir "$RUN_DIR" --env-file backend/.env
```

Import and activation write to the specified database; neither runs automatically during application startup. The earlier [40-game clean-database replay](https://github.com/MS3B09/Games-Recommendation-System/actions/runs/38680812079) verified the historical pipeline, not exact reproduction of the current production snapshot.
