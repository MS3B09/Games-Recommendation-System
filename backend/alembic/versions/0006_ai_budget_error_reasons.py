"""Precise error reasons; preserve counters, ceilings and legacy reservation API."""
from pathlib import Path
from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute((Path(__file__).resolve().parents[2] / 'migrations' / '0007_ai_budget_error_reasons.sql').read_text(encoding='utf-8'))


def downgrade() -> None:
    op.execute('drop function discovery.reserve_ai_usage_detailed(integer, integer, integer)')
