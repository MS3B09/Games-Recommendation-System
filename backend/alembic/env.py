"""Explicit developer workflow. Serving never imports or executes this module."""

from alembic import context
from sqlalchemy import Connection

config = context.config

if context.is_offline_mode():
    context.configure(
        url="postgresql+psycopg://offline:placeholder@localhost/postgres",
        literal_binds=True, version_table_schema="discovery_migrations",
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    connection: Connection = config.attributes["connection"]
    context.configure(connection=connection, version_table_schema="discovery_migrations")
    with context.begin_transaction():
        context.run_migrations()
