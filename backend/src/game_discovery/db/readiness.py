from dataclasses import dataclass
from datetime import datetime

from pydantic import SecretStr
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError, TimeoutError

from game_discovery.db.engine import create_runtime_engine


@dataclass(frozen=True)
class CatalogReadiness:
    error_code: str | None = None
    retryable: bool = False
    version: str | None = None
    game_count: int = 0
    observed_at: datetime | None = None


def probe_catalog(database_url: SecretStr, engine: Engine | None = None) -> CatalogReadiness:
    if not database_url.get_secret_value():
        return CatalogReadiness(error_code="database_unconfigured")
    owned_engine = engine is None
    try:
        engine = engine or create_runtime_engine(database_url)
        assert engine is not None
        with engine.connect() as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout = '2s'"))
            elevated = connection.execute(
                text("select rolsuper or rolcreatedb or rolcreaterole or rolbypassrls from pg_roles where rolname=current_user")
            ).scalar_one()
            if elevated:
                return CatalogReadiness(error_code="database_role_misconfigured")
            row = connection.execute(
                text("select version, game_count, source_observed_at from discovery.catalog_versions where active")
            ).fetchone()
            return CatalogReadiness(version=row[0], game_count=row[1], observed_at=row[2]) if row else CatalogReadiness()
    except ValueError:
        return CatalogReadiness(error_code="database_configuration_invalid")
    except TimeoutError:
        return CatalogReadiness(error_code="database_busy", retryable=True)
    except SQLAlchemyError:
        # Do not log DSNs or driver messages, which can contain connection details.
        return CatalogReadiness(error_code="database_unavailable", retryable=True)
    finally:
        if owned_engine and engine is not None:
            engine.dispose()
