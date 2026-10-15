"""Manually dispatched, GitHub-hosted-only M2 replay against a disposable service."""

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from fastapi.testclient import TestClient
from psycopg.errors import CheckViolation, ForeignKeyViolation, InsufficientPrivilege, UniqueViolation
from pydantic import SecretStr

from game_discovery.api.main import create_app
from game_discovery.catalog.contracts import Source, digest
from game_discovery.core.settings import Settings
from game_discovery.jobs.catalog import embed, normalize, normalize_payload, publish, validated_artifact, write_json
from game_discovery.jobs.verify_catalog import verify_catalog
from game_discovery.jobs.verify_import import verify_import

REPOSITORY = "MS3B09/Games-Recommendation-System"
DATABASE = "m2_replay"
TABLES = ("games", "game_platforms", "game_terms", "game_prices", "game_embeddings")


def replay_environment(environment: dict[str, str]) -> tuple[Path, int]:
    if (environment.get("GITHUB_ACTIONS") != "true" or environment.get("GITHUB_REPOSITORY") != REPOSITORY
            or environment.get("RUNNER_ENVIRONMENT") != "github-hosted" or not __debug__):
        raise ValueError("Replay requires the intended GitHub-hosted repository context")
    temporary = Path(environment["RUNNER_TEMP"]).resolve()
    root = Path(environment["M2_REPLAY_ROOT"]).resolve()
    if root != temporary / "m2-clean-replay":
        raise ValueError("Replay must use its dedicated runner temporary directory")
    port = int(environment["M2_REPLAY_PORT"])
    if not 1024 <= port <= 65535:
        raise ValueError("Invalid ephemeral service port")
    return root, port


def url(port: int, runtime: bool = False, database: str = DATABASE) -> str:
    # These are public, disposable CI-only passwords, never production credentials.
    user, password = ("game_discovery_runtime", "ci-runtime-only") if runtime else ("postgres", "ci-postgres-only")
    return f"postgresql://{user}:{password}@127.0.0.1:{port}/{database}"


