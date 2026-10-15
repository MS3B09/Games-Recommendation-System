"""Opt-in real-DB interruption test: all writes are deliberately rolled back."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from dotenv import dotenv_values
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import make_url

from game_discovery.catalog.contracts import digest
from game_discovery.core.database_url import normalize_db_url
from game_discovery.jobs.catalog import publish, validated_artifact, write_json


def verify_import(run_dir: Path, env_file: Path, output: Path) -> dict:
    games, embeddings, artifact = validated_artifact(run_dir)
    # A real-source one-game subset gives this test an independent artifact identity.
    documents = [games[0].model_dump(mode="json")]
    vectors = [next(item.model_dump() for item in embeddings if item.app_id == games[0].app_id)]
    manifest = {key: value for key, value in artifact.items()
                if key not in {"version", "embeddings_sha256", "encoder", "tokenizer_sha256", "model_sha256"}}
    manifest.update(games=1, games_sha256=digest(documents))
    unsigned = {**artifact, **manifest, "embeddings_sha256": digest(vectors)}
    unsigned.pop("version")
    subset = {**unsigned, "version": "m2-" + digest(unsigned)[:24]}
    raw_url = dotenv_values(env_file, interpolate=False).get("MIGRATION_DATABASE_URL")
    if not raw_url:
        raise ValueError("Configure MIGRATION_DATABASE_URL locally")
    engine = create_engine(make_url(normalize_db_url(raw_url)).set(drivername="postgresql+psycopg"),
                           hide_parameters=True, connect_args={"prepare_threshold": None, "connect_timeout": 10})
    try:
        with engine.connect() as connection:
            active_before = connection.execute(text("select version from discovery.catalog_versions where active")).scalar()
            if connection.execute(text("select count(*) from discovery.catalog_versions where version=:v"), {"v": subset["version"]}).scalar_one():
                raise ValueError("Interruption fixture already exists; refusing to touch it")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for filename, value in (("games.json", documents), ("normalized.json", manifest),
                                    ("embeddings.json", vectors), ("artifact.json", subset)):
                write_json(directory / filename, value)
            original = Connection.execute
            interrupted = []

            def interrupt(connection, statement, *args, **kwargs):
                result = original(connection, statement, *args, **kwargs)
                if str(statement).lstrip().startswith("insert into discovery.games"):
                    interrupted.append(True)
                    raise RuntimeError("simulated_interruption")
                return result

            with patch.object(Connection, "execute", interrupt):
                try:
                    publish(directory, env_file, activate=True)
                except RuntimeError as error:
                    if str(error) != "simulated_interruption":
                        raise
                else:
                    raise AssertionError("Simulated import did not interrupt")
            assert interrupted, "Import must actually reach the write transaction"
            # Missing vectors must fail validation before touching the database.
            write_json(directory / "embeddings.json", [])
            try:
                publish(directory, env_file, activate=True)
            except ValueError:
                pass
            else:
                raise AssertionError("Incomplete artifact was accepted")
        with engine.connect() as connection:
            remaining = connection.execute(text("select count(*) from discovery.catalog_versions where version=:v"), {"v": subset["version"]}).scalar_one()
            active_after = connection.execute(text("select version from discovery.catalog_versions where active")).scalar()
            assert remaining == 0 and active_before == active_after, "Interrupted import changed publication"
        report = {"status": "passed", "interrupted_write_rolled_back": True,
                  "incomplete_activation_rejected": True, "active_version_unchanged": active_after}
        write_json(output, report)
        return report
    finally:
        engine.dispose()
