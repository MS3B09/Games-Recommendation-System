"""Initial private metadata schema; existing M1 database adopts this verified baseline."""

from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = (Path(__file__).resolve().parents[2] / "migrations" / "0001_catalog_metadata.sql").read_text(encoding="utf-8")
    # The SQL file is developer-authored; it contains no credentials or user data.
    op.execute(sql)


def downgrade() -> None:
    raise RuntimeError("Destructive initial-schema rollback is manual; restore a verified backup instead.")