def materialize_fixture(fixture: Path, identities: Path, run_dir: Path) -> dict:
    packed = json.loads(fixture.read_text(encoding="utf-8"))
    expected = json.loads(identities.read_text(encoding="utf-8"))
    if packed.get("schema_version") != 1 or packed.get("kind") != "steam-appdetails-field-projections":
        raise ValueError("Unsupported frozen source fixture")
    records = packed["records"]
    ids = [item["app_id"] for item in records]
    if len(ids) != 40 or len(set(ids)) != 40 or set(ids) != set(expected):
        raise ValueError("Fixture must reproduce the selected 40-game catalog")
    observations = []
    for item in records:
        original = Source.model_validate(item["original_source"])
        app_id = item["app_id"]
        expected_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=english"
        if original.url != expected_url:
            raise ValueError("Fixture provenance URL mismatch")
        # Verify identity/classification using the same actual normalizer, not invented game records.
        game = normalize_payload(app_id, item["payload"], original)
        if game.eligibility != "eligible":
            raise ValueError("Ineligible replay fixture")
        body = (json.dumps(item["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
        projected = original.model_copy(update={"sha256": hashlib.sha256(body).hexdigest()})
        name = f"{app_id}-appdetails-projection.json"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_bytes(body)
        observations.append({"app_id": app_id, "snapshot": name, "source": projected.model_dump(mode="json"),
                             "snapshot_kind": "frozen-field-projection",
                             "original_http_sha256": original.sha256})
    write_json(run_dir / "collection.json", {"schema_version": 1, "region": "US", "app_ids": ids,
                                              "observations": observations})
    return {"games": len(ids), "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
            "provenance": "Frozen real-source field projections. Artifact source hashes identify the projections; "
                          "the fixture separately preserves original HTTP hashes and collection times."}


def check_cluster(port: int) -> dict:
    with psycopg.connect(url(port, database="postgres")) as connection:
        version = int(connection.execute("show server_version_num").fetchone()[0])
        databases = {row[0] for row in connection.execute("select datname from pg_database")}
        if version // 10000 != 17 or databases - {"postgres", "template0", "template1", DATABASE}:
            raise ValueError("Refusing a cluster other than the dedicated PostgreSQL 17 service")
        return {"postgres_version": connection.execute("show server_version").fetchone()[0]}


def discard_database(port: int) -> None:
    check_cluster(port)
    with psycopg.connect(url(port, database="postgres"), autocommit=True) as connection:
        # Identifiers are fixed constants; no remote DSN, CLI database name or production .env is accepted.
        connection.execute("drop database if exists m2_replay with (force)")
        connection.execute("drop role if exists game_discovery_runtime")


def expect_denied(connection_url: str, statement: str, error_type: type[Exception] = InsufficientPrivilege) -> None:
    with psycopg.connect(connection_url) as connection:
        try:
            with connection.transaction():
                connection.execute(statement)
                raise AssertionError("Expected database rejection did not occur")
        except error_type:
            pass


def fingerprint(port: int) -> dict:
    tables = {}
    counts = {}
    with psycopg.connect(url(port)) as connection:
        for table in TABLES:
            rows = [row[0] for row in connection.execute(
                f"select to_jsonb(t) from discovery.{table} t order by version, app_id, to_jsonb(t)::text")]
            tables[table] = digest(rows)
            counts[table] = len(rows)
        versions = [row[0] for row in connection.execute("""select to_jsonb(t) - 'created_at' - 'activated_at'
            from discovery.catalog_versions t order by version""")]
        tables["catalog_versions_without_operational_timestamps"] = digest(versions)
    return {"table_hashes": tables, "row_counts": counts, "sha256": digest(tables)}


def verify_permissions(port: int, active: bool, expected_count: int) -> dict:
    with psycopg.connect(url(port, runtime=True)) as connection:
        attributes = connection.execute("""select rolsuper,rolcreatedb,rolcreaterole,rolbypassrls,rolinherit
            from pg_roles where rolname=current_user""").fetchone()
        assert attributes == (False, False, False, False, False), "Elevated runtime role"
        assert connection.execute("select count(*) from pg_auth_members where member=(select oid from pg_roles where rolname=current_user)").fetchone()[0] == 0
        for table in TABLES:
            count = connection.execute(f"select count(*) from discovery.{table}").fetchone()[0]
            if not active:
                assert count == 0, "Staged rows leaked"
            elif table in {"games", "game_embeddings", "game_prices"}:
                assert count == expected_count, "Active row count mismatch"
            else:
                assert count > 0, "Active table is unexpectedly empty"
        assert not connection.execute("select has_schema_privilege(current_user,'discovery','CREATE')").fetchone()[0]
    with psycopg.connect(url(port)) as connection:
        assert connection.execute("""select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace
            where n.nspname='discovery' and c.relkind='r' and not c.relrowsecurity""").fetchone()[0] == 0
        assert connection.execute("""select count(*) from pg_namespace n,
            lateral aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a
            where n.nspname='discovery' and a.grantee=0 and a.privilege_type='USAGE'""").fetchone()[0] == 0
    for statement in (
        "select * from discovery.job_runs", "select * from discovery_migrations.alembic_version",
        "update discovery.catalog_versions set active=false", "delete from discovery.games",
        "insert into discovery.games (version,app_id,title,normalized_title,description,eligibility,semantic_hash,document) "
        "select version,app_id,title,normalized_title,description,eligibility,semantic_hash,document from discovery.games where false",
        "update discovery.games set title='forbidden'", "truncate discovery.game_embeddings",
        "create table discovery.forbidden(id integer)", "create schema forbidden",
    ):
        expect_denied(url(port, runtime=True), statement)
    return {"runtime_not_elevated": True, "runtime_has_no_memberships": True, "all_tables_rls": True,
            "public_schema_usage_denied": True, "staging_hidden" if not active else "active_rows_readable": True,
            "write_ddl_job_log_and_migration_access_denied": True}


def run_pass(root: Path, port: int, number: int, fixture: Path, identities: Path) -> dict:
    directory = root / f"pass-{number}"
    source = materialize_fixture(fixture, identities, directory)
    normalized = normalize(directory)
    assert normalized["games"] == 40 and not normalized["quarantine"]
    first_embedding = embed(directory, root / "models", 8, resume=False)
    assert first_embedding["embedded"] == 40 and first_embedding["reused"] == 0
    artifact_before = validated_artifact(directory)[2]
    resumed = embed(directory, root / "models", 8, resume=True)
    assert resumed["embedded"] == 0 and resumed["reused"] == 40
    assert validated_artifact(directory)[2] == artifact_before
    reference = json.loads(Path("docs/reports/m2-artifact-manifest.json").read_text(encoding="utf-8"))
    for key in ("model_id", "model_revision", "model_sha256", "tokenizer_sha256", "dimensions"):
        assert artifact_before[key] == reference[key], "Pinned representation changed"

    with psycopg.connect(url(port, database="postgres"), autocommit=True) as connection:
        # Pass 1 uses the pristine DB initialized by the service; pass 2 recreates it after teardown.
        if number == 2:
            connection.execute("create database m2_replay")
    with psycopg.connect(url(port)) as connection:
        assert connection.execute("select count(*) from pg_namespace where nspname in ('discovery','discovery_migrations','extensions')").fetchone()[0] == 0
        assert connection.execute("select count(*) from pg_roles where rolname='game_discovery_runtime'").fetchone()[0] == 0
        assert connection.execute("select count(*) from pg_extension where extname='vector'").fetchone()[0] == 0
    env_file = root / "replay.env"
    env_file.write_text(f"MIGRATION_DATABASE_URL={url(port)}\n", encoding="utf-8")
    child_env = {**os.environ, "DATABASE_URL": url(port, runtime=True), "MIGRATION_DATABASE_URL": url(port),
                 "GAME_DISCOVERY_ENV_FILE": str(env_file), "GROQ_API_KEY": ""}
    for _ in range(2):
        subprocess.run([sys.executable, "-m", "game_discovery.db.migrate", "upgrade", "--env-file", str(env_file)],
                       env=child_env, check=True, timeout=90)
    with psycopg.connect(url(port)) as connection:
        assert connection.execute("select version_num from discovery_migrations.alembic_version").fetchone()[0] == "0002"
        assert connection.execute("select extversion from pg_extension where extname='vector'").fetchone()[0] == "0.8.2"
        connection.execute("alter role game_discovery_runtime password 'ci-runtime-only'")
    settings = Settings(database_url=SecretStr(url(port, runtime=True)))
    with TestClient(create_app(settings)) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/api/v1/catalog/status").json()["state"] == "uninitialized"
        assert client.get("/health/ready").json()["code"] == "catalog_not_initialized"
    staged = publish(directory, env_file, activate=False)
    assert not staged["active"] and not staged["reused"]
    staging_permissions = verify_permissions(port, active=False, expected_count=40)
    repeated = publish(directory, env_file, activate=False)
    assert repeated["reused"] and fingerprint(port)["row_counts"]["games"] == 40
    activated = publish(directory, env_file, activate=True)
    assert activated["active"]
    active_permissions = verify_permissions(port, active=True, expected_count=40)
    with psycopg.connect(url(port)) as connection:
        assert connection.execute("select count(*) from discovery.catalog_versions where active").fetchone()[0] == 1
        assert connection.execute("""select count(*) from discovery.game_embeddings
            where extensions.vector_dims(embedding)<>384 or abs(extensions.vector_norm(embedding)-1)>0.001""").fetchone()[0] == 0
    for statement, error_type in (
        ("update discovery.catalog_versions set dimensions=383", CheckViolation),
        ("insert into discovery.games (version,app_id,title,normalized_title,description,eligibility,semantic_hash,document) "
         "select version,app_id,title,normalized_title,description,eligibility,semantic_hash,document from discovery.games limit 1", UniqueViolation),
        ("update discovery.game_platforms set app_id=2147483647 where (version,app_id,platform)="
         "(select version,app_id,platform from discovery.game_platforms order by app_id,platform limit 1)", ForeignKeyViolation),
    ):
        expect_denied(url(port), statement, error_type)
    before = fingerprint(port)
    publish(directory, env_file, activate=True)
    assert fingerprint(port) == before, "Repeated activation changed catalog content"
    # Existing opt-in checks receive only explicit disposable URLs, never the checkout's .env.
    previous = {key: os.environ.get(key) for key in child_env if key in {"DATABASE_URL", "MIGRATION_DATABASE_URL", "GAME_DISCOVERY_ENV_FILE", "GROQ_API_KEY"}}
    os.environ.update({key: child_env[key] for key in previous})
    try:
        api = verify_catalog(directory / "api-report.json")
        interrupted = verify_import(directory, env_file, directory / "interrupted-import.json")
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    with TestClient(create_app(Settings(database_url=SecretStr(url(port))))) as client:
        assert client.get("/api/v1/catalog/status").json()["code"] == "database_role_misconfigured"
    assert fingerprint(port) == before, "Negative checks changed catalog data"
    return {"pass": number, "source": source, "artifact": artifact_before, "embedding_initial": first_embedding,
            "embedding_resume": resumed, "fingerprint": before, "staging_permissions": staging_permissions,
            "active_permissions": active_permissions, "api_cases": api["cases"], "request_ms": api["request_ms"],
            "interruption": interrupted, "migrations_from_empty": True, "migration_rerun": True,
            "migration_head": "0002", "pgvector_version": "0.8.2",
            "constraint_rejections": True, "privileged_api_login_rejected": True}


def main() -> int:
    root, port = replay_environment(dict(os.environ))  # Refuse before any DB connection or file mutation.
    report = {"schema_version": 1, "status": "running", "code_revision": os.environ["GITHUB_SHA"],
              "run_url": f"https://github.com/{REPOSITORY}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
              "started_at": datetime.now(UTC).isoformat(), "python": platform.python_version(),
              "architecture": platform.machine(), "uv_lock_sha256": hashlib.sha256(Path("backend/uv.lock").read_bytes()).hexdigest(),
              "passes": []}
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    owned = False
    try:
        report.update(check_cluster(port))
        # This service must be newly initialized, not an existing project database.
        with psycopg.connect(url(port)) as connection:
            assert connection.execute("select count(*) from pg_namespace where nspname='discovery'").fetchone()[0] == 0
        owned = True
        for number in (1, 2):
            report["phase"] = f"pass-{number}"
            result = run_pass(root, port, number, Path("data/fixtures/m2-replay-sources.json"), Path("data/fixtures/m2-app-ids.json"))
            report["passes"].append(result)
            write_json(reports / "replay.json", report)
            discard_database(port)
        report["phase"] = "compare-independent-replays"
        first, second = report["passes"]
        assert first["artifact"] == second["artifact"], "Fresh embedding/artifact builds differ"
        assert first["fingerprint"] == second["fingerprint"], "Clean database contents differ"
        assert first["api_cases"] == second["api_cases"], "Recommendation order/constraints differ"
        report.update(status="passed", reproducibility="Two independent clean database and embedding builds match exactly on this runner.")
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__)
        import traceback
        frame = traceback.extract_tb(error.__traceback__)[-1]
        report["failure_location"] = {"file": Path(frame.filename).name, "line": frame.lineno, "function": frame.name}
        if isinstance(error, AssertionError):
            report["failed_check"] = str(error)[:300]
    finally:
        if owned:
            try:
                discard_database(port)
                report["test_database_and_runtime_role_discarded"] = True
            except Exception as error:
                report.update(status="failed", cleanup_error_type=type(error).__name__)
        report["finished_at"] = datetime.now(UTC).isoformat()
        report["scope"] = "Disposable native PostgreSQL 17/pgvector 0.8.2; frozen real source projections; " \
                          "real CPU embeddings and FastAPI TestClient to restricted SQL login. No production access or relevance-quality claim."
        write_json(reports / "replay.json", report)
        summary = f"## M2 clean-database replay: {report['status']}\n\nRevision: `{report['code_revision']}`\n\n" \
                  f"Completed clean passes: {len(report['passes'])}/2. See the small replay report artifact for checks and hashes.\n"
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
                stream.write(summary)
        print(json.dumps({"job": "m2-clean-replay", "status": report["status"], "phase": report.get("phase"),
                          "error_type": report.get("error_type"), "completed_passes": len(report["passes"])}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
