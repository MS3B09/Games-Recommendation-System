"""Alembic operations using only privileged developer credentials, never at startup."""

import argparse
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.util import CommandError
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from game_discovery.core.database_url import normalize_db_url

BOOTSTRAP = """
create schema if not exists discovery_migrations;
revoke all on schema discovery_migrations from public;
"""
HARDEN = """
revoke all on discovery_migrations.alembic_version from public;
alter table discovery_migrations.alembic_version enable row level security;
drop policy if exists alembic_no_client_access on discovery_migrations.alembic_version;
create policy alembic_no_client_access on discovery_migrations.alembic_version
for all to public using (false) with check (false);
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["current", "upgrade", "sql"])
    parser.add_argument("--env-file", type=Path, default=Path("backend/.env"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    cfg = Config(str(root / "alembic.ini"))
    if args.action == "sql":
        print(BOOTSTRAP)
        command.upgrade(cfg, "head", sql=True)
        print(HARDEN)
        return
    values = dotenv_values(args.env_file, interpolate=False) if args.env_file.is_file() else {}
    url = os.environ.get("MIGRATION_DATABASE_URL", values.get("MIGRATION_DATABASE_URL") or "")
    if not url:
        parser.exit(1, "Set MIGRATION_DATABASE_URL locally or in developer job settings.\n")
    engine = None
    try:
        engine = create_engine(
            make_url(normalize_db_url(url)).set(drivername="postgresql+psycopg"),
            poolclass=NullPool, hide_parameters=True,
            connect_args={"connect_timeout": 3, "prepare_threshold": None},
        )
        with engine.begin() as connection:
            cfg.attributes["connection"] = connection
            if args.action == "current":
                command.current(cfg, verbose=True)
            else:
                connection.exec_driver_sql(BOOTSTRAP)
                command.upgrade(cfg, "head")
                connection.exec_driver_sql(HARDEN)
    except (ValueError, SQLAlchemyError, CommandError):
        parser.exit(1, "Migration operation failed. Check configuration/schema with developer tools; credentials are not logged.\n")
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
