"""Lazy, bounded serving connections; migration credentials never enter this module."""

from pydantic import SecretStr
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url

from game_discovery.core.database_url import normalize_db_url


def create_runtime_engine(database_url: SecretStr) -> Engine | None:
    if not database_url.get_secret_value():
        return None
    url = make_url(normalize_db_url(database_url.get_secret_value()))
    if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
        raise ValueError("A PostgreSQL database URL is required")
    url = url.set(drivername="postgresql+psycopg")
    return create_engine(
        url, pool_size=2, max_overflow=0, pool_timeout=1, pool_recycle=300,
        connect_args={"connect_timeout": 3, "prepare_threshold": None},
        hide_parameters=True, echo=False,
    )
