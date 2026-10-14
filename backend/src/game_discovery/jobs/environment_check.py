"""Check configuration without printing values, credentials, DSNs or exceptions."""

import json
import socket
from pathlib import Path
from urllib.parse import urlsplit

from game_discovery.core.database_url import db_url_matches_project, normalize_db_url, role_identity

KNOWN_KEYS = (
    "DATABASE_URL", "MIGRATION_DATABASE_URL", "SUPABASE_URL", "SUPABASE_PROJECT_URL",
    "SUPABASE_DB_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY",
    "GROQ_API_KEY", "GROQ_MODEL", "AI_ENABLED",
)


def read_only_db_check(value: str) -> dict:
    import psycopg

    try:
        with psycopg.connect(normalize_db_url(value), connect_timeout=10, prepare_threshold=None) as connection:
            connection.read_only = True
            connection.execute("SET LOCAL statement_timeout = '5s'")
            row = connection.execute(
                "SELECT current_setting('server_version'), pg_database_size(current_database()), "
                "(SELECT extversion FROM pg_extension WHERE extname='vector'), "
                "(SELECT count(*) FROM pg_tables WHERE schemaname='public'), "
                "(SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls FROM pg_roles WHERE rolname=current_user)"
            ).fetchone()
            return {"status": "ok", "postgres_version": row[0], "database_bytes": row[1],
                    "pgvector_version": row[2], "public_table_count": row[3],
                    "role_has_elevated_attributes": row[4]}
    except Exception as error:
        # Exception messages may contain usernames, hostnames and connection details.
        text = str(error).casefold()
        failure = "connection_failed"
        for fragment, code in (
            ("password authentication failed", "authentication_failed"),
            ("tenant or user not found", "pooler_role_not_found"),
            ("network is unreachable", "network_unreachable"),
            ("no route to host", "network_unreachable"),
            ("getaddrinfo", "dns_resolution_failed"),
            ("could not translate host name", "dns_resolution_failed"),
            ("connection refused", "connection_refused"),
            ("timeout", "connection_timeout"),
            ("timed out", "connection_timeout"),
            ("invalid", "invalid_connection_configuration"),
        ):
            if fragment in text:
                failure = code
                break
        diagnostics = {"system_dns_resolves": False, "ipv4_address_available": False,
                       "ipv6_address_available": False}
        try:
            parsed = urlsplit(normalize_db_url(value))
            addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 5432, type=socket.SOCK_STREAM)
            diagnostics = {"system_dns_resolves": bool(addresses),
                           "ipv4_address_available": any(item[0] == socket.AF_INET for item in addresses),
                           "ipv6_address_available": any(item[0] == socket.AF_INET6 for item in addresses)}
        except (OSError, ValueError):
            pass
        return {"status": "failed", "error_type": type(error).__name__, "failure_code": failure,
                "network_diagnostics": diagnostics}


def run_environment_check(path: Path, project_url: str, connect: bool) -> int:
    from dotenv import dotenv_values

    if not path.is_file():
        raise ValueError("Configuration file is unavailable")
    config = dotenv_values(path, interpolate=False)
    report = {"job": "environment-check", "configured": {key: bool(config.get(key)) for key in KNOWN_KEYS},
              "project_matches": {key: db_url_matches_project(config.get(key), project_url)
                                  for key in ("DATABASE_URL", "MIGRATION_DATABASE_URL")}}
    report["connection_modes"] = {}
    report["url_contains_unescaped_at_sign"] = {}
    for key in ("DATABASE_URL", "MIGRATION_DATABASE_URL"):
        try:
            parsed = urlsplit(normalize_db_url(config.get(key) or ""))
            report["url_contains_unescaped_at_sign"][key] = urlsplit(config.get(key) or "").netloc.count("@") > 1
            mode = "direct" if (parsed.hostname or "").startswith("db.") else "shared_pooler"
            report["connection_modes"][key] = mode if parsed.hostname else "unconfigured"
        except ValueError:
            report["connection_modes"][key] = "invalid"
            report["url_contains_unescaped_at_sign"][key] = False
    # Check role separation without exposing either username or a secret fingerprint.
    try:
        runtime = role_identity(config.get("DATABASE_URL") or "", project_url)
        migration = role_identity(config.get("MIGRATION_DATABASE_URL") or "", project_url)
        report["runtime_and_migration_roles_distinct"] = bool(runtime and migration and runtime != migration)
    except ValueError:
        report["runtime_and_migration_roles_distinct"] = False
    if connect:
        report["connections"] = {
            key: read_only_db_check(config[key]) if config.get(key) and report["project_matches"][key]
            else {"status": "skipped", "reason": "missing_url_or_project_mismatch"}
            for key in ("DATABASE_URL", "MIGRATION_DATABASE_URL")
        }
    success = all(report["configured"][key] and report["project_matches"][key]
                  for key in ("DATABASE_URL", "MIGRATION_DATABASE_URL"))
    if connect:
        success = success and all(item["status"] == "ok" for item in report["connections"].values())
    report["status"] = "ok" if success else "partial"
    print(json.dumps(report))
    return 0 if success else 1
