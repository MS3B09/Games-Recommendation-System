"""Compact analytics sidecars bound to active catalog generations."""

from pathlib import Path

from alembic import op

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / 'migrations/0011_catalog_analytics.sql').read_text(encoding='utf-8'))


def downgrade() -> None:
    raise RuntimeError('No destructive analytics downgrade; roll back compatible application/catalog versions together')
